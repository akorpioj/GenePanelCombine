#!/usr/bin/env python3
"""
Version Control Management CLI

This script provides command-line tools for managing the version control system:
- Apply retention policies
- Clean up old versions
- Manage tags and branches
- Generate version control reports
- Configure system-wide version control settings
"""

import argparse
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    SavedPanel, PanelVersion, PanelVersionTag, PanelVersionBranch,
    PanelRetentionPolicy, TagType, User, AuditActionType
)
from app.version_control_service import VersionControlService, RetentionPolicyError
from app.audit_service import AuditService


def init_app():
    """Initialize Flask app for CLI operations"""
    app = create_app()
    app.app_context().push()
    return app


def apply_retention_policies(panel_ids: List[int] = None, dry_run: bool = False):
    """Apply retention policies to panels"""
    print("🧹 Applying retention policies...")
    
    if panel_ids:
        panels = SavedPanel.query.filter(SavedPanel.id.in_(panel_ids)).all()
    else:
        panels = SavedPanel.query.all()
    
    vc_service = VersionControlService()
    total_cleaned = 0
    
    for panel in panels:
        try:
            print(f"  Processing panel '{panel.name}' (ID: {panel.id})...")
            
            # Get current version count
            version_count_before = PanelVersion.query.filter_by(panel_id=panel.id).count()
            
            if not dry_run:
                vc_service.retention_policy.apply_retention(panel.id)
                db.session.commit()
            
            version_count_after = PanelVersion.query.filter_by(panel_id=panel.id).count()
            cleaned = version_count_before - version_count_after
            
            if cleaned > 0:
                print(f"    ✅ Cleaned {cleaned} old versions")
                total_cleaned += cleaned
            else:
                print(f"    ✅ No cleanup needed ({version_count_before} versions)")
                
        except RetentionPolicyError as e:
            print(f"    ❌ Error: {str(e)}")
        except Exception as e:
            print(f"    ❌ Unexpected error: {str(e)}")
    
    if dry_run:
        print(f"\n🔍 DRY RUN: Would clean {total_cleaned} versions across {len(panels)} panels")
    else:
        print(f"\n✅ Cleaned {total_cleaned} versions across {len(panels)} panels")
        
        # Log the cleanup operation
        AuditService.log_action(
            action_type=AuditActionType.SYSTEM_MAINTENANCE,
            action_description=f"Applied retention policies via CLI to {len(panels)} panels",
            details={
                "panels_processed": len(panels),
                "versions_cleaned": total_cleaned,
                "dry_run": dry_run,
                "timestamp": datetime.now().isoformat()
            }
        )


def list_protected_versions():
    """List all protected versions across all panels"""
    print("🔒 Protected versions:")
    
    protected_versions = PanelVersion.query.filter_by(is_protected=True)\
        .join(SavedPanel, PanelVersion.panel_id == SavedPanel.id).order_by(SavedPanel.name, PanelVersion.version_number).all()
    
    if not protected_versions:
        print("  No protected versions found.")
        return
    
    current_panel = None
    for version in protected_versions:
        if current_panel != version.panel.name:
            current_panel = version.panel.name
            print(f"\n  📁 Panel: {current_panel}")
        
        tags = version.tags.all()
        tag_info = ", ".join([f"{tag.tag_name}({tag.tag_type.value})" for tag in tags])
        
        print(f"    🏷️  Version {version.version_number}: {version.comment}")
        print(f"       Created: {version.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"       Tags: {tag_info if tag_info else 'No tags'}")
        print(f"       Priority: {version.retention_priority}")


def generate_version_control_report(output_file: str = None):
    """Generate a comprehensive version control report"""
    print("📊 Generating version control report...")
    
    # Gather statistics
    total_panels = SavedPanel.query.count()
    total_versions = PanelVersion.query.count()
    total_tags = PanelVersionTag.query.count()
    total_branches = PanelVersionBranch.query.count()
    protected_versions = PanelVersion.query.filter_by(is_protected=True).count()
    
    # Version distribution
    version_distribution = db.session.query(
        SavedPanel.id,
        SavedPanel.name,
        db.func.count(PanelVersion.id).label('version_count')
    ).join(PanelVersion, SavedPanel.id == PanelVersion.panel_id).group_by(SavedPanel.id, SavedPanel.name)\
     .order_by(db.func.count(PanelVersion.id).desc()).all()
    
    # Tag type distribution
    tag_distribution = db.session.query(
        PanelVersionTag.tag_type,
        db.func.count(PanelVersionTag.id).label('count')
    ).group_by(PanelVersionTag.tag_type).all()
    
    # Recent activity
    recent_versions = PanelVersion.query\
        .filter(PanelVersion.created_at >= datetime.now() - timedelta(days=30))\
        .count()
    
    recent_tags = PanelVersionTag.query\
        .filter(PanelVersionTag.created_at >= datetime.now() - timedelta(days=30))\
        .count()
    
    # Retention policy coverage
    panels_with_policies = PanelRetentionPolicy.query.count()
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_panels": total_panels,
            "total_versions": total_versions,
            "total_tags": total_tags,
            "total_branches": total_branches,
            "protected_versions": protected_versions,
            "panels_with_retention_policies": panels_with_policies
        },
        "activity_last_30_days": {
            "new_versions": recent_versions,
            "new_tags": recent_tags
        },
        "version_distribution": [
            {
                "panel_id": item[0],
                "panel_name": item[1],
                "version_count": item[2]
            }
            for item in version_distribution[:10]  # Top 10
        ],
        "tag_distribution": [
            {
                "tag_type": item[0].value if hasattr(item[0], 'value') else str(item[0]),
                "count": item[1]
            }
            for item in tag_distribution
        ]
    }
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Report saved to: {output_file}")
    else:
        print("\n📋 Version Control Report:")
        print(f"  📊 Summary:")
        print(f"    • Total panels: {total_panels}")
        print(f"    • Total versions: {total_versions}")
        print(f"    • Total tags: {total_tags}")
        print(f"    • Total branches: {total_branches}")
        print(f"    • Protected versions: {protected_versions}")
        print(f"    • Panels with retention policies: {panels_with_policies}")
        
        print(f"\n  📈 Activity (last 30 days):")
        print(f"    • New versions: {recent_versions}")
        print(f"    • New tags: {recent_tags}")
        
        print(f"\n  🏷️  Tag distribution:")
        for item in tag_distribution:
            tag_type = item[0].value if hasattr(item[0], 'value') else str(item[0])
            print(f"    • {tag_type}: {item[1]}")
        
        print(f"\n  📦 Top panels by version count:")
        for item in version_distribution[:5]:
            print(f"    • {item[1]}: {item[2]} versions")


def create_tag(panel_id: int, version_number: int, tag_name: str, tag_type: str, description: str = None):
    """Create a tag for a specific version"""
    print(f"🏷️  Creating tag '{tag_name}'...")
    
    try:
        panel = SavedPanel.query.get(panel_id)
        if not panel:
            print(f"❌ Panel {panel_id} not found")
            return False
        
        version = PanelVersion.query.filter_by(
            panel_id=panel_id, 
            version_number=version_number
        ).first()
        if not version:
            print(f"❌ Version {version_number} not found for panel {panel_id}")
            return False
        
        # Validate tag type
        try:
            tag_type_enum = TagType(tag_type.upper())
        except ValueError:
            print(f"❌ Invalid tag type: {tag_type}")
            print(f"Valid types: {', '.join([t.value for t in TagType])}")
            return False
        
        # Check for existing tag
        existing_tag = PanelVersionTag.query.filter_by(
            version_id=version.id,
            tag_name=tag_name
        ).first()
        if existing_tag:
            print(f"❌ Tag '{tag_name}' already exists for this version")
            return False
        
        # Create admin user for CLI operations
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found. Please create an admin user first.")
            return False
        
        # Use version control service
        vc_service = VersionControlService()
        vc_service.tag_manager.create_tag(version.id, tag_name, tag_type_enum, admin_user.id)
        
        print(f"✅ Created tag '{tag_name}' ({tag_type_enum.value}) for version {version_number}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tag: {str(e)}")
        return False


def configure_retention_policy(panel_id: int, max_versions: int = None, 
                             backup_retention_days: int = None, 
                             auto_cleanup: bool = None):
    """Configure retention policy for a panel"""
    print(f"⚙️  Configuring retention policy for panel {panel_id}...")
    
    try:
        panel = SavedPanel.query.get(panel_id)
        if not panel:
            print(f"❌ Panel {panel_id} not found")
            return False
        
        policy = PanelRetentionPolicy.query.filter_by(panel_id=panel_id).first()
        if not policy:
            # Create admin user for CLI operations
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("❌ Admin user not found. Please create an admin user first.")
                return False
            
            policy = PanelRetentionPolicy(
                panel_id=panel_id,
                created_by_id=admin_user.id
            )
            db.session.add(policy)
        
        # Update policy
        if max_versions is not None:
            policy.max_versions = max_versions
        if backup_retention_days is not None:
            policy.backup_retention_days = backup_retention_days
        if auto_cleanup is not None:
            policy.auto_cleanup_enabled = auto_cleanup
        
        policy.updated_at = datetime.now()
        db.session.commit()
        
        print(f"✅ Updated retention policy:")
        print(f"   • Max versions: {policy.max_versions}")
        print(f"   • Backup retention: {policy.backup_retention_days} days")
        print(f"   • Auto cleanup: {policy.auto_cleanup_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring retention policy: {str(e)}")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Version Control Management CLI for PanelMerge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply retention policies to all panels
  python version_control_cli.py retention --apply

  # Dry run retention policies
  python version_control_cli.py retention --apply --dry-run

  # List protected versions
  python version_control_cli.py list --protected

  # Generate report
  python version_control_cli.py report --output report.json

  # Create a production tag
  python version_control_cli.py tag --panel-id 1 --version 5 --name "v1.0-prod" --type production

  # Configure retention policy
  python version_control_cli.py config --panel-id 1 --max-versions 15 --retention-days 120
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Retention command
    retention_parser = subparsers.add_parser('retention', help='Manage retention policies')
    retention_parser.add_argument('--apply', action='store_true', help='Apply retention policies')
    retention_parser.add_argument('--panel-ids', type=int, nargs='+', help='Specific panel IDs (default: all)')
    retention_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List version control information')
    list_parser.add_argument('--protected', action='store_true', help='List protected versions')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate version control reports')
    report_parser.add_argument('--output', type=str, help='Output file for JSON report')
    
    # Tag command
    tag_parser = subparsers.add_parser('tag', help='Manage version tags')
    tag_parser.add_argument('--panel-id', type=int, required=True, help='Panel ID')
    tag_parser.add_argument('--version', type=int, required=True, help='Version number')
    tag_parser.add_argument('--name', type=str, required=True, help='Tag name')
    tag_parser.add_argument('--type', type=str, required=True, help='Tag type')
    tag_parser.add_argument('--description', type=str, help='Tag description')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configure retention policies')
    config_parser.add_argument('--panel-id', type=int, required=True, help='Panel ID')
    config_parser.add_argument('--max-versions', type=int, help='Maximum versions to keep')
    config_parser.add_argument('--retention-days', type=int, help='Backup retention days')
    config_parser.add_argument('--auto-cleanup', type=bool, help='Enable auto cleanup')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize Flask app
    app = init_app()
    
    try:
        if args.command == 'retention':
            if args.apply:
                apply_retention_policies(args.panel_ids, args.dry_run)
            else:
                print("Use --apply to run retention policies")
        
        elif args.command == 'list':
            if args.protected:
                list_protected_versions()
            else:
                print("Use --protected to list protected versions")
        
        elif args.command == 'report':
            generate_version_control_report(args.output)
        
        elif args.command == 'tag':
            create_tag(args.panel_id, args.version, args.name, args.type, args.description)
        
        elif args.command == 'config':
            configure_retention_policy(
                args.panel_id, 
                args.max_versions, 
                args.retention_days, 
                args.auto_cleanup
            )
        
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        raise


if __name__ == '__main__':
    main()
