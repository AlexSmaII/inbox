# NATRIO_2629_OP-pod-automation
Automated proof-of-delivery docket ingestion to CargoWise

# Requirements

1.  Install Python dependencies:
    ```
    cd backend
    git submodule update --init
    uv sync
    ```

2.  Add credentials to `backend/cwio/.env`.