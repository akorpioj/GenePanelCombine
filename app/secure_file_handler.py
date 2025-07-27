"""
Secure File Handler for PanelMerge Application

Provides secure file handling with:
- Encrypted file storage
- Secure file validation
- Temporary file management
- Safe file operations
"""

import os
import tempfile
import mimetypes
import hashlib
from typing import Optional, BinaryIO, List, Dict, Any
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask import current_app, abort
import logging

from .encryption_service import encryption_service

logger = logging.getLogger(__name__)

class SecureFileHandler:
    """
    Secure file handler with encryption and validation capabilities.
    
    Features:
    - Automatic file encryption
    - File type validation
    - Size limits
    - Secure temporary storage
    - File integrity checking
    """
    
    # Allowed file extensions and their MIME types
    ALLOWED_EXTENSIONS = {
        '.txt': ['text/plain'],
        '.csv': ['text/csv', 'application/csv'],
        '.tsv': ['text/tab-separated-values', 'text/tsv'],
        '.bed': ['text/plain', 'application/octet-stream'],
        '.json': ['application/json'],
        '.xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        '.xls': ['application/vnd.ms-excel']
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_FILENAME_LENGTH = 255
    
    def __init__(self):
        self.temp_dir = None
        self.upload_dir = None
        
    def init_app(self, app):
        """Initialize file handler with Flask app"""
        self.temp_dir = app.config.get('TEMP_UPLOAD_DIR', tempfile.gettempdir())
        self.upload_dir = app.config.get('UPLOAD_DIR', 
                                        os.path.join(app.instance_path, 'uploads'))
        
        # Ensure directories exist
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Set restrictive permissions
        os.chmod(self.temp_dir, 0o700)
        os.chmod(self.upload_dir, 0o700)
        
        logger.info("Secure file handler initialized")
    
    def validate_file(self, file: FileStorage) -> Dict[str, Any]:
        """
        Validate uploaded file for security and format compliance.
        
        Args:
            file: Uploaded file from Flask request
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ValueError: If file validation fails
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        # Check if file exists
        if not file or file.filename == '':
            result['errors'].append("No file provided")
            return result
        
        filename = file.filename
        
        # Validate filename length
        if len(filename) > self.MAX_FILENAME_LENGTH:
            result['errors'].append(f"Filename too long (max {self.MAX_FILENAME_LENGTH} characters)")
        
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        if ext not in self.ALLOWED_EXTENSIONS:
            result['errors'].append(f"File type not allowed: {ext}")
            return result
        
        # Validate MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        allowed_mimes = self.ALLOWED_EXTENSIONS[ext]
        
        if mime_type not in allowed_mimes:
            # Some files might not have correct MIME detection
            result['warnings'].append(f"MIME type '{mime_type}' may not match file extension")
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)     # Reset to beginning
        
        if file_size > self.MAX_FILE_SIZE:
            result['errors'].append(f"File too large: {file_size} bytes (max {self.MAX_FILE_SIZE})")
        
        if file_size == 0:
            result['errors'].append("File is empty")
        
        # Store file info
        result['file_info'] = {
            'filename': filename,
            'size': file_size,
            'extension': ext,
            'mime_type': mime_type
        }
        
        # File is valid if no errors
        result['valid'] = len(result['errors']) == 0
        
        return result
    
    def secure_save(self, file: FileStorage, encrypt: bool = True) -> Dict[str, Any]:
        """
        Securely save uploaded file with optional encryption.
        
        Args:
            file: Uploaded file from Flask request
            encrypt: Whether to encrypt the file content
            
        Returns:
            Dictionary with save results and file metadata
            
        Raises:
            ValueError: If file validation fails
            IOError: If file save fails
        """
        # Validate file first
        validation = self.validate_file(file)
        if not validation['valid']:
            raise ValueError(f"File validation failed: {validation['errors']}")
        
        # Generate secure filename
        original_filename = file.filename
        secure_name = secure_filename(original_filename)
        
        # Add timestamp and hash to prevent conflicts
        timestamp = int(time.time())
        file_hash = hashlib.md5(f"{secure_name}{timestamp}".encode()).hexdigest()[:8]
        
        # Create final filename
        name, ext = os.path.splitext(secure_name)
        final_filename = f"{name}_{timestamp}_{file_hash}{ext}"
        
        try:
            # Read file content
            file.seek(0)
            content = file.read()
            
            # Calculate file hash for integrity
            content_hash = hashlib.sha256(content).hexdigest()
            
            # Encrypt content if requested
            if encrypt:
                content = encryption_service.encrypt_file_content(content)
            
            # Save to upload directory
            file_path = os.path.join(self.upload_dir, final_filename)
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Set restrictive file permissions
            os.chmod(file_path, 0o600)
            
            # Prepare result
            result = {
                'success': True,
                'file_id': final_filename,
                'file_path': file_path,
                'original_filename': original_filename,
                'file_size': len(content),
                'content_hash': content_hash,
                'encrypted': encrypt,
                'validation': validation
            }
            
            logger.info(f"File saved securely: {original_filename} -> {final_filename}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to save file {original_filename}: {e}")
            raise IOError(f"File save failed: {e}")
    
    def secure_load(self, file_id: str, decrypt: bool = True) -> bytes:
        """
        Securely load file content with optional decryption.
        
        Args:
            file_id: File identifier from secure_save
            decrypt: Whether to decrypt the file content
            
        Returns:
            File content as bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If decryption fails
        """
        file_path = os.path.join(self.upload_dir, file_id)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_id}")
        
        # Security check - ensure file is within upload directory
        real_path = os.path.realpath(file_path)
        real_upload_dir = os.path.realpath(self.upload_dir)
        
        if not real_path.startswith(real_upload_dir):
            raise ValueError("Path traversal attempt detected")
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Decrypt if requested
            if decrypt:
                content = encryption_service.decrypt_file_content(content)
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to load file {file_id}: {e}")
            raise
    
    def secure_delete(self, file_id: str) -> bool:
        """
        Securely delete file with overwriting.
        
        Args:
            file_id: File identifier from secure_save
            
        Returns:
            True if deletion successful
        """
        file_path = os.path.join(self.upload_dir, file_id)
        
        if not os.path.exists(file_path):
            logger.warning(f"File not found for deletion: {file_id}")
            return False
        
        try:
            # Security check
            real_path = os.path.realpath(file_path)
            real_upload_dir = os.path.realpath(self.upload_dir)
            
            if not real_path.startswith(real_upload_dir):
                logger.error(f"Path traversal attempt in delete: {file_id}")
                return False
            
            # Overwrite file content before deletion for security
            file_size = os.path.getsize(file_path)
            with open(file_path, 'r+b') as f:
                f.write(b'\x00' * file_size)
                f.flush()
                os.fsync(f.fileno())
            
            # Delete file
            os.remove(file_path)
            logger.info(f"File securely deleted: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata without loading content.
        
        Args:
            file_id: File identifier from secure_save
            
        Returns:
            File metadata dictionary or None if not found
        """
        file_path = os.path.join(self.upload_dir, file_id)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            stat = os.stat(file_path)
            return {
                'file_id': file_id,
                'file_path': file_path,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'permissions': oct(stat.st_mode)[-3:]
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {file_id}: {e}")
            return None
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age in hours before deletion
        """
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        cleaned_count = 0
        
        try:
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_time:
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to clean temp file {filename}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} temporary files")
                
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")


# Global file handler instance
secure_file_handler = SecureFileHandler()


def init_file_handler(app):
    """Initialize secure file handler with Flask app"""
    secure_file_handler.init_app(app)
    return secure_file_handler


# Import time for timestamp generation
import time
