# Inbox: Microsoft Graph Client for Outlook Inboxes

`inbox` is a small Python library that reads emails and
attachments from a Microsoft Outlook inbox. It wraps the
parts of the Microsoft Graph Python SDK needed for this and
authenticates using a Microsoft Entra ID app registration
with application permissions (no signed-in user is
required).

For more information, refer to these Microsoft Learn
articles:

- [Build Python apps with Microsoft Graph and app-only authentication](https://learn.microsoft.com/en-us/graph/tutorials/python-app-only)
- [Add email capabilities to Python apps using Microsoft Graph](https://learn.microsoft.com/en-us/graph/tutorials/python-email)

## Requirements

- Python >= 3.13
- A Microsoft Entra ID app registration with the `Mail.Read`
  application permission granted admin consent for the
  target mailbox

## Installation

```powershell
uv add inbox
```

To work on the library itself:

```powershell
git clone <this-repo>
cd pod/backend/inbox
uv sync
```

## Project layout

```
src/inbox/
├── __init__.py     OutlookInbox
├── credentials.py  .env credential loading
└── inbox.py        Microsoft Graph client (OutlookInbox)
```

## Configuration

Credentials are read from environment variables (loaded from
a `.env` file in the working directory via `python-dotenv`):

```dotenv
OUTLOOK_INBOX_EMAIL_ADDRESS = ""
OUTLOOK_INBOX_CLIENT_ID     = ""
OUTLOOK_INBOX_TENANT_ID     = ""
OUTLOOK_INBOX_CLIENT_SECRET = ""
```

`.env` is git-ignored. The `OutlookInbox` constructor also
accepts these four values directly, so you can source them
from a secrets manager instead of a `.env` file.

## Usage

### Reading emails

`OutlookInbox` connects to the mailbox given by
`OUTLOOK_INBOX_EMAIL_ADDRESS` and returns messages as Microsoft
Graph `Message` objects.

```python
from inbox import OutlookInbox

inbox = OutlookInbox()

emails = await inbox.get_emails()

for email in emails:
    print(email.subject, email.received_date_time)
```

You may also pass credentials explicitly instead of relying on
the default ones in `.env`:

```python
inbox = OutlookInbox(
    email_address="reporting@example.com",
    client_id="...",
    tenant_id="...",
    client_secret="...",
)
```

### Reading attachments

```python
attachments = await inbox.get_attachments(email)

for attachment in attachments:
    content_bytes = inbox.read_attachment(attachment)
```

`get_attachments` only returns file attachments (not
SharePoint links), since only file attachments carry the
`content_bytes` field that `read_attachment` reads.

### Saving attachments to disk

```python
from pathlib import Path

out_path = Path("attachments")
out_path.mkdir(parents=True, exist_ok=True)

for attachment in attachments:
    inbox.save_attachment(attachment, out_path)
```

Errors surface as exceptions rather than silent failures:

- `credentials.MissingCredentials`: one or more of the four
  required environment variables is not set and no credentials
  were passed to the constructor
- `ValueError`: no emails were found, or an email is missing
  its `id` field
- `TypeError`: an attachment is missing its `content_bytes` or
  `name` field
