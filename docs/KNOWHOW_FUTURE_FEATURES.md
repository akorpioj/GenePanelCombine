# KnowHow — Future Feature Suggestions

_Last updated: 29/03/2026_

This document outlines potential enhancements to the KnowHow knowledge base, ordered roughly by implementation complexity and likely user value. Each suggestion notes which existing models or routes it builds on.

---

## 1. Full-text Search ✅ _Implemented 25/03/2026_

~~**Priority: High**~~

Users have no way to find content without knowing which category it lives in. A search box that queries article titles, article content, and link descriptions would significantly improve discoverability.

**Implemented as:**
- `GET /knowhow/search?q=<query>` route in `app/knowhow/routes.py`
- `ILIKE` queries on `KnowhowArticle.title`, `KnowhowArticle.content`, `KnowhowLink.description`, and `KnowhowLink.url`
- Results grouped into Articles and Links; up to 50 of each returned
- Match highlighting via `_highlight()` (`markupsafe.escape` + `<mark>` injection)
- Content snippets via `_snippet()` (strips HTML, extracts ±120 chars around first match)
- `_safe_like()` escapes `%` and `_` in user input (wildcard-injection protection)
- Search box added to KnowHow index header
- Searches are audit-logged
- New template: `app/templates/knowhow/search.html`

**DB changes:** None (uses `ILIKE`). Future upgrade path: `tsvector` generated column + GIN index on `knowhow_articles.content`.

---

## 2. Article Summary Field ✅ _Implemented 29/03/2026_

~~**Priority: High**~~

The index and category templates already contained `{% if article.summary %}` checks. Adding the model field, migration, and editor form field completes the intended design: a short plain-text teaser shown beneath article titles in list views.

**Implemented as:**
- `summary = db.Column(db.String(512), nullable=True)` added to `KnowhowArticle` in `app/models.py`
- Migration `b25d3df6625c_add_knowhow_article_summary.py` generated and applied via `flask db upgrade`
- Optional "Summary" textarea (max 512 chars, 2 rows) added between the Title and Category fields in `article_editor.html`
- `create_article()` and `update_article()` both read `request.form.get('summary', '').strip()` and validate `len(summary) <= 512`
- Existing `{% if article.summary %}` blocks in `index.html` and `category.html` now render automatically
- Summaries are not displayed on the article view page (the full article is shown there instead)

**DB changes:** One nullable `VARCHAR(512)` column added to `knowhow_articles`.

---

## 3. Bookmarks / Reading List ✅ _Implemented 29/03/2026_

~~**Priority: Medium**~~

Users can now bookmark articles for quick access via a personal reading list.

**Implemented as:**
- `KnowhowBookmark(id, user_id FK, article_id FK, created_at)` added to `app/models.py` with a `UniqueConstraint` on `(user_id, article_id)` and `CASCADE` deletes on both FKs
- `POST /knowhow/articles/<id>/bookmark` — toggle: removes bookmark if present, creates one if absent; returns `{bookmarked: true/false}` JSON; audits additions
- `GET /knowhow/bookmarks` — personal reading list page, newest bookmarks first, with category badges, summaries, and inline remove buttons
- Bookmark button (hollow/filled star) added to the article view header alongside the Edit button; state toggled client-side via `fetch()` without page reload
- "My Reading List" amber link added to the KnowHow index header
- Alembic migration `0bd52c3d4e36_add_knowhow_bookmarks.py` generated and applied
- New template: `app/templates/knowhow/bookmarks.html`

**DB changes:** New `knowhow_bookmarks` table.

---

## 4. Article Tags

**Priority: Medium**

Categories and subcategories provide a fixed two-level hierarchy. Tags offer a flexible cross-cutting dimension — e.g., tagging articles with `ACMG`, `PanelApp`, `NGS`, `OMIM` — that is not possible with the current structure.

**Suggested implementation:**
- New model: `KnowhowTag(id, label VARCHAR(64) unique)` and an association table `knowhow_article_tags(article_id, tag_id)`
- Free-text tag input in `article_editor.html` (comma-separated, client-side tokenisation)
- Tags displayed as small coloured badges on article cards and the article view header
- Clicking a tag navigates to `GET /knowhow/tags/<label>` — a filtered list of all articles with that tag
- Tags available as additional filter on the search results page (Feature 1)

**DB changes:** `knowhow_tags` table + `knowhow_article_tags` association table.

---

## 5. Draft / Publish Workflow

**Priority: Medium**

Currently all saved articles are immediately visible to all logged-in users. Drafts let authors work across multiple sessions before publishing, and allow EDITOR/ADMIN review before release.

**Suggested implementation:**
- Add `is_draft = db.Column(db.Boolean, default=False, nullable=False)` to `KnowhowArticle`
- The article editor gains a "Save as Draft" button alongside "Publish"
- Draft articles are visible only to their author, EDITORs, and ADMINs
- Index and category routes add `filter(or_(KnowhowArticle.is_draft == False, KnowhowArticle.user_id == current_user.id, current_user.role.in_([EDITOR, ADMIN])))` to the article query
- Draft articles show a muted "DRAFT" badge in list views and the article header
- Admin category management page can show a count of unpublished drafts per category

**DB changes:** One non-nullable boolean column on `knowhow_articles`.

---

## 6. "Helpful" Reactions

**Priority: Low–Medium**

A lightweight single-click reaction (e.g., "👍 Helpful") gives authors feedback without the complexity of a full comment system, and surfaces the most useful articles.

**Suggested implementation:**
- New model: `KnowhowReaction(id, user_id FK, article_id FK, created_at)` with unique constraint on `(user_id, article_id)`
- `POST /knowhow/articles/<id>/react` — toggle reaction; JSON response
- Display reaction count next to a thumbs-up icon on article cards and the article view
- Add `most_helpful` sort option to the index page sort selector (Feature already exists, just add one more option)
- Users cannot react to their own articles

**DB changes:** New `knowhow_reactions` table.

---

## 7. Related Articles

**Priority: Low–Medium**

At the bottom of each article, surface 3–5 other articles from the same category or sharing tags (Feature 4), reducing dead-ends and encouraging exploration.

**Suggested implementation:**
- Computed in `view_article()`: query up to 5 articles in the same `category` slug, excluding the current article, ordered by `created_at DESC`
- If tags are implemented (Feature 4), weight articles sharing more tags higher
- Rendered as a small "Related articles" card below the article body in `article_view.html`
- No DB changes required for the simple same-category version

**DB changes:** None (basic); tag table needed for tag-weighted version.

---

## 8. Article Version History

**Priority: Low**

Track the full content of each article at the time of every save, allowing authors and admins to view and restore previous versions.

**Suggested implementation:**
- New model: `KnowhowArticleRevision(id, article_id FK, content TEXT, title VARCHAR(256), edited_by FK User, edited_at DateTime)`
- On every `update_article()` call, write the *old* content to `KnowhowArticleRevision` before applying the new values
- New route `GET /knowhow/articles/<id>/history` lists all revisions (admin/EDITOR/author only)
- Diff view: compare current vs a chosen revision using Python `difflib.unified_diff`
- Restore button available to ADMIN/EDITOR

**DB changes:** New `knowhow_article_revisions` table. Can grow large; consider keeping only the last _N_ revisions.

---

## 9. Category Description Display ✅ _Implemented 29/03/2026_

~~**Priority: Low**~~

`KnowhowCategory` already has a `description` field settable via the admin panel.

**Implemented as:**
- `{% if category.description %}` block added to `category.html` immediately below the coloured header bar
- Renders as a light grey `bg-gray-50` strip with `text-sm text-gray-600 italic` styling and a bottom border
- No route, model, or DB changes required

**DB changes:** None.

---

## 10. Print / PDF Export of Articles

**Priority: Low**

Clinical geneticists may want a clean printable version of a protocol or guide to carry to the lab or MDT meeting.

**Suggested implementation:**
- Add a `?format=print` variant of `view_article()` that renders a stripped-down template (`print_article.html`) without the navbar, sidebar, and edit buttons
- Or use the browser print API: add a "Print" button that calls `window.print()` and ship a `@media print` CSS block in `styles.css` that hides nav and sets body to full-width
- For true PDF generation: add `weasyprint` to `requirements.txt` and a `GET /knowhow/articles/<id>.pdf` route

**DB changes:** None.

---

## 11. Link Preview Cards

**Priority: Low**

External links currently show only a description and URL. Showing an Open Graph title/description/favicon would make the resource immediately recognisable.

**Suggested implementation:**
- On link creation, fetch the target URL server-side with `httpx` (timeout 5 s, no redirects to private IPs — SSRF protection required) and extract `og:title`, `og:description`, `og:image`
- Store as nullable columns on `KnowhowLink`: `og_title VARCHAR(256)`, `og_description VARCHAR(512)`, `og_image_url VARCHAR(2048)`
- Background task (Celery or a simple deferred fetch on next page load) to avoid blocking the add-link form submission
- Rendered as a small card with favicon in the link list items

**Security note:** Any server-side URL fetching must validate the resolved IP is not RFC-1918 (private) to prevent SSRF. Use an allowlist of schemes (`https` only) and validate after DNS resolution.

**DB changes:** Three nullable columns on `knowhow_links`.

---

## 12. "New Since Last Visit" Indicator

**Priority: Low**

A small badge on the index category cards (e.g., "2 new") showing articles or links added since the user last visited that category, encouraging return visits.

**Suggested implementation:**
- Store the user's last visit time per category in a `KnowhowLastVisit(user_id, category_slug, visited_at)` table, updated on each `category()` page load
- On `index()`, query for articles/links created after `last_visit.visited_at` per category slug and pass counts in a `new_counts` dict to the template
- Rendered as a small red dot or count badge on the category header in `index.html`

**DB changes:** New `knowhow_last_visits` table.

---

## Implementation Priority Summary

| # | Feature | Complexity | Value | DB Migration? |
|---|---------|-----------|-------|---------------|
| 1 | ~~Full-text search~~ ✅ implemented | Low | ★★★★★ | No |
| 2 | ~~Article summary field~~ ✅ implemented | Very low | ★★★★☆ | Yes — 1 column |
| 3 | ~~Bookmarks / reading list~~ ✅ implemented | Medium | ★★★★☆ | Yes — 1 table |
| 4 | Article tags | Medium | ★★★☆☆ | Yes — 2 tables |
| 5 | Draft / publish workflow | Medium | ★★★☆☆ | Yes — 1 column |
| 6 | "Helpful" reactions | Low | ★★★☆☆ | Yes — 1 table |
| 7 | Related articles | Low | ★★★☆☆ | No (basic) |
| 8 | Article version history | High | ★★☆☆☆ | Yes — 1 table |
| 9 | ~~Category description display~~ ✅ implemented | Very low | ★★☆☆☆ | No |
| 10 | Print / PDF export | Low | ★★☆☆☆ | No |
| 11 | Link preview cards | High | ★★☆☆☆ | Yes — 3 columns |
| 12 | "New since last visit" badge | Medium | ★★☆☆☆ | Yes — 1 table |

**Recommended next sprint:** Feature 6 (helpful reactions) is now the next lowest-complexity addition with a DB change. Feature 7 (related articles) requires no DB changes and could also be added quickly.
