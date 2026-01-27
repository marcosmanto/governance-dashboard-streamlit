from datetime import date
from typing import Literal

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
