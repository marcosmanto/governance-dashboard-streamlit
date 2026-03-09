from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["reader", "editor", "admin"]


class User(BaseModel):
    username: str
    role: Role
    email: str | None = None
    name: str | None = None
    fullname: str | None = None
    avatar_path: str | None = None
    mfa_enabled: bool = False


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
    user: dict | None = None
    must_change_password: bool = False


class UserContext(BaseModel):
    username: str
    role: str
    session_id: str
    must_change_password: bool = False
    is_active: bool = True
    created_at: Optional[str] = None
    password_expiring_soon: bool = False
    password_days_remaining: Optional[int] = None
