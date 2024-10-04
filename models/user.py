from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Enum, Text, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import Integer, Text, ForeignKey, DOUBLE_PRECISION, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship


from models.account_to_task import AccountToTask
from db import Base
from enums import farmstatuses



class Partner(Base):
    __tablename__ = 'partners'

    id: Mapped[int] = mapped_column(Integer, nullable=False, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    inviteCode: Mapped[str] = mapped_column(Text, primary_key=True, index=True)

    users: Mapped[list['User']] = relationship('User', back_populates='Partner')

    def __str__(self) -> str:
        return self.name


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True, nullable=False, autoincrement=False, unique=True)
    last_name: Mapped[str] = mapped_column(Text, unique=False, nullable=True)
    first_name: Mapped[str] = mapped_column(Text, unique=False, nullable=True)
    username: Mapped[str] = mapped_column(Text, nullable=True, index=True)
    isPremium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(String(255), default='REGULAR', nullable=False)
    partner: Mapped[str] = mapped_column(ForeignKey('partners.inviteCode'), nullable=True)

    Partner: Mapped['Partner'] = relationship('Partner', back_populates='users')
    account: Mapped['Account'] = relationship('Account', back_populates='user')
    wallet: Mapped['Wallet'] = relationship('Wallet', back_populates='user')
    refferAccount: Mapped['RefferAccount'] = relationship('RefferAccount', back_populates='user')

    def __str__(self) -> str:
        return str(self.id)


class Account(Base):
    __tablename__ = 'accounts'

    id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, unique=True, index=True)
    age: Mapped[int] = mapped_column(DOUBLE_PRECISION, nullable=False, default=0)
    inviteCode: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    heSeeWelcomeScreen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reffers_checked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped['User'] = relationship('User', back_populates='account')
    reffers: Mapped[list['RefferAccount']] = relationship('RefferAccount', back_populates='OneWhoInvited')
    completedTasks: Mapped[list['Task']] = relationship(
        'Task',
        secondary=AccountToTask,
        back_populates='usersCompleted'
    )

    def __str__(self) -> str:
        return str(self.id)


class RefferAccount(Base):
    __tablename__ = 'reffers_accounts'

    id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, index=True)
    earned_coins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    earned_tickets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    oneWhoInvited: Mapped[int] = mapped_column(BigInteger, ForeignKey('accounts.id', onupdate='CASCADE', ondelete='CASCADE'), index=True)

    user: Mapped['User'] = relationship('User', back_populates='refferAccount')
    OneWhoInvited: Mapped['Account'] = relationship('Account', back_populates='reffers')

    def __str__(self) -> str:
        return str(self.id)


class Task(Base):
    __tablename__ = 'tasks'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    icon: Mapped[str] = mapped_column(String(255), default='Telegram', nullable=False)
    type: Mapped[str] = mapped_column(String(255), default='Partners', nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    link: Mapped[str] = mapped_column(Text, nullable=True)
    chatId: Mapped[str] = mapped_column(Text, nullable=True)

    usersCompleted: Mapped[list['Account']] = relationship(
        'Account',
        secondary=AccountToTask,
        back_populates='completedTasks'
    )


class Wallet(Base):
    __tablename__ = 'wallets'

    id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, unique=True, index=True)
    coins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tickets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wallet_address: Mapped[str] = mapped_column(Text, nullable=True)
    wallet_type: Mapped[str] = mapped_column(String(255), nullable=True)

    user: Mapped['User'] = relationship('User', back_populates='wallet')
    reward: Mapped['Reward'] = relationship('Reward', back_populates='wallet')
    farm: Mapped['Farm'] = relationship('Farm', back_populates='Wallet')

    def __str__(self) -> str:
        return str(self.id)
    
        
class Reward(Base):
    __tablename__ = 'rewards'

    id: Mapped[int] = mapped_column(BigInteger, ForeignKey('wallets.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True)
    lastReward: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    coinsCount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ticketCount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    day: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    wallet: Mapped['Wallet'] = relationship('Wallet', back_populates='reward')

    def __str__(self) -> str:
        return str(self.id)
    

class Farm(Base):
    __tablename__ = 'farms'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(255), default='Process', nullable=False)
    wallet: Mapped[int] = mapped_column(BigInteger, ForeignKey('wallets.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, index=True)

    Wallet: Mapped['Wallet'] = relationship('Wallet', back_populates='farm')
    