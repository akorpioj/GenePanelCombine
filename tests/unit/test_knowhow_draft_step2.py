"""
Tests for Feature 5 Step 2 — "Save as Draft" / "Publish" buttons in the article editor.

Covers:
- POST /knowhow/articles with action=publish  → article.is_draft == False
- POST /knowhow/articles with action=draft    → article.is_draft == True
- POST /knowhow/articles with no action field → defaults to published
- POST /knowhow/articles/<id>/edit with action=publish on an existing draft → publishes it
- POST /knowhow/articles/<id>/edit with action=draft   on a published article → retracts it
- POST /knowhow/articles/<id>/edit with no action field → preserves existing is_draft value

All tests use the HTTP test client so they exercise the full route stack.
"""
import pytest
from app.models import db, User, UserRole, KnowhowArticle


# ── Fixtures ─────────────────────────────────────────────────────────────────

# Use a slug from _DEFAULT_CATEGORIES so that _seed_categories() auto-creates
# it when the route first calls _get_categories(), regardless of any session
# isolation between the test's db_session and the request context's session.
_CATEGORY_SLUG = 'gene_panels'


@pytest.fixture
def author(db_session):
    user = User(username='draft_author', email='draft_author@test.com', role=UserRole.USER)
    user.set_password('draftpass')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def logged_in_client(client, author):
    """Test client with the author logged in.

    Uses direct session injection (bypasses the login form) so that auth works
    regardless of the login form field names. A GET to the editor is issued
    first to trigger _get_categories() → _seed_categories(), ensuring all
    default category slugs exist in the database before any POST.
    """
    with client.session_transaction() as sess:
        sess['_user_id'] = str(author.id)
        sess['_fresh'] = True
    # Trigger category seeding so the default slugs exist for subsequent POSTs.
    client.get('/knowhow/articles/new', follow_redirects=False)
    return client


def _article_payload(action=None, title='Draft Test Article'):
    data = {
        'title':    title,
        'category': _CATEGORY_SLUG,
        'content':  '<p>Body text</p>',
        'summary':  '',
        'tags':     '',
    }
    if action is not None:
        data['action'] = action
    return data


# ── create_article (POST /knowhow/articles) ───────────────────────────────────

@pytest.mark.unit
class TestCreateArticleAction:
    """POSTing to create_article with different action values."""

    def test_publish_action_creates_published_article(self, logged_in_client, db_session):
        """action=publish → is_draft=False."""
        resp = logged_in_client.post(
            '/knowhow/articles',
            data=_article_payload(action='publish', title='Publish me'),
            follow_redirects=False,
        )
        assert resp.status_code in (302, 200), f"Unexpected status {resp.status_code}"

        article = KnowhowArticle.query.filter_by(title='Publish me').first()
        assert article is not None, "Article was not created"
        assert article.is_draft is False, "action=publish should set is_draft=False"

    def test_draft_action_creates_draft_article(self, logged_in_client, db_session):
        """action=draft → is_draft=True."""
        resp = logged_in_client.post(
            '/knowhow/articles',
            data=_article_payload(action='draft', title='Save as draft'),
            follow_redirects=False,
        )
        assert resp.status_code in (302, 200), f"Unexpected status {resp.status_code}"

        article = KnowhowArticle.query.filter_by(title='Save as draft').first()
        assert article is not None, "Article was not created"
        assert article.is_draft is True, "action=draft should set is_draft=True"

    def test_no_action_field_creates_published_article(self, logged_in_client, db_session):
        """Omitting action entirely defaults to published (is_draft=False)."""
        resp = logged_in_client.post(
            '/knowhow/articles',
            data=_article_payload(action=None, title='No action field'),
            follow_redirects=False,
        )
        assert resp.status_code in (302, 200), f"Unexpected status {resp.status_code}"

        article = KnowhowArticle.query.filter_by(title='No action field').first()
        assert article is not None, "Article was not created"
        assert article.is_draft is False, "Missing action should default to published"


# ── update_article (POST /knowhow/articles/<id>/edit) ─────────────────────────

@pytest.mark.unit
class TestUpdateArticleAction:
    """POSTing to update_article with different action values."""

    def _seed_article(self, db_session, author, is_draft, title):
        article = KnowhowArticle(
            title=title,
            category=_CATEGORY_SLUG,
            content='<p>Original</p>',
            user_id=author.id,
            is_draft=is_draft,
        )
        db_session.add(article)
        db_session.commit()
        return article

    def test_publish_action_publishes_draft(self, logged_in_client, author, db_session):
        """action=publish on a draft article → is_draft=False."""
        article = self._seed_article(db_session, author, is_draft=True, title='Will publish')

        resp = logged_in_client.post(
            f'/knowhow/articles/{article.id}/edit',
            data=_article_payload(action='publish', title='Will publish'),
            follow_redirects=False,
        )
        assert resp.status_code in (302, 200)

        db_session.refresh(article)
        assert article.is_draft is False, "action=publish should un-draft the article"

    def test_draft_action_retracts_published_article(self, logged_in_client, author, db_session):
        """action=draft on a published article → is_draft=True."""
        article = self._seed_article(db_session, author, is_draft=False, title='Will retract')

        resp = logged_in_client.post(
            f'/knowhow/articles/{article.id}/edit',
            data=_article_payload(action='draft', title='Will retract'),
            follow_redirects=False,
        )
        assert resp.status_code in (302, 200)

        db_session.refresh(article)
        assert article.is_draft is True, "action=draft should retract the article"

    def test_no_action_defaults_to_published_on_draft(self, logged_in_client, author, db_session):
        """Omitting action on a draft article defaults to 'publish', so is_draft becomes False."""
        article = self._seed_article(db_session, author, is_draft=True, title='Stay draft')

        resp = logged_in_client.post(
            f'/knowhow/articles/{article.id}/edit',
            data=_article_payload(action=None, title='Stay draft'),
            follow_redirects=False,
        )
        assert resp.status_code in (302, 200)

        db_session.refresh(article)
        assert article.is_draft is False, (
            "Omitting action should default to 'publish', setting is_draft=False"
        )

    def test_no_action_keeps_published_as_published(self, logged_in_client, author, db_session):
        """Omitting action on a published article should leave it published."""
        article = self._seed_article(db_session, author, is_draft=False, title='Stay published')

        resp = logged_in_client.post(
            f'/knowhow/articles/{article.id}/edit',
            data=_article_payload(action=None, title='Stay published'),
            follow_redirects=False,
        )
        assert resp.status_code in (302, 200)

        db_session.refresh(article)
        assert article.is_draft is False, (
            "Omitting action on a published article should preserve is_draft=False"
        )

    def test_other_fields_updated_independently_of_draft_state(
        self, logged_in_client, author, db_session
    ):
        """Updating title with action=draft changes title but also sets is_draft correctly."""
        article = self._seed_article(db_session, author, is_draft=False, title='Old title')

        logged_in_client.post(
            f'/knowhow/articles/{article.id}/edit',
            data=_article_payload(action='draft', title='New title'),
            follow_redirects=False,
        )

        db_session.refresh(article)
        assert article.title == 'New title'
        assert article.is_draft is True
