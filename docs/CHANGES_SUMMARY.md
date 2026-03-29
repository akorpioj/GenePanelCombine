# Summary of Changes: v1.5.5

## Fix: nh3 panic when saving KnowHow articles (29/03/2026)

Saving or updating a KnowHow article crashed the server with a Rust `PanicException` from the `ammonia` library (backend used by `nh3`):

```
assertion failed: self.tag_attributes.get("a").and_then(|a| a.get("rel")).is_none()
```

**Root cause:** `ammonia` owns the `rel` attribute on `<a>` elements — it injects `rel="noopener noreferrer"` itself when the `link_rel` parameter is set. Its internal assertion fires if `rel` also appears in `tag_attributes`. The `_QUILL_ATTRS["a"]` allowlist included `"rel"`, which triggered the conflict.

**Fix:** Removed `"rel"` from `_QUILL_ATTRS["a"]`. The `link_rel="noopener noreferrer"` argument to `nh3.clean()` continues to enforce the secure `rel` value on all sanitized links.

**Files changed:** `app/knowhow/routes.py`

---

## Feature: KnowHow category description display (29/03/2026)

Completed Feature 9 from `KNOWHOW_FUTURE_FEATURES.md`. `KnowhowCategory` already has a `description` field editable via the admin panel, but it was never shown to regular users on the category detail page.

**User-facing behaviour:**
- When a category has a description set, it now appears immediately below the coloured header bar on the category detail page (`/knowhow/category/<slug>`)
- Rendered as a light grey strip (`bg-gray-50`) with small italic text and a bottom border
- Categories without a description are unaffected — the block is entirely hidden

**Implementation details:**
- Single `{% if category.description %}…{% endif %}` block added to `category.html` after the closing `</div>` of the coloured header
- No route, model, or DB changes required

**Files changed:** `app/templates/knowhow/category.html`

---

## Feature: KnowHow bookmarks / reading list (29/03/2026)

Implemented Feature 3 from `KNOWHOW_FUTURE_FEATURES.md`. Users can now bookmark any KnowHow article to a personal reading list accessible from the KnowHow index.

**User-facing behaviour:**
- Every article view page shows a **Save / Saved** bookmark button (hollow/filled star) in the header alongside the Edit button; clicking toggles the bookmark without a page reload
- **My Reading List** link (amber, bookmark icon) added to the KnowHow index header
- Reading list page (`/knowhow/bookmarks`) shows all bookmarked articles newest-first with category colour badges, optional summaries, and an inline remove button per row
- Removing a bookmark from the reading list page removes the row from the DOM immediately; empty-state message appears when the list becomes empty
- Bookmarks are per-user; users cannot see each other's reading lists

**Implementation details:**
- `KnowhowBookmark(id, user_id FK CASCADE, article_id FK CASCADE, created_at)` added to `app/models.py`; `UniqueConstraint` on `(user_id, article_id)` prevents duplicates
- Alembic migration `0bd52c3d4e36_add_knowhow_bookmarks.py` generated and applied via `flask db upgrade`
- `POST /knowhow/articles/<id>/bookmark` — toggle route returning `{bookmarked: true/false}` JSON; bookmark additions are audit-logged
- `GET /knowhow/bookmarks` — reading list route; passes articles and a category slug→object dict for badge rendering
- `view_article()` extended to pass `bookmarked` bool to the template
- Client-side toggle uses `fetch()` with `credentials: 'same-origin'`; button class, icon fill, label text, and `title` attribute all updated in-place
- New template: `app/templates/knowhow/bookmarks.html`

**Files changed:** `app/models.py`, `app/knowhow/routes.py`, `app/templates/knowhow/article_view.html`, `app/templates/knowhow/index.html`, `app/templates/knowhow/bookmarks.html` *(new)*, `migrations/versions/0bd52c3d4e36_add_knowhow_bookmarks.py` *(new)*

---

## Feature: KnowHow "Helpful" reactions (29/03/2026)

Implemented Feature 6 from `KNOWHOW_FUTURE_FEATURES.md`. Users can now mark any KnowHow article as helpful with a single click; the count is shown on article cards across the site and a new `Most helpful first` sort option surfaces the most-reacted categories.

**User-facing behaviour:**
- Every article view page shows a thumbs-up **Helpful?** button in the header alongside the bookmark button; clicking toggles the reaction without a page reload and updates the count in the button
- Article authors see a read-only reaction count badge (no interactive button) on their own articles
- Reaction counts (thumbs-up icon + number) shown on article cards in the KnowHow index and category pages when the count is ≥ 1
- New **Most helpful first** option in the KnowHow index sort selector; sorts categories by their total reaction count descending

**Implementation details:**
- `KnowhowReaction(id, user_id FK CASCADE, article_id FK CASCADE, created_at)` added to `app/models.py`; `UniqueConstraint` on `(user_id, article_id)` prevents duplicate reactions
- Alembic migration `9d38c69c3c02_add_knowhow_reactions.py` generated and applied via `flask db upgrade`
- `POST /knowhow/articles/<id>/react` — toggle route returning `{reacted: bool, count: int}` JSON; returns 403 if the article belongs to the requesting user
- `view_article()` extended to pass `reacted` (bool) and `reaction_count` (int) to the template
- `index()` builds a `reaction_counts` dict `{article_id: count}` via a grouped SQLAlchemy query and passes it to the template; `most_helpful` sort branch sorts categories by total reaction count
- `category()` similarly builds a scoped `reaction_counts` dict filtered to articles in that category
- Client-side toggle uses `fetch()` with `credentials: 'same-origin'`; button class, SVG fill, label, count text, and `title` attribute all updated in-place

**Files changed:** `app/models.py`, `app/knowhow/routes.py`, `app/templates/knowhow/article_view.html`, `app/templates/knowhow/index.html`, `app/templates/knowhow/category.html`, `migrations/versions/9d38c69c3c02_add_knowhow_reactions.py` *(new)*

---

## Feature: KnowHow related articles (29/03/2026)

Implemented Feature 7 from `KNOWHOW_FUTURE_FEATURES.md`. Each article view page now surfaces up to 5 related articles from the same category below the article body, reducing dead-ends and encouraging exploration.

**User-facing behaviour:**
- A "Related articles" card list appears between the article body and the "← Back to" link when there are other articles in the same category
- Each row shows the category-colour bullet, the article title as a link, and the optional summary (truncated)
- The section is entirely hidden for articles that are the only entry in their category

**Implementation details:**
- `view_article()` queries up to 5 `KnowhowArticle` records with the same `category` slug, excluding the current article, ordered by `updated_at DESC`; result passed as `related` to the template
- Template: bordered list with `{% if related %}` guard; no DB changes required

**Files changed:** `app/knowhow/routes.py`, `app/templates/knowhow/article_view.html`

---

## Feature: KnowHow article tags (29/03/2026)

Implemented Feature 4 from `KNOWHOW_FUTURE_FEATURES.md`. Articles can now be tagged with free-text labels; tags link to a filtered view of all articles sharing that tag.

**User-facing behaviour:**
- Article editor gains a **Tags** text input (comma-separated, e.g. `acmg, ngs, panelapp`); tags are normalised to lowercase
- Tag badges (sky-blue pill links prefixed with `#`) shown in the article view header, on article cards in the KnowHow index, and on article cards in category pages
- Clicking a tag badge navigates to `GET /knowhow/tags/<label>` — a page listing all articles with that tag, ordered most-recently-updated first
- Tags on existing articles can be edited via the article editor; removing all tags from an article clears them

**Implementation details:**
- `KnowhowTag(id, label VARCHAR(64) unique)` model and `knowhow_article_tags(article_id FK, tag_id FK)` pure-join association table added to `app/models.py`; `KnowhowArticle.tags` relationship via `secondary='knowhow_article_tags'`
- Alembic migration `a63cbbd8ad61_add_knowhow_tags.py` generated and applied via `flask db upgrade`
- `_sync_tags(article, raw_tags)` helper parses comma-separated input, creates missing `KnowhowTag` rows, and replaces the article's tag set in one flush
- `KnowhowTag` imported in `routes.py`; `create_article()` and `update_article()` both call `_sync_tags`
- `GET /knowhow/tags/<label>` route (`tag_articles`) added; 404 if tag doesn't exist; audit-logged
- `index()` and `category()` routes build `article_tags: dict[article_id → list[KnowhowTag]]` with a single batch query (no N+1) and pass it to templates
- New template: `app/templates/knowhow/tag_articles.html`

**Files changed:** `app/models.py`, `app/knowhow/routes.py`, `app/templates/knowhow/article_editor.html`, `app/templates/knowhow/article_view.html`, `app/templates/knowhow/index.html`, `app/templates/knowhow/category.html`, `app/templates/knowhow/tag_articles.html` *(new)*, `migrations/versions/a63cbbd8ad61_add_knowhow_tags.py` *(new)*

---

## Feature: KnowHow article print/PDF export (29/03/2026)

Implemented Feature 10 from `KNOWHOW_FUTURE_FEATURES.md`. Articles can be printed or saved as PDFs directly from the browser.

**User-facing behaviour:**
- A **Print** button appears in the article view action row (alongside Bookmark, Helpful, and Edit)
- Clicking it triggers the browser print dialog (`window.print()`), which also enables "Save as PDF" in all modern browsers / OS print drivers
- The printed output shows only the article title, author/date, tags, and body — all navigation, buttons, related articles, and back-link are hidden

**Implementation details:**
- `@media print` CSS block added inline in `article_view.html`:
  - `body > header` (site nav) and all elements with class `no-print` are hidden (`display: none !important`)
  - `body` background is set to white and padding removed
  - `#article-card` shadow, padding, and `max-width` constraint are removed so body content fills the page
- `no-print` class added to: breadcrumb `<nav>`, action-buttons `<div>`, related articles `<div>`, back-link `<div>`
- `id="article-card"` added to the outer card wrapper for `@media print` targeting
- No DB changes; no new routes

**Files changed:** `app/templates/knowhow/article_view.html`

---
