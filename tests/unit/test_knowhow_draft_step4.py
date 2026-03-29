"""
Tests for Feature 5 Step 4 — DRAFT badges and banners in templates.

Covers:
  article_view.html
    - A prominent DRAFT badge appears next to the article title when is_draft=True
    - No DRAFT badge when is_draft=False
    - An author-facing "not yet public" banner is shown on a draft article view
    - The banner is NOT shown on a published article

  index.html (article cards)
    - A small DRAFT label appears on a draft article card visible to the author
    - No DRAFT label on a published article card

  category.html (article cards)
    - A small DRAFT label appears on a draft article card visible to the author
    - No DRAFT label on a published article card

All tests inspect the rendered HTML for the presence / absence of a known
sentinel string that the template must render.  Titles deliberately avoid the
word "draft" so that only explicit template elements trigger the assertions.
The exact CSS classes are left to the implementation; tests check for the text
"DRAFT" (uppercase) rendered by the template as a badge / label.
"""
import pytest
from app.models import db, User, UserRole, KnowhowArticle

_SLUG = 'gene_panels'
# Sentinel: templates must render this exact string for draft articles.
# Titles below are chosen to NOT contain this word, so the only match must
# come from a badge / label element added by Step 4.
_BADGE = 'DRAFT'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(db_session, username, role=UserRole.USER):
    u = User(username=username, email=f'{username}@test.com', role=role)
    u.set_password('pw')
    db_session.add(u)
    db_session.commit()
    return u


def _make_article(db_session, user, title, is_draft):
    """Create an article.  Titles must NOT contain 'draft' (any case)."""
    assert 'draft' not in title.lower(), \
        "Test titles must not contain 'draft' to avoid false positives"
    a = KnowhowArticle(
        title=title, category=_SLUG,
        content=f'<p>{title}</p>',
        user_id=user.id, is_draft=is_draft,
    )
    db_session.add(a)
    db_session.commit()
    return a


def _login(client, user_id):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    client.get('/knowhow/articles/new', follow_redirects=False)  # seeds categories


def _has_badge(response):
    return _BADGE in response.get_data(as_text=True)


# ── article_view.html ─────────────────────────────────────────────────────────

@pytest.mark.unit
class TestArticleViewDraftBadge:
    """GET /knowhow/articles/<id> — DRAFT badge and banner."""

    def test_draft_badge_shown_on_draft_article(self, client, db_session):
        """A DRAFT badge must appear in the article view when is_draft=True."""
        author = _make_user(db_session, 'av_badge_author')
        article = _make_article(db_session, author, 'Unpublished Piece', is_draft=True)

        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')

        assert resp.status_code == 200
        assert _has_badge(resp), \
            f"Expected '{_BADGE}' badge text in article view for a draft article"

    def test_draft_badge_absent_on_published_article(self, client, db_session):
        """No DRAFT badge should appear when is_draft=False."""
        author = _make_user(db_session, 'av_nobadge_author')
        article = _make_article(db_session, author, 'Live Piece', is_draft=False)

        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')

        assert resp.status_code == 200
        assert not _has_badge(resp), \
            f"'{_BADGE}' badge text must NOT appear for a published article"

    def test_not_public_banner_shown_to_author_on_draft(self, client, db_session):
        """The author must see a 'not yet public' style banner on their draft."""
        author = _make_user(db_session, 'av_banner_author')
        article = _make_article(db_session, author, 'Hidden Piece', is_draft=True)

        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')

        assert resp.status_code == 200
        body = resp.get_data(as_text=True).lower()
        # Any of these phrases satisfies the "not yet public" banner requirement
        assert ('not yet public' in body
                or 'not visible' in body
                or 'only you' in body
                or 'only visible to you' in body
                or 'not published' in body), \
            "Author should see a banner warning that the article is not yet public"

    def test_not_public_banner_absent_on_published(self, client, db_session):
        """No 'not yet public' banner should show on a published article."""
        author = _make_user(db_session, 'av_no_banner_author')
        article = _make_article(db_session, author, 'Public Piece', is_draft=False)

        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')

        assert resp.status_code == 200
        body = resp.get_data(as_text=True).lower()
        assert 'not yet public' not in body
        assert 'not published' not in body


# ── index.html article cards ──────────────────────────────────────────────────

@pytest.mark.unit
class TestIndexDraftLabel:
    """GET /knowhow/ — DRAFT label on article cards."""

    def test_draft_label_shown_on_own_draft_card(self, client, db_session):
        """Author sees a DRAFT label on their own draft article card in the index."""
        author = _make_user(db_session, 'idx_label_author')
        article = _make_article(db_session, author, 'Unpublished Index Piece', is_draft=True)

        _login(client, author.id)
        resp = client.get('/knowhow/')

        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        # The article link must be present AND the DRAFT label must appear
        assert f'/knowhow/articles/{article.id}' in body, \
            "Draft article link should appear in the index for its own author"
        assert _has_badge(resp), \
            f"Expected '{_BADGE}' label text on the draft article card in the index"

    def test_draft_label_absent_on_published_card(self, client, db_session):
        """No DRAFT label on a published article card in the index."""
        author = _make_user(db_session, 'idx_nolabel_author')
        _make_article(db_session, author, 'Live Index Piece', is_draft=False)

        _login(client, author.id)
        resp = client.get('/knowhow/')

        assert resp.status_code == 200
        assert not _has_badge(resp), \
            f"'{_BADGE}' label must NOT appear for a published article card in the index"


# ── category.html article cards ───────────────────────────────────────────────

@pytest.mark.unit
class TestCategoryDraftLabel:
    """GET /knowhow/category/<slug> — DRAFT label on article cards."""

    def test_draft_label_shown_on_own_draft_card(self, client, db_session):
        """Author sees a DRAFT label on their own draft article card in category view."""
        author = _make_user(db_session, 'cat_label_author')
        article = _make_article(db_session, author, 'Unpublished Category Piece', is_draft=True)

        _login(client, author.id)
        resp = client.get(f'/knowhow/category/{_SLUG}')

        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert f'/knowhow/articles/{article.id}' in body, \
            "Draft article link should appear in the category for its own author"
        assert _has_badge(resp), \
            f"Expected '{_BADGE}' label text on the draft article card in the category"

    def test_draft_label_absent_on_published_card(self, client, db_session):
        """No DRAFT label on a published article card in the category view."""
        author = _make_user(db_session, 'cat_nolabel_author')
        _make_article(db_session, author, 'Live Category Piece', is_draft=False)

        _login(client, author.id)
        resp = client.get(f'/knowhow/category/{_SLUG}')

        assert resp.status_code == 200
        assert not _has_badge(resp), \
            f"'{_BADGE}' label must NOT appear for a published article card in the category"
