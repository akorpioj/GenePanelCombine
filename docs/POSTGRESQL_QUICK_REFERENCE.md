# Google Cloud PostgreSQL - Quick Reference

## Instance Information
- **Instance**: `gene-panel-user-db`
- **Location**: `europe-north1-c` 
- **Public IP**: `35.228.157.4`
- **Database**: `genepanel-userdb`

## Quick Commands

### Instance Management
```bash
# List instances
gcloud sql instances list

# Instance details
gcloud sql instances describe gene-panel-user-db

# Start/Stop instance
gcloud sql instances patch gene-panel-user-db --activation-policy=ALWAYS
gcloud sql instances patch gene-panel-user-db --activation-policy=NEVER
```

### Database Operations
```bash
# List databases
gcloud sql databases list --instance=gene-panel-user-db

# Connect to database
gcloud sql connect gene-panel-user-db --user=genepanel_app --database=genepanel-userdb

# Connect with psql directly
psql "postgresql://genepanel_app:PASSWORD@35.228.157.4:5432/genepanel-userdb?sslmode=require"
```

### User Management
```bash
# List users
gcloud sql users list --instance=gene-panel-user-db

# Change password
gcloud sql users set-password genepanel_app --instance=gene-panel-user-db --password="NEW_PASSWORD"
```

### Backup Operations
```bash
# List backups
gcloud sql backups list --instance=gene-panel-user-db

# Create backup
gcloud sql backups create --instance=gene-panel-user-db --description="Manual backup"

# Export database
gcloud sql export sql gene-panel-user-db gs://YOUR_BUCKET/backup-$(date +%Y%m%d).sql --database=genepanel-userdb
```

### Cloud SQL Proxy
```bash
# Start proxy (replace PROJECT_ID)
./cloud-sql-proxy.exe PROJECT_ID:europe-north1:gene-panel-user-db

# Connect via proxy
psql "postgresql://genepanel_app:PASSWORD@localhost:5432/genepanel-userdb"
```

### Monitoring
```bash
# Instance metrics
gcloud sql instances describe gene-panel-user-db --format="value(stats)"

# Recent operations
gcloud sql operations list --instance=gene-panel-user-db --limit=10

# Logs
gcloud logging read "resource.type=cloudsql_database" --limit=20
```

## Environment Variables
```bash
# Production
export GOOGLE_CLOUD_SQL=true
export DATABASE_URL="postgresql://genepanel_app:PASSWORD@35.228.157.4:5432/genepanel-userdb?sslmode=require"

# Via proxy
export DATABASE_URL="postgresql://genepanel_app:PASSWORD@localhost:5432/genepanel-userdb"
```

## Common SQL Queries
```sql
-- Check table sizes
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size 
FROM pg_tables WHERE schemaname='public';

-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Database stats
SELECT * FROM pg_stat_database WHERE datname = 'genepanel-userdb';

-- Table stats
SELECT * FROM pg_stat_user_tables;
```

## Emergency Contacts
- Database admin: Check Cloud SQL console
- Backup location: Automated daily backups
- Support: Google Cloud Support (if applicable)
