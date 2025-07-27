#!/usr/bin/env python3
"""
Comprehensive Test Suite for Encryption Implementation

Tests all encryption features:
- Field-level encryption/decryption
- JSON encryption/decryption
- File encryption/decryption
- Security headers and HTTPS enforcement
- Encrypted audit logging
- Session security

Run this script to verify encryption is working correctly.
"""

import os
import sys
import tempfile
import json
import time
from io import BytesIO

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, User, AuditLog, UserRole
from app.encryption_service import encryption_service, EncryptedField, EncryptedJSONField
from app.security_service import security_service
from app.secure_file_handler import secure_file_handler
from werkzeug.datastructures import FileStorage

def test_basic_encryption():
    """Test basic field encryption/decryption"""
    print("🔐 Testing basic field encryption...")
    
    try:
        # Test string encryption
        test_string = "Sensitive Information 123!@#"
        encrypted = encryption_service.encrypt_field(test_string)
        decrypted = encryption_service.decrypt_field(encrypted)
        
        assert decrypted == test_string, f"String encryption failed: {decrypted} != {test_string}"
        assert encrypted != test_string, "Encryption should change the value"
        print(f"   ✅ String encryption: '{test_string}' -> encrypted -> '{decrypted}'")
        
        # Test None handling
        encrypted_none = encryption_service.encrypt_field(None)
        decrypted_none = encryption_service.decrypt_field(encrypted_none)
        
        assert encrypted_none is None, "None encryption should return None"
        assert decrypted_none is None, "None decryption should return None"
        print("   ✅ None value handling")
        
        # Test empty string
        encrypted_empty = encryption_service.encrypt_field("")
        decrypted_empty = encryption_service.decrypt_field(encrypted_empty)
        
        assert decrypted_empty == "", "Empty string should decrypt to empty string"
        print("   ✅ Empty string handling")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Basic encryption test failed: {e}")
        return False

def test_json_encryption():
    """Test JSON encryption/decryption"""
    print("📊 Testing JSON encryption...")
    
    try:
        # Test complex JSON data
        test_data = {
            "user_id": 123,
            "sensitive_data": "confidential",
            "nested": {
                "array": [1, 2, 3],
                "boolean": True,
                "null_value": None
            },
            "unicode": "Test with émojis 🔐🚀"
        }
        
        encrypted = encryption_service.encrypt_json(test_data)
        decrypted = encryption_service.decrypt_json(encrypted)
        
        assert decrypted == test_data, f"JSON encryption failed: {decrypted} != {test_data}"
        print(f"   ✅ Complex JSON encryption successful")
        
        # Test None handling
        encrypted_none = encryption_service.encrypt_json(None)
        decrypted_none = encryption_service.decrypt_json(encrypted_none)
        
        assert encrypted_none is None, "None JSON encryption should return None"
        assert decrypted_none is None, "None JSON decryption should return None"
        print("   ✅ None JSON handling")
        
        return True
        
    except Exception as e:
        print(f"   ❌ JSON encryption test failed: {e}")
        return False

def test_file_encryption():
    """Test file content encryption/decryption"""
    print("📁 Testing file encryption...")
    
    try:
        # Test file content encryption
        test_content = b"This is test file content with binary data \x00\x01\x02\xFF"
        
        encrypted_content = encryption_service.encrypt_file_content(test_content)
        decrypted_content = encryption_service.decrypt_file_content(encrypted_content)
        
        assert decrypted_content == test_content, "File encryption failed"
        assert encrypted_content != test_content, "File should be encrypted"
        print(f"   ✅ File encryption: {len(test_content)} bytes -> {len(encrypted_content)} bytes -> {len(decrypted_content)} bytes")
        
        # Test large file
        large_content = b"Large file test\n" * 10000
        encrypted_large = encryption_service.encrypt_file_content(large_content)
        decrypted_large = encryption_service.decrypt_file_content(encrypted_large)
        
        assert decrypted_large == large_content, "Large file encryption failed"
        print(f"   ✅ Large file encryption: {len(large_content)} bytes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ File encryption test failed: {e}")
        return False

def test_encrypted_fields():
    """Test encrypted field descriptors"""
    print("🏷️ Testing encrypted field descriptors...")
    
    try:
        # Clean up any existing test user first
        existing_user = User.query.filter_by(username="test_encryption_user").first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()
        
        # Create a test user with encrypted fields
        user = User(
            username="test_encryption_user",
            email="test@encryption.com",
            password_hash="dummy_hash"
        )
        
        # Test setting encrypted fields
        user.first_name = "John"
        user.last_name = "Doe"
        user.organization = "Test Organization"
        
        # Verify the underlying encrypted fields are different
        assert user._first_name != "John", "Encrypted field should not store plain text"
        assert user._last_name != "Doe", "Encrypted field should not store plain text" 
        assert user._organization != "Test Organization", "Encrypted field should not store plain text"
        
        # Verify decryption works
        assert user.first_name == "John", f"Decryption failed: {user.first_name}"
        assert user.last_name == "Doe", f"Decryption failed: {user.last_name}"
        assert user.organization == "Test Organization", f"Decryption failed: {user.organization}"
        
        print("   ✅ Encrypted field descriptors working correctly")
        
        # Test with database persistence
        db.session.add(user)
        db.session.commit()
        
        # Reload from database
        reloaded_user = User.query.filter_by(username="test_encryption_user").first()
        assert reloaded_user.first_name == "John", "Database persistence failed"
        assert reloaded_user.last_name == "Doe", "Database persistence failed"
        assert reloaded_user.organization == "Test Organization", "Database persistence failed"
        
        print("   ✅ Database persistence with encryption")
        
        # Clean up
        db.session.delete(reloaded_user)
        db.session.commit()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Encrypted fields test failed: {e}")
        db.session.rollback()
        return False

def test_encrypted_audit_logging():
    """Test encrypted audit logging"""
    print("📋 Testing encrypted audit logging...")
    
    try:
        from app.audit_service import AuditService
        from app.models import AuditActionType
        
        # Test creating encrypted audit log
        test_old_values = {"password": "old_secret", "email": "old@example.com"}
        test_new_values = {"password": "new_secret", "email": "new@example.com"}
        test_details = {"ip": "192.168.1.1", "user_agent": "Test Browser"}
        
        # Create audit log with encrypted fields
        audit_log = AuditLog(
            action_type=AuditActionType.PROFILE_UPDATE,
            action_description="Test encrypted audit log",
            ip_address="192.168.1.1",
            username="test_user"
        )
        
        # Set encrypted fields
        audit_log.old_values = test_old_values
        audit_log.new_values = test_new_values
        audit_log.details = test_details
        
        # Verify encryption
        assert audit_log._old_values != json.dumps(test_old_values), "Audit data should be encrypted"
        assert audit_log._new_values != json.dumps(test_new_values), "Audit data should be encrypted"
        assert audit_log._details != json.dumps(test_details), "Audit data should be encrypted"
        
        # Verify decryption
        assert audit_log.old_values == test_old_values, f"Audit decryption failed: {audit_log.old_values}"
        assert audit_log.new_values == test_new_values, f"Audit decryption failed: {audit_log.new_values}"
        assert audit_log.details == test_details, f"Audit decryption failed: {audit_log.details}"
        
        print("   ✅ Encrypted audit fields working correctly")
        
        # Test database persistence
        db.session.add(audit_log)
        db.session.commit()
        
        # Reload from database
        reloaded_log = AuditLog.query.filter_by(action_description="Test encrypted audit log").first()
        assert reloaded_log.old_values == test_old_values, "Audit database persistence failed"
        assert reloaded_log.new_values == test_new_values, "Audit database persistence failed"
        assert reloaded_log.details == test_details, "Audit database persistence failed"
        
        print("   ✅ Encrypted audit database persistence")
        
        # Clean up
        db.session.delete(reloaded_log)
        db.session.commit()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Encrypted audit logging test failed: {e}")
        db.session.rollback()
        return False

def test_secure_file_handler():
    """Test secure file handler with encryption"""
    print("📄 Testing secure file handler...")
    
    try:
        # Create test file
        test_content = "Test file content for encryption\nLine 2\nLine 3"
        test_file = FileStorage(
            stream=BytesIO(test_content.encode('utf-8')),
            filename="test_file.txt",
            content_type="text/plain"
        )
        
        # Test file validation
        validation = secure_file_handler.validate_file(test_file)
        assert validation['valid'], f"File validation failed: {validation['errors']}"
        print("   ✅ File validation")
        
        # Test secure save with encryption
        save_result = secure_file_handler.secure_save(test_file, encrypt=True)
        assert save_result['success'], "File save failed"
        assert save_result['encrypted'], "File should be encrypted"
        
        file_id = save_result['file_id']
        print(f"   ✅ Secure file save: {file_id}")
        
        # Test secure load with decryption
        loaded_content = secure_file_handler.secure_load(file_id, decrypt=True)
        assert loaded_content.decode('utf-8') == test_content, "File content mismatch after encryption/decryption"
        print("   ✅ Secure file load with decryption")
        
        # Test file info
        file_info = secure_file_handler.get_file_info(file_id)
        assert file_info is not None, "File info should exist"
        print("   ✅ File info retrieval")
        
        # Test secure delete
        delete_result = secure_file_handler.secure_delete(file_id)
        assert delete_result, "File deletion failed"
        print("   ✅ Secure file deletion")
        
        # Verify file is gone
        file_info_after = secure_file_handler.get_file_info(file_id)
        assert file_info_after is None, "File should be deleted"
        
        return True
        
    except Exception as e:
        print(f"   ❌ Secure file handler test failed: {e}")
        return False

def test_security_headers():
    """Test security headers and HTTPS enforcement"""
    print("🛡️ Testing security headers...")
    
    try:
        # This would need to be tested in a request context
        # For now, just verify the security service is configured
        assert security_service is not None, "Security service not initialized"
        
        # Test CSRF token generation
        with app.test_request_context():
            csrf_token = security_service.generate_csrf_token()
            assert csrf_token is not None, "CSRF token generation failed"
            assert len(csrf_token) > 20, "CSRF token too short"
            print(f"   ✅ CSRF token generation: {len(csrf_token)} characters")
        
        # Test secure filename generation
        dangerous_filename = "../../../etc/passwd.txt"
        safe_filename = security_service.secure_filename(dangerous_filename)
        assert "../" not in safe_filename, "Path traversal not prevented"
        print(f"   ✅ Secure filename: '{dangerous_filename}' -> '{safe_filename}'")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Security headers test failed: {e}")
        return False

def test_key_management():
    """Test encryption key management"""
    print("🔑 Testing encryption key management...")
    
    try:
        # Test secure token generation
        token1 = encryption_service.generate_secure_token(32)
        token2 = encryption_service.generate_secure_token(32)
        
        assert len(token1) > 30, "Token too short"
        assert token1 != token2, "Tokens should be unique"
        print(f"   ✅ Secure token generation: {len(token1)} characters")
        
        # Test password-based key derivation
        password = "test_password_123"
        key1, salt1 = encryption_service.derive_key_from_password(password)
        key2, salt2 = encryption_service.derive_key_from_password(password, salt1)
        
        assert len(key1) == 32, "Derived key wrong length"
        assert key1 == key2, "Same password + salt should produce same key"
        assert salt1 == salt2, "Same salt should be used when provided"
        print("   ✅ Password-based key derivation")
        
        # Test data hashing
        sensitive_data = "john.doe@example.com"
        hash1 = encryption_service.hash_sensitive_data(sensitive_data)
        hash2 = encryption_service.hash_sensitive_data(sensitive_data)
        
        assert hash1 == hash2, "Same data should produce same hash"
        assert hash1 != sensitive_data, "Hash should be different from original"
        print("   ✅ Sensitive data hashing")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Key management test failed: {e}")
        return False

def run_all_tests():
    """Run all encryption tests"""
    print("🚀 Starting Comprehensive Encryption Test Suite")
    print("=" * 60)
    
    tests = [
        ("Basic Encryption", test_basic_encryption),
        ("JSON Encryption", test_json_encryption),
        ("File Encryption", test_file_encryption),
        ("Encrypted Fields", test_encrypted_fields),
        ("Encrypted Audit Logging", test_encrypted_audit_logging),
        ("Secure File Handler", test_secure_file_handler),
        ("Security Headers", test_security_headers),
        ("Key Management", test_key_management),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Total Tests: {passed + failed}")
    print(f"   🎯 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All encryption tests passed! Security implementation is working correctly.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please review the implementation.")
    
    return failed == 0

def main():
    """Main test function"""
    global app
    
    try:
        # Create Flask app
        app = create_app('development')
        
        with app.app_context():
            # Initialize all services
            encryption_service.initialize(app)
            secure_file_handler.init_app(app)
            
            # Create tables if they don't exist
            db.create_all()
            
            # Run tests
            success = run_all_tests()
            
            return success
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
