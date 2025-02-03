from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, col

from auth import get_admin_user, get_current_user
from db import get_db_session
from models import MessageOutput, User, Message, MessageInput

router = APIRouter(prefix='/messages')


# Function containing the share search logic for both inbox and outbox
def query_message_by_params(
        session: Session,
        mailbox_name: str | None = None,
        create_timestamp: datetime | None = None,
        subject: str | None = None,
        body: str | None = None,
        inbox_outbox_f: str = None,
        read_f: bool | None = None,
        ) -> list:
    """Return the list of messages matching the query parameters, or all messages if none provided"""
    sql = select(Message)
    # Check which optional parameters (if any) are set and apply if applicable
    if mailbox_name:
        sql = sql.where(Message.mailbox_name == mailbox_name)
    if inbox_outbox_f:
        sql = sql.where(Message.inbox_outbox_f == inbox_outbox_f)
    if read_f:
        sql = sql.where(Message.read_f == read_f)
    if create_timestamp:
        sql = sql.where(Message.create_timestamp >= create_timestamp)
    if subject:
        sql = sql.where(col(Message.subject).icontains(subject))
    if body:
        sql = sql.where(col(Message.body).icontains(body))
    return list(session.exec(sql).all())


@router.get("/", response_model=list[Message])
def query_user_by_params(
        mailbox_name: str | None = None,
        create_timestamp: datetime | None = None,
        subject: str | None = None,
        body: str | None = None,
        inbox_outbox_f: str = None,
        read_f: bool = None,
        session: Session = Depends(get_db_session),
        curr_user: User = Depends(get_admin_user)) -> list:
    """Return the list of users matching the query parameters, or all users if none provided"""
    # Call the shared query function for both inboxes and outboxes
    return query_message_by_params(session, mailbox_name, create_timestamp, subject, body, inbox_outbox_f, read_f)


@router.get("/inbox", response_model=list[MessageOutput])
def query_inbox_by_params(
        mailbox_name: str | None = None,
        create_timestamp: datetime | None = None,
        subject: str | None = None,
        body: str | None = None,
        read_f: bool = None,
        session: Session = Depends(get_db_session),
        admin_user: User = Depends(get_admin_user)) -> list:
    """Return the list of messages matching the query parameters, or all messages if none provided"""
    # Call the shared query function for just inboxes
    return query_message_by_params(session, mailbox_name, create_timestamp, subject, body, 'inbox', read_f)


@router.get("/inbox/{name}", response_model=list[MessageOutput])
def query_inbox_by_name(name: str, session: Session = Depends(get_db_session),
                        curr_user: User = Depends(get_current_user)) -> list:
    """Return all inbox messages for the specified user"""
    if curr_user.name != 'admin' and curr_user.name != name:
        raise HTTPException(status_code=403, detail=f"User '{curr_user.name}' is not authorized to view this inbox!")
    # Get the result list and then set the read flag for all previously unread messages:
    result_list = query_message_by_params(session=session, mailbox_name=name, inbox_outbox_f='inbox')
    for msg in result_list:
        if not msg.read_f:
            msg.read_f = True
            session.add(msg)
            session.commit()
    return result_list


@router.get("/outbox", response_model=list[MessageOutput])
def query_outbox_by_params(
        mailbox_name: str | None = None,
        create_timestamp: datetime | None = None,
        subject: str | None = None,
        body: str | None = None,
        session: Session = Depends(get_db_session),
        admin_user: User = Depends(get_admin_user)) -> list:
    """Return the list of messages matching the query parameters, or all messages if none provided"""
    # Call the shared query function for just outboxes
    return query_message_by_params(session, mailbox_name, create_timestamp, subject, body, 'outbox', None)


@router.get("/outbox/{name}", response_model=list[MessageOutput])
def query_inbox_by_name(name: str, session: Session = Depends(get_db_session),
                        curr_user: User = Depends(get_current_user)) -> list:
    """Return all outbox messages for the specified user"""
    if curr_user.name != 'admin' and curr_user.name != name:
        raise HTTPException(status_code=403, detail=f"User '{curr_user.name}' is not authorized to view this outbox!")
    return query_message_by_params(session=session, mailbox_name=name, inbox_outbox_f='outbox')


@router.get('/{id}', response_model=MessageOutput)
def query_message_by_id(id: int, session: Session = Depends(get_db_session),
                       curr_user: User = Depends(get_current_user)) -> Message:
    """Return the user with the matching name, if exists"""
    statement = select(Message).where(Message.id == id)
    msg = session.exec(statement).first()
    # Check first if message ID is valid, and then ensure user permissions are appropriate
    if not msg:
        raise HTTPException(status_code=404, detail=f"No message with {id=} found.")
    if curr_user.name != 'admin' and msg.mailbox_name != curr_user.name:
        raise HTTPException(status_code=403, detail=f"User '{curr_user.name}' is not authorized to view this message!")
    # If message was previously unread, then set the read flag to True
    if not msg.read_f:
        msg.read_f = True
        session.add(msg)
        session.commit()
    return msg


@router.post("/", response_model=MessageOutput, status_code=201)
def send_message(msg: MessageInput, session: Session = Depends(get_db_session),
                 curr_user: User = Depends(get_current_user)):
    # Confirm recipient is an existing user
    recipient_check = select(User).where(User.name == msg.to_name)
    recipient = session.exec(recipient_check).first()
    if not recipient:
        raise HTTPException(status_code=404, detail=f"Message recipient '{msg.to_name}' not found!")
    # Create new Message object
    inbox_msg = Message(mailbox_name=msg.to_name, inbox_outbox_f='inbox', to_name=msg.to_name,
                        from_name=curr_user.name, subject=msg.subject, body=msg.body)
    outbox_msg = Message(mailbox_name=curr_user.name, inbox_outbox_f='outbox', to_name=msg.to_name,
                        from_name=curr_user.name, subject=msg.subject, body=msg.body, read_f=True)
    session.add(inbox_msg)
    session.add(outbox_msg)
    session.commit()
    return inbox_msg


@router.delete('/{id}')
def delete_user(id: int, session: Session = Depends(get_db_session),
                curr_user: User = Depends(get_current_user)) -> dict:
    # Check if message exists
    statement = select(Message).where(Message.id == id)
    msg = session.exec(statement).first()
    # If Message indicated for deletion not found, return 404
    if not msg:
        raise HTTPException(status_code=404, detail=f"No message with {id=} found!")
    # Ensure user permissions are appropriate
    if curr_user.name != 'admin' and msg.mailbox_name != curr_user.name:
        raise HTTPException(status_code=403, detail=f"User '{curr_user.name}' is not authorized to delete this message!")
    # Found user, so proceed with deletion
    session.delete(msg)
    session.commit()
    return {"detail": f"Message '{id}' successfully deleted."}
