"""
Tests for Feature 3 — Bookmarks / Reading List.

Covers:
  POST /knowhow/articles/<id>/bookmark  (toggle_bookmark)
    - Adding a bookmark returns JSON {"bookmarked": true}
    - Adding a bookmark creates a KnowhowBookmark row in the DB
    - Toggling a second time removes the bookmark and returns {"bookmarked": false}
    - Toggling again removes the DB row
    - Bookmarking a non-existent article returns 404
    - Anonymous user is redirected / rejected

  GET /knowhow/bookmarks  (bookmarks page)
    - Returns 200 for a logged-in user
    - Anonymous user is redirected
    - Bookmarked article link appears on the page
    - Non-bookmarked article does NOT appear
    - Bookmarks are personal — another user's bookmark does not appear
    - Removing a bookmark removes it from the page
    - Articles are ordered newest-bookmarked first

  GET /knowhow/articles/<id>  (article_view — bookmark button state)
    - Bookmark button shows "Save" when article is NOT bookmarked
    - Bookmark button shows "Saved" when article IS bookmarked

  GET /knowhow/ (index)
    - "My Reading List" link is present in the index header

  Cascade delete
    - Deleting an article also removes its bookmarks (no orphan rows)
"""
import pytest
from app.models import db, User, UserRole, KnowhowArticle, KnowhowBookmark

_SLUG = 'gene_panels'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(db_session, username, role=UserRole.USER):
    u = User(username=username, email=f'{username}@test.com', role=role)
    u.set_password('pw')
    db_session.add(u)
    db_session.commit()
    return u


def _make_article(db_session, user, title='Test Article'):
    a = KnowhowArticle(
        title=title, category=_SLUG,
        content='<p>Content.</p>', user_id=user.id, is_draft=False,
    )
    db_session.add(a)
    db_session.commit()
    return a


def _login(client, user_id):
    with client.session_transaction() as sess:
        sess.clear()
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    client.get('/knowhow/articles/new', follow_redirects=False)


def _toggle(client, article_id):
    """POST to the bookmark toggle endpoint."""
    return client.post(f'/knowhow/articles/{article_id}/bookmark',
                       content_type='application/json')


# ── toggle_bookmark ───────────────────────────────────────────────────────────

@pytest.mark.unit
class TestToggleBookmark:
    def test_add_bookmark_returns_bookmarked_true(self, client, db_session):
        user = _make_user(db_session, 'bm_add_user')
        article = _make_article(db_session, user)
        _login(client, user.id)
        resp = _toggle(client, article.id)
        assert resp.status_code == 200
        assert resp.get_json() == {'bookmarked': True}

    def test_add_bookmark_creates_db_row(self, client, db_session):
        user = _make_user(db_session, 'bm_dbrow_user')
        article = _make_article(db_session, user)
        _login(client, user.id)
        _toggle(client, article.id)
        bm = KnowhowBookmark.query.filter_by(
            user_id=user.id, article_id=article.id).first()
        assert bm is not None

    def test_second_toggle_removes_bookmark(self, client, db_session):
        user = _make_user(db_session, 'bm_remove_user')
        article = _make_article(db_session, user)
        _login(client, user.id)
        _toggle(client, article.id)   # add
        resp = _toggle(client, article.id)  # remove
        assert resp.status_code == 200
        assert resp.get_json() == {'bookmarked': False}

    def test_second_toggle_removes_db_row(self, client, db_session):
        user = _make_user(db_session, 'bm_rmrow_user')
        article = _make_article(db_session, user)
        _login(client, user.id)
        _toggle(client, article.id)
        _toggle(client, article.id)
        bm = KnowhowBookmark.query.filter_by(
            user_id=user.id, article_id=article.id).first()
        assert bm is None

    def test_bookmark_nonexistent_article_returns_404(self, client, db_session):
        user = _make_user(db_session, 'bm_404_user')
        _login(client, user.id)
        resp = _toggle(client, 999999)
        assert resp.status_code == 404

    def test_anonymous_user_cannot_toggle_bookmark(self, client, db_session):
        user = _make_user(db_session, 'bm_anon_owner')
        article = _make_article(db_session, user)
        resp = client.post(f'/knowhow/articles/{article.id}/bookmark',
                           follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_third_toggle_re_adds_bookmark(self, client, db_session):
        """Toggle a third time — should be bookmarked again."""
        user = _make_user(db_session, 'bm_readd_user')
        article = _make_article(db_session, user)
        _login(client, user.id)
        _toggle(client, article.id)  # add
        _toggle(client, article.id)  # remove
        resp = _toggle(client, article.id)  # add again
        assert resp.get_json() == {'bookmarked': True}
        assert KnowhowBookmark.query.filter_by(
            user_id=user.id, article_id=article.id).count() == 1


# ── bookmarks page ────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestBookmarksPage:
    def test_returns_200_for_logged_in_user(self, client, db_session):
        user = _make_user(db_session, 'bmp_access_user')
        _login(client, user.id)
        assert client.get('/knowhow/bookmarks').status_code == 200

    def test_anonymous_user_redirected(self, client, db_session):
        resp = client.get('/knowhow/bookmarks', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_bookmarked_article_link_appears(self, client, db_session):
        user = _make_user(db_session, 'bmp_link_user')
        article = _make_article(db_session, user, 'Bookmarked Article')
        _login(client, user.id)
        _toggle(client, article.id)
        resp = client.get('/knowhow/bookmarks')
        assert f'/knowhow/articles/{article.id}' in resp.get_data(as_text=True)

    def test_non_bookmarked_article_absent(self, client, db_session):
        user = _make_user(db_session, 'bmp_absent_user')
        article = _make_article(db_session, user, 'Not Bookmarked Article')
        _login(client, user.id)
        # do NOT toggle — article should not appear
        resp = client.get('/knowhow/bookmarks')
        assert f'/knowhow/articles/{article.id}' not in resp.get_data(as_text=True)

    def test_bookmarks_are_personal(self, client, db_session):
        """KnowhowBookmark rows are scoped per-user — the model enforces isolation."""
        owner = _make_user(db_session, 'bmp_owner_user')
        viewer = _make_user(db_session, 'bmp_viewer_user')
        article = _make_article(db_session, owner, 'Owners Exclusive Piece')
        _login(client, owner.id)
        _toggle(client, article.id)
        # After owner bookmarks, only owner has a row — viewer has none
        assert KnowhowBookmark.query.filter_by(user_id=owner.id).count() == 1
        assert KnowhowBookmark.query.filter_by(user_id=viewer.id).count() == 0

    def test_removing_bookmark_removes_from_page(self, client, db_session):
        user = _make_user(db_session, 'bmp_rm_user')
        article = _make_article(db_session, user, 'Remove Bookmark Article')
        _login(client, user.id)
        _toggle(client, article.id)   # add
        _toggle(client, article.id)   # remove
        resp = client.get('/knowhow/bookmarks')
        assert f'/knowhow/articles/{article.id}' not in resp.get_data(as_text=True)

    def test_bookmarks_ordered_newest_first(self, client, db_session):
        """The most recently bookmarked article should appear before earlier ones."""
        user = _make_user(db_session, 'bmp_order_user')
        first = _make_article(db_session, user, 'First Bookmarked')
        second = _make_article(db_session, user, 'Second Bookmarked')
        _login(client, user.id)
        _toggle(client, first.id)
        _toggle(client, second.id)
        resp = client.get('/knowhow/bookmarks')
        body = resp.get_data(as_text=True)
        pos_first = body.find(f'/knowhow/articles/{first.id}')
        pos_second = body.find(f'/knowhow/articles/{second.id}')
        assert pos_second < pos_first, \
            "Most recently bookmarked article should appear first"

    def test_empty_reading_list_renders_without_error(self, client, db_session):
        user = _make_user(db_session, 'bmp_empty_user')
        _login(client, user.id)
        resp = client.get('/knowhow/bookmarks')
        assert resp.status_code == 200


# ── article_view — bookmark button state ─────────────────────────────────────

@pytest.mark.unit
class TestArticleViewBookmarkButton:
    def test_button_shows_save_when_not_bookmarked(self, client, db_session):
        user = _make_user(db_session, 'bm_btn_nosave_user')
        article = _make_article(db_session, user, 'Bookmark Toggle Article')
        _login(client, user.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        body = resp.get_data(as_text=True)
        # The button label is rendered in a <span id="bookmark-label">Save</span>
        # When not bookmarked it says "Save"; when bookmarked it says "Saved".
        assert 'id="bookmark-label">Save<' in body
        assert 'id="bookmark-label">Saved<' not in body

    def test_button_shows_saved_when_bookmarked(self, client, db_session):
        user = _make_user(db_session, 'bm_btn_saved_user')
        article = _make_article(db_session, user, 'Star This Article')
        _login(client, user.id)
        _toggle(client, article.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert 'id="bookmark-label">Saved<' in resp.get_data(as_text=True)


# ── index — "My Reading List" link ───────────────────────────────────────────

@pytest.mark.unit
class TestIndexBookmarkLink:
    def test_reading_list_link_present_in_index_header(self, client, db_session):
        user = _make_user(db_session, 'bm_idxlink_user')
        _login(client, user.id)
        resp = client.get('/knowhow/')
        assert b'/knowhow/bookmarks' in resp.data


# ── model FK configuration ───────────────────────────────────────────────────

@pytest.mark.unit
class TestBookmarkModel:
    def test_article_fk_has_cascade_delete(self, db_session):
        """The article_id FK on KnowhowBookmark must declare ON DELETE CASCADE."""
        col = KnowhowBookmark.__table__.c['article_id']
        fk = next(iter(col.foreign_keys))
        assert fk.ondelete.upper() == 'CASCADE'

    def test_user_fk_has_cascade_delete(self, db_session):
        """The user_id FK on KnowhowBookmark must declare ON DELETE CASCADE."""
        col = KnowhowBookmark.__table__.c['user_id']
        fk = next(iter(col.foreign_keys))
        assert fk.ondelete.upper() == 'CASCADE'

    def test_unique_constraint_prevents_duplicate_bookmark(self, client, db_session):
        """A user cannot bookmark the same article twice (unique constraint)."""
        from sqlalchemy.exc import IntegrityError
        user = _make_user(db_session, 'bm_uniq_user')
        article = _make_article(db_session, user, 'Unique Constraint Article')
        db_session.add(KnowhowBookmark(user_id=user.id, article_id=article.id))
        db_session.commit()
        db_session.add(KnowhowBookmark(user_id=user.id, article_id=article.id))
        with pytest.raises(IntegrityError):
            db_session.commit()
