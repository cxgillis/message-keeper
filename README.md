# README

## Overview

For my SEIS603 Fall 2024 final project, I have built an application that serves as a rudimentary messaging
system. This application consists of a REST API service that allows users to create messages addressed to different
users, retrieve a user’s messages, delete messages, and search messages based on basic fields like sender and
message body.

To power this service, I have leveraged the FastAPI framework to accept HTTP requests and use JSON for request and
response bodies. The application uses SQLite to store message information in a file-based database, and if desired
can persist the app data across application restarts. The application does basic user authorization using a username
and password provided in the requests, but is not meant to pass any rigorous security standards.

## Pre-requisites

Before running my applications some pre-requisites must be satisfied:
- Python 3.12+ (I developed and tested using Python 3.13)
- Required packages and compatible versions specified in the `requirements.txt` must be installed
- If executing with PyCharm, the project interpreter should be configured with an environment satisfying above
- Must have some way to execute HTTP requests and view responses
    - My examples will use `curl` but any tool supporting HTTP requests should be fine

## How to run my application and code examples

My application can be run in one of two ways:
- Directly from the terminal using this command:
    - `uvicorn main:app --reload`
- From within PyCharm by using the `Run 'Main.py'` button or option.

On startup the application will create an admin user and a guest user, along with some sample messages.
By default, the application will clear out any existing database file. However, if desired this can be
changed to persist any data between runs by commenting out the following lines in `main.py`
under the `lifespan` function:
- `os.remove('msg_keeper.db')` (currently line 18)
- `initial_db_load()` (currently line 20)

The application also requires requests provide basic authorization, which in our examples is handled by `curl` including
the `-u <username>:<password>` option. The request can also be configured to send a header having
username:password in base 64 encoded format as well (e.g. ), if that is preferred by the user.

## Application interaction examples and test requests/responses

The following is a sample list of application interactions demonstrating some of its capabilities. In each case we will
specify the user allowed to execute the request, and we are also providing `curl` the silent and show-error options
via the `-sS` switch to keep the output more readable. If we want prettier display of the JSON response, we could redirect
the response output to a utility like `jq` or also use a tool like Postman or Bruno to format data. For the below, the
response data is manually formatted to balance legibility and compactness.
NOTE: The presence and absence of trailing spaces is important, and incorrect usage will generate incorrect behavior.
Consult the following examples and/or the router code for guidance on when to include.

User-related Commands

- Query all users (allowed for both admin and user)
    command: curl -sS -u "admin:adminAdmin" -X GET "http://127.0.0.1:8000/users/"
    output:  [{"name":"admin","create_timestamp":"2024-12-01T00:00:00","enabled":true},
              {"name":"guest","create_timestamp":"2024-12-24T15:23:14","enabled":true}]

    command: curl -sS -u "guest:guest123" -X GET "http://127.0.0.1:8000/users/"
    output:  [{"name":"admin","create_timestamp":"2024-12-01T00:00:00","enabled":true},
              {"name":"guest","create_timestamp":"2024-12-24T15:23:14","enabled":true}]

- Query users using parameters (allowed for both admin and user)
    command: curl -sS -u "guest:guest123" -X GET "http://127.0.0.1:8000/users/?create_timestamp=2024-12-02"
    output:  [{"name":"guest","create_timestamp":"2024-12-24T15:23:14","enabled":true}]

- Query specific user by name (allowed for both admin and user)
    command: curl -sS -u "guest:guest123" -X GET "http://127.0.0.1:8000/users/guest"
    output:  {"name":"guest","create_timestamp":"2024-12-24T15:23:14","enabled":true}

- Add new user (allowed only for admin)
    command: curl -sS -u "admin:adminAdmin" -X POST -H 'content-type: application/json' \
                  -d '{"name":"chris","password":"test123"}' "http://127.0.0.1:8000/users/"
    output:  {"name":"chris","create_timestamp":"2024-12-24T15:45:39","enabled":true}

- Delete a user (allowed only for admin)
    command: curl -sS -u "admin:adminAdmin" -X DELETE "http://127.0.0.1:8000/users/chris"
    output:  {"detail":"User 'chris' successfully deleted."}

- Update a user e.g. password or enable/disable (allowed only for admin)
    command: curl -sS -u "admin:adminAdmin" -X PUT -H 'content-type: application/json' \                                                                                                   ─╯
                  -d '{"password":"test444","enabled":false}' "http://127.0.0.1:8000/users/chris"
    output:  {"name":"chris","create_timestamp":"2024-12-24T15:52:32","enabled":false}

Message-related Commands
- Query all messages, both inbox and outbox (allowed only for admin)
    command: curl -sS -u "admin:adminAdmin" -X GET "http://127.0.0.1:8000/messages/"
    output:  [{"body":"This is a sample message provided for testing. Use carefully!","id":1,"to_name":"guest",
               "inbox_outbox_f":"inbox","read_f":false,"mailbox_name":"admin","subject":"Sample Admin message 1 - Hi!",
               "from_name":"admin","create_timestamp":"2024-12-24T15:59:15"},
           ... (more messages) ...,
              {"body":"Very important announcement coming soon...","id":6,"to_name":"admin",
               "inbox_outbox_f":"outbox","read_f":true,"mailbox_name":"guest","subject":"Outgoing mail",
               "from_name":"guest","create_timestamp":"2024-12-24T15:59:15"}]

- Query all messages using parameters (allowed only for admin)
    command: curl -sS -u "admin:adminAdmin" -X GET "http://127.0.0.1:8000/messages/?mailbox_name=guest&body=dolorem"
    output:  [{"body":"Neque porro quisquam est qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit...",
               "id":4,"to_name":"admin","inbox_outbox_f":"inbox","read_f":false,"mailbox_name":"guest",
               "subject":"Sample Guest message 1 - Messages are fun","from_name":"guest","create_timestamp":"2024-12-24T15:59:15"}]

- Query specific messages in inbox or outbox (allowed only for admin)
    command: same as above, but just add `/inbox` or `/outbox` (no trailing /) after `/messages` to only search either

- Query all user messages in inbox or outbox (allowed for both admin and user, but non-admins can only view their own messages)
    command: curl -sS -u "guest:guest123" -X GET "http://127.0.0.1:8000/messages/inbox/guest"
        and  curl -sS -u "guest:guest123" -X GET "http://127.0.0.1:8000/messages/outbox/guest"
    output:  same list of messages response as previous examples

- Query specific message ID (allowed for both admin and user, but non-admins can only view their own messages)
    command: curl -sS -u "guest:guest123" -X GET "http://127.0.0.1:8000/messages/5"
    output:  {"to_name":"admin","subject":"Running out of subject line ideas","body":"","id":5,"mailbox_name":"guest",
              "from_name":"guest","create_timestamp":"2024-12-24T15:59:15","read_f":true}

- Send a message (allowed for all users)
    command: curl -sS -u "guest:guest123" -X POST -H 'content-type: application/json'\
                   -d '{"to_name":"chris","subject":"Greetings to Chris!",
                        "body":"I am very happy to see that this fancy new messaging app is working as expected :)"}' \
                   "http://127.0.0.1:8000/messages/"
    output:  echoes message response, and message now viewable by recipient e.g.
             curl -sS -u "chris:test123" -X GET "http://127.0.0.1:8000/messages/inbox/chris"                                                                                               ─╯
             [{"to_name":"chris","subject":"Greetings to Chris!",
             "body":"I am very happy to see that this fancy new messaging app is working as expected :)","id":7,
             "mailbox_name":"chris","from_name":"guest","create_timestamp":"2024-12-24T16:16:27","read_f":true}]

- Delete a message (allowed for both admin and user, but non-admins can only delete their own messages)
    command: curl -sS -u "chris:test123" -X DELETE "http://127.0.0.1:8000/messages/7"
    output:  {"detail":"Message '7' successfully deleted."}
