from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user
import datetime
from app.extensions import limiter, cache
from . import main_bp # Import the Blueprint object defined in __init__.py
from ..models import PanelDownload, db
from .excel import generate_excel_file
from .utils import get_all_panels_from_api, get_panel_genes_data_from_api, filter_genes_from_panel_data
from .utils import list_type_options, MAX_PANELS
from .utils import logger
from .cache_utils import (
    get_cached_all_panels, get_cached_panel_genes, get_cached_gene_suggestions,
    get_cached_combined_panels, clear_panel_cache, get_cache_stats
)
from ..audit_service import AuditService
from werkzeug.utils import secure_filename
import pandas as pd

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
        for i in range(1, MAX_PANELS + 1):
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
    
    return generate_excel_file(final_unique_gene_set, selected_panel_configs_for_generation, panel_names, panel_full_gene_data, search_term_from_post_form, uploaded_panels=uploaded_panels)

@main_bp.route('/upload_user_panel', methods=['POST'])
@limiter.limit("30 per hour")
def upload_user_panel():
    """
    Receives one or more user-uploaded gene panel files (Excel, CSV, or TSV), parses them, and stores the gene lists in the session for later use.
    Returns JSON with status and gene counts, or error message.
    """
    from flask import session
    files = request.files.getlist('user_panel_file')
    if not files or all(f.filename == '' for f in files):
        logger.error("No files uploaded in /upload_user_panel")
        return jsonify({'success': False, 'error': 'No file(s) uploaded.'}), 400
    session['uploaded_panels'] = []
    session.modified = True
    user_panels = []
    results = []
    for file in files:
        if not file or not file.filename:
            continue
        filename = secure_filename(file.filename)
        ext = filename.split('.')[-1].lower()
        try:
            if ext in ['csv', 'tsv']:
                sep = '\t' if ext == 'tsv' else ','
                df = pd.read_csv(file, sep=sep)
            elif ext in ['xls', 'xlsx']:
                df = pd.read_excel(file)
            else:
                results.append({'filename': filename, 'success': False, 'error': 'Unsupported file type.'})
                continue
            # Look for gene column with various common names (case-insensitive)
            gene_column = None
            acceptable_columns = ['gene', 'genes', 'entity_name', 'genesymbol']
            for col in df.columns:
                if col.strip().lower() in acceptable_columns:
                    gene_column = col
                    break
            
            if gene_column is None:
                results.append({'filename': filename, 'success': False, 'error': 'No gene column found. Looking for: gene, genes, entity_name, or genesymbol.'})
                continue
            
            genes = [str(g).strip() for g in df[gene_column] if pd.notnull(g) and str(g).strip()]
            sheetname = filename.rsplit('.', 1)[0][:31]  # Limit sheet name to 31 characters
            if sheetname not in user_panels:
                user_panels.append({'sheet_name': sheetname, 'genes': genes})
                results.append({'filename': filename, 'success': True, 'gene_count': len(genes), 'sheet_name': filename.rsplit('.', 1)[0][:31]})
                
                # Log successful panel upload
                AuditService.log_panel_upload(filename, len(genes), success=True)
                
            else:
                logger.error(f"Duplicate panel name '{sheetname}' found in uploaded files.")
                results.append({'filename': filename, 'success': False, 'error': f'Duplicate panel name: {sheetname}'})
                
                # Log failed panel upload
                AuditService.log_panel_upload(filename, 0, success=False, error_message=f'Duplicate panel name: {sheetname}')
                
        except Exception as e:
            logger.error(f"Failed to parse uploaded panel {filename}: {e}")
            results.append({'filename': filename, 'success': False, 'error': f'Failed to parse file: {e}'})
            
            # Log failed panel upload
            AuditService.log_panel_upload(filename, 0, success=False, error_message=str(e))
    session['uploaded_panels'] = user_panels
    session.modified = True
    if any(r['success'] for r in results):
        return jsonify({'success': True, 'results': results})
    else:
        return jsonify({'success': False, 'results': results}), 400

@main_bp.route('/uploaded_user_panels', methods=['GET'])
def uploaded_user_panels():
    from flask import session
    user_panels = session.get('uploaded_panels', [])
    files = [panel.get('sheet_name', 'UserPanel') for panel in user_panels]
    return jsonify({'files': files})

@main_bp.route('/remove_user_panel', methods=['POST'])
def remove_user_panel():
    from flask import session, request
    sheet_name = request.json.get('sheet_name')
    user_panels = session.get('uploaded_panels', [])
    
    # Find the panel being removed for audit logging
    removed_panel = next((p for p in user_panels if p.get('sheet_name') == sheet_name), None)
    
    new_panels = [p for p in user_panels if p.get('sheet_name') != sheet_name]
    session['uploaded_panels'] = new_panels
    session.modified = True
    
    # Log panel deletion
    if removed_panel:
        gene_count = len(removed_panel.get('genes', []))
        AuditService.log_panel_delete(
            panel_id=sheet_name, 
            panel_name=sheet_name
        )
    
    return jsonify({'success': True, 'removed': sheet_name})


@main_bp.route('/api/cache/stats')
@limiter.limit("10 per minute")
def api_cache_stats():
    """
    Get cache statistics (for debugging/monitoring)
    """
    try:
        stats = get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({"error": "Failed to get cache stats"}), 500


@main_bp.route('/api/cache/clear')
@limiter.limit("5 per minute")
def api_cache_clear():
    """
    Clear panel cache (for admin use or debugging)
    """
    try:
        clear_panel_cache()
        
        # Log cache clear action
        AuditService.log_cache_clear("panel_cache")
        
        return jsonify({"success": True, "message": "Panel cache cleared"})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"error": "Failed to clear cache"}), 500


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
