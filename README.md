# Notes Backend

An asynchronous REST API for managing personal notes, folders, and file attachments.

## Tech Stack

- **API:** FastAPI, Pydantic, Uvicorn
- **Database:** PostgreSQL, SQLAlchemy 2 (async), Alembic
- **Authentication:** JWT access and refresh tokens, Argon2 password hashing
- **Object storage:** MinIO (S3-compatible)
- **Testing:** Pytest, pytest-asyncio
- **Deployment:** Docker, Docker Compose

## Architecture

```mermaid
flowchart TD
    Client["HTTP Client"]
    Router["API Router"]
    Service["Service Layer"]
    Repository["Repository Layer"]
    StorageAdapter["Storage Adapter"]
    Database[("PostgreSQL")]
    MinIO[("MinIO")]

    Client --> Router
    Router --> Service
    Service --> Repository
    Service --> StorageAdapter
    Repository --> Database
    StorageAdapter --> MinIO
```

## Use Cases

The system provides account management and note organization. A user must be authenticated to access protected resources, and resource operations must enforce ownership.

### Use Case Diagram

Mermaid does not currently provide a native UML use-case diagram type. The following Mermaid diagram uses actor and use-case-style notation so GitHub can render it directly; it is **not a fully standard UML use-case diagram**.

```mermaid
flowchart LR
    User["Actor: User"]

    subgraph System["Notes Backend"]
        UC1(["Register"])
        UC2(["Sign in"])
        UC3(["Refresh access token"])
        UC4(["Manage profile and password"])
        UC5(["Create, view, update, and delete notes"])
        UC6(["Search and filter notes"])
        UC7(["Create and manage folders"])
        UC8(["Organize notes in folders"])
        UC9(["Upload attachments"])
        UC10(["View and delete attachments"])
    end

    User --- UC1
    User --- UC2
    User --- UC3
    User --- UC4
    User --- UC5
    User --- UC6
    User --- UC7
    User --- UC8
    User --- UC9
    User --- UC10
```

## Data Model

PostgreSQL stores application records and attachment metadata. Attachment contents are stored in MinIO; the database stores their object keys and metadata.

### Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ NOTE : owns
    USER ||--o{ FOLDER : owns
    FOLDER o|--o{ FOLDER : contains
    FOLDER o|--o{ NOTE : contains
    NOTE ||--o{ ATTACHMENT : has

    USER {
        int id PK
        string email UK
        string hashed_password
    }

    FOLDER {
        int id PK
        int user_id FK
        int parent_id FK
        string name
    }

    NOTE {
        int id PK
        int user_id FK
        int folder_id FK
        string title
        text content
    }

    ATTACHMENT {
        int id PK
        int note_id FK
        string object_key UK
        string content_type
        int size_bytes
    }
```

**Important:** Verify entity and field names, nullability, and relationships against the actual SQLAlchemy models before treating this diagram as the authoritative schema.

## API Overview

All endpoints are versioned under `/api/v1`.

| Area | Endpoints |
|---|---|
| Authentication | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh` |
| User | `GET /users/me`, `POST /users/me/change-password`, `DELETE /users/me` |
| Notes | `GET/POST /notes`, `GET/PUT/DELETE /notes/{note_id}` |
| Folders | `GET/POST /folders`, `GET/PATCH/DELETE /folders/{folder_id}`, `GET /folders/{folder_id}/children`, `GET /folders/{folder_id}/notes` |
| Attachments | `GET/POST /notes/{note_id}/attachments`, `GET/DELETE /notes/{note_id}/attachments/{attachment_id}` |

Notes and folders listing endpoints support pagination, search, and sorting. Notes can be filtered by folder. Folder operations validate ownership and prevent invalid or circular parent relationships.

### Attachments

Supported content types:

- `image/png`
- `image/jpeg`
- `application/pdf`

Uploads are checked against content type, file signature, per-file size limit, and per-note aggregate size limit. Access to an attachment is authorized through ownership of its parent note.

## Getting Started

### Prerequisites

- Python 3
- PostgreSQL
- MinIO
- Docker Engine or Docker Desktop with Docker Compose

### Environment Configuration

Create a local `.env` file using the configuration expected by `app/core/config.py`. Set the database URL, JWT secret, and MinIO endpoint and credentials.

Never commit real credentials or `.env` files.

Example database URL:

```text
postgresql+asyncpg://username:password@localhost:5432/notes
```

Use the environment variables and port mappings defined in the repository's Docker Compose configuration.

### Run with Docker Compose

From the repository root:

```bash
docker compose up --build
```

View service logs:

```bash
docker compose logs -f
```

Stop services without deleting persisted volumes:

```bash
docker compose down
```

### Run Locally

Create and activate a virtual environment, then install dependencies.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux/macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

After configuring `.env` and starting PostgreSQL and MinIO, apply migrations and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

The default local API address is `http://localhost:8000`, unless overridden by configuration.

## API Documentation

When the API is running:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI schema:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Testing

Run the complete test suite:

```bash
pytest -q
```

Run test groups separately:

```bash
pytest tests/unit -q
pytest tests/integration -q
```

Integration tests require a configured test database. Check `tests/conftest.py` and the test environment before running them. Never point tests at production data.

## Security

- Passwords are hashed with Argon2.
- JWTs are used for authentication.
- Resource ownership checks help prevent cross-user access.
- Attachment uploads validate content type, file signature, and size.
- The application includes centralized error handling and logging.
- Use strong secrets and production-specific environment variables.
- Do not expose PostgreSQL or MinIO administration ports publicly.

## Project Structure

```text
app/
├── api/             # Versioned routers and dependencies
├── core/            # Configuration, database, security, storage, logging
├── middlewares/
├── models/          # SQLAlchemy models
├── repositories/    # Database access
├── schemas/         # Pydantic schemas
├── services/        # Business logic
└── main.py

alembic/             # Database migrations
tests/
├── unit/
└── integration/
```