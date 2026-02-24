from pydantic import BaseModel


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


class UserProfileUpdate(BaseModel):
    email: str
    name: str
    fullname: str
