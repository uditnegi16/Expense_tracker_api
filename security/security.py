from pwdlib import PasswordHash
password_hash=PasswordHash.recommended()


from datetime import datetime ,timedelta,timezone

import jwt
from jwt.exceptions import InvalidTokenError
from config.config import settings

def create_access_token(user_id:int)->str:
    expire=datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_expire_minutes)
    payload={"sub":str(user_id),"exp":expire}
    return jwt.encode(payload,settings.secret_key,algorithm=settings.algorithm)

def decode_access_token(token:str)->int|None:
    try:
        payload=jwt.decode(token,settings.secret_key,settings.algorithm)
    except InvalidTokenError:
        return None
    sub=payload.get("sub")
    return int(sub) if sub is not None else None


def hash_password(password:str)->str:
    return password_hash.hash(password)
def verify_password(plain_password:str,hashed_password:str)->bool:
    return password_hash.verify(plain_password,hashed_password)
