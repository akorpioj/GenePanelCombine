"""
Enhanced API endpoints for Version Control System

This module provides REST API endpoints for:
- Creating and managing version branches
- Tagging versions with different types
- Configuring retention policies
- Merging versions with conflict resolution
- Advanced version history and diff operations
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from flask import current_app, request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import desc, and_, or_
from sqlalchemy.exc import IntegrityError

from app import db, limiter
from app.models import (
    SavedPanel, PanelVersion, PanelVersionTag, PanelVersionBranch,
    PanelVersionMetadata, PanelRetentionPolicy, TagType, VersionType,
    User, AuditActionType
)
from app.api.auth_decorators import api_login_required
from flask_login import current_user
from app.api.models import error_response_model
from app.audit_service import AuditService
from app.version_control_service import (
    VersionControlService, VersionControlError, BranchConflictError,
    MergeStrategy
)

logger = logging.getLogger(__name__)

# Create namespace
ns = Namespace('version-control', description='Version Control operations for saved panels')

# API Models
tag_model = ns.model('VersionTag', {
    'id': fields.Integer(required=True, description='Tag ID'),
    'tag_name': fields.String(required=True, description='Tag name'),
    'tag_type': fields.String(required=True, description='Tag type (PRODUCTION, STAGING, RELEASE, etc.)'),
    'description': fields.String(description='Tag description'),
    'created_by': fields.Raw(description='User who created the tag'),
    'created_at': fields.String(description='Creation timestamp'),
    'is_protected': fields.Boolean(description='Whether the tag is protected from deletion')
})

branch_model = ns.model('VersionBranch', {
    'id': fields.Integer(required=True, description='Branch ID'),
    'branch_name': fields.String(required=True, description='Branch name'),
    'description': fields.String(description='Branch description'),
    'parent_version': fields.Raw(description='Parent version information'),
    'head_version': fields.Raw(description='Head version information'),
    'created_by': fields.Raw(description='User who created the branch'),
    'created_at': fields.String(description='Creation timestamp'),
    'is_active': fields.Boolean(description='Whether the branch is active'),
    'is_merged': fields.Boolean(description='Whether the branch has been merged'),
    'merged_at': fields.String(description='Merge timestamp'),
    'merged_by': fields.Raw(description='User who merged the branch')
})

retention_policy_model = ns.model('RetentionPolicy', {
    'id': fields.Integer(required=True, description='Policy ID'),
    'panel_id': fields.Integer(required=True, description='Panel ID'),
    'max_versions': fields.Integer(description='Maximum number of versions to keep'),
    'backup_retention_days': fields.Integer(description='Days to retain backup versions'),
    'keep_tagged_versions': fields.Boolean(description='Keep all tagged versions'),
    'keep_production_tags': fields.Boolean(description='Keep production-tagged versions permanently'),
    'auto_cleanup_enabled': fields.Boolean(description='Enable automatic cleanup'),
    'cleanup_frequency_hours': fields.Integer(description='Hours between cleanup runs'),
    'last_cleanup_at': fields.String(description='Last cleanup timestamp'),
    'created_by': fields.Raw(description='User who created the policy'),
    'created_at': fields.String(description='Creation timestamp'),
    'updated_at': fields.String(description='Last update timestamp')
})

version_diff_model = ns.model('VersionDiff', {
    'version1': fields.Raw(description='First version information'),
    'version2': fields.Raw(description='Second version information'),
    'differences': fields.Raw(description='Detailed differences between versions')
})

merge_request_model = ns.model('MergeRequest', {
    'source_version_id': fields.Integer(required=True, description='Source version to merge from'),
    'target_version_id': fields.Integer(required=True, description='Target version to merge into'),
    'strategy': fields.String(description='Merge strategy (auto, manual, ours, theirs)', default='auto'),
    'conflict_resolutions': fields.Raw(description='Manual conflict resolutions'),
    'comment': fields.String(description='Merge commit message')
})

tag_create_model = ns.model('CreateTag', {
    'tag_name': fields.String(required=True, description='Tag name'),
    'tag_type': fields.String(required=True, description='Tag type'),
    'description': fields.String(description='Tag description')
})

branch_create_model = ns.model('CreateBranch', {
    'branch_name': fields.String(required=True, description='Branch name'),
    'from_version_id': fields.Integer(required=True, description='Version to branch from'),
    'description': fields.String(description='Branch description')
})

retention_policy_create_model = ns.model('CreateRetentionPolicy', {
    'max_versions': fields.Integer(description='Maximum versions to keep', default=10),
    'backup_retention_days': fields.Integer(description='Backup retention days', default=90),
    'keep_tagged_versions': fields.Boolean(description='Keep tagged versions', default=True),
    'keep_production_tags': fields.Boolean(description='Keep production tags', default=True),
    'auto_cleanup_enabled': fields.Boolean(description='Enable auto cleanup', default=True),
    'cleanup_frequency_hours': fields.Integer(description='Cleanup frequency', default=24)
})


@ns.route('/<int:panel_id>/versions/<int:version_id>/tags')
class VersionTagList(Resource):
    @ns.doc('get_version_tags')
    @ns.marshal_list_with(tag_model)
    @ns.response(200, 'Success')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(404, 'Version not found', error_response_model)
    @api_login_required
    @limiter.limit("30 per minute")
    def get(self, panel_id, version_id):
        """Get all tags for a specific version"""
        try:
            version = PanelVersion.query.filter_by(id=version_id, panel_id=panel_id).first()
            if not version:
                ns.abort(404, "Version not found")

            tags = PanelVersionTag.query.filter_by(version_id=version_id).all()
            return [tag.to_dict() for tag in tags]

        except Exception as e:
            logger.error(f"Error getting tags for version {version_id}: {str(e)}")
            ns.abort(500, "Internal server error")

    @ns.doc('create_version_tag')
    @ns.expect(tag_create_model)
    @ns.marshal_with(tag_model)
    @ns.response(201, 'Tag created successfully')
    @ns.response(400, 'Invalid input', error_response_model)
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(409, 'Tag already exists', error_response_model)
    @api_login_required
    @limiter.limit("10 per minute")
    def post(self, panel_id, version_id):
        """Create a new tag for a version"""
        try:
            data = request.get_json()
            
            version = PanelVersion.query.filter_by(id=version_id, panel_id=panel_id).first()
            if not version:
                ns.abort(404, "Version not found")

            # Validate tag type
            try:
                tag_type = TagType(data['tag_type'].upper())
            except ValueError:
                ns.abort(400, f"Invalid tag type: {data['tag_type']}")

            # Check for duplicate tag name
            existing_tag = PanelVersionTag.query.filter_by(
                version_id=version_id, 
                tag_name=data['tag_name']
            ).first()
            if existing_tag:
                ns.abort(409, f"Tag '{data['tag_name']}' already exists for this version")

            # Create tag
            tag = PanelVersionTag(
                version_id=version_id,
                tag_name=data['tag_name'],
                tag_type=tag_type,
                description=data.get('description'),
                created_by_id=current_user.id,
                is_protected=(tag_type in [TagType.PRODUCTION, TagType.STAGING])
            )

            db.session.add(tag)

            # Update version protection if needed
            if tag.is_protected:
                version.is_protected = True
                version.retention_priority = 10

            db.session.commit()

            # Log tag creation
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Created tag '{data['tag_name']}' ({tag_type.value}) for version {version.version_number}",
                details={
                    "panel_id": panel_id,
                    "version_id": version_id,
                    "tag_name": data['tag_name'],
                    "tag_type": tag_type.value,
                    "is_protected": tag.is_protected
                }
            )

            return tag.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating tag: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route('/<int:panel_id>/branches')
class BranchList(Resource):
    @ns.doc('get_panel_branches')
    @ns.marshal_list_with(branch_model)
    @ns.response(200, 'Success')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(404, 'Panel not found', error_response_model)
    @api_login_required
    @limiter.limit("30 per minute")
    def get(self, panel_id):
        """Get all branches for a panel"""
        try:
            panel = SavedPanel.query.get(panel_id)
            if not panel:
                ns.abort(404, "Panel not found")

            branches = PanelVersionBranch.query.filter_by(panel_id=panel_id)\
                .order_by(desc(PanelVersionBranch.created_at)).all()
            
            return [branch.to_dict() for branch in branches]

        except Exception as e:
            logger.error(f"Error getting branches for panel {panel_id}: {str(e)}")
            ns.abort(500, "Internal server error")

    @ns.doc('create_branch')
    @ns.expect(branch_create_model)
    @ns.marshal_with(branch_model)
    @ns.response(201, 'Branch created successfully')
    @ns.response(400, 'Invalid input', error_response_model)
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(409, 'Branch already exists', error_response_model)
    @api_login_required
    @limiter.limit("5 per minute")
    def post(self, panel_id):
        """Create a new branch"""
        try:
            data = request.get_json()
            
            panel = SavedPanel.query.get(panel_id)
            if not panel:
                ns.abort(404, "Panel not found")

            from_version = PanelVersion.query.get(data['from_version_id'])
            if not from_version or from_version.panel_id != panel_id:
                ns.abort(400, "Invalid source version")

            # Check for duplicate branch name
            existing_branch = PanelVersionBranch.query.filter_by(
                panel_id=panel_id,
                branch_name=data['branch_name']
            ).first()
            if existing_branch:
                ns.abort(409, f"Branch '{data['branch_name']}' already exists")

            # Use version control service to create branch
            vc_service = VersionControlService()
            branch_version = vc_service.create_branch(
                panel_id=panel_id,
                from_version_id=data['from_version_id'],
                branch_name=data['branch_name'],
                user_id=current_user.id,
                description=data.get('description')
            )

            # Get the created branch
            branch = PanelVersionBranch.query.filter_by(
                panel_id=panel_id,
                branch_name=data['branch_name']
            ).first()

            return branch.to_dict(), 201

        except VersionControlError as e:
            logger.error(f"Version control error creating branch: {str(e)}")
            ns.abort(400, str(e))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating branch: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route('/<int:panel_id>/versions/<int:version_id>/diff/<int:other_version_id>')
class VersionDiff(Resource):
    @ns.doc('get_version_diff')
    @ns.marshal_with(version_diff_model)
    @ns.response(200, 'Success')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(404, 'Version not found', error_response_model)
    @api_login_required
    @limiter.limit("20 per minute")
    def get(self, panel_id, version_id, other_version_id):
        """Get differences between two versions"""
        try:
            version1 = PanelVersion.query.filter_by(id=version_id, panel_id=panel_id).first()
            version2 = PanelVersion.query.filter_by(id=other_version_id, panel_id=panel_id).first()
            
            if not version1 or not version2:
                ns.abort(404, "One or both versions not found")

            # Use version control service to get diff
            vc_service = VersionControlService()
            diff = vc_service.get_version_diff(version_id, other_version_id)

            return diff

        except VersionControlError as e:
            logger.error(f"Version control error getting diff: {str(e)}")
            ns.abort(400, str(e))
        except Exception as e:
            logger.error(f"Error getting version diff: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route('/<int:panel_id>/merge')
class VersionMerge(Resource):
    @ns.doc('merge_versions')
    @ns.expect(merge_request_model)
    @ns.response(200, 'Merge completed successfully')
    @ns.response(400, 'Invalid input or merge conflicts', error_response_model)
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(409, 'Merge conflicts require manual resolution', error_response_model)
    @api_login_required
    @limiter.limit("3 per minute")
    def post(self, panel_id):
        """Merge two versions"""
        try:
            data = request.get_json()
            
            panel = SavedPanel.query.get(panel_id)
            if not panel:
                ns.abort(404, "Panel not found")

            # Validate merge strategy
            try:
                strategy = MergeStrategy(data.get('strategy', 'auto').upper())
            except ValueError:
                ns.abort(400, f"Invalid merge strategy: {data.get('strategy')}")

            # Use version control service to perform merge
            vc_service = VersionControlService()
            
            try:
                merged_version = vc_service.merge_versions(
                    panel_id=panel_id,
                    source_version_id=data['source_version_id'],
                    target_version_id=data['target_version_id'],
                    user_id=current_user.id,
                    strategy=strategy,
                    conflict_resolutions=data.get('conflict_resolutions')
                )

                return {
                    'success': True,
                    'merged_version': merged_version.to_dict(),
                    'message': f'Successfully merged versions {data["source_version_id"]} and {data["target_version_id"]}'
                }

            except BranchConflictError as e:
                ns.abort(409, str(e))

        except VersionControlError as e:
            logger.error(f"Version control error during merge: {str(e)}")
            ns.abort(400, str(e))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error merging versions: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route('/<int:panel_id>/retention-policy')
class RetentionPolicyResource(Resource):
    @ns.doc('get_retention_policy')
    @ns.marshal_with(retention_policy_model)
    @ns.response(200, 'Success')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(404, 'Panel or policy not found', error_response_model)
    @api_login_required
    @limiter.limit("30 per minute")
    def get(self, panel_id):
        """Get retention policy for a panel"""
        try:
            panel = SavedPanel.query.get(panel_id)
            if not panel:
                ns.abort(404, "Panel not found")

            policy = PanelRetentionPolicy.query.filter_by(panel_id=panel_id).first()
            if not policy:
                # Create default policy
                policy = PanelRetentionPolicy(
                    panel_id=panel_id,
                    created_by_id=current_user.id
                )
                db.session.add(policy)
                db.session.commit()

            return policy.to_dict()

        except Exception as e:
            logger.error(f"Error getting retention policy for panel {panel_id}: {str(e)}")
            ns.abort(500, "Internal server error")

    @ns.doc('update_retention_policy')
    @ns.expect(retention_policy_create_model)
    @ns.marshal_with(retention_policy_model)
    @ns.response(200, 'Policy updated successfully')
    @ns.response(400, 'Invalid input', error_response_model)
    @ns.response(401, 'Authentication required', error_response_model)
    @api_login_required
    @limiter.limit("10 per minute")
    def put(self, panel_id):
        """Update retention policy for a panel"""
        try:
            data = request.get_json()
            
            panel = SavedPanel.query.get(panel_id)
            if not panel:
                ns.abort(404, "Panel not found")

            policy = PanelRetentionPolicy.query.filter_by(panel_id=panel_id).first()
            if not policy:
                # Create new policy
                policy = PanelRetentionPolicy(
                    panel_id=panel_id,
                    created_by_id=current_user.id
                )
                db.session.add(policy)

            # Update policy fields
            if 'max_versions' in data:
                policy.max_versions = data['max_versions']
            if 'backup_retention_days' in data:
                policy.backup_retention_days = data['backup_retention_days']
            if 'keep_tagged_versions' in data:
                policy.keep_tagged_versions = data['keep_tagged_versions']
            if 'keep_production_tags' in data:
                policy.keep_production_tags = data['keep_production_tags']
            if 'auto_cleanup_enabled' in data:
                policy.auto_cleanup_enabled = data['auto_cleanup_enabled']
            if 'cleanup_frequency_hours' in data:
                policy.cleanup_frequency_hours = data['cleanup_frequency_hours']

            policy.updated_at = datetime.now()
            db.session.commit()

            # Log policy update
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Updated retention policy for panel '{panel.name}'",
                details={
                    "panel_id": panel_id,
                    "policy_id": policy.id,
                    "changes": list(data.keys())
                }
            )

            return policy.to_dict()

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating retention policy: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route('/<int:panel_id>/cleanup')
class RetentionCleanup(Resource):
    @ns.doc('run_retention_cleanup')
    @ns.response(200, 'Cleanup completed successfully')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(404, 'Panel not found', error_response_model)
    @api_login_required
    @limiter.limit("2 per hour")  # Limit cleanup operations
    def post(self, panel_id):
        """Manually run retention cleanup for a panel"""
        try:
            panel = SavedPanel.query.get(panel_id)
            if not panel:
                ns.abort(404, "Panel not found")

            # Use version control service to apply retention
            vc_service = VersionControlService()
            vc_service.retention_policy.apply_retention(panel_id)

            # Update policy timestamp
            policy = PanelRetentionPolicy.query.filter_by(panel_id=panel_id).first()
            if policy:
                policy.update_cleanup_timestamp()
                db.session.commit()

            # Log cleanup operation
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Manually ran retention cleanup for panel '{panel.name}'",
                details={
                    "panel_id": panel_id,
                    "triggered_by": "manual",
                    "user_id": current_user.id
                }
            )

            return {
                'success': True,
                'message': 'Retention cleanup completed successfully',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error running retention cleanup: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route('/<int:panel_id>/versions/<int:version_id>/restore')
class VersionRestore(Resource):
    @ns.doc('restore_version')
    @ns.response(200, 'Version restored successfully')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(404, 'Version not found', error_response_model)
    @api_login_required
    @limiter.limit("3 per hour")  # Limit restore operations
    def post(self, panel_id, version_id):
        """Restore a panel to a specific version"""
        try:
            data = request.get_json() or {}
            create_backup = data.get('create_backup', True)

            panel = SavedPanel.query.get(panel_id)
            if not panel:
                ns.abort(404, "Panel not found")

            version = PanelVersion.query.filter_by(id=version_id, panel_id=panel_id).first()
            if not version:
                ns.abort(404, "Version not found")

            # Use version control service to restore
            vc_service = VersionControlService()
            restored_version = vc_service.restore_version(
                panel_id=panel_id,
                version_id=version_id,
                user_id=current_user.id,
                create_backup=create_backup
            )

            return {
                'success': True,
                'restored_version': restored_version.to_dict(),
                'message': f'Successfully restored to version {version.version_number}',
                'backup_created': create_backup
            }

        except VersionControlError as e:
            logger.error(f"Version control error during restore: {str(e)}")
            ns.abort(400, str(e))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error restoring version: {str(e)}")
            ns.abort(500, "Internal server error")
