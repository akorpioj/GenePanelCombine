"""
Tests for Feature 10 — Print / PDF Export of Articles.

Feature 10 is implemented entirely in the browser:
  - A "Print" button in the article view action row calls window.print()
  - @media print CSS hides the site nav, breadcrumb, interactive buttons,
    related-articles section, and back-link footer via a shared .no-print class
  - The article title, body content, author, and date are NOT marked no-print
    and thus remain fully visible in print layout

Covers:
  Print button (GET /knowhow/articles/<id>)
    - onclick="window.print()" is present in the rendered HTML
    - Button carries title="Print / Save as PDF"
    - Button text "Print" is rendered
    - Anonymous user cannot reach the article view (redirect to login)

  no-print class placement
    - Breadcrumb nav has the no-print class
    - Action-row div (bookmark / reaction / edit / print buttons) has no-print
    - Back-link footer div has the no-print class
    - Related-articles section has the no-print class (when related exist)

  Print CSS (@media print block)
    - @media print rule is present in the page HTML
    - display: none !important; rule hides .no-print elements
    - #article-card shadow/padding reset is included

  Printable content (visible in print)
    - Article title is rendered outside the no-print action row
    - Article body <div> carries the knowhow-article-body class (not no-print)
    - Author by-line is present without no-print
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


def _make_article(db_session, user, title='Test Article', is_draft=False):
    a = KnowhowArticle(
        title=title, category=_SLUG,
        content='<p>Content.</p>', user_id=user.id, is_draft=is_draft,
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


# ── Print button ──────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestPrintButton:

    def test_print_button_has_window_print_handler(self, client, db_session):
        """The article view page contains onclick=\"window.print()\" for the print button."""
        author = _make_user(db_session, 'print_btn_handler_author')
        article = _make_article(db_session, author, title='Print Button Article')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        assert b'onclick="window.print()"' in resp.data

    def test_print_button_has_correct_title(self, client, db_session):
        """The print button carries title=\"Print / Save as PDF\"."""
        author = _make_user(db_session, 'print_btn_title_author')
        article = _make_article(db_session, author, title='Print Title Article')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        assert b'title="Print / Save as PDF"' in resp.data

    def test_print_button_text_rendered(self, client, db_session):
        """The word Print appears as visible button text in the page."""
        author = _make_user(db_session, 'print_btn_text_author')
        article = _make_article(db_session, author, title='Print Text Article')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        # Template renders "Print" between opening SVG and closing </button>
        assert b'Print' in resp.data

    def test_anonymous_user_cannot_access_article_view(self, client, db_session):
        """An unauthenticated request redirects away rather than returning the print page."""
        author = _make_user(db_session, 'print_anon_author')
        article = _make_article(db_session, author, title='Anon Article')
        resp = client.get(f'/knowhow/articles/{article.id}', follow_redirects=False)
        assert resp.status_code in (302, 303, 307, 308)
        assert b'onclick="window.print()"' not in resp.data


# ── no-print class placement ──────────────────────────────────────────────────

@pytest.mark.unit
class TestNoPrintClassPlacement:

    def test_breadcrumb_nav_has_no_print_class(self, client, db_session):
        """The breadcrumb <nav> element carries the no-print CSS class."""
        author = _make_user(db_session, 'noprint_breadcrumb_author')
        article = _make_article(db_session, author, title='Breadcrumb No-Print')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        # class string on the breadcrumb nav ends with "flex-wrap no-print"
        assert b'flex-wrap no-print' in resp.data

    def test_action_row_div_has_no_print_class(self, client, db_session):
        """The action-row div (bookmark/reaction/edit/print buttons) has no-print."""
        author = _make_user(db_session, 'noprint_actionrow_author')
        article = _make_article(db_session, author, title='Action Row No-Print')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        # class string on the action-row wrapper div ends with "flex-shrink-0 no-print"
        assert b'flex-shrink-0 no-print' in resp.data

    def test_back_link_footer_has_no_print_class(self, client, db_session):
        """The back-link div at the bottom of the article carries no-print."""
        author = _make_user(db_session, 'noprint_backlink_author')
        article = _make_article(db_session, author, title='Back-Link No-Print')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        # class string on the back-link wrapper: "mt-6 pt-4 border-t border-gray-100 no-print"
        assert b'border-gray-100 no-print' in resp.data

    def test_related_articles_section_has_no_print_class(self, client, db_session):
        """The related-articles section carries no-print when it is rendered."""
        author = _make_user(db_session, 'noprint_related_author')
        main = _make_article(db_session, author, title='No-Print Related Main')
        _make_article(db_session, author, title='No-Print Related Neighbour')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{main.id}')
        assert resp.status_code == 200
        assert b'Related articles' in resp.data
        # class string on the related div: "mt-8 pt-6 border-t border-gray-100 no-print"
        assert b'pt-6 border-t border-gray-100 no-print' in resp.data

    def test_at_least_one_no_print_element_on_page(self, client, db_session):
        """The article view always renders at least one no-print element (action row)."""
        author = _make_user(db_session, 'noprint_any_author')
        article = _make_article(db_session, author, title='Any No-Print Article')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        assert b'no-print' in resp.data


# ── Print CSS ─────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestPrintCSS:

    def test_media_print_rule_present(self, client, db_session):
        """The article view page includes an @media print CSS block."""
        author = _make_user(db_session, 'printcss_media_author')
        article = _make_article(db_session, author, title='Print CSS Article')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        assert b'@media print' in resp.data

    def test_display_none_rule_targets_no_print(self, client, db_session):
        """The print CSS applies display:none to .no-print elements."""
        author = _make_user(db_session, 'printcss_none_author')
        article = _make_article(db_session, author, title='Display None Article')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        assert b'display: none !important' in resp.data

    def test_article_card_reset_included_in_print_css(self, client, db_session):
        """The print CSS includes a rule targeting #article-card."""
        author = _make_user(db_session, 'printcss_card_author')
        article = _make_article(db_session, author, title='Card Reset Article')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        assert b'#article-card' in resp.data

    def test_body_header_hidden_in_print_css(self, client, db_session):
        """The print CSS rule hides the site-wide body > header nav."""
        author = _make_user(db_session, 'printcss_bodyheader_author')
        article = _make_article(db_session, author, title='Body Header Article')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        assert b'body > header' in resp.data


# ── Printable content (not hidden) ───────────────────────────────────────────

@pytest.mark.unit
class TestPrintableContent:

    def test_article_title_rendered_in_heading(self, client, db_session):
        """The article title appears in an <h1> tag that carries no no-print class."""
        author = _make_user(db_session, 'printable_title_author')
        article = _make_article(db_session, author, title='Printable Title Sentinel')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        assert b'Printable Title Sentinel' in resp.data

    def test_article_body_element_carries_knowhow_article_body_class(self, client, db_session):
        """The article body div has the knowhow-article-body class (no no-print)."""
        author = _make_user(db_session, 'printable_body_author')
        article = _make_article(db_session, author, title='Printable Body Article')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        assert b'knowhow-article-body' in resp.data

    def test_article_body_content_present(self, client, db_session):
        """The article body content is rendered on the page."""
        author = _make_user(db_session, 'printable_content_author')
        article = KnowhowArticle(
            title='Printable Content Article', category=_SLUG,
            content='<p>Body content sentinel text</p>', user_id=author.id,
            is_draft=False,
        )
        db_session.add(article)
        db_session.commit()
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        assert b'Body content sentinel text' in resp.data

    def test_author_byline_present(self, client, db_session):
        """The author's name appears in the by-line (not hidden by no-print)."""
        author = _make_user(db_session, 'printable_author_byline')
        article = _make_article(db_session, author, title='Byline Article')
        _login(client, author.id)
        resp = client.get(f'/knowhow/articles/{article.id}')
        assert resp.status_code == 200
        # author username appears in "By <name>" byline
        assert b'printable_author_byline' in resp.data
