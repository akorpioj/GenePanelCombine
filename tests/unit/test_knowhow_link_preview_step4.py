"""
Tests for Feature 11 Step 4 — Render OG preview cards in templates.

These are template-rendering tests that verify the category and index pages
emit preview-card HTML when a ``KnowhowLink`` has OG data, and gracefully
fall back to the plain description link when it does not.

Templates under test
────────────────────
  - ``app/templates/knowhow/category.html``
       route: GET /knowhow/category/<slug>
       two link contexts: root links (subcategory_id=None) and sub-links
  - ``app/templates/knowhow/index.html``
       route: GET /knowhow/
       two link contexts: root links and sub-links

Test plan
─────────
  Preview card — category page, root links
    - og_title appears as the link label (not link.description)
    - og_description appears below the link
    - og_image_url is present in an <img> src attribute
    - no <img> when og_image_url is None
    - href on the link is still link.url
    - link.description text NOT shown when og_title is set

  Fallback — category page, root links
    - link.description used as label when og_title is None
    - og_description NOT rendered when og_title is None
    - no <img> rendered when og data is entirely absent

  Preview card — category page, sub-links
    - og_title appears as link label in subcategory section
    - fallback shows description in subcategory section

  Preview card — index page, root links
    - og_title appears as link label
    - og_description appears
    - og_image_url present in <img> src
    - fallback shows description when no OG data
    - no <img> when og_image_url absent

  Preview card — index page, sub-links
    - og_title appears as link label in subcategory section
"""

import pytest

from app.models import db, User, UserRole, KnowhowLink, KnowhowCategory, KnowhowSubcategory


# ── Fixture strings ────────────────────────────────────────────────────────────

_SLUG = 'gene_panels'

_OG_TITLE       = 'Open Graph Preview Title'
_OG_DESC        = 'Open Graph preview description text'
_OG_IMAGE       = 'https://img.example.com/og-step4-preview.png'
_OG_IMAGE_PART  = b'og-step4-preview.png'   # unique enough to search for in HTML
_OG_URL         = 'https://example.com/og-step4-link'

_PLAIN_DESC     = 'Plain user-typed description step4'
_PLAIN_URL      = 'https://example.com/plain-step4-link'


# ── Helpers ────────────────────────────────────────────────────────────────────

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
    # Trigger category seeding
    client.get('/knowhow/', follow_redirects=False)


def _create_link_with_og(db_session, user_id):
    """KnowhowLink with all three OG fields populated."""
    link = KnowhowLink(
        category=_SLUG,
        url=_OG_URL,
        description='This description should NOT appear in the card',
        user_id=user_id,
        subcategory_id=None,
        og_title=_OG_TITLE,
        og_description=_OG_DESC,
        og_image_url=_OG_IMAGE,
    )
    db_session.add(link)
    db_session.commit()
    return link


def _create_link_without_og(db_session, user_id):
    """KnowhowLink with no OG data — fallback case."""
    link = KnowhowLink(
        category=_SLUG,
        url=_PLAIN_URL,
        description=_PLAIN_DESC,
        user_id=user_id,
        subcategory_id=None,
        og_title=None,
        og_description=None,
        og_image_url=None,
    )
    db_session.add(link)
    db_session.commit()
    return link


def _create_subcategory(db_session):
    """Return the gene_panels KnowhowCategory and a child subcategory."""
    cat = KnowhowCategory.query.filter_by(slug=_SLUG).first()
    sub = KnowhowSubcategory(category_id=cat.id, label='Step4 SubFolder', position=0)
    db_session.add(sub)
    db_session.commit()
    return cat, sub


def _create_sub_link_with_og(db_session, user_id, subcategory_id):
    link = KnowhowLink(
        category=_SLUG,
        url='https://example.com/og-step4-sub',
        description='Subcategory description should not show',
        user_id=user_id,
        subcategory_id=subcategory_id,
        og_title='Sub OG Title Step4',
        og_description='Sub OG desc step4',
        og_image_url='https://img.example.com/og-sub-step4.png',
    )
    db_session.add(link)
    db_session.commit()
    return link


def _create_sub_link_without_og(db_session, user_id, subcategory_id):
    link = KnowhowLink(
        category=_SLUG,
        url='https://example.com/plain-step4-sub',
        description='Sub plain description step4',
        user_id=user_id,
        subcategory_id=subcategory_id,
        og_title=None,
        og_description=None,
        og_image_url=None,
    )
    db_session.add(link)
    db_session.commit()
    return link


# ── Category page — root links — preview card ─────────────────────────────────

@pytest.mark.unit
class TestCategoryPageRootLinkPreviewCard:
    """GET /knowhow/category/<slug> with a root link that has OG data."""

    def _get_category_page(self, client, db_session):
        user = _make_user(db_session, 'step4_cat_og')
        _login(client, user.id)
        _create_link_with_og(db_session, user.id)
        return client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)

    def test_og_title_shown_as_link_text(self, client, db_session):
        resp = self._get_category_page(client, db_session)
        assert _OG_TITLE.encode() in resp.data

    def test_og_description_shown_in_card(self, client, db_session):
        resp = self._get_category_page(client, db_session)
        assert _OG_DESC.encode() in resp.data

    def test_og_image_url_in_img_src(self, client, db_session):
        resp = self._get_category_page(client, db_session)
        assert _OG_IMAGE_PART in resp.data

    def test_link_href_is_og_url(self, client, db_session):
        resp = self._get_category_page(client, db_session)
        assert _OG_URL.encode() in resp.data

    def test_user_description_not_shown_when_og_title_present(self, client, db_session):
        resp = self._get_category_page(client, db_session)
        assert b'This description should NOT appear in the card' not in resp.data


# ── Category page — root links — no OG image ──────────────────────────────────

@pytest.mark.unit
class TestCategoryPageRootLinkNoImage:
    """OG title and description present but no image."""

    def test_no_img_when_og_image_url_absent(self, client, db_session):
        user = _make_user(db_session, 'step4_cat_noimg')
        _login(client, user.id)
        link = KnowhowLink(
            category=_SLUG, url='https://example.com/noimg-step4',
            description='No image link',
            user_id=user.id, subcategory_id=None,
            og_title='OG Title No Image', og_description='OG desc no image',
            og_image_url=None,
        )
        db_session.add(link)
        db_session.commit()
        resp = client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)
        html = resp.data.decode('utf-8', errors='replace')
        # 'OG Title No Image' is the title, but no img tag should reference a None src
        assert 'OG Title No Image' in html
        assert 'OG desc no image' in html
        # No <img> element should appear in the link section with a None/empty src
        # (we check that the image string for this link is absent, not a generic img check)
        assert 'noimg-step4' not in html.split('<img')[1] if '<img' in html else True


# ── Category page — root links — fallback ────────────────────────────────────

@pytest.mark.unit
class TestCategoryPageRootLinkFallback:
    """GET /knowhow/category/<slug> with a root link that has NO OG data."""

    def _get_category_page(self, client, db_session):
        user = _make_user(db_session, 'step4_cat_plain')
        _login(client, user.id)
        _create_link_without_og(db_session, user.id)
        return client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)

    def test_description_shown_as_link_text_in_fallback(self, client, db_session):
        resp = self._get_category_page(client, db_session)
        assert _PLAIN_DESC.encode() in resp.data

    def test_og_description_not_shown_in_fallback(self, client, db_session):
        """No og_description noise when og_title is absent."""
        user = _make_user(db_session, 'step4_cat_plain2')
        _login(client, user.id)
        link = KnowhowLink(
            category=_SLUG, url='https://example.com/fallback-step4',
            description='Fallback description step4',
            user_id=user.id, subcategory_id=None,
            og_title=None,
            og_description='Should not appear in fallback',
            og_image_url=None,
        )
        db_session.add(link)
        db_session.commit()
        resp = client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)
        assert b'Should not appear in fallback' not in resp.data

    def test_no_img_in_fallback(self, client, db_session):
        """When og_image_url is None and og_title is None, no OG image rendered."""
        user = _make_user(db_session, 'step4_cat_noimg2')
        _login(client, user.id)
        _create_link_without_og(db_session, user.id)
        resp = client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)
        # The plain link URL should not appear inside an <img> src
        assert f'src="{_PLAIN_URL}"'.encode() not in resp.data


# ── Category page — subcategory links ────────────────────────────────────────

@pytest.mark.unit
class TestCategoryPageSubLinkPreviewCard:
    """Links nested under a subcategory should render the same preview logic."""

    def test_og_title_shown_for_sub_link(self, client, db_session):
        user = _make_user(db_session, 'step4_sub_og')
        _login(client, user.id)
        cat, sub = _create_subcategory(db_session)
        _create_sub_link_with_og(db_session, user.id, sub.id)
        resp = client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)
        assert b'Sub OG Title Step4' in resp.data

    def test_og_description_shown_for_sub_link(self, client, db_session):
        user = _make_user(db_session, 'step4_sub_desc')
        _login(client, user.id)
        cat, sub = _create_subcategory(db_session)
        _create_sub_link_with_og(db_session, user.id, sub.id)
        resp = client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)
        assert b'Sub OG desc step4' in resp.data

    def test_fallback_for_sub_link(self, client, db_session):
        user = _make_user(db_session, 'step4_sub_plain')
        _login(client, user.id)
        cat, sub = _create_subcategory(db_session)
        _create_sub_link_without_og(db_session, user.id, sub.id)
        resp = client.get(f'/knowhow/category/{_SLUG}', follow_redirects=False)
        assert b'Sub plain description step4' in resp.data


# ── Index page — root links — preview card ────────────────────────────────────

@pytest.mark.unit
class TestIndexPageRootLinkPreviewCard:
    """GET /knowhow/ with a root link that has OG data."""

    def _get_index(self, client, db_session):
        user = _make_user(db_session, 'step4_idx_og')
        _login(client, user.id)
        _create_link_with_og(db_session, user.id)
        return client.get('/knowhow/', follow_redirects=False)

    def test_og_title_shown_as_link_text(self, client, db_session):
        resp = self._get_index(client, db_session)
        assert _OG_TITLE.encode() in resp.data

    def test_og_description_shown_on_index(self, client, db_session):
        resp = self._get_index(client, db_session)
        assert _OG_DESC.encode() in resp.data

    def test_og_image_in_img_src_on_index(self, client, db_session):
        resp = self._get_index(client, db_session)
        assert _OG_IMAGE_PART in resp.data

    def test_user_description_not_shown_when_og_title_present(self, client, db_session):
        resp = self._get_index(client, db_session)
        assert b'This description should NOT appear in the card' not in resp.data


# ── Index page — root links — fallback ────────────────────────────────────────

@pytest.mark.unit
class TestIndexPageRootLinkFallback:
    """GET /knowhow/ with a root link that has NO OG data."""

    def _get_index(self, client, db_session):
        user = _make_user(db_session, 'step4_idx_plain')
        _login(client, user.id)
        _create_link_without_og(db_session, user.id)
        return client.get('/knowhow/', follow_redirects=False)

    def test_description_shown_as_link_text_in_fallback(self, client, db_session):
        resp = self._get_index(client, db_session)
        assert _PLAIN_DESC.encode() in resp.data

    def test_no_img_in_fallback(self, client, db_session):
        resp = self._get_index(client, db_session)
        assert f'src="{_PLAIN_URL}"'.encode() not in resp.data


# ── Index page — sub-links — preview card ────────────────────────────────────

@pytest.mark.unit
class TestIndexPageSubLinkPreviewCard:
    """Index page sub-link section should also use the preview card."""

    def test_og_title_shown_for_sub_link_on_index(self, client, db_session):
        user = _make_user(db_session, 'step4_idx_sub')
        _login(client, user.id)
        cat, sub = _create_subcategory(db_session)
        _create_sub_link_with_og(db_session, user.id, sub.id)
        resp = client.get('/knowhow/', follow_redirects=False)
        assert b'Sub OG Title Step4' in resp.data

    def test_fallback_for_sub_link_on_index(self, client, db_session):
        user = _make_user(db_session, 'step4_idx_sub_plain')
        _login(client, user.id)
        cat, sub = _create_subcategory(db_session)
        _create_sub_link_without_og(db_session, user.id, sub.id)
        resp = client.get('/knowhow/', follow_redirects=False)
        assert b'Sub plain description step4' in resp.data
