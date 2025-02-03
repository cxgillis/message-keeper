from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class UserBaseInput(SQLModel):
    name: str

class UserCreateInput(UserBaseInput):
    password: str

class User(UserCreateInput, table=True):
    name: str = Field(primary_key=True)
    create_timestamp: datetime | None = Field(default_factory=lambda: datetime.now().replace(microsecond=0))
    enabled: bool

class UserUpdateInput(UserCreateInput):
    name: ClassVar[str]
    create_timestamp: ClassVar[datetime]
    password: str | None = None
    enabled: bool | None = None

class UserOutput(User):
    password: ClassVar[str]


class MessageInput(SQLModel):
    to_name: str
    subject: str
    body: str | None = None

class Message(MessageInput, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mailbox_name: str = Field(foreign_key="user.name")
    to_name: str = Field(foreign_key="user.name")
    from_name: str = Field(foreign_key="user.name")
    inbox_outbox_f: str
    create_timestamp: datetime | None = Field(default_factory=lambda: datetime.now().replace(microsecond=0))
    read_f: bool = Field(default=False)

class MessageOutput(Message):
    inbox_outbox_f: ClassVar[str]
