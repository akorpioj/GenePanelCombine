# LitReview Phase 1: Basic PubMed Search Integration
## Detailed Implementation Plan

**Version**: 1.6.0
**Target Release**: Q2 2026
**Priority**: High
**Estimated Effort**: 4-6 weeks

---

## 1. Overview

This document provides a detailed implementation plan for integrating basic PubMed search functionality into the LitReview module. This is the foundation feature that will enable users to search biomedical literature directly from PanelMerge.

### 1.1 Goals
- Enable gene-based literature search using NCBI PubMed
- Provide clean, user-friendly display of search results
- Store search history for user convenience
- Integrate with existing PanelMerge gene panel system
- Establish foundation for future literature analysis features

### 1.2 Non-Goals (Future Phases)
- Advanced filtering (Phase 2)
- AI-powered summarization (Phase 3)
- Multi-database integration beyond PubMed (Phase 2)
- Collaboration features (Phase 4)

---

## 2. Technical Architecture

### 2.1 NCBI E-utilities API Integration

#### 2.1.1 API Overview
- **API Base URL**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- **Key Endpoints**:
  - `esearch.fcgi`: Search database and retrieve list of UIDs
  - `esummary.fcgi`: Retrieve document summaries for list of UIDs
  - `efetch.fcgi`: Retrieve formatted data records
  - `elink.fcgi`: Link between Entrez databases

#### 2.1.2 API Rate Limits & Best Practices
- **Without API Key**: 3 requests per second
- **With API Key**: 10 requests per second
- **Best Practices**:
  - Include `tool` parameter with application name
  - Include `email` parameter for contact
  - Implement exponential backoff for rate limit errors
  - Weekend usage allowed without restrictions

#### 2.1.3 Required Python Libraries
```python
# requirements.txt additions
biopython>=1.81          # Bio.Entrez for PubMed API access
xmltodict>=0.13.0        # XML parsing for PubMed results
python-dateutil>=2.8.2   # Date parsing for publication dates
```

### 2.2 Database Schema Changes

#### 2.2.1 New Tables

**Table: `literature_searches`**
```sql
CREATE TABLE literature_searches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    search_term VARCHAR(500) NOT NULL,
    search_type VARCHAR(50) DEFAULT 'gene',  -- 'gene', 'keyword', 'author'
    database_source VARCHAR(50) DEFAULT 'pubmed',
    results_count INTEGER DEFAULT 0,
    search_parameters JSONB,  -- Store filters, date ranges, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_searches (user_id, created_at DESC),
    INDEX idx_search_term (search_term)
);
```

**Table: `literature_articles`**
```sql
CREATE TABLE literature_articles (
    id SERIAL PRIMARY KEY,
    pmid VARCHAR(20) UNIQUE NOT NULL,  -- PubMed ID
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT,  -- JSON array of authors
    journal VARCHAR(500),
    publication_date DATE,
    doi VARCHAR(100),
    article_type VARCHAR(100),
    mesh_terms TEXT,  -- JSON array of MeSH terms
    keywords TEXT,  -- JSON array of keywords
    citation_count INTEGER DEFAULT 0,
    metadata JSONB,  -- Additional metadata
    full_text_url TEXT,
    pdf_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pmid (pmid),
    INDEX idx_publication_date (publication_date DESC),
    INDEX idx_title_text (title) -- Full-text search index
);
```

**Table: `search_results`** (Junction table)
```sql
CREATE TABLE search_results (
    id SERIAL PRIMARY KEY,
    search_id INTEGER REFERENCES literature_searches(id) ON DELETE CASCADE,
    article_id INTEGER REFERENCES literature_articles(id) ON DELETE CASCADE,
    relevance_score FLOAT,
    position_in_results INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(search_id, article_id),
    INDEX idx_search_results (search_id, position_in_results)
);
```

**Table: `user_article_actions`**
```sql
CREATE TABLE user_article_actions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    article_id INTEGER REFERENCES literature_articles(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,  -- 'view', 'save', 'export', 'cite'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_articles (user_id, article_id),
    INDEX idx_action_type (action_type, created_at DESC)
);
```

#### 2.2.2 Migration Script
```python
# migrations/versions/xxx_add_litreview_tables.py
"""Add LitReview literature search tables

Revision ID: xxx
Revises: previous_revision
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'xxx'
down_revision = 'previous_revision'

def upgrade():
    # Create literature_searches table
    op.create_table(
        'literature_searches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('search_term', sa.String(500), nullable=False),
        sa.Column('search_type', sa.String(50), server_default='gene'),
        sa.Column('database_source', sa.String(50), server_default='pubmed'),
        sa.Column('results_count', sa.Integer(), server_default='0'),
        sa.Column('search_parameters', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_searches', 'literature_searches', ['user_id', 'created_at'])
    op.create_index('idx_search_term', 'literature_searches', ['search_term'])
    
    # Create literature_articles table
    # ... (complete table creation)
    
    # Create search_results junction table
    # ... (complete table creation)
    
    # Create user_article_actions table
    # ... (complete table creation)

def downgrade():
    op.drop_table('user_article_actions')
    op.drop_table('search_results')
    op.drop_table('literature_articles')
    op.drop_table('literature_searches')
```

---

## 3. Backend Implementation

### 3.1 PubMed Service Module

**File**: `app/litreview/pubmed_service.py`

### 3.2 Database Models

**File**: `app/models.py` (additions)

```python
class LiteratureSearch(db.Model):
    """Model for literature search history"""
    __tablename__ = 'literature_searches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    search_term = db.Column(db.String(500), nullable=False)
    search_type = db.Column(db.String(50), default='gene')
    database_source = db.Column(db.String(50), default='pubmed')
    results_count = db.Column(db.Integer, default=0)
    search_parameters = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('literature_searches', lazy='dynamic'))
    results = db.relationship('SearchResult', backref='search', lazy='dynamic', 
                            cascade='all, delete-orphan')


class LiteratureArticle(db.Model):
    """Model for literature articles"""
    __tablename__ = 'literature_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    pmid = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.Text, nullable=False)
    abstract = db.Column(db.Text)
    authors = db.Column(db.JSON)  # List of authors
    journal = db.Column(db.String(500))
    publication_date = db.Column(db.Date)
    doi = db.Column(db.String(100))
    article_type = db.Column(db.String(100))
    mesh_terms = db.Column(db.JSON)  # List of MeSH terms
    keywords = db.Column(db.JSON)  # List of keywords
    citation_count = db.Column(db.Integer, default=0)
    metadata = db.Column(db.JSON)
    full_text_url = db.Column(db.Text)
    pdf_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    search_results = db.relationship('SearchResult', backref='article', lazy='dynamic',
                                   cascade='all, delete-orphan')
    user_actions = db.relationship('UserArticleAction', backref='article', lazy='dynamic',
                                  cascade='all, delete-orphan')


class SearchResult(db.Model):
    """Junction table for search results"""
    __tablename__ = 'search_results'
    
    id = db.Column(db.Integer, primary_key=True)
    search_id = db.Column(db.Integer, db.ForeignKey('literature_searches.id', ondelete='CASCADE'))
    article_id = db.Column(db.Integer, db.ForeignKey('literature_articles.id', ondelete='CASCADE'))
    relevance_score = db.Column(db.Float)
    position_in_results = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserArticleAction(db.Model):
    """Track user interactions with articles"""
    __tablename__ = 'user_article_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    article_id = db.Column(db.Integer, db.ForeignKey('literature_articles.id', ondelete='CASCADE'))
    action_type = db.Column(db.String(50), nullable=False)  # view, save, export, cite
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('article_actions', lazy='dynamic'))
```

### 3.3 API Routes

**File**: `app/litreview/routes.py` (enhanced)

---

## 4. Frontend Implementation

### 4.1 Search Interface Template

**File**: `app/templates/litreview/search.html`

### 4.2 Results Display Template

**File**: `app/templates/litreview/results.html`

---

## 5. Configuration & Environment

### 5.1 Environment Variables

Add to `.env` file:
```bash
# PubMed API Configuration
PUBMED_EMAIL=your.email@example.com
PUBMED_API_KEY=your_ncbi_api_key_here  # Optional but recommended
PUBMED_TOOL_NAME=PanelMerge-LitReview
PUBMED_MAX_RESULTS=200
```

### 5.2 Config Settings

Add to `app/config_settings.py`:
```python
class Config:
    # ... existing config ...
    
    # PubMed Configuration
    PUBMED_EMAIL = os.getenv('PUBMED_EMAIL', 'default@example.com')
    PUBMED_API_KEY = os.getenv('PUBMED_API_KEY', None)
    PUBMED_TOOL_NAME = os.getenv('PUBMED_TOOL_NAME', 'PanelMerge-LitReview')
    PUBMED_MAX_RESULTS = int(os.getenv('PUBMED_MAX_RESULTS', 200))
```

---

## 6. Testing Plan

### 6.1 Unit Tests

**File**: `tests/test_pubmed_service.py`

### 6.2 Integration Tests

**File**: `tests/test_litreview_routes.py`

```python
import pytest
from flask import url_for

class TestLitReviewRoutes:
    
    def test_search_page_requires_login(self, client):
        """Test that search page requires authentication"""
        response = client.get(url_for('litreview.search'))
        assert response.status_code == 302  # Redirect to login
    
    def test_search_submission(self, client, authenticated_user):
        """Test search form submission"""
        response = client.post(
            url_for('litreview.search'),
            data={
                'search_term': 'BRCA1',
                'search_type': 'gene',
                'max_results': '50'
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Found' in response.data
    
    # Add more tests...
```

---

## 7. Documentation

### 7.1 User Documentation

Create `docs/LITREVIEW_USER_GUIDE.md` with:
- How to perform a literature search
- Understanding search results
- Viewing article details
- Managing search history

### 7.2 API Documentation

Update Swagger/OpenAPI documentation with new endpoints:
- POST `/api/litreview/search`
- GET `/api/litreview/results/<search_id>`
- GET `/api/litreview/article/<article_id>`

---

## 8. Implementation Timeline

### Week 1: Foundation
- [X] Set up NCBI API credentials
- [X] Create database migration
- [X] Implement basic PubMedService class
- [X] Write unit tests for service

### Week 2: Backend Integration
- [X] Complete PubMedService implementation
- [X] Create database models
- [X] Implement API routes
- [ ] Write integration tests

### Week 3: Frontend Development
- [X] Create search interface template
- [X] Create results display template
- [X] Create article detail template
- [X] Add search history view

### Week 4: Testing & Polish
- [ ] Comprehensive testing
- [X] Performance optimization
- [ ] Documentation
- [ ] User acceptance testing

### Week 5-6: Deployment & Monitoring
- [ ] Deploy to staging environment
- [ ] Monitor API rate limits
- [ ] Fix any production issues
- [ ] Deploy to production

---

## 9. Success Criteria

- [ ] Users can search PubMed by gene name
- [ ] Search results display correctly with all metadata
- [ ] Article details are viewable and well-formatted
- [ ] Search history is saved and accessible
- [ ] API rate limits are respected
- [ ] Response time < 3 seconds for typical searches
- [ ] All tests pass
- [ ] Documentation is complete

---

## 10. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| API rate limits exceeded | High | Implement caching, use API key, exponential backoff |
| Large result sets slow | Medium | Implement pagination, limit max results |
| Database growth | Medium | Regular cleanup of old searches, archiving strategy |
| XML parsing errors | Low | Robust error handling, logging |
| Network timeouts | Low | Retry logic, timeout configuration |

---

## 11. Future Enhancements (Post Phase 1)

- Advanced filtering (date range, article type)
- Export to citation managers
- Save favorite articles
- Annotation and notes
- Integration with gene panels
- Automated literature alerts

---

*Document Version: 1.0*
*Last Updated: March 22, 2026*
*Author: Development Team*
