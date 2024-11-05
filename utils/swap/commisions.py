from solders.pubkey import Pubkey # type: ignore
from solders.system_program import transfer, TransferParams

from sqlalchemy.ext.asyncio import AsyncSession

from models import RefferAccount, SolanaWallet
from utils import wallet



COMMISION_REWARDS_PERCENTS = {
    1: 30,
    2: 3.5,
    3: 2.5,
    4: 1
}


LIMIT_FOR_LAYERS = {
    10: 1,
    20: 2,
    30: 3,
    40: 4
}


def get_layer_for_amount(amount: int):
    if amount < min(LIMIT_FOR_LAYERS.keys()):
        return None
    else:
        for limit, layer in LIMIT_FOR_LAYERS.items():
            if amount < limit:
                print(layer-1)
                break

    return max(LIMIT_FOR_LAYERS.values())


async def get_all_instructions_for_referrals(user_id: int, from_pubkey: str, fee_amount: int, layers: int, session: AsyncSession):
    instructions = []
    total_fee = 0
    result = []

    referral_layers = await get_referral_layers(user_id=user_id, layers=layers, session=session)
    if referral_layers:
        referral_layers_wallet = await get_referral_layers_wallets(referral_layers, session)
        if referral_layers_wallet:
            for i, wallet in enumerate(referral_layers_wallet, 1):
                amount = fee_amount * (COMMISION_REWARDS_PERCENTS[i] / 100)
                if amount <= 5000000:
                    check = await check_balance(wallet.public_key)
                    if check == False:
                        continue
                instruction = create_referral_instruction(
                    from_pubkey=from_pubkey,
                    to_pubkey=wallet.public_key,
                    amount=amount
                )
                if instruction:
                    total_fee += amount
                    instructions.append(instruction)
                    result.append(wallet, amount)
    
    return instructions, total_fee, result


async def check_balance(public_key: str) -> bool:
    balance = await wallet.get_wallet_balance(public_key)
    return balance > 0.005


async def get_referral_layers(user_id: int, layers: int, session: AsyncSession):
    reffer_account = await session.get(RefferAccount, user_id)
    layer_referrals: list[int] = []
    if reffer_account:
        layer_referrals.append(reffer_account.oneWhoInvited)
        for _ in range(layers - 1):
            reffer_account = await session.get(RefferAccount, reffer_account.oneWhoInvited)
            if reffer_account:
                layer_referrals.append(reffer_account.oneWhoInvited)
            else:
                break

    return layer_referrals


async def get_referral_layers_wallets(referral_layers: list[int], session: AsyncSession):
    referral_layer_wallets: list[SolanaWallet] = []
    for referral_layer in referral_layers:
        db_wallet = await wallet.get_wallet_by_id(session, referral_layer)
        if db_wallet:
            referral_layer_wallets.append(db_wallet)

    return referral_layer_wallets


def create_referral_instruction(from_pubkey: str, to_pubkey: str, amount: int):
    try:
        return transfer(
            TransferParams(
                from_pubkey=Pubkey.from_string(from_pubkey),
                to_pubkey=Pubkey.from_string(to_pubkey),
                lamports=int(amount)
            )
        )
    except Exception as e:
        print(f'Error creating instruciton: {e}')
        return None