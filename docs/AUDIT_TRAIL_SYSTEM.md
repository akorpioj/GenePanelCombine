# Audit Trail System Documentation

## Overview

The PanelMerge application includes a comprehensive audit trail system that tracks all user actions, system changes, and security events. This system provides complete visibility into application usage for compliance, security monitoring, and troubleshooting purposes.

## Features

### Comprehensive Logging
- **User Authentication**: Login attempts, logout events, registration activities
- **Data Operations**: Panel downloads, uploads, searches, and modifications
- **Administrative Actions**: User management, system configuration changes
- **Security Events**: Failed login attempts, permission changes, suspicious activities
- **System Events**: Errors, cache operations, performance metrics

### Advanced Admin Interface
- **Filtering**: Filter logs by action type, user, date range, success status
- **Pagination**: Efficient handling of large log datasets
- **Detailed Views**: Expandable details showing complete context for each action
- **Export Functionality**: CSV export for external analysis and reporting
- **Real-time Updates**: Live view of ongoing system activities

### Compliance & Security
- **Complete Audit Trail**: Every action is logged with full context
- **IP Address Tracking**: Proxy-aware IP detection for security monitoring
- **Session Correlation**: Track user activities across sessions
- **Data Integrity**: Immutable log entries with comprehensive metadata
- **Error Handling**: Robust logging that doesn't affect application performance

## Architecture

### Database Schema

The audit system uses a dedicated `audit_log` table with the following structure:

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,                    -- Reference to user (nullable for anonymous)
    username VARCHAR(80),               -- Username for quick reference
    action_type VARCHAR(15) NOT NULL,   -- Type of action performed
    action_description VARCHAR(500),    -- Human-readable description
    ip_address VARCHAR(45),             -- Client IP address
    user_agent VARCHAR(500),            -- Browser/client information
    session_id VARCHAR(200),            -- Session identifier
    resource_type VARCHAR(50),          -- Type of resource affected
    resource_id VARCHAR(100),           -- ID of affected resource
    old_values TEXT,                    -- Previous values (JSON)
    new_values TEXT,                    -- New values (JSON)
    details TEXT,                       -- Additional context (JSON)
    timestamp TIMESTAMP NOT NULL,       -- When action occurred
    success BOOLEAN NOT NULL,           -- Whether action succeeded
    error_message VARCHAR(1000),        -- Error details if failed
    duration_ms INTEGER                 -- Action duration in milliseconds
);
```

### Action Types

The system tracks the following action types:

| Action Type | Description |
|-------------|-------------|
| `LOGIN` | User login attempts |
| `LOGOUT` | User logout events |
| `REGISTER` | New user registrations |
| `PROFILE_UPDATE` | User profile modifications |
| `PASSWORD_CHANGE` | Password change events |
| `PANEL_DOWNLOAD` | Gene panel downloads |
| `PANEL_UPLOAD` | Panel file uploads |
| `PANEL_DELETE` | Panel deletions |
| `SEARCH` | Search operations |
| `VIEW` | Panel view operations |
| `ADMIN_ACTION` | Administrative actions |
| `USER_CREATE` | New user account creation |
| `USER_UPDATE` | User account modifications |
| `USER_DELETE` | User account deletions |
| `ROLE_CHANGE` | User role modifications |
| `CACHE_CLEAR` | Cache operations |
| `CONFIG_CHANGE` | Configuration modifications |
| `DATA_EXPORT` | Data export operations |
| `ERROR` | System errors and exceptions |

## Implementation

### Core Components

#### 1. AuditService Class (`app/audit_service.py`)

The main service class provides static methods for logging different types of actions:

```python
from app.audit_service import AuditService
from app.models import AuditActionType

# Log a user login
AuditService.log_login(username="user@example.com", success=True)

# Log a panel download
AuditService.log_panel_download(
    panel_ids="123,456", 
    list_types="diagnostic,research", 
    gene_count=150
)

# Log an admin action
AuditService.log_admin_action(
    action_description="Updated user permissions",
    target_user_id=42,
    details={"permissions": ["read", "write"]}
)
```

#### 2. AuditContext Manager

For automatic timing and error handling:

```python
from app.audit_service import AuditContext
from app.models import AuditActionType

with AuditContext(
    action_type=AuditActionType.PANEL_DOWNLOAD,
    action_description="Downloading gene panel data"
) as audit:
    # Your code here - timing and error logging is automatic
    result = download_panel_data()
```

#### 3. Audit Decorator

For function-level auditing:

```python
from app.audit_service import audit_action
from app.models import AuditActionType

@audit_action(
    action_type=AuditActionType.PANEL_UPLOAD,
    description="Processing uploaded panel file"
)
def process_panel_upload(file_data):
    # Function execution is automatically audited
    return process_file(file_data)
```

### Integration Points

#### Authentication Routes (`app/auth/routes.py`)
- Login/logout tracking with success/failure status
- Registration events with user details
- Password change logging
- Profile update tracking

#### Main Application Routes (`app/main/routes.py`)
- Panel download logging with metadata
- Panel upload and deletion tracking
- Panel view logging
- Search operation tracking
- Cache clear operations
- Error logging for failed operations

#### Admin Interface (`app/auth/routes.py`)
- User management actions (create, update, delete)
- Role change operations
- Audit log viewing and filtering
- CSV export functionality with export tracking

## Admin Interface

### Accessing Audit Logs

1. **Login as Admin**: Access requires admin privileges
2. **Navigate to Admin Panel**: Available in main navigation for admin users
3. **Select "Audit Logs"**: View comprehensive audit trail

### Filtering Options

- **Action Type**: Filter by specific action categories
- **Username**: Search for specific user activities
- **Date Range**: Limit results to specific time periods
- **Success Status**: Show only successful or failed actions

### Viewing Details

Each audit entry can be expanded to show:
- Complete resource information
- Before/after values for changes
- Error messages for failed operations
- Additional context and metadata
- User agent and session details

### Exporting Data

- **CSV Export**: Download filtered results as CSV
- **Maintains Filters**: Export respects current filter settings
- **Complete Data**: Includes all fields and details

## Security Considerations

### Data Protection
- **Sensitive Data**: Passwords and sensitive information are never logged
- **Data Minimization**: Only necessary information is captured
- **Access Control**: Audit logs are restricted to admin users

### Performance
- **Asynchronous Logging**: Audit operations don't block application flow
- **Error Isolation**: Audit failures don't affect application functionality
- **Efficient Queries**: Optimized database queries for large datasets

### Compliance
- **Immutable Records**: Audit entries cannot be modified after creation
- **Complete Trail**: All significant actions are captured
- **Retention Policy**: Consider implementing data retention policies

## Configuration

### Environment Variables

No additional environment variables are required. The audit system uses the existing database configuration.

### Database Migration

To enable the audit system in an existing installation:

```bash
# Run the audit table creation script
python scripts/create_audit_table.py
```

### Testing

Verify the audit system is working:

```bash
# Run comprehensive audit system tests
python scripts/test_all_audit_implementations.py

# Run basic audit system tests
python scripts/test_audit_system.py
```

The comprehensive test suite validates all 19 AuditActionType implementations and should show 100% success rate when the system is properly configured.

## Usage Examples

### Basic Logging

```python
# Log successful login
AuditService.log_login("user@example.com", success=True)

# Log failed login attempt
AuditService.log_login(
    "user@example.com", 
    success=False, 
    error_message="Invalid password"
)

# Log panel download
AuditService.log_panel_download(
    panel_ids="123,456,789",
    list_types="diagnostic",
    gene_count=200,
    file_name="BRCA_panel.txt"
)
```

### Advanced Logging with Context

```python
# Log complex operations with timing
with AuditContext(
    action_type=AuditActionType.PANEL_UPLOAD,
    action_description="Processing uploaded panel file",
    resource_type="panel",
    details={"file_size": file_size, "format": "BED"}
) as audit:
    try:
        result = process_panel_file(uploaded_file)
        # Success is automatically logged
    except Exception as e:
        # Error is automatically captured
        raise
```

### Custom Audit Entries

```python
# Log custom actions
AuditService.log_action(
    action_type=AuditActionType.ADMIN_ACTION,
    action_description="Bulk user import completed",
    resource_type="user",
    details={
        "imported_count": 50,
        "failed_count": 2,
        "source_file": "users.csv"
    }
)
```

## Monitoring and Maintenance

### Regular Monitoring
- Review failed login attempts for security threats
- Monitor admin actions for unauthorized changes
- Track system errors for operational issues
- Analyze usage patterns for performance optimization

### Data Retention
- Consider implementing automatic cleanup of old audit logs
- Archive historical data for long-term compliance
- Balance storage costs with retention requirements

### Performance Optimization
- Monitor audit table size and query performance
- Consider partitioning for very large datasets
- Optimize indexes for common query patterns

## Troubleshooting

### Common Issues

1. **Audit Logs Not Appearing**
   - Verify database table exists: `audit_log`
   - Check application logs for audit service errors
   - Ensure proper permissions for database writes

2. **Admin Interface Access Denied**
   - Confirm user has admin role
   - Check authentication and session status
   - Verify admin routes are properly configured

3. **Export Functionality Not Working**
   - Check file system permissions
   - Verify CSV generation doesn't timeout
   - Monitor for memory issues with large datasets

### Debug Mode

Enable debug logging to troubleshoot audit issues:

```python
import logging
logging.getLogger('app.audit_service').setLevel(logging.DEBUG)
```

## Future Enhancements

### Potential Improvements
- **Real-time Alerts**: Automated notifications for security events
- **Dashboard Analytics**: Visual representation of audit data
- **Advanced Filtering**: More sophisticated search capabilities
- **API Access**: RESTful API for external audit analysis
- **Data Visualization**: Charts and graphs for usage patterns

### Integration Opportunities
- **SIEM Integration**: Connect with security information systems
- **Compliance Reporting**: Automated compliance report generation
- **Backup Integration**: Include audit logs in backup procedures
- **External Storage**: Archive old logs to external systems

## Conclusion

The audit trail system provides comprehensive tracking of all application activities, ensuring security, compliance, and operational visibility. The system is designed to be robust, performant, and easy to use while maintaining the highest standards for data integrity and security.

**Current Status**: The audit system is fully implemented with 100% test coverage across all 19 AuditActionType implementations. All core functionality including user authentication, panel operations, administrative actions, and system events are comprehensively logged and tracked.

For questions or issues with the audit system, refer to the application logs or contact the development team.
