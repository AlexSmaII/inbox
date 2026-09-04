"""
Simple utility to load values from .env
and give descriptive errors on failure.
"""

import os

from dotenv import load_dotenv

load_dotenv()

READ_TEST = [
    "CW_DB_TEST_SERVER",
    "CW_DB_TEST_USERNAME",
    "CW_DB_TEST_PASSWORD",
    "CW_DB_TEST_DATABASE"
]
READ_PROD = [
    "CW_DB_PROD_SERVER",
    "CW_DB_PROD_USERNAME",
    "CW_DB_PROD_PASSWORD",
    "CW_DB_PROD_DATABASE"
]
WRITE_TEST = [
    "CW_EADAPTOR_TEST_URL",
    "CW_EADAPTOR_TEST_USERNAME",
    "CW_EADAPTOR_TEST_PASSWORD"
]
WRITE_PROD = [
    "CW_EADAPTOR_PROD_URL",
    "CW_EADAPTOR_PROD_USERNAME",
    "CW_EADAPTOR_PROD_PASSWORD"
]
MCP = [
    "CW_MCP_URL",
    "CW_MCP_TOKEN"
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

def read(
    production : bool = False
) -> list[str]:
    return _load_env_variables(
        READ_PROD if production else READ_TEST
    )

def write(
    production : bool = False
) -> list[str]:
    return _load_env_variables(
        WRITE_PROD if production else WRITE_TEST
    )

def mcp() -> list[str]:
    return _load_env_variables(MCP)