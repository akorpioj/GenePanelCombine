from flask import Flask, render_template, request, send_file, flash
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions (similar to Streamlit version) ---

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
                    "display_name": f"{panel_data.get('name', 'N/A')} (v{panel_data.get('version', 'N/A')}, ID: {panel_data.get('id')})"
                })
            url = data.get("next")
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error (get_all_panels): {e}")
            flash(f"Error fetching panels from API: {e}", "error")
            return [] # Return empty on error
        except ValueError as e:
            logger.error(f"API Error (get_all_panels - JSON parsing): {e}")
            flash(f"Error parsing panel data from API: {e}", "error")
            return []

    if page_count == max_pages and url:
        logger.warning("Reached maximum page limit while fetching panels. List might be incomplete.")
        flash("Panel list might be incomplete due to API pagination limits.", "warning")

    sorted_panels = sorted(panels, key=lambda x: x["name"])
    get_all_panels_from_api.cache = sorted_panels # Simple in-memory cache
    logger.info(f"Fetched and cached {len(sorted_panels)} panels.")
    return sorted_panels

get_all_panels_from_api.cache = None # Initialize cache attribute


def get_panel_genes_data_from_api(panel_id):
    """
    Fetches gene details for a specific panel ID from the PanelApp API.
    """
    if not panel_id:
        return []
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
    if not panel_genes_data:
        return filtered_gene_symbols

    for gene_info in panel_genes_data:
        gene_symbol = gene_info.get("entity_name")
        confidence = int(gene_info.get("confidence_level"))

        if not gene_symbol:
            continue

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
    all_panels = get_all_panels_from_api()
    if not all_panels and not get_all_panels_from_api.cache : # If fetch failed and no cache
        flash("Could not load panel list from Genomics England PanelApp. The API might be down or an error occurred.", "danger")
    return render_template('index.html', all_panels=all_panels, max_panels=3)


@app.route('/generate_gene_list', methods=['POST'])
def generate_gene_list():
    """
    Handles form submission, processes selected panels, filters genes,
    and returns an Excel file.
    """
    final_unique_gene_set = set()
    selected_panel_configs = []
    max_panels = 3 # Should match the number of form groups in HTML

    for i in range(1, max_panels + 1):
        panel_id_str = request.form.get(f'panel_id_{i}')
        list_type = request.form.get(f'list_type_{i}')

        if panel_id_str and panel_id_str != "None" and list_type: # "None" is value for empty selection
            try:
                panel_id = int(panel_id_str)
                selected_panel_configs.append({
                    "id": panel_id,
                    "list_type": list_type,
                    "form_index": i # For logging/error messages
                })
            except ValueError:
                flash(f"Invalid panel ID received for panel slot {i}.", "error")
                continue # Skip this invalid entry

    if not selected_panel_configs:
        flash("No valid panels selected. Please select at least one panel and its list type.", "warning")
        return render_template('index.html', all_panels=get_all_panels_from_api(), max_panels=3) # Re-render form

    logger.info(f"Processing {len(selected_panel_configs)} selected panel configurations.")

    for config in selected_panel_configs:
        panel_id = config["id"]
        list_type = config["list_type"]
        
        logger.info(f"Fetching genes for panel ID {panel_id} with filter '{list_type}'")
        raw_genes_for_panel = get_panel_genes_data_from_api(panel_id)

        if raw_genes_for_panel:
            filtered_genes = filter_genes_from_panel_data(raw_genes_for_panel, list_type)
            for gene_symbol in filtered_genes:
                final_unique_gene_set.add(gene_symbol)
            logger.info(f"Panel ID {panel_id}: Added {len(filtered_genes)} genes (before overall deduplication).")
        else:
            # Flash message for this specific panel might have already been set in get_panel_genes_data_from_api
            logger.warning(f"No genes retrieved or processed for panel ID {panel_id} (filter: {list_type}).")


    if not final_unique_gene_set:
        flash("No genes found matching the selected criteria across all chosen panels.", "info")
        return render_template('index.html', all_panels=get_all_panels_from_api(), max_panels=3)

    logger.info(f"Total unique genes found: {len(final_unique_gene_set)}")
    
    # Create DataFrame and Excel file
    df = pd.DataFrame(sorted(list(final_unique_gene_set)), columns=['GeneSymbol'])
    
    excel_output = io.BytesIO()
    try:
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='FilteredGeneList')
        excel_output.seek(0) # Reset stream position
    except Exception as e:
        logger.error(f"Error generating Excel file: {e}")
        flash(f"An error occurred while generating the Excel file: {e}", "error")
        return render_template('index.html', all_panels=get_all_panels_from_api(), max_panels=3)

    flash(f"Successfully generated a list of {len(final_unique_gene_set)} unique genes.", "success")
    
    return send_file(
        excel_output,
        as_attachment=True,
        download_name='filtered_gene_list.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    # For development, using Flask's built-in server.
    # For production, use a WSGI server like Gunicorn.
    app.run(debug=True)
