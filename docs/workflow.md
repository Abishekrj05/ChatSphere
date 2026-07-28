# Workflow

1. A user registers or logs in.
2. The dashboard loads private and group conversations.
3. Starting a private chat creates or reuses a conversation.
4. The browser opens a WebSocket connection.
5. ASGI routes the connection to the chat consumer.
6. The consumer verifies that the user belongs to the conversation.
7. New messages are stored in the database.
8. The channel layer broadcasts messages to connected participants.
9. The notification consumer pushes browser notifications.
10. Typing events are broadcast without being stored.
11. Attachment messages are accepted over an authenticated multipart endpoint
    and then broadcast to the same conversation WebSocket group.
12. Each recipient receives a persisted notification and a live notification
    event.
13. Opening a conversation marks its incoming messages and notifications read.
14. Authorized message edits, deletion, reactions and pin changes are broadcast
    to every connected participant.
15. Group owners manage membership and destructive group actions; regular
    members may leave without affecting the remaining conversation.
