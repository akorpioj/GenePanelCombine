from flask import Flask, render_template, request, send_file, flash, url_for, redirect
import os
import requests
import pandas as pd
import io
import logging
import openpyxl

app = Flask(__name__)
app.secret_key = 'your_very_secret_key'  # Important for flash messages

# --- Configuration & Constants ---
BASE_API_URL = "https://panelapp.genomicsengland.co.uk/api/v1/"
CONFIDENCE_MAPPING = {
    "Green": 3,
    "Amber": 2,
    "Red": 1,
}
# For displaying labels if needed, though not directly used in this Flask version's filtering logic
# CONFIDENCE_LABELS = {v: k for k, v in CONFIDENCE_MAPPING.items()}

MAX_PANELS_CONFIGURABLE = 3 # Define how many panel selection groups are on the form

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions ((largely unchanged, minor logging adjustments) ---

def get_all_panels_from_api():
    """
    Fetches all available panels from the PanelApp API, handling pagination.
    Returns a list of panel dictionaries, sorted by name.
    Caches results in a simple way for the duration of the app run (for a more robust cache, use Flask-Caching).
    """
    if hasattr(get_all_panels_from_api, "cache") and get_all_panels_from_api.cache:
        logger.info("Returning cached panel list.")
        return get_all_panels_from_api.cache

    panels = []
    url = f"{BASE_API_URL}panels/"
    page_count = 0
    max_pages = 50  # Safety break for pagination

    logger.info("Fetching panel list from API...")
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
                    "disease_group": panel_data.get("disease_group", ""), # Ensure empty string if None for search
                    "disease_sub_group": panel_data.get("disease_sub_group", ""), # Ensure empty string
                    "description": panel_data.get("description", ""),
                    # display_name is now constructed in the route after filtering                    
                })
            url = data.get("next")
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error (get_all_panels): {e}")
            # Do not flash here, let the route handle UI messages based on context
            #flash(f"Error fetching panels from API: {e}", "error")
            get_all_panels_from_api.cache = [] # Cache empty list on error to prevent re-fetch attempts
            return [] # Return empty on error
        except ValueError as e:
            logger.error(f"API Error (get_all_panels - JSON parsing): {e}")
            #flash(f"Error parsing panel data from API: {e}", "error")
            get_all_panels_from_api.cache = []
            return []

    if page_count == max_pages and url:
        logger.warning("Reached maximum page limit while fetching panels. List might be incomplete.")
        #flash("Panel list might be incomplete due to API pagination limits.", "warning")

    # Store in simple in-memory cache
    get_all_panels_from_api.cache = panels
    logger.info(f"Fetched and cached {len(panels)} panels.")
    return panels

get_all_panels_from_api.cache = None # Initialize cache attribute

def get_panel_genes_data_from_api(panel_id):
    """
    Fetches gene details for a specific panel ID from the PanelApp API.
    """
    if not panel_id: return []
    url = f"{BASE_API_URL}panels/{panel_id}/"
    logger.info(f"Fetching genes for panel ID: {panel_id}")
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

        if list_type_selection == "Whole gene panel":
            filtered_gene_symbols.append(gene_symbol)
        elif list_type_selection == "Green genes":
            if confidence == CONFIDENCE_MAPPING["Green"]:
                filtered_gene_symbols.append(gene_symbol)
        elif list_type_selection == "Green and Amber genes":
            if confidence == CONFIDENCE_MAPPING["Green"] or \
               confidence == CONFIDENCE_MAPPING["Amber"]:
                filtered_gene_symbols.append(gene_symbol)
        elif list_type_selection == "Amber genes":
            if confidence == CONFIDENCE_MAPPING["Amber"]:
                filtered_gene_symbols.append(gene_symbol)
        elif list_type_selection == "Red genes":
            if confidence == CONFIDENCE_MAPPING["Red"]:
                filtered_gene_symbols.append(gene_symbol)
    return filtered_gene_symbols

# --- Flask Routes ---

@app.route('/', methods=['GET'])
def index():
    """
    Renders the main page, populating panel selection dropdowns.
    """
    search_term = request.args.get('search_term', '').strip().lower()

    # Retrieve current selections for panels from query parameters
    current_selections = {}
    for i in range(1, MAX_PANELS_CONFIGURABLE + 1):
        panel_id_key = f'selected_panel_id_{i}'
        list_type_key = f'selected_list_type_{i}'
        current_selections[f'panel_id_{i}'] = request.args.get(panel_id_key)
        current_selections[f'list_type_{i}'] = request.args.get(list_type_key)

    logger.info(f"Index route. Search: '{search_term}', Current Selections: {current_selections}")

    all_panels_raw = get_all_panels_from_api()

    if not all_panels_raw and get_all_panels_from_api.cache == []: # API fetch failed
        flash("Could not load panel list from Genomics England PanelApp. The API might be down or an error occurred. Please try again later.", "danger")
        return render_template('index.html', all_panels=[], max_panels_configurable=MAX_PANELS_CONFIGURABLE, search_term=search_term, current_selections=current_selections)

    processed_panels_for_display = []
    source_list_for_filtering = all_panels_raw

    if search_term:
        logger.info(f"Filtering panels with search term: '{search_term}'")
        filtered_list = []
        for panel in source_list_for_filtering:
            # Check search term against relevant fields
            if (search_term in panel.get('name', '').lower() or
                search_term in panel.get('disease_group', '').lower() or
                search_term in panel.get('disease_sub_group', '').lower() or
                search_term in panel.get('description', '').lower()):
                filtered_list.append(panel)

        if not filtered_list:
            flash(f"No panels found matching '{request.args.get('search_term', '')}'. Displaying full list or previous filter state if applicable.", "info")
            # If filter yields no results, we might want to show all panels.
            # Or, if current_selections are present, it implies user was working with a list,
            # so perhaps we should preserve the list that allowed those selections.
            # For now, if search yields nothing, the dropdowns will be based on all_panels_raw.
            # This means selected IDs might not appear if they are filtered out.
            source_list_for_display = all_panels_raw # Fallback to all if filter is empty
        else:
            source_list_for_display = filtered_list or all_panels_raw
    else:
        source_list_for_display = all_panels_raw

    # ──────────── preserve any already‐selected panels ────────────
    # current_selections['panel_id_i'] holds the string ID if slot i was set
    for i in range(1, MAX_PANELS_CONFIGURABLE + 1):
        sel = current_selections.get(f'panel_id_{i}')
        if sel and sel != 'None':
            # find the full panel dict in the unfiltered master list
            extra = next((p for p in all_panels_raw if str(p['id']) == sel), None)
            if extra and extra not in source_list_for_display:
                source_list_for_display.append(extra)
    # ───────────────────────────────────────────────────────────────

    # Construct display_name for all panels that will be shown in dropdowns
    for panel in source_list_for_display:
        panel_copy = panel.copy() # Avoid modifying cached items
        panel_copy['display_name'] = f"{panel.get('name', 'N/A')} (v{panel.get('version', 'N/A')}, ID: {panel.get('id')})"
        processed_panels_for_display.append(panel_copy)
    
    if processed_panels_for_display: # Sort if list is not empty
      sorted_display_panels = sorted(processed_panels_for_display, key=lambda x: x.get('display_name', ''))
    else:
      sorted_display_panels = []

    return render_template('index.html', 
                           all_panels=sorted_display_panels, 
                           max_panels_configurable=MAX_PANELS_CONFIGURABLE, 
                           search_term=search_term, 
                           current_selections=current_selections)

@app.route('/generate_gene_list', methods=['POST'])
def generate_gene_list():
    """
    Handles form submission, processes selected panels, filters genes,
    and returns an Excel file.
    """
    final_unique_gene_set = set()
    selected_panel_configs_for_generation = []

    # Values from the POST form for generating the list
    search_term_from_post_form = request.form.get('search_term_hidden', '') # Get search term if passed from main form

    for i in range(1, MAX_PANELS_CONFIGURABLE + 1):
        panel_id_str = request.form.get(f'main_panel_id_{i}') # Names from the main form
        list_type = request.form.get(f'main_list_type_{i}')

        if panel_id_str and panel_id_str != "None" and list_type: # "None" is value for empty selection
            try:
                panel_id = int(panel_id_str)
                selected_panel_configs_for_generation.append({
                    "id": panel_id,
                    "list_type": list_type,
                    "form_index": i # For logging/error messages
                })
            except ValueError:
                flash(f"Invalid panel ID received for panel slot {i}.", "error")
                continue # Skip this invalid entry

    if not selected_panel_configs_for_generation:
        flash("No valid panels selected for gene list generation.", "warning")
        # Redirect back to index, trying to preserve search term and selections
        # This requires GET parameters, so we build them.
        redirect_params = {'search_term': search_term_from_post_form}
        for i in range(1, MAX_PANELS_CONFIGURABLE + 1):
            redirect_params[f'selected_panel_id_{i}'] = request.form.get(f'main_panel_id_{i}')
            redirect_params[f'selected_list_type_{i}'] = request.form.get(f'main_list_type_{i}')
        return redirect(url_for('index', **redirect_params))

    logger.info(f"Processing {len(selected_panel_configs_for_generation)} panel configurations for gene list.")

    for config in selected_panel_configs_for_generation:
        raw_genes_for_panel = get_panel_genes_data_from_api(config["id"])
        if raw_genes_for_panel:
            filtered_genes = filter_genes_from_panel_data(raw_genes_for_panel, config["list_type"])
            for gene_symbol in filtered_genes: final_unique_gene_set.add(gene_symbol)
            logger.info(f"Panel ID {config['id']}: Added {len(filtered_genes)} genes.")

    if not final_unique_gene_set:
        flash("No genes found for the selected criteria.", "info")
        redirect_params = {'search_term': search_term_from_post_form}
        for i in range(1, MAX_PANELS_CONFIGURABLE + 1):
            redirect_params[f'selected_panel_id_{i}'] = request.form.get(f'main_panel_id_{i}')
            redirect_params[f'selected_list_type_{i}'] = request.form.get(f'main_list_type_{i}')
        return redirect(url_for('index', **redirect_params))

    logger.info(f"Total unique genes for Excel: {len(final_unique_gene_set)}")
    
    # Create DataFrame and Excel file
    df = pd.DataFrame(sorted(list(final_unique_gene_set)), columns=['GeneSymbol'])
    excel_output = io.BytesIO()
    try:
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='FilteredGeneList')
        excel_output.seek(0) # Reset stream position
    except Exception as e:
        logger.error(f"Error generating Excel: {e}")
        flash(f"Error generating Excel file: {e}", "error")
        redirect_params = {'search_term': search_term_from_post_form}
        for i in range(1, MAX_PANELS_CONFIGURABLE + 1):
            redirect_params[f'selected_panel_id_{i}'] = request.form.get(f'main_panel_id_{i}')
            redirect_params[f'selected_list_type_{i}'] = request.form.get(f'main_list_type_{i}')
        return redirect(url_for('index', **redirect_params))

    # Flashing success message before sending file can be tricky as it might not be displayed
    # if the browser immediately starts a download.
    # Consider a separate download page or JavaScript for better UX if this is an issue.
    # For now, the browser will just download the file.
    #flash(f"Successfully generated a list of {len(final_unique_gene_set)} unique genes.", "success")
    
    return send_file(
        excel_output,
        as_attachment=True,
        download_name='filtered_gene_list.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    # For development, using Flask's built-in server.
    # For production, use a WSGI server like Gunicorn.
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
