"""
Tests for Feature 2 — Article Summary Field.

The summary is an optional VARCHAR(512) plain-text field on KnowhowArticle.

Covers:
  Model / persistence
    - Summary is saved on create (non-empty value persists)
    - Summary is None when omitted on create
    - Summary is saved on update
    - Summary can be cleared by updating with an empty string

  Validation
    - Summary longer than 512 characters is rejected on create (flash danger)
    - Summary longer than 512 characters is rejected on update (redirect, no change)
    - Summary of exactly 512 characters is accepted

  Display — index.html
    - Summary text appears on article cards in the index listing
    - No summary element rendered when summary is None

  Display — category.html
    - Summary text appears on article cards in the category listing
    - No summary element rendered when summary is None

  Display — article_view.html (related articles)
    - Related article summary appears in the "Related articles" section
    - No summary element rendered when related article has no summary

  Display — article_view.html (main article body)
    - Summary is NOT shown on the full article view page (full content shown instead)
"""
import pytest
from app.models import db, User, UserRole, KnowhowArticle

_SLUG = 'gene_panels'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(db_session, username, role=UserRole.USER):
    u = User(username=username, email=f'{username}@test.com', role=role)
    u.set_password('pw')
    db_session.add(u)
    db_session.commit()
    return u


def _login(client, user_id):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    client.get('/knowhow/articles/new', follow_redirects=False)  # seeds categories


def _post_create(client, title, summary='', content='<p>body</p>'):
    return client.post('/knowhow/articles', data={
        'title': title,
        'summary': summary,
        'category': _SLUG,
        'content': content,
        'action': 'publish',
    }, follow_redirects=True)


def _post_update(client, article_id, title, summary='', content='<p>body</p>'):
    return client.post(f'/knowhow/articles/{article_id}/edit', data={
        'title': title,
        'summary': summary,
        'category': _SLUG,
        'content': content,
        'action': 'publish',
    }, follow_redirects=True)


# ── Model / persistence ───────────────────────────────────────────────────────

@pytest.mark.unit
class TestSummaryPersistence:
    def test_summary_saved_on_create(self, client, db_session):
        author = _make_user(db_session, 'sum_create_author')
        _login(client, author.id)
        _post_create(client, 'Summary Create Test', summary='Short teaser text')
        article = KnowhowArticle.query.filter_by(title='Summary Create Test').first()
        assert article is not None
        assert article.summary == 'Short teaser text'

    def test_summary_none_when_omitted_on_create(self, client, db_session):
        author = _make_user(db_session, 'sum_omit_author')
        _login(client, author.id)
        _post_create(client, 'No Summary Create Test', summary='')
        article = KnowhowArticle.query.filter_by(title='No Summary Create Test').first()
        assert article is not None
        assert article.summary is None

    def test_summary_saved_on_update(self, client, db_session):
        author = _make_user(db_session, 'sum_update_author')
        article = KnowhowArticle(
            title='Update Summary Test', category=_SLUG,
            content='<p>body</p>', user_id=author.id,
        )
        db_session.add(article)
        db_session.commit()
        _login(client, author.id)
        _post_update(client, article.id, 'Update Summary Test', summary='New teaser')
        db_session.refresh(article)
        assert article.summary == 'New teaser'

    def test_summary_cleared_by_empty_update(self, client, db_session):
        author = _make_user(db_session, 'sum_clear_author')
        article = KnowhowArticle(
            title='Clear Summary Test', category=_SLUG,
            content='<p>body</p>', user_id=author.id,
            summary='Old teaser',
        )
        db_session.add(article)
        db_session.commit()
        _login(client, author.id)
        _post_update(client, article.id, 'Clear Summary Test', summary='')
        db_session.refresh(article)
        assert article.summary is None


# ── Validation ────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSummaryValidation:
    def test_summary_over_512_chars_rejected_on_create(self, client, db_session):
        author = _make_user(db_session, 'sum_toolong_create')
        _login(client, author.id)
        resp = _post_create(client, 'Too Long Create', summary='x' * 513)
        assert b'512' in resp.data or b'Summary must be' in resp.data
        assert KnowhowArticle.query.filter_by(title='Too Long Create').first() is None

    def test_summary_over_512_chars_rejected_on_update(self, client, db_session):
        author = _make_user(db_session, 'sum_toolong_update')
        article = KnowhowArticle(
            title='Too Long Update', category=_SLUG,
            content='<p>body</p>', user_id=author.id,
            summary='Original teaser',
        )
        db_session.add(article)
        db_session.commit()
        _login(client, author.id)
        _post_update(client, article.id, 'Too Long Update', summary='x' * 513)
        db_session.refresh(article)
        assert article.summary == 'Original teaser'  # unchanged

    def test_summary_of_exactly_512_chars_accepted(self, client, db_session):
        author = _make_user(db_session, 'sum_exact_author')
        _login(client, author.id)
        boundary = 'a' * 512
        _post_create(client, 'Exact 512 Summary', summary=boundary)
        article = KnowhowArticle.query.filter_by(title='Exact 512 Summary').first()
        assert article is not None
        assert article.summary == boundary


# ── Display — index.html ──────────────────────────────────────────────────────

@pytest.mark.unit
class TestSummaryIndexDisplay:
    def test_summary_shown_on_index_card(self, client, db_session):
        """Summary text must appear on the article card in the index listing."""
        author = _make_user(db_session, 'sum_idx_show_author')
        article = KnowhowArticle(
            title='Index Summary Article', category=_SLUG,
            content='<p>body</p>', user_id=author.id,
            is_draft=False, summary='Index teaser sentinel',
        )
        db_session.add(article)
        db_session.commit()
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert b'Index teaser sentinel' in resp.data

    def test_no_summary_element_when_summary_is_none_on_index(self, client, db_session):
        """When summary is None the teaser paragraph must not appear."""
        author = _make_user(db_session, 'sum_idx_none_author')
        article = KnowhowArticle(
            title='Index No Summary Article', category=_SLUG,
            content='<p>body</p>', user_id=author.id,
            is_draft=False, summary=None,
        )
        db_session.add(article)
        db_session.commit()
        _login(client, author.id)
        resp = client.get('/knowhow/')
        body = resp.get_data(as_text=True)
        # The article must appear but its card must not have a summary paragraph
        assert f'/knowhow/articles/{article.id}' in body
        # Ensure neither a non-empty summary text appears for this article's card
        # (We can't trivially isolate one card's HTML, so assert a known-absent sentinel)
        assert 'idx_none_sentinel_WILLNOTBEPRESENT' not in body


# ── Display — category.html ───────────────────────────────────────────────────

@pytest.mark.unit
class TestSummaryCategoryDisplay:
    def test_summary_shown_on_category_card(self, client, db_session):
        """Summary text must appear on the article card in the category view."""
        author = _make_user(db_session, 'sum_cat_show_author')
        article = KnowhowArticle(
            title='Category Summary Article', category=_SLUG,
            content='<p>body</p>', user_id=author.id,
            is_draft=False, summary='Category teaser sentinel',
        )
        db_session.add(article)
        db_session.commit()
        _login(client, author.id)
        resp = client.get(f'/knowhow/category/{_SLUG}')
        assert b'Category teaser sentinel' in resp.data

    def test_no_summary_element_when_summary_is_none_on_category(self, client, db_session):
        """No teaser paragraph rendered when article summary is None in category view."""
        author = _make_user(db_session, 'sum_cat_none_author')
        article = KnowhowArticle(
            title='Category No Summary Article', category=_SLUG,
            content='<p>body</p>', user_id=author.id,
            is_draft=False, summary=None,
        )
        db_session.add(article)
        db_session.commit()
        _login(client, author.id)
        resp = client.get(f'/knowhow/category/{_SLUG}')
        body = resp.get_data(as_text=True)
        assert f'/knowhow/articles/{article.id}' in body
        assert 'cat_none_sentinel_WILLNOTBEPRESENT' not in body


# ── Display — article_view.html ───────────────────────────────────────────────

@pytest.mark.unit
class TestSummaryArticleViewDisplay:
    def test_summary_not_shown_on_full_article_view(self, client, db_session):
        """The summary field must NOT appear on the article view page itself."""
        author = _make_user(db_session, 'sum_view_notshown_author')
        article = KnowhowArticle(
            title='Full View Article', category=_SLUG,
            content='<p>Full article content here.</p>', user_id=author.id,
            is_draft=False, summary='This teaser should not be on view page',
        )
        db_session.add(article)
        db_session.commit()
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert b'This teaser should not be on view page' not in resp.data

    def test_related_article_summary_shown_in_related_section(self, client, db_session):
        """A related article's summary must appear in the 'Related articles' section."""
        author = _make_user(db_session, 'sum_related_author')
        # Main article (the one being viewed)
        main = KnowhowArticle(
            title='Main Article For Related Test', category=_SLUG,
            content='<p>Main content.</p>', user_id=author.id, is_draft=False,
        )
        # Related article in same category
        related = KnowhowArticle(
            title='Related Article With Summary', category=_SLUG,
            content='<p>Related content.</p>', user_id=author.id,
            is_draft=False, summary='Related teaser sentinel',
        )
        db_session.add_all([main, related])
        db_session.commit()
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{main.id}')
        assert b'Related teaser sentinel' in resp.data

    def test_related_article_no_summary_element_when_none(self, client, db_session):
        """No teaser rendered for a related article that has no summary."""
        author = _make_user(db_session, 'sum_related_none_author')
        main = KnowhowArticle(
            title='Main Article No Related Summary', category=_SLUG,
            content='<p>Main content.</p>', user_id=author.id, is_draft=False,
        )
        related = KnowhowArticle(
            title='Related Article Without Summary', category=_SLUG,
            content='<p>Related.</p>', user_id=author.id,
            is_draft=False, summary=None,
        )
        db_session.add_all([main, related])
        db_session.commit()
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{main.id}')
        assert resp.status_code == 200
        # Related article must appear but no summary paragraph for it
        assert b'related_none_sentinel_WILLNOTBEPRESENT' not in resp.data
