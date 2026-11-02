from sqlmodel import SQLModel,Field
from datetime import datetime
from sqlalchemy import DateTime
from datetime import timezone
from pydantic import EmailStr

class UserBase(SQLModel):
    email: EmailStr=Field(index=True,unique=True,max_length=255)
    fullname:str|None=Field(default=None,max_length=100)

class User(UserBase,table=True):
    id:int|None=Field(default=None,primary_key=True)
    hashed_password:str
    created_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc),sa_type=DateTime(timezone=True))
class UserCreate(UserBase):
    password:str=Field(min_length=8,max_length=128)
class UserPublic(UserBase):
    id:int
     
    