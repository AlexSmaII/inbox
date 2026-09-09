"""
Simple utility to load values from .env
and give descriptive errors on failure.
"""

import os

from dotenv import load_dotenv

load_dotenv()

POD_INBOX = [
    "POD_INBOX_EMAIL_ADDRESS",
    "POD_INBOX_CLIENT_ID",
    "POD_INBOX_TENANT_ID",
    "POD_INBOX_CLIENT_SECRET"
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

def pod_inbox() -> list[str]:
    return _load_env_variables(POD_INBOX)
