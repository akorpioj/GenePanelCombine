"""
Routes for the LitReview blueprint
"""

import io
import csv
import re
import click
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill
from flask import render_template, request, flash, redirect, url_for, jsonify, make_response, send_file
from flask_login import login_required, current_user
from . import litreview_bp
from .pubmed_service import pubmed_service
from ..models import db, LiteratureSearch, LiteratureArticle, UserArticleAction, AuditActionType
from ..audit_service import AuditService

# Retention period: searches and article interactions older than this are eligible
# for automated deletion via the `flask litreview cleanup` CLI command / scheduled job.
_RETENTION_DAYS = 365  # 12 months


@litreview_bp.route('/', methods=['GET'])
@login_required
def index():
    """Literature Review main page"""
    # Get recent searches
    recent_searches = LiteratureSearch.query.filter_by(
        user_id=current_user.id
    ).order_by(LiteratureSearch.created_at.desc()).limit(10).all()
    
    # Log page view
    AuditService.log_view(
        resource_type='page',
        resource_id='litreview_index',
        description='Accessed LitReview page'
    )
    
    return render_template('litreview/index.html', recent_searches=recent_searches)


@litreview_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """Perform literature search"""
    if request.method == 'POST':
        search_term = request.form.get('search_term', '').strip()
        search_type = request.form.get('search_type', 'gene')
        max_results = int(request.form.get('max_results', 50))
        
        if not search_term:
            flash('Please enter a search term', 'error')
            return redirect(url_for('litreview.index'))
        
        try:
            # Perform PubMed search
            pmids, total_count = pubmed_service.search_by_gene(
                gene_name=search_term,
                max_results=max_results
            )
            
            # Fetch article details
            articles = pubmed_service.fetch_article_details(pmids)
            
            # Save search to database
            search = pubmed_service.save_search(
                user_id=current_user.id,
                search_term=search_term,
                search_type=search_type,
                results_count=len(articles),
                search_params={'max_results': max_results}
            )
            
            # Save articles
            pubmed_service.save_articles(articles, search.id)
            
            flash(f'Found {total_count} results for "{search_term}"', 'success')
            return redirect(url_for('litreview.search_results', search_id=search.id))
            
        except Exception as e:
            flash(f'Error performing search: {str(e)}', 'error')
            return redirect(url_for('litreview.index'))
    
    return render_template('litreview/search.html')


@litreview_bp.route('/results/<int:search_id>')
@login_required
def search_results(search_id):
    """Display search results"""
    search = LiteratureSearch.query.get_or_404(search_id)
    
    # Verify user owns search
    if search.user_id != current_user.id and not current_user.is_admin():
        flash('Unauthorized access', 'error')
        return redirect(url_for('litreview.index'))
    
    # Get search results with articles
    results = search.results.order_by('rank').all()
    
    # Log view
    AuditService.log_view(
        resource_type='search_results',
        resource_id=str(search_id),
        description=f'Viewed search results for "{search.search_query}"'
    )
    
    return render_template('litreview/results.html', search=search, results=results)


def _safe_filename(text):
    """Strip characters that are unsafe in filenames."""
    return re.sub(r'[^\w\-]', '_', text)


@litreview_bp.route('/results/<int:search_id>/export/csv')
@login_required
def export_csv(search_id):
    """Download search results as CSV"""
    search = LiteratureSearch.query.get_or_404(search_id)
    if search.user_id != current_user.id and not current_user.is_admin():
        flash('Unauthorized access', 'error')
        return redirect(url_for('litreview.index'))

    results = search.results.order_by('rank').all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Rank', 'PMID', 'Title', 'Authors', 'Journal', 'Year', 'DOI', 'Abstract', 'MeSH Terms'])
    for r in results:
        a = r.article
        writer.writerow([
            r.rank,
            a.pubmed_id,
            a.title,
            '; '.join(a.authors or []),
            a.journal or '',
            a.publication_date.year if a.publication_date else '',
            a.doi or '',
            a.abstract or '',
            '; '.join(a.mesh_terms or []),
        ])

    safe_term = _safe_filename(search.search_query)
    filename = f"litreview_{safe_term}_{search.created_at.strftime('%Y%m%d')}.csv"
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response


@litreview_bp.route('/results/<int:search_id>/export/excel')
@login_required
def export_excel(search_id):
    """Download search results as Excel spreadsheet"""
    search = LiteratureSearch.query.get_or_404(search_id)
    if search.user_id != current_user.id and not current_user.is_admin():
        flash('Unauthorized access', 'error')
        return redirect(url_for('litreview.index'))

    results = search.results.order_by('rank').all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Search Results'

    headers = ['Rank', 'PMID', 'Title', 'Authors', 'Journal', 'Year', 'DOI', 'Abstract', 'MeSH Terms']
    ws.append(headers)

    # Style header row
    header_fill = PatternFill(start_color='0284C7', end_color='0284C7', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font

    # Column widths
    col_widths = [8, 12, 50, 40, 30, 8, 30, 80, 50]
    for i, width in enumerate(col_widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    for r in results:
        a = r.article
        ws.append([
            r.rank,
            a.pubmed_id,
            a.title,
            '; '.join(a.authors or []),
            a.journal or '',
            a.publication_date.year if a.publication_date else '',
            a.doi or '',
            a.abstract or '',
            '; '.join(a.mesh_terms or []),
        ])

    # Wrap text in Title and Abstract columns
    for row in ws.iter_rows(min_row=2):
        for cell in (row[2], row[7]):  # Title, Abstract
            cell.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical='top')

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    safe_term = _safe_filename(search.search_query)
    filename = f"litreview_{safe_term}_{search.created_at.strftime('%Y%m%d')}.xlsx"
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@litreview_bp.route('/article/<int:article_id>')
@login_required
def article_detail(article_id):
    """Display article details"""
    article = LiteratureArticle.query.get_or_404(article_id)
    
    # Log article view
    from ..models import UserArticleAction
    action = UserArticleAction.query.filter_by(
        user_id=current_user.id,
        article_id=article.id
    ).first()
    if action:
        action.is_viewed = True
        action.view_count = (action.view_count or 0) + 1
        action.last_viewed_at = datetime.utcnow()
    else:
        action = UserArticleAction(
            user_id=current_user.id,
            article_id=article.id,
            is_viewed=True,
            view_count=1
        )
        db.session.add(action)
    db.session.commit()
    
    AuditService.log_view(
        resource_type='article',
        resource_id=article.pubmed_id,
        description=f'Viewed article: {article.title[:100]}'
    )
    
    return render_template('litreview/article.html', article=article)


@litreview_bp.route('/api/search', methods=['POST'])
@login_required
def api_search():
    """API endpoint for literature search"""
    data = request.get_json()
    
    search_term = data.get('search_term', '').strip()
    search_type = data.get('search_type', 'gene')
    max_results = data.get('max_results', 50)
    
    if not search_term:
        return jsonify({'error': 'Search term required'}), 400
    
    try:
        # Perform search
        pmids, total_count = pubmed_service.search_by_gene(
            gene_name=search_term,
            max_results=max_results
        )
        
        # Fetch articles
        articles = pubmed_service.fetch_article_details(pmids[:max_results])
        
        # Save search
        search = pubmed_service.save_search(
            user_id=current_user.id,
            search_term=search_term,
            search_type=search_type,
            results_count=len(articles)
        )
        
        # Save articles
        saved_articles = pubmed_service.save_articles(articles, search.id)
        
        # Format response
        results = [{
        'pmid': article.pubmed_id,
            'title': article.title,
            'authors': article.authors[:3] if article.authors else [],
            'journal': article.journal,
            'publication_date': article.publication_date.isoformat() if article.publication_date else None,
            'abstract': article.abstract[:300] + '...' if article.abstract and len(article.abstract) > 300 else article.abstract,
            'url': url_for('litreview.article_detail', article_id=article.id, _external=True)
        } for article in saved_articles]
        
        return jsonify({
            'success': True,
            'search_id': search.id,
            'total_count': total_count,
            'results_count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@litreview_bp.route('/search-history')
@login_required
def search_history():
    """Display user's search history"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    searches = LiteratureSearch.query.filter_by(
        user_id=current_user.id
    ).order_by(LiteratureSearch.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('litreview/history.html', searches=searches)


# ── Self-service search history deletion ──────────────────────────────────────

@litreview_bp.route('/search/<int:search_id>/delete', methods=['POST'])
@login_required
def delete_search(search_id):
    """Delete a single search record (and its results via cascade)."""
    search = LiteratureSearch.query.get_or_404(search_id)
    if search.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('litreview.search_history'))

    query_text = search.search_query
    db.session.delete(search)
    db.session.commit()

    AuditService.log_action(
        action_type=AuditActionType.USER_DELETE,
        action_description=f'User deleted LitReview search: "{query_text}"',
        resource_type='literature_search',
        resource_id=str(search_id),
    )
    flash(f'Search "{query_text}" deleted.', 'success')
    return redirect(url_for('litreview.search_history'))


@litreview_bp.route('/search-history/clear', methods=['POST'])
@login_required
def clear_search_history():
    """Delete ALL search records for the current user."""
    count = LiteratureSearch.query.filter_by(user_id=current_user.id).count()
    LiteratureSearch.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    AuditService.log_action(
        action_type=AuditActionType.USER_DELETE,
        action_description=f'User cleared all LitReview search history ({count} record(s))',
        resource_type='literature_search',
        resource_id='all',
    )
    flash(f'Search history cleared ({count} record(s) removed).', 'success')
    return redirect(url_for('litreview.search_history'))


# ── Retention CLI command ──────────────────────────────────────────────────────

@litreview_bp.cli.command('cleanup')
@click.option('--days', default=_RETENTION_DAYS, show_default=True,
              help='Delete searches and article interactions older than this many days.')
@click.option('--dry-run', is_flag=True, default=False,
              help='Show what would be deleted without committing.')
def cleanup_old_data(days, dry_run):
    """Delete LitReview personal data older than the retention period.

    Run this command periodically (e.g. daily cron):
        flask litreview cleanup
        flask litreview cleanup --days 180
        flask litreview cleanup --dry-run
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    searches_q = LiteratureSearch.query.filter(LiteratureSearch.created_at < cutoff)
    actions_q = UserArticleAction.query.filter(
        UserArticleAction.updated_at < cutoff,
        UserArticleAction.is_saved == False,  # never delete explicitly saved articles
    )

    search_count = searches_q.count()
    action_count = actions_q.count()

    click.echo(f'Retention cutoff: {cutoff.date()} (>{days} days old)')
    click.echo(f'  LiteratureSearch records to delete : {search_count}')
    click.echo(f'  UserArticleAction records to delete: {action_count}  (unsaved only)')

    if dry_run:
        click.echo('Dry-run — no changes committed.')
        return

    searches_q.delete(synchronize_session=False)
    actions_q.delete(synchronize_session=False)
    db.session.commit()
    click.echo(f'Done. {search_count} searches and {action_count} action records deleted.')
