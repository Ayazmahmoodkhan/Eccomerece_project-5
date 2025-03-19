from pydantic import BaseModel, EmailStr, Field
from enum import Enum

class UserRoleEnum(str,Enum):
    admin="admin"
    user="user"
class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    username: str = Field(..., min_length=3, max_length=25)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=20)
    confirm_password: str = Field(..., min_length=6, max_length=20)
    role: UserRoleEnum=UserRoleEnum.user

class UserLogin(BaseModel):
    login:str
    password:str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str