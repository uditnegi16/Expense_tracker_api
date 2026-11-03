from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from dependencies.dependencies import SessionDep, CurrentUser
from models.User import User
from models.Category import Category, CategoryCreate, CategoryUpdate, CategoryPublic

router = APIRouter(prefix="/categories", tags=["categories"])


def get_owned_category(session: Session, user: User, category_id: int) -> Category:
    category = session.get(Category, category_id)
    if category is None or category.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(category_in: CategoryCreate, session: SessionDep, user: CurrentUser):
    category = Category.model_validate(category_in, update={"user_id": user.id})
    session.add(category)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    session.refresh(category)
    return category


@router.get("", response_model=list[CategoryPublic])
def list_categories(session: SessionDep, user: CurrentUser):
    statement = select(Category).where(Category.user_id == user.id).order_by(Category.name)
    return session.exec(statement).all()


@router.get("/{category_id}", response_model=CategoryPublic)
def get_category(category_id: int, session: SessionDep, user: CurrentUser):
    return get_owned_category(session, user, category_id)


@router.patch("/{category_id}", response_model=CategoryPublic)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    session: SessionDep,
    user: CurrentUser,
):
    category = get_owned_category(session, user, category_id)
    category.sqlmodel_update(category_in.model_dump(exclude_unset=True))
    session.add(category)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    session.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, session: SessionDep, user: CurrentUser):
    category = get_owned_category(session, user, category_id)
    session.delete(category)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Category still has expenses")