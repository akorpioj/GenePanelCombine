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
- Priority order: explicit `?sort=` query param → saved cookie → default (`position`)
- Sort selector `<select onchange="this.form.submit()">` submits a GET form on change — no JavaScript framework needed
- `sort` context variable passed to template to keep the selected option highlighted

**Files changed:** `app/knowhow/routes.py`, `app/templates/knowhow/index.html`

---
