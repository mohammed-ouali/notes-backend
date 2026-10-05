# Notes Backend

A REST API for managing personal notes, folders, and file attachments.

The project provides user authentication, note and folder management, attachment storage, validation, authorization, rate limiting, structured error handling, logging, and automated tests.

## Tech Stack

- **Python**
- **FastAPI** — REST API framework
- **PostgreSQL** — relational database
- **SQLAlchemy 2** — asynchronous ORM
- **Alembic** — database migrations
- **Pydantic v2** — request and response validation
- **JWT** — access and refresh token authentication
- **Argon2** — password hashing
- **MinIO** — S3-compatible object storage for attachments
- **Pytest** — automated testing
- **Uvicorn** — ASGI server
- **Docker / Docker Compose** — containerized deployment setup

## Architecture

The application follows a layered architecture:

```mermaid
flowchart TD
    Client["Client / Frontend"]

    Router["FastAPI Routers"]
    Service["Service Layer"]
    Repository["Repository Layer"]

    DB[("PostgreSQL")]
    Storage["MinIO Object Storage"]

    Security["Authentication & Authorization"]
    Middleware["Middleware"]
    Exceptions["Exception Handlers"]

    Client --> Middleware
    Middleware --> Router

    Router --> Security
    Router --> Service

    Service --> Repository
    Repository --> DB

    Service --> Storage
    Router --> Exceptions
    Service --> Exceptions
```

### Main Components

| Component | Responsibility |
|---|---|
| Routers | HTTP endpoints, request handling and API documentation |
| Services | Business logic and validation |
| Repositories | Database access |
| SQLAlchemy Models | Database entities and relationships |
| Pydantic Schemas | Request validation and response serialization |
| PostgreSQL | Persistent application data |
| MinIO | Binary attachment storage |
| Authentication | JWT access and refresh tokens |
| Middleware | Logging, security headers, CORS and rate limiting |
| Exception Handlers | Consistent API error responses |
| Alembic | Database schema migrations |

The main API is mounted under:

```text
/api/v1
```

## Use Cases

The main actor is an authenticated user.

```mermaid
flowchart LR
    User((User))

    Register["Register"]
    Login["Login"]
    Refresh["Refresh Token"]

    Notes["Manage Notes"]
    Folders["Manage Folders"]
    Attachments["Manage Attachments"]

    Profile["View Profile"]
    Password["Change Password"]
    DeleteAccount["Delete Account"]

    User --> Register
    User --> Login
    User --> Refresh

    User --> Notes
    User --> Folders
    User --> Attachments

    User --> Profile
    User --> Password
    User --> DeleteAccount
```

Main functional areas:

- Account registration
- Login and token refresh
- User profile management
- Password change
- Account deletion
- Note creation, retrieval, update and deletion
- Note search, sorting and pagination
- Folder creation, retrieval, update and deletion
- Nested folders
- Listing notes inside folders
- File attachment upload, download and deletion

## Database Design

The application uses PostgreSQL for persistent application data.

```mermaid
erDiagram
    USER ||--o{ NOTE : owns
    USER ||--o{ FOLDER : owns
    FOLDER ||--o{ FOLDER : contains
    FOLDER ||--o{ NOTE : contains
    NOTE ||--o{ ATTACHMENT : has

    USER {
        int id PK
        string email UK
        string password_hash
        boolean is_active
        datetime created_at
    }

    FOLDER {
        int id PK
        int user_id FK
        int parent_id FK
        string name
        datetime created_at
        datetime updated_at
    }

    NOTE {
        int id PK
        int user_id FK
        int folder_id FK
        string title
        text content
        datetime created_at
        datetime updated_at
    }

    ATTACHMENT {
        int id PK
        int note_id FK
        string file_name
        string object_key UK
        string content_type
        int size_bytes
        datetime created_at
    }
```

### Important Relationships

- A user can own multiple notes.
- A user can own multiple folders.
- Folders can contain nested subfolders.
- A folder can contain multiple notes.
- A note can have multiple attachments.
- Deleting a user cascades to their notes and folders.
- Deleting a note cascades to its database attachments.
- Attachment file content itself is stored in MinIO rather than PostgreSQL.

## Sequence Diagrams

### User Login

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI Router
    participant Auth as AuthService
    participant UserService
    participant Repository as UserRepository
    participant Security as JWT/Security

    User->>API: POST /api/v1/auth/login
    API->>Auth: login_user(email, password)
    Auth->>UserService: authenticate user
    UserService->>Repository: get_by_email(email)
    Repository-->>UserService: User
    UserService-->>Auth: Authenticated user
    Auth->>Security: Create access + refresh tokens
    Security-->>Auth: Token pair
    Auth-->>API: Token
    API-->>User: 200 OK + tokens
```

### Create Note

```mermaid
sequenceDiagram
    actor User
    participant API as Notes Router
    participant Auth as Authentication
    participant Service as NoteService
    participant FolderRepo as FolderRepository
    participant NoteRepo as NoteRepository
    participant DB as PostgreSQL

    User->>API: POST /api/v1/notes
    API->>Auth: Validate access token
    Auth-->>API: Current user

    API->>Service: create_note(note_data, user_id)

    alt Note has a folder
        Service->>FolderRepo: Validate folder ownership
        FolderRepo->>DB: Query folder
        DB-->>FolderRepo: Folder
        FolderRepo-->>Service: Valid folder
    end

    Service->>NoteRepo: Create note
    NoteRepo->>DB: INSERT note
    DB-->>NoteRepo: Created note
    NoteRepo-->>Service: Note
    Service-->>API: Note
    API-->>User: 201 Created
```

### Upload Attachment

```mermaid
sequenceDiagram
    actor User
    participant API as Notes Router
    participant Service as AttachmentService
    participant NoteRepo as NoteRepository
    participant Storage as MinIO
    participant AttachmentRepo as AttachmentRepository
    participant DB as PostgreSQL

    User->>API: POST /api/v1/notes/{note_id}/attachments
    API->>Service: upload_attachment(user_id, note_id, file)

    Service->>NoteRepo: Validate note ownership
    NoteRepo->>DB: Query note
    DB-->>NoteRepo: Note
    NoteRepo-->>Service: Note

    Service->>Service: Validate MIME type
    Service->>Service: Read and validate file size
    Service->>Service: Validate file signature
    Service->>AttachmentRepo: Get current attachment size
    AttachmentRepo->>DB: Query total size
    DB-->>AttachmentRepo: Current size

    Service->>Storage: Upload object
    Storage-->>Service: Object stored

    Service->>AttachmentRepo: Create attachment metadata
    AttachmentRepo->>DB: INSERT attachment
    DB-->>AttachmentRepo: Attachment
    AttachmentRepo-->>Service: Attachment

    Service-->>API: AttachmentResponse
    API-->>User: 201 Created
```

## API

The API is versioned under:

```text
/api/v1
```

### Authentication

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
```

Registration and login return an access token and refresh token.

Protected endpoints use the access token through the HTTP `Authorization` header:

```http
Authorization: Bearer <access_token>
```

### Users

```text
GET    /api/v1/users/me
POST   /api/v1/users/me/change-password
DELETE /api/v1/users/me
```

### Notes

```text
GET    /api/v1/notes
GET    /api/v1/notes/{note_id}
POST   /api/v1/notes
PUT    /api/v1/notes/{note_id}
DELETE /api/v1/notes/{note_id}
```

The note list supports:

- Pagination
- Search by title or content
- Sorting by `created_at` or `updated_at`
- Ascending or descending order
- Filtering by folder

Example:

```text
GET /api/v1/notes?page=1&limit=10&q=python&sort_by=created_at&order=desc
```

### Folders

```text
GET    /api/v1/folders
GET    /api/v1/folders/{folder_id}
GET    /api/v1/folders/{folder_id}/children
GET    /api/v1/folders/{folder_id}/notes
POST   /api/v1/folders
PATCH  /api/v1/folders/{folder_id}
DELETE /api/v1/folders/{folder_id}
```

Folders support nested hierarchies.

The service layer prevents invalid parent relationships, including making a folder its own parent or creating a circular hierarchy.

### Attachments

```text
GET    /api/v1/notes/{note_id}/attachments
GET    /api/v1/notes/{note_id}/attachments/{attachment_id}
POST   /api/v1/notes/{note_id}/attachments
DELETE /api/v1/notes/{note_id}/attachments/{attachment_id}
```

Supported file types:

```text
image/png
image/jpeg
application/pdf
```

Attachments are validated using both their declared content type and file signature.

The application also enforces:

- Maximum size per attachment
- Maximum combined attachment size per note
- Sanitized original filenames
- Ownership checks through the parent note

Binary files are stored in MinIO. PostgreSQL stores their metadata and object keys.

## API Documentation

FastAPI automatically exposes interactive API documentation.

After starting the application:

```text
Swagger UI:
http://localhost:8000/docs

ReDoc:
http://localhost:8000/redoc

OpenAPI schema:
http://localhost:8000/openapi.json
```

## Installation

### Prerequisites

Install the following:

- Python 3.x
- PostgreSQL
- MinIO
- Git

Docker support is also provided by the project configuration once the containerization files are present.

### Clone the Repository

```bash
git clone https://github.com/mohammed-ouali/notes-backend.git
cd notes-backend
```

### Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

The application loads its configuration from `.env`.

The configuration includes:

```text
APP_NAME
DEBUG
API_VERSION

DATABASE_URL

SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS

LOG_LEVEL
LOG_FORMAT_JSON
LOG_FILE_PATH
LOG_ROTATION
LOG_RETENTION

MINIO_ENDPOINT
MINIO_ACCESS_KEY
MINIO_SECRET_KEY
MINIO_BUCKET_NAME
MINIO_SECURE

MAX_ATTACHMENT_SIZE_BYTES
MAX_NOTE_ATTACHMENTS_SIZE_BYTES

SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_FROM

RATE_LIMIT_AUTH
RATE_LIMIT_DEFAULT
RATE_LIMIT_WINDOW_SECONDS
```

Do not commit `.env` or credentials to the repository.

### PostgreSQL

Create the application database in PostgreSQL and configure its connection string through `DATABASE_URL`.

Example format:

```text
postgresql+asyncpg://username:password@localhost:5432/notes
```

The actual credentials and database name depend on the local environment.

### MinIO

MinIO is used as S3-compatible object storage for note attachments.

For a local Windows installation, for example:

```powershell
.\minio.exe server C:\minio\data --console-address ":9001"
```

The default local endpoints are:

```text
MinIO API:     http://localhost:9000
MinIO Console: http://localhost:9001
```

The application initializes the configured bucket when `app.main` starts.

The MinIO endpoint and credentials must match the corresponding application settings.

### Database Migrations

After configuring PostgreSQL and the environment:

```bash
alembic upgrade head
```

To create a new migration after a model change:

```bash
alembic revision --autogenerate -m "describe the change"
```

Then apply it:

```bash
alembic upgrade head
```

### Run the Application

Start the development server with:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

## Docker

The project is intended to support running the application and its infrastructure through Docker Compose.

The containerized environment should provide the application together with its required infrastructure services:

```text
FastAPI
   │
   ├── PostgreSQL
   │
   └── MinIO
```

Expected workflow:

```bash
docker compose up --build
```

Stop the services:

```bash
docker compose down
```

View logs:

```bash
docker compose logs -f
```

> Docker configuration is part of the planned project setup. The repository currently does not contain a `Dockerfile` or `docker-compose.yml`; these commands should be enabled/documented as executable commands after the Docker implementation is added.

## Testing

The project uses **Pytest** and `pytest-asyncio`.

The test suite is divided into:

```text
tests/
├── conftest.py
├── unit/
│   └── test_security.py
└── integration/
    ├── test_auth.py
    ├── test_attachments.py
    ├── test_folders.py
    ├── test_notes.py
    └── test_users.py
```

### Test Coverage

The tests cover the main application areas:

- Security and password/token behavior
- Authentication
- Users
- Notes
- Folders
- Attachments
- Authorization and ownership behavior
- Validation and error cases

Integration tests use a dedicated test database derived from the configured database URL.

The test configuration replaces the `notes` database name with `notes_test`, so the test database must exist before running the integration suite.

### Run All Tests

Activate the virtual environment first.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

Linux/macOS:

```bash
source .venv/bin/activate
pytest
```

Run a specific test directory:

```bash
pytest tests/unit
```

```bash
pytest tests/integration
```

Run a specific test file:

```bash
pytest tests/integration/test_notes.py
```

Run with more detailed output:

```bash
pytest -v
```

## Security

The API implements several security mechanisms:

- JWT access and refresh tokens
- Argon2 password hashing
- Protected authenticated endpoints
- User ownership checks
- Cross-user resource isolation
- Account activity checks
- Password validation
- File type validation
- File signature validation
- Attachment size limits
- Filename sanitization
- Security headers
- CORS configuration
- Rate limiting
- Centralized exception handling

Resources belonging to another user are intentionally treated as not found rather than exposing ownership information.

## Error Handling

The API uses a centralized problem-details style error format.

Example:

```json
{
  "type": "about:blank",
  "title": "Note Not Found",
  "status": 404,
  "detail": "Note with ID 123 not found",
  "instance": "/api/v1/notes/123"
}
```

Validation errors can additionally include invalid parameter information.

## Project Structure

```text
notes-backend/
├── app/
│   ├── api/
│   │   ├── dependencies/
│   │   └── v1/
│   │       ├── routers/
│   │       └── router.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── email.py
│   │   ├── exception_handlers.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   ├── rate_limiter.py
│   │   ├── security.py
│   │   └── storage.py
│   │
│   ├── middlewares/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
│
├── alembic/
│   └── versions/
│
├── tests/
│   ├── integration/
│   ├── unit/
│   └── conftest.py
│
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── README.md
```

## Project Status

The project currently includes:

- REST API with FastAPI
- Authentication and authorization
- User management
- Notes management
- Folder management with nested folders
- Object storage for attachments
- Database migrations
- Centralized error handling
- Logging
- Security middleware
- Rate limiting
- Automated unit and integration tests
- OpenAPI documentation

Docker containerization is the next infrastructure step.