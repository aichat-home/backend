import base58
from solders.keypair import Keypair # type: ignore

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from solders.transaction_status import TransactionConfirmationStatus # type: ignore
from solana.rpc.commitment import Finalized

from bot.keyboards import wallet_keyboard, export_wallet_confirmation, close_private_key, cancel_withdraw, to_home
from bot.texts import texts
from bot.states import withdraw
from rpc import client
from utils import wallet
from models import SolanaWallet as Wallet


router = Router()


@router.callback_query(F.data == 'wallet')
async def get_token(callback_query: CallbackQuery, session: AsyncSession):
    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
    balance = await wallet.get_wallet_balance(db_wallet.public_key)
    try:
        await callback_query.message.edit_caption(caption=(
            'Your Wallet:\n\n'

            f'Address: <code>{db_wallet.public_key}</code>\n'
            f'Balance: <code>{balance} SOL</code>\n\n'

            'Tap to copy the address and send SOL to deposit.'),
            reply_markup=wallet_keyboard(db_wallet.public_key)
            )
    except Exception:
        pass
    await callback_query.answer()


@router.callback_query(F.data.startswith('export_confirmation_'))
async def key_confirmation(callback_query: CallbackQuery):
    wallet_address = callback_query.data.split('_')[2]
    await callback_query.message.edit_caption(
        caption=texts.CONFIRMATION_TEXT,
        reply_markup=export_wallet_confirmation(wallet_address)   
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith('export_key_'))
async def export_key(callback_query: CallbackQuery, session: AsyncSession):
    wallet_address = callback_query.data.split('_')[2]
    db_wallet = await wallet.get_wallet_by_public_key(session, wallet_address)
    if db_wallet:
        private_key_bytes = wallet.decrypt_private_key(db_wallet.encrypted_private_key)
        keypair = Keypair.from_seed(private_key_bytes)
        public_key_bytes = bytes(keypair.pubkey())
        encoded_keypair = private_key_bytes+public_key_bytes
        private_key = base58.b58encode(encoded_keypair).decode()

        await callback_query.message.edit_caption(
            caption=('Your <b>Private Key</b> is:\n\n'
             f'<code>{private_key}</code>\n\n'
             'You can now e.g. import the key into apps like Phantom (tap to copy)'
             ),
             reply_markup=close_private_key()
             )
    
    await callback_query.answer()


@router.callback_query(F.data.startswith('withdraw_'))
async def withdraw_check(callback_query: CallbackQuery, session: AsyncSession, state: FSMContext):
        amount = callback_query.data.split('_')[1]

        db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
        balance = await wallet.get_wallet_balance(db_wallet.public_key)
        await state.update_data(db_wallet=db_wallet)

        if amount == 'all':
            amount = balance
            await state.update_data(amount=amount)

            await state.set_state(withdraw.WithdrawState.receiver_address)
            caption = 'Enter receiver address'
        else:
            await state.set_state(withdraw.WithdrawState.amount)
            caption = 'Enter amount'
        await callback_query.message.edit_caption(caption=caption, reply_markup=cancel_withdraw())
    

@router.callback_query(F.data == 'confirm')
async def confirm_withdraw(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state == withdraw.WithdrawState.confirm:
        data = await state.get_data()

        db_wallet: Wallet = data.get('db_wallet')
        receiver_address = data.get('receiver_address')
        amount = data.get('amount')

        balance = await wallet.get_wallet_balance(db_wallet.public_key)

        if amount <= balance:
            try:
                tx_sig = await wallet.send_transaction(amount * 1_000_000_000, db_wallet.encrypted_private_key, receiver_address)
                await callback_query.message.edit_caption(caption='Transaction sent. Waiting for confirmation...')

                confirmation = await client.confirm_transaction(tx_sig, commitment=Finalized, sleep_seconds=5)
                if confirmation.value:
                    if confirmation.value[0].confirmation_status == TransactionConfirmationStatus.Finalized:
                        await callback_query.message.edit_caption(caption='Transaction went successfull', reply_markup=to_home())
                        await state.clear()

                        await wallet.create_withdraw_in_db(
                            from_pubkey=db_wallet.public_key,
                            to_pubkey=receiver_address,
                            lamports=amount,
                            wallet_id=db_wallet.id,
                            session=session
                        )
            except Exception as e:
                print(e)
                await callback_query.message.edit_caption(caption='Transaction failed', reply_markup=to_home())
                return
        else:
            await callback_query.message.edit_caption(caption='Insufficient balance', reply_markup=to_home())
            return
        await callback_query.answer()
        