import json
import base64

from solders.keypair import Keypair # type: ignore
from solders.message import  to_bytes_versioned # type: ignore
from solders.transaction import VersionedTransaction # type: ignore

from solana.rpc.types import TxOpts
from solana.rpc.commitment import Processed

from . import wallet
from rpc import metis_client as client
from session import get_session



async def get_quote(input_mint, output_mint, amount, slippage_bps, session):
    '''Get a quote from the Jupiter API'''
    try:
        url = "https://quote-api.jup.ag/v6/quote"
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': amount,
            'slippageBps': slippage_bps
        }
        headers = {'Accept': 'application/json'}
        async with session.get(url, params=params, headers=headers) as response:
            return await response.json()
    except Exception as e:
        print(f"Error in get_quote: {e}")
        return None
    

async def get_swap(user_public_key, quote_response, session):
    '''Get swap instructions from the Jupiter API'''
    try:
        url = "https://quote-api.jup.ag/v6/swap"
        payload = json.dumps({
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": True,
            "useSharedAccounts": True,
            "quoteResponse": quote_response
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        async with session.post(url, data=payload, headers=headers) as response:
            return await response.json()
    except Exception as e:
        print(f"Error in get_swap_instructions: {e}")
        return None
    

async def swap(encrypted_private_key, input_mint, output_mint, amount_lamports, slippage_bps, decimals):
    '''Swap tokens using the Jupiter API'''
    try:    
        # Get a aiohttp session for making API calls
        session = get_session()

        # Decrypt the private key, create a keypair, and get the public key string
        private_key = wallet.decrypt_private_key(encrypted_private_key=encrypted_private_key)
        keypair = Keypair.from_seed(private_key)

        pub_key_str = str(keypair.pubkey())
        
        # Convert the amount to lamports and set it in the transaction
        amount_lamports = int(amount_lamports * 10 ** decimals)
        
        # Get a quote and swap instructions from the Jupiter API
        quote_response = await get_quote(input_mint, output_mint, amount_lamports, slippage_bps, session)
        if not quote_response:
            print("No quote response.")
            return False
        print(quote_response)
        
        # Get the swap transaction from the Jupiter API
        swap_transaction = await get_swap(pub_key_str, quote_response, session)
        if not swap_transaction:
            print("No swap transaction response.")
            return False
        print(swap_transaction)
        
        # Sign the transaction, send it to the Solana network, and print the transaction signature
        raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(swap_transaction['swapTransaction']))
        signature = keypair.sign_message(to_bytes_versioned(raw_transaction.message))
        signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
        opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
        tx_sig = await client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
        print(f"Transaction Signature: {tx_sig.value}")

        return tx_sig.value, quote_response
    except Exception as e:
        print(e)
        return False