from pydantic import BaseModel



class TaskResponse(BaseModel):
    id: int
    title: str
    amountType: str
    icon: str
    type: str
    amount: int
    link: str


class TaskCheck(BaseModel):
    task_id: int


class CompletedTaskResponse(BaseModel):
    id: int
    title: str
    amountType: str
    amount: int
    icon: str
    type: str

