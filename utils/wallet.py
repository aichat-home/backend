from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore
from solders.rpc.responses import RpcKeyedAccountJsonParsed # type: ignore

from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts

from spl.token.constants import TOKEN_PROGRAM_ID

from cryptography.fernet import Fernet

from core import settings
from models import SolanaWallet


fernet = Fernet(key=settings.encryption_key)
client = AsyncClient('https://api.mainnet-beta.solana.com')


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


async def create_wallet(session: AsyncSession, user_id: int) -> SolanaWallet:
    '''Create a new wallet in the database and return Solana wallet instance'''
    public_key, encrypted_private_key = create_keypair()
    wallet = SolanaWallet(wallet=user_id, public_key=public_key, private_key=encrypted_private_key)

    session.add(wallet)
    await session.commit()

    return wallet


async def get_wallets_by_id(session: AsyncSession, user_id: int) -> list[SolanaWallet | None] | None:
    '''Get all wallets of a given user by ID'''
    result = await session.execute(select(SolanaWallet).filter(SolanaWallet.wallet == user_id))
    wallets =  result.scalars().all()

    return wallets


async def get_wallet_by_public_key(session: AsyncSession, public_key: str) -> SolanaWallet | None:
    '''Get wallet by public key'''
    result = await session.execute(select(SolanaWallet).filter(SolanaWallet.public_key == public_key))
    wallet = result.scalars().first()

    return wallet


async def get_tokens(wallet_address: Pubkey):
    '''Get all tokens of a given wallet'''
    tokens = await client.get_token_accounts_by_owner_json_parsed(wallet_address, opts=opts)
    return tokens


def parse_token_mint_address_and_amount(token: RpcKeyedAccountJsonParsed):
    '''Parse token mint address and amount'''
    mint_address = token.account.data.parsed['info']['mint']
    amount = token.account.data.parsed['info']['tokenAmount']['uiAmount']

    return mint_address, amount