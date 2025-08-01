"""
Panels API endpoints
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_login import login_required, current_user
from ..extensions import limiter
from ..main.cache_utils import get_cached_all_panels, get_cached_panel_genes
from ..main.utils import logger
from ..audit_service import AuditService
from .models import (
    panel_model, panel_list_model, gene_list_model, panel_preview_model,
    error_response_model, success_response_model
)

ns = Namespace('panels', description='Panel management operations')

@ns.route('')
class PanelList(Resource):
    @ns.doc('get_panels')
    @ns.param('source', 'API source (uk/aus)', type='string', default='uk')
    @ns.marshal_with(panel_list_model)
    @ns.response(200, 'Success')
    @ns.response(500, 'Internal server error', error_response_model)
    @limiter.limit("10 per minute")
    def get(self):
        """Get list of all available panels"""
        try:
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
            
            # Log panel list access
            AuditService.log_view(
                resource_type="panel_list",
                resource_id=api_source,
                description=f"Retrieved {len(processed)} panels from {api_source} API",
                details={"panel_count": len(processed), "api_source": api_source}
            )
            
            return {
                'panels': processed,
                'total': len(processed)
            }
            
        except Exception as e:
            logger.error(f"Error getting panels: {e}")
            ns.abort(500, f"Failed to retrieve panels: {str(e)}")

@ns.route('/<int:panel_id>')
class Panel(Resource):
    @ns.doc('get_panel_details')
    @ns.param('source', 'API source (uk/aus)', type='string', default='uk')
    @ns.marshal_with(panel_preview_model)
    @ns.response(200, 'Success')
    @ns.response(404, 'Panel not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @limiter.limit("30 per minute")
    def get(self, panel_id):
        """Get detailed information about a specific panel"""
        try:
            api_source = request.args.get('source', 'uk')
            
            # Get basic panel info
            all_panels = get_cached_all_panels(api_source)
            panel_info = next((p for p in all_panels if p['id'] == panel_id), None)
            
            if not panel_info:
                ns.abort(404, f"Panel {panel_id} not found in {api_source} API")
            
            # Get gene data for this panel
            genes_data = get_cached_panel_genes(panel_id, api_source)
            gene_count = len(genes_data) if genes_data else 0
            
            # Calculate confidence statistics
            confidence_stats = {
                'green': 0,
                'amber': 0,
                'red': 0,
                'unknown': 0
            }
            
            all_genes = []
            if genes_data:
                confidence_levels = [gene.get('confidence_level', 'Unknown') for gene in genes_data]
                confidence_stats = {
                    'green': confidence_levels.count('3'),
                    'amber': confidence_levels.count('2'), 
                    'red': confidence_levels.count('1'),
                    'unknown': confidence_levels.count('Unknown') + confidence_levels.count('')
                }
                
                # Get all genes with their details
                all_genes = [
                    {
                        'gene_symbol': gene.get('gene_symbol', 'Unknown'),
                        'confidence_level': gene.get('confidence_level', 'Unknown'),
                        'mode_of_inheritance': gene.get('mode_of_inheritance', 'N/A'),
                        'phenotype': gene.get('phenotype', 'N/A')[:100] + ('...' if len(gene.get('phenotype', '')) > 100 else ''),
                        'entity_name': gene.get('entity_name', ''),
                        'entity_type': gene.get('entity_type', '')
                    }
                    for gene in genes_data
                    if gene.get('gene_symbol') and gene.get('gene_symbol') != 'Unknown'
                ]
                
                # Sort genes by confidence level then alphabetically
                confidence_order = {'3': 0, '2': 1, '1': 2, 'Unknown': 3, '': 3}
                all_genes.sort(key=lambda x: (confidence_order.get(x['confidence_level'], 3), x['gene_symbol'].upper()))
            
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
            
            # Log panel view
            AuditService.log_view(
                resource_type="panel",
                resource_id=str(panel_id),
                description=f"Viewed panel details: {panel_info['name']}",
                details={
                    "panel_id": panel_id,
                    "panel_name": panel_info['name'],
                    "api_source": api_source,
                    "gene_count": gene_count
                }
            )
            
            return preview_data
            
        except Exception as e:
            logger.error(f"Error getting panel preview for {panel_id}: {e}")
            ns.abort(500, f"Failed to get panel preview: {str(e)}")

@ns.route('/<int:panel_id>/genes')
class PanelGenes(Resource):
    @ns.doc('get_panel_genes')
    @ns.param('source', 'API source (uk/aus)', type='string', default='uk')
    @ns.marshal_with(gene_list_model)
    @ns.response(200, 'Success')
    @ns.response(404, 'Panel not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @limiter.limit("20 per minute")
    def get(self, panel_id):
        """Get all genes for a specific panel"""
        try:
            api_source = request.args.get('source', 'uk')
            
            # Get basic panel info
            all_panels = get_cached_all_panels(api_source)
            panel_info = next((p for p in all_panels if p['id'] == panel_id), None)
            
            if not panel_info:
                ns.abort(404, f"Panel {panel_id} not found in {api_source} API")
            
            # Get gene data for this panel
            genes_data = get_cached_panel_genes(panel_id, api_source)
            
            if not genes_data:
                genes_data = []
            
            # Format gene data
            formatted_genes = [
                {
                    'gene_symbol': gene.get('gene_symbol', 'Unknown'),
                    'confidence_level': gene.get('confidence_level', 'Unknown'),
                    'mode_of_inheritance': gene.get('mode_of_inheritance', 'N/A'),
                    'phenotype': gene.get('phenotype', 'N/A'),
                    'entity_name': gene.get('entity_name', ''),
                    'entity_type': gene.get('entity_type', '')
                }
                for gene in genes_data
                if gene.get('gene_symbol') and gene.get('gene_symbol') != 'Unknown'
            ]
            
            # Log gene list access
            AuditService.log_view(
                resource_type="panel_genes",
                resource_id=str(panel_id),
                description=f"Retrieved {len(formatted_genes)} genes for panel: {panel_info['name']}",
                details={
                    "panel_id": panel_id,
                    "panel_name": panel_info['name'],
                    "api_source": api_source,
                    "gene_count": len(formatted_genes)
                }
            )
            
            return {
                'genes': formatted_genes,
                'total': len(formatted_genes),
                'panel_id': panel_id,
                'panel_name': panel_info['name']
            }
            
        except Exception as e:
            logger.error(f"Error getting genes for panel {panel_id}: {e}")
            ns.abort(500, f"Failed to get panel genes: {str(e)}")

@ns.route('/compare')
class PanelComparison(Resource):
    @ns.doc('compare_panels')
    @ns.param('panel_ids', 'Comma-separated list of panel IDs with source (e.g., "123-uk,456-aus")', required=True)
    @ns.response(200, 'Success')
    @ns.response(400, 'Invalid panel IDs', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @limiter.limit("20 per minute")
    def get(self):
        """Compare multiple panels side by side"""
        try:
            panel_ids_param = request.args.get('panel_ids', '')
            if not panel_ids_param:
                ns.abort(400, "No panel IDs provided")
            
            panel_details = []
            panel_ids = panel_ids_param.split(',')
            
            for panel_id_str in panel_ids:
                if '-' not in panel_id_str:
                    continue
                    
                panel_id, api_source = panel_id_str.strip().split('-', 1)
                
                # Get basic panel info
                all_panels = get_cached_all_panels(api_source)
                panel_info = next((p for p in all_panels if str(p['id']) == panel_id), None)
                
                if not panel_info:
                    continue
                
                # Get gene data for this panel
                try:
                    panel_genes_data = get_cached_panel_genes(int(panel_id), api_source)
                    gene_count = len(panel_genes_data) if panel_genes_data else 0
                    
                    # Get all gene names
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
                    'all_genes': gene_names,
                    'created': panel_info.get('created', 'N/A'),
                    'status': panel_info.get('status', 'N/A')
                }
                panel_details.append(panel_detail)
            
            # Log panel comparison
            if panel_details:
                panel_names = [p['name'] for p in panel_details]
                AuditService.log_view(
                    resource_type="panel",
                    resource_id=panel_ids_param,
                    description=f"Compared {len(panel_details)} panels: {', '.join(panel_names[:3])}{'...' if len(panel_names) > 3 else ''}",
                    details={
                        "panel_count": len(panel_details),
                        "panel_ids": panel_ids_param,
                        "panel_names": panel_names
                    }
                )

            return {
                'panels': panel_details,
                'total': len(panel_details),
                'comparison_id': panel_ids_param
            }
            
        except Exception as e:
            logger.error(f"Error comparing panels: {e}")
            ns.abort(500, f"Failed to compare panels: {str(e)}")
