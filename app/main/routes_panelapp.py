from flask import request, jsonify
from flask_login import current_user, login_required
from app.extensions import limiter, cache
from . import main_bp # Import the Blueprint object defined in __init__.py
from .utils import logger
from .cache_utils import (
    get_cached_all_panels, get_cached_panel_genes, get_cached_gene_suggestions,
    get_cached_combined_panels, clear_panel_cache, get_cache_stats
)
from ..audit_service import AuditService
from sqlalchemy import desc

@main_bp.route("/api/panels")
@limiter.limit("10 per minute")
def api_panels():
    logger.info("api_panels")
    api_source = request.args.get('source', 'uk')
    
    # Use cached function for better performance
    all_panels_raw = get_cached_all_panels(api_source)

    # inject a display_name for the client
    processed = []
    for p in all_panels_raw:
        p2 = p.copy()
        source_emoji = "🇬🇧" if p.get('api_source') == 'uk' else "🇦🇺"
        p2["display_name"] = f"{source_emoji} {p['name']} (v{p['version']}, ID: {p['id']})"
        processed.append(p2)
    processed.sort(key=lambda x: x["display_name"])
    return jsonify(processed)

@main_bp.route("/api/genes/<entity_name>")
@limiter.limit("10 per minute")
def api_genes(entity_name):
    """
    Search for panels containing a specific gene by entity name.
    Returns a list of panels similar to /api/panels but filtered by gene.
    """
    logger.info(f"api_genes: {entity_name}")
    api_source = request.args.get('source', 'uk')
    
    try:
        # Get gene data from PanelApp API which includes associated panels
        from .utils import get_gene_panels_from_api
        gene_panels = get_gene_panels_from_api(entity_name, api_source)
        
        # Process panels similar to api_panels route
        processed = []
        for p in gene_panels:
            p2 = p.copy()
            source_emoji = "🇬🇧" if p.get('api_source') == 'uk' else "🇦🇺"
            p2["display_name"] = f"{source_emoji} {p['name']} (v{p['version']}, ID: {p['id']})"
            processed.append(p2)
        processed.sort(key=lambda x: x["display_name"])
        
        logger.info(f"Found {len(processed)} panels containing gene {entity_name}")
        return jsonify(processed)
        
    except Exception as e:
        logger.error(f"Error searching for gene {entity_name}: {e}")
        return jsonify({'error': f'Failed to search for gene {entity_name}'}), 500

@main_bp.route("/api/gene-suggestions")
@limiter.limit("30 per minute")
def api_gene_suggestions():
    """
    Provide autocomplete suggestions for gene names based on a query.
    Returns a list of gene names that match the query.
    """
    query = request.args.get('q', '').strip().upper()
    api_source = request.args.get('source', 'uk')
    limit = min(int(request.args.get('limit', 10)), 20)  # Max 20 suggestions
    
    if len(query) < 2:
        return jsonify([])
    
    try:
        # Use cached function for better performance
        suggestions = get_cached_gene_suggestions(query, api_source, limit)
        
        # Log search action (only for non-trivial searches to avoid spam)
        if len(query) >= 3:
            AuditService.log_search(query, len(suggestions))
        
        return jsonify(suggestions)
        
    except Exception as e:
        logger.error(f"Error getting gene suggestions for {query}: {e}")
        AuditService.log_error(
            error_description=f"Gene suggestions API error for query: {query}",
            error_message=str(e),
            resource_type="search",
            resource_id=query
        )
        return jsonify([])

@main_bp.route("/api/panel-details")
@limiter.limit("20 per minute")
def api_panel_details():
    """
    API endpoint to get detailed information about multiple panels for comparison.
    Expects panel_ids as comma-separated list like "123-uk,456-aus"
    """
    panel_ids_param = request.args.get('panel_ids', '')
    if not panel_ids_param:
        return jsonify({"error": "No panel IDs provided"}), 400
    
    try:
        panel_details = []
        panel_ids = panel_ids_param.split(',')
        
        for panel_id_str in panel_ids:
            if '-' not in panel_id_str:
                continue
                
            panel_id, api_source = panel_id_str.strip().split('-', 1)
            
            # Get basic panel info - use cached version
            all_panels = get_cached_all_panels(api_source)
            panel_info = next((p for p in all_panels if str(p['id']) == panel_id), None)
            
            if not panel_info:
                continue
                
            # Get gene data for this panel - use cached version
            try:
                panel_genes_data = get_cached_panel_genes(int(panel_id), api_source)
                gene_count = len(panel_genes_data) if panel_genes_data else 0
                
                # Get all gene names (not just a sample)
                gene_names = []
                if panel_genes_data:
                    gene_names = [gene.get('gene_symbol', 'Unknown') 
                                for gene in panel_genes_data]
                    # Remove any 'Unknown' entries and sort
                    gene_names = sorted([name for name in gene_names if name != 'Unknown'])
                    
            except Exception as e:
                logger.error(f"Error getting genes for panel {panel_id}: {e}")
                gene_count = 0
                gene_names = []
            
            # Compile panel details
            source_emoji = "🇬🇧" if api_source == 'uk' else "🇦🇺"
            panel_detail = {
                'id': panel_info['id'],
                'api_source': api_source,
                'name': panel_info['name'],
                'display_name': f"{source_emoji} {panel_info['name']}",
                'version': panel_info.get('version', 'N/A'),
                'description': panel_info.get('description', 'No description available'),
                'disease_group': panel_info.get('disease_group', 'N/A'),
                'disease_sub_group': panel_info.get('disease_sub_group', 'N/A'),
                'gene_count': gene_count,
                'all_genes': gene_names,  # Changed from sample_genes to all_genes
                'created': panel_info.get('created', 'N/A'),
                'status': panel_info.get('status', 'N/A')
            }
            panel_details.append(panel_detail)
        
        # Log panel view action
        if panel_details:
            panel_names = [p['name'] for p in panel_details]
            AuditService.log_view(
                resource_type="panel",
                resource_id=panel_ids_param,
                description=f"Viewed details for {len(panel_details)} panels: {', '.join(panel_names[:3])}{'...' if len(panel_names) > 3 else ''}",
                details={
                    "panel_count": len(panel_details),
                    "panel_ids": panel_ids_param,
                    "panel_names": panel_names
                }
            )

        return jsonify(panel_details)    
    except Exception as e:
        logger.error(f"Error getting panel details: {e}")
        return jsonify({"error": "Failed to get panel details"}), 500

@main_bp.route('/api/panel-preview/<int:panel_id>')
@limiter.limit("30 per minute")
def api_panel_preview(panel_id):
    """
    Get quick panel preview with gene count and summary information
    without full gene data loading - optimized for fast response
    """
    api_source = request.args.get('source', 'uk')
    
    try:
        # First, get basic panel info from cached panels list
        all_panels = get_cached_all_panels(api_source)
        panel_info = next((p for p in all_panels if p['id'] == panel_id), None)
        
        if not panel_info:
            return jsonify({"error": "Panel not found"}), 404
        
        # Get cached gene data for count and basic stats
        genes_data = get_cached_panel_genes(panel_id, api_source)
        
        # Calculate summary statistics
        gene_count = len(genes_data) if genes_data else 0
        
        # Analyze gene confidence levels if data is available
        confidence_stats = {}
        all_genes = []
        
        if genes_data:
            # Count confidence levels
            confidence_levels = [gene.get('confidence_level', 'Unknown') for gene in genes_data]
            confidence_stats = {
                'green': confidence_levels.count('3'),
                'amber': confidence_levels.count('2'), 
                'red': confidence_levels.count('1'),
                'unknown': confidence_levels.count('Unknown') + confidence_levels.count('')
            }
            
            # Get all genes with their details
            all_genes = []
            for gene in genes_data:
                if gene.get('gene_symbol') and gene.get('gene_symbol') != 'Unknown':
                    phenotypes = gene.get('phenotypes', [])
                    if isinstance(phenotypes, list) and phenotypes and len(phenotypes) > 0:
                        phenotype_str = ', '.join(phenotypes)
                    else:
                        phenotype_str = gene.get('phenotype', 'N/A')
                    all_genes.append({
                        'symbol': gene.get('gene_symbol', 'Unknown'),
                        'confidence': gene.get('confidence_level', 'Unknown'),
                        'moi': gene.get('mode_of_inheritance', 'N/A'),
                        'phenotype': phenotype_str
                    })
            
            # Sort genes by confidence level (3=green, 2=amber, 1=red) then alphabetically
            confidence_order = {'3': 0, '2': 1, '1': 2, 'Unknown': 3, '': 3}
            all_genes.sort(key=lambda x: (confidence_order.get(x['confidence'], 3), x['symbol'].upper()))
        
        # Format source display
        source_emoji = "🇬🇧" if api_source == 'uk' else "🇦🇺"
        source_name = "PanelApp UK" if api_source == 'uk' else "PanelApp Australia"
        
        preview_data = {
            'id': panel_info['id'],
            'api_source': api_source,
            'name': panel_info['name'],
            'display_name': f"{source_emoji} {panel_info['name']}",
            'version': panel_info.get('version', 'N/A'),
            'description': panel_info.get('description', 'No description available')[:200] + ('...' if len(panel_info.get('description', '')) > 200 else ''),
            'disease_group': panel_info.get('disease_group', 'N/A'),
            'disease_sub_group': panel_info.get('disease_sub_group', 'N/A'),
            'source_name': source_name,
            'gene_count': gene_count,
            'confidence_stats': confidence_stats,
            'all_genes': all_genes,
            'has_detailed_data': gene_count > 0
        }
        
        return jsonify(preview_data)
        
    except Exception as e:
        logger.error(f"Error getting panel preview for {panel_id}: {e}")
        return jsonify({"error": "Failed to get panel preview"}), 500
