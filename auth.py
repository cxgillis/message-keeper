from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session, select

from db import get_db_session
from models import User

security = HTTPBasic()


def verify_admin_user(user: User) -> bool:
    """Check if the password user matches the designated admin user, return True/False."""
    return user.name == 'admin'


def get_current_user(credentials: HTTPBasicCredentials = Depends(security),
                     session: Session = Depends(get_db_session)) -> User:
    """Check if user exists in the system and is currently enabled, return User object if so."""
    statement = select(User).where(User.name == credentials.username and User.password == credentials.password)
    validated_user = session.exec(statement).first()
    if validated_user and validated_user.enabled:
        return validated_user
    elif validated_user:
        raise HTTPException(status_code=401, detail=f"This user is no longer active!")
    else:
        raise HTTPException(status_code=401, detail=f"Invalid Username or Password!")


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """Check if the calling user has been designated as the admin user, return User object if so."""
    if verify_admin_user(user):
        return user
    else:
        raise HTTPException(status_code=401, detail=f"Not an authorized admin user!")
