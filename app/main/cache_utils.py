"""
Cached utility functions for PanelMerge
High-impact caching for API calls and data processing
"""

from app.extensions import cache
from flask import current_app
import requests
from datetime import datetime, timedelta
import pytz
import logging

logger = logging.getLogger(__name__)

# API configurations
API_CONFIGS = {
    'uk': {
        'name': 'PanelApp UK',
        'url': 'https://panelapp.genomicsengland.co.uk',
        'panels_endpoint': '/api/v1/panels/',
        'genes_endpoint': '/api/v1/panels/{panel_id}/'
    },
    'aus': {
        'name': 'PanelApp Australia',
        'url': 'https://panelapp.agha.umccr.org',
        'panels_endpoint': '/api/v1/panels/',
        'genes_endpoint': '/api/v1/panels/{panel_id}/'
    }
}

def get_cache_timeout(timeout_type='default'):
    """Get cache timeout from config with fallback defaults"""
    try:
        if timeout_type == 'panel':
            return current_app.config.get('CACHE_PANEL_TIMEOUT', 1800)
        elif timeout_type == 'gene':
            return current_app.config.get('CACHE_GENE_TIMEOUT', 86400)
        else:
            return current_app.config.get('CACHE_DEFAULT_TIMEOUT', 3600)
    except RuntimeError:
        # Outside app context, use defaults
        defaults = {'panel': 1800, 'gene': 86400, 'default': 3600}
        return defaults.get(timeout_type, 3600)

@cache.memoize(timeout=1800)  # Use static timeout for decorator
def get_cached_all_panels(api_source='uk'):
    """
    Cached version of get_all_panels_from_api
    Caches for 30 minutes by default
    """
    logger.info(f"Fetching panels from {api_source} API (cache miss)")
    
    api_config = API_CONFIGS.get(api_source)
    if not api_config:
        logger.error(f"Invalid API source: {api_source}")
        return []

    panels = []
    url = f"{api_config['url']}{api_config['panels_endpoint']}"
    page_count = 0
    max_pages = 50

    while url and page_count < max_pages:
        page_count += 1
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            for panel_data in data.get("results", []):
                panels.append({
                    "id": panel_data.get("id"),
                    "name": panel_data.get("name", "N/A"),
                    "version": panel_data.get("version", "N/A"),
                    "disease_group": panel_data.get("disease_group", ""),
                    "disease_sub_group": panel_data.get("disease_sub_group", ""),
                    "description": panel_data.get("description", ""),
                    "api_source": api_source
                })
            
            url = data.get("next")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error (get_cached_all_panels): {e}")
            return []

    # Sort panels by name
    panels.sort(key=lambda x: x.get("name", "").lower())
    logger.info(f"Fetched {len(panels)} panels from {api_config['name']}")
    return panels


@cache.memoize(timeout=1800)  # Use static timeout for decorator
def get_cached_panel_genes(panel_id, api_source='uk'):
    """
    Cached version of get_panel_genes_data_from_api
    Caches individual panel gene data for 30 minutes
    """
    logger.info(f"Fetching genes for panel {panel_id} from {api_source} API (cache miss)")
    
    api_config = API_CONFIGS.get(api_source)
    if not api_config:
        logger.error(f"Invalid API source: {api_source}")
        return []

    url = f"{api_config['url']}{api_config['genes_endpoint'].format(panel_id=panel_id)}"
    
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        panel_data = response.json()
        
        genes = []
        for gene in panel_data.get("genes", []):
            genes.append({
                "gene_symbol": gene.get("gene_data", {}).get("gene_symbol", ""),
                "gene_name": gene.get("gene_data", {}).get("gene_name", ""),
                "confidence_level": gene.get("confidence_level", ""),
                "penetrance": gene.get("penetrance", ""),
                "mode_of_pathogenicity": gene.get("mode_of_pathogenicity", ""),
                "mode_of_inheritance": gene.get("mode_of_inheritance", ""),
                "panel_id": panel_id,
                "api_source": api_source
            })
        
        logger.info(f"Fetched {len(genes)} genes for panel {panel_id}")
        return genes
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API Error (get_cached_panel_genes): {e}")
        return []


@cache.memoize(timeout=86400)  # Use static timeout for decorator
def get_cached_gene_suggestions(query, api_source='uk', limit=10):
    """
    Cached gene autocomplete suggestions
    Caches for 24 hours by default
    """
    if not query or len(query) < 2:
        return []
    
    logger.info(f"Fetching gene suggestions for '{query}' from {api_source} API (cache miss)")
    
    api_config = API_CONFIGS.get(api_source)
    if not api_config:
        return []

    # Use the genes search endpoint if available
    search_url = f"{api_config['url']}/api/v1/genes/"
    
    try:
        params = {
            'search': query,
            'page_size': limit
        }
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        suggestions = []
        for gene in data.get("results", []):
            gene_symbol = gene.get("gene_symbol", "")
            gene_name = gene.get("gene_name", "")
            if gene_symbol:
                suggestions.append({
                    "symbol": gene_symbol,
                    "name": gene_name,
                    "label": f"{gene_symbol} - {gene_name}" if gene_name else gene_symbol
                })
        
        logger.info(f"Found {len(suggestions)} gene suggestions for '{query}'")
        return suggestions[:limit]
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"Gene search API error: {e}")
        return []


@cache.memoize(timeout=3600)  # Use static timeout for decorator
def get_cached_combined_panels():
    """
    Get combined panels from both UK and Australia APIs
    Cached for 1 hour by default
    """
    logger.info("Fetching combined panels from both APIs (cache miss)")
    
    uk_panels = get_cached_all_panels('uk')
    aus_panels = get_cached_all_panels('aus')
    
    # Combine and sort
    all_panels = uk_panels + aus_panels
    all_panels.sort(key=lambda x: x.get("name", "").lower())
    
    logger.info(f"Combined {len(uk_panels)} UK + {len(aus_panels)} AUS = {len(all_panels)} total panels")
    return all_panels


def clear_panel_cache():
    """
    Clear all panel-related cache entries
    Useful for forced refresh
    """
    cache.delete_memoized(get_cached_all_panels, 'uk')
    cache.delete_memoized(get_cached_all_panels, 'aus')
    cache.delete_memoized(get_cached_combined_panels)
    logger.info("Cleared panel cache")


def clear_gene_cache():
    """
    Clear gene-related cache entries
    """
    # Note: Clearing specific memoized functions with arguments is complex
    # For now, we can clear the entire cache or use cache.clear()
    logger.info("Gene cache clearing requested - consider cache.clear() for full reset")


def get_cache_stats():
    """
    Get cache statistics (if supported by the cache backend)
    """
    try:
        # Redis-specific stats
        if hasattr(cache.cache, '_read_client'):
            redis_client = cache.cache._read_client
            info = redis_client.info()
            return {
                'redis_version': info.get('redis_version'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'cache_hits': info.get('keyspace_hits', 0),
                'cache_misses': info.get('keyspace_misses', 0)
            }
    except Exception as e:
        logger.warning(f"Could not get cache stats: {e}")
    
    return {"status": "Cache stats not available"}
