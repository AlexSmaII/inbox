# CWIO: CargoWise One I/O Utilities

`cwio` is a small Python library for working with
[CargoWise One](https://www.cargowise.com/) from Python. It
wraps the three interfaces you normally have to deal with:

| Interface | Class | Transport | Use |
| --- | --- | --- | --- |
| CargoWise SQL Server database | `CargoReader` | ODBC / SQLAlchemy | Read data out of CW1 as DataFrames |
| CargoWise eAdaptor | `CargoWriter` | HTTP + Universal XML | Push objects into CW1 |
| CargoWise MCP server | `CargoWiseMCP` | JSON-RPC 2.0 over HTTP | Schema discovery and MCP tool calls |

It also ships Pydantic models for the CargoWise Universal
XML schemas (`UniversalShipment`, `UniversalEvent`,
`UniversalTransaction`, …), generated with
[`xsdata-pydantic`](https://github.com/tefra/xsdata-pydantic),
so you can build eAdaptor payloads as typed Python objects
instead of hand-writing XML.

## Requirements

- Python >= 3.13
- [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
  (only needed for `CargoReader`)

## Installation

```bash
uv add cwio
```

To work on the library itself:

```bash
git clone <this-repo>
cd CW1utils
uv sync
```

## Project layout

```
src/cwio/
├── __init__.py       CargoReader, CargoWriter, CargoWiseMCP
├── credentials.py    .env credential loading
├── reader.py         SQL Server connection (CargoReader)
├── writer.py         eAdaptor HTTP+XML client (CargoWriter)
├── parser.py         Universal XML response parsing
├── mcp.py            CargoWise MCP JSON-RPC client
└── schemas/          Generated Pydantic models for Universal XML
```

## Configuration

Credentials are read from environment variables (loaded from
a `.env` file in the working directory via `python-dotenv`).
Populate only the sections you actually use:

```dotenv
# CargoReader: SQL Server, test instance
CW_DB_TEST_SERVER=
CW_DB_TEST_USERNAME=
CW_DB_TEST_PASSWORD=
CW_DB_TEST_DATABASE=

# CargoReader: SQL Server, production instance
CW_DB_PROD_SERVER=
CW_DB_PROD_USERNAME=
CW_DB_PROD_PASSWORD=
CW_DB_PROD_DATABASE=

# CargoWriter: eAdaptor, test instance
CW_EADAPTOR_TEST_URL=
CW_EADAPTOR_TEST_USERNAME=
CW_EADAPTOR_TEST_PASSWORD=

# CargoWriter: eAdaptor, production instance
CW_EADAPTOR_PROD_URL=
CW_EADAPTOR_PROD_USERNAME=
CW_EADAPTOR_PROD_PASSWORD=

# CargoWiseMCP
CW_MCP_URL=
CW_MCP_TOKEN=
```

`.env` is git-ignored. Every constructor also accepts
credentials directly, so you can source them from a secrets
manager instead: see the examples below.

## Usage

### Reading from the CW1 database

`CargoReader` opens a SQLAlchemy connection to the CargoWise
SQL Server database and returns query results as pandas
DataFrames.

```python
from cwio import CargoReader

reader = CargoReader(production=False)

shipments = reader.query("""
    SELECT TOP 100 JS_ID, JS_Waybill, JS_ETD, JS_ETA
    FROM JobShipment
    ORDER BY JS_ETD DESC
""")

print(shipments.head())
```

You may also pass credentials explicitly
instead of relying on the default ones in `.env`:

```python
reader = CargoReader(
    server_name="sql.example.com",
    username="reporting",
    password="...",
    database_name="CargoWise",
)
```

### Writing to CargoWise via eAdaptor

`CargoWriter` serialises a Universal XML object and POSTs it
to the eAdaptor endpoint with HTTP Basic auth, then parses
the reply into a `UniversalResponse`.

```python
from datetime import datetime, timedelta

from cwio import CargoWriter
from cwio.schemas import DataContext, DataTarget, Event, UniversalEvent

writer = CargoWriter(production=False)

event = UniversalEvent(
    event=Event(
        data_context=DataContext(
            data_target=[DataTarget(type_value="ForwardingShipment", key="S00001234")],
        ),
        event_time=datetime.now().isoformat(),
        event_type="ABC",
    )
)

response = writer.post(event, timeout=timedelta(minutes=2))
print(response.status)          # "PRS" on success
print(response.processing_log)
```

Errors surface as exceptions rather than silent failures:

- `ValueError`: the object could not be serialised, or the
  response was empty/unparseable
- `requests.HTTPError`: non-2xx response from the eAdaptor
- `CargoWriter.CW1Error`: the eAdaptor returned
  `status == "ERR"`: the CW1 processing log is included in
  the message

### Querying the CargoWise MCP server

```python
from cwio import CargoWiseMCP
from cwio import credentials

url, token = credentials.mcp()      # reads CW_MCP_URL / CW_MCP_TOKEN
mcp = CargoWiseMCP(url=url, token=token)

tables = mcp.tables_list(instance="prod")
columns = mcp.table_describe("JobShipment", instance="prod")

for column in columns[:5]:
    print(column.name, column.type, column.length)

# Anything else the MCP exposes:
mcp.tool_call(
    "cw.schema.search", {
        "table_like": "JobShipment",
        "column_like": "Waybill",
        "top": 100,
        "instance": "prod"
})
```

Requests are retried up to 3 times with a 60-second wait on
`HTTPError`. MCP-level failures raise
`CargoWiseMCP.MCPError`; failures reported by CargoWise
itself raise `CargoWiseMCP.CW1Error`.

### Parsing an eAdaptor response on its own

If you receive Universal XML from somewhere else (a webhook,
a file, a queue), parse it directly:

```python
from cwio.parser import parse_cw_response

response = parse_cw_response(xml_string)
```

### Universal XML schemas

`cwio.schemas` exports the generated Pydantic models for the CargoWise Universal 2011/11 namespace —
the top-level documents (`UniversalShipment`, `UniversalEvent`, `UniversalTransaction`,
`UniversalTransactionBatch`, `UniversalActivity`, `UniversalResponse`, `UniversalInterchange`,
`UniversalSchedule`, `UniversalDocumentRequest`, and their `*Request` variants) plus the several
hundred shared types they are built from (`Shipment`, `Container`, `Organization*`, `ChargeLine`,
`PackingLine`, …).

`CargoWiseObject` is the union type accepted by `CargoWriter.post`:

```python
CargoWiseObject = (
    UniversalActivity | UniversalEvent | UniversalShipment
    | UniversalResponse | UniversalTransaction | UniversalTransactionBatch
)
```

Field names follow Python conventions (`event_type`), while the XML element names
(`EventType`) are carried in the model metadata, so serialisation round-trips to valid CargoWise
XML.

Refer to the CargoWise *eAdaptor Developer's Guide* for the meaning of individual fields and for
which document type each interface expects.
