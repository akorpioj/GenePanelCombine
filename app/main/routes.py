from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user, login_required
import datetime
from app.extensions import limiter, cache
from . import main_bp # Import the Blueprint object defined in __init__.py
from ..models import PanelDownload, SavedPanel, PanelVersion, PanelGene, PanelStatus, PanelVisibility, db, AuditActionType
from .excel import generate_excel_file
from .utils import filter_genes_from_panel_data
from .utils import list_type_options, MAX_PANELS
from .utils import logger
from .cache_utils import (
    get_cached_all_panels, get_cached_panel_genes, get_cached_gene_suggestions,
    get_cached_combined_panels, clear_panel_cache, get_cache_stats
)
from ..audit_service import AuditService
from werkzeug.utils import secure_filename

# --- Flask Routes ---

@main_bp.route('/')
@limiter.limit("30 per minute")
def index():
    logger.info("index")
    
    # Get active admin messages
    from ..models import AdminMessage
    admin_messages = AdminMessage.get_active_messages()
    
    # No more server-side filtering
    return render_template('index.html', 
                           max_panels=MAX_PANELS,
                           list_type_options=list_type_options,
                           admin_messages=admin_messages)

@main_bp.route('/version-history')
@limiter.limit("30 per minute")
def version_history():
    """Display the version history page."""
    return render_template('version_history.html')

@main_bp.route('/my-panels')
@login_required
@limiter.limit("30 per minute")
def panel_library():
    """Display the enhanced panel library management interface."""
    return render_template('panel_library.html')

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
    include_original_panels = request.form.get('include_original_panels') == 'on'  # Get checkbox value

    # Determine the maximum panel index from form data (dynamic panels)
    max_panel_index = 0
    for key in request.form.keys():
        if key.startswith('panel_id_'):
            try:
                panel_index = int(key.split('_')[-1])
                max_panel_index = max(max_panel_index, panel_index)
            except (ValueError, IndexError):
                continue
    
    # Fallback to MAX_PANELS if no dynamic panels found
    if max_panel_index == 0:
        max_panel_index = MAX_PANELS

    for i in range(1, max_panel_index + 1):
        panel_id = None
        api_source = None
        panel_id_str = request.form.get(f'panel_id_{i}')
        list_type = request.form.get(f'list_type_{i}')
        logger.info(f"generate: slot {i}: panel_id_str={panel_id_str}, list_type={list_type}")
        
        # Only split if we have a valid panel_id_str that's not "None"
        if panel_id_str and panel_id_str != "None" and '-' in panel_id_str:
            try:
                panel_id, api_source = panel_id_str.split('-', 1)
                logger.info(f"generate: slot {i}: parsed panel_id={panel_id}, api_source={api_source}")
            except ValueError:
                logger.error(f"Invalid panel_id_str format: {panel_id_str}")
                continue
        
        if panel_id_str and panel_id_str != "None" and list_type and panel_id and api_source: # "None" is value for empty selection
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
        for i in range(1, max_panel_index + 1):
            redirect_params[f'selected_panel_id_{i}'] = request.form.get(f'panel_id_{i}')
            redirect_params[f'selected_list_type_{i}'] = request.form.get(f'list_type_{i}')
        return redirect(url_for('main.index', **redirect_params))

    logger.info(f"Processing {len(selected_panel_configs_for_generation)} panel configurations for gene list.")    

    # Handle user-uploaded panels stored in session (from /upload_user_panel)
    from flask import session
    uploaded_panels = []
    user_panels = session.get('uploaded_panels', set())
    for panel in user_panels:
        sheet_name = panel.get('sheet_name', 'UserPanel')[:31]
        genes = panel.get('genes', [])
        if genes:
            uploaded_panels.append((sheet_name, genes))
            logger.info(f"session panel '{sheet_name}' with {len(genes)} genes.")
    # Optionally clear session after use (uncomment if you want one-time use)
    # session['uploaded_panels'] = []
    # session.modified = True

    for idx, config in enumerate(selected_panel_configs_for_generation, 1):
        # Use cached version for better performance
        raw_genes_for_panel = get_cached_panel_genes(config["id"], config["api_source"])
        logger.info(f"Panel {config['id']}: got {len(raw_genes_for_panel) if raw_genes_for_panel else 0} raw genes")
        panel_full_gene_data.append(raw_genes_for_panel)
        # Add GB or AUS before the panel name
        panel_prefix = "GB" if config["api_source"] == "uk" else "AUS"
        panel_name = f"{panel_prefix} Panel {idx}"
        try:
            # Use cached version for better performance
            all_panels = get_cached_all_panels(config["api_source"])
            match = next((p for p in all_panels if p["id"] == config["id"]), None)
            if match:
                panel_name = f"{panel_prefix} {match['name']}"
        except Exception:
            pass
        panel_names.append(panel_name)
        # Filtered genes for combined list
        if raw_genes_for_panel:
            filtered_genes = filter_genes_from_panel_data(raw_genes_for_panel, config["list_type"])
            logger.info(f"Panel {config['id']}: filtered to {len(filtered_genes)} genes with list_type={config['list_type']}")
            for gene_symbol in filtered_genes:
                final_unique_gene_set.add(gene_symbol)
            logger.info(f"Panel ID {config['id']}: Added {len(filtered_genes)} genes. Total unique genes so far: {len(final_unique_gene_set)}")
        else:
            logger.warning(f"Panel {config['id']}: No raw genes data found")

    # Add genes from all uploaded panels (including session panels) to the combined list
    for sheet_name, genes in uploaded_panels:
        for gene in genes:
            final_unique_gene_set.add(gene)
    if uploaded_panels:
        logger.info(f"Added {sum(len(genes) for _, genes in uploaded_panels)} genes from uploaded panels to combined list.")

    # Add uploaded panel sheets to be included in Excel
    if not final_unique_gene_set and not uploaded_panels:
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
        user_id=current_user.id if current_user.is_authenticated else None,
        ip_address=ip,
        download_date=datetime.datetime.now(),
        panel_ids=','.join(str(config['id']) for config in selected_panel_configs_for_generation),
        list_types=','.join(config['list_type'] for config in selected_panel_configs_for_generation),
        gene_count=len(final_unique_gene_set)
    )
    
    try:
        db.session.add(download)
        db.session.commit()
        
        # Log panel download in audit trail
        panel_ids_str = ','.join(str(config['id']) for config in selected_panel_configs_for_generation)
        list_types_str = ','.join(config['list_type'] for config in selected_panel_configs_for_generation)
        AuditService.log_panel_download(
            panel_ids=panel_ids_str,
            list_types=list_types_str,
            gene_count=len(final_unique_gene_set)
        )
        
    except:
        db.session.rollback()
        logger.error("Failed to log panel download")

    logger.info(f"Total unique genes for Excel: {len(final_unique_gene_set)}")
    logger.info(f"Panel names: {panel_names}")
    logger.info(f"User panels: {uploaded_panels}")
    logger.info(f"Include original panels: {include_original_panels}")
    
    # Automatically save downloaded panel to user's saved panels if authenticated
    if current_user.is_authenticated:
        try:
            from .panel_saver import create_saved_panel_from_download
            saved_panel = create_saved_panel_from_download(
                final_unique_gene_set=final_unique_gene_set,
                selected_panel_configs_for_generation=selected_panel_configs_for_generation,
                panel_names=panel_names,
                panel_full_gene_data=panel_full_gene_data,
                search_term_from_post_form=search_term_from_post_form,
                uploaded_panels=uploaded_panels
            )
            if saved_panel:
                logger.info(f"Automatically saved downloaded panel as '{saved_panel.name}' for user {current_user.username}")
                # Store panel info in session for frontend notification
                from flask import session
                session['last_saved_panel'] = {
                    'id': saved_panel.id,
                    'name': saved_panel.name,
                    'gene_count': saved_panel.gene_count
                }
                session.modified = True
            else:
                logger.warning(f"Failed to auto-save downloaded panel for user {current_user.username}")
        except Exception as e:
            logger.error(f"Error auto-saving downloaded panel for user {current_user.username}: {e}")
    
    return generate_excel_file(final_unique_gene_set, selected_panel_configs_for_generation, panel_names, panel_full_gene_data, search_term_from_post_form, uploaded_panels=uploaded_panels, include_original_panels=include_original_panels)

@main_bp.route('/check_saved_panel_notification', methods=['GET'])
def check_saved_panel_notification():
    """
    Check if there's a saved panel notification in the session and return it
    """
    from flask import session
    if current_user.is_authenticated:
        saved_panel_info = session.pop('last_saved_panel', None)
        if saved_panel_info:
            session.modified = True
            return jsonify({
                'success': True,
                'panel': saved_panel_info
            })
    
    return jsonify({'success': False})

@main_bp.route('/api/version')
@limiter.limit("10 per minute")
def api_version():
    """API endpoint to get application version information"""
    from app.version import get_version_info
    return jsonify(get_version_info())


@main_bp.route('/version')
def version():
    """Simple version display page"""
    from app.version import get_version_info
    version_info = get_version_info()
    return render_template('main/version.html', version_info=version_info)
