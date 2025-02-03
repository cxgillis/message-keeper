from datetime import datetime

from fastapi import HTTPException, APIRouter, Depends
from sqlmodel import Session, select

from auth import get_current_user, get_admin_user
from db import get_db_session
from models import UserOutput, User, UserCreateInput, UserUpdateInput

router = APIRouter(prefix='/users')


@router.get("/", response_model=list[UserOutput])
def query_user_by_params(
        name: str | None = None,
        create_timestamp: datetime | None = None,
        enabled: bool | None = None,
        session: Session = Depends(get_db_session),
        curr_user: User = Depends(get_current_user)) -> list:
    """Return the list of users matching the query parameters, or all users if none provided"""
    sql = select(User)
    if name:
        sql = sql.where(User.name == name)
    if create_timestamp:
        sql = sql.where(User.create_timestamp >= create_timestamp)
    if enabled:
        sql = sql.where(User.enabled == enabled)
    return list(session.exec(sql).all())


@router.get('/{name}', response_model=UserOutput)
def query_user_by_name(name: str, session: Session = Depends(get_db_session),
                       curr_user: User = Depends(get_current_user)) -> User:
    """Return the user with the matching name, if exists"""
    statement = select(User).where(User.name == name)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"No user with {name=} found!")
    return user


@router.post('/', response_model=UserOutput, status_code=201)
def add_user(user: UserCreateInput, session: Session = Depends(get_db_session),
             admin_user: User = Depends(get_admin_user)) -> User:
    # Check if user already exists
    statement = select(User).where(User.name == user.name)
    existing_user = session.exec(statement).first()
    # If so, then return 200 already exists message
    if existing_user:
        raise HTTPException(status_code=200, detail=f"User '{user.name}' already exists, no changes made!")
    # Otherwise continue to create new user
    new_user = User(name=user.name, password=user.password,
                create_timestamp=datetime.now().replace(microsecond=0), enabled=True)
    session.add(new_user)
    session.commit()
    return new_user


@router.delete('/{name}')
def delete_user(name: str, session: Session = Depends(get_db_session),
                admin_user: User = Depends(get_admin_user)) -> dict:
    # Check if user exists
    statement = select(User).where(User.name == name)
    user = session.exec(statement).first()
    # If User indicated for deletion not found, return 404
    if not user:
        raise HTTPException(status_code=404, detail=f"No user with {name=} found!")
    # Found user, so proceed with deletion
    session.delete(user)
    session.commit()
    return {"detail": f"User '{name}' successfully deleted."}


@router.put('/{name}', response_model=UserOutput)
def update_user(name: str, user_input: UserUpdateInput, session: Session = Depends(get_db_session),
                admin_user: User = Depends(get_admin_user)) -> User:
    # Get existing user
    statement = select(User).where(User.name == name)
    existing_user = session.exec(statement).first()
    # If User indicated for update not found, return 404
    if not existing_user:
        raise HTTPException(status_code=404, detail=f"No user with {name=} found!")
    # Merge updated values into existing update
    user_data = user_input.model_dump(exclude_unset=True)
    existing_user.sqlmodel_update(user_data)
    # Update data in DB
    session.add(existing_user)
    session.commit()
    session.refresh(existing_user)
    return existing_user
