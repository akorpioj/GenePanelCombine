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
