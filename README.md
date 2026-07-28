# ChatSphere — Real-Time Chat Application

A Django real-time chat project using Django Channels, WebSockets, Django REST
Framework, optional Redis, file sharing, notifications, profiles, group chats,
and an optional Groq AI assistant.

## Included features

- Registration, login, logout, profiles, avatars, bios, and last-seen state
- Reusable private conversations and member-selected group conversations
- Persisted real-time messages, typing indicators, and unread counters
- Message replies, edits, soft deletion, emoji reactions, and pinned messages
- Image, document, and audio attachment uploads with size validation
- Persisted in-app notifications plus live browser notification updates
- Cross-conversation message search with participant-only visibility
- Group-owner controls for renaming, membership management, and deletion
- Safe group-leave flow for regular members
- Authenticated REST endpoints for conversations and messages
- An authenticated AI assistant screen backed by Groq
- Django admin screens and automated workflow tests

## Windows setup

```powershell
cd chat_application
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py makemigrations accounts chat notifications
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Real-time testing

Register one account in a normal browser window and another account in an
incognito window. Start a private conversation and send messages from both
windows.

## Redis

Development works without Redis because `USE_REDIS=False`.

To use Redis:

```env
USE_REDIS=True
REDIS_URL=redis://127.0.0.1:6379/0
```

Then run:

```powershell
docker compose -f redis/docker-compose.yml up -d
python manage.py runserver
```

## AI assistant

Add a Groq API key to `.env`:

```env
GROQ_API_KEY=your_key_here
```

The endpoint is `POST /ai/generate/`.
The browser interface is available at `/ai/`.

If no key is configured, the rest of the application still works and the AI
screen displays a configuration error when a prompt is submitted.

## Tests

```powershell
python manage.py check
python manage.py test
```

## Production notes

Set a strong `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=False`, configure
`DJANGO_ALLOWED_HOSTS`, use Redis for the channel layer, and serve static/media
files through your web server or object storage. SQLite and the in-memory
channel layer are intended for local development.
