"""
Tests for Feature 11 Step 3 — Populate OG data when a link is saved.

Strategy: patch ``app.knowhow.routes._fetch_og_data`` (the name used inside
routes.py after the import) so no real HTTP traffic is made.  The test client
POSTs to ``POST /knowhow/links`` and we assert that the saved ``KnowhowLink``
row has the OG values that the mock returned.

Test plan
─────────
  OG data stored on add_link
    - OG fields from a successful fetch are persisted on the new link row
    - og_title is stored
    - og_description is stored
    - og_image_url is stored
    - When fetcher returns all-None (e.g. HTTP error), link is still saved
    - When fetcher returns all-None, og_title is NULL in the DB
    - When fetcher returns partial data (title only), partial data is stored

  _fetch_og_data is called with the submitted URL
    - The fetcher is called exactly once per add_link request
    - It is called with the exact URL that was submitted in the form

  Link is saved regardless of fetch result
    - fetch raises an exception → link still saved (the route-level wrapper
      should already handle this, but belt-and-braces test)
    - fetch returns all-None → link row exists in DB

  No OG fetch for invalid submissions
    - Invalid URL (missing scheme) → redirect, no link row, fetcher not called
    - Description too short → redirect, no link row, fetcher not called

  Route behaviour unchanged
    - Successful add still redirects (302)
    - Flash message still says 'Link added.'
"""
import pytest
from unittest.mock import patch, MagicMock

from app.models import db, User, UserRole, KnowhowLink


_SLUG = 'gene_panels'        # one of _DEFAULT_CATEGORIES slugs
_URL  = 'https://example.com/resource'

_FULL_OG  = {'og_title': 'Example Title', 'og_description': 'Example desc.', 'og_image_url': 'https://example.com/img.png'}
_NULL_OG  = {'og_title': None, 'og_description': None, 'og_image_url': None}
_TITLE_OG = {'og_title': 'Title Only', 'og_description': None, 'og_image_url': None}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(db_session, username):
    u = User(username=username, email=f'{username}@test.com', role=UserRole.USER)
    u.set_password('pw')
    db_session.add(u)
    db_session.commit()
    return u


def _login(client, user_id):
    with client.session_transaction() as sess:
        sess.clear()
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    # Seed categories
    client.get('/knowhow/', follow_redirects=False)


def _post_add_link(client, url=_URL, description='A useful resource', category=_SLUG,
                   follow_redirects=False):
    return client.post('/knowhow/links', data={
        'category':    category,
        'url':         url,
        'description': description,
    }, follow_redirects=follow_redirects)


def _last_link():
    """Return the most recently created KnowhowLink, or None."""
    return KnowhowLink.query.order_by(KnowhowLink.id.desc()).first()


# ── OG data stored on add_link ────────────────────────────────────────────────

@pytest.mark.unit
class TestOgDataStoredOnAddLink:
    """All three OG fields from a successful fetch must be persisted."""

    def test_og_title_stored(self, client, db_session):
        user = _make_user(db_session, 'og_add_title')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_FULL_OG):
            _post_add_link(client)
        link = _last_link()
        assert link is not None
        assert link.og_title == 'Example Title'

    def test_og_description_stored(self, client, db_session):
        user = _make_user(db_session, 'og_add_desc')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_FULL_OG):
            _post_add_link(client)
        link = _last_link()
        assert link.og_description == 'Example desc.'

    def test_og_image_url_stored(self, client, db_session):
        user = _make_user(db_session, 'og_add_img')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_FULL_OG):
            _post_add_link(client)
        link = _last_link()
        assert link.og_image_url == 'https://example.com/img.png'

    def test_all_three_fields_stored_together(self, client, db_session):
        user = _make_user(db_session, 'og_add_all')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_FULL_OG):
            _post_add_link(client)
        link = _last_link()
        assert link.og_title       == 'Example Title'
        assert link.og_description == 'Example desc.'
        assert link.og_image_url   == 'https://example.com/img.png'

    def test_partial_og_data_stored(self, client, db_session):
        """Title-only result → title stored, description and image are NULL."""
        user = _make_user(db_session, 'og_add_partial')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_TITLE_OG):
            _post_add_link(client)
        link = _last_link()
        assert link.og_title       == 'Title Only'
        assert link.og_description is None
        assert link.og_image_url   is None


# ── Link saved even when fetch returns all-None ───────────────────────────────

@pytest.mark.unit
class TestLinkSavedWhenFetchFails:
    """The link row must always be committed even when OG data is unavailable."""

    def test_link_saved_when_og_all_none(self, client, db_session):
        user = _make_user(db_session, 'og_fail_save')
        _login(client, user.id)
        count_before = KnowhowLink.query.count()
        with patch('app.knowhow.routes._fetch_og_data', return_value=_NULL_OG):
            _post_add_link(client)
        assert KnowhowLink.query.count() == count_before + 1

    def test_og_fields_null_when_fetch_returns_none(self, client, db_session):
        user = _make_user(db_session, 'og_fail_null')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_NULL_OG):
            _post_add_link(client)
        link = _last_link()
        assert link.og_title       is None
        assert link.og_description is None
        assert link.og_image_url   is None

    def test_link_saved_when_og_fetch_raises(self, client, db_session):
        """If _fetch_og_data itself raises unexpectedly, the link must still be saved."""
        user = _make_user(db_session, 'og_exc_save')
        _login(client, user.id)
        count_before = KnowhowLink.query.count()
        with patch('app.knowhow.routes._fetch_og_data', side_effect=Exception('boom')):
            _post_add_link(client)
        # Link was committed despite the exception
        assert KnowhowLink.query.count() == count_before + 1


# ── Fetcher called with the correct URL ──────────────────────────────────────

@pytest.mark.unit
class TestFetcherCalledWithUrl:
    """_fetch_og_data must be invoked exactly once with the submitted URL."""

    def test_fetcher_called_once(self, client, db_session):
        user = _make_user(db_session, 'og_called_once')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_NULL_OG) as mock_fetch:
            _post_add_link(client, url=_URL)
        mock_fetch.assert_called_once()

    def test_fetcher_called_with_submitted_url(self, client, db_session):
        user = _make_user(db_session, 'og_called_url')
        _login(client, user.id)
        target_url = 'https://ncbi.nlm.nih.gov/gene/1234'
        with patch('app.knowhow.routes._fetch_og_data', return_value=_NULL_OG) as mock_fetch:
            _post_add_link(client, url=target_url)
        mock_fetch.assert_called_once_with(target_url)


# ── Fetcher not called on invalid submissions ─────────────────────────────────

@pytest.mark.unit
class TestFetcherNotCalledOnInvalidInput:
    """Validation failures must short-circuit before the fetcher is invoked."""

    def test_invalid_url_scheme_does_not_call_fetcher(self, client, db_session):
        user = _make_user(db_session, 'og_no_call_scheme')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_NULL_OG) as mock_fetch:
            _post_add_link(client, url='ftp://example.com/file')
        mock_fetch.assert_not_called()

    def test_description_too_short_does_not_call_fetcher(self, client, db_session):
        user = _make_user(db_session, 'og_no_call_desc')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_NULL_OG) as mock_fetch:
            _post_add_link(client, description='ab')   # min is 3
        mock_fetch.assert_not_called()

    def test_invalid_url_no_link_row_created(self, client, db_session):
        user = _make_user(db_session, 'og_no_row_scheme')
        _login(client, user.id)
        count_before = KnowhowLink.query.count()
        with patch('app.knowhow.routes._fetch_og_data', return_value=_NULL_OG):
            _post_add_link(client, url='ftp://example.com/file')
        assert KnowhowLink.query.count() == count_before


# ── Route behaviour unchanged ─────────────────────────────────────────────────

@pytest.mark.unit
class TestRouteBehaviourUnchanged:
    """OG integration must not change the existing redirect / flash behaviour."""

    def test_successful_add_still_redirects(self, client, db_session):
        user = _make_user(db_session, 'og_redirect')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_NULL_OG):
            resp = _post_add_link(client)
        assert resp.status_code == 302

    def test_flash_message_still_link_added(self, client, db_session):
        user = _make_user(db_session, 'og_flash')
        _login(client, user.id)
        with patch('app.knowhow.routes._fetch_og_data', return_value=_NULL_OG):
            resp = _post_add_link(client, follow_redirects=True)
        assert b'Link added' in resp.data
