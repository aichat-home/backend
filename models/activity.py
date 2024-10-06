from datetime import datetime

from sqlalchemy import Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class Activity(Base):
    __tablename__ = 'activities'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    daily_activities: Mapped[list['DailyActivity']] = relationship('DailyActivity', back_populates='activity')


class DailyActivity(Base):
    __tablename__ = 'daily_activities'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey('activities.id'))
    users_entered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_users_entered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partner_users_entered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  
    reffered_users_entered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    connected_wallets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    farm_started: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    finished: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    activity: Mapped['Activity'] = relationship('Activity', back_populates='daily_activities')