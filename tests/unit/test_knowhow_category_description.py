"""
Tests for Feature 9 — Category Description Display.

Covers:
  GET /knowhow/category/<slug>  (category page — description block rendering)
    - Description block shown when category has a non-null description
    - Description block hidden when category description is None
    - Exact description text is rendered verbatim
    - Header (label) renders regardless of whether description is set

  POST /knowhow/admin/categories  (create_category — description persistence)
    - Creating a category with a description persists it to the DB
    - Creating a category without a description stores None
    - Whitespace-only description is stripped and stored as None

  POST /knowhow/admin/categories/<id>/edit  (update_category — description editing)
    - Updating a category sets a new description
    - Submitting empty description clears it (stores None)
    - Other fields (slug, label) are unchanged when only description is updated

  Model: KnowhowCategory
    - description field is nullable (None accepted without error)
    - description persists long text values (Text column, no length cap)
"""
import pytest
from app.models import db, User, UserRole, KnowhowCategory

_VALID_COLOR = '#0369a1'   # First entry in PALETTE, guaranteed valid


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(db_session, username, role=UserRole.USER):
    u = User(username=username, email=f'{username}@test.com', role=role)
    u.set_password('pw')
    db_session.add(u)
    db_session.commit()
    return u


def _make_category(db_session, slug, label='Test Category',
                   description=None, color=_VALID_COLOR, position=0):
    c = KnowhowCategory(slug=slug, label=label, color=color,
                        description=description, position=position)
    db_session.add(c)
    db_session.commit()
    return c


def _login(client, user_id):
    with client.session_transaction() as sess:
        sess.clear()
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    client.get('/knowhow/articles/new', follow_redirects=False)


# ── Category page — description rendering ─────────────────────────────────────

@pytest.mark.unit
class TestCategoryDescriptionDisplay:

    def test_description_shown_when_set(self, client, db_session):
        """Category page renders the description when it has a non-null value."""
        author = _make_user(db_session, 'cat_desc_shown_author')
        cat = _make_category(db_session, 'cat_desc_shown',
                             description='A helpful description sentinel')
        _login(client, author.id)
        resp = client.get(f'/knowhow/category/{cat.slug}')
        assert resp.status_code == 200
        assert b'A helpful description sentinel' in resp.data

    def test_description_block_hidden_when_null(self, client, db_session):
        """No description block is rendered when category.description is None."""
        author = _make_user(db_session, 'cat_desc_null_author')
        cat = _make_category(db_session, 'cat_desc_null', description=None)
        _login(client, author.id)
        resp = client.get(f'/knowhow/category/{cat.slug}')
        assert resp.status_code == 200
        # The template only renders the description div inside {% if category.description %}
        assert b'text-gray-600 italic' not in resp.data

    def test_description_text_rendered_verbatim(self, client, db_session):
        """The exact stored description text appears unchanged on the category page."""
        author = _make_user(db_session, 'cat_desc_verbatim_author')
        text = 'Use this category for variant classification workflows.'
        cat = _make_category(db_session, 'cat_desc_verbatim', description=text)
        _login(client, author.id)
        resp = client.get(f'/knowhow/category/{cat.slug}')
        assert resp.status_code == 200
        assert text.encode() in resp.data

    def test_category_label_renders_regardless_of_description(self, client, db_session):
        """The coloured header with the category label always renders, with or without description."""
        author = _make_user(db_session, 'cat_header_author')
        cat = _make_category(db_session, 'cat_header_slug',
                             label='Header Only Category', description=None)
        _login(client, author.id)
        resp = client.get(f'/knowhow/category/{cat.slug}')
        assert resp.status_code == 200
        assert b'Header Only Category' in resp.data

    def test_description_not_shown_for_category_with_none(self, client, db_session):
        """Viewing a no-description category doesn't bleed description content onto the page."""
        author = _make_user(db_session, 'cat_no_bleed_author')
        cat = _make_category(db_session, 'cat_no_bleed_slug',
                             label='No Description Cat', description=None)
        _login(client, author.id)
        resp = client.get(f'/knowhow/category/{cat.slug}')
        assert resp.status_code == 200
        assert b'No Description Cat' in resp.data   # header rendered
        assert b'bg-gray-50 border-b border-gray-200 text-sm text-gray-600 italic' not in resp.data


# ── Admin: create category with description ───────────────────────────────────

@pytest.mark.unit
class TestAdminCreateCategoryDescription:

    def test_create_category_with_description_persists(self, client, db_session):
        """POSTing a description when creating a category saves it to the DB."""
        admin = _make_user(db_session, 'cat_create_desc_admin', role=UserRole.ADMIN)
        _login(client, admin.id)
        resp = client.post('/knowhow/admin/categories', data={
            'label': 'Created With Desc',
            'slug': 'created_with_desc',
            'color': _VALID_COLOR,
            'description': 'Created description sentinel',
        }, follow_redirects=False)
        assert resp.status_code == 302
        cat = KnowhowCategory.query.filter_by(slug='created_with_desc').first()
        assert cat is not None
        assert cat.description == 'Created description sentinel'

    def test_create_category_without_description_stores_none(self, client, db_session):
        """Omitting description when creating a category stores None."""
        admin = _make_user(db_session, 'cat_create_nodesc_admin', role=UserRole.ADMIN)
        _login(client, admin.id)
        resp = client.post('/knowhow/admin/categories', data={
            'label': 'Created No Desc',
            'slug': 'created_no_desc',
            'color': _VALID_COLOR,
        }, follow_redirects=False)
        assert resp.status_code == 302
        cat = KnowhowCategory.query.filter_by(slug='created_no_desc').first()
        assert cat is not None
        assert cat.description is None

    def test_create_category_whitespace_description_stored_as_none(self, client, db_session):
        """A whitespace-only description is stripped to '' then stored as None."""
        admin = _make_user(db_session, 'cat_create_ws_admin', role=UserRole.ADMIN)
        _login(client, admin.id)
        resp = client.post('/knowhow/admin/categories', data={
            'label': 'Created Whitespace Desc',
            'slug': 'created_ws_desc',
            'color': _VALID_COLOR,
            'description': '   ',
        }, follow_redirects=False)
        assert resp.status_code == 302
        cat = KnowhowCategory.query.filter_by(slug='created_ws_desc').first()
        assert cat is not None
        assert cat.description is None

    def test_create_category_requires_admin_role(self, client, db_session):
        """A regular user POSTing to create_category receives 403."""
        user = _make_user(db_session, 'cat_create_nonadmin', role=UserRole.USER)
        _login(client, user.id)
        resp = client.post('/knowhow/admin/categories', data={
            'label': 'Should Fail',
            'slug': 'should_fail',
            'color': _VALID_COLOR,
        }, follow_redirects=False)
        assert resp.status_code == 403


# ── Admin: update category description ────────────────────────────────────────

@pytest.mark.unit
class TestAdminUpdateCategoryDescription:

    def test_update_category_sets_description(self, client, db_session):
        """POSTing to update route with a description saves it on the category."""
        admin = _make_user(db_session, 'cat_update_desc_admin', role=UserRole.ADMIN)
        cat = _make_category(db_session, 'cat_update_slug', description=None)
        _login(client, admin.id)
        resp = client.post(f'/knowhow/admin/categories/{cat.id}/edit', data={
            'label': 'Updated Label',
            'color': _VALID_COLOR,
            'description': 'Updated description sentinel',
            'position': '0',
        }, follow_redirects=False)
        assert resp.status_code == 302
        db_session.refresh(cat)
        assert cat.description == 'Updated description sentinel'

    def test_update_category_clears_description(self, client, db_session):
        """Submitting empty description via update route clears the existing description."""
        admin = _make_user(db_session, 'cat_clear_desc_admin', role=UserRole.ADMIN)
        cat = _make_category(db_session, 'cat_clear_slug',
                             description='Old description to be cleared')
        _login(client, admin.id)
        resp = client.post(f'/knowhow/admin/categories/{cat.id}/edit', data={
            'label': 'Cleared Desc Label',
            'color': _VALID_COLOR,
            'description': '',
            'position': '0',
        }, follow_redirects=False)
        assert resp.status_code == 302
        db_session.refresh(cat)
        assert cat.description is None

    def test_update_category_slug_unchanged(self, client, db_session):
        """The update route does not accept or alter the slug field."""
        admin = _make_user(db_session, 'cat_slug_unchanged_admin', role=UserRole.ADMIN)
        cat = _make_category(db_session, 'cat_slug_unchanged',
                             label='Slug Unchanged', description=None)
        _login(client, admin.id)
        client.post(f'/knowhow/admin/categories/{cat.id}/edit', data={
            'label': 'Slug Unchanged',
            'color': _VALID_COLOR,
            'description': 'New description',
            'position': '0',
        }, follow_redirects=False)
        db_session.refresh(cat)
        assert cat.slug == 'cat_slug_unchanged'
        assert cat.description == 'New description'

    def test_update_category_requires_admin_role(self, client, db_session):
        """A regular user POSTing to update_category receives 403."""
        admin = _make_user(db_session, 'cat_update_owner', role=UserRole.ADMIN)
        cat = _make_category(db_session, 'cat_update_blocked_slug')
        user = _make_user(db_session, 'cat_update_blocked_user', role=UserRole.USER)
        _login(client, user.id)
        resp = client.post(f'/knowhow/admin/categories/{cat.id}/edit', data={
            'label': 'Should Fail',
            'color': _VALID_COLOR,
            'description': 'Blocked',
            'position': '0',
        }, follow_redirects=False)
        assert resp.status_code == 403


# ── Model: KnowhowCategory.description ───────────────────────────────────────

@pytest.mark.unit
class TestKnowhowCategoryDescriptionModel:

    def test_description_nullable(self, db_session):
        """KnowhowCategory.description accepts None without any DB error."""
        cat = KnowhowCategory(
            slug='model_null_desc', label='Nullable Test',
            color=_VALID_COLOR, description=None, position=0,
        )
        db_session.add(cat)
        db_session.commit()
        fetched = KnowhowCategory.query.filter_by(slug='model_null_desc').first()
        assert fetched is not None
        assert fetched.description is None

    def test_description_persists_long_text(self, db_session):
        """A long description is fully stored and retrieved (Text column, no cap)."""
        long_text = 'Use this category for variant classification workflows. ' * 20
        cat = KnowhowCategory(
            slug='model_long_desc', label='Long Text Test',
            color=_VALID_COLOR, description=long_text, position=0,
        )
        db_session.add(cat)
        db_session.commit()
        fetched = KnowhowCategory.query.filter_by(slug='model_long_desc').first()
        assert fetched.description == long_text

    def test_description_update_reflects_in_db(self, db_session):
        """Mutating description on a persisted object and committing updates the DB."""
        cat = KnowhowCategory(
            slug='model_update_desc', label='Update Test',
            color=_VALID_COLOR, description='Original', position=0,
        )
        db_session.add(cat)
        db_session.commit()
        cat.description = 'Mutated'
        db_session.commit()
        fetched = KnowhowCategory.query.filter_by(slug='model_update_desc').first()
        assert fetched.description == 'Mutated'
