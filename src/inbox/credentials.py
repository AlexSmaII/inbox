"""
Simple utility to load values from .env
and give descriptive errors on failure.
"""

import os

from dotenv import load_dotenv

load_dotenv()

OUTLOOK_INBOX = [
    "OUTLOOK_INBOX_EMAIL_ADDRESS",
    "OUTLOOK_INBOX_CLIENT_ID",
    "OUTLOOK_INBOX_TENANT_ID",
    "OUTLOOK_INBOX_CLIENT_SECRET"
]

class MissingCredentials(Exception): pass

def _load_env_variables(
    names : list[str]
):
    try:
        return [os.environ[i] for i in names]
    except KeyError:
        raise MissingCredentials(
            "You are missing the following credentials: "
            f"{[i for i in names if os.getenv(i) is None]}"
            "\n\n"
            "Please add values for these credentials into .env."
        )

def outlook_inbox() -> list[str]:
    return _load_env_variables(OUTLOOK_INBOX)
