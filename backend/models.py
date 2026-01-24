from datetime import date

from pydantic import BaseModel, Field


class RegistroIn(BaseModel):
    data: date
    categoria: str = Field(min_length=1)
    valor: int


class RegistroOut(RegistroIn):
    id: int
