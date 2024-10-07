from pydantic import BaseModel



class NewsResponse(BaseModel):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    link: str | None = None
