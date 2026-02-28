# Architecture

> Phase 2 output — Tech Lead leads, all roles assist.

## System Overview

```mermaid
graph TB
    Client["Client"] --> API["API Layer"]
    API --> App["Application Layer"]
    App --> Domain["Domain Layer"]
    App --> Infra["Infrastructure Layer"]
    Infra --> DB["Database"]
```

*High-level description of the system and its purpose.*

## Tech Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Runtime | *e.g., .NET 8* | *Why this choice* |
| Framework | *e.g., ASP.NET Core* | |
| Database | *e.g., PostgreSQL* | |
| ORM | *e.g., EF Core* | |
| Testing | *e.g., xUnit* | |
| Infrastructure | *e.g., Docker* | |

## Data Models

```mermaid
erDiagram
    Entity1 ||--o{ Entity2 : "has many"
    Entity1 {
        guid Id PK
        string Name
        datetime CreatedAt
    }
    Entity2 {
        guid Id PK
        guid Entity1Id FK
        string Value
    }
```

### Entity Definitions

#### Entity1

| Property | Type | Constraints | Description |
|----------|------|------------|-------------|
| Id | Guid | PK, Required | Unique identifier |
| Name | string | Required, MaxLength(100) | *Description* |

## API Contracts

### `GET /api/resource`

**Description:** *What this endpoint does.*

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "guid",
      "name": "string"
    }
  ],
  "totalCount": 0
}
```

**Error Responses:**

| Status | Condition |
|--------|----------|
| 400 | Invalid query parameters |
| 500 | Internal server error |

---

### `POST /api/resource`

**Description:** *What this endpoint does.*

**Request Body:**
```json
{
  "name": "string"
}
```

**Response:** `201 Created`
```json
{
  "id": "guid",
  "name": "string"
}
```

**Validation Rules:**
- `name`: Required, 1-100 characters

---

## Component Architecture

```mermaid
graph TB
    subgraph Api["Api Layer"]
        Controllers
        Middleware
    end
    subgraph Application["Application Layer"]
        Services
        DTOs
        Interfaces
    end
    subgraph Domain["Domain Layer"]
        Entities
        Enums
    end
    subgraph Infrastructure["Infrastructure Layer"]
        Repositories
        DbContext
        Migrations
    end

    Controllers --> Services
    Services --> Interfaces
    Repositories -.->|implements| Interfaces
    Repositories --> DbContext
    Services --> Entities
    DbContext --> Entities
```

## Error Handling Strategy

| Scenario | Approach | HTTP Status |
|----------|----------|-------------|
| Validation failure | Return `ProblemDetails` | 400 |
| Resource not found | Return `ProblemDetails` | 404 |
| Business rule violation | Return `Result<T>` failure, map to `ProblemDetails` | 422 |
| Unexpected error | Log + return generic `ProblemDetails` | 500 |

## Security Considerations

- *Authentication approach*
- *Authorization rules*
- *Input validation strategy*
- *CORS configuration*

## Project Structure

```mermaid
graph TD
    Root["project-root/"]
    Root --> src["src/"]
    src --> Api & Application & Domain & Infrastructure
    Root --> tests["tests/"]
    tests --> Unit & Integration
    Root --> docs["docs/"]
    Root --> docker["docker-compose.yml"]
```
