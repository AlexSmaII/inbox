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
├── __init__.py     OutlookInbox, IndexedSearch
├── credentials.py  .env credential loading
├── index.py        Search by content (IndexedSearch)
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

## Searching by content

A mailbox search narrows messages by their wording. Microsoft
Graph can be asked for the messages whose subject contains a
term, and `get_emails` passes a `search_term` straight through
to it. That answers a question about how a subject was worded
rather than about what the message holds, so a reply quoting the
term is returned, an automatic reply carrying it is returned,
and a message whose sender worded the subject differently is
missed.

`IndexedSearch` searches by what a message is instead. It takes
three parts. A classifier decides what one message is and
returns a `MessageLabel` saying so. An index remembers that
decision against the message it was made about. `IndexedSearch`
asks the mailbox for candidates using only the things the
mailbox answers cheaply and exactly, reads the index for the
candidates already decided, puts the rest to the classifier, and
writes every new decision back. A message is therefore
classified once however often the mailbox is searched, which is
what makes a classifier costly enough to be worth caching usable
at all.

The label is a string the caller chooses. Nothing in the package
knows what any of them mean, so the same machinery serves a
mailbox sorting scanned forms and a mailbox sorting invoices.
The one label the package reserves is `UNKNOWN`, which a
classifier returns when it could not decide. It is written to
the index so the attempt is visible, and it is read as
undecided, so the message is put to the classifier again on the
next search rather than being passed over for good.

### Writing a classifier

A classifier offers a name and a `label` method. The mailbox is
passed in so the classifier can read whatever the message itself
does not carry, such as its attachments.

```python
from inbox import MessageLabel, OutlookInbox
from msgraph.generated.models.message import Message


class InvoiceClassifier:
    name = "filename-rule"

    async def label(
        self,
        inbox: OutlookInbox,
        message: Message,
    ) -> MessageLabel:
        attachments = await inbox.list_attachments(message)
        found = any("invoice" in (a.name or "").lower() for a in attachments)

        return MessageLabel(
            message_id=message.id,
            label="invoice" if found else "other",
            decided_by=self.name,
        )
```

A classifier which raises is recorded as `UNKNOWN` rather than
allowed to end the search, so one unreadable message does not
stop the rest being found.

### Running a search

```python
from inbox import IndexedSearch, OutlookInbox

search = IndexedSearch(
    inbox=OutlookInbox(),
    classifier=InvoiceClassifier(),
)

emails = await search.search("invoice", limit=10)
```

The mailbox holds wanted and unwanted messages mixed together
and cannot be asked to return only one of them, so the search
reads it a page at a time until `limit` messages carrying the
label have been found. A caller which leaves a message where it
is, rather than marking it as read or moving it, accumulates
unwanted messages ahead of the wanted ones, which is why one
page is not enough. `max_candidates` bounds how far it reads,
and `limit` left out returns everything found within that bound.

### Keeping decisions

The default index is `MemoryIndex`, which holds decisions for
the life of the process. A search repeated in one process
classifies nothing twice and a restart classifies everything
again, which is enough for a script and not enough for a
service.

A service supplies its own index, because where decisions are
kept is a question about that deployment rather than about the
mailbox. An index offers two methods, `labels` for reading a
batch of identifiers and `remember` for writing one decision,
and anything which offers both satisfies `MessageIndex`.

```python
search = IndexedSearch(
    inbox=OutlookInbox(),
    classifier=InvoiceClassifier(),
    index=YourDatabaseIndex(),
)
```
