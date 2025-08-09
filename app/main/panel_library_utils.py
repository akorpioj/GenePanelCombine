from flask import request, jsonify
from flask_login import current_user
import datetime
from ..models import SavedPanel, PanelVersion, PanelGene, PanelStatus, PanelVisibility, db, AuditActionType
from .utils import logger
from ..audit_service import AuditService
from sqlalchemy import desc

def get_panels(request):
    """Get user's saved panels for enhanced panel library"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Get user's panels
        query = SavedPanel.query.filter_by(owner_id=current_user.id)
        
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
                    'tags': []  # Add tags support later
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
        total_query = SavedPanel.query.filter_by(owner_id=current_user.id)
        
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
        return jsonify({'error': 'Failed to get panels'}), 500

def create_or_update_panel(request):
    """Create a new panel or update an existing panel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Check if this is an update (panel_id provided) or create (no panel_id)
        panel_id = data.get('panel_id') or data.get('id')
        
        # Validate required fields for new panels
        if not panel_id:
            if not data.get('name'):
                return jsonify({'error': 'Panel name is required'}), 400
            if not data.get('genes') and not data.get('gene_list'):
                return jsonify({'error': 'Gene list is required'}), 400
        
        # Parse and validate enum values
        try:
            status = PanelStatus(data.get('status', 'ACTIVE'))
        except ValueError:
            status = PanelStatus.ACTIVE
        
        try:
            visibility = PanelVisibility(data.get('visibility', 'PRIVATE'))
        except ValueError:
            visibility = PanelVisibility.PRIVATE
        
        if panel_id:
            # Update existing panel
            panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).first()
            if not panel:
                return jsonify({'error': 'Panel not found or access denied'}), 404
            
            # Update fields if provided
            if 'name' in data:
                panel.name = data['name'][:255]  # Ensure within limits
            if 'description' in data:
                panel.description = data['description']
            if 'tags' in data:
                panel.tags = data['tags'][:500] if data['tags'] else None
            if 'status' in data:
                panel.status = status
            if 'visibility' in data:
                panel.visibility = visibility
            
            panel.updated_at = datetime.datetime.now()
            
            # Create audit entry
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Panel updated: {panel.name}",
                user_id=current_user.id,
                details={"panel_id": panel.id, "updated_fields": list(data.keys())}
            )
            
        else:
            # Create new panel
            panel = SavedPanel(
                name=data['name'][:255],
                description=data.get('description', '')[:1000] if data.get('description') else None,
                tags=data.get('tags', '')[:500] if data.get('tags') else None,
                owner_id=current_user.id,
                status=status,
                visibility=visibility,
                source_type=data.get('source_type', 'manual'),
                source_reference=data.get('source_reference', ''),
                gene_count=0,  # Will be updated after genes are added
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                last_accessed_at=datetime.datetime.now()
            )
            
            db.session.add(panel)
            db.session.flush()  # Get the panel ID
            
            # Create audit entry
            AuditService.log_action(
                action_type=AuditActionType.PANEL_CREATE,
                action_description=f"Panel created: {panel.name}",
                user_id=current_user.id,
                details={"panel_id": panel.id, "name": panel.name, "source_type": panel.source_type}
            )
        
        # Handle gene updates if provided
        genes_data = data.get('genes') or data.get('gene_list')
        if genes_data:
            # Clear existing genes if updating
            if panel_id:
                PanelGene.query.filter_by(panel_id=panel.id).delete()
            
            # Add genes
            gene_count = 0
            added_gene_symbols = set()  # Track added genes to prevent duplicates
            
            if isinstance(genes_data, list):
                for gene_data in genes_data:
                    if isinstance(gene_data, dict):
                        gene_symbol = gene_data.get('gene_symbol', '').strip()
                        if gene_symbol and gene_symbol not in added_gene_symbols:  # Check for empty and duplicates
                            gene = PanelGene(
                                panel_id=panel.id,
                                gene_symbol=gene_symbol,
                                ensembl_id=gene_data.get('ensembl_id', ''),
                                gene_name=gene_data.get('gene_name', ''),
                                confidence_level=gene_data.get('confidence_level', 'Unknown'),
                                mode_of_inheritance=gene_data.get('mode_of_inheritance', ''),
                                phenotype=gene_data.get('phenotype', '')
                            )
                            db.session.add(gene)
                            added_gene_symbols.add(gene_symbol)
                            gene_count += 1
                    elif isinstance(gene_data, str):
                        # Simple gene symbol
                        gene_symbol = gene_data.strip()
                        if gene_symbol and gene_symbol not in added_gene_symbols:  # Check for empty and duplicates
                            gene = PanelGene(
                                panel_id=panel.id,
                                gene_symbol=gene_symbol
                            )
                            db.session.add(gene)
                            added_gene_symbols.add(gene_symbol)
                            gene_count += 1
            elif isinstance(genes_data, str):
                # Parse comma-separated or newline-separated genes
                gene_symbols = [g.strip() for g in genes_data.replace('\n', ',').split(',') if g.strip()]
                for symbol in gene_symbols:
                    if symbol and symbol not in added_gene_symbols:  # Check for empty and duplicates
                        gene = PanelGene(
                            panel_id=panel.id,
                            gene_symbol=symbol
                        )
                        db.session.add(gene)
                        added_gene_symbols.add(symbol)
                        gene_count += 1
            
            # Update gene count
            panel.gene_count = gene_count
        
        # Commit all changes
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit panel changes: {e}")
            return jsonify({'error': 'Failed to save panel due to database constraint violation. Please check for duplicate genes.'}), 400
        
        # Return updated panel data
        response_data = {
            'id': panel.id,
            'name': panel.name,
            'description': panel.description,
            'gene_count': panel.gene_count,
            'status': str(panel.status),
            'visibility': str(panel.visibility),
            'source_type': panel.source_type,
            'created_at': panel.created_at.isoformat(),
            'updated_at': panel.updated_at.isoformat(),
            'version_count': panel.current_version_number or 1,
            'tags': panel.tags.split(',') if panel.tags else []
        }
        
        action = 'updated' if panel_id else 'created'
        return jsonify({
            'message': f'Panel {action} successfully',
            'panel': response_data
        }), 200 if panel_id else 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating/updating panel: {e}")
        return jsonify({'error': 'Failed to save panel'}), 500

def get_panel_data(panel):
    try:
        # Get panel genes
        genes = []
        for gene in panel.genes:
            genes.append({
                'symbol': gene.gene_symbol,
                'ensembl_id': gene.ensembl_id,
                'name': gene.gene_name,
                'confidence_level': gene.confidence_level,
                'mode_of_inheritance': gene.mode_of_inheritance,
                'phenotype': gene.phenotype
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
        return jsonify({'error': 'Failed to get panel details'}), 500

def update_panel_data(panel, request):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Parse and validate enum values
        updated_fields = []
        
        if 'name' in data:
            panel.name = data['name'][:255]
            updated_fields.append('name')
        if 'description' in data:
            panel.description = data['description'][:1000] if data['description'] else None
            updated_fields.append('description')
        if 'tags' in data:
            panel.tags = data['tags'][:500] if data['tags'] else None
            updated_fields.append('tags')
        if 'status' in data:
            try:
                panel.status = PanelStatus(data['status'])
                updated_fields.append('status')
            except ValueError:
                return jsonify({'error': f'Invalid status: {data["status"]}'}), 400
        if 'visibility' in data:
            try:
                panel.visibility = PanelVisibility(data['visibility'])
                updated_fields.append('visibility')
            except ValueError:
                return jsonify({'error': f'Invalid visibility: {data["visibility"]}'}), 400
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
                            ensembl_id=gene_data.get('ensembl_id', ''),
                            gene_name=gene_data.get('name', ''),
                            confidence_level=gene_data.get('confidence_level', 'Unknown'),
                            mode_of_inheritance=gene_data.get('mode_of_inheritance', ''),
                            phenotype=gene_data.get('phenotype', '')
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
        return jsonify({'error': 'Failed to update panel'}), 500


