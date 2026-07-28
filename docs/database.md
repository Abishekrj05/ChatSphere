# Database

## Profile

One-to-one extension of Django User.

Fields: avatar, bio, is_online and last_seen.

## Conversation

Stores private and group conversations.

Fields: name, is_group, participants, created_by and timestamps.

## Message

Stores message content, sender, conversation, images, documents, voice notes,
read state and timestamps.

## Notification

Stores recipient notifications related to conversations.
