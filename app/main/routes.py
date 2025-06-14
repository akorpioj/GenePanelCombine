from flask import render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
from app.extensions import limiter 
from . import main_bp # Import the Blueprint object defined in __init__.py
from ..models import PanelDownload, db
from .excel import generate_excel_file
from .utils import get_all_panels_from_api, get_panel_genes_data_from_api, filter_genes_from_panel_data
from .utils import list_type_options, MAX_PANELS
from .utils import logger

# --- Flask Routes ---

@main_bp.route('/')
@limiter.limit("30 per minute")
def index():
    logger.info("index")
    # No more server-side filtering
    return render_template('index.html', 
                           max_panels=MAX_PANELS,
                           list_type_options=list_type_options)

@main_bp.route("/api/panels")
@limiter.limit("10 per minute")
def api_panels():
    logger.info("api_panels")
    api_source = request.args.get('source', 'uk')
    
    # (re)fetch or cache your master list here
    all_panels_raw = get_all_panels_from_api(api_source)

    # inject a display_name for the client
    processed = []
    for p in all_panels_raw:
        p2 = p.copy()
        source_emoji = "🇬🇧" if p.get('api_source') == 'uk' else "🇦🇺"
        p2["display_name"] = f"{source_emoji} {p['name']} (v{p['version']}, ID: {p['id']})"
        processed.append(p2)
    processed.sort(key=lambda x: x["display_name"])
    return jsonify(processed)

@main_bp.route('/generate', methods=['POST'])
@limiter.limit("30 per hour")  # More strict limit for resource-intensive operation
def generate():
    """
    Handles form submission, processes selected panels, filters genes,
    and returns an Excel file.
    """
    final_unique_gene_set = set()
    selected_panel_configs_for_generation = []
    panel_full_gene_data = []  # Store full gene data for each panel
    panel_names = []           # Store panel names for sheet naming    # Values from the POST form for generating the list
    search_term_from_post_form = request.form.get('search_term_hidden', '') # Get search term if passed from main form

    for i in range(1, MAX_PANELS + 1):
        panel_id = None
        api_source = None
        panel_id_str = request.form.get(f'panel_id_{i}')
        logger.info(f"generate: {panel_id_str}")
        if panel_id_str != "None":
            panel_id, api_source = panel_id_str.split('-', 1)
        list_type = request.form.get(f'list_type_{i}')

        logger.info(f"generate: {list_type} {api_source}")
        if panel_id_str and panel_id_str != "None" and list_type: # "None" is value for empty selection
            try: 
                selected_panel_configs_for_generation.append({
                    "id": int(panel_id),
                    "list_type": list_type,
                    "form_index": i, # For logging/error messages
                    "api_source": api_source
                })
            except ValueError:
                flash(f"Invalid panel ID received for panel slot {i}.", "error")
                continue # Skip this invalid entry

    if not selected_panel_configs_for_generation:
        flash("No valid panels selected for gene list generation.", "warning")
        # Redirect back to index, trying to preserve search term and selections
        # This requires GET parameters, so we build them.
        redirect_params = {'search_term': search_term_from_post_form}
        for i in range(1, MAX_PANELS + 1):
            redirect_params[f'selected_panel_id_{i}'] = request.form.get(f'panel_id_{i}')
            redirect_params[f'selected_list_type_{i}'] = request.form.get(f'list_type_{i}')
        return redirect(url_for('main.index', **redirect_params))

    logger.info(f"Processing {len(selected_panel_configs_for_generation)} panel configurations for gene list.")    
    for idx, config in enumerate(selected_panel_configs_for_generation, 1):
        raw_genes_for_panel = get_panel_genes_data_from_api(config["id"], config["api_source"])
        panel_full_gene_data.append(raw_genes_for_panel)
        # Add GB or AUS before the panel name
        panel_prefix = "GB" if config["api_source"] == "uk" else "AUS"
        panel_name = f"{panel_prefix} Panel {idx}"
        try:
            all_panels = get_all_panels_from_api(config["api_source"])
            match = next((p for p in all_panels if p["id"] == config["id"]), None)
            if match:
                panel_name = f"{panel_prefix} {match['name']}"
        except Exception:
            pass
        panel_names.append(panel_name)
        # Filtered genes for combined list
        if raw_genes_for_panel:
            filtered_genes = filter_genes_from_panel_data(raw_genes_for_panel, config["list_type"])
            for gene_symbol in filtered_genes:
                final_unique_gene_set.add(gene_symbol)
            logger.info(f"Panel ID {config['id']}: Added {len(filtered_genes)} genes.")

    if not final_unique_gene_set:
        flash("No genes found for the selected criteria.", "info")
        redirect_params = {'search_term': search_term_from_post_form}
        for i in range(1, MAX_PANELS + 1):
            redirect_params[f'selected_panel_id_{i}'] = request.form.get(f'panel_id_{i}')
            redirect_params[f'selected_list_type_{i}'] = request.form.get(f'list_type_{i}')
        return redirect(url_for('main.index', **redirect_params))

    # Log the download
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip and ',' in ip:
        ip = ip.split(',')[0].strip()
        
    download = PanelDownload(
        ip_address=ip,
        download_date=datetime.utcnow(),
        panel_ids=','.join(str(config['id']) for config in selected_panel_configs_for_generation),
        list_types=','.join(config['list_type'] for config in selected_panel_configs_for_generation),
        gene_count=len(final_unique_gene_set)
    )
    
    try:
        db.session.add(download)
        db.session.commit()
    except:
        db.session.rollback()
        logger.error("Failed to log panel download")

    logger.info(f"Total unique genes for Excel: {len(final_unique_gene_set)}")
    
    return generate_excel_file(final_unique_gene_set, selected_panel_configs_for_generation, panel_names, panel_full_gene_data, search_term_from_post_form)
