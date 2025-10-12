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

        # Update existing panel

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
        
        # Prevent modifications to deleted panels
        if panel.status == PanelStatus.DELETED:
            return jsonify({'message': 'Cannot modify deleted panels'}), 403

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
        
        if 'tags' in data and data['tags'] != panel.tags:
            print("tags:", data['tags'])
            old_values['tags'] = panel.tags
            new_values['tags'] = data['tags']
            panel.tags = data['tags']
        
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
        print("01")
        if changed['added'] and n_added > 0:
            genes = [ gene.get('gene_symbol', '') for gene in changed['added'] ]
            changed_str += f"Added genes: {', '.join(genes)}. "
        print("02")
        if changed['removed'] and n_removed > 0:
            genes = [ gene.gene_symbol for gene in changed['removed'] ]
            changed_str += f"Removed genes: {', '.join(genes)}. "
        print("03")
        if changed['updated'] and n_updated > 0:
            genes = [ gene.get('gene_symbol', '') for gene in changed['updated'] ]
            changed_str += f"Updated genes: {', '.join(genes)}. "
        logger.info(changed_str)
    
        # Create new version if significant changes
        print("04")
        if old_values or n_added > 0 or n_removed > 0 or n_updated > 0:
            print("1")
            version_comment = ''
            change_summary = 'Updated: '
            if old_values: 
                version_comment += "Panel metadata updated. "
                change_summary += ', '.join(old_values.keys())
            print("2")
            if n_added > 0 or n_removed > 0 or n_updated > 0:
                version_comment += changed_str
                change_summary += f"Added: {n_added} genes, removed: {n_removed} genes, updated: {n_updated} genes"
            print("3")
            version = panel.create_new_version(
                user_id=current_user.id,
                comment=data.get('version_comment', version_comment),
                changes_summary=change_summary)
            
            print("4")
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
            print("5")
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
            print("6")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating saved panel {panel_id}: {str(e)}")
            
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
        'message': f'Panel updated successfully',
        'panel': response_data
        }), 200

def update_genes(old_data, new_data):
    old_genes = old_data.genes
    new_genes = new_data['genes']

    # Compare old and new genes to find changes
    added_genes = []
    removed_genes = []
    updated_genes = []
    old_gene_symbols = {gene.gene_symbol for gene in old_genes}
    new_gene_symbols = {gene['gene_symbol'] for gene in new_genes}
    for gene in new_genes:
        if gene['gene_symbol'] not in old_gene_symbols:
            added_genes.append(gene)
        else:
            # Check for updates in existing genes
            old_gene = next((g for g in old_genes if g.gene_symbol == gene['gene_symbol']), None)
            if old_gene:

                if old_gene.gene_name != gene.get('gene_name', old_gene.gene_name):
                    print(old_gene.gene_name, gene.get('gene_name', old_gene.gene_name))
                if old_gene.evidence_level != gene.get('evidence_level', old_gene.evidence_level):
                    print(old_gene.evidence_level, gene.get('evidence_level', old_gene.evidence_level))
                if old_gene.source_panel_id != gene.get('source_panel_id', old_gene.source_panel_id):
                    print(old_gene.source_panel_id, gene.get('source_panel_id', old_gene.source_panel_id))
                if old_gene.source_list_type != gene.get('source_list_type', old_gene.source_list_type):
                    print(old_gene.source_list_type, gene.get('source_list_type', old_gene.source_list_type))

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

    # Remove old genes
    for gene in removed_genes:
        # Assuming PanelGene has a unique constraint on (panel_id, gene_symbol)
        db.session.query(PanelGene).filter(
            PanelGene.panel_id == old_data.id,
            PanelGene.gene_symbol == gene.gene_symbol
        ).delete()
        print("Removed: ", gene.gene_symbol)

    # Update existing genes
    for update in updated_genes:
        old_gene = update['old']
        new_gene = update['new']
        db.session.query(PanelGene).filter(
            PanelGene.panel_id == old_data.id,
            PanelGene.gene_symbol == new_gene['gene_symbol']
        ).update({
            'gene_name': new_gene.get('gene_name', old_gene.gene_name),
            'ensembl_id': new_gene.get('ensembl_id', old_gene.ensembl_id),
            'hgnc_id': new_gene.get('hgnc_id', old_gene.hgnc_id),
            'confidence_level': new_gene.get('confidence_level', old_gene.confidence_level),
            'mode_of_inheritance': new_gene.get('mode_of_inheritance', old_gene.mode_of_inheritance),
            'phenotype': new_gene.get('phenotype', old_gene.phenotype),
            'evidence_level': new_gene.get('evidence_level', old_gene.evidence_level),
            'source_panel_id': new_gene.get('source_panel_id', old_gene.source_panel_id),
            'source_list_type': new_gene.get('source_list_type', old_gene.source_list_type),
            'added_by_id': new_gene.get('added_by_id', old_gene.added_by_id),
            'user_notes': new_gene.get('user_notes', old_gene.user_notes),
            'custom_confidence': new_gene.get('custom_confidence', old_gene.custom_confidence),
            'is_modified': True  # Mark as modified
        })
        print("Updated: ", new_gene.get('gene_symbol', ''))

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
        
        # Parse and validate enum values
        updated_fields = []
        
        if 'name' in data:
            panel.name = data['name'][:255]
            updated_fields.append('name')
        if 'description' in data:
            panel.description = data['description'][:1000] if data['description'] else None
            updated_fields.append('description')
        if 'tags' in data:
            print("tags:", data['tags'])
            panel.tags = data['tags'][:500] if data['tags'] else None
            updated_fields.append('tags')
        if 'status' in data:
            try:
                panel.status = PanelStatus(data['status'])
                updated_fields.append('status')
            except ValueError:
                return jsonify({'message': f'Invalid status: {data["status"]}'}), 400
        if 'visibility' in data:
            try:
                panel.visibility = PanelVisibility(data['visibility'])
                updated_fields.append('visibility')
            except ValueError:
                return jsonify({'message': f'Invalid visibility: {data["visibility"]}'}), 400
        if 'source_reference' in data:
            panel.source_reference = data['source_reference'][:1000] if data['source_reference'] else None
            updated_fields.append('source_reference')
        
        # Handle gene updates if provided
        genes_data = data.get('genes') or data.get('gene_list')
        if genes_data is not None:  # Allow empty list to clear genes
            # Clear existing genes
            PanelGene.query.filter_by(panel_id=panel.id).delete()
            
            # Add new genes
            gene_count = 0
            if isinstance(genes_data, list):
                for gene_data in genes_data:
                    if isinstance(gene_data, dict):
                        gene = PanelGene(
                            panel_id=panel.id,
                            gene_symbol=gene_data.get('symbol', ''),
                            gene_name=gene_data.get('name', ''),
                            ensembl_id=gene_data.get('ensembl_id', ''),
                            hgnc_id=gene_data.get('hgnc_id', ''),
                            confidence_level=gene_data.get('confidence_level', 'Unknown'),
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
                        gene_count += 1
                    elif isinstance(gene_data, str):
                        gene = PanelGene(
                            panel_id=panel.id,
                            gene_symbol=gene_data.strip()
                        )
                        db.session.add(gene)
                        gene_count += 1
            elif isinstance(genes_data, str):
                # Parse comma-separated or newline-separated genes
                gene_symbols = [g.strip() for g in genes_data.replace('\n', ',').split(',') if g.strip()]
                for symbol in gene_symbols:
                    gene = PanelGene(
                        panel_id=panel.id,
                        gene_symbol=symbol
                    )
                    db.session.add(gene)
                    gene_count += 1
            
            panel.gene_count = gene_count
            updated_fields.append('genes')
        
        panel.updated_at = datetime.datetime.now()
        
        # Create audit entry
        AuditService.log_action(
            action_type=AuditActionType.PANEL_UPDATE,
            action_description=f"Panel updated: {panel.name}",
            user_id=current_user.id,
            details={"panel_id": panel.id, "updated_fields": updated_fields}
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Panel updated successfully',
            'panel': {
                'id': panel.id,
                'name': panel.name,
                'description': panel.description,
                'gene_count': panel.gene_count,
                'status': str(panel.status),
                'visibility': str(panel.visibility),
                'updated_at': panel.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating panel {panel.id}: {e}")
        return jsonify({'message': 'Failed to update panel'}), 500
