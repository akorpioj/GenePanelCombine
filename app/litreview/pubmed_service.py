"""
PubMed API integration service for literature search
"""

from Bio import Entrez
import os
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import xmltodict
from flask import current_app
from ..models import db, LiteratureSearch, LiteratureArticle, SearchResult
from ..audit_service import AuditService
from ..extensions import cache as flask_cache

class PubMedService:
    """Service for interacting with NCBI PubMed database"""
    
    def __init__(self):
        """Initialize PubMed service (config is read lazily on first use)"""
        self.tool_name = 'PanelMerge-LitReview'
        self._configured = False

    def _configure(self):
        """Configure Entrez credentials from app config (requires app context)"""
        if self._configured:
            return
        # Prefer app config; fall back to environment variables so the service
        # also works in CLI / testing contexts.
        try:
            email = current_app.config.get('PUBMED_EMAIL')
            api_key = current_app.config.get('PUBMED_API_KEY')
        except RuntimeError:
            email = None
            api_key = None

        self.email = email or os.environ.get('PUBMED_EMAIL', 'your.email@example.com')
        self.api_key = api_key or os.environ.get('PUBMED_API_KEY')

        Entrez.email = self.email
        Entrez.tool = self.tool_name
        if self.api_key:
            Entrez.api_key = self.api_key
        self._configured = True
    
    # Mapping from UI date-range value to number of days
    _DATE_RANGE_DAYS: Dict[str, int] = {
        '6months': 183,
        '1year':   365,
        '5years':  1825,
    }

    # PubMed publication-type filter strings for each UI article-type value
    _ARTICLE_TYPE_FILTERS: Dict[str, str] = {
        'review':          'Review[pt]',
        'clinical_trial':  'Clinical Trial[pt]',
        'meta_analysis':   'Meta-Analysis[pt]',
        'case_report':     'Case Reports[pt]',
    }

    def search_by_gene(self, gene_name: str, max_results: int = 100,
                       retstart: int = 0,
                       date_range: Optional[str] = None,
                       article_type: Optional[str] = None,
                       pub_status: Optional[str] = None,
                       language: Optional[str] = None) -> Tuple[List[str], int]:
        """
        Search PubMed for articles related to a specific gene.

        Args:
            gene_name:    Gene symbol or free-text term.
            max_results:  Maximum number of results to return.
            retstart:     Starting position for pagination.
            date_range:   One of '6months', '1year', '5years', or None (no limit).
            article_type: One of 'review', 'clinical_trial', 'meta_analysis',
                          'case_report', or None (all types).
            pub_status:   One of 'published', 'preprint', 'inpress', or None (all).
            language:     ISO-639-1 language code, e.g. 'english', or None (all).

        Returns:
            Tuple of (list of PMIDs, total count)
        """
        self._configure()

        # Layer 1: Redis cache — avoid repeat API calls for the same query
        cache_key = (
            f'pubmed_search:{gene_name.lower()}:{max_results}:{retstart}'
            f':{date_range}:{article_type}:{pub_status}:{language}'
        )
        try:
            cached = flask_cache.get(cache_key)
            if cached is not None:
                current_app.logger.debug(f"PubMed search cache hit for '{gene_name}'")
                return cached
        except Exception:
            pass  # Cache unavailable; proceed without it

        try:
            # Construct search query
            query = f"{gene_name}[Gene Name]"

            # --- Date range filter ---
            if date_range and date_range in self._DATE_RANGE_DAYS:
                days = self._DATE_RANGE_DAYS[date_range]
                from_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y/%m/%d')
                query += f' AND ("{from_date}"[PDAT] : "3000"[PDAT])'

            # --- Article type filter ---
            if article_type and article_type in self._ARTICLE_TYPE_FILTERS:
                query += f' AND {self._ARTICLE_TYPE_FILTERS[article_type]}'

            # --- Publication status filter ---
            if pub_status == 'preprint':
                query += ' AND preprint[sb]'
            elif pub_status == 'inpress':
                query += ' AND inprocess[sb]'
            # 'published' requires no extra clause (default PubMed behaviour)

            # --- Language filter ---
            if language:
                query += f' AND {language}[la]'

            # Execute search
            handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=max_results,
                retstart=retstart,
                sort="relevance",
                usehistory="y"
            )
            
            results = Entrez.read(handle)
            handle.close()
            
            pmids = results.get('IdList', [])
            total_count = int(results.get('Count', 0))
            
            # Rate limiting
            time.sleep(0.34)  # ~3 requests per second

            result = (pmids, total_count)
            try:
                flask_cache.set(cache_key, result, timeout=3600)  # Cache for 1 hour
            except Exception:
                pass
            return result
            
        except Exception as e:
            current_app.logger.error(f"PubMed search error for {gene_name}: {str(e)}")
            raise
    
    def fetch_article_details(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch detailed information for a list of PubMed IDs.
        Serves from the article DB cache where available; hits the PubMed
        API only for PMIDs that are absent or whose cache_expires_at has passed.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of article dictionaries in the same order as *pmids*
        """
        if not pmids:
            return []

        self._configure()
        now = datetime.utcnow()

        # Layer 2: DB cache — query articles that exist and haven't expired
        cached_rows = LiteratureArticle.query.filter(
            LiteratureArticle.pubmed_id.in_(pmids),
            db.or_(
                LiteratureArticle.cache_expires_at.is_(None),
                LiteratureArticle.cache_expires_at > now
            )
        ).all()

        cached_by_pmid: Dict[str, Dict] = {
            row.pubmed_id: self._article_to_dict(row) for row in cached_rows
        }
        uncached_pmids = [pid for pid in pmids if pid not in cached_by_pmid]

        if uncached_pmids:
            current_app.logger.debug(
                f"Fetching {len(uncached_pmids)} articles from PubMed API "
                f"({len(cached_by_pmid)} served from DB cache)"
            )

        api_articles: List[Dict] = []
        if uncached_pmids:
            api_articles = self._fetch_from_api(uncached_pmids)

        # Merge and return in original PMID order
        api_by_pmid = {a['pmid']: a for a in api_articles}
        all_by_pmid = {**cached_by_pmid, **api_by_pmid}
        return [all_by_pmid[pid] for pid in pmids if pid in all_by_pmid]

    def _fetch_from_api(self, pmids: List[str]) -> List[Dict]:
        """Fetch article details from the PubMed API in batches of 200."""
        batch_size = 200
        all_articles: List[Dict] = []
        try:
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i + batch_size]

                handle = Entrez.efetch(
                    db="pubmed",
                    id=','.join(batch_pmids),
                    rettype="xml",
                    retmode="xml"
                )
                records = Entrez.read(handle)
                handle.close()

                for record in records['PubmedArticle']:
                    article = self._parse_article(record)
                    if article:
                        all_articles.append(article)

                # Rate limiting
                time.sleep(0.34)

            return all_articles
        except Exception as e:
            current_app.logger.error(f"Error fetching article details: {str(e)}")
            raise

    def _article_to_dict(self, article: LiteratureArticle) -> Dict:
        """Convert a cached LiteratureArticle DB row to the article dict format."""
        pub_types = article.publication_types or []
        return {
            'pmid': article.pubmed_id,
            'title': article.title or '',
            'abstract': article.abstract or '',
            'authors': article.authors or [],
            'journal': article.journal or '',
            'publication_date': article.publication_date,
            'doi': article.doi,
            'article_type': pub_types[0] if pub_types else '',
            'mesh_terms': article.mesh_terms or [],
            'metadata': {},
        }
    
    def _parse_article(self, record: Dict) -> Optional[Dict]:
        """
        Parse PubMed XML record into article dictionary
        
        Args:
            record: PubMed XML record
            
        Returns:
            Article dictionary or None if parsing fails
        """
        try:
            medline = record.get('MedlineCitation', {})
            article = medline.get('Article', {})
            
            # Extract PMID
            pmid = str(medline.get('PMID', ''))
            
            # Extract title
            title = article.get('ArticleTitle', '')
            
            # Extract abstract
            abstract_parts = article.get('Abstract', {}).get('AbstractText', [])
            if isinstance(abstract_parts, list):
                abstract = ' '.join([str(part) for part in abstract_parts])
            else:
                abstract = str(abstract_parts) if abstract_parts else ''
            
            # Extract authors
            author_list = article.get('AuthorList', [])
            authors = []
            for author in author_list:
                if isinstance(author, dict):
                    last_name = author.get('LastName', '')
                    fore_name = author.get('ForeName', '')
                    if last_name:
                        authors.append(f"{last_name}, {fore_name}".strip(', '))
            
            # Extract journal
            journal = article.get('Journal', {})
            journal_title = journal.get('Title', '')
            
            # Extract publication date
            pub_date = journal.get('JournalIssue', {}).get('PubDate', {})
            pub_year = pub_date.get('Year', '')
            pub_month = pub_date.get('Month', '01')
            pub_day = pub_date.get('Day', '01')
            
            publication_date = None
            if pub_year:
                try:
                    publication_date = datetime.strptime(
                        f"{pub_year}-{pub_month}-{pub_day}",
                        "%Y-%m-%d"
                    ).date()
                except:
                    publication_date = datetime.strptime(pub_year, "%Y").date()
            
            # Extract DOI
            article_ids = record.get('PubmedData', {}).get('ArticleIdList', [])
            doi = None
            for aid in article_ids:
                if aid.attributes.get('IdType') == 'doi':
                    doi = str(aid)
                    break
            
            # Extract MeSH terms
            mesh_list = medline.get('MeshHeadingList', [])
            mesh_terms = []
            for mesh in mesh_list:
                if isinstance(mesh, dict):
                    descriptor = mesh.get('DescriptorName', '')
                    if descriptor:
                        mesh_terms.append(str(descriptor))
            
            # Extract article type
            pub_type_list = article.get('PublicationTypeList', [])
            article_type = ', '.join([str(pt) for pt in pub_type_list]) if pub_type_list else ''
            
            return {
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'journal': journal_title,
                'publication_date': publication_date,
                'doi': doi,
                'article_type': article_type,
                'mesh_terms': mesh_terms,
                'metadata': {
                    'pub_year': pub_year,
                    'raw_record': True
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error parsing article: {str(e)}")
            return None
    
    def save_search(self, user_id: int, search_term: str, 
                   search_type: str, results_count: int,
                   search_params: Dict = None) -> LiteratureSearch:
        """
        Save search to database
        
        Args:
            user_id: User performing search
            search_term: Search query
            search_type: Type of search (gene, keyword, etc.)
            results_count: Number of results found
            search_params: Additional search parameters
            
        Returns:
            LiteratureSearch object
        """
        search = LiteratureSearch(
            user_id=user_id,
            search_query=search_term,
            filters=search_params or {},
            result_count=results_count
        )
        
        db.session.add(search)
        db.session.commit()
        
        # Log the search
        AuditService.log_search(
            search_term=search_term,
            results_count=results_count
        )
        
        return search
    
    def save_articles(self, articles: List[Dict], 
                     search_id: int) -> List[LiteratureArticle]:
        """
        Save articles to database and link to search
        
        Args:
            articles: List of article dictionaries
            search_id: Associated search ID
            
        Returns:
            List of LiteratureArticle objects
        """
        saved_articles = []
        cache_expires = datetime.utcnow() + timedelta(days=7)

        for idx, article_data in enumerate(articles):
            # Check if article already exists
            article = LiteratureArticle.query.filter_by(
                pubmed_id=article_data['pmid']
            ).first()
            
            if not article:
                # Create new article
                article = LiteratureArticle(
                    pubmed_id=article_data['pmid'],
                    title=article_data['title'],
                    abstract=article_data['abstract'],
                    authors=article_data['authors'],
                    journal=article_data['journal'],
                    publication_date=article_data['publication_date'],
                    doi=article_data['doi'],
                    publication_types=[article_data['article_type']] if article_data.get('article_type') else [],
                    mesh_terms=article_data['mesh_terms'],
                    cache_expires_at=cache_expires
                )
                db.session.add(article)
                db.session.flush()  # Get article ID
            else:
                # Refresh cache expiry so frequently accessed articles stay warm
                article.cache_expires_at = cache_expires
            
            # Create search result link
            search_result = SearchResult(
                search_id=search_id,
                article_id=article.id,
                rank=idx + 1
            )
            db.session.add(search_result)
            
            saved_articles.append(article)
        
        db.session.commit()
        return saved_articles


# Initialize service instance
pubmed_service = PubMedService()
