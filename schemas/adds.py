from typing import List
from pydantic import BaseModel


class AddBase(BaseModel):
    title: str
    description: str
    button_text: str
    link_text: str

    class Config:
        from_attributes = True


class AddCreate(AddBase):
    pass


class AddResponse(AddBase):
    id: int

