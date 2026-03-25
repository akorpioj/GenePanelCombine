# Summary of Changes: v1.5.4

---

## Feature: KnowHow category sort order (25/03/2026)

Added a sort selector to the KnowHow index page allowing users to reorder categories. The selected sort is persisted in a browser cookie so it is remembered across sessions.

**Sort options:**
- **Custom order** — admin-defined position (default)
- **A → Z** — category label alphabetical ascending
- **Z → A** — category label alphabetical descending
- **Most content first** — categories with the highest combined article + link count appear first
- **Recently updated** — categories whose most recent article edit or link addition appears first

**Implementation details:**
- Sort applied in `app/knowhow/routes.py` `index()` after fetching categories; server-side Python sort on the list returned by `_get_categories()`
- `_VALID_SORTS` whitelist validated on every request; invalid values silently fall back to `position`
- Preference persisted in `knowhow_sort` cookie (1-year expiry, `httponly`, `SameSite=Lax`) via `make_response` + `set_cookie`

**Files changed:** `app/knowhow/routes.py`, `app/templates/knowhow/index.html`

---

## Feature: KnowHow category detail page (25/03/2026)

Each category header on the KnowHow index is now a link. Clicking it opens a dedicated page showing all articles and links for that category.

**Behaviour:**
- Category `h2` labels in the index are rendered as `<a>` links styled with `hover:underline` against the coloured header background
- The detail page shows the full content for one category: root-level articles and links, plus all subcategory folders with their content
- The Add Link modal is available on the category page so users can add links without navigating back to the index
- Breadcrumb on the article view page (`KnowHow › Category › Article`) links to the category detail page instead of anchoring the index

**Implementation details:**
- New route `GET /knowhow/category/<slug>` (`knowhow.category`) in `app/knowhow/routes.py`
- Queries articles and links for the given slug; builds `articles_map` and `links_map` keyed by `subcategory_id` (same pattern as index)
- Returns 404 for unknown slugs via `filter_by(slug=slug).first_or_404()`
- Audit log entry recorded on each category page view
- New template `app/templates/knowhow/category.html` — shares the same card structure and Add Link modal JS as the index

**Files changed:** `app/knowhow/routes.py`, `app/templates/knowhow/index.html`, `app/templates/knowhow/article_view.html`, `app/templates/knowhow/category.html` *(new)*

---

## Feature: KnowHow index — limit to 3 most recent articles per bucket (25/03/2026)

The KnowHow index now shows at most 3 articles per category/subcategory slot. A "see all" link appears when there are more.

**Behaviour:**
- Each root-level category bucket and each subcategory folder show the 3 most recently created articles
- If more than 3 articles exist in a bucket, a `+ N more article(s) — see all` link appears below, pointing to the category detail page
- The category detail page is unaffected and continues to show all articles
- Articles are ordered most-recent first (newest at the top)

**Implementation details:**
- Article query in `index()` changed from `ORDER BY created_at ASC` to `ORDER BY created_at DESC` so that `[:3]` in the template selects the newest items
- Template slices applied with `{% for article in root_articles[:3] %}` and `{% for article in sub_articles[:3] %}`
- Overflow count computed inline: `{{ root_articles|length - 3 }}` / `{{ sub_articles|length - 3 }}`
- Singular/plural handled via `{{ 's' if count != 1 }}`

**Files changed:** `app/knowhow/routes.py`, `app/templates/knowhow/index.html`

---

## Feature: KnowHow full-text search (25/03/2026)

Added a search page allowing users to search across all KnowHow article titles, article content (Quill HTML), and link descriptions/URLs. Results are highlighted and grouped by type.

**User-facing behaviour:**
- Search box added to the KnowHow index header; submits `GET /knowhow/search?q=`
- Minimum query length: 2 characters
- Results grouped into **Articles** and **Links** sections, each showing a category badge
- Articles show a highlighted content snippet centred on the first match (~240 chars with `…` ellipsis)
- Link results show the highlighted description and the full URL
- Up to 50 articles and 50 links returned per search
- Searches are audit-logged (query string, truncated to 256 chars)

**Implementation details:**
- `GET /knowhow/search` route in `app/knowhow/routes.py`
- `_safe_like(q)` — escapes `%` and `_` in user input before building the `ILIKE` pattern (wildcard-injection protection)
- `_strip_html(html)` — strips Quill HTML tags to produce plain text for snippeting; uses `re.sub` (no external parser dependency)
- `_highlight(text, query)` — HTML-escapes via `markupsafe.escape`, then wraps case-insensitive matches in `<mark class="bg-yellow-200 rounded px-0.5">`, returns `markupsafe.Markup`
- `_snippet(html, query)` — extracts `±120` chars around the first match, adds `…` ellipsis, calls `_highlight`; falls back to first 240 chars if query not found in plain text
- Database queries use SQLAlchemy `ilike` on `KnowhowArticle.title`, `KnowhowArticle.content`, `KnowhowLink.description`, `KnowhowLink.url` via `db.or_`
- Results ordered `created_at DESC`, capped with `.limit(50)` before `.all()`
- Template uses `| safe` on pre-escaped `Markup` strings — XSS-safe because all user-controlled text passes through `markupsafe.escape` before insertion

**Files changed:** `app/knowhow/routes.py` *(search helpers + route)*, `app/templates/knowhow/index.html` *(search box)*, `app/templates/knowhow/search.html` *(new)*
