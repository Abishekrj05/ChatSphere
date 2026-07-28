# API

All endpoints require an authenticated Django session.

## Conversations

`GET /api/conversations/`

## Messages

`GET /api/conversations/<conversation_id>/messages/`

`POST /api/conversations/<conversation_id>/messages/`

```json
{
  "content": "Hello from the REST API"
}
```

The message endpoint also accepts multipart form data with optional `image`,
`document`, and `voice_note` files. A request must include text or at least one
attachment.

## AI assistant

`POST /ai/generate/`

```json
{
  "message": "Explain Django Channels"
}
```
