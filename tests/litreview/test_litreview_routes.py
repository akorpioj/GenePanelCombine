import pytest
from app.litreview.pubmed_service import PubMedService
from app.models import LiteratureSearch, LiteratureArticle

class TestPubMedService:
    
    def test_search_by_gene(self, app):
        """Test basic gene search"""
        service = PubMedService()
        pmids, total_count = service.search_by_gene('BRCA1', max_results=10)
        
        assert len(pmids) <= 10
        assert total_count > 0
        assert all(isinstance(pmid, str) for pmid in pmids)
    
    def test_fetch_article_details(self, app):
        """Test fetching article details"""
        service = PubMedService()
        # Use known PMID
        articles = service.fetch_article_details(['34562839'])
        
        assert len(articles) == 1
        assert articles[0]['pmid'] == '34562839'
        assert 'title' in articles[0]
        assert 'abstract' in articles[0]
    
    def test_save_search(self, app, test_user):
        """Test saving search to database"""
        service = PubMedService()
        search = service.save_search(
            user_id=test_user.id,
            search_term='BRCA1',
            search_type='gene',
            results_count=10
        )
        
        assert search.id is not None
        assert search.search_term == 'BRCA1'
        assert search.results_count == 10
    
    # Add more tests...