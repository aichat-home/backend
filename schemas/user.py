from datetime import datetime

from pydantic import BaseModel
from .task import CompletedTaskResponse


class UserBase(BaseModel):
    id: int
    last_name: str | None = None
    first_name: str | None = None
    username: str | None = None


class RefferAccountResponse(BaseModel):
    id: int
    user: UserBase


class AccountResponse(BaseModel):
    id: int
    age: int
    inviteCode: str
    heSeeWelcomeScreen: bool = False
    completedTasks: list[CompletedTaskResponse] = []
    reffers: list[RefferAccountResponse] = []


class RewardResponse(BaseModel):
    id: int
    coinsCount: int
    day: int


class FarmResponse(BaseModel):
    status: str
    createdAt: datetime | None = None


class WalletResponse(BaseModel):
    id: int
    coins: int
    reward: RewardResponse


class UserCreate(UserBase):
    inviteCode: str | None = None


class UserResponse(UserBase):
    account: AccountResponse | None = None
    wallet: WalletResponse | None = None
    taskRewardAmount: int = 0
    time_passed: int | None = None
    need_to_claim: bool = False
    current_farm_reward: float | None = None
    plus_every_second: float | None = None
    total_duration: int
    total_farm_reward: float | None = None


class UserCreateBody(BaseModel):
    isPremium: bool | None = False
    inviteCode: str | None = None


class RefferResponse(BaseModel):
    id: int
    earned_coins: int 
    user: UserBase


class GetOrCreate(BaseModel):
    id: int
    first_name: str
    day: int | None = None
    heSeeWelcomeScreen: bool = False
    age: int | None = None
    age_coins: int | None = None
    title: str | None = None
    percent : float | None = None


class SaveWallet(BaseModel):
    name: str
    address: str