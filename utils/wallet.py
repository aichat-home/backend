from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore
from solders.rpc.responses import RpcKeyedAccountJsonParsed # type: ignore
from solders.system_program import transfer, TransferParams

from solana.rpc.types import TokenAccountOpts, TxOpts
from solana.transaction import Transaction

from spl.token.constants import TOKEN_PROGRAM_ID

from cryptography.fernet import Fernet

from core import settings
from models import SolanaWallet as Wallet, Swap, Withdraw
from rpc import client


fernet = Fernet(key=settings.encryption_key)


opts = TokenAccountOpts(
    program_id=TOKEN_PROGRAM_ID
)


def encrypt_private_key(private_key_bytes: bytes) -> bytes:
    '''Encrypt private key'''
    encrypted_key = fernet.encrypt(private_key_bytes)
    return encrypted_key


def decrypt_private_key(encrypted_private_key: bytes | str) -> bytes:
    '''Decrypt private key'''
    decrypted_private_key = fernet.decrypt(encrypted_private_key)
    return decrypted_private_key


def create_keypair() -> tuple[str | bytes]:
    '''Create a new keypair and return public key and encrypted private key'''
    keypair = Keypair()
    public_key = str(keypair.pubkey())
    private_key_bytes = keypair.secret()

    encrypted_private_key = encrypt_private_key(private_key_bytes)
    return public_key, encrypted_private_key


async def create_wallet(session: AsyncSession, user_id: int) -> Wallet:
    '''Create a new wallet in the database and return Solana wallet instance'''
    public_key, encrypted_private_key = create_keypair()
    wallet = Wallet(wallet=user_id, public_key=public_key, encrypted_private_key=encrypted_private_key)

    session.add(wallet)
    await session.commit()

    return wallet


async def get_wallet_by_id(session: AsyncSession, user_id: int) -> Wallet | None:
    '''Get all wallets of a given user by ID'''
    result = await session.execute(select(Wallet).filter(Wallet.wallet == user_id))
    wallets =  result.scalars().first()

    return wallets


async def get_wallet_by_public_key(session: AsyncSession, public_key: str) -> Wallet | None:
    '''Get wallet by public key'''
    result = await session.execute(select(Wallet).filter(Wallet.public_key == public_key))
    wallet = result.scalars().first()

    return wallet


async def get_tokens(wallet_address: str):
    '''Get all tokens of a given wallet'''
    wallet_address = Pubkey.from_string(wallet_address)
    tokens = await client.get_token_accounts_by_owner_json_parsed(wallet_address, opts=opts)
    return tokens

async def get_token(wallet_address: str, input_mint: str):
    '''Get a token by mint address'''
    wallet_address = Pubkey.from_string(wallet_address)
    tokens = await client.get_token_accounts_by_owner_json_parsed(wallet_address, TokenAccountOpts(
        program_id=TOKEN_PROGRAM_ID,
        mint=Pubkey.from_string(input_mint)
    ))
    return tokens


def parse_token_mint_address_amount_decimals(token: RpcKeyedAccountJsonParsed) -> tuple[str, str]:
    '''Parse token mint address and amount'''
    mint_address = token.account.data.parsed['info']['mint']
    amount = token.account.data.parsed['info']['tokenAmount']['uiAmount']
    decimals = token.account.data.parsed['info']['tokenAmount']['decimals']

    return mint_address, amount, decimals


async def get_wallet_balance(wallet_address: str):
    '''Get wallet balance'''
    wallet_address = Pubkey.from_string(wallet_address)
    balance = await client.get_balance(wallet_address)
    return balance.value / 1_000_000_000


async def send_transaction(lamports_amount: int, encrypted_private_key: bytes, receiver_address: str):
    '''Send transaction to a Solana wallet'''
    private_key = decrypt_private_key(encrypted_private_key=encrypted_private_key)
    sender_keypair = Keypair.from_seed(private_key)

    receiver_public_key = Pubkey.from_string(receiver_address)

    transaction = Transaction()

    # Add the transfer instruction to the transaction
    transfer_to_user = transfer(
        TransferParams(
            from_pubkey=sender_keypair.pubkey(),
            to_pubkey=receiver_public_key,
            lamports=int(lamports_amount)
        )
    )
    transaction.add(transfer_to_user)

    # Sign the transaction
    transaction.sign(sender_keypair)

    # Send the transaction
    response = await client.send_transaction(transaction, sender_keypair, opts=TxOpts(skip_preflight=False, preflight_commitment="processed"))

    return response.value


def calculate_fee(lamports_amount: int) -> tuple[int, int]:
    '''Calculate transaction fee'''
    solana_fee = settings.solana_fee
    program_fee_percentage = settings.program_fee_percentage

    lamports_amount -= solana_fee

    lamports_to_send_to_admin_wallet = (lamports_amount * program_fee_percentage) // 100
    lamports_to_send_to_user_wallet = lamports_amount - lamports_to_send_to_admin_wallet
    
    return int(lamports_to_send_to_user_wallet), int(lamports_to_send_to_admin_wallet)


async def get_buy_swaps(wallet_id: int, token_address: str, session: AsyncSession) -> list[Swap]:
    '''Get swaps for a given wallet'''
    stmt = select(Swap).filter(Swap.wallet == wallet_id).filter(Swap.output_mint == token_address).filter(Swap.status == 'Finalized')
    result = await session.execute(stmt)
    swaps = result.scalars().all()
    return swaps


async def get_sell_swaps(wallet_id: int, token_address: str, session: AsyncSession) -> list[Swap]:
    '''Get swaps for a given wallet'''
    stmt = select(Swap).filter(Swap.wallet == wallet_id).filter(Swap.input_mint == token_address).filter(Swap.status == 'Finalized')
    result = await session.execute(stmt)
    swaps = result.scalars().all()
    return swaps


def get_total_amount(swaps: list[Swap]) -> tuple[int, int]:
    '''Calculate total amount for swaps'''
    input_amount = sum(swap.input_amount for swap in swaps)
    output_amount = sum(swap.output_amount for swap in swaps)
    return input_amount, output_amount


def calculate_pnl(average_buy_price: int, average_sell_price: int) -> float:
    '''Calculate profit and loss'''
    return (average_sell_price / average_buy_price) * 100 - 100


async def get_average_buy_price_and_pnl(wallet_id: int, token_address: str, session: AsyncSession) -> tuple[float, float]:
    '''Calculate profit and loss for a given wallet'''
    try:
        buy_swaps = await get_buy_swaps(wallet_id, token_address, session)

        if not buy_swaps:
            return 0

        buy_input_amount, buy_output_amount = get_total_amount(buy_swaps)

        average_buy_price = buy_input_amount / buy_output_amount

        if not buy_swaps:
            return average_buy_price

        return average_buy_price
    except Exception as e:
        print(f"Error: {e}")
        return 0, 0
    


async def create_withdraw_in_db(
        from_pubkey: str,
        to_pubkey: str,
        lamports: int,
        session: AsyncSession,
        wallet_id: int
    ):
    '''Create withdrawal in the database'''

    withdraw = Withdraw(
        wallet=wallet_id,
        from_pubkey=from_pubkey,
        to_pubkey=to_pubkey,
        lamports=lamports,
        date=datetime.now()
    )
    session.add(withdraw)
    await session.commit()