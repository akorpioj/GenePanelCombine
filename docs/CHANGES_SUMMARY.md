# Summary of Changes: v1.5.6

## KnowHow Draft / Publish Workflow (Feature 5)

### Step 1 — `is_draft` DB column
- Added `is_draft = Boolean(nullable=False, default=False, server_default='false')` to `KnowhowArticle`
- Alembic migration generated and applied; all existing articles default to `is_draft=False` (published)

### Step 2 — Article editor: "Save as Draft" button
- Single submit button in `article_editor.html` replaced with two buttons: **Save as draft** (`action=draft`) and **Publish article** / **Publish changes** (`action=publish`)
- `create_article()` and `update_article()` routes read `action = request.form.get('action', 'publish')` and set `is_draft` accordingly
- Flash messages distinguish between `'Draft saved.'` and `'Article published.'` / `'Article updated.'`

### Step 3 — Draft filter on list routes
- `_draft_filter()` helper added to `routes.py`: ADMIN/EDITOR see all articles; USER role sees published articles plus their own drafts
- Applied to `index()`, `category()`, `search()`, and `tag_articles()` routes

### Step 4 — DRAFT badges in templates
- `article_view.html`: red `DRAFT` pill badge added next to the `<h1>` title; amber "not yet public" warning banner shown above the header — both conditional on `article.is_draft`
- `index.html` and `category.html`: small red `DRAFT` label added after the article title on article cards, conditional on `article.is_draft`

### Step 5 — "My Drafts" shortcut page
- New `GET /knowhow/drafts` route: USER sees their own drafts; EDITOR/ADMIN see all users' drafts; ordered by `updated_at DESC`
- New template `app/templates/knowhow/drafts.html`: article list with DRAFT badge and Edit button per row; empty state
- `index()` queries `user_draft_count` and passes it to `index.html`; a conditional "My Drafts" link (red, with count badge) appears in the index header only when `user_draft_count > 0`

### Tests
- 57 unit tests across 5 test files (`test_knowhow_draft_step1–5.py`), all passing


## KnowHow Link Preview Cards (Feature 11)

### Step 1 — OG data columns on `KnowhowLink`
- Added three nullable columns to `KnowhowLink`: `og_title VARCHAR(256)`, `og_description VARCHAR(512)`, `og_image_url VARCHAR(2048)`
- Alembic migration `f1a2b3c4d5e6_add_og_columns_to_knowhow_links.py` generated and applied; all existing links default to `NULL` for the new columns
- 23 unit tests in `test_knowhow_link_preview_step1.py`, all passing

### Step 2 — SSRF-safe OG metadata fetcher
- New module `app/knowhow/og_utils.py` with `_fetch_og_data(url: str) -> dict`
- Rejects non-`https://` schemes before making any network call
- Resolves the target hostname via DNS first and rejects private/loopback/link-local IP ranges (SSRF protection)
- Fetches with `httpx.get(timeout=5, follow_redirects=False)`; parses `og:title`, `og:description`, `og:image` meta tags with stdlib `html.parser`; falls back to `<title>` for `og_title`
- Always returns `{'og_title': …, 'og_description': …, 'og_image_url': …}` — never raises
- `httpx>=0.27` added to `requirements.txt`
- 33 unit tests in `test_knowhow_link_preview_step2.py`, all passing

### Step 3 — Populate OG data when a link is saved
- `app/knowhow/routes.py`: added `from .og_utils import _fetch_og_data` import
- `add_link()` route now creates the `KnowhowLink` object, calls `_fetch_og_data(url)` inside a `try/except` (best-effort; link is always committed even if the fetch raises), stores all three OG fields, then commits
- 15 unit tests in `test_knowhow_link_preview_step3.py`, all passing

### Step 4 — Render preview cards in templates
- `app/templates/knowhow/category.html` (root-link and sub-link blocks) and `app/templates/knowhow/index.html` (root-link and sub-link blocks) updated
- When `link.og_title` is set: renders a flex card containing an optional thumbnail (`<img>` from `og_image_url`), the OG title as the clickable link, an optional `og_description` paragraph, and the raw URL in small grey text
- When `link.og_title` is `None`: existing fallback — plain anchor with `link.description` as label — unchanged
- 20 unit tests in `test_knowhow_link_preview_step4.py`, all passing


## LitReview Advanced Filters (v1.6)

### Overview
Extended the PubMed search with four optional filters: date range, article type, publication status, and language. Filters are translated into PubMed E-utilities query clauses and are stored alongside each saved search for history display.

### `app/litreview/pubmed_service.py`
- Added class-level lookup tables `_DATE_RANGE_DAYS` and `_ARTICLE_TYPE_FILTERS`
- `search_by_gene()` gains four new optional parameters: `date_range`, `article_type`, `pub_status`, `language`
  - `date_range` (`6months` / `1year` / `5years`) appends a `[PDAT]` date-range clause
  - `article_type` (`review` / `clinical_trial` / `meta_analysis` / `case_report`) appends a publication-type `[pt]` clause
  - `pub_status` (`preprint` / `inpress`) appends `preprint[sb]` or `inprocess[sb]`; `published` requires no extra clause
  - `language` (e.g. `english`) appends a `[la]` language clause
- Redis cache key now includes all four filter values so different filter combinations are cached independently

### `app/litreview/routes.py`
- `search()` route reads the four new form fields (`date_range`, `article_type`, `pub_status`, `language`) from `request.form`
- All four are forwarded to `pubmed_service.search_by_gene()`
- All four are stored in the `search_params` JSON field of the saved `LiteratureSearch` record

### `app/templates/litreview/search.html`
- Added collapsible "Advanced Filters" section (toggle button with animated chevron) between the Max Results field and the Submit button
- Four `<select>` fields inside the panel: Date Range, Article Type, Publication Status, Language
- Inline JavaScript auto-expands the panel if any filter is already selected (e.g. after a validation error round-trip)


