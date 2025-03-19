from sqlalchemy import Column, Integer, String, Boolean ,Enum
from database import Base
import enum
class UserRole(str,enum.Enum):
    admin="admin"
    user="user"

class User(Base):
    __tablename__="users"
    id=Column(Integer, primary_key=True,index=True)
    name=Column(String, nullable=False)
    username=Column(String, nullable=False, unique=True)
    email=Column(String,unique=True, nullable=False)
    hashed_password=Column(String,nullable=False)
    is_active=Column(Boolean, default=True)
    role=Column(Enum(UserRole,default=UserRole.user))