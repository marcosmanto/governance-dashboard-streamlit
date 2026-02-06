from pydantic import BaseModel


class ForgotPasswordIn(BaseModel):
    username: str


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str
