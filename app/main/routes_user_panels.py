from flask import render_template, request, jsonify, flash, redirect, url_for
from app.extensions import limiter, cache
from . import main_bp # Import the Blueprint object defined in __init__.py
from .utils import logger
from ..audit_service import AuditService
from werkzeug.utils import secure_filename
import pandas as pd
from sqlalchemy import desc

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
