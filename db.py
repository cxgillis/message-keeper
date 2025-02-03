from datetime import datetime

from sqlmodel import create_engine, Session

from models import User, Message

engine = create_engine(
    'sqlite:///msg_keeper.db',
    connect_args={'check_same_thread': False}, # Need for SQLite
    echo=True # Adding logging for debugging
)


def get_db_session():
    with Session(engine) as session:
        yield session


# Seed the DB with some default users and messages
def initial_db_load():
    user_admin = User(name='admin', password='adminAdmin', create_timestamp=datetime.strptime('2024-12-01', '%Y-%m-%d'),
                  enabled=True)
    user_guest = User(name='guest', password='guest123', enabled=True)
    message_adm_1 = Message(mailbox_name='admin', inbox_outbox_f='inbox', to_name='guest', from_name='admin',
                            subject='Sample Admin message 1 - Hi!',
                            body='This is a sample message provided for testing. Use carefully!')
    message_adm_2 = Message(mailbox_name='admin', inbox_outbox_f='inbox', to_name='guest', from_name='admin',
                            subject='Sample Admin message 2 - Still here?',
                            body='Yet another friendly message to the admin. Make sure you do your homework.')
    message_adm_3 = Message(mailbox_name='admin', inbox_outbox_f='outbox', to_name='guest', from_name='admin',
                            subject='Sending messages for fun',
                            body='Will anyone ever read this? Not likely by choice.',
                            read_f=True)
    message_gst_1 = Message(mailbox_name='guest', inbox_outbox_f='inbox', to_name='admin', from_name='guest',
                            subject='Sample Guest message 1 - Messages are fun',
                            body='Neque porro quisquam est qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit...')
    message_gst_2 = Message(mailbox_name='guest', inbox_outbox_f='inbox', to_name='admin', from_name='guest',
                            subject='Running out of subject line ideas',
                            body='')
    message_gst_3 = Message(mailbox_name='guest', inbox_outbox_f='outbox', to_name='admin', from_name='guest',
                            subject='Outgoing mail',
                            body='Very important announcement coming soon...',
                            read_f=True)
    with Session(engine) as session:
        session.add(user_admin)
        session.add(user_guest)
        session.add(message_adm_1)
        session.add(message_adm_2)
        session.add(message_adm_3)
        session.add(message_gst_1)
        session.add(message_gst_2)
        session.add(message_gst_3)
        session.commit()
