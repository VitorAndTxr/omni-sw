---
name: api-testing
description: |
  REST API testing patterns and scripts. Use when: testing endpoints, debugging API issues,
  validating responses, or user says "test api", "curl", "api request", "postman", "http request",
  "test endpoint", "api not working".
---

# API Testing

## Quick HTTP Requests

### Using curl (Windows/PowerShell)
```powershell
# GET
curl.exe -X GET "http://localhost:5000/api/users" -H "Authorization: Bearer {token}"

# POST with JSON
curl.exe -X POST "http://localhost:5000/api/users" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer {token}" `
  -d '{"name": "John", "email": "john@example.com"}'

# PUT
curl.exe -X PUT "http://localhost:5000/api/users/123" `
  -H "Content-Type: application/json" `
  -d '{"name": "Updated"}'

# DELETE
curl.exe -X DELETE "http://localhost:5000/api/users/123"
```

### Using PowerShell Invoke-RestMethod
```powershell
# GET
$response = Invoke-RestMethod -Uri "http://localhost:5000/api/users" -Method Get

# POST
$body = @{ name = "John"; email = "john@example.com" } | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:5000/api/users" `
  -Method Post -Body $body -ContentType "application/json"

# With Bearer token
$headers = @{ Authorization = "Bearer $token" }
$response = Invoke-RestMethod -Uri "http://localhost:5000/api/users" `
  -Method Get -Headers $headers
```

## Common Test Scenarios

### Authentication Flow
```powershell
# 1. Login
$loginBody = @{ email = "user@example.com"; password = "pass" } | ConvertTo-Json
$auth = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" `
  -Method Post -Body $loginBody -ContentType "application/json"

# 2. Use token
$headers = @{ Authorization = "Bearer $($auth.token)" }
$users = Invoke-RestMethod -Uri "http://localhost:5000/api/users" `
  -Method Get -Headers $headers
```

### Pagination
```powershell
# Test pagination
$page1 = Invoke-RestMethod "http://localhost:5000/api/users?page=1&pageSize=10"
$page2 = Invoke-RestMethod "http://localhost:5000/api/users?page=2&pageSize=10"

# Verify
Write-Host "Total: $($page1.totalCount), Page 1 items: $($page1.items.Count)"
```

### Error Handling
```powershell
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/invalid" -Method Get
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    $errorBody = $_.ErrorDetails.Message
    Write-Host "Status: $statusCode, Error: $errorBody"
}
```

## Response Validation

| Check | What to Verify |
|-------|----------------|
| Status Code | 200 OK, 201 Created, 204 No Content |
| Content-Type | application/json |
| Response Time | < 500ms for simple queries |
| Pagination | totalCount, page, pageSize, items |
| Error Format | Consistent error structure |

## Debugging Tips

```powershell
# Verbose output
curl.exe -v "http://localhost:5000/api/users"

# Show response headers
Invoke-WebRequest -Uri "http://localhost:5000/api/users" | Select-Object -ExpandProperty Headers

# Time request
Measure-Command { Invoke-RestMethod "http://localhost:5000/api/users" }
```

## Health Check Script

```powershell
$endpoints = @(
    "http://localhost:5000/health",
    "http://localhost:5000/api/users",
    "http://localhost:5001/health"
)

foreach ($url in $endpoints) {
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 5
        $sw.Stop()
        Write-Host "[OK] $url - $($response.StatusCode) ($($sw.ElapsedMilliseconds)ms)"
    } catch {
        Write-Host "[FAIL] $url - $($_.Exception.Message)"
    }
}
```
