"""
Tests for Feature 12 — "New Since Last Visit" Indicator.

Covers:
  GET /knowhow/category/<slug>  (category — last-visit upsert)
    - First visit to a category creates a KnowhowLastVisit row in the DB
    - Second visit updates visited_at on the existing row (upsert, not duplicate)
    - Last-visit records are personal — one row per user per category
    - Anonymous user cannot reach the category page (redirect)

  GET /knowhow/  (index — new_counts computation)
    - Category never visited shows no badge (no entry in new_counts)
    - Category visited after all its content was created shows no badge
    - Article created after last visit increments the badge count
    - Multiple articles created after last visit show the summed count
    - Articles created before last visit are NOT counted
    - A new link added after last visit is counted alongside articles
    - new_counts are personal — another user's last visit does not affect the badge
    - Draft articles from other users are excluded from the count

  GET /knowhow/  (index — badge template rendering)
    - Badge number matches the new_counts value
    - Badge carries title="N new since your last visit"
    - Badge element uses text-red-600 style class
    - Badge is absent when there is no new content since last visit
    - Badge is absent for a category that has never been visited

  Model: KnowhowLastVisit
    - Composite primary key (user_id, category_slug) prevents duplicate rows
    - Records are personal per user (two users have separate rows)
    - visited_at field stores and retrieves a datetime correctly
"""
import datetime
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import db, User, UserRole, KnowhowArticle, KnowhowCategory, KnowhowLastVisit, KnowhowLink

_SLUG = 'gene_panels'
_VALID_COLOR = '#0369a1'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(db_session, username, role=UserRole.USER):
    u = User(username=username, email=f'{username}@test.com', role=role)
    u.set_password('pw')
    db_session.add(u)
    db_session.commit()
    return u


def _make_category(db_session, slug, label='Test Category', position=99):
    c = KnowhowCategory(slug=slug, label=label, color=_VALID_COLOR,
                        description=None, position=position)
    db_session.add(c)
    db_session.commit()
    return c


def _make_article(db_session, user, title='Test Article',
                  category=_SLUG, is_draft=False,
                  created_at=None):
    a = KnowhowArticle(
        title=title, category=category,
        content='<p>Content.</p>', user_id=user.id, is_draft=is_draft,
    )
    if created_at is not None:
        a.created_at = created_at
        a.updated_at = created_at
    db_session.add(a)
    db_session.commit()
    return a


def _make_link(db_session, user, category=_SLUG, created_at=None):
    lnk = KnowhowLink(
        category=category,
        url='https://example.com',
        description='A test link',
        user_id=user.id,
    )
    if created_at is not None:
        lnk.created_at = created_at
    db_session.add(lnk)
    db_session.commit()
    return lnk


def _make_last_visit(db_session, user, slug, visited_at):
    lv = KnowhowLastVisit(user_id=user.id, category_slug=slug, visited_at=visited_at)
    db_session.add(lv)
    db_session.commit()
    return lv


def _login(client, user_id):
    with client.session_transaction() as sess:
        sess.clear()
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    client.get('/knowhow/articles/new', follow_redirects=False)


# ── category() — last-visit upsert ───────────────────────────────────────────

@pytest.mark.unit
class TestLastVisitUpsert:

    def test_first_category_visit_creates_last_visit_row(self, client, db_session):
        """Visiting a category for the first time creates a KnowhowLastVisit row."""
        author = _make_user(db_session, 'lv_first_visit_author')
        cat = _make_category(db_session, 'lv_first_visit_slug')
        _login(client, author.id)
        assert KnowhowLastVisit.query.filter_by(
            user_id=author.id, category_slug='lv_first_visit_slug'
        ).first() is None
        resp = client.get(f'/knowhow/category/{cat.slug}')
        assert resp.status_code == 200
        lv = KnowhowLastVisit.query.filter_by(
            user_id=author.id, category_slug='lv_first_visit_slug'
        ).first()
        assert lv is not None

    def test_second_category_visit_updates_visited_at(self, client, db_session):
        """Re-visiting a category updates visited_at rather than creating a second row."""
        author = _make_user(db_session, 'lv_upsert_author')
        cat = _make_category(db_session, 'lv_upsert_slug')
        old_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        _make_last_visit(db_session, author, cat.slug, old_time)
        _login(client, author.id)
        client.get(f'/knowhow/category/{cat.slug}')
        rows = KnowhowLastVisit.query.filter_by(
            user_id=author.id, category_slug=cat.slug
        ).all()
        assert len(rows) == 1, 'Upsert must not create a duplicate row'
        assert rows[0].visited_at > old_time

    def test_last_visit_row_is_personal(self, client, db_session):
        """Visiting a category creates a row scoped to the visiting user only."""
        user_a = _make_user(db_session, 'lv_personal_a')
        user_b = _make_user(db_session, 'lv_personal_b')
        cat = _make_category(db_session, 'lv_personal_slug')
        _login(client, user_a.id)
        client.get(f'/knowhow/category/{cat.slug}')
        assert KnowhowLastVisit.query.filter_by(
            user_id=user_a.id, category_slug=cat.slug
        ).first() is not None
        assert KnowhowLastVisit.query.filter_by(
            user_id=user_b.id, category_slug=cat.slug
        ).first() is None

    def test_anonymous_cannot_visit_category_page(self, client, db_session):
        """An unauthenticated request to the category page is redirected."""
        cat = _make_category(db_session, 'lv_anon_slug')
        resp = client.get(f'/knowhow/category/{cat.slug}', follow_redirects=False)
        assert resp.status_code in (302, 303, 307, 308)


# ── index() — new_counts computation ─────────────────────────────────────────

@pytest.mark.unit
class TestNewCountsComputation:

    def test_never_visited_category_has_no_badge(self, client, db_session):
        """No badge for a category the user has never visited."""
        author = _make_user(db_session, 'nc_never_visited_author')
        cat = _make_category(db_session, 'nc_never_visited_slug', label='Never Visited Cat')
        _make_article(db_session, author, category=cat.slug)
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        # No last-visit record → no badge for this category
        assert b'Never Visited Cat' in resp.data
        assert b'new since your last visit' not in resp.data

    def test_no_badge_when_all_content_predates_last_visit(self, client, db_session):
        """No badge when every article/link was created before the user last visited."""
        author = _make_user(db_session, 'nc_all_old_author')
        cat = _make_category(db_session, 'nc_all_old_slug', label='All Old Cat')
        old_article_time = datetime.datetime(2024, 1, 1)
        _make_article(db_session, author, category=cat.slug, created_at=old_article_time)
        # Last visit is AFTER the article was created
        _make_last_visit(db_session, author, cat.slug,
                         datetime.datetime(2024, 6, 1))
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'new since your last visit' not in resp.data

    def test_single_new_article_produces_badge_count_one(self, client, db_session):
        """One article created after last visit yields a badge showing count = 1."""
        author = _make_user(db_session, 'nc_one_new_author')
        cat = _make_category(db_session, 'nc_one_new_slug', label='One New Cat')
        last_visit_time = datetime.datetime(2024, 1, 1)
        new_article_time = datetime.datetime(2024, 6, 1)  # after last visit
        _make_last_visit(db_session, author, cat.slug, last_visit_time)
        _make_article(db_session, author, category=cat.slug, created_at=new_article_time)
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'1 new since your last visit' in resp.data

    def test_multiple_new_articles_show_summed_count(self, client, db_session):
        """Three new articles after last visit produce a badge showing count = 3."""
        author = _make_user(db_session, 'nc_multi_new_author')
        cat = _make_category(db_session, 'nc_multi_new_slug', label='Multi New Cat')
        last_visit_time = datetime.datetime(2024, 1, 1)
        new_time = datetime.datetime(2024, 6, 1)
        _make_last_visit(db_session, author, cat.slug, last_visit_time)
        for i in range(3):
            _make_article(db_session, author, title=f'New Article {i}',
                          category=cat.slug, created_at=new_time)
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'3 new since your last visit' in resp.data

    def test_old_and_new_articles_only_new_counted(self, client, db_session):
        """Old articles (before last visit) are excluded; only new ones are counted."""
        author = _make_user(db_session, 'nc_mixed_author')
        cat = _make_category(db_session, 'nc_mixed_slug', label='Mixed Cat')
        last_visit_time = datetime.datetime(2024, 3, 1)
        _make_last_visit(db_session, author, cat.slug, last_visit_time)
        _make_article(db_session, author, title='Old Article', category=cat.slug,
                      created_at=datetime.datetime(2024, 1, 1))   # before lv
        _make_article(db_session, author, title='New Article', category=cat.slug,
                      created_at=datetime.datetime(2024, 6, 1))   # after lv
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'1 new since your last visit' in resp.data

    def test_new_link_counted_in_badge(self, client, db_session):
        """A link added after last visit contributes to the new_counts badge."""
        author = _make_user(db_session, 'nc_link_author')
        cat = _make_category(db_session, 'nc_link_slug', label='New Link Cat')
        last_visit_time = datetime.datetime(2024, 1, 1)
        _make_last_visit(db_session, author, cat.slug, last_visit_time)
        _make_link(db_session, author, category=cat.slug,
                   created_at=datetime.datetime(2024, 6, 1))
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'1 new since your last visit' in resp.data

    def test_mixed_new_article_and_link_summed(self, client, db_session):
        """One new article plus one new link produces badge count = 2."""
        author = _make_user(db_session, 'nc_article_link_author')
        cat = _make_category(db_session, 'nc_article_link_slug', label='Article Link Cat')
        last_visit_time = datetime.datetime(2024, 1, 1)
        new_time = datetime.datetime(2024, 6, 1)
        _make_last_visit(db_session, author, cat.slug, last_visit_time)
        _make_article(db_session, author, category=cat.slug, created_at=new_time)
        _make_link(db_session, author, category=cat.slug, created_at=new_time)
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'2 new since your last visit' in resp.data

    def test_new_counts_are_personal(self, client, db_session):
        """Another user's last-visit timestamp does not affect the logged-in user's badge."""
        user_a = _make_user(db_session, 'nc_personal_a')
        user_b = _make_user(db_session, 'nc_personal_b')
        cat = _make_category(db_session, 'nc_personal_slug', label='Personal Cat')
        new_time = datetime.datetime(2024, 6, 1)
        # user_a visited long ago → should see a badge
        _make_last_visit(db_session, user_a, cat.slug, datetime.datetime(2024, 1, 1))
        # user_b visited recently → should see no badge
        _make_last_visit(db_session, user_b, cat.slug, datetime.datetime(2025, 1, 1))
        _make_article(db_session, user_a, category=cat.slug, created_at=new_time)
        # Log in as user_b — user_b's last visit is after the article, so no badge
        _login(client, user_b.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'new since your last visit' not in resp.data

    def test_draft_articles_from_other_users_not_counted(self, client, db_session):
        """Other users' draft articles are not visible and not counted in new_counts."""
        viewer = _make_user(db_session, 'nc_draft_viewer')
        other = _make_user(db_session, 'nc_draft_other')
        cat = _make_category(db_session, 'nc_draft_slug', label='Draft Count Cat')
        last_visit_time = datetime.datetime(2024, 1, 1)
        new_time = datetime.datetime(2024, 6, 1)
        _make_last_visit(db_session, viewer, cat.slug, last_visit_time)
        _make_article(db_session, other, title='Other Draft', category=cat.slug,
                      is_draft=True, created_at=new_time)
        _login(client, viewer.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        # Draft from another user must not produce a badge for the viewer
        assert b'new since your last visit' not in resp.data


# ── index() — badge template rendering ───────────────────────────────────────

@pytest.mark.unit
class TestNewCountsBadgeTemplate:

    def test_badge_count_number_displayed(self, client, db_session):
        """The badge renders the numeric count from new_counts."""
        author = _make_user(db_session, 'badge_tmpl_count_author')
        cat = _make_category(db_session, 'badge_tmpl_count_slug', label='Badge Count Cat')
        last_visit_time = datetime.datetime(2024, 1, 1)
        new_time = datetime.datetime(2024, 6, 1)
        _make_last_visit(db_session, author, cat.slug, last_visit_time)
        _make_article(db_session, author, category=cat.slug, created_at=new_time)
        _make_article(db_session, author, title='Second New', category=cat.slug,
                      created_at=new_time)
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'2 new since your last visit' in resp.data

    def test_badge_has_red_text_class(self, client, db_session):
        """The badge span carries the text-red-600 CSS class."""
        author = _make_user(db_session, 'badge_tmpl_red_author')
        cat = _make_category(db_session, 'badge_tmpl_red_slug', label='Red Badge Cat')
        last_visit_time = datetime.datetime(2024, 1, 1)
        new_time = datetime.datetime(2024, 6, 1)
        _make_last_visit(db_session, author, cat.slug, last_visit_time)
        _make_article(db_session, author, category=cat.slug, created_at=new_time)
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'text-red-600' in resp.data

    def test_badge_absent_when_no_new_content(self, client, db_session):
        """No badge element when there are no new items since last visit."""
        author = _make_user(db_session, 'badge_absent_author')
        cat = _make_category(db_session, 'badge_absent_slug', label='Badge Absent Cat')
        old_time = datetime.datetime(2024, 1, 1)
        _make_article(db_session, author, category=cat.slug, created_at=old_time)
        # last visit is after the article, so nothing is "new"
        _make_last_visit(db_session, author, cat.slug, datetime.datetime(2024, 6, 1))
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'new since your last visit' not in resp.data

    def test_badge_absent_for_never_visited_category(self, client, db_session):
        """No badge for a category that the user has never visited (no last-visit row)."""
        author = _make_user(db_session, 'badge_never_author')
        cat = _make_category(db_session, 'badge_never_slug', label='Never Badge Cat')
        _make_article(db_session, author, category=cat.slug)
        _login(client, author.id)
        resp = client.get('/knowhow/')
        assert resp.status_code == 200
        assert b'Never Badge Cat' in resp.data
        assert b'new since your last visit' not in resp.data


# ── Model: KnowhowLastVisit ───────────────────────────────────────────────────

@pytest.mark.unit
class TestKnowhowLastVisitModel:

    def test_composite_pk_prevents_duplicate_rows(self, db_session):
        """Inserting a second row with the same (user_id, category_slug) raises IntegrityError."""
        user = _make_user(db_session, 'model_lv_dup_user')
        lv1 = KnowhowLastVisit(
            user_id=user.id, category_slug='dup_slug',
            visited_at=datetime.datetime(2024, 1, 1),
        )
        db_session.add(lv1)
        db_session.commit()
        lv2 = KnowhowLastVisit(
            user_id=user.id, category_slug='dup_slug',
            visited_at=datetime.datetime(2024, 6, 1),
        )
        db_session.add(lv2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_records_are_personal_per_user(self, db_session):
        """Two users can each have their own last-visit row for the same slug."""
        user_a = _make_user(db_session, 'model_lv_personal_a')
        user_b = _make_user(db_session, 'model_lv_personal_b')
        time_a = datetime.datetime(2024, 1, 1)
        time_b = datetime.datetime(2024, 6, 1)
        db_session.add(KnowhowLastVisit(user_id=user_a.id, category_slug='shared_slug',
                                        visited_at=time_a))
        db_session.add(KnowhowLastVisit(user_id=user_b.id, category_slug='shared_slug',
                                        visited_at=time_b))
        db_session.commit()
        row_a = KnowhowLastVisit.query.filter_by(user_id=user_a.id, category_slug='shared_slug').first()
        row_b = KnowhowLastVisit.query.filter_by(user_id=user_b.id, category_slug='shared_slug').first()
        assert row_a is not None and row_b is not None
        assert row_a.visited_at == time_a
        assert row_b.visited_at == time_b

    def test_visited_at_persisted_correctly(self, db_session):
        """The visited_at timestamp is stored and retrieved without mutation."""
        user = _make_user(db_session, 'model_lv_ts_user')
        ts = datetime.datetime(2025, 6, 15, 9, 30, 0)
        lv = KnowhowLastVisit(user_id=user.id, category_slug='ts_slug', visited_at=ts)
        db_session.add(lv)
        db_session.commit()
        fetched = KnowhowLastVisit.query.filter_by(user_id=user.id, category_slug='ts_slug').first()
        assert fetched.visited_at == ts
