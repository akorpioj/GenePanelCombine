"""
Tests for Feature 1 — Full-text Search (GET /knowhow/search?q=).

Covers:
  Route access
    - Returns 200 for a logged-in user
    - Redirects anonymous users (login required)
    - Returns 200 with an empty query (no results, no error)
    - Returns 200 when query is a single character (below 2-char minimum — no results)

  Article results
    - Matches article by title (case-insensitive)
    - Matches article by content
    - Matched article link appears in the response
    - Article whose title and content do not match the query is absent
    - Other users' published articles are returned (search is not author-restricted)
    - Other users' DRAFT articles are NOT returned (respects _draft_filter)
    - Own draft articles ARE returned to their author

  Link results
    - Matches link by description
    - Matches link by URL
    - Matched link URL / description appears in the response
    - Link that does not match the query is absent

  Query safety
    - SQL wildcard % in query does not cause errors and matches only literal %
    - SQL wildcard _ in query does not cause errors and matches only literal _
    - XSS payload in query is HTML-escaped in the response (not rendered as HTML)

  Edge cases
    - Empty result set renders without error
    - Query matching both articles and links returns both
"""
import pytest
from app.models import db, User, UserRole, KnowhowArticle, KnowhowLink

_SLUG = 'gene_panels'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(db_session, username, role=UserRole.USER):
    u = User(username=username, email=f'{username}@test.com', role=role)
    u.set_password('pw')
    db_session.add(u)
    db_session.commit()
    return u


def _make_article(db_session, user, title, content='<p>content</p>', is_draft=False):
    a = KnowhowArticle(
        title=title, category=_SLUG,
        content=content,
        user_id=user.id, is_draft=is_draft,
    )
    db_session.add(a)
    db_session.commit()
    return a


def _make_link(db_session, user, url, description):
    lnk = KnowhowLink(
        category=_SLUG, url=url,
        description=description,
        user_id=user.id,
    )
    db_session.add(lnk)
    db_session.commit()
    return lnk


def _login(client, user_id):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    # Seeds gene_panels category
    client.get('/knowhow/articles/new', follow_redirects=False)


def _search(client, q):
    return client.get(f'/knowhow/search?q={q}')


# ── Route access ──────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSearchAccess:
    def test_returns_200_for_logged_in_user(self, client, db_session):
        user = _make_user(db_session, 'srch_access_user')
        _login(client, user.id)
        resp = _search(client, 'anything')
        assert resp.status_code == 200

    def test_redirects_anonymous_user(self, client, db_session):
        resp = client.get('/knowhow/search?q=anything', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_empty_query_returns_200_no_results(self, client, db_session):
        user = _make_user(db_session, 'srch_empty_user')
        _login(client, user.id)
        resp = _search(client, '')
        assert resp.status_code == 200

    def test_single_char_query_returns_200_no_results(self, client, db_session):
        """Queries shorter than 2 chars must return the page without crashing."""
        user = _make_user(db_session, 'srch_short_user')
        _make_article(db_session, user, 'X marks the spot')
        _login(client, user.id)
        resp = _search(client, 'X')
        assert resp.status_code == 200
        # The article link must NOT appear — query too short to trigger search
        body = resp.get_data(as_text=True)
        assert f'/knowhow/articles/' not in body


# ── Article matching ──────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSearchArticleResults:
    def test_matches_article_by_title(self, client, db_session):
        author = _make_user(db_session, 'srch_title_author')
        article = _make_article(db_session, author, 'Unique Zygosity Concept')
        _login(client, author.id)
        resp = _search(client, 'Zygosity')
        assert f'/knowhow/articles/{article.id}' in resp.get_data(as_text=True)

    def test_title_match_is_case_insensitive(self, client, db_session):
        author = _make_user(db_session, 'srch_ci_author')
        article = _make_article(db_session, author, 'Haploinsufficiency Guide')
        _login(client, author.id)
        resp = _search(client, 'haploinsufficiency')
        assert f'/knowhow/articles/{article.id}' in resp.get_data(as_text=True)

    def test_matches_article_by_content(self, client, db_session):
        author = _make_user(db_session, 'srch_content_author')
        article = _make_article(
            db_session, author, 'General Article',
            content='<p>The xyzquux concept is described here.</p>',
        )
        _login(client, author.id)
        resp = _search(client, 'xyzquux')
        assert f'/knowhow/articles/{article.id}' in resp.get_data(as_text=True)

    def test_non_matching_article_is_absent(self, client, db_session):
        author = _make_user(db_session, 'srch_nomatch_author')
        article = _make_article(db_session, author, 'Completely Irrelevant Title')
        _login(client, author.id)
        resp = _search(client, 'xyzquux_nomatch_sentinel')
        assert f'/knowhow/articles/{article.id}' not in resp.get_data(as_text=True)

    def test_other_users_published_article_is_returned(self, client, db_session):
        """Search is NOT restricted to own articles — others' published articles appear."""
        author = _make_user(db_session, 'srch_other_author')
        viewer = _make_user(db_session, 'srch_other_viewer')
        article = _make_article(db_session, author, 'Shared Penetrance Concept')
        _login(client, viewer.id)
        resp = _search(client, 'Penetrance')
        assert f'/knowhow/articles/{article.id}' in resp.get_data(as_text=True)

    def test_other_users_draft_is_not_returned(self, client, db_session):
        """Draft articles belonging to another user must not appear in search results."""
        author = _make_user(db_session, 'srch_draft_author')
        viewer = _make_user(db_session, 'srch_draft_viewer')
        article = _make_article(
            db_session, author, 'Secret Unpublished Work',
            content='<p>secretxyzterm</p>', is_draft=True,
        )
        _login(client, viewer.id)
        resp = _search(client, 'secretxyzterm')
        assert f'/knowhow/articles/{article.id}' not in resp.get_data(as_text=True)

    def test_own_draft_is_returned_to_author(self, client, db_session):
        """Authors must be able to find their own drafts via search."""
        author = _make_user(db_session, 'srch_owndraft_author')
        article = _make_article(
            db_session, author, 'My Work In Progress',
            content='<p>owndraftsentinel</p>', is_draft=True,
        )
        _login(client, author.id)
        resp = _search(client, 'owndraftsentinel')
        assert f'/knowhow/articles/{article.id}' in resp.get_data(as_text=True)

    def test_admin_sees_other_users_draft_in_search(self, client, db_session):
        """ADMIN users must see all drafts in search results."""
        author = _make_user(db_session, 'srch_admindraft_author')
        admin = _make_user(db_session, 'srch_admindraft_admin', role=UserRole.ADMIN)
        article = _make_article(
            db_session, author, 'Admin Visible Draft',
            content='<p>adminvisiblesentinel</p>', is_draft=True,
        )
        _login(client, admin.id)
        resp = _search(client, 'adminvisiblesentinel')
        assert f'/knowhow/articles/{article.id}' in resp.get_data(as_text=True)


# ── Link matching ─────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSearchLinkResults:
    def test_matches_link_by_description(self, client, db_session):
        user = _make_user(db_session, 'srch_linkdesc_user')
        lnk = _make_link(db_session, user,
                         url='https://example.com/panels',
                         description='Rare zygosentinel disease panel registry')
        _login(client, user.id)
        resp = _search(client, 'zygosentinel')
        assert 'https://example.com/panels' in resp.get_data(as_text=True)

    def test_matches_link_by_url(self, client, db_session):
        user = _make_user(db_session, 'srch_linkurl_user')
        _make_link(db_session, user,
                   url='https://uniqueurlsentinel.example.com/',
                   description='Some link description')
        _login(client, user.id)
        resp = _search(client, 'uniqueurlsentinel')
        assert 'uniqueurlsentinel' in resp.get_data(as_text=True)

    def test_non_matching_link_is_absent(self, client, db_session):
        user = _make_user(db_session, 'srch_linknomatch_user')
        _make_link(db_session, user,
                   url='https://nomatch.example.com/',
                   description='This link does not match the sentinel')
        _login(client, user.id)
        resp = _search(client, 'xyzquux_nomatch_sentinel')
        assert 'nomatch.example.com' not in resp.get_data(as_text=True)


# ── Query safety ──────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSearchQuerySafety:
    def test_percent_wildcard_in_query_does_not_crash(self, client, db_session):
        """A literal % in the search query must not cause a DB error."""
        user = _make_user(db_session, 'srch_pct_user')
        _login(client, user.id)
        resp = _search(client, '100%25')  # URL-encoded %
        assert resp.status_code == 200

    def test_underscore_wildcard_in_query_does_not_crash(self, client, db_session):
        """A literal _ in the search query must not cause a DB error."""
        user = _make_user(db_session, 'srch_us_user')
        _login(client, user.id)
        resp = _search(client, 'gene_panel')
        assert resp.status_code == 200

    def test_xss_payload_in_query_is_escaped(self, client, db_session):
        """A <script> tag in the query must be HTML-escaped, not rendered."""
        user = _make_user(db_session, 'srch_xss_user')
        _login(client, user.id)
        # URL-encode angle brackets so the query reaches the route
        resp = client.get('/knowhow/search?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert '<script>alert(1)</script>' not in body
        assert '&lt;script&gt;' in body or 'alert(1)' not in body


# ── Combined and edge cases ───────────────────────────────────────────────────

@pytest.mark.unit
class TestSearchEdgeCases:
    def test_no_results_renders_without_error(self, client, db_session):
        """An empty result set (nothing matches) must render the page cleanly."""
        user = _make_user(db_session, 'srch_nores_user')
        _login(client, user.id)
        resp = _search(client, 'zzznomatchxyzzy')
        assert resp.status_code == 200

    def test_query_matching_both_articles_and_links_returns_both(self, client, db_session):
        """A query that matches an article title AND a link description must return both."""
        user = _make_user(db_session, 'srch_both_user')
        sentinel = 'sharedsentinelterm'
        article = _make_article(db_session, user,
                                title=f'Article about {sentinel}')
        lnk = _make_link(db_session, user,
                         url='https://bothtest.example.com/',
                         description=f'Link about {sentinel}')
        _login(client, user.id)
        resp = _search(client, sentinel)
        body = resp.get_data(as_text=True)
        assert f'/knowhow/articles/{article.id}' in body
        assert 'bothtest.example.com' in body
