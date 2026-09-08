---
Project Title:      POD Automation
Project Year:       2026
Project Number:     29
Project Client:     Axima
Project Department: Freight Forwarding (FF)
Project ID:         NATRIO_2629_FF-pod-automation
---

## Goal

Automate Axima's need to outsource manual processing of
proof of delivery (POD) dockets to Offshore Business
Processing (OBP) by extracting data from scanned dockets and
pushing them to CargoWise One (CW1) eDocs.

## Requirements

1.  Install Python dependencies:
    ```powershell
    cd backend
    git submodule update --init
    uv sync
    ```

2.  Add credentials to `backend/.env`.

## Testing

The service can be interfaced through a FastAPI endpoint:

```powershell
uv run fastapi run main.py --host 0.0.0.0 --port 8080
```
