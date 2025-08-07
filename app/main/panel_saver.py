"""
Helper functions for automatically saving downloaded panels to user's saved panels

Audit Events Logged:
- PANEL_CREATE: Successful auto-save of panel from download
- ACCESS_DENIED: Attempt to save panel without authentication  
- PANEL_UPDATE: Bulk addition of genes to saved panel
- ERROR: Failed panel creation attempts with detailed error information

All audit events include comprehensive details about source panels, gene counts,
and the download context for security and compliance tracking.
"""
import datetime
from flask_login import current_user
from app.models import (
    db, SavedPanel, PanelVersion, PanelGene, PanelChange, 
    PanelStatus, PanelVisibility, ChangeType, AuditActionType
)
from app.audit_service import AuditService
from .utils import logger


def create_saved_panel_from_download(
    final_unique_gene_set, 
    selected_panel_configs_for_generation, 
    panel_names, 
    panel_full_gene_data, 
    search_term_from_post_form=None,
    uploaded_panels=None
):
    """
    Create a SavedPanel entry from download data
    
    Args:
        final_unique_gene_set: Set of unique gene symbols
        selected_panel_configs_for_generation: List of panel config dicts with id, list_type, api_source
        panel_names: List of panel names
        panel_full_gene_data: List of full panel gene data
        search_term_from_post_form: Optional search term used
        uploaded_panels: Optional list of user uploaded panels
    
    Returns:
        SavedPanel instance or None if user not authenticated or error
    """
    if not current_user.is_authenticated:
        # Log attempt to save panel without authentication
        AuditService.log_action(
            action_type=AuditActionType.ACCESS_DENIED,
            action_description="Attempted to auto-save panel from download without authentication",
            resource_type="saved_panel",
            success=False,
            details={
                'creation_method': 'auto_save_from_download',
                'reason': 'user_not_authenticated',
                'attempted_gene_count': len(final_unique_gene_set) if final_unique_gene_set else 0
            }
        )
        return None
    
    try:
        # Generate panel name
        panel_name = generate_panel_name(
            selected_panel_configs_for_generation, 
            panel_names, 
            search_term_from_post_form,
            uploaded_panels
        )
        
        # Generate description
        description = generate_panel_description(
            selected_panel_configs_for_generation,
            panel_names,
            search_term_from_post_form,
            uploaded_panels,
            len(final_unique_gene_set)
        )
        
        # Generate source reference
        source_reference = generate_source_reference(
            selected_panel_configs_for_generation,
            uploaded_panels
        )
        
        # Create SavedPanel
        saved_panel = SavedPanel(
            name=panel_name,
            description=description,
            owner_id=current_user.id,
            status=PanelStatus.ACTIVE,
            visibility=PanelVisibility.PRIVATE,
            gene_count=len(final_unique_gene_set),
            source_type='panelapp',
            source_reference=source_reference,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            last_accessed_at=datetime.datetime.now(),
            storage_backend='gcs'  # Default to GCS
        )
        
        db.session.add(saved_panel)
        db.session.flush()  # Get the ID
        
        # Create initial version
        version = saved_panel.create_new_version(
            user_id=current_user.id,
            comment="Initial version from panel download"
        )
        
        # Add genes to the panel
        add_genes_to_panel(
            saved_panel, 
            version,
            final_unique_gene_set,
            selected_panel_configs_for_generation,
            panel_full_gene_data,
            uploaded_panels
        )
        
        # Create change record for panel creation
        change = PanelChange(
            panel_id=saved_panel.id,
            version_id=version.id,
            change_type=ChangeType.PANEL_CREATED,
            target_type='panel',
            target_id=str(saved_panel.id),
            new_value={
                'name': panel_name,
                'gene_count': len(final_unique_gene_set),
                'source_panels': source_reference
            },
            changed_by_id=current_user.id,
            change_reason="Panel created from download"
        )
        db.session.add(change)
        
        db.session.commit()
        
        # Log successful panel creation in audit trail
        AuditService.log_action(
            action_type=AuditActionType.PANEL_CREATE,
            action_description=f"Auto-saved panel '{panel_name}' from download with {len(final_unique_gene_set)} genes",
            resource_type="saved_panel",
            resource_id=str(saved_panel.id),
            new_values={
                'panel_id': saved_panel.id,
                'panel_name': panel_name,
                'gene_count': len(final_unique_gene_set),
                'source_type': 'panelapp',
                'source_reference': source_reference,
                'visibility': 'PRIVATE'
            },
            details={
                'creation_method': 'auto_save_from_download',
                'source_panels': [{'id': config['id'], 'api_source': config['api_source'], 'list_type': config['list_type']} 
                                for config in selected_panel_configs_for_generation],
                'uploaded_panels': [{'name': name, 'gene_count': len(genes)} for name, genes in (uploaded_panels or [])],
                'search_term': search_term_from_post_form,
                'total_source_panels': len(selected_panel_configs_for_generation) + len(uploaded_panels or [])
            }
        )
        
        logger.info(f"Successfully created saved panel '{panel_name}' with {len(final_unique_gene_set)} genes for user {current_user.username}")
        
        return saved_panel
        
    except Exception as e:
        db.session.rollback()
        
        # Log failed panel creation in audit trail
        error_details = {
            'creation_method': 'auto_save_from_download',
            'attempted_gene_count': len(final_unique_gene_set),
            'source_panels_count': len(selected_panel_configs_for_generation),
            'uploaded_panels_count': len(uploaded_panels or []),
            'search_term': search_term_from_post_form,
            'error_type': type(e).__name__
        }
        
        AuditService.log_action(
            action_type=AuditActionType.ERROR,
            action_description=f"Failed to auto-save panel from download: {str(e)}",
            resource_type="saved_panel",
            success=False,
            error_message=str(e),
            details=error_details
        )
        
        logger.error(f"Error creating saved panel from download: {e}")
        return None


def generate_panel_name(selected_panel_configs, panel_names, search_term, uploaded_panels):
    """Generate a descriptive name for the saved panel"""
    if search_term:
        # Use search term as primary name component
        clean_search = search_term.strip().replace(',', ' ').replace(';', ' ')
        base_name = f"Search: {clean_search}"
    elif len(selected_panel_configs) == 1:
        # Single panel - use its name
        panel_name = panel_names[0] if panel_names else f"Panel {selected_panel_configs[0]['id']}"
        base_name = f"Downloaded: {panel_name}"
    elif len(selected_panel_configs) > 1:
        # Multiple panels - create combined name
        base_name = f"Combined: {len(selected_panel_configs)} panels"
    elif uploaded_panels:
        # Only user uploaded panels
        if len(uploaded_panels) == 1:
            base_name = f"User Panel: {uploaded_panels[0][0]}"
        else:
            base_name = f"Combined: {len(uploaded_panels)} user panels"
    else:
        # Fallback
        base_name = "Downloaded Panel"
    
    # Add timestamp for uniqueness
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"{base_name} ({timestamp})"


def generate_panel_description(selected_panel_configs, panel_names, search_term, uploaded_panels, gene_count):
    """Generate a detailed description for the saved panel"""
    parts = []
    
    if search_term:
        parts.append(f"Panel generated from search term: '{search_term}'")
    
    if selected_panel_configs:
        parts.append(f"Source panels ({len(selected_panel_configs)}):")
        for i, (config, panel_name) in enumerate(zip(selected_panel_configs, panel_names)):
            api_source = config['api_source']
            list_type = config['list_type']
            source_name = "UK" if api_source == "uk" else "Australia"
            parts.append(f"  - {panel_name} ({source_name}, {list_type} genes)")
    
    if uploaded_panels:
        parts.append(f"User uploaded panels ({len(uploaded_panels)}):")
        for sheet_name, genes in uploaded_panels:
            parts.append(f"  - {sheet_name} ({len(genes)} genes)")
    
    parts.append(f"Total unique genes: {gene_count}")
    parts.append(f"Downloaded on: {datetime.datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")
    
    return "\n".join(parts)


def generate_source_reference(selected_panel_configs, uploaded_panels):
    """Generate source_reference string with comma-separated panel IDs"""
    sources = []
    
    # Add PanelApp source panels
    for config in selected_panel_configs:
        api_source = config['api_source']
        panel_id = config['id']
        sources.append(f"{api_source}-{panel_id}")
    
    # Add user uploaded panels (use file name as reference)
    for sheet_name, _ in uploaded_panels or []:
        sources.append(f"user-{sheet_name}")
    
    return ", ".join(sources)


def add_genes_to_panel(saved_panel, version, final_unique_gene_set, selected_panel_configs, panel_full_gene_data, uploaded_panels):
    """Add genes to the saved panel with source information"""
    
    # Create mapping from gene symbol to source panel info
    gene_source_map = {}
    
    # Process PanelApp source panels
    for config, panel_genes in zip(selected_panel_configs, panel_full_gene_data):
        if not panel_genes:
            continue
            
        # Filter genes based on list type
        from app.main.utils import filter_genes_from_panel_data
        filtered_genes = filter_genes_from_panel_data(panel_genes, config["list_type"])
        
        for gene_symbol in filtered_genes:
            if gene_symbol in final_unique_gene_set:
                # Find the full gene data for this symbol
                gene_data = next((g for g in panel_genes if g.get('entity_name') == gene_symbol), {})
                
                gene_source_map[gene_symbol] = {
                    'source_panel_id': f"{config['api_source']}-{config['id']}",
                    'source_list_type': config['list_type'],
                    'gene_data': gene_data
                }
    
    # Process user uploaded panels
    for sheet_name, genes in uploaded_panels or []:
        for gene_symbol in genes:
            if gene_symbol in final_unique_gene_set and gene_symbol not in gene_source_map:
                gene_source_map[gene_symbol] = {
                    'source_panel_id': f"user-{sheet_name}",
                    'source_list_type': 'user_upload',
                    'gene_data': {}
                }
    
    # Create PanelGene entries
    genes_added = 0
    for gene_symbol in final_unique_gene_set:
        source_info = gene_source_map.get(gene_symbol, {})
        gene_data = source_info.get('gene_data', {})
        
        # Process evidence field - convert list to pipe-separated string
        evidence = gene_data.get('evidence', [])
        if isinstance(evidence, list):
            evidence_str = '|'.join(str(e) for e in evidence)
        else:
            evidence_str = str(evidence) if evidence else ''
        
        # Process phenotypes field - convert list to string
        phenotypes = gene_data.get('phenotypes', [])
        if isinstance(phenotypes, list):
            phenotypes_str = '; '.join(str(p) for p in phenotypes)
        else:
            phenotypes_str = str(phenotypes) if phenotypes else ''
        
        # Ensure all string fields are properly handled
        gene_name = gene_data.get('gene_name', '') or gene_data.get('entity_name', '')
        confidence_level = str(gene_data.get('confidence_level', '')) if gene_data.get('confidence_level') else ''
        mode_of_inheritance = str(gene_data.get('mode_of_inheritance', '')) if gene_data.get('mode_of_inheritance') else ''
        
        panel_gene = PanelGene(
            panel_id=saved_panel.id,
            gene_symbol=gene_symbol,
            gene_name=gene_name,
            confidence_level=confidence_level,
            mode_of_inheritance=mode_of_inheritance,
            phenotype=phenotypes_str,
            evidence_level=evidence_str,
            source_panel_id=source_info.get('source_panel_id', ''),
            source_list_type=source_info.get('source_list_type', ''),
            added_by_id=current_user.id,
            added_at=datetime.datetime.now()
        )
        
        db.session.add(panel_gene)
        genes_added += 1
        
        # Create change record for gene addition
        if genes_added <= 100:  # Limit change records to avoid overwhelming the DB
            change = PanelChange(
                panel_id=saved_panel.id,
                version_id=version.id,
                change_type=ChangeType.GENE_ADDED,
                target_type='gene',
                target_id=gene_symbol,
                new_value={
                    'gene_symbol': gene_symbol,
                    'source': source_info.get('source_panel_id', ''),
                    'list_type': source_info.get('source_list_type', '')
                },
                changed_by_id=current_user.id,
                change_reason="Gene added from download"
            )
            db.session.add(change)
    
    logger.info(f"Added {genes_added} genes to saved panel {saved_panel.id}")
    
    # Log gene addition summary in audit trail
    if genes_added > 0:
        AuditService.log_action(
            action_type=AuditActionType.PANEL_UPDATE,
            action_description=f"Added {genes_added} genes to auto-saved panel {saved_panel.id}",
            resource_type="saved_panel",
            resource_id=str(saved_panel.id),
            details={
                'operation': 'bulk_gene_addition',
                'genes_added_count': genes_added,
                'source_panels': list(set(source_info.get('source_panel_id', '') for source_info in 
                                        [gene_source_map.get(gene, {}) for gene in final_unique_gene_set] 
                                        if source_info.get('source_panel_id'))),
                'creation_context': 'auto_save_from_download'
            }
        )
