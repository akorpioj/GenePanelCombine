# Storage Configuration Quick Reference

## Quick Setup Commands

### Google Cloud Storage Setup
```bash
# 1. Set project and enable API
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
gcloud services enable storage.googleapis.com

# 2. Create buckets
gcloud storage buckets create gs://${PROJECT_ID}-panels --location=europe-north1 --default-storage-class=STANDARD
gcloud storage buckets create gs://${PROJECT_ID}-versions --location=europe-north1 --default-storage-class=STANDARD
gcloud storage buckets create gs://${PROJECT_ID}-backups --location=europe-north1 --default-storage-class=COLDLINE

# 3. Create service account
gcloud iam service-accounts create gene-panel-storage --display-name="Gene Panel Storage Service Account"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:gene-panel-storage@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"
gcloud iam service-accounts keys create gcs-service-account-key.json --iam-account=gene-panel-storage@${PROJECT_ID}.iam.gserviceaccount.com
```

### Environment Variables
```bash
# Required for GCS
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=gcs-service-account-key.json
PRIMARY_STORAGE_BACKEND=gcs
BACKUP_STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=instance/saved_panels

# Panel management
MAX_PANEL_VERSIONS=10
AUTO_BACKUP_ENABLED=True
BACKUP_RETENTION_DAYS=90
```

### Test Storage Setup
```bash
# Run storage demo
python test_storage_demo.py

# Test individual components
python -c "from app.storage_backends import get_storage_manager; storage = get_storage_manager(); print('✅ Storage initialized')"
```

## Storage Backends Comparison

| Feature | Google Cloud Storage | Local File Storage |
|---------|---------------------|-------------------|
| **Scalability** | Unlimited | Limited by disk space |
| **Reliability** | 99.999999999% durability | Depends on hardware |
| **Cost** | Pay-per-use | No service costs |
| **Setup Complexity** | Moderate (GCP account) | Simple |
| **Backup** | Automatic redundancy | Manual required |
| **Access** | Global | Local only |
| **Performance** | Network dependent | Fast local access |

## Configuration Patterns

### Development (Local Only)
```bash
PRIMARY_STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=instance/dev_panels
BACKUP_STORAGE_BACKEND=none
MAX_PANEL_VERSIONS=3
AUTO_BACKUP_ENABLED=False
```

### Production (GCS Primary + Local Backup)
```bash
PRIMARY_STORAGE_BACKEND=gcs
BACKUP_STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=/app/storage/backup
MAX_PANEL_VERSIONS=10
AUTO_BACKUP_ENABLED=True
BACKUP_RETENTION_DAYS=365
STORAGE_ENCRYPTION_ENABLED=True
```

### Hybrid (GCS + Local Redundancy)
```bash
PRIMARY_STORAGE_BACKEND=gcs
BACKUP_STORAGE_BACKEND=local
STORAGE_FAILOVER_ENABLED=True
STORAGE_RETRY_ATTEMPTS=3
AUTO_BACKUP_ENABLED=True
```

## Common Issues & Solutions

### ❌ "google.auth.exceptions.DefaultCredentialsError"
**Solution**: 
```bash
# Check service account key file
ls -la gcs-service-account-key.json
export GOOGLE_APPLICATION_CREDENTIALS=gcs-service-account-key.json
```

### ❌ "403 Insufficient Permission"
**Solution**:
```bash
# Verify service account role
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:gene-panel-storage@*"
```

### ❌ "404 The specified bucket does not exist"
**Solution**:
```bash
# List and verify buckets
gsutil ls
# Create missing bucket
gcloud storage buckets create gs://your-project-id-panels --location=europe-north1
```

### ❌ "Permission denied" (Local Storage)
**Solution**:
```bash
# Fix directory permissions
mkdir -p instance/saved_panels
chmod 755 instance/saved_panels
chown -R www-data:www-data instance/saved_panels  # For production
```

## Storage Operations Examples

### Save Panel
```python
from app.storage_backends import get_storage_manager

storage = get_storage_manager()
panel_data = {
    "name": "BRCA_Comprehensive",
    "genes": ["BRCA1", "BRCA2"],
    "version": "1.0",
    "created_by": "user123"
}

# Save panel
storage.save_panel(user_id=123, panel_name="BRCA_Comprehensive", data=panel_data)
```

### Load Panel
```python
# Load current version
panel = storage.load_panel(user_id=123, panel_name="BRCA_Comprehensive")

# Load specific version
panel = storage.load_panel_version(user_id=123, panel_name="BRCA_Comprehensive", version="1.0")
```

### List User Panels
```python
# Get all panels for user
panels = storage.list_user_panels(user_id=123)

# Get panel versions
versions = storage.list_panel_versions(user_id=123, panel_name="BRCA_Comprehensive")
```

## Security Notes

1. **Service Account Key**: Never commit `gcs-service-account-key.json` to version control
2. **IAM Roles**: Use least privilege principle - Storage Object Admin only
3. **Bucket Access**: Enable uniform bucket-level access for security
4. **Encryption**: GCS encrypts data at rest by default
5. **Audit Logging**: Enable Cloud Audit Logs for compliance

## Monitoring Commands

```bash
# Check storage usage
gsutil du -sh gs://your-project-id-panels/

# Monitor bucket activity
gcloud logging read 'resource.type="gcs_bucket"' --limit=10

# Check service account activity
gcloud logging read 'protoPayload.authenticationInfo.principalEmail="gene-panel-storage@your-project-id.iam.gserviceaccount.com"' --limit=5
```

## Cost Optimization

1. **Storage Classes**: Use Coldline for backups (90-day minimum)
2. **Lifecycle Policies**: Auto-delete old data after retention period
3. **Regional Buckets**: Choose nearest region to reduce costs
4. **Compression**: Enable for large panel data
5. **Monitoring**: Set up billing alerts

For complete documentation, see:
- [Google Cloud Storage Setup Guide](GOOGLE_CLOUD_STORAGE_SETUP.md)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
