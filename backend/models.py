from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["reader", "editor", "admin"]


class User(BaseModel):
    username: str
    role: Role


class RegistroIn(BaseModel):
    data: date
    categoria: str = Field(min_length=1)
    valor: int


class RegistroOut(RegistroIn):
    id: int


class AuditoriaOut(BaseModel):
    id: int
    timestamp: str
    username: str
    role: str
    action: str
    resource: str
    resource_id: Optional[int]
    payload_before: Optional[str]
    payload_after: Optional[str]
    endpoint: str
    method: str


class UserLoginOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserContext(BaseModel):
    username: str
    role: str
    session_id: str
