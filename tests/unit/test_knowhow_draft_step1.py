"""
Tests for Feature 5 Step 1 — is_draft column on KnowhowArticle.

Covers:
- Column exists in the schema with correct type/constraints
- Python-level default: new articles are published (is_draft=False) by default
- is_draft=True creates a valid draft article
- is_draft cannot be NULL (NOT NULL constraint)
- Toggling is_draft works and persists
"""
import pytest
import datetime
from sqlalchemy import inspect as sa_inspect
from app.models import db, User, UserRole, KnowhowArticle


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def author(db_session):
    user = User(username='article_author', email='author@test.com', role=UserRole.USER)
    user.set_password('password')
    db_session.add(user)
    db_session.commit()
    return user


def _make_article(author, is_draft=False, title='Test Article'):
    return KnowhowArticle(
        title=title,
        category='genetics',
        content='<p>Body text</p>',
        user_id=author.id,
        is_draft=is_draft,
    )


# ── Schema tests ─────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.database
class TestIsDraftColumn:
    """Verify the is_draft column exists with the right schema properties."""

    def test_column_exists(self, db_session):
        """is_draft column must be present on knowhow_articles."""
        inspector = sa_inspect(db.engine)
        columns = {c['name'] for c in inspector.get_columns('knowhow_articles')}
        assert 'is_draft' in columns, (
            "Column 'is_draft' missing from knowhow_articles — "
            "run Step 1 migration: flask db upgrade"
        )

    def test_column_is_not_nullable(self, db_session):
        """is_draft must be NOT NULL."""
        inspector = sa_inspect(db.engine)
        col = next(
            c for c in inspector.get_columns('knowhow_articles')
            if c['name'] == 'is_draft'
        )
        assert col['nullable'] is False, "is_draft should be NOT NULL"

    def test_column_default_is_false(self, db_session):
        """The DB-level or server default for is_draft should be false/0."""
        inspector = sa_inspect(db.engine)
        col = next(
            c for c in inspector.get_columns('knowhow_articles')
            if c['name'] == 'is_draft'
        )
        # SQLite stores booleans as integers; PostgreSQL stores as boolean.
        # Accept either a server_default of '0', 'false', False, or 0.
        default = col.get('default') or col.get('server_default')
        if default is not None:
            # PostgreSQL returns server_default as "'false'" (with inner quotes)
            # SQLite returns 0 or 'false'. Accept all valid falsy representations.
            assert str(default).strip("'\" ").lower() in ('0', 'false'), (
                f"Unexpected default value for is_draft: {default!r}"
            )


# ── Model-level default tests ─────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.database
class TestIsDraftModelDefault:
    """Verify the Python-level default on KnowhowArticle."""

    def test_new_article_is_published_by_default(self, db_session, author):
        """Creating an article without specifying is_draft should produce is_draft=False."""
        article = KnowhowArticle(
            title='Default draft test',
            category='genetics',
            content='<p>Hello</p>',
            user_id=author.id,
        )
        db_session.add(article)
        db_session.commit()

        fetched = KnowhowArticle.query.get(article.id)
        assert fetched.is_draft is False, (
            "Articles should be published (is_draft=False) by default"
        )

    def test_explicit_published_article(self, db_session, author):
        """Explicitly setting is_draft=False creates a published article."""
        article = _make_article(author, is_draft=False, title='Published article')
        db_session.add(article)
        db_session.commit()

        fetched = KnowhowArticle.query.get(article.id)
        assert fetched.is_draft is False

    def test_explicit_draft_article(self, db_session, author):
        """Explicitly setting is_draft=True creates a draft article."""
        article = _make_article(author, is_draft=True, title='Draft article')
        db_session.add(article)
        db_session.commit()

        fetched = KnowhowArticle.query.get(article.id)
        assert fetched.is_draft is True


# ── Persistence & toggle tests ────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.database
class TestIsDraftPersistence:
    """Verify is_draft persists correctly through updates."""

    def test_draft_to_published(self, db_session, author):
        """Changing is_draft from True to False (i.e. publishing) persists."""
        article = _make_article(author, is_draft=True, title='Will publish')
        db_session.add(article)
        db_session.commit()

        article.is_draft = False
        db_session.commit()

        fetched = KnowhowArticle.query.get(article.id)
        assert fetched.is_draft is False

    def test_published_to_draft(self, db_session, author):
        """Changing is_draft from False to True (retracting) persists."""
        article = _make_article(author, is_draft=False, title='Will retract')
        db_session.add(article)
        db_session.commit()

        article.is_draft = True
        db_session.commit()

        fetched = KnowhowArticle.query.get(article.id)
        assert fetched.is_draft is True

    def test_is_draft_independent_of_other_fields(self, db_session, author):
        """Updating title does not change is_draft."""
        article = _make_article(author, is_draft=True, title='Original title')
        db_session.add(article)
        db_session.commit()

        article.title = 'Updated title'
        db_session.commit()

        fetched = KnowhowArticle.query.get(article.id)
        assert fetched.is_draft is True
        assert fetched.title == 'Updated title'


# ── Query filter tests ────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.database
class TestIsDraftQueryFiltering:
    """
    Verify that draft articles can be filtered correctly at the query level.
    (Validates the filter pattern used in Step 3, but depends only on Step 1.)
    """

    def test_filter_excludes_drafts(self, db_session, author):
        """Querying is_draft==False should exclude draft articles."""
        published = _make_article(author, is_draft=False, title='Published')
        draft     = _make_article(author, is_draft=True,  title='Draft')
        db_session.add_all([published, draft])
        db_session.commit()

        results = KnowhowArticle.query.filter_by(is_draft=False).all()
        titles = [a.title for a in results]

        assert 'Published' in titles
        assert 'Draft' not in titles

    def test_filter_returns_only_drafts(self, db_session, author):
        """Querying is_draft==True should return only draft articles."""
        published = _make_article(author, is_draft=False, title='Published2')
        draft     = _make_article(author, is_draft=True,  title='Draft2')
        db_session.add_all([published, draft])
        db_session.commit()

        results = KnowhowArticle.query.filter_by(is_draft=True).all()
        titles = [a.title for a in results]

        assert 'Draft2' in titles
        assert 'Published2' not in titles

    def test_author_can_see_own_drafts(self, db_session, author):
        """Author's own draft articles are returned when filtering by user_id."""
        draft = _make_article(author, is_draft=True, title='My draft')
        db_session.add(draft)
        db_session.commit()

        results = (KnowhowArticle.query
                   .filter_by(user_id=author.id, is_draft=True)
                   .all())
        assert any(a.title == 'My draft' for a in results)

    def test_multiple_authors_drafts_isolated(self, db_session, author):
        """Draft articles from one author should not appear when filtering by another."""
        other = User(username='other_author', email='other@test.com', role=UserRole.USER)
        other.set_password('password')
        db_session.add(other)
        db_session.commit()

        author_draft = _make_article(author, is_draft=True, title='Author draft')
        other_draft  = _make_article(other,  is_draft=True, title='Other draft')
        db_session.add_all([author_draft, other_draft])
        db_session.commit()

        author_drafts = (KnowhowArticle.query
                         .filter_by(user_id=author.id, is_draft=True)
                         .all())
        titles = [a.title for a in author_drafts]

        assert 'Author draft' in titles
        assert 'Other draft' not in titles
