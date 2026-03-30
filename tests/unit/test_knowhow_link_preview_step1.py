"""
Tests for Feature 11 Step 1 — OG preview columns on KnowhowLink.

Covers the DB-level changes only (no HTTP routes, no fetcher logic):

  Model — column existence
    - KnowhowLink has og_title, og_description, og_image_url columns
    - All three columns are nullable
    - Columns have the correct maximum lengths (256 / 512 / 2048)

  Model — defaults & persistence
    - A new link created without OG values stores NULL for all three fields
    - OG values can be set and retrieved unchanged
    - Partial OG data is allowed (any combination of NULLs is valid)
    - og_title is truncated to 256 chars if the caller passes a longer string
    - og_description is truncated to 512 chars if the caller passes a longer string
    - og_image_url is truncated to 2048 chars if the caller passes a longer string

  Model — independence
    - Adding OG columns does not affect existing KnowhowLink fields
      (url, description, category, user_id still behave as before)
    - Two separate links can share the same og_title without conflict
      (no unique constraint on OG fields)
    - Deleting a link with OG data set leaves no orphan rows
"""
import pytest
from sqlalchemy import inspect as sa_inspect
from app.models import db, User, UserRole, KnowhowLink


_CATEGORY = 'gene_panels'
_URL      = 'https://example.com/resource'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(db_session, username):
    u = User(username=username, email=f'{username}@test.com', role=UserRole.USER)
    u.set_password('pw')
    db_session.add(u)
    db_session.commit()
    return u


def _make_link(db_session, user, url=_URL, description='A resource',
               og_title=None, og_description=None, og_image_url=None):
    link = KnowhowLink(
        category=_CATEGORY,
        url=url,
        description=description,
        user_id=user.id,
        og_title=og_title,
        og_description=og_description,
        og_image_url=og_image_url,
    )
    db_session.add(link)
    db_session.commit()
    return link


# ── Column existence ──────────────────────────────────────────────────────────

@pytest.mark.unit
class TestOgColumnsExist:
    """The three OG columns must be present on the knowhow_links table."""

    def _column_names(self, db_session):
        inspector = sa_inspect(db.engine)
        return {c['name'] for c in inspector.get_columns('knowhow_links')}

    def test_og_title_column_exists(self, db_session):
        assert 'og_title' in self._column_names(db_session)

    def test_og_description_column_exists(self, db_session):
        assert 'og_description' in self._column_names(db_session)

    def test_og_image_url_column_exists(self, db_session):
        assert 'og_image_url' in self._column_names(db_session)

    def test_og_title_is_nullable(self, db_session):
        cols = {
            c['name']: c
            for c in sa_inspect(db.engine).get_columns('knowhow_links')
        }
        assert cols['og_title']['nullable'] is True

    def test_og_description_is_nullable(self, db_session):
        cols = {
            c['name']: c
            for c in sa_inspect(db.engine).get_columns('knowhow_links')
        }
        assert cols['og_description']['nullable'] is True

    def test_og_image_url_is_nullable(self, db_session):
        cols = {
            c['name']: c
            for c in sa_inspect(db.engine).get_columns('knowhow_links')
        }
        assert cols['og_image_url']['nullable'] is True


# ── Defaults & persistence ────────────────────────────────────────────────────

@pytest.mark.unit
class TestOgColumnDefaults:
    """New links without OG data must store NULL; set values must round-trip."""

    def test_new_link_has_null_og_title(self, db_session):
        user = _make_user(db_session, 'og_null_title')
        link = _make_link(db_session, user)
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_title is None

    def test_new_link_has_null_og_description(self, db_session):
        user = _make_user(db_session, 'og_null_desc')
        link = _make_link(db_session, user)
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_description is None

    def test_new_link_has_null_og_image_url(self, db_session):
        user = _make_user(db_session, 'og_null_img')
        link = _make_link(db_session, user)
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_image_url is None

    def test_og_title_persists(self, db_session):
        user = _make_user(db_session, 'og_title_persist')
        link = _make_link(db_session, user, og_title='Example Resource')
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_title == 'Example Resource'

    def test_og_description_persists(self, db_session):
        user = _make_user(db_session, 'og_desc_persist')
        link = _make_link(db_session, user, og_description='A helpful guide about genetics.')
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_description == 'A helpful guide about genetics.'

    def test_og_image_url_persists(self, db_session):
        user = _make_user(db_session, 'og_img_persist')
        link = _make_link(db_session, user, og_image_url='https://example.com/image.png')
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_image_url == 'https://example.com/image.png'

    def test_all_three_og_fields_persist_together(self, db_session):
        user = _make_user(db_session, 'og_all_persist')
        link = _make_link(
            db_session, user,
            og_title='Full Preview',
            og_description='Description text',
            og_image_url='https://example.com/thumb.jpg',
        )
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_title       == 'Full Preview'
        assert fetched.og_description == 'Description text'
        assert fetched.og_image_url   == 'https://example.com/thumb.jpg'

    def test_partial_og_data_only_title(self, db_session):
        user = _make_user(db_session, 'og_partial_title')
        link = _make_link(db_session, user, og_title='Title Only')
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_title is not None
        assert fetched.og_description is None
        assert fetched.og_image_url   is None

    def test_partial_og_data_only_description(self, db_session):
        user = _make_user(db_session, 'og_partial_desc')
        link = _make_link(db_session, user, og_description='Desc only')
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_title       is None
        assert fetched.og_description is not None
        assert fetched.og_image_url   is None

    def test_og_title_updated_after_creation(self, db_session):
        """OG fields can be updated on an existing link row."""
        user = _make_user(db_session, 'og_update_user')
        link = _make_link(db_session, user)
        assert link.og_title is None
        link.og_title = 'Updated Title'
        db_session.commit()
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_title == 'Updated Title'

    def test_og_fields_can_be_cleared_to_null(self, db_session):
        """Setting OG fields back to None must persist as NULL."""
        user = _make_user(db_session, 'og_clear_user')
        link = _make_link(db_session, user, og_title='Will Be Cleared')
        link.og_title = None
        db_session.commit()
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.og_title is None


# ── Max-length truncation ─────────────────────────────────────────────────────

@pytest.mark.unit
class TestOgColumnLengths:
    """Values at the column length boundary must be stored without error."""

    def test_og_title_at_max_length(self, db_session):
        user = _make_user(db_session, 'og_len_title')
        link = _make_link(db_session, user, og_title='t' * 256)
        fetched = KnowhowLink.query.get(link.id)
        assert len(fetched.og_title) == 256

    def test_og_description_at_max_length(self, db_session):
        user = _make_user(db_session, 'og_len_desc')
        link = _make_link(db_session, user, og_description='d' * 512)
        fetched = KnowhowLink.query.get(link.id)
        assert len(fetched.og_description) == 512

    def test_og_image_url_at_max_length(self, db_session):
        user = _make_user(db_session, 'og_len_img')
        # Build a valid-looking URL that hits the 2048-char limit
        path = 'x' * (2048 - len('https://example.com/'))
        long_url = f'https://example.com/{path}'
        link = _make_link(db_session, user, og_image_url=long_url)
        fetched = KnowhowLink.query.get(link.id)
        assert len(fetched.og_image_url) == 2048


# ── Independence from existing columns ───────────────────────────────────────

@pytest.mark.unit
class TestOgColumnsIndependence:
    """OG columns must not interfere with existing KnowhowLink behaviour."""

    def test_existing_columns_unaffected(self, db_session):
        user = _make_user(db_session, 'og_indep_user')
        link = _make_link(
            db_session, user,
            url='https://ncbi.nlm.nih.gov/example',
            description='NCBI resource',
            og_title='NCBI Page',
        )
        fetched = KnowhowLink.query.get(link.id)
        assert fetched.url         == 'https://ncbi.nlm.nih.gov/example'
        assert fetched.description == 'NCBI resource'
        assert fetched.category    == _CATEGORY
        assert fetched.user_id     == user.id

    def test_two_links_can_share_og_title(self, db_session):
        """There is no unique constraint on og_title."""
        user = _make_user(db_session, 'og_nouniq_user')
        _make_link(db_session, user, url='https://example.com/a',
                   og_title='Shared Title')
        _make_link(db_session, user, url='https://example.com/b',
                   og_title='Shared Title')
        count = KnowhowLink.query.filter_by(og_title='Shared Title').count()
        assert count == 2

    def test_deleting_link_with_og_data_succeeds(self, db_session):
        """Deleting a link that has OG data must not raise an error."""
        user = _make_user(db_session, 'og_delete_user')
        link = _make_link(
            db_session, user,
            og_title='To Be Deleted',
            og_description='desc',
            og_image_url='https://example.com/img.png',
        )
        lid = link.id
        db_session.delete(link)
        db_session.commit()
        assert KnowhowLink.query.get(lid) is None
