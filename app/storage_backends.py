"""
PanelMerge - Storage Backend Abstraction Layer
Provides multiple storage backends for saved panel library system
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, BinaryIO
from datetime import datetime
from google.cloud import storage
from google.cloud.exceptions import NotFound, GoogleCloudError

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    def save_panel(self, user_id: int, panel_id: str, panel_data: Dict, version: str = None) -> str:
        """Save panel data and return storage path"""
        pass
    
    @abstractmethod
    def load_panel(self, user_id: int, panel_id: str, version: str = None) -> Dict:
        """Load panel data"""
        pass
    
    @abstractmethod
    def delete_panel(self, user_id: int, panel_id: str, version: str = None) -> bool:
        """Delete panel data"""
        pass
    
    @abstractmethod
    def list_panel_versions(self, user_id: int, panel_id: str) -> List[str]:
        """List all versions of a panel"""
        pass
    
    @abstractmethod
    def create_backup(self, user_id: int, panel_id: str) -> str:
        """Create backup of panel"""
        pass


class LocalFileStorageBackend(StorageBackend):
    """Local file system storage backend"""
    
    def __init__(self, base_path: str = "instance/saved_panels"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    def _get_panel_path(self, user_id: int, panel_id: str, version: str = None) -> str:
        """Get file path for panel"""
        user_dir = os.path.join(self.base_path, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        
        if version:
            return os.path.join(user_dir, f"{panel_id}_v{version}.json")
        return os.path.join(user_dir, f"{panel_id}.json")
    
    def save_panel(self, user_id: int, panel_id: str, panel_data: Dict, version: str = None) -> str:
        """Save panel data to local file"""
        try:
            file_path = self._get_panel_path(user_id, panel_id, version)
            
            # Add metadata
            panel_data['_metadata'] = {
                'saved_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'panel_id': panel_id,
                'version': version,
                'storage_backend': 'local'
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(panel_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Panel saved locally: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save panel locally: {e}")
            raise
    
    def load_panel(self, user_id: int, panel_id: str, version: str = None) -> Dict:
        """Load panel data from local file"""
        try:
            file_path = self._get_panel_path(user_id, panel_id, version)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Panel not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                panel_data = json.load(f)
            
            logger.info(f"Panel loaded locally: {file_path}")
            return panel_data
            
        except Exception as e:
            logger.error(f"Failed to load panel locally: {e}")
            raise
    
    def delete_panel(self, user_id: int, panel_id: str, version: str = None) -> bool:
        """Delete panel data from local file"""
        try:
            file_path = self._get_panel_path(user_id, panel_id, version)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Panel deleted locally: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete panel locally: {e}")
            raise
    
    def list_panel_versions(self, user_id: int, panel_id: str) -> List[str]:
        """List all versions of a panel"""
        try:
            user_dir = os.path.join(self.base_path, f"user_{user_id}")
            
            if not os.path.exists(user_dir):
                return []
            
            versions = []
            for filename in os.listdir(user_dir):
                if filename.startswith(f"{panel_id}_v") and filename.endswith('.json'):
                    version = filename.replace(f"{panel_id}_v", "").replace(".json", "")
                    versions.append(version)
            
            return sorted(versions)
            
        except Exception as e:
            logger.error(f"Failed to list panel versions locally: {e}")
            return []
    
    def create_backup(self, user_id: int, panel_id: str) -> str:
        """Create backup of panel"""
        try:
            # For local storage, backup is just a copy with timestamp
            panel_data = self.load_panel(user_id, panel_id)
            backup_version = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.save_panel(user_id, panel_id, panel_data, backup_version)
            
            logger.info(f"Panel backup created locally: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create panel backup locally: {e}")
            raise


class GoogleCloudStorageBackend(StorageBackend):
    """Google Cloud Storage backend"""
    
    def __init__(self, project_id: str, credentials_path: str = None):
        self.project_id = project_id
        
        # Initialize client with service account key
        if credentials_path and os.path.exists(credentials_path):
            self.client = storage.Client.from_service_account_json(credentials_path, project=project_id)
        else:
            # Use default credentials (for Cloud Run, etc.)
            self.client = storage.Client(project=project_id)
        
        # Bucket names
        self.panels_bucket_name = "gene-panel-combine-panels"
        self.versions_bucket_name = "gene-panel-combine-versions"
        self.backups_bucket_name = "gene-panel-combine-backups"
        
        # Initialize buckets
        self._init_buckets()
    
    def _init_buckets(self):
        """Initialize bucket references"""
        try:
            self.panels_bucket = self.client.bucket(self.panels_bucket_name)
            self.versions_bucket = self.client.bucket(self.versions_bucket_name)
            self.backups_bucket = self.client.bucket(self.backups_bucket_name)
            
            logger.info("Google Cloud Storage buckets initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS buckets: {e}")
            raise
    
    def _get_blob_path(self, user_id: int, panel_id: str, version: str = None) -> str:
        """Get blob path for panel"""
        if version:
            return f"user_{user_id}/{panel_id}/v{version}.json"
        return f"user_{user_id}/{panel_id}/current.json"
    
    def save_panel(self, user_id: int, panel_id: str, panel_data: Dict, version: str = None) -> str:
        """Save panel data to Google Cloud Storage"""
        try:
            # Choose bucket based on whether this is a version
            bucket = self.versions_bucket if version else self.panels_bucket
            blob_path = self._get_blob_path(user_id, panel_id, version)
            
            # Add metadata
            panel_data['_metadata'] = {
                'saved_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'panel_id': panel_id,
                'version': version,
                'storage_backend': 'gcs',
                'bucket': bucket.name
            }
            
            # Create blob and upload
            blob = bucket.blob(blob_path)
            blob.metadata = {
                'user_id': str(user_id),
                'panel_id': panel_id,
                'version': version or 'current',
                'content_type': 'application/json'
            }
            
            blob.upload_from_string(
                json.dumps(panel_data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            
            logger.info(f"Panel saved to GCS: gs://{bucket.name}/{blob_path}")
            return f"gs://{bucket.name}/{blob_path}"
            
        except GoogleCloudError as e:
            logger.error(f"Failed to save panel to GCS: {e}")
            raise
    
    def load_panel(self, user_id: int, panel_id: str, version: str = None) -> Dict:
        """Load panel data from Google Cloud Storage"""
        try:
            # Choose bucket based on whether this is a version
            bucket = self.versions_bucket if version else self.panels_bucket
            blob_path = self._get_blob_path(user_id, panel_id, version)
            
            blob = bucket.blob(blob_path)
            
            if not blob.exists():
                raise NotFound(f"Panel not found: gs://{bucket.name}/{blob_path}")
            
            panel_data = json.loads(blob.download_as_text())
            
            logger.info(f"Panel loaded from GCS: gs://{bucket.name}/{blob_path}")
            return panel_data
            
        except GoogleCloudError as e:
            logger.error(f"Failed to load panel from GCS: {e}")
            raise
    
    def delete_panel(self, user_id: int, panel_id: str, version: str = None) -> bool:
        """Delete panel data from Google Cloud Storage"""
        try:
            # Choose bucket based on whether this is a version
            bucket = self.versions_bucket if version else self.panels_bucket
            blob_path = self._get_blob_path(user_id, panel_id, version)
            
            blob = bucket.blob(blob_path)
            
            if blob.exists():
                blob.delete()
                logger.info(f"Panel deleted from GCS: gs://{bucket.name}/{blob_path}")
                return True
            
            return False
            
        except GoogleCloudError as e:
            logger.error(f"Failed to delete panel from GCS: {e}")
            raise
    
    def list_panel_versions(self, user_id: int, panel_id: str) -> List[str]:
        """List all versions of a panel"""
        try:
            prefix = f"user_{user_id}/{panel_id}/"
            blobs = self.versions_bucket.list_blobs(prefix=prefix)
            
            versions = []
            for blob in blobs:
                # Extract version from blob name (e.g., "user_1/panel_123/v1.0.json" -> "1.0")
                if blob.name.endswith('.json') and '/v' in blob.name:
                    version = blob.name.split('/v')[-1].replace('.json', '')
                    versions.append(version)
            
            return sorted(versions)
            
        except GoogleCloudError as e:
            logger.error(f"Failed to list panel versions from GCS: {e}")
            return []
    
    def create_backup(self, user_id: int, panel_id: str) -> str:
        """Create backup of panel"""
        try:
            # Load current panel
            panel_data = self.load_panel(user_id, panel_id)
            
            # Create backup with timestamp
            backup_timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_path = f"user_{user_id}/{panel_id}/backup_{backup_timestamp}.json"
            
            # Add backup metadata
            panel_data['_metadata']['backup_created'] = datetime.utcnow().isoformat()
            panel_data['_metadata']['backup_type'] = 'automated'
            
            # Save to backup bucket
            blob = self.backups_bucket.blob(backup_path)
            blob.metadata = {
                'user_id': str(user_id),
                'panel_id': panel_id,
                'backup_timestamp': backup_timestamp,
                'content_type': 'application/json'
            }
            
            blob.upload_from_string(
                json.dumps(panel_data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            
            logger.info(f"Panel backup created in GCS: gs://{self.backups_bucket.name}/{backup_path}")
            return f"gs://{self.backups_bucket.name}/{backup_path}"
            
        except GoogleCloudError as e:
            logger.error(f"Failed to create panel backup in GCS: {e}")
            raise


class StorageManager:
    """Storage manager that handles multiple backends"""
    
    def __init__(self, primary_backend: StorageBackend, backup_backend: StorageBackend = None):
        self.primary_backend = primary_backend
        self.backup_backend = backup_backend
    
    def save_panel(self, user_id: int, panel_id: str, panel_data: Dict, version: str = None) -> str:
        """Save panel using primary backend"""
        try:
            result = self.primary_backend.save_panel(user_id, panel_id, panel_data, version)
            
            # Optionally save to backup backend
            if self.backup_backend:
                try:
                    self.backup_backend.save_panel(user_id, panel_id, panel_data, version)
                except Exception as e:
                    logger.warning(f"Failed to save to backup backend: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to save panel: {e}")
            raise
    
    def load_panel(self, user_id: int, panel_id: str, version: str = None) -> Dict:
        """Load panel from primary backend, fallback to backup if needed"""
        try:
            return self.primary_backend.load_panel(user_id, panel_id, version)
            
        except Exception as e:
            logger.warning(f"Failed to load from primary backend: {e}")
            
            # Try backup backend if available
            if self.backup_backend:
                try:
                    logger.info("Attempting to load from backup backend")
                    return self.backup_backend.load_panel(user_id, panel_id, version)
                except Exception as backup_e:
                    logger.error(f"Failed to load from backup backend: {backup_e}")
            
            raise e
    
    def delete_panel(self, user_id: int, panel_id: str, version: str = None) -> bool:
        """Delete panel from all backends"""
        primary_deleted = False
        backup_deleted = False
        
        try:
            primary_deleted = self.primary_backend.delete_panel(user_id, panel_id, version)
        except Exception as e:
            logger.error(f"Failed to delete from primary backend: {e}")
        
        if self.backup_backend:
            try:
                backup_deleted = self.backup_backend.delete_panel(user_id, panel_id, version)
            except Exception as e:
                logger.warning(f"Failed to delete from backup backend: {e}")
        
        return primary_deleted or backup_deleted
    
    def list_panel_versions(self, user_id: int, panel_id: str) -> List[str]:
        """List panel versions from primary backend"""
        return self.primary_backend.list_panel_versions(user_id, panel_id)
    
    def create_backup(self, user_id: int, panel_id: str) -> str:
        """Create backup using primary backend"""
        return self.primary_backend.create_backup(user_id, panel_id)


def get_storage_backend(backend_type: str = None) -> StorageBackend:
    """Factory function to get storage backend"""
    if backend_type is None:
        backend_type = os.getenv('STORAGE_BACKEND', 'local')
    
    if backend_type == 'gcs':
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'gene-panel-combine')
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'gcs-service-account-key.json')
        return GoogleCloudStorageBackend(project_id, credentials_path)
    
    elif backend_type == 'local':
        base_path = os.getenv('LOCAL_STORAGE_PATH', 'instance/saved_panels')
        return LocalFileStorageBackend(base_path)
    
    else:
        raise ValueError(f"Unsupported storage backend: {backend_type}")


def get_storage_manager() -> StorageManager:
    """Get configured storage manager"""
    primary_backend_type = os.getenv('PRIMARY_STORAGE_BACKEND', 'gcs')
    backup_backend_type = os.getenv('BACKUP_STORAGE_BACKEND', 'local')
    
    primary_backend = get_storage_backend(primary_backend_type)
    
    backup_backend = None
    if backup_backend_type and backup_backend_type != primary_backend_type:
        try:
            backup_backend = get_storage_backend(backup_backend_type)
        except Exception as e:
            logger.warning(f"Failed to initialize backup backend: {e}")
    
    return StorageManager(primary_backend, backup_backend)
