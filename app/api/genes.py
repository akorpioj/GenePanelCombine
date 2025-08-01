"""
Genes API endpoints
"""

from flask import request
from flask_restx import Namespace, Resource
from ..extensions import limiter
from ..main.cache_utils import get_cached_gene_suggestions
from ..main.utils import logger, get_panel_genes_data_from_api
from ..audit_service import AuditService
from .models import (
    gene_suggestion_model, gene_list_model, error_response_model
)

ns = Namespace('genes', description='Gene-related operations')

@ns.route('/suggestions')
class GeneSuggestions(Resource):
    @ns.doc('get_gene_suggestions')
    @ns.param('q', 'Search query (gene symbol or name)', required=True)
    @ns.param('limit', 'Maximum number of suggestions', type='int', default=10)
    @ns.marshal_list_with(gene_suggestion_model)
    @ns.response(200, 'Success')
    @ns.response(400, 'Missing query parameter', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @limiter.limit("30 per minute")
    def get(self):
        """Get gene suggestions for autocomplete"""
        try:
            query = request.args.get('q', '').strip()
            limit = request.args.get('limit', 10, type=int)
            
            if not query:
                ns.abort(400, "Search query 'q' is required")
            
            if len(query) < 2:
                return []
            
            # Use cached gene suggestions
            suggestions = get_cached_gene_suggestions(query, limit)
            
            # Log gene search
            AuditService.log_search(
                search_term=query,
                result_count=len(suggestions),
                search_type="gene_suggestions",
                details={
                    "query": query,
                    "limit": limit,
                    "suggestion_count": len(suggestions)
                }
            )
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting gene suggestions for '{query}': {e}")
            ns.abort(500, f"Failed to get gene suggestions: {str(e)}")

@ns.route('/<string:gene_symbol>')
class GeneDetails(Resource):
    @ns.doc('get_gene_details')
    @ns.param('source', 'API source (uk/aus)', type='string', default='uk')
    @ns.response(200, 'Success')
    @ns.response(404, 'Gene not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @limiter.limit("20 per minute")
    def get(self, gene_symbol):
        """Get detailed information about a specific gene"""
        try:
            api_source = request.args.get('source', 'uk')
            
            # Search for the gene across all panels
            gene_info = []
            
            # This is a simplified implementation - in a real system you might
            # want to have a dedicated gene lookup service
            logger.info(f"Gene lookup for {gene_symbol} not fully implemented")
            
            # Log gene lookup
            AuditService.log_view(
                resource_type="gene",
                resource_id=gene_symbol,
                description=f"Looked up gene details: {gene_symbol}",
                details={
                    "gene_symbol": gene_symbol,
                    "api_source": api_source
                }
            )
            
            return {
                'gene_symbol': gene_symbol,
                'message': 'Gene detail lookup not fully implemented',
                'api_source': api_source
            }
            
        except Exception as e:
            logger.error(f"Error getting gene details for {gene_symbol}: {e}")
            ns.abort(500, f"Failed to get gene details: {str(e)}")

@ns.route('/search')
class GeneSearch(Resource):
    @ns.doc('search_genes')
    @ns.param('q', 'Search query', required=True)
    @ns.param('source', 'API source (uk/aus)', type='string', default='both')
    @ns.param('confidence', 'Minimum confidence level (1-3)', type='int')
    @ns.response(200, 'Success')
    @ns.response(400, 'Missing query parameter', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @limiter.limit("20 per minute")
    def get(self):
        """Search for genes across all panels"""
        try:
            query = request.args.get('q', '').strip()
            api_source = request.args.get('source', 'both')
            min_confidence = request.args.get('confidence', type=int)
            
            if not query:
                ns.abort(400, "Search query 'q' is required")
            
            # This would implement a cross-panel gene search
            # For now, return a placeholder response
            
            # Log gene search
            AuditService.log_search(
                search_term=query,
                result_count=0,
                search_type="gene_search",
                details={
                    "query": query,
                    "api_source": api_source,
                    "min_confidence": min_confidence
                }
            )
            
            return {
                'genes': [],
                'total': 0,
                'query': query,
                'api_source': api_source,
                'message': 'Cross-panel gene search not fully implemented'
            }
            
        except Exception as e:
            logger.error(f"Error searching genes for '{query}': {e}")
            ns.abort(500, f"Failed to search genes: {str(e)}")
