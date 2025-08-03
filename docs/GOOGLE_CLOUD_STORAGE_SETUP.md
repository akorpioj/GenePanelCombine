# Google Cloud Storage Setup Guide

This guide walks you through setting up Google Cloud Storage for the PanelMerge saved panel library system.

## Overview

The PanelMerge application uses Google Cloud Storage (GCS) as the primary storage backend for user-saved panels, with local file system as a backup. This provides scalable, reliable, and cost-effective storage for panel data.

## Architecture

### Storage Buckets

Three GCS buckets are used for different types of data:

1. **`gene-panel-combine-panels`** (Standard storage)
   - Stores active panel data
   - Frequently accessed current panels
   - Fast retrieval for user operations

2. **`gene-panel-combine-versions`** (Standard storage)
   - Stores panel version history
   - Version control and diff operations
   - Moderately frequent access

3. **`gene-panel-combine-backups`** (Coldline storage)
   - Long-term panel backups
   - Disaster recovery
   - Infrequent access, cost-optimized

### Service Account vs User Authentication

- **Service Account Name**: `gene-panel-storage`
- **Service Account Role**: Storage Object Admin  
- **Service Account Purpose**: Provides secure access to GCS buckets for production deployments
- **Service Account Key File**: `gcs-service-account-key.json` (production environments)
- **User Authentication**: Alternative for development using `gcloud auth login` (no key file required)

## Prerequisites

1. **Google Cloud Platform Account**
   - Active GCP project
   - Billing enabled
   - Cloud Storage API enabled

2. **Google Cloud CLI (gcloud)**
   - Installed and configured
   - Authenticated with your GCP account

3. **Python Environment**
   - `google-cloud-storage` package installed
   - Flask application with proper configuration

## Step-by-Step Setup

### 1. Enable Required APIs

```bash
# Enable Cloud Storage API
gcloud services enable storage.googleapis.com

# Verify enabled services
gcloud services list --enabled --filter="name:storage"
```

### 2. Create Storage Buckets

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Create main panels bucket (Standard storage)
gcloud storage buckets create gs://${PROJECT_ID}-panels \
  --location=europe-north1 \
  --default-storage-class=STANDARD

# Create versions bucket (Standard storage)
gcloud storage buckets create gs://${PROJECT_ID}-versions \
  --location=europe-north1 \
  --default-storage-class=STANDARD

# Create backups bucket (Coldline storage for cost optimization)
gcloud storage buckets create gs://${PROJECT_ID}-backups \
  --location=europe-north1 \
  --default-storage-class=COLDLINE
```

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create gene-panel-storage \
  --display-name="Gene Panel Storage Service Account" \
  --description="Service account for managing saved panel storage in Google Cloud Storage"

# Grant Storage Object Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:gene-panel-storage@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

### 4. Authentication Setup

You have two options for authentication:

#### Option A: Service Account Authentication (Production)

```bash
# Generate and download service account key
gcloud iam service-accounts keys create gcs-service-account-key.json \
  --iam-account=gene-panel-storage@${PROJECT_ID}.iam.gserviceaccount.com
```

**⚠️ Security Note**: Keep this key file secure and never commit it to version control. It's already included in `.gitignore`.

#### Option B: User Authentication (Development)

```bash
# Authenticate with your user account
gcloud auth login

# Grant your user account Storage Object Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:your-email@gmail.com" \
  --role="roles/storage.objectAdmin"

# Verify permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --filter="bindings.members:user:your-email@gmail.com" \
  --format="value(bindings.role)" | grep storage
```

This approach is recommended for development as it:
- Eliminates the need to manage service account key files
- Uses your existing authenticated gcloud session
- Reduces security risks from key file exposure
- Automatically works with other Google Cloud services

### 5. Configure Application

#### Environment Variables (.env)

**For Production (Service Account Authentication):**

```bash
# Google Cloud Storage Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=gcs-service-account-key.json

# Storage Backend Configuration
PRIMARY_STORAGE_BACKEND=gcs
BACKUP_STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=instance/saved_panels

# Panel Storage Configuration
MAX_PANEL_VERSIONS=10
AUTO_BACKUP_ENABLED=True
BACKUP_RETENTION_DAYS=90
```

**For Development (User Authentication):**

```bash
# Google Cloud Storage Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_APPLICATION_CREDENTIALS=gcs-service-account-key.json  # Commented out to use user auth

# Storage Backend Configuration
PRIMARY_STORAGE_BACKEND=gcs
BACKUP_STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=instance/saved_panels

# Panel Storage Configuration
MAX_PANEL_VERSIONS=10
AUTO_BACKUP_ENABLED=True
BACKUP_RETENTION_DAYS=90
```

**Important**: When using user authentication, comment out or remove the `GOOGLE_APPLICATION_CREDENTIALS` line to prevent conflicts with other Google Cloud services (like Cloud SQL).

#### Update Bucket Names

If you used a different project ID or naming convention, update the bucket names in `app/storage_backends.py`:

```python
# Update these lines in GoogleCloudStorageBackend.__init__()
self.panels_bucket_name = "your-project-id-panels"
self.versions_bucket_name = "your-project-id-versions"  
self.backups_bucket_name = "your-project-id-backups"
```

## Testing the Setup

### 1. Test Storage Backend

Run the demo script to verify your setup:

```bash
python test_storage_demo.py
```

Expected output:
```
🚀 PanelMerge Storage Backend Demo
==================================================
✅ Storage manager initialized
📁 Saving panel 'BRCA_COMPREHENSIVE' for user 123...
✅ Panel saved to: gs://your-project-panels/user_123/BRCA_COMPREHENSIVE/current.json
...
🎉 Storage backend demo completed successfully!
```

### 2. Verify Bucket Contents

```bash
# List contents of panels bucket
gsutil ls gs://your-project-id-panels/

# List contents with details
gsutil ls -l gs://your-project-id-panels/user_123/
```

### 3. Test from Python

```python
from app.storage_backends import get_storage_manager

# Initialize storage manager
storage = get_storage_manager()

# Test basic operations
test_data = {"test": "data", "timestamp": "2025-08-03"}
storage.save_panel(123, "test_panel", test_data)
loaded = storage.load_panel(123, "test_panel")
print(f"Test successful: {loaded['test']}")
```

## Production Deployment

### 1. Workload Identity (Recommended)

For production deployments on Google Cloud (Cloud Run, GKE, etc.), use Workload Identity instead of service account keys:

```bash
# Enable Workload Identity
gcloud container clusters update CLUSTER_NAME \
  --workload-pool=PROJECT_ID.svc.id.goog

# Create Kubernetes service account
kubectl create serviceaccount gene-panel-storage

# Bind to Google service account
gcloud iam service-accounts add-iam-policy-binding \
  gene-panel-storage@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/gene-panel-storage]"

# Annotate Kubernetes service account
kubectl annotate serviceaccount gene-panel-storage \
  iam.gke.io/gcp-service-account=gene-panel-storage@PROJECT_ID.iam.gserviceaccount.com
```

### 2. Environment-Specific Configuration

Set environment variables in your production environment:

```bash
# Production environment variables
export GOOGLE_CLOUD_PROJECT="your-project-id"
export PRIMARY_STORAGE_BACKEND="gcs"
export BACKUP_STORAGE_BACKEND="local"
# Don't set GOOGLE_APPLICATION_CREDENTIALS when using Workload Identity
```

## Security Best Practices

### 1. Service Account Permissions

- **Principle of Least Privilege**: Only grant Storage Object Admin role
- **Scope**: Limit to specific buckets if possible
- **Rotation**: Regularly rotate service account keys

### 2. Bucket Security

```bash
# Enable uniform bucket-level access
gsutil uniformbucketlevelaccess set on gs://your-project-id-panels/
gsutil uniformbucketlevelaccess set on gs://your-project-id-versions/
gsutil uniformbucketlevelaccess set on gs://your-project-id-backups/

# Set lifecycle policies for cost optimization
gsutil lifecycle set lifecycle-config.json gs://your-project-id-backups/
```

Example lifecycle configuration (`lifecycle-config.json`):

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 2555}
      }
    ]
  }
}
```

### 3. Data Encryption

- **Encryption at Rest**: Enabled by default in GCS
- **Encryption in Transit**: Always used with HTTPS
- **Customer-Managed Keys**: Optional for additional security

## Monitoring and Logging

### 1. Enable Audit Logs

```bash
# Enable Cloud Storage audit logs
gcloud logging sinks create storage-audit-sink \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/audit_logs \
  --log-filter='protoPayload.serviceName="storage.googleapis.com"'
```

### 2. Set Up Monitoring

```bash
# Create alerting policy for storage errors
gcloud alpha monitoring policies create \
  --policy-from-file=storage-alerting-policy.yaml
```

### 3. Cost Monitoring

- Monitor storage usage in GCP Console
- Set up billing alerts
- Review storage class optimization opportunities

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```
   google.auth.exceptions.DefaultCredentialsError: File gcs-service-account-key.json was not found
   ```
   **Solutions**:
   - **For Service Account Auth**: Verify `GOOGLE_APPLICATION_CREDENTIALS` path and ensure key file exists
   - **For User Auth**: Comment out `GOOGLE_APPLICATION_CREDENTIALS` in `.env` and run `gcloud auth login`
   - Ensure gcloud is authenticated: `gcloud auth list`

2. **Cloud SQL Connection Conflicts**
   ```
   google.auth.exceptions.DefaultCredentialsError when connecting to Cloud SQL
   ```
   **Root Cause**: GCS service account key is being used for Cloud SQL authentication
   **Solutions**:
   - **Development**: Comment out `GOOGLE_APPLICATION_CREDENTIALS` to use user authentication for both services
   - **Production**: Create service account with both Cloud SQL and Storage permissions
   - **Verify user permissions**: `gcloud projects get-iam-policy PROJECT_ID --filter="bindings.members:user:YOUR_EMAIL" --format="value(bindings.role)"`

3. **Permission Denied**
   ```
   google.api_core.exceptions.PermissionDenied: 403 Insufficient Permission
   ```
   - **Service Account**: Verify service account has Storage Object Admin role
   - **User Account**: Grant Storage Object Admin role to your user account
   - Check bucket names are correct
   - Ensure Storage API is enabled

4. **Bucket Not Found**
   ```
   google.api_core.exceptions.NotFound: 404 The specified bucket does not exist
   ```
   - Verify bucket names in configuration
   - Check buckets exist: `gsutil ls`
   - Ensure correct project is set

4. **Performance Issues**
   - Check network connectivity
   - Consider regional bucket locations
   - Monitor request patterns for optimization

### Debug Mode

Enable debug logging in your application:

```python
import logging
logging.getLogger('google.cloud.storage').setLevel(logging.DEBUG)
```

## Cost Optimization

### Storage Classes

- **Standard**: Active panel data (frequent access)
- **Coldline**: Backups (infrequent access, 90-day minimum)
- **Archive**: Long-term retention (annual access)

### Lifecycle Management

Automatically transition or delete old data:

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 90}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 2555}
      }
    ]
  }
}
```

## Backup and Disaster Recovery

### 1. Cross-Region Replication

```bash
# Enable cross-region replication for critical data
gsutil cp -r gs://your-project-id-panels gs://your-project-id-panels-backup
```

### 2. Export to BigQuery

```bash
# Schedule regular exports to BigQuery for analytics
bq mk --dataset PROJECT_ID:panel_analytics
```

### 3. Local Backup Strategy

The application automatically maintains local backups when `BACKUP_STORAGE_BACKEND=local` is configured.

## Support and Resources

- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Python Client Library](https://cloud.google.com/storage/docs/reference/libraries#client-libraries-usage-python)
- [Storage Pricing](https://cloud.google.com/storage/pricing)
- [Best Practices](https://cloud.google.com/storage/docs/best-practices)

For project-specific support, check the PanelMerge documentation or contact the development team.
