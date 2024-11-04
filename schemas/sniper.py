from pydantic import BaseModel



class SniperNotificate(BaseModel):
    user_id: int
    order_id: int
    txn_sig: str
    confirmed: bool
    token_amount: float