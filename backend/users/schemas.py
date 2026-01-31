from pydantic import BaseModel


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str
