---
name: docker-compose-helper
description: |
  Docker Compose management for multi-container applications. Use when: starting/stopping containers,
  viewing logs, debugging network issues, managing volumes, or user says "docker", "container",
  "compose up", "docker logs", "container not starting", "network issue".
---

# Docker Compose Helper

## Essential Commands

```bash
# Start services
docker-compose up -d                    # Detached mode
docker-compose -f custom.yml up -d      # Custom file

# Stop services
docker-compose down                     # Stop and remove containers
docker-compose down -v                  # Also remove volumes
docker-compose stop                     # Stop without removing

# Rebuild
docker-compose up -d --build            # Rebuild images
docker-compose build --no-cache         # Force rebuild from scratch

# Logs
docker logs -f {container}              # Follow logs
docker logs --tail 100 {container}      # Last 100 lines
docker-compose logs -f                  # All services

# Status
docker-compose ps                       # List services
docker ps -a                            # All containers
docker stats                            # Resource usage
```

## Debugging

### Container Won't Start
```bash
# Check logs
docker logs {container}

# Check exit code
docker inspect {container} --format='{{.State.ExitCode}}'

# Interactive shell
docker run -it --entrypoint /bin/sh {image}
```

### Network Issues
```bash
# List networks
docker network ls

# Inspect network
docker network inspect {network}

# Test connectivity between containers
docker exec -it {container1} ping {container2}

# Check DNS resolution
docker exec -it {container} nslookup {service-name}
```

### Volume Issues
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect {volume}

# Remove unused volumes
docker volume prune
```

## Common Patterns

### Health Check
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Depends On with Condition
```yaml
depends_on:
  db:
    condition: service_healthy
```

### Environment from File
```yaml
env_file:
  - .env
  - .env.local
```

## Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove everything unused
docker system prune -a --volumes

# Nuclear option (remove ALL)
docker system prune -a --volumes -f
```

## Quick Diagnostics

| Symptom | Check |
|---------|-------|
| Port conflict | `netstat -ano | findstr :{port}` (Windows) |
| Out of space | `docker system df` |
| Slow builds | Check `.dockerignore` |
| Can't connect | Verify network and ports in compose |
