# Data Encryption Implementation Guide

## Quick Start

This guide provides step-by-step instructions for implementing and using the data encryption system in PanelMerge.

## Prerequisites

- Python 3.8+
- Flask application with SQLAlchemy
- PostgreSQL or SQLite database
- `cryptography>=3.4.8` package

## Installation & Setup

### 1. Install Dependencies

```bash
pip install cryptography>=3.4.8
```

### 2. Initialize Encryption in Your App

```python
# app/__init__.py
from app.encryption_service import init_encryption
from app.security_service import init_security

def create_app():
    app = Flask(__name__)
    
    # Initialize encryption services
    init_encryption(app)
    init_security(app)
    
    return app
```

### 3. Run Database Migration

```bash
# Add encrypted columns to existing tables
python scripts/add_encryption_columns.py

# Migrate existing data (if applicable)
python scripts/migrate_encryption.py
```

## Usage Examples

### Field-Level Encryption

#### Basic Field Encryption

```python
from app.encryption_service import encryption_service

# Encrypt a field
encrypted_value = encryption_service.encrypt_field("sensitive_data")
# Returns: "Z0FBQUFBQm9oZm56..."

# Decrypt a field
decrypted_value = encryption_service.decrypt_field(encrypted_value)
# Returns: "sensitive_data"
```

#### Model Integration

```python
from app.encryption_service import EncryptedField
from app.models import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    
    # Encrypted fields
    _first_name = db.Column('first_name_encrypted', db.Text)
    _last_name = db.Column('last_name_encrypted', db.Text)
    
    # Transparent encryption/decryption
    first_name = EncryptedField('_first_name')
    last_name = EncryptedField('_last_name')

# Usage
user = User(username="john_doe")
user.first_name = "John"  # Automatically encrypted
user.last_name = "Doe"    # Automatically encrypted

db.session.add(user)
db.session.commit()

# Retrieval
user = User.query.first()
print(user.first_name)  # Returns "John" (automatically decrypted)
```

### JSON Encryption

```python
from app.encryption_service import EncryptedJSONField

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Encrypted JSON fields
    _details = db.Column('details_encrypted', db.Text)
    details = EncryptedJSONField('_details')

# Usage
audit = AuditLog()
audit.details = {
    "user_id": 123,
    "action": "login",
    "metadata": {"ip": "192.168.1.1", "browser": "Chrome"}
}

db.session.add(audit)
db.session.commit()

# Retrieval
audit = AuditLog.query.first()
print(audit.details["user_id"])  # Returns 123
```

### File Encryption

```python
from app.secure_file_handler import secure_file_handler
from werkzeug.datastructures import FileStorage

# Initialize file handler
secure_file_handler.init_app(app)

# Save encrypted file
def upload_file(file):
    # Validate file
    validation = secure_file_handler.validate_file(file)
    if not validation['valid']:
        return {"error": validation['errors']}
    
    # Save with encryption
    result = secure_file_handler.secure_save(file, encrypt=True)
    
    return {
        "file_id": result['file_id'],
        "encrypted": result['encrypted'],
        "size": result['file_size']
    }

# Load encrypted file
def download_file(file_id):
    try:
        content = secure_file_handler.secure_load(file_id, decrypt=True)
        return content
    except FileNotFoundError:
        return None
```

## Configuration

### Environment Variables

```bash
# .env file
ENCRYPTION_MASTER_KEY=<base64-encoded-key>
ENCRYPT_SENSITIVE_FIELDS=true
REQUIRE_HTTPS=true
HSTS_MAX_AGE=31536000
SESSION_TIMEOUT=3600
```

### Application Config

```python
# config_settings.py
class Config:
    # Encryption settings
    ENCRYPTION_MASTER_KEY = os.getenv('ENCRYPTION_MASTER_KEY')
    ENCRYPT_SENSITIVE_FIELDS = os.getenv('ENCRYPT_SENSITIVE_FIELDS', 'True').lower() == 'true'
    
    # Security settings
    REQUIRE_HTTPS = os.getenv('REQUIRE_HTTPS', 'False').lower() == 'true'
    HSTS_MAX_AGE = int(os.getenv('HSTS_MAX_AGE', '31536000'))
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))

class ProductionConfig(Config):
    REQUIRE_HTTPS = True
    ENCRYPT_SENSITIVE_FIELDS = True
    SESSION_TIMEOUT = 1800  # 30 minutes
```

## Security Implementation

### CSRF Protection

```python
from app.security_service import security_service, csrf_protect

@app.route('/sensitive-action', methods=['POST'])
@csrf_protect
def sensitive_action():
    # This route is protected against CSRF attacks
    return "Action completed"

# In templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=security_service.generate_csrf_token)
```

```html
<!-- In HTML forms -->
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <!-- form fields -->
</form>
```

### HTTPS Enforcement

```python
from app.security_service import require_https

@app.route('/admin')
@require_https
def admin_panel():
    # This route requires HTTPS
    return render_template('admin.html')
```

### Session Security

```python
# Enhanced session security is automatic
# Sessions include:
# - CSRF token
# - Session timeout validation
# - User agent verification
# - IP address tracking

from flask import session

# Check if user session is valid
if 'user_id' in session:
    # Session security is automatically validated
    user_id = session['user_id']
```

## Database Considerations

### Encrypted Column Types

```sql
-- Use TEXT for encrypted fields (base64-encoded data)
ALTER TABLE user ADD COLUMN first_name_encrypted TEXT;
ALTER TABLE user ADD COLUMN last_name_encrypted TEXT;

-- JSON fields also use TEXT
ALTER TABLE audit_log ADD COLUMN details_encrypted TEXT;
```

### Indexing Encrypted Data

```python
# For searchable encrypted fields, use hashed values
from app.encryption_service import encryption_service

class User(db.Model):
    email = db.Column(db.String(120), unique=True, nullable=False)
    email_hash = db.Column(db.String(64), index=True)  # For searching
    
    _personal_email = db.Column('personal_email_encrypted', db.Text)
    personal_email = EncryptedField('_personal_email')
    
    def set_personal_email(self, email):
        self.personal_email = email
        self.email_hash = encryption_service.hash_sensitive_data(email)

# Search using hash
def find_user_by_personal_email(email):
    email_hash = encryption_service.hash_sensitive_data(email)
    return User.query.filter_by(email_hash=email_hash).first()
```

## Testing

### Unit Tests

```python
import unittest
from app import create_app
from app.models import db
from app.encryption_service import encryption_service

class EncryptionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        encryption_service.initialize(self.app)
        db.create_all()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_field_encryption(self):
        # Test basic encryption
        original = "sensitive_data"
        encrypted = encryption_service.encrypt_field(original)
        decrypted = encryption_service.decrypt_field(encrypted)
        
        self.assertEqual(original, decrypted)
        self.assertNotEqual(original, encrypted)
    
    def test_user_encryption(self):
        # Test model encryption
        user = User(username="test", email="test@example.com")
        user.first_name = "John"
        
        db.session.add(user)
        db.session.commit()
        
        # Reload from database
        user = User.query.first()
        self.assertEqual("John", user.first_name)
```

### Integration Tests

```python
def test_file_encryption():
    with app.test_client() as client:
        # Upload encrypted file
        data = {'file': (BytesIO(b'test content'), 'test.txt')}
        response = client.post('/upload', data=data)
        
        self.assertEqual(response.status_code, 200)
        
        file_id = response.json['file_id']
        
        # Download and verify
        response = client.get(f'/download/{file_id}')
        self.assertEqual(response.data, b'test content')
```

## Error Handling

### Graceful Degradation

```python
from app.encryption_service import encryption_service

def safe_decrypt(encrypted_value):
    """Safely decrypt with fallback"""
    try:
        return encryption_service.decrypt_field(encrypted_value)
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return None  # Or return a default value

def get_user_name(user):
    """Get user name with fallback"""
    first_name = safe_decrypt(user._first_name)
    last_name = safe_decrypt(user._last_name)
    
    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    else:
        return user.username  # Fallback to username
```

### Error Logging

```python
import logging

# Configure encryption logging
logging.getLogger('app.encryption_service').setLevel(logging.INFO)
logging.getLogger('app.security_service').setLevel(logging.INFO)

# Custom error handling
@app.errorhandler(Exception)
def handle_encryption_error(error):
    if "encryption" in str(error).lower():
        logger.error(f"Encryption error: {error}")
        return "Security error occurred", 500
    return "An error occurred", 500
```

## Performance Optimization

### Lazy Loading

```python
class User(db.Model):
    # Only load encrypted fields when accessed
    @property
    def full_profile(self):
        """Load full profile only when needed"""
        if not hasattr(self, '_profile_loaded'):
            # Decrypt all personal fields at once
            self._profile_loaded = True
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'organization': self.organization
        }
```

### Batch Operations

```python
def encrypt_multiple_users(users_data):
    """Efficiently encrypt multiple users"""
    for user_data in users_data:
        user = User(**user_data)
        # Encryption happens automatically on commit
        db.session.add(user)
    
    # Single commit for all users
    db.session.commit()
```

## Monitoring & Maintenance

### Health Checks

```python
@app.route('/health/encryption')
def encryption_health():
    """Check encryption system health"""
    try:
        # Test basic encryption
        test_value = "health_check"
        encrypted = encryption_service.encrypt_field(test_value)
        decrypted = encryption_service.decrypt_field(encrypted)
        
        if decrypted == test_value:
            return {"status": "healthy", "encryption": "ok"}
        else:
            return {"status": "error", "encryption": "failed"}, 500
            
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
```

### Metrics Collection

```python
from flask import g
import time

@app.before_request
def start_timer():
    g.start = time.time()

@app.after_request
def log_encryption_metrics(response):
    """Log encryption performance metrics"""
    if hasattr(g, 'start'):
        duration = time.time() - g.start
        if 'encrypt' in request.endpoint or 'decrypt' in request.endpoint:
            logger.info(f"Encryption operation took {duration:.3f}s")
    return response
```

## Troubleshooting

### Common Issues

1. **Key Not Found**
   ```
   RuntimeError: Encryption service not initialized
   ```
   Solution: Call `init_encryption(app)` in app factory

2. **Database Errors**
   ```
   column "field_encrypted" does not exist
   ```
   Solution: Run migration script

3. **Decryption Failures**
   ```
   InvalidToken: 
   ```
   Solution: Check master key consistency

### Debug Commands

```python
# Check encryption status
def debug_encryption():
    try:
        test = encryption_service.encrypt_field("test")
        print(f"Encryption working: {len(test)} chars")
        
        decrypted = encryption_service.decrypt_field(test)
        print(f"Decryption working: {decrypted}")
        
        return True
    except Exception as e:
        print(f"Encryption error: {e}")
        return False
```

## Security Best Practices

1. **Never log decrypted data**
2. **Use HTTPS in production**
3. **Rotate encryption keys periodically**
4. **Monitor for unusual patterns**
5. **Backup encrypted data securely**
6. **Limit access to encryption keys**
7. **Use strong session management**
8. **Implement proper error handling**

---

This implementation guide provides everything needed to integrate and use the encryption system effectively. Follow the examples and best practices to ensure secure handling of sensitive data.
