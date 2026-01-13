# PostgreSQL Migration Guide

This guide explains how to migrate from SQLite (development) to PostgreSQL (production).

## Prerequisites

1. PostgreSQL 14+ installed
2. `psycopg2-binary` Python package installed
3. Access to create databases

## Setup PostgreSQL

### 1. Install PostgreSQL (macOS)
```bash
brew install postgresql@14
brew services start postgresql@14
```

### 2. Create Database
```bash
createdb youtube_recipes
```

### 3. Create User (Optional)
```bash
psql -c "CREATE USER recipe_app WITH PASSWORD 'your_secure_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE youtube_recipes TO recipe_app;"
```

## Install Python Dependencies

```bash
pip install psycopg2-binary
```

## Migration Steps

### Step 1: Backup SQLite Data
```bash
cd youtube_to_list
sqlite3 youtube_cards.db .dump > backup_$(date +%Y%m%d).sql
```

### Step 2: Update Environment Variables
Add to your `.env` file:
```bash
DATABASE_URL=postgresql://recipe_app:your_secure_password@localhost:5432/youtube_recipes
```

Or for local development without password:
```bash
DATABASE_URL=postgresql://localhost/youtube_recipes
```

### Step 3: Run Alembic Migrations
```bash
cd youtube_to_list
python3 -m alembic upgrade head
```

This creates all tables with proper PostgreSQL types.

### Step 4: Migrate Data (Optional)

#### Option A: Fresh Start
If you don't need existing recipes, skip this step. The database is ready to use.

#### Option B: Use pgloader (Recommended for Large Data)
```bash
# Install pgloader
brew install pgloader

# Create pgloader config file
cat > migrate.load << 'EOF'
LOAD DATABASE
    FROM sqlite:///youtube_cards.db
    INTO postgresql://localhost/youtube_recipes

WITH include drop, create tables, create indexes, reset sequences

SET work_mem to '16MB', maintenance_work_mem to '512 MB';
EOF

# Run migration
pgloader migrate.load
```

#### Option C: Manual Python Script
```python
#!/usr/bin/env python3
"""Migrate data from SQLite to PostgreSQL"""
import os
os.environ['DATABASE_URL'] = 'sqlite:///youtube_cards.db'

from src.database import SessionLocal as SQLiteSession
from src.models import Recipe, Ingredient, Tag

# Switch to PostgreSQL
os.environ['DATABASE_URL'] = 'postgresql://localhost/youtube_recipes'
# Reimport with new URL
from importlib import reload
import src.database
reload(src.database)
from src.database import SessionLocal as PGSession

# Copy data
sqlite_db = SQLiteSession()
pg_db = PGSession()

for recipe in sqlite_db.query(Recipe).all():
    pg_db.merge(recipe)

pg_db.commit()
print("Migration complete!")
```

### Step 5: Verify Data Integrity
```bash
# Count recipes in PostgreSQL
psql youtube_recipes -c "SELECT COUNT(*) FROM recipes;"

# Compare with SQLite
sqlite3 youtube_cards.db "SELECT COUNT(*) FROM recipes;"
```

## Rollback Plan

If issues occur, revert to SQLite:

1. Remove or comment out `DATABASE_URL` from `.env`
2. Restart the application
3. The app will use the SQLite database

**Keep SQLite backup for at least 30 days after migration.**

## Connection Pooling

PostgreSQL configuration includes connection pooling:
- `pool_size`: 5 (default connections)
- `max_overflow`: 10 (additional connections under load)
- `pool_pre_ping`: True (validates connections before use)
- `pool_recycle`: 3600 (recycle connections after 1 hour)

## Troubleshooting

### Connection Refused
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Start if needed
brew services start postgresql@14
```

### Permission Denied
```bash
# Grant permissions
psql -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO recipe_app;"
psql -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO recipe_app;"
```

### SSL Required (Cloud Providers)
```bash
# Update DATABASE_URL with SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

## Production Recommendations

1. **Use connection pooling service** (PgBouncer) for high traffic
2. **Enable SSL** for all connections
3. **Regular backups** with pg_dump
4. **Monitor connections** to avoid exhaustion
5. **Use read replicas** for heavy read workloads

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-12
