# Chris Gillis
# SEIS 603-01 Final Project Fall 2024
# Eric V. Level
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqlmodel import SQLModel

from db import engine, initial_db_load
from routers import users, messages


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Purge the SQLite DB file to allow fresh testing, can comment this line to persist between runs
    os.remove('msg_keeper.db')
    SQLModel.metadata.create_all(engine)
    initial_db_load()
    yield


app = FastAPI(title='Message Keeper', lifespan=lifespan)
app.include_router(users.router)
app.include_router(messages.router)


@app.get('/')
def welcome():
    """Return a friendly welcome message."""
    return {'message': 'Welcome to the Message Keeper service! Please refer to http://localhost:8000/docs '
                       'for supported endpoints and methods.'}


# This is to enable execution and debugging in PyCharm
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
