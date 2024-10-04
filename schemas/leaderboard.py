from pydantic import BaseModel


class LeaderboardResponse(BaseModel):
    id: int
    username: str
    coins: int


class LeaderboardFullResponse(BaseModel):
    leaderboard: list[LeaderboardResponse]
    user_rank: int | None = None
