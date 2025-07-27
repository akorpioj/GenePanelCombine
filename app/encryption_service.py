"""
Encryption Service for PanelMerge Application

Provides comprehensive encryption for:
- Sensitive database fields (at rest)
- Session data and cookies
- File uploads and temporary data
- API communications

Uses AES-256-GCM for symmetric encryption and RSA for key exchange.
"""

import os
import base64
import json
from typing import Optional, Union, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    """
    Centralized encryption service for the application.
    
    Provides methods for:
    - Field-level database encryption
    - Session data encryption
    - File encryption
    - Secure key management
    """
    
    def __init__(self):
        self._fernet = None
        self._aes_gcm = None
        self._master_key = None
        self._initialized = False
    
    def initialize(self, app=None):
        """Initialize encryption service with application context"""
        try:
            if app:
                self._master_key = self._get_or_create_master_key(app)
            else:
                self._master_key = self._get_or_create_master_key(current_app)
            
            # Initialize Fernet for general encryption
            self._fernet = Fernet(self._master_key)
            
            # Initialize AES-GCM for high-performance encryption
            self._aes_gcm = AESGCM(self._master_key[:32])  # Use first 32 bytes for AES-256
            
            self._initialized = True
            logger.info("Encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise
    
    def _get_or_create_master_key(self, app) -> bytes:
        """Get or create the master encryption key"""
        # Try to get key from environment first
        env_key = os.getenv('ENCRYPTION_MASTER_KEY')
        if env_key:
            try:
                return base64.urlsafe_b64decode(env_key.encode())
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
        
        # Get key from app config
        config_key = app.config.get('ENCRYPTION_MASTER_KEY')
        if config_key:
            try:
                return base64.urlsafe_b64decode(config_key.encode())
            except Exception as e:
                logger.warning(f"Invalid encryption key in config: {e}")
        
        # Generate new key and save to instance directory
        instance_path = app.config.get('INSTANCE_PATH', 'instance')
        key_file = os.path.join(instance_path, '.encryption_key')
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Could not read existing key file: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Save key to file
        try:
            os.makedirs(instance_path, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Restrict file permissions
            logger.info("Generated new encryption master key")
        except Exception as e:
            logger.error(f"Could not save encryption key: {e}")
        
        return key
    
    def _ensure_initialized(self):
        """Ensure the service is initialized"""
        if not self._initialized:
            raise RuntimeError("Encryption service not initialized. Call initialize() first.")
    
    # Field-level database encryption
    def encrypt_field(self, value: Union[str, bytes, None]) -> Optional[str]:
        """
        Encrypt a database field value.
        
        Args:
            value: The value to encrypt (string, bytes, or None)
            
        Returns:
            Base64-encoded encrypted value or None
        """
        if value is None:
            return None
        
        self._ensure_initialized()
        
        try:
            if isinstance(value, str):
                value = value.encode('utf-8')
            
            encrypted = self._fernet.encrypt(value)
            return base64.urlsafe_b64encode(encrypted).decode('ascii')
            
        except Exception as e:
            logger.error(f"Field encryption failed: {e}")
            raise
    
    def decrypt_field(self, encrypted_value: Optional[str]) -> Optional[str]:
        """
        Decrypt a database field value.
        
        Args:
            encrypted_value: Base64-encoded encrypted value
            
        Returns:
            Decrypted string value or None
        """
        if encrypted_value is None:
            return None
        
        self._ensure_initialized()
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode('ascii'))
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Field decryption failed: {e}")
            # Return None instead of raising to handle corrupted data gracefully
            return None
    
    # JSON data encryption
    def encrypt_json(self, data: Dict[Any, Any]) -> Optional[str]:
        """
        Encrypt a JSON-serializable object.
        
        Args:
            data: Dictionary or other JSON-serializable data
            
        Returns:
            Base64-encoded encrypted JSON string
        """
        if data is None:
            return None
        
        try:
            json_str = json.dumps(data, separators=(',', ':'))
            return self.encrypt_field(json_str)
        except Exception as e:
            logger.error(f"JSON encryption failed: {e}")
            raise
    
    def decrypt_json(self, encrypted_json: Optional[str]) -> Optional[Dict[Any, Any]]:
        """
        Decrypt a JSON object.
        
        Args:
            encrypted_json: Base64-encoded encrypted JSON string
            
        Returns:
            Decrypted dictionary or None
        """
        if encrypted_json is None:
            return None
        
        try:
            json_str = self.decrypt_field(encrypted_json)
            if json_str is None:
                return None
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"JSON decryption failed: {e}")
            return None
    
    # File encryption
    def encrypt_file_content(self, content: bytes) -> bytes:
        """
        Encrypt file content using AES-GCM for better performance.
        
        Args:
            content: Raw file content as bytes
            
        Returns:
            Encrypted content with nonce prepended
        """
        self._ensure_initialized()
        
        try:
            nonce = os.urandom(12)  # 96-bit nonce for GCM
            encrypted = self._aes_gcm.encrypt(nonce, content, None)
            return nonce + encrypted  # Prepend nonce to encrypted data
            
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            raise
    
    def decrypt_file_content(self, encrypted_content: bytes) -> bytes:
        """
        Decrypt file content using AES-GCM.
        
        Args:
            encrypted_content: Encrypted content with nonce prepended
            
        Returns:
            Decrypted file content
        """
        self._ensure_initialized()
        
        try:
            nonce = encrypted_content[:12]  # Extract nonce
            ciphertext = encrypted_content[12:]  # Extract encrypted data
            return self._aes_gcm.decrypt(nonce, ciphertext, None)
            
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            raise
    
    # Session data encryption
    def encrypt_session_data(self, session_data: Dict[str, Any]) -> str:
        """
        Encrypt session data for secure storage.
        
        Args:
            session_data: Session dictionary
            
        Returns:
            Encrypted session token
        """
        return self.encrypt_json(session_data)
    
    def decrypt_session_data(self, encrypted_token: str) -> Optional[Dict[str, Any]]:
        """
        Decrypt session data.
        
        Args:
            encrypted_token: Encrypted session token
            
        Returns:
            Session dictionary or None
        """
        return self.decrypt_json(encrypted_token)
    
    # Key derivation for passwords
    def derive_key_from_password(self, password: str, salt: bytes = None) -> tuple[bytes, bytes]:
        """
        Derive an encryption key from a password using PBKDF2.
        
        Args:
            password: User password
            salt: Salt bytes (generated if None)
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # Recommended minimum
        )
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
    
    # Utility methods
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return base64.urlsafe_b64encode(os.urandom(length)).decode('ascii')
    
    def hash_sensitive_data(self, data: str) -> str:
        """Create a non-reversible hash of sensitive data for indexing"""
        digest = hashes.Hash(hashes.SHA256())
        digest.update(data.encode('utf-8'))
        return base64.urlsafe_b64encode(digest.finalize()).decode('ascii')


# Global encryption service instance
encryption_service = EncryptionService()


def init_encryption(app):
    """Initialize encryption service with Flask app"""
    encryption_service.initialize(app)
    return encryption_service


# Decorators for easy field encryption
class EncryptedField:
    """
    Descriptor for automatic field encryption/decryption in SQLAlchemy models.
    
    Usage:
        class User(db.Model):
            _social_security = db.Column(db.Text)
            social_security = EncryptedField('_social_security')
    """
    
    def __init__(self, field_name: str):
        self.field_name = field_name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        encrypted_value = getattr(obj, self.field_name)
        return encryption_service.decrypt_field(encrypted_value)
    
    def __set__(self, obj, value):
        encrypted_value = encryption_service.encrypt_field(value)
        setattr(obj, self.field_name, encrypted_value)


class EncryptedJSONField:
    """
    Descriptor for automatic JSON encryption/decryption in SQLAlchemy models.
    
    Usage:
        class AuditLog(db.Model):
            _details = db.Column(db.Text)
            details = EncryptedJSONField('_details')
    """
    
    def __init__(self, field_name: str):
        self.field_name = field_name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        encrypted_value = getattr(obj, self.field_name)
        return encryption_service.decrypt_json(encrypted_value)
    
    def __set__(self, obj, value):
        encrypted_value = encryption_service.encrypt_json(value)
        setattr(obj, self.field_name, encrypted_value)
