from typing import Annotated
from sqlmodel import Session
from fastapi import Depends,HTTPException,status
from data.data import get_session
from fastapi.security import OAuth2PasswordBearer
from models import User
from security.security import decode_access_token
SessionDep=Annotated[Session,Depends(get_session)]
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token:Annotated[str,Depends(oauth2_scheme)],
    session:SessionDep,
)->User:
    credential_error=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"},
    )
    user_id=decode_access_token(token)
    if user_id  is None:
        raise credential_error
    user=session.get(User,user_id)
    if user is None:
        raise credential_error
    return user

CurrentUser=Annotated[User,Depends(get_current_user)]