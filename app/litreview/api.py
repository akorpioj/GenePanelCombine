"""
Flask-RESTX namespace for the LitReview module.

Endpoints:
  POST /api/v1/litreview/search
  GET  /api/v1/litreview/results/<search_id>
  GET  /api/v1/litreview/article/<article_id>
"""

from flask import request
from flask_login import login_required, current_user
from flask_restx import Namespace, Resource, fields

from ..api import api
from ..models import db, LiteratureSearch, LiteratureArticle
from .pubmed_service import pubmed_service

ns = api.namespace('litreview', description='PubMed literature search')

# ---------------------------------------------------------------------------
# Shared model definitions (used both for request parsing and response docs)
# ---------------------------------------------------------------------------

article_brief = ns.model('ArticleBrief', {
    'pmid':             fields.String(description='PubMed ID'),
    'title':            fields.String(description='Article title'),
    'authors':          fields.List(fields.String, description='First 3 authors'),
    'journal':          fields.String(description='Journal name'),
    'publication_date': fields.String(description='Publication date (ISO 8601)'),
    'abstract':         fields.String(description='Abstract preview (≤ 300 chars)'),
    'url':              fields.String(description='URL to the article detail page'),
})

search_response = ns.model('SearchResponse', {
    'success':       fields.Boolean,
    'search_id':     fields.Integer(description='Saved search ID'),
    'total_count':   fields.Integer(description='Total results in PubMed'),
    'results_count': fields.Integer(description='Articles returned in this response'),
    'results':       fields.List(fields.Nested(article_brief)),
})

article_full = ns.model('ArticleFull', {
    'id':               fields.Integer,
    'pubmed_id':        fields.String(description='PubMed ID'),
    'pmc_id':           fields.String,
    'doi':              fields.String,
    'title':            fields.String,
    'abstract':         fields.String,
    'authors':          fields.List(fields.String),
    'journal':          fields.String,
    'publication_date': fields.String(description='ISO 8601 date'),
    'publication_types': fields.List(fields.String),
    'mesh_terms':       fields.List(fields.String),
    'keywords':         fields.List(fields.String),
    'gene_mentions':    fields.List(fields.String),
    'cached_at':        fields.String(description='ISO 8601 datetime'),
})

result_item = ns.model('SearchResultItem', {
    'rank':    fields.Integer,
    'article': fields.Nested(article_full),
})

results_response = ns.model('SearchResultsResponse', {
    'search_id':    fields.Integer,
    'search_query': fields.String,
    'result_count': fields.Integer,
    'created_at':   fields.String,
    'results':      fields.List(fields.Nested(result_item)),
})

search_request = ns.model('SearchRequest', {
    'search_term': fields.String(required=True,  description='Gene symbol or keyword', example='BRCA1'),
    'search_type': fields.String(required=False, description="'gene', 'keyword', or 'author'", default='gene', example='gene'),
    'max_results': fields.Integer(required=False, description='Max results (1-200)', default=50, example=50),
})

error_model = ns.model('Error', {
    'error': fields.String(description='Error message'),
})

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@ns.route('/search')
class LitReviewSearch(Resource):
    """Perform a PubMed literature search and persist the results."""

    @login_required
    @ns.expect(search_request, validate=True)
    @ns.response(200, 'OK', search_response)
    @ns.response(400, 'Bad request', error_model)
    @ns.response(401, 'Not authenticated')
    @ns.response(500, 'Internal error', error_model)
    def post(self):
        """Search PubMed and save results to the database."""
        data = request.get_json() or {}

        search_term = (data.get('search_term') or '').strip()
        search_type = data.get('search_type', 'gene')
        max_results  = int(data.get('max_results', 50))

        if not search_term:
            return {'error': 'search_term is required'}, 400
        if not (1 <= max_results <= 200):
            return {'error': 'max_results must be between 1 and 200'}, 400

        try:
            pmids, total_count = pubmed_service.search_by_gene(
                gene_name=search_term,
                max_results=max_results,
            )
            articles = pubmed_service.fetch_article_details(pmids[:max_results])
            search   = pubmed_service.save_search(
                user_id=current_user.id,
                search_term=search_term,
                search_type=search_type,
                results_count=len(articles),
            )
            saved_articles = pubmed_service.save_articles(articles, search.id)

            from flask import url_for
            results = [{
                'pmid':   a.pubmed_id,
                'title':  a.title,
                'authors': (a.authors or [])[:3],
                'journal': a.journal,
                'publication_date': a.publication_date.isoformat() if a.publication_date else None,
                'abstract': (
                    a.abstract[:300] + '...'
                    if a.abstract and len(a.abstract) > 300
                    else a.abstract
                ),
                'url': url_for('litreview.article_detail', article_id=a.id, _external=True),
            } for a in saved_articles]

            return {
                'success':       True,
                'search_id':     search.id,
                'total_count':   total_count,
                'results_count': len(results),
                'results':       results,
            }, 200

        except Exception as exc:
            return {'error': str(exc)}, 500


@ns.route('/results/<int:search_id>')
@ns.param('search_id', 'ID of a previously saved search')
class LitReviewResults(Resource):
    """Retrieve a previously saved search and its ranked article list."""

    @login_required
    @ns.response(200, 'OK', results_response)
    @ns.response(401, 'Not authenticated')
    @ns.response(403, 'Forbidden')
    @ns.response(404, 'Search not found')
    def get(self, search_id):
        """Return search metadata and all linked articles in rank order."""
        search = LiteratureSearch.query.get_or_404(search_id)

        if search.user_id != current_user.id and not current_user.is_admin():
            return {'error': 'Access denied'}, 403

        results = search.results.order_by('rank').all()
        return {
            'search_id':    search.id,
            'search_query': search.search_query,
            'result_count': search.result_count,
            'created_at':   search.created_at.isoformat(),
            'results': [{
                'rank': r.rank,
                'article': {
                    'id':               r.article.id,
                    'pubmed_id':        r.article.pubmed_id,
                    'pmc_id':           r.article.pmc_id,
                    'doi':              r.article.doi,
                    'title':            r.article.title,
                    'abstract':         r.article.abstract,
                    'authors':          r.article.authors,
                    'journal':          r.article.journal,
                    'publication_date': r.article.publication_date.isoformat() if r.article.publication_date else None,
                    'publication_types': r.article.publication_types,
                    'mesh_terms':       r.article.mesh_terms,
                    'keywords':         r.article.keywords,
                    'gene_mentions':    r.article.gene_mentions,
                    'cached_at':        r.article.cached_at.isoformat() if r.article.cached_at else None,
                },
            } for r in results],
        }, 200


@ns.route('/article/<int:article_id>')
@ns.param('article_id', 'Internal article ID')
class LitReviewArticle(Resource):
    """Retrieve full metadata for a single cached article."""

    @login_required
    @ns.response(200, 'OK', article_full)
    @ns.response(401, 'Not authenticated')
    @ns.response(404, 'Article not found')
    def get(self, article_id):
        """Return full article metadata by internal ID."""
        article = LiteratureArticle.query.get_or_404(article_id)
        return {
            'id':               article.id,
            'pubmed_id':        article.pubmed_id,
            'pmc_id':           article.pmc_id,
            'doi':              article.doi,
            'title':            article.title,
            'abstract':         article.abstract,
            'authors':          article.authors,
            'journal':          article.journal,
            'publication_date': article.publication_date.isoformat() if article.publication_date else None,
            'publication_types': article.publication_types,
            'mesh_terms':       article.mesh_terms,
            'keywords':         article.keywords,
            'gene_mentions':    article.gene_mentions,
            'cached_at':        article.cached_at.isoformat() if article.cached_at else None,
        }, 200
