"""
Tests for Feature 4 — Article Tags.

Covers:
  _sync_tags() behaviour (via POST /knowhow/articles and POST /knowhow/articles/<id>/edit)
    - Tags submitted on create are persisted to the article
    - Tags are normalised to lowercase
    - Tags are trimmed of whitespace
    - Tags longer than 64 characters are truncated
    - Empty / whitespace-only tag entries are ignored
    - Submitting no tags results in no tags on the article
    - _sync_tags replaces the full tag set on update (old tags removed)
    - Re-used tag label reuses the same KnowhowTag row (no duplicate rows)
    - Comma-separated list creates multiple tags

  GET /knowhow/tags/<label>  (tag_articles)
    - Returns 200 for a logged-in user
    - Anonymous user is redirected
    - Non-existent tag label returns 404
    - Only articles with that tag are shown
    - Draft articles are hidden from regular users
    - Draft articles ARE shown to the author
    - Articles with that tag display a link to the tag page

  Tag display
    - Tag badge links appear on the article view page
    - Tag badge links appear on the index page (/knowhow/)
    - Tag badge links appear on the category page
    - An article with no tags renders no tag badges

  Model: KnowhowTag
    - label column has a unique constraint
    - association table FK cascade: removing article removes association rows
"""
import pytest
from app.models import db, User, UserRole, KnowhowArticle, KnowhowTag

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


def _post_create(client, title, tags, category=_SLUG):
    """POST to the create-article route and follow to the article view."""
    return client.post('/knowhow/articles', data={
        'title': title,
        'category': category,
        'content': '<p>Body.</p>',
        'tags': tags,
        'action': 'publish',
    }, follow_redirects=True)


def _post_update(client, article_id, title, tags, category=_SLUG):
    """POST to the update-article route and follow to the article view."""
    return client.post(f'/knowhow/articles/{article_id}/edit', data={
        'title': title,
        'category': category,
        'content': '<p>Body.</p>',
        'tags': tags,
        'action': 'publish',
    }, follow_redirects=True)


# ── _sync_tags via create_article ─────────────────────────────────────────────

@pytest.mark.unit
class TestSyncTagsOnCreate:
    def test_tags_persisted_on_create(self, client, db_session):
        user = _make_user(db_session, 'tag_create_user')
        _login(client, user.id)
        _post_create(client, 'Tagged Article', 'acmg, ngs')
        article = KnowhowArticle.query.filter_by(title='Tagged Article').first()
        labels = {t.label for t in article.tags.all()}
        assert labels == {'acmg', 'ngs'}

    def test_tags_normalised_to_lowercase(self, client, db_session):
        user = _make_user(db_session, 'tag_lower_user')
        _login(client, user.id)
        _post_create(client, 'Case Article', 'ACMG, NGS, PanelApp')
        article = KnowhowArticle.query.filter_by(title='Case Article').first()
        labels = {t.label for t in article.tags.all()}
        assert labels == {'acmg', 'ngs', 'panelapp'}

    def test_tags_trimmed_of_whitespace(self, client, db_session):
        user = _make_user(db_session, 'tag_trim_user')
        _login(client, user.id)
        _post_create(client, 'Trim Article', '  acmg  ,  ngs  ')
        article = KnowhowArticle.query.filter_by(title='Trim Article').first()
        labels = {t.label for t in article.tags.all()}
        assert labels == {'acmg', 'ngs'}

    def test_tags_truncated_at_64_chars(self, client, db_session):
        user = _make_user(db_session, 'tag_trunc_user')
        _login(client, user.id)
        long_label = 'x' * 80
        _post_create(client, 'Truncated Tag Article', long_label)
        article = KnowhowArticle.query.filter_by(title='Truncated Tag Article').first()
        labels = {t.label for t in article.tags.all()}
        assert len(list(labels)) == 1
        assert len(list(labels)[0]) == 64

    def test_empty_tag_entries_ignored(self, client, db_session):
        user = _make_user(db_session, 'tag_empty_user')
        _login(client, user.id)
        _post_create(client, 'Empty Tags Article', ',  ,  , acmg ,  ,')
        article = KnowhowArticle.query.filter_by(title='Empty Tags Article').first()
        labels = {t.label for t in article.tags.all()}
        assert labels == {'acmg'}

    def test_no_tags_submitted_means_no_tags(self, client, db_session):
        user = _make_user(db_session, 'tag_none_user')
        _login(client, user.id)
        _post_create(client, 'No Tags Article', '')
        article = KnowhowArticle.query.filter_by(title='No Tags Article').first()
        assert article.tags.count() == 0

    def test_reused_label_creates_single_tag_row(self, client, db_session):
        """Two articles sharing a tag label must share one KnowhowTag row."""
        user = _make_user(db_session, 'tag_reuse_user')
        _login(client, user.id)
        _post_create(client, 'First Shared Tag Article', 'shared')
        _post_create(client, 'Second Shared Tag Article', 'shared')
        assert KnowhowTag.query.filter_by(label='shared').count() == 1

    def test_multiple_comma_separated_tags(self, client, db_session):
        user = _make_user(db_session, 'tag_multi_user')
        _login(client, user.id)
        _post_create(client, 'Multi Tag Article', 'alpha, beta, gamma')
        article = KnowhowArticle.query.filter_by(title='Multi Tag Article').first()
        assert article.tags.count() == 3


# ── _sync_tags via update_article ─────────────────────────────────────────────

@pytest.mark.unit
class TestSyncTagsOnUpdate:
    def test_update_replaces_tags(self, client, db_session):
        """Updating with a new tag set removes old tags and adds new ones."""
        user = _make_user(db_session, 'tag_upd_user')
        article = _make_article(db_session, user, 'Update Tags Article')
        _login(client, user.id)
        _post_update(client, article.id, 'Update Tags Article', 'old1, old2')
        assert {t.label for t in article.tags.all()} == {'old1', 'old2'}
        _post_update(client, article.id, 'Update Tags Article', 'new1')
        db_session.expire(article)
        assert {t.label for t in article.tags.all()} == {'new1'}

    def test_update_with_empty_tags_clears_all_tags(self, client, db_session):
        user = _make_user(db_session, 'tag_clr_user')
        article = _make_article(db_session, user, 'Clear Tags Article')
        _login(client, user.id)
        _post_update(client, article.id, 'Clear Tags Article', 'keep')
        assert article.tags.count() == 1
        _post_update(client, article.id, 'Clear Tags Article', '')
        db_session.expire(article)
        assert article.tags.count() == 0

    def test_update_does_not_duplicate_shared_tag(self, client, db_session):
        """Updating two articles to share the same tag must not duplicate the tag row."""
        user = _make_user(db_session, 'tag_nodup_user')
        a1 = _make_article(db_session, user, 'No Dup Article One')
        a2 = _make_article(db_session, user, 'No Dup Article Two')
        _login(client, user.id)
        _post_update(client, a1.id, 'No Dup Article One', 'shared-label')
        _post_update(client, a2.id, 'No Dup Article Two', 'shared-label')
        assert KnowhowTag.query.filter_by(label='shared-label').count() == 1


# ── GET /knowhow/tags/<label> ─────────────────────────────────────────────────

@pytest.mark.unit
class TestTagArticlesRoute:
    def test_returns_200_for_logged_in_user(self, client, db_session):
        user = _make_user(db_session, 'tag_route_user')
        _login(client, user.id)
        _post_create(client, 'Route Tag Article', 'mytag')
        resp = client.get('/knowhow/tags/mytag')
        assert resp.status_code == 200

    def test_anonymous_user_redirected(self, client, db_session):
        resp = client.get('/knowhow/tags/anything', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_nonexistent_tag_returns_404(self, client, db_session):
        user = _make_user(db_session, 'tag_404_user')
        _login(client, user.id)
        resp = client.get('/knowhow/tags/does-not-exist')
        assert resp.status_code == 404

    def test_only_tagged_articles_shown(self, client, db_session):
        user = _make_user(db_session, 'tag_filter_user')
        _login(client, user.id)
        _post_create(client, 'Tagged With Foo', 'foo')
        _post_create(client, 'Tagged With Bar', 'bar')
        resp = client.get('/knowhow/tags/foo')
        body = resp.get_data(as_text=True)
        assert 'Tagged With Foo' in body
        assert 'Tagged With Bar' not in body

    def test_draft_hidden_from_regular_user(self, client, db_session):
        author = _make_user(db_session, 'tag_draft_author')
        reader = _make_user(db_session, 'tag_draft_reader')
        # Author creates a draft with a tag directly in DB
        article = KnowhowArticle(
            title='Hidden Draft Tagged', category=_SLUG,
            content='x', user_id=author.id, is_draft=True,
        )
        db_session.add(article)
        db_session.commit()
        tag = KnowhowTag(label='drafttag'); db_session.add(tag); db_session.commit()
        article.tags.append(tag); db_session.commit()
        # Reader gets 200 but the draft article must not appear in the listing
        _login(client, reader.id)
        resp = client.get('/knowhow/tags/drafttag')
        assert resp.status_code == 200
        assert 'Hidden Draft Tagged' not in resp.get_data(as_text=True)

    def test_draft_visible_to_author_on_tag_page(self, client, db_session):
        author = _make_user(db_session, 'tag_draft_vis_author')
        article = KnowhowArticle(
            title='Author Draft Tagged', category=_SLUG,
            content='x', user_id=author.id, is_draft=True,
        )
        db_session.add(article)
        db_session.commit()
        tag = KnowhowTag(label='authortag'); db_session.add(tag); db_session.commit()
        article.tags.append(tag); db_session.commit()
        _login(client, author.id)
        resp = client.get('/knowhow/tags/authortag')
        assert 'Author Draft Tagged' in resp.get_data(as_text=True)


# ── Tag display ───────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestTagDisplay:
    def test_tag_badges_on_article_view(self, client, db_session):
        user = _make_user(db_session, 'tag_view_user')
        _login(client, user.id)
        _post_create(client, 'Badge View Article', 'viewtag')
        article = KnowhowArticle.query.filter_by(title='Badge View Article').first()
        resp = client.get(f'/knowhow/articles/{article.id}')
        body = resp.get_data(as_text=True)
        assert 'viewtag' in body
        assert '/knowhow/tags/viewtag' in body

    def test_no_tag_badges_when_article_has_no_tags(self, client, db_session):
        user = _make_user(db_session, 'tag_notags_user')
        _login(client, user.id)
        _post_create(client, 'No Badge Article', '')
        article = KnowhowArticle.query.filter_by(title='No Badge Article').first()
        resp = client.get(f'/knowhow/articles/{article.id}')
        # No tag links should be present in the tag section
        assert '/knowhow/tags/' not in resp.get_data(as_text=True)

    def test_tag_badges_on_index_page(self, client, db_session):
        user = _make_user(db_session, 'tag_index_user')
        _login(client, user.id)
        _post_create(client, 'Index Badge Article', 'indextag')
        resp = client.get('/knowhow/')
        body = resp.get_data(as_text=True)
        assert 'indextag' in body
        assert '/knowhow/tags/indextag' in body

    def test_tag_badges_on_category_page(self, client, db_session):
        user = _make_user(db_session, 'tag_cat_user')
        _login(client, user.id)
        _post_create(client, 'Category Badge Article', 'cattag')
        resp = client.get(f'/knowhow/category/{_SLUG}')
        body = resp.get_data(as_text=True)
        assert 'cattag' in body
        assert '/knowhow/tags/cattag' in body


# ── Model: KnowhowTag ─────────────────────────────────────────────────────────

@pytest.mark.unit
class TestKnowhowTagModel:
    def test_label_unique_constraint(self, db_session):
        """Two KnowhowTag rows with the same label must raise an IntegrityError."""
        from sqlalchemy.exc import IntegrityError
        db_session.add(KnowhowTag(label='unique-tag'))
        db_session.commit()
        db_session.add(KnowhowTag(label='unique-tag'))
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_association_rows_removed_when_article_deleted(self, client, db_session):
        """Deleting an article must remove its rows from knowhow_article_tags."""
        from app.models import knowhow_article_tags
        user = _make_user(db_session, 'tag_cascade_user')
        _login(client, user.id)
        _post_create(client, 'Cascade Delete Tag Article', 'cascadetag')
        article = KnowhowArticle.query.filter_by(title='Cascade Delete Tag Article').first()
        aid = article.id
        tag = KnowhowTag.query.filter_by(label='cascadetag').first()
        # Verify the association row exists
        count_before = db_session.execute(
            db.select(db.func.count()).select_from(knowhow_article_tags)
            .where(knowhow_article_tags.c.article_id == aid)
        ).scalar()
        assert count_before == 1
        # Delete article via HTTP (route handles db delete)
        _login(client, user.id)
        client.post(f'/knowhow/articles/{aid}/delete', follow_redirects=True)
        count_after = db_session.execute(
            db.select(db.func.count()).select_from(knowhow_article_tags)
            .where(knowhow_article_tags.c.article_id == aid)
        ).scalar()
        assert count_after == 0
        # The KnowhowTag row itself should still exist (not cascade-deleted)
        assert KnowhowTag.query.filter_by(label='cascadetag').count() == 1
