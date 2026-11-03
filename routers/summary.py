from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import func
from sqlmodel import SQLModel, select

from dependencies.dependencies import SessionDep, CurrentUser
from models.Category import Category
from models.Expense import Expense

router = APIRouter(prefix="/summary", tags=["summary"])


class MonthlyTotal(SQLModel):
    year: int
    month: int
    total: Decimal


class CategoryTotal(SQLModel):
    category_id: int
    category_name: str
    total: Decimal
    percent: float


@router.get("/monthly", response_model=list[MonthlyTotal])
def monthly_summary(session: SessionDep, user: CurrentUser):
    year = func.extract("year", Expense.spent_on)
    month = func.extract("month", Expense.spent_on)
    statement = (
        select(year.label("year"), month.label("month"), func.sum(Expense.amount).label("total"))
        .where(Expense.user_id == user.id)
        .group_by(year, month)
        .order_by(year, month)
    )
    rows = session.exec(statement).all()
    return [MonthlyTotal(year=int(r.year), month=int(r.month), total=r.total) for r in rows]


@router.get("/by-category", response_model=list[CategoryTotal])
def category_summary(session: SessionDep, user: CurrentUser):
    total = func.sum(Expense.amount)
    statement = (
        select(Category.id, Category.name, total.label("total"))
        .join(Expense, Expense.category_id == Category.id)
        .where(Expense.user_id == user.id)
        .group_by(Category.id, Category.name)
        .order_by(total.desc())
    )
    rows = session.exec(statement).all()
    grand_total = sum(r.total for r in rows)
    return [
        CategoryTotal(
            category_id=r.id,
            category_name=r.name,
            total=r.total,
            percent=round(float(r.total / grand_total * 100), 2),
        )
        for r in rows
    ]