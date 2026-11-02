from sqlmodel import SQLModel,Field
from datetime import date,datetime,timezone
from decimal import Decimal
from sqlalchemy import DateTime
class ExpenseBase(SQLModel):
    amount:Decimal=Field(max_digits=10,decimal_places=2,gt=0)
    description:str|None=Field(default=None,max_length=255)
    spent_on:date=Field(index=True)
    category_id:int=Field(foreign_key="category.id",index=True)
    
class Expense(ExpenseBase,table=True):
    id:int|None=Field(default=None,primary_key=True)
    user_id:int=Field(foreign_key="user.id",index=True)
    created_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc),sa_type=DateTime(timezone=True))
    
class ExpenseCreate(ExpenseBase):
    pass
class ExpenseUpdate(SQLModel):
    amount:Decimal|None=Field(default=None,max_digits=10,decimal_places=2,gt=0)
    description:str|None=Field(default=None,max_length=255)
    spent_on:date|None=Field(default=None)
    category_id:int|None=Field(default=None)
        
class ExpensePublic(ExpenseBase):
    id:int
    created_at:datetime
    