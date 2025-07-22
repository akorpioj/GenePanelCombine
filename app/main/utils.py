import requests
import logging
import pytz
from datetime import datetime, timedelta
from flask import flash
from flask import redirect, url_for
from . import main_bp  # Import the Blueprint object defined in __init__.py
from app.extensions import limiter  # Import the limiter instance if needed
# from flask import current_app  # Import current_app if you need to access app context

# --- Configuration & Constants ---
UK_API_URL = "https://panelapp.genomicsengland.co.uk/api/v1/"
AUS_API_URL = "https://panelapp-aus.org/api/v1/"
BASE_API_URL = UK_API_URL  # Keep for backward compatibility

API_CONFIGS = {
    'uk': {
        'name': 'UK PanelApp',
        'url': UK_API_URL,
        'panels_endpoint': 'panels/'
    },
    'aus': {
        'name': 'Australian PanelApp',
        'url': AUS_API_URL,
        'panels_endpoint': 'panels/'
    }
}

CONFIDENCE_MAPPING = {
    "Green": 3,
    "Amber": 2,
    "Red": 1,
}
# For displaying labels if needed, though not directly used in this Flask version's filtering logic
# CONFIDENCE_LABELS = {v: k for k, v in CONFIDENCE_MAPPING.items()}
LIST_TYPE_GREEN = "Green genes"
LIST_TYPE_GREEN_AND_AMBER = "Green and Amber genes"
LIST_TYPE_AMBER = "Amber genes"
LIST_TYPE_RED = "Red genes"
LIST_TYPE_ALL = "Whole gene panel"
list_type_options = [LIST_TYPE_ALL, LIST_TYPE_GREEN, LIST_TYPE_GREEN_AND_AMBER, LIST_TYPE_AMBER, LIST_TYPE_RED]
GENE_FILTER = { LIST_TYPE_ALL: [1,2,3],
                LIST_TYPE_GREEN: [3],
                LIST_TYPE_GREEN_AND_AMBER: [2,3],
                LIST_TYPE_AMBER: [2],
                LIST_TYPE_RED: [1]
                }

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Cache clear control ---
last_cache_clear_time = None
CACHE_CLEAR_INTERVAL = timedelta(hours=2)

MAX_PANELS = 5 # Define how many panel selection groups are on the form

# --- Helper Functions --- #

def get_all_panels_from_api(api_source='uk'):
    """
    Fetches all available panels from the specified PanelApp API, handling pagination.
    Args:
        api_source: Either 'uk' or 'aus' to specify which API to use
    Returns a list of panel dictionaries, sorted by name.
    """
    helsinki = pytz.timezone('Europe/Helsinki')
    now = datetime.now(helsinki)

    # Use separate cache for each API
    cache_attr = f"cache_{api_source}"
    cache_time_attr = f"cache_time_{api_source}"
    next_refresh_attr = f"next_refresh_{api_source}"

    # Check if cache exists and is still valid
    cache = getattr(get_all_panels_from_api, cache_attr, None)
    cache_time = getattr(get_all_panels_from_api, cache_time_attr, None)
    next_refresh = getattr(get_all_panels_from_api, next_refresh_attr, None)
    
    if cache is not None and next_refresh is not None and now < next_refresh:
        logger.info(f"Returning cached panel list for {api_source}.")
        return cache    # Get API configuration
    api_config = API_CONFIGS.get(api_source)
    if not api_config:
        logger.error(f"Invalid API source: {api_source}")
        return []

    # Fetch from API
    panels = []
    url = f"{api_config['url']}{api_config['panels_endpoint']}"
    page_count = 0
    max_pages = 50  # Safety break for pagination

    logger.info(f"Fetching panel list from {api_config['name']}...")
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
                    "api_source": api_source  # Add source information
                })
            url = data.get("next")
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error (get_all_panels): {e}")
            # Do not flash here, let the route handle UI messages based on context
            #flash(f"Error fetching panels from API: {e}", "error")
            get_all_panels_from_api.cache = [] # Cache empty list on error to prevent re-fetch attempts
            get_all_panels_from_api.cache_time = now
            get_all_panels_from_api.next_refresh = now + timedelta(hours=1)
            return [] # Return empty on error
        except ValueError as e:
            logger.error(f"API Error (get_all_panels - JSON parsing): {e}")
            #flash(f"Error parsing panel data from API: {e}", "error")
            get_all_panels_from_api.cache = []
            get_all_panels_from_api.cache_time = now
            get_all_panels_from_api.next_refresh = now + timedelta(hours=1)
            return []

    if page_count == max_pages and url:
        logger.warning("Reached maximum page limit while fetching panels. List might be incomplete.")
        #flash("Panel list might be incomplete due to API pagination limits.", "warning")

    # Store in cache and set next refresh to next 7:00 Helsinki time
    # Calculate next 7:00
    next_7 = now.replace(hour=7, minute=0, second=0, microsecond=0)
    if now >= next_7:
        next_7 = next_7 + timedelta(days=1)
    get_all_panels_from_api.cache = panels
    get_all_panels_from_api.cache_time = now
    get_all_panels_from_api.next_refresh = next_7
    logger.info(f"Fetched and cached {len(panels)} panels. Next refresh at {next_7}.")
    return panels

# Initialize separate caches for each API
get_all_panels_from_api.cache_uk = None
get_all_panels_from_api.cache_time_uk = None
get_all_panels_from_api.next_refresh_uk = None
get_all_panels_from_api.cache_aus = None
get_all_panels_from_api.cache_time_aus = None
get_all_panels_from_api.next_refresh_aus = None

def get_panel_genes_data_from_api(panel_id, api_source='uk'):
    """
    Fetches gene details for a specific panel ID from the specified PanelApp API.
    """
    logger.info("get_panel_gene_from_api")
    if not panel_id: return []
    
    api_config = API_CONFIGS.get(api_source)
    if not api_config:
        logger.error(f"Invalid API source: {api_source}")
        return []
    
    url = f"{api_config['url']}panels/{panel_id}/"
    logger.info(f"Fetching genes for panel ID: {panel_id} from {api_config['name']}")
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("genes", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"API Error (get_panel_genes_data for panel {panel_id}): {e}")
        flash(f"Error fetching genes for panel ID {panel_id}: {e}", "error")
        return []
    except ValueError as e:
        logger.error(f"API Error (get_panel_genes_data for panel {panel_id} - JSON parsing): {e}")
        flash(f"Error parsing gene data for panel ID {panel_id}: {e}", "error")
        return []

def filter_genes_from_panel_data(panel_genes_data, list_type_selection):
    """
    Filters genes from a panel's gene data based on the selected list type.
    """
    filtered_gene_symbols = []
    if not panel_genes_data: return filtered_gene_symbols

    for gene_info in panel_genes_data:
        gene_symbol = gene_info.get("entity_name")
        confidence = int(gene_info.get("confidence_level"))

        if not gene_symbol: continue

        if confidence in GENE_FILTER[list_type_selection]:
            filtered_gene_symbols.append(gene_symbol)

    return filtered_gene_symbols

@main_bp.route('/clear_cache', methods=['POST'])
@limiter.limit("2 per hour")  # Limit cache clearing
def clear_cache():
    global last_cache_clear_time
    helsinki = pytz.timezone('Europe/Helsinki')
    now = datetime.now(helsinki)
    if last_cache_clear_time is not None and (now - last_cache_clear_time) < CACHE_CLEAR_INTERVAL:
        wait_time = CACHE_CLEAR_INTERVAL - (now - last_cache_clear_time)
        flash(f"Cache can only be cleared every 2 hours. Please wait {wait_time} longer.", "warning")    
    else:
        # Clear both UK and AUS caches
        get_all_panels_from_api.cache_uk = None
        get_all_panels_from_api.cache_time_uk = None
        get_all_panels_from_api.next_refresh_uk = None
        get_all_panels_from_api.cache_aus = None
        get_all_panels_from_api.cache_time_aus = None
        get_all_panels_from_api.next_refresh_aus = None
        last_cache_clear_time = now
        flash("Panel cache cleared!", "success")
    return redirect(url_for('main.index'))

