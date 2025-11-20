# Docker Containers Explained

## Container Overview

Your AETHERA project uses **2 Docker containers**:

### 1. `aethera-postgres` (PostgreSQL Database)
- **Purpose**: Main database for the application
- **Defined in**: `docker-compose.yml`
- **Port**: 55432 (mapped from container port 5432)
- **Image**: Built from `docker/postgres/Dockerfile`
- **Status**: Currently stopped

**What it stores**:
- Projects and runs
- Reports and embeddings
- Security (users, roles, permissions, audit logs)
- Model governance data
- Legal evaluation results

### 2. `aethera-redis` (Redis Cache/Queue)
- **Purpose**: Task queue and caching for Celery
- **Created by**: VS Code task or manual command
- **Port**: 6379
- **Image**: `redis:7-alpine`
- **Status**: Currently stopped

**What it's used for**:
- Celery task queue (async job processing)
- Result backend for completed tasks
- Optional caching

## Which Container to Initialize?

**Answer: You don't need to manually initialize either!**

The **"Start All Services"** VS Code task will:
1. ✅ Start `aethera-postgres` automatically (via `docker-compose up -d db`)
2. ✅ Start `aethera-redis` automatically (creates if doesn't exist, starts if exists)

## Manual Start (If Needed)

If you want to start them manually:

### Start PostgreSQL
```powershell
docker-compose up -d db
# OR
docker start aethera-postgres
```

### Start Redis
```powershell
docker start aethera-redis
# OR if it doesn't exist:
docker run -d -p 6379:6379 --name aethera-redis redis:7-alpine
```

## Current Status

Based on your system:
- ✅ `aethera-redis` exists (stopped)
- ✅ `aethera-postgres` exists (stopped)

Both will be started automatically by the "Start All Services" task.

## Verification

After starting services, verify containers are running:
```powershell
docker ps
```

Should show:
```
NAMES              IMAGE                 STATUS
aethera-postgres   aethera_original-db   Up X minutes
aethera-redis      redis:7-alpine        Up X minutes
```

## Important Notes

1. **Docker Desktop must be running** before starting containers
2. **Container names**:
   - Container name: `aethera-postgres` (what you see in `docker ps`)
   - Image name: `aethera_original-db` (internal Docker image name)
3. **No manual initialization needed** - just use "Start All Services" task

---

**TL;DR**: Use the "Start All Services" task - it handles both containers automatically! 🚀

