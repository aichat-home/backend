from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from db import Base



class New(Base):
    __tablename__ = 'news'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, nullable=False, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    creator_name: Mapped[str] = mapped_column(String(255), nullable=False, default='Unknown')
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    link: Mapped[str] = mapped_column(Text, nullable=True)
    
