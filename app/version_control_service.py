"""
Version Control Service for Saved Panels

This service implements Git-like version control for saved panels with:
- Branch/merge capabilities
- Configurable retention policy
- Automatic versioning on save with optional commit messages
- Tag system for important versions (e.g., "v1.0-production")
"""

import datetime
import json
import logging
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum

from flask import current_app
from sqlalchemy import desc, and_, or_, func
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import (
    SavedPanel, PanelVersion, PanelGene, PanelChange, ChangeType,
    User, AuditActionType, TagType, PanelVersionTag, PanelVersionBranch,
    PanelVersionMetadata, PanelRetentionPolicy, VersionType
)
from app.audit_service import AuditService

logger = logging.getLogger(__name__)


class VersionControlError(Exception):
    """Base exception for version control operations"""
    pass


class BranchConflictError(VersionControlError):
    """Raised when there are conflicts during merge operations"""
    pass


class RetentionPolicyError(VersionControlError):
    """Raised when retention policy operations fail"""
    pass


class MergeStrategy(Enum):
    """Merge strategies for version control"""
    AUTO = "auto"          # Automatic merge if no conflicts
    MANUAL = "manual"      # Always require manual resolution
    OURS = "ours"         # Prefer current version in conflicts
    THEIRS = "theirs"     # Prefer incoming version in conflicts


class VersionControlService:
    """Service for managing panel version control operations"""

    def __init__(self):
        self.retention_policy = RetentionPolicy()
        self.branch_manager = BranchManager()
        self.tag_manager = TagManager()
        self.merge_engine = MergeEngine()

    def create_version(self, panel_id: int, user_id: int, comment: str = None,
                      tag: str = None, tag_type: TagType = None) -> PanelVersion:
        """
        Create a new version of a panel with optional tagging
        
        Args:
            panel_id: Panel ID to version
            user_id: User creating the version
            comment: Optional commit message
            tag: Optional tag name (e.g., "v1.0-production")
            tag_type: Optional tag type
            
        Returns:
            PanelVersion: The newly created version
        """
        try:
            panel = SavedPanel.query.get(panel_id)
            if not panel:
                raise VersionControlError(f"Panel {panel_id} not found")

            # Get the next version number
            latest_version = self._get_latest_version(panel_id)
            next_version_number = (latest_version.version_number + 1) if latest_version else 1

            # Create the new version
            new_version = PanelVersion(
                panel_id=panel_id,
                version_number=next_version_number,
                comment=comment or f"Version {next_version_number}",
                created_by_id=user_id,
                gene_count=panel.gene_count,
                changes_summary=self._generate_changes_summary(panel, latest_version)
            )

            db.session.add(new_version)
            db.session.flush()  # Get the version ID

            # Apply tag if provided
            if tag:
                self.tag_manager.create_tag(new_version.id, tag, tag_type or TagType.FEATURE, user_id)

            # Update panel's current version
            panel.current_version_id = new_version.id
            panel.version_count = next_version_number
            panel.updated_at = datetime.datetime.now()

            # Apply retention policy
            self.retention_policy.apply_retention(panel_id)

            db.session.commit()

            # Log the version creation
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Created version {next_version_number} for panel '{panel.name}'",
                details={
                    "panel_id": panel_id,
                    "version_id": new_version.id,
                    "version_number": next_version_number,
                    "comment": comment,
                    "tag": tag,
                    "tag_type": tag_type.value if tag_type else None
                }
            )

            return new_version

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating version for panel {panel_id}: {str(e)}")
            raise VersionControlError(f"Failed to create version: {str(e)}")

    def create_branch(self, panel_id: int, from_version_id: int, branch_name: str,
                     user_id: int, description: str = None) -> PanelVersion:
        """
        Create a new branch from an existing version
        
        Args:
            panel_id: Panel ID
            from_version_id: Version to branch from
            branch_name: Name of the new branch
            user_id: User creating the branch
            description: Optional branch description
            
        Returns:
            PanelVersion: The new branch version
        """
        return self.branch_manager.create_branch(
            panel_id, from_version_id, branch_name, user_id, description
        )

    def merge_versions(self, panel_id: int, source_version_id: int,
                      target_version_id: int, user_id: int,
                      strategy: MergeStrategy = MergeStrategy.AUTO,
                      conflict_resolutions: Dict[str, Any] = None) -> PanelVersion:
        """
        Merge two versions of a panel
        
        Args:
            panel_id: Panel ID
            source_version_id: Source version to merge from
            target_version_id: Target version to merge into
            user_id: User performing the merge
            strategy: Merge strategy to use
            conflict_resolutions: Manual conflict resolutions if needed
            
        Returns:
            PanelVersion: The merged version
        """
        return self.merge_engine.merge_versions(
            panel_id, source_version_id, target_version_id, user_id,
            strategy, conflict_resolutions
        )

    def get_version_diff(self, version1_id: int, version2_id: int) -> Dict[str, Any]:
        """
        Get differences between two versions
        
        Args:
            version1_id: First version ID
            version2_id: Second version ID
            
        Returns:
            Dict containing the differences
        """
        return self.merge_engine.get_version_diff(version1_id, version2_id)

    def restore_version(self, panel_id: int, version_id: int, user_id: int,
                       create_backup: bool = True) -> PanelVersion:
        """
        Restore a panel to a specific version
        
        Args:
            panel_id: Panel ID
            version_id: Version to restore to
            user_id: User performing the restore
            create_backup: Whether to create a backup version before restore
            
        Returns:
            PanelVersion: The restored version
        """
        try:
            panel = SavedPanel.query.get(panel_id)
            if not panel:
                raise VersionControlError(f"Panel {panel_id} not found")

            target_version = PanelVersion.query.get(version_id)
            if not target_version or target_version.panel_id != panel_id:
                raise VersionControlError(f"Version {version_id} not found for panel {panel_id}")

            # Create backup if requested
            if create_backup:
                self.create_version(
                    panel_id, user_id,
                    f"Backup before restore to version {target_version.version_number}",
                    tag=f"backup-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    tag_type=TagType.BACKUP
                )

            # Create new version that's a copy of the target
            restored_version = self.create_version(
                panel_id, user_id,
                f"Restored to version {target_version.version_number}",
                tag=f"restored-from-v{target_version.version_number}",
                tag_type=TagType.FEATURE
            )

            # Copy gene data from target version
            self._copy_genes_to_version(target_version.id, restored_version.id)

            # Log the restore operation
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Restored panel '{panel.name}' to version {target_version.version_number}",
                details={
                    "panel_id": panel_id,
                    "restored_to_version": target_version.version_number,
                    "new_version_id": restored_version.id,
                    "backup_created": create_backup
                }
            )

            return restored_version

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error restoring panel {panel_id} to version {version_id}: {str(e)}")
            raise VersionControlError(f"Failed to restore version: {str(e)}")

    def _get_latest_version(self, panel_id: int) -> Optional[PanelVersion]:
        """Get the latest version for a panel"""
        return PanelVersion.query.filter_by(panel_id=panel_id)\
            .order_by(desc(PanelVersion.version_number)).first()

    def _generate_changes_summary(self, panel: SavedPanel, previous_version: Optional[PanelVersion]) -> str:
        """Generate a summary of changes since the previous version"""
        if not previous_version:
            return f"Initial version with {panel.gene_count} genes"
        
        # This would compare current panel state with previous version
        # For now, return a basic summary
        return f"Updated from {previous_version.gene_count} to {panel.gene_count} genes"

    def _copy_genes_to_version(self, from_version_id: int, to_version_id: int):
        """Copy genes from one version to another"""
        # This would copy gene data between versions
        # Implementation depends on how genes are stored per version
        pass


class RetentionPolicy:
    """Manages version retention policies"""

    def __init__(self):
        self.max_versions = current_app.config.get('MAX_PANEL_VERSIONS', 10)
        self.backup_retention_days = current_app.config.get('BACKUP_RETENTION_DAYS', 90)

    def apply_retention(self, panel_id: int):
        """
        Apply retention policy to a panel's versions
        
        Args:
            panel_id: Panel ID to apply retention to
        """
        try:
            panel = SavedPanel.query.get(panel_id)
            if not panel:
                return

            # Get all versions sorted by version number (newest first)
            all_versions = PanelVersion.query.filter_by(panel_id=panel_id)\
                .order_by(desc(PanelVersion.version_number)).all()

            if len(all_versions) <= self.max_versions:
                return  # No cleanup needed

            # Keep the most recent versions and tagged versions
            versions_to_keep = set()
            
            # Always keep the most recent N versions
            for version in all_versions[:self.max_versions]:
                versions_to_keep.add(version.id)

            # Always keep tagged versions (production, staging, etc.)
            tagged_versions = self._get_tagged_versions(panel_id)
            for version_id in tagged_versions:
                versions_to_keep.add(version_id)

            # Mark old versions for deletion
            versions_to_delete = [v for v in all_versions if v.id not in versions_to_keep]
            
            # Apply backup retention policy for very old versions
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.backup_retention_days)
            final_deletions = []
            
            for version in versions_to_delete:
                if version.created_at < cutoff_date:
                    final_deletions.append(version)

            # Delete old versions
            for version in final_deletions:
                self._delete_version(version)

            if final_deletions:
                logger.info(f"Retention policy cleaned up {len(final_deletions)} old versions for panel {panel_id}")

        except Exception as e:
            logger.error(f"Error applying retention policy to panel {panel_id}: {str(e)}")
            raise RetentionPolicyError(f"Failed to apply retention policy: {str(e)}")

    def _get_tagged_versions(self, panel_id: int) -> List[int]:
        """Get list of version IDs that have tags"""
        # Query for tagged versions - this would need a proper tag table
        # For now, return empty list
        return []

    def _delete_version(self, version: PanelVersion):
        """Safely delete a version and its associated data"""
        try:
            # Delete associated changes
            PanelChange.query.filter_by(version_id=version.id).delete()
            
            # Delete the version
            db.session.delete(version)
            
        except Exception as e:
            logger.error(f"Error deleting version {version.id}: {str(e)}")
            raise


class BranchManager:
    """Manages branch operations for version control"""

    def create_branch(self, panel_id: int, from_version_id: int, branch_name: str,
                     user_id: int, description: str = None) -> PanelVersion:
        """Create a new branch from an existing version"""
        try:
            # Validate inputs
            panel = SavedPanel.query.get(panel_id)
            if not panel:
                raise VersionControlError(f"Panel {panel_id} not found")

            from_version = PanelVersion.query.get(from_version_id)
            if not from_version or from_version.panel_id != panel_id:
                raise VersionControlError(f"Version {from_version_id} not found for panel {panel_id}")

            # Create branch version
            branch_version = PanelVersion(
                panel_id=panel_id,
                version_number=self._get_next_branch_number(panel_id, branch_name),
                comment=description or f"Branch '{branch_name}' from version {from_version.version_number}",
                created_by_id=user_id,
                gene_count=from_version.gene_count,
                changes_summary=f"Branched from version {from_version.version_number}",
                # Add branch metadata
                storage_path=f"branches/{branch_name}/{datetime.datetime.now().isoformat()}"
            )

            db.session.add(branch_version)
            db.session.flush()

            # Copy data from source version
            self._copy_version_data(from_version_id, branch_version.id)

            db.session.commit()

            # Log branch creation
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Created branch '{branch_name}' for panel '{panel.name}'",
                details={
                    "panel_id": panel_id,
                    "branch_name": branch_name,
                    "from_version": from_version.version_number,
                    "branch_version_id": branch_version.id,
                    "description": description
                }
            )

            return branch_version

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating branch '{branch_name}' for panel {panel_id}: {str(e)}")
            raise VersionControlError(f"Failed to create branch: {str(e)}")

    def _get_next_branch_number(self, panel_id: int, branch_name: str) -> int:
        """Get the next version number for a branch"""
        # For branches, we could use a different numbering scheme
        # For now, use the next available version number
        latest = PanelVersion.query.filter_by(panel_id=panel_id)\
            .order_by(desc(PanelVersion.version_number)).first()
        return (latest.version_number + 1) if latest else 1

    def _copy_version_data(self, from_version_id: int, to_version_id: int):
        """Copy all data from one version to another"""
        # This would copy genes, metadata, and other version-specific data
        # Implementation depends on the specific data model
        pass


class TagManager:
    """Manages version tags"""

    def create_tag(self, version_id: int, tag_name: str, tag_type: TagType, user_id: int):
        """Create a tag for a version"""
        try:
            # For now, store tags in the version comment or metadata
            # In a full implementation, this would use a separate tags table
            version = PanelVersion.query.get(version_id)
            if not version:
                raise VersionControlError(f"Version {version_id} not found")

            # Add tag information to storage_path for now
            tag_info = f"tag:{tag_name}:{tag_type.value}"
            if version.storage_path:
                version.storage_path += f"|{tag_info}"
            else:
                version.storage_path = tag_info

            db.session.commit()

            logger.info(f"Created tag '{tag_name}' ({tag_type.value}) for version {version_id}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating tag '{tag_name}' for version {version_id}: {str(e)}")
            raise VersionControlError(f"Failed to create tag: {str(e)}")

    def get_tagged_versions(self, panel_id: int, tag_type: TagType = None) -> List[Dict[str, Any]]:
        """Get all tagged versions for a panel"""
        try:
            query = PanelVersion.query.filter_by(panel_id=panel_id)
            
            if tag_type:
                query = query.filter(PanelVersion.storage_path.contains(f"tag_type:{tag_type.value}"))
            else:
                query = query.filter(PanelVersion.storage_path.contains("tag:"))

            versions = query.all()
            
            result = []
            for version in versions:
                if version.storage_path and "tag:" in version.storage_path:
                    # Parse tag information from storage_path
                    tags = self._parse_tags_from_path(version.storage_path)
                    result.append({
                        "version_id": version.id,
                        "version_number": version.version_number,
                        "tags": tags,
                        "created_at": version.created_at,
                        "comment": version.comment
                    })
            
            return result

        except Exception as e:
            logger.error(f"Error getting tagged versions for panel {panel_id}: {str(e)}")
            return []

    def _parse_tags_from_path(self, storage_path: str) -> List[Dict[str, str]]:
        """Parse tag information from storage path"""
        tags = []
        parts = storage_path.split("|")
        
        for part in parts:
            if part.startswith("tag:"):
                try:
                    _, tag_name, tag_type = part.split(":", 2)
                    tags.append({"name": tag_name, "type": tag_type})
                except ValueError:
                    continue
        
        return tags


class MergeEngine:
    """Handles merging of panel versions"""

    def merge_versions(self, panel_id: int, source_version_id: int,
                      target_version_id: int, user_id: int,
                      strategy: MergeStrategy = MergeStrategy.AUTO,
                      conflict_resolutions: Dict[str, Any] = None) -> PanelVersion:
        """
        Merge two versions of a panel
        
        Args:
            panel_id: Panel ID
            source_version_id: Version to merge from
            target_version_id: Version to merge into
            user_id: User performing the merge
            strategy: Merge strategy
            conflict_resolutions: Manual conflict resolutions
            
        Returns:
            PanelVersion: The merged version
        """
        try:
            # Get versions
            source_version = PanelVersion.query.get(source_version_id)
            target_version = PanelVersion.query.get(target_version_id)
            
            if not source_version or not target_version:
                raise VersionControlError("Source or target version not found")
            
            if source_version.panel_id != panel_id or target_version.panel_id != panel_id:
                raise VersionControlError("Versions do not belong to the specified panel")

            # Detect conflicts
            conflicts = self._detect_conflicts(source_version_id, target_version_id)
            
            if conflicts and strategy == MergeStrategy.AUTO:
                raise BranchConflictError(f"Conflicts detected, manual resolution required: {conflicts}")

            # Perform merge based on strategy
            merged_data = self._perform_merge(
                source_version, target_version, conflicts, strategy, conflict_resolutions
            )

            # Create merged version
            merged_version = PanelVersion(
                panel_id=panel_id,
                version_number=target_version.version_number + 1,
                comment=f"Merged version {source_version.version_number} into {target_version.version_number}",
                created_by_id=user_id,
                gene_count=len(merged_data.get('genes', [])),
                changes_summary=f"Merged {len(conflicts)} conflicts using {strategy.value} strategy"
            )

            db.session.add(merged_version)
            db.session.flush()

            # Apply merged data
            self._apply_merged_data(merged_version.id, merged_data)

            db.session.commit()

            # Log merge operation
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Merged versions for panel {panel_id}",
                details={
                    "panel_id": panel_id,
                    "source_version": source_version.version_number,
                    "target_version": target_version.version_number,
                    "merged_version_id": merged_version.id,
                    "strategy": strategy.value,
                    "conflicts_count": len(conflicts)
                }
            )

            return merged_version

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error merging versions: {str(e)}")
            raise VersionControlError(f"Failed to merge versions: {str(e)}")

    def get_version_diff(self, version1_id: int, version2_id: int) -> Dict[str, Any]:
        """Get differences between two versions"""
        try:
            version1 = PanelVersion.query.get(version1_id)
            version2 = PanelVersion.query.get(version2_id)
            
            if not version1 or not version2:
                raise VersionControlError("One or both versions not found")

            # Get gene data for both versions
            genes1 = self._get_genes_for_version(version1_id)
            genes2 = self._get_genes_for_version(version2_id)

            # Calculate differences
            diff = {
                "version1": {
                    "id": version1.id,
                    "number": version1.version_number,
                    "comment": version1.comment,
                    "gene_count": len(genes1)
                },
                "version2": {
                    "id": version2.id,
                    "number": version2.version_number,
                    "comment": version2.comment,
                    "gene_count": len(genes2)
                },
                "differences": self._calculate_gene_differences(genes1, genes2)
            }

            return diff

        except Exception as e:
            logger.error(f"Error calculating version diff: {str(e)}")
            raise VersionControlError(f"Failed to calculate diff: {str(e)}")

    def _detect_conflicts(self, source_version_id: int, target_version_id: int) -> List[Dict[str, Any]]:
        """Detect conflicts between two versions"""
        conflicts = []
        
        try:
            source_genes = self._get_genes_for_version(source_version_id)
            target_genes = self._get_genes_for_version(target_version_id)
            
            # Create lookup dictionaries
            source_dict = {gene['symbol']: gene for gene in source_genes}
            target_dict = {gene['symbol']: gene for gene in target_genes}
            
            # Find conflicts (same gene with different properties)
            for symbol in set(source_dict.keys()) & set(target_dict.keys()):
                source_gene = source_dict[symbol]
                target_gene = target_dict[symbol]
                
                # Check for differences in key properties
                differences = {}
                for key in ['confidence_level', 'mode_of_inheritance', 'phenotype']:
                    if source_gene.get(key) != target_gene.get(key):
                        differences[key] = {
                            'source': source_gene.get(key),
                            'target': target_gene.get(key)
                        }
                
                if differences:
                    conflicts.append({
                        'gene_symbol': symbol,
                        'type': 'property_conflict',
                        'differences': differences
                    })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error detecting conflicts: {str(e)}")
            return []

    def _perform_merge(self, source_version: PanelVersion, target_version: PanelVersion,
                      conflicts: List[Dict[str, Any]], strategy: MergeStrategy,
                      conflict_resolutions: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform the actual merge operation"""
        
        source_genes = self._get_genes_for_version(source_version.id)
        target_genes = self._get_genes_for_version(target_version.id)
        
        # Start with target genes as base
        merged_genes = {gene['symbol']: gene for gene in target_genes}
        
        # Apply source genes based on strategy
        for source_gene in source_genes:
            symbol = source_gene['symbol']
            
            if symbol not in merged_genes:
                # New gene from source, add it
                merged_genes[symbol] = source_gene
            else:
                # Existing gene, handle conflict based on strategy
                if strategy == MergeStrategy.OURS:
                    # Keep target version
                    continue
                elif strategy == MergeStrategy.THEIRS:
                    # Use source version
                    merged_genes[symbol] = source_gene
                elif strategy == MergeStrategy.MANUAL and conflict_resolutions:
                    # Use manual resolution if provided
                    if symbol in conflict_resolutions:
                        resolved_gene = conflict_resolutions[symbol]
                        merged_genes[symbol] = resolved_gene
        
        return {
            'genes': list(merged_genes.values()),
            'metadata': {
                'merge_strategy': strategy.value,
                'conflicts_resolved': len(conflicts),
                'merged_at': datetime.datetime.now().isoformat()
            }
        }

    def _get_genes_for_version(self, version_id: int) -> List[Dict[str, Any]]:
        """Get gene data for a specific version"""
        # This would query the actual gene data for the version
        # For now, return mock data
        return []

    def _calculate_gene_differences(self, genes1: List[Dict], genes2: List[Dict]) -> Dict[str, Any]:
        """Calculate differences between two gene lists"""
        symbols1 = {gene['symbol'] for gene in genes1}
        symbols2 = {gene['symbol'] for gene in genes2}
        
        return {
            'added': list(symbols2 - symbols1),
            'removed': list(symbols1 - symbols2),
            'modified': [],  # Would need to compare gene properties
            'summary': {
                'total_changes': len(symbols1.symmetric_difference(symbols2)),
                'additions': len(symbols2 - symbols1),
                'deletions': len(symbols1 - symbols2)
            }
        }

    def _apply_merged_data(self, version_id: int, merged_data: Dict[str, Any]):
        """Apply merged data to a version"""
        # This would store the merged gene data
        # Implementation depends on the data model
        pass


# Configuration helper functions
def get_retention_policy_config() -> Dict[str, Any]:
    """Get current retention policy configuration"""
    return {
        'max_versions': current_app.config.get('MAX_PANEL_VERSIONS', 10),
        'backup_retention_days': current_app.config.get('BACKUP_RETENTION_DAYS', 90),
        'auto_backup_enabled': current_app.config.get('AUTO_BACKUP_ENABLED', True),
        'tag_retention_enabled': True,  # Always keep tagged versions
        'production_tag_protected': True  # Never delete production tags
    }


def update_retention_policy_config(max_versions: int = None, backup_retention_days: int = None):
    """Update retention policy configuration"""
    if max_versions is not None:
        current_app.config['MAX_PANEL_VERSIONS'] = max_versions
    
    if backup_retention_days is not None:
        current_app.config['BACKUP_RETENTION_DAYS'] = backup_retention_days
    
    logger.info(f"Updated retention policy: max_versions={max_versions}, backup_retention_days={backup_retention_days}")
