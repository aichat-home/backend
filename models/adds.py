from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db import Base



class Add(Base):
    __tablename__ ='add'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    button_text: Mapped[str] = mapped_column(String(32), nullable=False)
    link_text: Mapped[str] = mapped_column(String(255), nullable=False)

