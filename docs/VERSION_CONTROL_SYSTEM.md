# Version Control System Documentation

## Overview

The Version Control System provides Git-like versioning capabilities for saved panels in PanelMerge. This system enables users to track changes, create branches, tag important versions, and manage version history with configurable retention policies.

## Features

### Core Features
- **Automatic Versioning**: Every save operation creates a new version with incremental version numbers
- **Branch Management**: Create branches for experimental changes or parallel development
- **Tagging System**: Tag important versions (production, staging, releases, hotfixes)
- **Retention Policies**: Configurable cleanup of old versions to manage storage
- **Merge Operations**: Merge branches back to main with conflict detection
- **Version Protection**: Protect important versions from automatic cleanup
- **Audit Trail**: Complete audit trail of all version control operations

### Advanced Features
- **Three-way Merge**: Intelligent merging using common ancestor algorithm
- **Conflict Resolution**: Automatic and manual conflict resolution
- **Access Tracking**: Track when versions are accessed for retention decisions
- **Priority-based Retention**: Weighted retention based on tags, protection, and access patterns
- **Batch Operations**: CLI tools for bulk version management

## Architecture

### Database Schema

#### Core Tables
- `panel_versions`: Main version tracking table
- `panel_version_tags`: Version tags (production, staging, etc.)
- `panel_version_branches`: Branch metadata
- `panel_version_metadata`: Extended version metadata
- `panel_retention_policies`: Per-panel retention configuration

#### Key Relationships
```sql
SavedPanel 1 -> N PanelVersion
PanelVersion 1 -> N PanelVersionTag
PanelVersion 1 -> 1 PanelVersionBranch (optional)
PanelVersion 1 -> 1 PanelVersionMetadata (optional)
SavedPanel 1 -> 1 PanelRetentionPolicy (optional)
```

### Service Layer

#### VersionControlService
Main orchestrator for version control operations:
- `create_version()`: Create new versions
- `create_branch()`: Create branches
- `merge_versions()`: Merge operations
- `restore_version()`: Restore to previous versions

#### RetentionPolicy
Manages version cleanup:
- `apply_retention()`: Apply retention rules
- `calculate_retention_score()`: Determine version importance
- `can_delete_version()`: Check if version is eligible for deletion

#### BranchManager
Handles branch operations:
- `create_branch()`: Create new branches
- `list_branches()`: List active branches
- `delete_branch()`: Remove branches

#### TagManager
Manages version tags:
- `create_tag()`: Create version tags
- `list_tags()`: List version tags
- `delete_tag()`: Remove tags

#### MergeEngine
Handles merge operations:
- `merge_versions()`: Perform merges
- `detect_conflicts()`: Identify conflicts
- `resolve_conflicts()`: Conflict resolution

## Usage Guide

### Basic Operations

#### Creating Versions
Versions are created automatically when panels are saved:

```python
# Automatic version creation on panel save
panel.save()  # Creates version 1

# Manual version creation with comment
vc_service = VersionControlService()
version = vc_service.create_version(
    panel_id=panel.id,
    user_id=user.id,
    comment="Added new gene panel data",
    changes_summary={'genes_added': 5, 'genes_removed': 2}
)
```

#### Creating Branches
Create branches for experimental changes:

```python
branch_version = vc_service.create_branch(
    panel_id=panel.id,
    user_id=user.id,
    source_version_id=base_version.id,
    branch_name="feature-new-genes",
    comment="Experimental gene additions"
)
```

#### Tagging Versions
Tag important versions:

```python
vc_service.tag_manager.create_tag(
    version_id=version.id,
    tag_name="v1.0-production",
    tag_type=TagType.PRODUCTION,
    user_id=user.id,
    description="First production release"
)
```

### API Endpoints

#### Version Tags
```http
# Create a tag
POST /api/v1/version-control/versions/{version_id}/tags
{
    "tag_name": "v1.0-prod",
    "tag_type": "PRODUCTION",
    "description": "Production release"
}

# List tags for a version
GET /api/v1/version-control/versions/{version_id}/tags

# Delete a tag
DELETE /api/v1/version-control/versions/{version_id}/tags/{tag_id}
```

#### Branches
```http
# Create a branch
POST /api/v1/version-control/panels/{panel_id}/branches
{
    "source_version_id": 123,
    "branch_name": "feature-branch",
    "comment": "Feature development"
}

# List branches
GET /api/v1/version-control/panels/{panel_id}/branches

# Delete a branch
DELETE /api/v1/version-control/branches/{branch_id}
```

#### Version Diffs
```http
# Get diff between versions
GET /api/v1/version-control/versions/{version1_id}/diff/{version2_id}
```

#### Merging
```http
# Merge versions
POST /api/v1/version-control/versions/{source_id}/merge/{target_id}
{
    "comment": "Merge feature branch",
    "conflict_resolution": "auto"
}
```

#### Retention Policies
```http
# Create/update retention policy
POST /api/v1/version-control/panels/{panel_id}/retention-policy
{
    "max_versions": 10,
    "backup_retention_days": 90,
    "auto_cleanup_enabled": true
}

# Apply retention policy
POST /api/v1/version-control/panels/{panel_id}/retention-policy/apply
{
    "dry_run": false
}
```

### CLI Operations

#### Basic Commands
```bash
# Apply retention policies to all panels
python scripts/version_control_cli.py retention --apply

# Dry run to see what would be cleaned
python scripts/version_control_cli.py retention --apply --dry-run

# List protected versions
python scripts/version_control_cli.py list --protected

# Generate system report
python scripts/version_control_cli.py report --output report.json
```

#### Tag Management
```bash
# Create a production tag
python scripts/version_control_cli.py tag \
    --panel-id 1 --version 5 \
    --name "v1.0-prod" --type production \
    --description "Production release"
```

#### Retention Configuration
```bash
# Configure retention policy
python scripts/version_control_cli.py config \
    --panel-id 1 --max-versions 15 \
    --retention-days 120 --auto-cleanup true
```

## Configuration

### Application Settings
Add to `config_settings.py`:

```python
# Version Control Configuration
VERSION_CONTROL_ENABLED = True
VERSION_CONTROL_DEFAULT_MAX_VERSIONS = 10
VERSION_CONTROL_DEFAULT_RETENTION_DAYS = 90
VERSION_CONTROL_AUTO_CLEANUP_ENABLED = True
VERSION_CONTROL_PROTECTION_ENABLED = True
VERSION_CONTROL_BRANCH_LIMIT = 50
VERSION_CONTROL_TAG_LIMIT = 100
```

### Retention Policies

#### Default Policy
- **Max Versions**: 10 versions per panel
- **Retention Period**: 90 days for old versions
- **Auto Cleanup**: Enabled
- **Protection**: Respect protected versions and tags

#### Custom Policies
Each panel can have custom retention policies:

```python
policy = PanelRetentionPolicy(
    panel_id=panel.id,
    max_versions=20,          # Keep more versions
    backup_retention_days=180, # Longer retention
    auto_cleanup_enabled=True,
    priority_threshold=5       # Custom priority threshold
)
```

### Tag Types

| Tag Type | Purpose | Color | Auto-Protection |
|----------|---------|-------|-----------------|
| PRODUCTION | Live/deployed versions | Red | Yes |
| STAGING | Testing versions | Yellow | Yes |
| RELEASE | Official releases | Green | Yes |
| HOTFIX | Emergency fixes | Orange | Yes |
| FEATURE | Feature development | Blue | No |
| BACKUP | Manual backups | Gray | Yes |

## Best Practices

### Version Management
1. **Use Meaningful Comments**: Always provide descriptive comments for versions
2. **Tag Important Versions**: Tag production, staging, and release versions
3. **Protect Critical Versions**: Enable protection for versions that must not be deleted
4. **Regular Cleanup**: Use retention policies to manage storage automatically

### Branch Strategy
1. **Feature Branches**: Create branches for new features or experimental changes
2. **Short-lived Branches**: Merge or delete branches promptly to avoid clutter
3. **Naming Convention**: Use descriptive branch names (e.g., "feature-new-genes", "hotfix-validation")

### Tagging Strategy
1. **Semantic Versioning**: Use semantic version numbers (v1.0.0, v1.1.0)
2. **Environment Tags**: Tag versions for different environments (production, staging)
3. **Release Tags**: Tag all official releases for easy identification

### Retention Strategy
1. **Balanced Retention**: Balance storage costs with version history needs
2. **Priority-based**: Use priority levels to keep important versions longer
3. **Regular Review**: Periodically review retention policies and adjust as needed

## Troubleshooting

### Common Issues

#### Retention Policy Not Applied
- Check if auto-cleanup is enabled
- Verify user permissions
- Check for protected versions blocking cleanup

#### Merge Conflicts
- Review conflicting changes manually
- Use three-way merge for complex conflicts
- Consider creating new version instead of merging

#### Performance Issues
- Implement version archiving for very old versions
- Optimize database indexes
- Consider pagination for large version lists

### Error Messages

#### "Version is protected and cannot be deleted"
- Version has protection enabled or important tags
- Remove protection or tags if deletion is necessary

#### "Merge conflict detected"
- Manual resolution required
- Review conflicting changes and choose resolution strategy

#### "Retention policy would delete all versions"
- Adjust retention policy settings
- Ensure at least one version is protected

## Migration Guide

### Upgrading from Basic Versioning
1. Run the migration script: `alembic upgrade head`
2. Configure retention policies for existing panels
3. Tag important existing versions
4. Enable auto-cleanup gradually

### Data Migration
The migration script handles:
- Creating new tables
- Adding columns to existing tables
- Setting up foreign key relationships
- Creating indexes for performance

## Performance Considerations

### Database Optimization
- Indexed foreign keys for fast lookups
- Partitioning for large version tables
- Archived storage for very old versions

### API Performance
- Pagination for large result sets
- Caching for frequently accessed versions
- Asynchronous cleanup operations

### Storage Management
- Configurable retention policies
- Automatic cleanup scheduling
- Compression for archived versions

## Security Considerations

### Access Control
- Version operations respect user permissions
- Audit trail for all version control actions
- Protection against unauthorized deletions

### Data Integrity
- Foreign key constraints prevent orphaned records
- Transaction boundaries for complex operations
- Backup before destructive operations

## Monitoring and Metrics

### System Metrics
- Version creation rate
- Storage usage trends
- Retention policy effectiveness
- User adoption metrics

### Health Checks
- Database constraint violations
- Orphaned version records
- Failed cleanup operations
- Performance bottlenecks

## Future Enhancements

### Planned Features
1. **Version Comparison UI**: Visual diff interface
2. **Automated Merging**: AI-assisted conflict resolution
3. **Version Analytics**: Usage patterns and recommendations
4. **Integration APIs**: External system integration
5. **Advanced Workflows**: Custom approval workflows

### Extensibility
The system is designed for extension:
- Plugin architecture for custom retention policies
- Webhook support for external integrations
- Custom tag types and metadata
- Advanced merge strategies
