from flask import request, jsonify
from flask_login import current_user
import datetime
from app.models import SavedPanel, PanelVersion, PanelGene, PanelStatus, PanelVisibility, db, AuditActionType, PanelChange, ChangeType
from app.main.utils import logger
from app.audit_service import AuditService
from sqlalchemy import desc, exc

def _get_panel_query_base(user_id, include_deleted=False):
    """
    Get base query for user panels with optional inclusion of deleted panels
    
    Args:
        user_id: The user ID to filter by
        include_deleted: Whether to include panels with DELETED status
        
    Returns:
        SQLAlchemy query object
    """
    query = SavedPanel.query.filter_by(owner_id=user_id)
    if not include_deleted:
        query = query.filter(SavedPanel.status != PanelStatus.DELETED)
    return query

def get_panels(request):
    """
    Get user's saved panels for enhanced panel library
    
    Note: This function excludes panels with DELETED status from the results.
    Only active, draft, and archived panels are returned.
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Get user's panels (exclude deleted panels)
        query = SavedPanel.query.filter_by(owner_id=current_user.id).filter(SavedPanel.status != PanelStatus.DELETED)
        
        # Apply search filter if provided
        search = request.args.get('search', '').strip()
        if search:
            query = query.filter(SavedPanel.name.contains(search))
        
        # Apply status filter if provided
        status = request.args.get('status', '').strip()
        if status:
            query = query.filter(SavedPanel.status == status)
            
        # Apply visibility filter if provided
        visibility = request.args.get('visibility', '').strip()
        if visibility:
            query = query.filter(SavedPanel.visibility == visibility)
        
        # Apply gene count range filter if provided
        gene_count_min = request.args.get('gene_count_min')
        gene_count_max = request.args.get('gene_count_max')
        if gene_count_min is not None:
            try:
                min_count = int(gene_count_min)
                query = query.filter(SavedPanel.gene_count >= min_count)
            except ValueError:
                pass
        if gene_count_max is not None:
            try:
                max_count = int(gene_count_max)
                query = query.filter(SavedPanel.gene_count <= max_count)
            except ValueError:
                pass
        
        # Apply sorting
        sort_by = request.args.get('sort_by', 'updated_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if hasattr(SavedPanel, sort_by):
            sort_field = getattr(SavedPanel, sort_by)
            if sort_order == 'desc':
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(sort_field)
        else:
            query = query.order_by(desc(SavedPanel.updated_at))
        
        # Paginate
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        panels = []
        for panel in pagination.items:
            try:
                panels.append({
                    'id': panel.id,
                    'name': panel.name or '',
                    'description': panel.description or '',
                    'gene_count': panel.gene_count or 0,
                    'status': str(panel.status) if panel.status else 'ACTIVE',
                    'visibility': str(panel.visibility) if panel.visibility else 'PRIVATE',
                    'source_type': panel.source_type or 'unknown',
                    'created_at': panel.created_at.isoformat() if panel.created_at else None,
                    'updated_at': panel.updated_at.isoformat() if panel.updated_at else None,
                    'version_count': panel.version_count or 1,
                    'tags': panel.tags.split(',') if panel.tags else [],
                    'owner': {
                        'id': panel.owner.id,
                        'username': panel.owner.username
                    }
                })
            except Exception as e:
                logger.error(f"Error processing panel {panel.id}: {e}")
                continue

        AuditService.log_action(
            resource_type="panel_list",
            user_id=current_user.id,
            action_type=AuditActionType.PANEL_LIST,
            action_description=f"User viewed panels list (page {page}, {per_page} per page)",
            details={"page": page, "per_page": per_page, "search": search, "status": status, "visibility": visibility}
        )
        
        # Calculate totals for all filtered results (not just current page)
        total_query = SavedPanel.query.filter_by(owner_id=current_user.id).filter(SavedPanel.status != PanelStatus.DELETED)
        
        # Apply the same filters to the totals query
        if search:
            total_query = total_query.filter(SavedPanel.name.contains(search))
        if status:
            total_query = total_query.filter(SavedPanel.status == status)
        if visibility:
            total_query = total_query.filter(SavedPanel.visibility == visibility)
        if gene_count_min is not None:
            try:
                min_count = int(gene_count_min)
                total_query = total_query.filter(SavedPanel.gene_count >= min_count)
            except ValueError:
                pass
        if gene_count_max is not None:
            try:
                max_count = int(gene_count_max)
                total_query = total_query.filter(SavedPanel.gene_count <= max_count)
            except ValueError:
                pass
        
        # Calculate totals from filtered results
        from sqlalchemy import func
        totals_result = total_query.with_entities(
            func.sum(SavedPanel.gene_count).label('total_genes'),
            func.sum(SavedPanel.version_count).label('total_versions'),
            func.count(SavedPanel.id).label('total_panels')
        ).first()
        
        total_genes = totals_result.total_genes or 0
        total_versions = totals_result.total_versions or 0
        total_panels = totals_result.total_panels or 0
        
        print(pagination.page, pagination.pages, pagination.per_page, pagination.total)
        return jsonify({
            'panels': panels,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'total_genes': total_genes,
                'total_versions': total_versions,
                'total_panels': total_panels
            }
        })
    except Exception as e:
        logger.error(f"Error getting user panels: {e}")
        return jsonify({'message': 'Failed to get panels'}), 500

def create_or_update_panel(request):
    """
    Create a new panel or update an existing panel
    
    Note: Updates to panels with DELETED status are not allowed and will return 403 Forbidden.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        if not data.get('genes') or not isinstance(data['genes'], list):
            return jsonify({'message': 'Genes list is required'}), 400
        if not data.get('name') or data['name'] == '':
            return jsonify({'message': 'Panel name is required'}), 400

        # Check if this is an update (panel_id provided) or create (no panel_id)
        panel_id = data.get('panel_id') or data.get('id')

        if not panel_id:
            # Create new panel
            return create_panel(data)


        # Convert panel_id to int if it's provided as a string
        if panel_id:
            try:
                panel_id = int(panel_id)
            except (ValueError, TypeError):
                return jsonify({'message': 'Invalid panel ID format'}), 400
                        
        # Use explicit filter with integer comparison to avoid type casting issues
        panel = SavedPanel.query.filter(
            SavedPanel.id == panel_id,
            SavedPanel.owner_id == current_user.id
        ).first()
        if not panel:
            return jsonify({'message': 'Panel not found or access denied'}), 404

        return update_panel_data(panel, request)

        # Update existing panel
    except Exception as e:
        logger.error(f"Error creating/updating panel: {e}")
        return jsonify({'message': 'Failed to create/update panel'}), 500

def update_genes(old_data, new_data):
    old_genes = old_data.genes
    new_genes = new_data['genes']

    # Compare old and new genes to find changes
    added_genes = []
    removed_genes = []
    updated_genes = []
    
    # Use sets for O(1) membership testing instead of O(n) list lookup
    new_gene_symbols = {gene['gene_symbol'] for gene in new_genes}
    
    # Create a dictionary for O(1) lookups instead of O(n) linear search
    old_genes_dict = {gene.gene_symbol: gene for gene in old_genes}
    old_gene_symbols = set(old_genes_dict.keys())
    
    # Find added and updated genes
    for gene in new_genes:
        gene_symbol = gene['gene_symbol']
        if gene_symbol not in old_gene_symbols:
            added_genes.append(gene)
        else:
            # Check for updates in existing genes - now O(1) lookup
            old_gene = old_genes_dict[gene_symbol]
            if old_gene:
                if old_gene.gene_name != gene.get('gene_name', old_gene.gene_name) or \
                    old_gene.ensembl_id != gene.get('ensembl_id', old_gene.ensembl_id) or \
                    old_gene.hgnc_id != gene.get('hgnc_id', old_gene.hgnc_id) or \
                    old_gene.confidence_level != gene.get('confidence_level', old_gene.confidence_level) or \
                    old_gene.mode_of_inheritance != gene.get('mode_of_inheritance', old_gene.mode_of_inheritance) or \
                    old_gene.phenotype != gene.get('phenotype', old_gene.phenotype) or \
                    old_gene.evidence_level != gene.get('evidence_level', old_gene.evidence_level) or \
                    old_gene.source_panel_id != gene.get('source_panel_id', old_gene.source_panel_id) or \
                    old_gene.source_list_type != gene.get('source_list_type', old_gene.source_list_type) or \
                    old_gene.user_notes != gene.get('user_notes', old_gene.user_notes) or \
                    old_gene.custom_confidence != gene.get('custom_confidence', old_gene.custom_confidence):

                    updated_genes.append({
                        'old': old_gene,
                        'new': gene
                    })
    for gene in old_genes:
        if gene.gene_symbol not in new_gene_symbols:
            removed_genes.append(gene)

    # Add new genes
    for gene_data in added_genes:
        gene = PanelGene(
            panel_id=old_data.id,
            gene_symbol=gene_data.get('gene_symbol', ''),
            gene_name=gene_data.get('gene_name', ''),
            ensembl_id=gene_data.get('ensembl_id', ''),
            hgnc_id=gene_data.get('hgnc_id', ''),
            confidence_level=gene_data.get('confidence_level', ''),
            mode_of_inheritance=gene_data.get('mode_of_inheritance', ''),
            phenotype=gene_data.get('phenotype', ''),
            evidence_level=gene_data.get('evidence_level', ''),
            source_panel_id=gene_data.get('source_panel_id', ''),
            source_list_type=gene_data.get('source_list_type', ''),
            added_by_id=current_user.id,
            user_notes=gene_data.get('user_notes', ''),
            custom_confidence=gene_data.get('custom_confidence', '')
        )

        db.session.add(gene)
        print("Added: ", gene_data.get('gene_symbol', ''))

    # Remove old genes - BULK DELETE using IN clause (single query instead of N queries)
    if removed_genes:
        removed_symbols = [gene.gene_symbol for gene in removed_genes]
        db.session.query(PanelGene).filter(
            PanelGene.panel_id == old_data.id,
            PanelGene.gene_symbol.in_(removed_symbols)
        ).delete(synchronize_session='fetch')
        print(f"Removed {len(removed_symbols)} genes in bulk: {', '.join(removed_symbols)}")

    # Update existing genes - Use ORM objects for better performance
    for update in updated_genes:
        old_gene = update['old']
        new_gene = update['new']
        
        # Update the ORM object directly instead of using query().update()
        old_gene.gene_name = new_gene.get('gene_name', old_gene.gene_name)
        old_gene.ensembl_id = new_gene.get('ensembl_id', old_gene.ensembl_id)
        old_gene.hgnc_id = new_gene.get('hgnc_id', old_gene.hgnc_id)
        old_gene.confidence_level = new_gene.get('confidence_level', old_gene.confidence_level)
        old_gene.mode_of_inheritance = new_gene.get('mode_of_inheritance', old_gene.mode_of_inheritance)
        old_gene.phenotype = new_gene.get('phenotype', old_gene.phenotype)
        old_gene.evidence_level = new_gene.get('evidence_level', old_gene.evidence_level)
        old_gene.source_panel_id = new_gene.get('source_panel_id', old_gene.source_panel_id)
        old_gene.source_list_type = new_gene.get('source_list_type', old_gene.source_list_type)
        old_gene.user_notes = new_gene.get('user_notes', old_gene.user_notes)
        old_gene.custom_confidence = new_gene.get('custom_confidence', old_gene.custom_confidence)
        old_gene.is_modified = True
        
        print(f"Updated: {new_gene.get('gene_symbol', '')}")

    return {
        'added': added_genes,
        'removed': removed_genes,
        'updated': updated_genes
    }

def create_panel(data):

    try:        
        # Check for duplicate panel name for this user
        existing_panel = SavedPanel.query.filter_by(
            owner_id=current_user.id,
            name=data['name']
        ).first()
        
        if existing_panel:
            return jsonify({'message': f"Panel with name '{data['name']}' already exists"}), 400
        
        # Create saved panel
        panel = SavedPanel(
            name=data['name'],
            description=data.get('description', ''),
            tags=data.get('tags', ''),
            owner_id=current_user.id,
            status=PanelStatus(data.get('status', 'ACTIVE').upper()),
            visibility=PanelVisibility(data.get('visibility', 'PRIVATE').upper()),
            gene_count=len(data['genes']),
            source_type=data.get('source_type', 'manual'),
            source_reference=data.get('source_reference', ''),
            storage_backend='gcs',  # Default to Google Cloud Storage
        )
        
        db.session.add(panel)
        db.session.flush()  # Get the panel ID
        
        # Create initial version
        version = PanelVersion(
            panel_id=panel.id,
            version_number=1,
            comment=data.get('version_comment', 'Initial version'),
            created_by_id=current_user.id,
            gene_count=len(data['genes']),
            changes_summary=f"Created panel with {len(data['genes'])} genes"
        )
        
        db.session.add(version)
        db.session.flush()  # Get the version ID
        
        # Set current version
        panel.current_version_id = version.id
        
        # Add genes
        for gene_data in data['genes']:
            gene = PanelGene(
                panel_id=panel.id,
                gene_symbol=gene_data.get('gene_symbol', ''),
                gene_name=gene_data.get('gene_name', ''),
                ensembl_id=gene_data.get('ensembl_id', ''),
                hgnc_id=gene_data.get('hgnc_id', ''),
                confidence_level=gene_data.get('confidence_level', ''),
                mode_of_inheritance=gene_data.get('mode_of_inheritance', ''),
                phenotype=gene_data.get('phenotype', ''),
                evidence_level=gene_data.get('evidence_level', ''),
                source_panel_id=gene_data.get('source_panel_id', ''),
                source_list_type=gene_data.get('source_list_type', ''),
                added_by_id=current_user.id,
                user_notes=gene_data.get('user_notes', ''),
                custom_confidence=gene_data.get('custom_confidence', '')
            )
            db.session.add(gene)
        
        # Record creation change
        change = PanelChange(
            panel_id=panel.id,
            version_id=version.id,
            change_type=ChangeType.PANEL_CREATED,
            target_type='panel',
            target_id=str(panel.id),
            changed_by_id=current_user.id,
            change_reason=data.get('version_comment', 'Panel created')
        )
        change.new_value = {
            'panel_name': panel.name,
            'gene_count': panel.gene_count,
            'description': panel.description
        }
        db.session.add(change)
        
        db.session.commit()
        
        # Log creation
        AuditService.log_action(
            action_type=AuditActionType.PANEL_CREATE,
            action_description=f"Created saved panel '{panel.name}' via web page",
            user_id=current_user.id,
            details={
                "panel_id": panel.id,
                "panel_name": panel.name,
                "gene_count": panel.gene_count,
                "status": panel.status.value,
                "visibility": panel.visibility.value
            }
        )        
    except exc.IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database integrity error creating panel: {str(e)}")
        return jsonify({'message': 'Database constraint violation'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating saved panel: {str(e)}")
        return jsonify({'message': 'Failed to create saved panel'}), 500

    # Return created panel
    response_data = {
        'id': panel.id,
        'name': panel.name,
        'description': panel.description,
        'tags': panel.tags,
        'status': panel.status.value,
        'visibility': panel.visibility.value,
        'gene_count': panel.gene_count,
        'version_count': panel.version_count,
        'created_at': panel.created_at.isoformat(),
        'updated_at': panel.updated_at.isoformat(),
        'source_type': panel.source_type,
        'source_reference': panel.source_reference,
        'storage_backend': panel.storage_backend,
        'current_version_id': panel.current_version_id
    }
    return jsonify({
        'message': f'Panel created successfully',
        'panel': response_data
        }), 201

def get_panel_data(panel):
    try:
        # Get panel genes
        genes = []
        for gene in panel.genes:
            genes.append({
                'symbol': gene.gene_symbol,
                'name': gene.gene_name,
                'ensembl_id': gene.ensembl_id,
                'hgnc_id': gene.hgnc_id,
                'confidence_level': gene.confidence_level,
                'mode_of_inheritance': gene.mode_of_inheritance,
                'phenotype': gene.phenotype,
                'evidence_level': gene.evidence_level,
                'source_panel_id': gene.source_panel_id,
                'source_list_type': gene.source_list_type,
                'added_by_id': gene.added_by_id,
                'user_notes': gene.user_notes,
                'custom_confidence': gene.custom_confidence
            })
        
        panel_data = {
            'id': panel.id,
            'name': panel.name,
            'description': panel.description,
            'gene_count': panel.gene_count,
            'status': str(panel.status),
            'visibility': str(panel.visibility),
            'source_type': panel.source_type,
            'source_reference': panel.source_reference,
            'created_at': panel.created_at.isoformat(),
            'updated_at': panel.updated_at.isoformat(),
            'last_accessed_at': panel.last_accessed_at.isoformat() if panel.last_accessed_at else None,
            'version_count': panel.current_version_number or 1,
            'tags': panel.tags.split(',') if panel.tags else [],
            'genes': genes
        }
        
        # Update last accessed time
        panel.last_accessed_at = datetime.datetime.now()
        db.session.commit()
        
        return jsonify({'panel': panel_data})
        
    except Exception as e:
        logger.error(f"Error getting panel {panel.id}: {e}")
        return jsonify({'message': 'Failed to get panel details'}), 500

def update_panel_data(panel, request):
    """
    Update panel data
    
    Note: Updates to panels with DELETED status are not allowed and will return 403 Forbidden.
    """
    try:
        # Prevent modifications to deleted panels
        if panel.status == PanelStatus.DELETED:
            return jsonify({'message': 'Cannot modify deleted panels'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        old_values = {}
        new_values = {}
        
        # Track changes for version history
        if 'name' in data and data['name'] != panel.name:
            old_values['name'] = panel.name
            new_values['name'] = data['name']
            panel.name = data['name']
        
        if 'description' in data and data['description'] != panel.description:
            old_values['description'] = panel.description
            new_values['description'] = data['description']
            panel.description = data['description']
        
        if 'tags' in data:
            new_tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']
            if new_tags != panel.tags:
                old_values['tags'] = panel.tags
                new_values['tags'] = data['tags']
                panel.tags = new_tags
        
        if 'status' in data:
            try:
                new_status = PanelStatus(data['status'].upper())
                if new_status != panel.status:
                    old_values['status'] = panel.status.value
                    new_values['status'] = new_status.value
                    panel.status = new_status
            except ValueError:
                return jsonify({'message': f"Invalid status: {data['status']}"}), 400
        
        if 'visibility' in data:
            try:
                new_visibility = PanelVisibility(data['visibility'].upper())
                if new_visibility != panel.visibility:
                    old_values['visibility'] = panel.visibility.value
                    new_values['visibility'] = new_visibility.value
                    panel.visibility = new_visibility
            except ValueError:
                return jsonify({'message': f"Invalid visibility: {data['visibility']}"}), 400

        changed = update_genes(panel, data)
        changed_str = ''
        n_added = len(changed['added'])
        n_removed = len(changed['removed'])
        n_updated = len(changed['updated'])
        
        # Update gene count after gene modifications
        panel.gene_count = panel.gene_count - n_removed + n_added
        print("Gene count: ", panel.gene_count)

        if changed['added'] and n_added > 0:
            genes = [ gene.get('gene_symbol', '') for gene in changed['added'] ]
            changed_str += f"Added genes: {', '.join(genes)}. "
        if changed['removed'] and n_removed > 0:
            genes = [ gene.gene_symbol for gene in changed['removed'] ]
            changed_str += f"Removed genes: {', '.join(genes)}. "
        if changed['updated'] and n_updated > 0:
            genes = [ gene.get('gene_symbol', '') for gene in changed['updated'] ]
            changed_str += f"Updated genes: {', '.join(genes)}. "
        logger.info("Changed genes: %s", changed_str)
    
        # Create new version if significant changes
        if len(old_values) > 0 or n_added > 0 or n_removed > 0 or n_updated > 0:
            logger.info("Significant changes detected, creating new version")
            panel.updated_at = datetime.datetime.now()
            panel.last_accessed_at = datetime.datetime.now()
            version_comment = ''
            change_summary = 'Updated: '
            if len(old_values) > 0: 
                version_comment += "Panel metadata updated. "
                change_summary += ', '.join(old_values.keys())
            if n_added > 0 or n_removed > 0 or n_updated > 0:
                version_comment += changed_str
                change_summary += f"Added: {n_added} genes, removed: {n_removed} genes, updated: {n_updated} genes"
            logger.info("Version comment: %s", version_comment)
            logger.info("Change summary: %s", change_summary)
            version = panel.create_new_version(
                user_id=current_user.id,
                comment=data.get('version_comment', version_comment),
                changes_summary=change_summary)
            panel.version_count = version.version_number
            
            # Record change
            change = PanelChange(
                panel_id=panel.id,
                version_id=version.id,
                change_type=ChangeType.METADATA_CHANGED,
                target_type='panel',
                target_id=str(panel.id),
                changed_by_id=current_user.id,
                change_reason=data.get('version_comment', 'Panel metadata updated')
            )        
            change.old_value = old_values
            change.new_value = new_values
            db.session.add(change)
            db.session.commit()
        
            # Log update
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Updated saved panel '{panel.name}' via web",
                details={
                    "panel_id": panel.id,
                    "panel_name": panel.name,
                    "changes": list(old_values.keys())
                }
            )
        else:
            logger.info("No significant changes detected, no new version created")
            panel.last_accessed_at = datetime.datetime.now()
            db.session.commit()
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Accessed saved panel '{panel.name}' via web (no changes)",
                details={
                    "panel_id": panel.id,
                    "panel_name": panel.name,
                    "changes": []
                }
            )
            return jsonify({'message': 'No changes detected, panel not updated.'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating saved panel {panel.id}: {str(e)}.")
            
        # Provide specific error messages based on the type of constraint violation
        error_msg = str(e)
        if "uq_panel_gene_symbol" in error_msg:
            return jsonify({'message': 'Duplicate gene detected. A gene with this symbol already exists in the panel.'}), 400
        elif "duplicate key" in error_msg.lower():
            return jsonify({'message': 'Duplicate data detected. Please check for duplicate entries.'}), 400
        elif "constraint" in error_msg.lower():
            return jsonify({'message': 'Database constraint violation. Please check your data for invalid values.'}), 400
        else:
            return jsonify({'message': 'Failed to save panel due to a database error. Please try again.'}), 500
        
    # Return updated panel data
    response_data = {
        'id': panel.id,
        'name': panel.name,
        'description': panel.description,
        'tags': panel.tags,
        'status': panel.status.value,
        'visibility': panel.visibility.value,
        'gene_count': panel.gene_count,
        'version_count': panel.version_count,
        'created_at': panel.created_at.isoformat(),
        'updated_at': panel.updated_at.isoformat(),
        'source_type': panel.source_type,
        'source_reference': panel.source_reference,
        'storage_backend': panel.storage_backend,
        'current_version_id': panel.current_version_id
    }
        
    return jsonify({
        'message': f'Panel updated successfully.',
        'panel': response_data
        }), 200      
