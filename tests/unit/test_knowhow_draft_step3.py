"""
Tests for Feature 5 Step 3 — Filter draft articles out of list routes.

The _draft_filter() helper must be applied to four routes:
  GET /knowhow/          → index()        — all_articles query
  GET /knowhow/category/<slug>            → category()   — articles query
  GET /knowhow/search?q=<term>            → search()     — articles query
  GET /knowhow/tags/<label>               → tag_articles() — tag.articles query

Rules under test:
  - Regular users (USER role) do NOT see other users' drafts.
  - Regular users DO see their own drafts.
  - EDITOR / ADMIN users see ALL articles, including other users' drafts.
  - Published articles are visible to everyone on all four routes.

All tests use the HTTP test client and inspect the rendered HTML for article
titles, so they exercise the full template stack.
"""
import pytest
from app.models import db, User, UserRole, KnowhowArticle, KnowhowTag

# Default slug guaranteed to exist after _seed_categories() runs.
_SLUG = 'gene_panels'


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_user(db_session, username, role=UserRole.USER):
    u = User(username=username, email=f'{username}@test.com', role=role)
    u.set_password('pw')
    db_session.add(u)
    db_session.commit()
    return u


def _make_article(db_session, user, title, is_draft, tag_label=None):
    a = KnowhowArticle(
        title=title,
        category=_SLUG,
        content=f'<p>{title}</p>',
        user_id=user.id,
        is_draft=is_draft,
    )
    db_session.add(a)
    db_session.flush()
    if tag_label:
        tag = KnowhowTag.query.filter_by(label=tag_label).first()
        if tag is None:
            tag = KnowhowTag(label=tag_label)
            db_session.add(tag)
            db_session.flush()
        a.tags.append(tag)
    db_session.commit()
    return a


def _login(client, user_id):
    """Inject a Flask-Login session directly."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    # Trigger _seed_categories() so default slugs exist.
    client.get('/knowhow/articles/new', follow_redirects=False)


# ── index() ──────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestIndexDraftFilter:
    """GET /knowhow/ filters drafts correctly."""

    def test_user_cannot_see_other_users_draft_on_index(self, client, db_session):
        author  = _make_user(db_session, 'idx_author')
        viewer  = _make_user(db_session, 'idx_viewer')
        _make_article(db_session, author, 'Hidden Draft', is_draft=True)
        _make_article(db_session, author, 'Visible Published', is_draft=False)

        _login(client, viewer.id)
        resp = client.get('/knowhow/', follow_redirects=False)

        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'Hidden Draft' not in body
        assert 'Visible Published' in body

    def test_author_sees_own_draft_on_index(self, client, db_session):
        author = _make_user(db_session, 'idx_own_author')
        _make_article(db_session, author, 'My Own Draft', is_draft=True)

        _login(client, author.id)
        resp = client.get('/knowhow/', follow_redirects=False)

        assert resp.status_code == 200
        assert b'My Own Draft' in resp.data

    def test_admin_sees_all_drafts_on_index(self, client, db_session):
        author = _make_user(db_session, 'idx_admin_author')
        admin  = _make_user(db_session, 'idx_admin_user', role=UserRole.ADMIN)
        _make_article(db_session, author, 'Others Draft Admin', is_draft=True)

        _login(client, admin.id)
        resp = client.get('/knowhow/', follow_redirects=False)

        assert resp.status_code == 200
        assert b'Others Draft Admin' in resp.data

    def test_editor_sees_all_drafts_on_index(self, client, db_session):
        author = _make_user(db_session, 'idx_editor_author')
        editor = _make_user(db_session, 'idx_editor_user', role=UserRole.EDITOR)
        _make_article(db_session, author, 'Others Draft Editor', is_draft=True)

        _login(client, editor.id)
        resp = client.get('/knowhow/', follow_redirects=False)

        assert resp.status_code == 200
        assert b'Others Draft Editor' in resp.data


# ── category() ───────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestCategoryDraftFilter:
    """GET /knowhow/category/<slug> filters drafts correctly."""

    def test_user_cannot_see_other_users_draft_in_category(self, client, db_session):
        author = _make_user(db_session, 'cat_author')
        viewer = _make_user(db_session, 'cat_viewer')
        _make_article(db_session, author, 'Cat Hidden Draft', is_draft=True)
        _make_article(db_session, author, 'Cat Visible Published', is_draft=False)

        _login(client, viewer.id)
        resp = client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)

        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'Cat Hidden Draft' not in body
        assert 'Cat Visible Published' in body

    def test_author_sees_own_draft_in_category(self, client, db_session):
        author = _make_user(db_session, 'cat_own_author')
        _make_article(db_session, author, 'Cat My Draft', is_draft=True)

        _login(client, author.id)
        resp = client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)

        assert resp.status_code == 200
        assert b'Cat My Draft' in resp.data

    def test_admin_sees_all_drafts_in_category(self, client, db_session):
        author = _make_user(db_session, 'cat_admin_author')
        admin  = _make_user(db_session, 'cat_admin_user', role=UserRole.ADMIN)
        _make_article(db_session, author, 'Cat Others Draft Admin', is_draft=True)

        _login(client, admin.id)
        resp = client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)

        assert resp.status_code == 200
        assert b'Cat Others Draft Admin' in resp.data

    def test_editor_sees_all_drafts_in_category(self, client, db_session):
        author = _make_user(db_session, 'cat_editor_author')
        editor = _make_user(db_session, 'cat_editor_user', role=UserRole.EDITOR)
        _make_article(db_session, author, 'Cat Others Draft Editor', is_draft=True)

        _login(client, editor.id)
        resp = client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)

        assert resp.status_code == 200
        assert b'Cat Others Draft Editor' in resp.data


# ── search() ─────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSearchDraftFilter:
    """GET /knowhow/search?q=... filters drafts correctly.

    Article titles are highlighted in the template with <mark> tags around the
    matched query term, so we verify results by checking the article URL
    (/knowhow/articles/<id>) which appears unmodified in every result link.
    """

    def test_user_cannot_find_other_users_draft_via_search(self, client, db_session):
        author = _make_user(db_session, 'srch_author')
        viewer = _make_user(db_session, 'srch_viewer')
        draft = _make_article(db_session, author, 'SrchHiddenDraft',   is_draft=True)
        pub   = _make_article(db_session, author, 'SrchVisiblePublish', is_draft=False)

        _login(client, viewer.id)
        resp = client.get('/knowhow/search?q=Srch', follow_redirects=False)

        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert f'/knowhow/articles/{draft.id}' not in body
        assert f'/knowhow/articles/{pub.id}' in body

    def test_author_can_find_own_draft_via_search(self, client, db_session):
        author = _make_user(db_session, 'srch_own_author')
        draft = _make_article(db_session, author, 'SrchOwnDraft', is_draft=True)

        _login(client, author.id)
        resp = client.get('/knowhow/search?q=SrchOwn', follow_redirects=False)

        assert resp.status_code == 200
        assert f'/knowhow/articles/{draft.id}' in resp.get_data(as_text=True)

    def test_admin_can_find_all_drafts_via_search(self, client, db_session):
        author = _make_user(db_session, 'srch_admin_author')
        admin  = _make_user(db_session, 'srch_admin_user', role=UserRole.ADMIN)
        draft = _make_article(db_session, author, 'SrchAdminDraft', is_draft=True)

        _login(client, admin.id)
        resp = client.get('/knowhow/search?q=SrchAdmin', follow_redirects=False)

        assert resp.status_code == 200
        assert f'/knowhow/articles/{draft.id}' in resp.get_data(as_text=True)

    def test_editor_can_find_all_drafts_via_search(self, client, db_session):
        author = _make_user(db_session, 'srch_editor_author')
        editor = _make_user(db_session, 'srch_editor_user', role=UserRole.EDITOR)
        draft = _make_article(db_session, author, 'SrchEditorDraft', is_draft=True)

        _login(client, editor.id)
        resp = client.get('/knowhow/search?q=SrchEditor', follow_redirects=False)

        assert resp.status_code == 200
        assert f'/knowhow/articles/{draft.id}' in resp.get_data(as_text=True)


# ── tag_articles() ───────────────────────────────────────────────────────────

@pytest.mark.unit
class TestTagDraftFilter:
    """GET /knowhow/tags/<label> filters drafts correctly."""

    def test_user_cannot_see_other_users_draft_via_tag(self, client, db_session):
        author = _make_user(db_session, 'tag_author')
        viewer = _make_user(db_session, 'tag_viewer')
        _make_article(db_session, author, 'Tag Hidden Draft', is_draft=True,  tag_label='step3tag')
        _make_article(db_session, author, 'Tag Visible Published', is_draft=False, tag_label='step3tag')

        _login(client, viewer.id)
        resp = client.get('/knowhow/tags/step3tag', follow_redirects=False)

        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'Tag Hidden Draft' not in body
        assert 'Tag Visible Published' in body

    def test_author_sees_own_draft_via_tag(self, client, db_session):
        author = _make_user(db_session, 'tag_own_author')
        _make_article(db_session, author, 'Tag My Own Draft', is_draft=True, tag_label='step3owntag')

        _login(client, author.id)
        resp = client.get('/knowhow/tags/step3owntag', follow_redirects=False)

        assert resp.status_code == 200
        assert b'Tag My Own Draft' in resp.data

    def test_admin_sees_all_drafts_via_tag(self, client, db_session):
        author = _make_user(db_session, 'tag_admin_author')
        admin  = _make_user(db_session, 'tag_admin_user', role=UserRole.ADMIN)
        _make_article(db_session, author, 'Tag Others Draft Admin', is_draft=True, tag_label='step3admintag')

        _login(client, admin.id)
        resp = client.get('/knowhow/tags/step3admintag', follow_redirects=False)

        assert resp.status_code == 200
        assert b'Tag Others Draft Admin' in resp.data

    def test_editor_sees_all_drafts_via_tag(self, client, db_session):
        author = _make_user(db_session, 'tag_editor_author')
        editor = _make_user(db_session, 'tag_editor_user', role=UserRole.EDITOR)
        _make_article(db_session, author, 'Tag Others Draft Editor', is_draft=True, tag_label='step3editortag')

        _login(client, editor.id)
        resp = client.get('/knowhow/tags/step3editortag', follow_redirects=False)

        assert resp.status_code == 200
        assert b'Tag Others Draft Editor' in resp.data
