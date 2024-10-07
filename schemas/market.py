from pydantic import BaseModel



class TokenResponse(BaseModel):
    symbol: str | None = None
    name: str | None = None
    image: str | None = None
    address: str | None = None
    price: float | None = None
    market_cap: float | None = None
    total_volume: float | None = None
    price_change_percentage_24h: float | None = None

