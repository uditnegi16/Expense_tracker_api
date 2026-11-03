from fastapi import APIRouter,HTTPException,status
from models.User import User
from models.Category import Category
from sqlmodel import select
from models.Expense import Expense,ExpensePublic,ExpenseCreate,ExpenseUpdate
from sqlmodel import Session
from dependencies.dependencies import SessionDep,CurrentUser

from datetime import date
from decimal import Decimal
from fastapi import Query

router=APIRouter(prefix="/expenses",tags=["expenses"])

def check_category_owned(session:Session,user:User,category_id:int):
    category=session.exec(select(Category).where(Category.id==category_id)).first()
    if category is None or user.id!=category.user_id:
        raise HTTPException(status_code=400,detail="Invalid Category")
    
def get_owned_expense(session:Session,current_user:User,expense_id:int):
    expense=session.get(Expense,expense_id)
    if expense is None or expense.user_id!=current_user.id:
        raise HTTPException(status_code=404,detail="expense not found")
    return expense


@router.post("",response_model=ExpensePublic,status_code=status.HTTP_201_CREATED)
def create_expense(expense_in:ExpenseCreate,session:SessionDep,user:CurrentUser):
    check_category_owned(session,user,expense_in.category_id)
    expense=Expense.model_validate(expense_in,update={"user_id":user.id})
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense

@router.get("/{expense_id}",response_model=ExpensePublic)
def get_expense(expense_id:int,session:SessionDep,user:CurrentUser):
    return get_owned_expense(session,user,expense_id)

@router.patch("/{expense_id}",response_model=ExpensePublic)
def update_expense(
    expense_id:int,
    expense_in:ExpenseUpdate,
    session:SessionDep,
    user:CurrentUser):
    expense=get_owned_expense(session,user,expense_id)
    data=expense_in.model_dump(exclude_unset=True)
    for field in ("amount", "spent_on", "category_id"):
        if field in data and data[field] is None:
            raise HTTPException(status_code=422, detail=f"{field} cannot be null")
    if "category_id" in data:
        check_category_owned(session,user,data["category_id"])
    expense.sqlmodel_update(data)
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, session: SessionDep, user: CurrentUser):
    expense = get_owned_expense(session, user, expense_id)
    session.delete(expense)
    session.commit()


@router.get("", response_model=list[ExpensePublic])
def list_expenses(
    session: SessionDep,
    user: CurrentUser,
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: int | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(status_code=422, detail="min_amount cannot be greater than max_amount")

    statement = select(Expense).where(Expense.user_id == user.id)

    if start_date is not None:
        statement = statement.where(Expense.spent_on >= start_date)
    if end_date is not None:
        statement = statement.where(Expense.spent_on <= end_date)
    if category_id is not None:
        statement = statement.where(Expense.category_id == category_id)
    if min_amount is not None:
        statement = statement.where(Expense.amount >= min_amount)
    if max_amount is not None:
        statement = statement.where(Expense.amount <= max_amount)

    statement = (
        statement.order_by(Expense.spent_on.desc(), Expense.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return session.exec(statement).all()