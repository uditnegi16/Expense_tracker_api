from sqlmodel import SQLModel,Field
from sqlalchemy import UniqueConstraint

class CategoryBase(SQLModel):
    name:str=Field(min_length=1,max_length=50)
class Category(CategoryBase,table=True):
    __table_args__=(UniqueConstraint("user_id","name"),)
    id:int|None=Field(default=None,primary_key=True)
    user_id:int=Field(foreign_key="user.id",index=True)
class CategoryCreate(CategoryBase):
    pass
class CategoryUpdate(SQLModel):
    name:str|None=Field(default=None,min_length=1,max_length=50)
class CategoryPublic(CategoryBase):
    id:int

    
    
    