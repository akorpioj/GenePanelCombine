# Summary of Changes: v1.6

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


## LitReview Advanced Filters

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


## LitReview Review Feature — Genie Integration

### Overview
Adds a full article-categorization workflow ("LitReview Review") that lets users classify each article in a PubMed search result set (Useful / Possibly useful / Probably not useful / Not useful) and submit the classifications to the **Genie** gene-literature knowledge base. Genie classifications stored by previous reviews are fetched and displayed on the search-results page for instant context.

### Database
- New model `LitReviewSession` (`litreview_review_sessions`): tracks a gene-focused review session linked to a `LiteratureSearch`, storing the resolved Ensembl ID, gene symbol, status (`in_progress` / `complete`), and `submitted_to_genie` flag
- New model `LitReviewArticleCategory` (`litreview_article_categories`): one row per article per session, storing the integer category (0–4) and timestamp; unique constraint `(session_id, article_id)`
- Alembic migration `g2h3i4j5k6l7_add_litreview_review_tables.py` generated and applied

### `app/litreview/genie_service.py` (new)
- Singleton `GenieService` with lazy configuration from `GENIE_API_URL` / `GENIE_API_KEY`
- `lookup_gene(symbol)` → list of Ensembl IDs
- `get_gene_detail(ensembl_id)` → gene annotation dict (display name, chromosome, description)
- `get_omim_id(ensembl_id)` → OMIM ID string or `None`
- `get_categorizations(ensembl_id)` → list of `{pmid, category}` dicts stored in Genie
- `save_categorizations_bulk(ensembl_id, pmid_category_list)` → bulk-submit to Genie
- All methods are non-fatal wrappers with structured logging

### `app/litreview/routes.py` — new routes
- `GET /api/gene-lookup?q=<symbol>` — resolves gene symbol to Ensembl candidates with parallel detail+OMIM fetch via `ThreadPoolExecutor`
- `POST /api/reclassify` — saves a single PMID/category directly to Genie; used by the inline reclassify strip on the results page
- `GET /results/<id>/review/start` — gene-confirmation page (redirects to review if session exists)
- `POST /results/<id>/review/confirm-gene` — creates `LitReviewSession`, bulk-inserts category rows (pre-populated from Genie in a single write), redirects to review UI
- `GET /results/<id>/review` — main categorization UI; serializes articles to plain dicts for JSON safety
- `POST /results/<id>/review/categorize` — AJAX endpoint; updates `LitReviewArticleCategory` by PK + session ownership check
- `POST /results/<id>/review/finish` — commits `status='complete'` first (so UI reflects done regardless), then submits to Genie; `submitted_to_genie` flag updated on success
- `GET /results/<id>` (`search_results`) updated: resolves `genie_ensembl_id` from session or by iterating all Ensembl IDs returned by `lookup_gene` (picks first with data); honours `?ensembl_id=` query-param override; passes `genie_categories`, `genie_unclassified_count`, `genie_ensembl_id` to template

### Templates
- **`review_start.html`** (new): gene-confirmation page with 5-state JS machine (loading → single match / multiple matches / not found / manual entry); hidden form POSTs `ensembl_id` + `gene_symbol`
- **`review.html`** (new): article-by-article categorization with progress bar, 4 category buttons, keyboard shortcuts 1–4, "Save & exit" (navigates immediately, saves in background with `keepalive: true`)
- **`results.html`** updated:
  - Each article card has a **clickable colored left strip** (green/amber/orange/red/gray) reflecting its Genie category; clicking opens an inline reclassify dialog that saves to Genie without a page reload
  - Ensembl ID shown as a link to Ensembl (e.g. `https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG…`) with a **"Wrong gene?"** button that opens a gene-lookup modal (same UX as `review_start.html`) and reloads with `?ensembl_id=<new>`
  - Color legend row with **"What is Genie?"** button that opens an explanatory popup
  - **Start LitReview** button only shown when `genie_unclassified_count > 0` (hidden when all articles are already classified); sub-label shows unclassified count
  - **Continue Review** button with `N / total categorized` sub-label when a session is `in_progress`
  - **Review complete ✓** badge when session is `complete`
  - Save-exit toast: `?save_exit=1` query param triggers "Progress saved ✓" notification on the results page after background save
- **`history.html`** updated: fixed `csrf_token()` → `session['csrf_token']` (app uses custom session-based CSRF, not Flask-WTF)

### Bug fixes during development
- `logging().debug(…)` → `log.debug(…)` (module was being called as a function)
- `LitReviewArticleCategory` lookup used `article_id` FK column instead of `id` PK — fixed to match what the frontend sends (`cat_id`)
- `status='complete'` now committed before Genie submission so the UI always reflects the final state; Genie failure is non-fatal with a warning flash
- Duplicate `bulk_save_objects` call on same objects caused `23505 unique constraint` violation — fixed by fetching Genie prior categorizations before any DB write and applying them at construction time (single write)
- Missing `@litreview_bp.route` decorator on `review_start` (accidentally dropped during editing) restored


## Panel Library — Genie Integration & Gene Detail Page

### "Add Genes to Genie" Wizard (Panel Library)
- New full-page wizard at `GET /panels/<panel_id>/add-to-genie` rendered by `panel_genie_export.html`
- Per-gene state machine: each gene card transitions through lookup → candidate selection → registration
- Bulk operations replace all one-by-one API fan-outs:
  - Ensembl ID resolution: single `POST /genes/ensembl-ids` via `genie_service.lookup_genes_bulk()`
  - Gene registration: single `POST /genes` via `genie_service.create_genes_bulk()` (server skips existing genes)
  - OMIM lookup: single `POST /genes/omim-ids` via `genie_service.get_omim_ids_bulk()`
- `_build_candidates_bulk()` helper in `litreview/routes.py` fetches gene detail in parallel (ThreadPoolExecutor) then makes one bulk OMIM call, replacing N individual `_build_candidate` calls
- New `POST /litreview/api/gene-lookup-bulk` route accepts `{"symbols": [...]}` and returns all candidates in one response
- `api_panel_add_to_genie` (POST) refactored: partitions genes into to-register / skip, calls `create_genes_bulk` once, writes resolved Ensembl IDs back to `PanelGene` records, commits once
- Fixed "Unexpected token '<'" error by adding `resp.ok` guards before `.json()` calls in the wizard template

### Inline Genie Status in Panel Details Modal
- New `GET /api/user/panels/<id>/genie-status` route: collects stored Ensembl IDs; for genes without a stored ID, bulk-resolves by symbol via `lookup_genes_bulk`, then calls `check_genes` once
- `_updateGenieStatusBadges(panelId)` added to `PanelActionsManager.js`: fetches the status endpoint and injects teal "✓ In Genie" badge into each gene card's `.genie-status-badge` slot
- Gene cards now carry both `data-ensembl-id` and `data-gene-symbol` attributes; badge injection falls back to symbol-based matching for genes whose Ensembl ID is not yet stored locally
- "Add genes to Genie" button (`#genie-add-btn`) is automatically hidden when every gene in the panel is already registered in Genie

### Gene Card UI (Panel Details Modal)
- Numeric confidence badge replaced with traffic-light coloured dot: green (`bg-green-500`) for level 3, amber (`bg-amber-400`) for level 2, red (`bg-red-500`) for level 1; dot has a tooltip
- Layout: outer `flex justify-between`; gene info (symbol + dot + name + Ensembl ID) fills `flex-1 min-w-0`; Genie badge sits as a `shrink-0` sibling on the right
- Ensembl ID displayed left-aligned in monospace below the gene name

### Panel Library Search
- `get_panels()` in `panel_library_utils.py` extended to search panel **name**, **description**, and **gene symbols** (case-insensitive `ilike` with an `EXISTS` subquery on `PanelGene`)
- Both the paginated query and the totals query use identical filter logic
- `exists` imported from `sqlalchemy` to support the subquery

### Gene Detail Page
- New `GET /genes/<ensembl_id>` route (`gene_detail_page`) in `routes_panel_library.py`:
  - Validates Ensembl ID format (`^ENSG\d{6,}$`)
  - Fetches gene annotation via `genie_service.get_gene_detail()`
  - Checks Genie registration via `genie_service.check_genes()`
  - Fetches OMIM ID (only if gene is already in Genie)
  - Renders `main/gene_detail.html`
- New `POST /api/genes/<ensembl_id>/register` API route (`api_gene_register`): registers the gene via `create_genes_bulk`, idempotent
- New template `app/templates/main/gene_detail.html`:
  - **Gene found & in Genie**: annotation card (name, description, chromosome, coordinates, biotype, assembly, OMIM), external links to Ensembl / GeneCards / OMIM, teal "In Genie" badge
  - **Gene found but not in Genie**: same annotation card + amber prompt with "Add to Genie" button; JS POSTs to register endpoint and on success updates badge and replaces prompt with confirmation
  - **Unknown Ensembl ID**: error box
  - **Service unavailable**: amber warning banner


## LitReview Performance & Genie Reclassify Fix

### Async Genie loading on search-results page
- `search_results` route previously blocked ~8 s per request on three sequential Genie API calls (`lookup_gene`, `check_genes`, `get_categorizations`) before sending any HTML
- All Genie logic moved to a new endpoint `GET /litreview/api/results/<id>/genie-context` that returns `{ensembl_id, categories}` as JSON
- `search_results` now returns immediately after DB queries (sub-second); the browser fetches Genie data client-side after the page is displayed
- `results.html` updated for progressive enhancement:
  - Article left-border strips default to gray (`bg-gray-200`) at render time
  - Genie context bar (Ensembl ID + "Wrong gene?" button) and colour legend start hidden
  - "Start LitReview" button replaced with a small "Loading Genie…" spinner; the real button is revealed once data arrives
  - Async loader script fetches `/genie-context`, then updates strip colours, legend, context bar, LitReview button, and the reclassify modal's `ENSEMBL_ID` in one callback

### N+1 SQL query fix
- `search.results.options(joinedload(...))` was silently ignored because `LiteratureSearch.results` is a `lazy='dynamic'` relationship — incompatible with `joinedload`
- Fixed by querying `SearchResult` directly: `db.session.query(SearchResult).options(joinedload(SearchResult.article)).filter(SearchResult.search_id == search_id)` — reduces 51 round-trips to 1 JOIN

### AuditService made fully non-blocking
- `AuditService.log_action` previously called `db.session.commit()` synchronously on every invocation, adding a Cloud SQL round-trip to every audited request
- Added a module-level `ThreadPoolExecutor(max_workers=4)` (`_audit_pool`) and helper `_write_audit_record(app, row)`
- `log_action` now captures all request-context values (user ID, username, IP, user agent, session ID, serialised JSON blobs) synchronously on the request thread, then submits only the DB write to the pool and returns immediately
- All 142 call sites across 10 files benefit automatically; no call-site changes required
- Removed leftover `🔍 AUDIT DEBUG` log lines that were spamming the application log

### Genie reclassify fix
- `api_reclassify` route previously used `POST /pmids/bulk` (add-only); existing classifications were silently skipped and the old category was restored on page refresh
- Genie API added `PATCH /gene/id:{ensembl_id}/pmids/{pmid}` (single) and `PATCH /gene/id:{ensembl_id}/pmids` (bulk) endpoints that support updates
- Added `_patch()` helper to `GenieService`, plus `update_categorization()` and `update_categorizations_bulk()` public methods
- `api_reclassify` now: PATCHes first (update existing), falls back to POST bulk only on 404 (PMID not yet stored in Genie); any other error returns 502 with a clear message
- Removed the previous 409-handling workaround from the template JS

