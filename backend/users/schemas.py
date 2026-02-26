from pydantic import BaseModel

from backend.models import Role


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


class UserProfileUpdate(BaseModel):
    email: str
    name: str
    fullname: str


class RoleRequestIn(BaseModel):
    requested_role: Role
    justification: str
