from fastapi import APIRouter
from models.User import UserPublic,UserCreate
from fastapi import status,HTTPException
from dependencies.dependencies import SessionDep
from sqlmodel import select
from models import User
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from models.token import Token
from security.security import hash_password,verify_password,create_access_token

router=APIRouter(prefix="/auth",tags=["auth"])

@router.post("/register",response_model=UserPublic,status_code=status.HTTP_201_CREATED)
def register(user_in:UserCreate,session:SessionDep):
    existing=session.exec(select(User).where(User.email==user_in.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User.model_validate(user_in, update={"hashed_password": hash_password(user_in.password)})
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))
