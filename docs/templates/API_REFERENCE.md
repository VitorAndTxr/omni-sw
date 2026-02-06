# API Reference

> Phase 7 output — Tech Lead leads technical documentation.

## Base URL

```
http://localhost:{port}/api
```

## Authentication

*Describe authentication method (e.g., Bearer token, API key, none).*

## Common Response Formats

### Success Response

```json
{
  "data": { },
  "message": "string"
}
```

### Error Response (ProblemDetails - RFC 7807)

```json
{
  "type": "https://tools.ietf.org/html/rfc7807",
  "title": "Error title",
  "status": 400,
  "detail": "Detailed error message",
  "instance": "/api/resource/123",
  "errors": {
    "fieldName": ["Validation error message"]
  }
}
```

## Endpoints

---

### Resource Name

#### `GET /api/resources`

List all resources.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | int | No | 1 | Page number |
| `pageSize` | int | No | 10 | Items per page |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "string",
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ],
  "totalCount": 1,
  "page": 1,
  "pageSize": 10
}
```

---

#### `GET /api/resources/{id}`

Get a resource by ID.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | Guid | Resource identifier |

**Response:** `200 OK`

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "string",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**

| Status | Condition |
|--------|----------|
| 404 | Resource not found |

---

#### `POST /api/resources`

Create a new resource.

**Request Body:**

```json
{
  "name": "string"
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `name` | Required, 1-100 characters |

**Response:** `201 Created`

**Error Responses:**

| Status | Condition |
|--------|----------|
| 400 | Validation failure |

---

#### `PUT /api/resources/{id}`

Update an existing resource.

**Request Body:**

```json
{
  "name": "string"
}
```

**Response:** `200 OK`

**Error Responses:**

| Status | Condition |
|--------|----------|
| 400 | Validation failure |
| 404 | Resource not found |

---

#### `DELETE /api/resources/{id}`

Delete a resource.

**Response:** `204 No Content`

**Error Responses:**

| Status | Condition |
|--------|----------|
| 404 | Resource not found |
