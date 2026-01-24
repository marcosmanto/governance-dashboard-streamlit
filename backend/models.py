from datetime import date

from pydantic import BaseModel, Field


class Registro(BaseModel):
    data: date
    categoria: str = Field(min_length=1)
    valor: int


class RegistroOut(Registro):
    id: int
