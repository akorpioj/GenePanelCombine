"""
API Models for Swagger/OpenAPI documentation
"""

from flask_restx import fields
from . import api

# Panel Models
panel_model = api.model('Panel', {
    'id': fields.Integer(required=True, description='Panel ID'),
    'name': fields.String(required=True, description='Panel name'),
    'display_name': fields.String(required=True, description='Formatted display name with emoji'),
    'version': fields.String(description='Panel version'),
    'description': fields.String(description='Panel description'),
    'disease_group': fields.String(description='Disease group'),
    'disease_sub_group': fields.String(description='Disease sub-group'),
    'api_source': fields.String(description='API source (uk/aus)'),
    'status': fields.String(description='Panel status'),
    'created': fields.String(description='Creation date'),
    'gene_count': fields.Integer(description='Number of genes in panel')
})

panel_list_model = api.model('PanelList', {
    'panels': fields.List(fields.Nested(panel_model)),
    'total': fields.Integer(description='Total number of panels')
})

# Gene Models
gene_model = api.model('Gene', {
    'gene_symbol': fields.String(required=True, description='Gene symbol'),
    'confidence_level': fields.String(description='Confidence level (1=red, 2=amber, 3=green)'),
    'mode_of_inheritance': fields.String(description='Mode of inheritance'),
    'phenotype': fields.String(description='Associated phenotype'),
    'entity_name': fields.String(description='Entity name'),
    'entity_type': fields.String(description='Entity type')
})

gene_list_model = api.model('GeneList', {
    'genes': fields.List(fields.Nested(gene_model)),
    'total': fields.Integer(description='Total number of genes'),
    'panel_id': fields.Integer(description='Panel ID'),
    'panel_name': fields.String(description='Panel name')
})

gene_suggestion_model = api.model('GeneSuggestion', {
    'symbol': fields.String(required=True, description='Gene symbol'),
    'name': fields.String(description='Gene name'),
    'aliases': fields.List(fields.String, description='Gene aliases')
})

# Panel Preview Models
confidence_stats_model = api.model('ConfidenceStats', {
    'green': fields.Integer(description='Number of green confidence genes'),
    'amber': fields.Integer(description='Number of amber confidence genes'),
    'red': fields.Integer(description='Number of red confidence genes'),
    'unknown': fields.Integer(description='Number of unknown confidence genes')
})

panel_preview_model = api.model('PanelPreview', {
    'id': fields.Integer(required=True, description='Panel ID'),
    'api_source': fields.String(required=True, description='API source'),
    'name': fields.String(required=True, description='Panel name'),
    'display_name': fields.String(required=True, description='Formatted display name'),
    'version': fields.String(description='Panel version'),
    'description': fields.String(description='Panel description'),
    'disease_group': fields.String(description='Disease group'),
    'disease_sub_group': fields.String(description='Disease sub-group'),
    'source_name': fields.String(description='Source name'),
    'gene_count': fields.Integer(description='Number of genes'),
    'confidence_stats': fields.Nested(confidence_stats_model),
    'all_genes': fields.List(fields.Nested(gene_model)),
    'has_detailed_data': fields.Boolean(description='Whether detailed gene data is available')
})

# User Models
user_model = api.model('User', {
    'id': fields.Integer(required=True, description='User ID'),
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email address'),
    'first_name': fields.String(description='First name'),
    'last_name': fields.String(description='Last name'),
    'organization': fields.String(description='Organization'),
    'role': fields.String(description='User role (USER/ADMIN)'),
    'is_active': fields.Boolean(description='Whether user is active'),
    'created_at': fields.DateTime(description='Registration date'),
    'last_login': fields.DateTime(description='Last login date'),
    'login_count': fields.Integer(description='Number of logins')
})

user_list_model = api.model('UserList', {
    'users': fields.List(fields.Nested(user_model)),
    'total': fields.Integer(description='Total number of users'),
    'active': fields.Integer(description='Number of active users'),
    'admins': fields.Integer(description='Number of admin users')
})

user_update_model = api.model('UserUpdate', {
    'role': fields.String(description='User role (USER/ADMIN)'),
    'is_active': fields.Boolean(description='Whether user is active')
})

# Authentication Models
login_model = api.model('Login', {
    'username_or_email': fields.String(required=True, description='Username or email'),
    'password': fields.String(required=True, description='Password'),
    'remember_me': fields.Boolean(description='Remember me option')
})

register_model = api.model('Register', {
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password'),
    'confirm_password': fields.String(required=True, description='Confirm password'),
    'first_name': fields.String(description='First name'),
    'last_name': fields.String(description='Last name'),
    'organization': fields.String(description='Organization')
})

# Admin Message Models
admin_message_model = api.model('AdminMessage', {
    'id': fields.Integer(required=True, description='Message ID'),
    'title': fields.String(required=True, description='Message title'),
    'message': fields.String(required=True, description='Message content'),
    'message_type': fields.String(description='Message type (info/warning/error/success)'),
    'is_active': fields.Boolean(description='Whether message is active'),
    'created_at': fields.DateTime(description='Creation date'),
    'expires_at': fields.DateTime(description='Expiration date'),
    'created_by': fields.Nested(user_model, description='User who created the message')
})

admin_message_create_model = api.model('AdminMessageCreate', {
    'title': fields.String(required=True, description='Message title'),
    'message': fields.String(required=True, description='Message content'),
    'message_type': fields.String(description='Message type (info/warning/error/success)'),
    'expires_at': fields.String(description='Expiration date (YYYY-MM-DD format)')
})

# Cache Models
cache_stats_model = api.model('CacheStats', {
    'total_keys': fields.Integer(description='Total number of cached keys'),
    'memory_usage': fields.String(description='Memory usage'),
    'hit_rate': fields.Float(description='Cache hit rate'),
    'cache_type': fields.String(description='Cache implementation type')
})

# Response Models
success_response_model = api.model('SuccessResponse', {
    'success': fields.Boolean(required=True, description='Success status'),
    'message': fields.String(description='Success message')
})

error_response_model = api.model('ErrorResponse', {
    'error': fields.String(required=True, description='Error message'),
    'code': fields.Integer(description='Error code')
})

# File Upload Models
upload_result_model = api.model('UploadResult', {
    'filename': fields.String(required=True, description='Uploaded filename'),
    'success': fields.Boolean(required=True, description='Upload success status'),
    'gene_count': fields.Integer(description='Number of genes processed'),
    'sheet_name': fields.String(description='Sheet name for Excel files'),
    'error': fields.String(description='Error message if upload failed')
})

upload_response_model = api.model('UploadResponse', {
    'success': fields.Boolean(required=True, description='Overall upload success'),
    'results': fields.List(fields.Nested(upload_result_model), description='Individual file results')
})

# Version Models
version_info_model = api.model('VersionInfo', {
    'version': fields.String(required=True, description='Application version'),
    'build_date': fields.String(description='Build date'),
    'commit_hash': fields.String(description='Git commit hash'),
    'environment': fields.String(description='Environment (development/production)')
})

# Saved Panel Models
saved_panel_gene_model = api.model('SavedPanelGene', {
    'id': fields.Integer(description='Gene ID'),
    'gene_symbol': fields.String(required=True, description='Gene symbol'),
    'gene_name': fields.String(description='Gene name'),
    'ensembl_id': fields.String(description='Ensembl gene ID'),
    'hgnc_id': fields.String(description='HGNC gene ID'),
    'confidence_level': fields.String(description='Confidence level (1=red, 2=amber, 3=green)'),
    'mode_of_inheritance': fields.String(description='Mode of inheritance'),
    'phenotype': fields.String(description='Associated phenotype'),
    'evidence_level': fields.String(description='Evidence level'),
    'source_panel_id': fields.String(description='Source panel ID'),
    'source_list_type': fields.String(description='Source list type'),
    'user_notes': fields.String(description='User notes'),
    'custom_confidence': fields.String(description='Custom confidence rating'),
    'is_modified': fields.Boolean(description='Whether gene has been modified'),
    'added_at': fields.String(description='Date gene was added')
})

saved_panel_owner_model = api.model('SavedPanelOwner', {
    'id': fields.Integer(required=True, description='User ID'),
    'username': fields.String(required=True, description='Username')
})

saved_panel_model = api.model('SavedPanel', {
    'id': fields.Integer(required=True, description='Panel ID'),
    'name': fields.String(required=True, description='Panel name'),
    'description': fields.String(description='Panel description'),
    'tags': fields.String(description='Panel tags (comma-separated)'),
    'status': fields.String(description='Panel status (ACTIVE/DRAFT/ARCHIVED)'),
    'visibility': fields.String(description='Panel visibility (PRIVATE/SHARED/PUBLIC)'),
    'gene_count': fields.Integer(description='Number of genes in panel'),
    'version_count': fields.Integer(description='Number of versions'),
    'created_at': fields.String(description='Creation timestamp'),
    'updated_at': fields.String(description='Last update timestamp'),
    'last_accessed_at': fields.String(description='Last access timestamp'),
    'source_type': fields.String(description='Source type (manual/panelapp/upload)'),
    'source_reference': fields.String(description='Source reference identifier'),
    'storage_backend': fields.String(description='Storage backend (gcs/local)'),
    'current_version_id': fields.Integer(description='Current version ID'),
    'owner': fields.Nested(saved_panel_owner_model, description='Panel owner'),
    'genes': fields.List(fields.Nested(saved_panel_gene_model), description='Panel genes')
})

saved_panel_pagination_model = api.model('SavedPanelPagination', {
    'page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page'),
    'total': fields.Integer(description='Total number of items'),
    'pages': fields.Integer(description='Total number of pages'),
    'has_next': fields.Boolean(description='Whether there is a next page'),
    'has_prev': fields.Boolean(description='Whether there is a previous page')
})

saved_panel_list_model = api.model('SavedPanelList', {
    'panels': fields.List(fields.Nested(saved_panel_model)),
    'pagination': fields.Nested(saved_panel_pagination_model, description='Pagination info'),
    'total': fields.Integer(description='Total number of panels')
})

saved_panel_create_gene_model = api.model('SavedPanelCreateGene', {
    'gene_symbol': fields.String(required=True, description='Gene symbol'),
    'gene_name': fields.String(description='Gene name'),
    'ensembl_id': fields.String(description='Ensembl gene ID'),
    'hgnc_id': fields.String(description='HGNC gene ID'),
    'confidence_level': fields.String(description='Confidence level'),
    'mode_of_inheritance': fields.String(description='Mode of inheritance'),
    'phenotype': fields.String(description='Associated phenotype'),
    'evidence_level': fields.String(description='Evidence level'),
    'source_panel_id': fields.String(description='Source panel ID'),
    'source_list_type': fields.String(description='Source list type'),
    'user_notes': fields.String(description='User notes'),
    'custom_confidence': fields.String(description='Custom confidence rating')
})

saved_panel_create_model = api.model('SavedPanelCreate', {
    'name': fields.String(required=True, description='Panel name'),
    'description': fields.String(description='Panel description'),
    'tags': fields.String(description='Panel tags (comma-separated)'),
    'status': fields.String(description='Panel status (ACTIVE/DRAFT/ARCHIVED)', default='ACTIVE'),
    'visibility': fields.String(description='Panel visibility (PRIVATE/SHARED/PUBLIC)', default='PRIVATE'),
    'source_type': fields.String(description='Source type (manual/panelapp/upload)', default='manual'),
    'source_reference': fields.String(description='Source reference identifier'),
    'version_comment': fields.String(description='Version comment'),
    'genes': fields.List(fields.Nested(saved_panel_create_gene_model), required=True, description='Panel genes')
})

saved_panel_update_model = api.model('SavedPanelUpdate', {
    'name': fields.String(description='Panel name'),
    'description': fields.String(description='Panel description'),
    'tags': fields.String(description='Panel tags (comma-separated)'),
    'status': fields.String(description='Panel status (ACTIVE/DRAFT/ARCHIVED)'),
    'visibility': fields.String(description='Panel visibility (PRIVATE/SHARED/PUBLIC)'),
    'version_comment': fields.String(description='Version comment for this update')
})

# Panel Version Models
panel_version_creator_model = api.model('PanelVersionCreator', {
    'id': fields.Integer(required=True, description='User ID'),
    'username': fields.String(required=True, description='Username')
})

panel_version_model = api.model('PanelVersion', {
    'id': fields.Integer(required=True, description='Version ID'),
    'version_number': fields.Integer(required=True, description='Version number'),
    'comment': fields.String(description='Version comment'),
    'gene_count': fields.Integer(description='Number of genes in this version'),
    'changes_summary': fields.String(description='Summary of changes'),
    'storage_path': fields.String(description='Storage path for version data'),
    'created_at': fields.String(description='Creation timestamp'),
    'created_by': fields.Nested(panel_version_creator_model, description='Version creator')
})

panel_version_list_model = api.model('PanelVersionList', {
    'panel_id': fields.Integer(required=True, description='Panel ID'),
    'panel_name': fields.String(required=True, description='Panel name'),
    'versions': fields.List(fields.Nested(panel_version_model)),
    'total': fields.Integer(description='Total number of versions')
})

# Panel Share Models
panel_share_model = api.model('PanelShare', {
    'id': fields.Integer(required=True, description='Share ID'),
    'panel_id': fields.Integer(required=True, description='Panel ID'),
    'shared_with_user_id': fields.Integer(description='Shared with user ID'),
    'permission_level': fields.String(description='Permission level (VIEW/EDIT/ADMIN)'),
    'can_reshare': fields.Boolean(description='Whether user can reshare'),
    'is_active': fields.Boolean(description='Whether share is active'),
    'expires_at': fields.String(description='Expiration timestamp'),
    'created_at': fields.String(description='Creation timestamp'),
    'share_token': fields.String(description='Share token for links')
})

panel_share_create_model = api.model('PanelShareCreate', {
    'shared_with_user_id': fields.Integer(description='User ID to share with'),
    'permission_level': fields.String(description='Permission level (VIEW/EDIT/ADMIN)', default='VIEW'),
    'can_reshare': fields.Boolean(description='Whether user can reshare', default=False),
    'expires_in_days': fields.Integer(description='Number of days until expiration'),
    'create_public_link': fields.Boolean(description='Create public share link', default=False)
})

# Common Response Models
error_response_model = api.model('ErrorResponse', {
    'error': fields.String(required=True, description='Error message'),
    'details': fields.String(description='Additional error details')
})

success_response_model = api.model('SuccessResponse', {
    'success': fields.Boolean(required=True, description='Operation success status'),
    'message': fields.String(description='Success message')
})
