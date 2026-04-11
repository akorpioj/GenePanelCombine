LitReview Review Feature

Preconditions: The user has done a gene specific search to PubMed, and the search results are shown on /litreview/results/ page.

In buttons row (where New Search, Download CSV, Download Excel buttons are), add new button "Start LitReview".

This starts a process in a new window/popup, where each of the search result articles are shown one-by-one to user one by one. 

But first, the gene name is verified by searhing it's Ensembl ID using the Genie API (details provided later). The fetched Ensembl ID, link to gene's Ensembl and OMIM web pages are shown to the user and the UI asks the user to confirm that this is the correct gene. If the user provided gene name is ambiguous (two or more Ensembl IDs are returned), UI asks the user to select the correct one. If no Ensembl ID is not found or the user says the ID is incorrect, the UI asks the user to provide the correct Ensembl ID.

After the correct Ensembl ID is confirmed, the categorization starts:

The user categorizes each article to one of these categories:
- Not useful
- Probably not useful
- Possibly useful
- Useful
All articles are by default in Uncategoried category until categorized. In future versions, the preliminary categorization is done by AI, but for now, the user does the categorization.

After the user has categorized all the articles (or has chosen to stop categorization (a button is provided)), the PMID and the category are sent with Genie API for storage.

If the categorization process is unfinished, the user can continue it from a button provided in the Pubmed search page. The app gets the stored PMIDs and categories for the gene with Genie API and restores the article details one-by-one from PubMed. The categorization continues with the uncategorized articles.

---

## LitReview Review Feature — Finalized Implementation Task List

### Category integer mapping
| Int | Label |
|-----|-------|
| 0 | Uncategorized (default) |
| 1 | Not useful |
| 2 | Probably not useful |
| 3 | Possibly useful |
| 4 | Useful |

---

### Task 1 — Configuration

**config_settings.py**
- [X] Add `GENIE_API_URL = os.getenv('GENIE_API_URL', 'http://127.0.0.1:8000')`
- [X] Add `GENIE_API_KEY = os.getenv('GENIE_SECRET_API_KEY')`

**.env / docs**
- [X] Add `GENIE_API_URL` and `GENIE_SECRET_API_KEY` to the env variable docs / `CONFIGURATION_GUIDE.md`

---

### Task 2 — Genie API service module

**`app/litreview/genie_service.py`** (new file)

- [X] `GenieService.__init__()` — reads `base_url` and `api_key` from app config lazily (same `_configured` pattern as `PubMedService`); raises `RuntimeError` at first use if key is missing
- [X] `lookup_gene(gene_symbol) -> list[str]` — `GET /gene/{gene_symbol}`, returns list of Ensembl IDs; returns `[]` on 404
- [X] `get_gene_detail(ensembl_id) -> dict` — `GET /gene/id:{ensembl_id}`, returns `gene_info` dict (`display_name`, `seq_region_name`/chromosome, `description`); returns `None` on 404
- [X] `get_omim_id(ensembl_id) -> str | None` — `GET /gene/id:{ensembl_id}/omim`, returns OMIM ID string or `None` on 404
- [X] `get_categorizations(ensembl_id) -> list[dict]` — `GET /gene/id:{ensembl_id}/pmids`, returns `[{"pmid": int, "category": int}, ...]`; returns `[]` on 404
- [X] `save_categorizations_bulk(ensembl_id, pmid_category_list) -> dict` — `POST /gene/id:{ensembl_id}/pmids/bulk`, body: `[{"pmid": int, "category": int}, ...]`; returns `{"added": [...], "skipped": [...]}`
- [X] Module-level singleton: `genie_service = GenieService()`

---

### Task 3 — Database models & migration

**models.py**

- [X] `LitReviewSession` model (`__tablename__ = 'litreview_review_sessions'`):
  - `id` SERIAL PK
  - `search_id` FK → `literature_searches.id` ON DELETE CASCADE, indexed
  - `user_id` FK → `users.id` ON DELETE CASCADE, indexed
  - `ensembl_id` VARCHAR(50) NOT NULL
  - `gene_symbol` VARCHAR(100) NOT NULL
  - `status` VARCHAR(20) NOT NULL default `'in_progress'` — values: `'in_progress'`, `'complete'`
  - `submitted_to_genie` Boolean default False
  - `created_at`, `updated_at`
  - Relationship: `categories` → `LitReviewArticleCategory` (cascade delete)

- [X] `LitReviewArticleCategory` model (`__tablename__ = 'litreview_article_categories'`):
  - `id` SERIAL PK
  - `session_id` FK → `litreview_review_sessions.id` ON DELETE CASCADE, indexed
  - `article_id` FK → `literature_articles.id` ON DELETE CASCADE, indexed
  - `pmid` VARCHAR(20) NOT NULL (denormalized for Genie API submission)
  - `category` Integer NOT NULL default `0`
  - `categorized_at` DateTime nullable
  - UniqueConstraint on `(session_id, article_id)`

**`migrations/versions/xxx_add_litreview_review_tables.py`** (new Alembic migration)
- [X] `upgrade()` creates both tables with indexes and constraints
- [X] `downgrade()` drops both tables in reverse order

---

### Task 4 — Backend routes

**routes.py**

**4a. Gene lookup API** (called by JS during gene confirmation step)
- [X] `GET /litreview/api/gene-lookup` — query param `q=<symbol_or_ensembl_id>` — calls `genie_service.lookup_gene(q)`, then for each Ensembl ID calls `get_gene_detail()` + `get_omim_id()` in parallel; returns JSON list of candidates:
  ```json
  [{"ensembl_id": "ENSG...", "display_name": "BRCA1", "chromosome": "17",
    "description": "...", "ensembl_url": "https://www.ensembl.org/...",
    "omim_url": "https://www.omim.org/entry/<omim_id>"}]
  ```
  Returns `{"candidates": [], "not_found": true}` when Genie returns 404

**4b. Start review** (gene confirmation page)
- [X] `GET /litreview/results/<int:search_id>/review/start` — `login_required`, ownership check; redirects to `/review` if a session already exists; renders `litreview/review_start.html` passing `search` and `search_term`

**4c. Confirm gene** (form POST from gene confirmation step)
- [X] `POST /litreview/results/<int:search_id>/review/confirm-gene` — `login_required`, ownership check; receives `ensembl_id` from form; creates `LitReviewSession`; bulk-inserts `LitReviewArticleCategory` rows (one per article from `search.results`, all `category=0`); also pre-populates from Genie API (`genie_service.get_categorizations(ensembl_id)`) to restore any prior submissions; redirects to `/review`

**4d. Review UI** (categorization page)
- [X] `GET /litreview/results/<int:search_id>/review` — `login_required`, ownership check; redirects to `/review/start` if no session found; queries `LitReviewArticleCategory` joined with `LiteratureArticle`; passes `session`, `articles_with_categories` (ordered by rank), `total`, `categorized_count`, `remaining_count` to template `litreview/review.html`

**4e. Categorize one article** (AJAX)
- [X] `POST /litreview/results/<int:search_id>/review/categorize` — `login_required`, JSON in: `{"article_id": int, "category": int}` (1–4); validates `1 <= category <= 4`; updates `LitReviewArticleCategory.category` and `categorized_at`; returns JSON `{"ok": true, "remaining": int}`

**4f. Finish review**
- [X] `POST /litreview/results/<int:search_id>/review/finish` — `login_required`; calls `genie_service.save_categorizations_bulk(ensembl_id, [{pmid, category}, ...])` with all rows where `category > 0`; marks `session.status = 'complete'` and `session.submitted_to_genie = True`; logs to `AuditService`; redirects to `/litreview/results/<search_id>` with success flash

**4g. Update `search_results()` route**
- [X] Query for existing `LitReviewSession` for `search_id + current_user.id`; pass `review_session` to template; if session exists also compute `categorized_count` and `total`

---

### Task 5 — Templates

**`app/templates/litreview/review_start.html`** (new)

- [ ] Page header: "Confirm Gene: `<search_term>`"
- [ ] On page load, JS calls `GET /litreview/api/gene-lookup?q=<search_term>`
- [ ] **Loading state**: spinner while waiting
- [ ] **Single match**: show Ensembl ID, display name, chromosome, description, Ensembl link, OMIM link; "Yes, confirm" button (posts `ensembl_id` to `confirm-gene`); "Wrong gene" link → shows manual input
- [ ] **Multiple matches**: radio list of candidates; "Confirm selection" button; "None of these" → manual input
- [ ] **No match (not_found)**: "No Ensembl ID found" message; goes straight to manual input
- [ ] **Manual input section**: text field for Ensembl ID; "Verify" button (calls gene-lookup with typed ID); shows name if found; "Confirm" button posts to `confirm-gene`
- [ ] All states handled in JS without page reload

**`app/templates/litreview/review.html`** (new)

- [ ] Header: gene symbol + confirmed Ensembl ID
- [ ] Progress bar: "X of N categorized" — percentage fill
- [ ] Article card (full, not truncated):
  - Title (large, bold)
  - Authors (up to 6, then "et al.")
  - Journal, year
  - PMID badge, DOI link, "Open on PubMed" link
  - Full abstract (scrollable if long)
- [ ] Four category buttons, stacked full-width, colour-coded:
  - 🔴 `1` — Not useful
  - 🟠 `2` — Probably not useful
  - 🟡 `3` — Possibly useful
  - 🟢 `4` — Useful
- [ ] Clicking a button: `fetch` → `POST /categorize` → on success, animate to next uncategorized article (JS advances index without page reload)
- [ ] If all articles categorized: hide buttons, show "All done!" message + green "Submit to Genie & Finish" button → posts to `/finish`
- [ ] "Save & exit" button (always visible): calls `POST /categorize` for current article if a category is selected, then redirects back to results page; shows "Progress saved" toast
- [ ] On page load: JS skips already-categorized articles (starts at first `category == 0`)
- [ ] Keyboard shortcuts (optional but useful): `1`–`4` keys trigger category buttons

**results.html** (update)

- [ ] In button row: add "Start LitReview" button (teal/purple) linking to `/review/start`
- [ ] If `review_session.status == 'in_progress'`: show "Continue Review" button instead, with sub-text "`categorized_count` / `total` categorized"
- [ ] If `review_session.status == 'complete'`: show "Review complete ✓" badge (non-clickable, green)

---

### Task 6 — Tests

**`tests/litreview/test_litreview_review.py`** (new)

- [ ] Unit: `GenieService.lookup_gene()` — single result, multiple results, 404 → `[]`, network error (mock `requests`)
- [ ] Unit: `GenieService.get_gene_detail()` — success, 404 → `None`
- [ ] Unit: `GenieService.get_omim_id()` — success, 404 → `None`
- [ ] Unit: `GenieService.save_categorizations_bulk()` — success response, partial skipped response
- [ ] Unit: `GenieService.get_categorizations()` — success list, 404 gene → `[]`
- [ ] Integration: `GET /review/start` — redirects to login if unauthenticated; 404 if wrong user
- [ ] Integration: `POST /review/confirm-gene` — creates session + category rows; pre-populates from Genie; redirects to `/review`
- [ ] Integration: `POST /review/categorize` — updates category; returns correct `remaining`; rejects `category=0` or `category=5`
- [ ] Integration: `POST /review/finish` — marks session complete; calls Genie bulk submit; redirects with flash
- [ ] Integration: `search_results()` — `review_session` context variable present; `None` when no session; correct status when in-progress vs complete

---

### Implementation order

1. Task 1 (config) → Task 2 (Genie service) → Task 3 (DB + migration) → Task 4 (routes) → Task 5 (templates) → Task 6 (tests)