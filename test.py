import asyncio
import base58

from solders.pubkey import Pubkey # type: ignore

from session import get_session, init_session




async def main():
    init_session()
    session = get_session()
    
    fee_token_account = Pubkey.find_program_address(
            [
                b'referral_ata',
                bytes(Pubkey.from_string('3hf1aGtRFdUZtjsej149KTVMsftbv4TRfndtGMJKdVdb')),
                bytes(Pubkey.from_string('JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN'))
            ],
            program_id=Pubkey.from_string('REFER4ZgmyYx9c6He5XfaTMiGfdLwRnkV4RPp9t9iF3')
        )
    
    print(fee_token_account[0].to_json())    


asyncio.run(main())