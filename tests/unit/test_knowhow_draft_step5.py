"""
Tests for Feature 5 Step 5 — "My Drafts" shortcut page.

Covers:
  GET /knowhow/drafts
    - Returns 200 for any logged-in user
    - Regular USER sees only their own drafts (not other users' drafts)
    - Regular USER does NOT see published articles on this page
    - EDITOR sees all users' drafts
    - ADMIN sees all users' drafts
    - Page contains a link to each visible draft article
    - Page is empty (no article links) when the user has no drafts

  GET /knowhow/ (index)
    - "My Drafts" link appears in the header when the current user has at least
      one draft article
    - "My Drafts" link is absent when the current user has no drafts

  Titles deliberately avoid the word "draft" so assertions are not triggered
  by content text.
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


def _make_article(db_session, user, title, is_draft):
    assert 'draft' not in title.lower(), \
        "Titles must not contain 'draft' to avoid false positives"
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
    # Seeds the gene_panels category
    client.get('/knowhow/articles/new', follow_redirects=False)


# ── GET /knowhow/drafts — access and content ──────────────────────────────────

@pytest.mark.unit
class TestDraftsPageAccess:
    """Basic access to GET /knowhow/drafts."""

    def test_drafts_page_returns_200_for_logged_in_user(self, client, db_session):
        user = _make_user(db_session, 'dp_access_user')
        _login(client, user.id)
        resp = client.get('/knowhow/drafts')
        assert resp.status_code == 200

    def test_drafts_page_redirects_anonymous_user(self, client, db_session):
        """Unauthenticated visitors should be redirected (login required)."""
        resp = client.get('/knowhow/drafts', follow_redirects=False)
        assert resp.status_code in (302, 401)


@pytest.mark.unit
class TestDraftsPageContent:
    """Content rules for GET /knowhow/drafts."""

    def test_user_sees_own_unpublished_article(self, client, db_session):
        """A USER's own unpublished article must appear on their drafts page."""
        author = _make_user(db_session, 'dp_own_author')
        article = _make_article(db_session, author, 'Unpublished Piece A', is_draft=True)

        _login(client, author.id)
        resp = client.get('/knowhow/drafts')

        assert resp.status_code == 200
        assert f'/knowhow/articles/{article.id}' in resp.get_data(as_text=True)

    def test_user_cannot_see_other_users_unpublished_article(self, client, db_session):
        """A USER must not see another user's unpublished article on the drafts page."""
        author = _make_user(db_session, 'dp_other_author')
        viewer = _make_user(db_session, 'dp_viewer')
        article = _make_article(db_session, author, 'Other Authors Unpublished', is_draft=True)

        _login(client, viewer.id)
        resp = client.get('/knowhow/drafts')

        assert resp.status_code == 200
        assert f'/knowhow/articles/{article.id}' not in resp.get_data(as_text=True)

    def test_published_articles_not_shown_on_drafts_page(self, client, db_session):
        """Published articles must not appear on the drafts page."""
        author = _make_user(db_session, 'dp_pub_author')
        published = _make_article(db_session, author, 'Live Published Piece', is_draft=False)

        _login(client, author.id)
        resp = client.get('/knowhow/drafts')

        assert resp.status_code == 200
        assert f'/knowhow/articles/{published.id}' not in resp.get_data(as_text=True)

    def test_editor_sees_all_users_unpublished_articles(self, client, db_session):
        """An EDITOR must see all users' unpublished articles on the drafts page."""
        author = _make_user(db_session, 'dp_ed_author')
        editor = _make_user(db_session, 'dp_editor', role=UserRole.EDITOR)
        article = _make_article(db_session, author, 'Unpublished Piece B', is_draft=True)

        _login(client, editor.id)
        resp = client.get('/knowhow/drafts')

        assert resp.status_code == 200
        assert f'/knowhow/articles/{article.id}' in resp.get_data(as_text=True)

    def test_admin_sees_all_users_unpublished_articles(self, client, db_session):
        """An ADMIN must see all users' unpublished articles on the drafts page."""
        author = _make_user(db_session, 'dp_adm_author')
        admin = _make_user(db_session, 'dp_admin', role=UserRole.ADMIN)
        article = _make_article(db_session, author, 'Unpublished Piece C', is_draft=True)

        _login(client, admin.id)
        resp = client.get('/knowhow/drafts')

        assert resp.status_code == 200
        assert f'/knowhow/articles/{article.id}' in resp.get_data(as_text=True)

    def test_no_article_links_when_user_has_no_drafts(self, client, db_session):
        """Drafts page is empty (no article links) when the user has no unpublished articles."""
        user = _make_user(db_session, 'dp_empty_user')
        _make_article(db_session, user, 'Only Live Piece', is_draft=False)

        _login(client, user.id)
        resp = client.get('/knowhow/drafts')
        body = resp.get_data(as_text=True)

        assert resp.status_code == 200
        # No article view links should appear
        assert '/knowhow/articles/' not in body

    def test_multiple_own_drafts_all_appear(self, client, db_session):
        """All of a user's own unpublished articles must appear on the drafts page."""
        author = _make_user(db_session, 'dp_multi_author')
        a1 = _make_article(db_session, author, 'Unpublished Multi One', is_draft=True)
        a2 = _make_article(db_session, author, 'Unpublished Multi Two', is_draft=True)

        _login(client, author.id)
        resp = client.get('/knowhow/drafts')
        body = resp.get_data(as_text=True)

        assert f'/knowhow/articles/{a1.id}' in body
        assert f'/knowhow/articles/{a2.id}' in body


# ── GET /knowhow/ — "My Drafts" link in the index header ─────────────────────

@pytest.mark.unit
class TestIndexMyDraftsLink:
    """The index header shows a 'My Drafts' link only when the user has drafts."""

    def _drafts_link_present(self, resp):
        body = resp.get_data(as_text=True)
        return '/knowhow/drafts' in body

    def test_drafts_link_shown_when_user_has_own_draft(self, client, db_session):
        """Index header must contain a link to /knowhow/drafts when the user has at least one draft."""
        author = _make_user(db_session, 'il_link_author')
        _make_article(db_session, author, 'Unpublished Index Piece', is_draft=True)

        _login(client, author.id)
        resp = client.get('/knowhow/')

        assert self._drafts_link_present(resp), \
            "Expected a link to /knowhow/drafts in the index when the user has a draft"

    def test_drafts_link_absent_when_user_has_no_drafts(self, client, db_session):
        """Index header must NOT contain a link to /knowhow/drafts when user has no drafts."""
        author = _make_user(db_session, 'il_nolink_author')
        _make_article(db_session, author, 'Live Only Piece', is_draft=False)

        _login(client, author.id)
        resp = client.get('/knowhow/')

        assert not self._drafts_link_present(resp), \
            "Did not expect /knowhow/drafts link in the index when user has no drafts"

    def test_drafts_link_absent_when_user_has_no_articles(self, client, db_session):
        """Index header must NOT contain a link to /knowhow/drafts when user has no articles at all."""
        user = _make_user(db_session, 'il_none_user')

        _login(client, user.id)
        resp = client.get('/knowhow/')

        assert not self._drafts_link_present(resp)
