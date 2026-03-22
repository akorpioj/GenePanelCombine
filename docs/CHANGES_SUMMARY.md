# Summary of Changes: v1.5.3

## Admin: Delete Old Audit Logs

### What was added

Admins can now delete audit log records older than a chosen time period directly from the Audit Logs page.

### New route

- `POST /admin/audit-logs/delete-old` (`auth.delete_old_audit_logs`)
  - Admin-only; validates the submitted `months` value against the allowed set `{1, 2, 3, 6}`
  - Calculates a cutoff date (`now − months × 30 days`), bulk-deletes all `AuditLog` rows older than the cutoff, and commits the transaction
  - Logs the deletion via `AuditService.log_admin_action` (records the period, cutoff date, and count deleted)
  - Flashes a confirmation message with the number of records removed, then redirects back to the Audit Logs page

### UI changes (Audit Logs page)

- **"Delete Old Logs" button** (red) added to the top-right action bar, next to the existing "Export CSV" button
- Clicking the button opens a **modal overlay** containing:
  - A warning that deletion is permanent and cannot be undone
  - A 2×2 grid of radio buttons: **1 Month**, **2 Months**, **3 Months**, **6 Months**
  - **Cancel** and **Delete Logs** buttons
- Submitting without selecting a period is blocked with an alert
- A browser `confirm()` dialog provides a final warning before the form is posted

### Other fixes

- Corrected a pre-existing bug in `export_audit_logs()` where `datetime.now()` was used instead of `datetime.datetime.now()` (the module is imported as `import datetime`, not `from datetime import datetime`)

---

## Security & GDPR Compliance

### Fix: Stored XSS in KnowHow articles (DPIA R12)

**Problem:** `app/templates/knowhow/article_view.html` rendered `article.content | safe` without any server-side sanitization. Any authenticated user could submit malicious HTML/JavaScript via the Quill editor, which would then execute in the browsers of all other users viewing the article.

**Fix:**
- Added `nh3>=0.2.14` to `requirements.txt` (installed v0.3.3 — pure-Rust HTML sanitizer, no C dependencies)
- Added `_sanitize_content()` helper in `app/knowhow/routes.py` using `nh3.clean()` with a Quill 1.3.7 tag/attribute allowlist
  - Permitted tags: `p`, `h1`–`h4`, `strong`, `em`, `u`, `s`, `a`, `code`, `pre`, `blockquote`, `ul`, `ol`, `li`, `br`, `hr`, `span`, `img`
  - `class` and `style` allowed on all tags (needed for Quill alignment/indent)
  - `href`, `rel`, `target` on `<a>`; `src`, `alt`, `width`, `height` on `<img>`
  - `link_rel="noopener noreferrer"` and `strip_comments=True`
- Sanitization applied in both `create_article()` and `update_article()` after the size check, before DB write
- `{{ article.content | safe }}` in the template is now safe by construction

---

### Fix: Undisclosed international data transfer to NCBI/USA (DPIA R7)

**Problem:** Every PubMed search in LitReview transmits the user's search query, PMID lists, and admin email to NCBI (US federal agency) with no EU adequacy decision and no disclosure to users — a GDPR Art. 44 violation.

**Fix:**
- **`docs/PRIVACY_POLICY.md`** — Section 8 restructured into three subsections:
  - 8.1 Genomics England PanelApp (UK adequacy, no personal data)
  - 8.2 NCBI PubMed (USA) — names NCBI as a third-country recipient, lists data sent (query, PMIDs, tool email, IP), cites **Art. 49(1)(b)** GDPR as legal basis, links to NCBI's own privacy policy (`nlm.nih.gov/web_policies`), notes users can opt out by not using LitReview
  - 8.3 General — no commercial sharing
- **`app/templates/main/privacy.html`** — Section 8 updated to match, with bullet list of transmitted data and link to NCBI policy
- **`app/templates/litreview/search.html`** — amber information banner added above the search form, informing users before submission that their query is processed by NCBI in the USA, citing Art. 49(1)(b) and linking to the Privacy Policy

---

### Notice: Personal/patient data warning in KnowHow article editor (DPIA R11)

- Red warning banner added to `app/templates/knowhow/article_editor.html` directly above the Quill editor field (shown for both new articles and edits)
- Text: *"Do not include identifiable personal or patient information in this article. KnowHow articles are visible to all logged-in users. Any content containing patient names, identifiers, clinical notes referencing individuals, or other personal data is a violation of data protection policy and must not be published here."*

---

### Fix: No retention schedule for LitReview personal data (DPIA R8/R9)

**Problem:** LitReview search history (`literature_searches` table) and article interaction records (`user_article_actions` table) accumulated indefinitely with no automated purge. Users had no self-service mechanism to delete their own search history short of requesting full account deletion — a GDPR Art. 5(1)(e) storage-limitation gap.

**Solution:**

#### Retention constant and CLI command (`app/litreview/routes.py`)
- `_RETENTION_DAYS = 365` constant defines the retention period (12 months)
- `flask litreview cleanup` CLI command added:
  - Deletes `LiteratureSearch` records where `created_at < cutoff`
  - Deletes `UserArticleAction` records where `updated_at < cutoff` **and** `is_saved=False` — explicitly saved articles are never auto-deleted
  - `--days <n>` option to override the cutoff (default: 365)
  - `--dry-run` flag to preview deletions without committing
  - Example: `flask litreview cleanup --days 180 --dry-run`
- Run this command via a scheduled task (e.g., daily cron) to enforce the retention period

#### Self-service deletion routes (`app/litreview/routes.py`)
- `POST /litreview/search/<search_id>/delete` — deletes a single search record (owner-only; 403 redirect if user mismatch); cascades to associated `LiteratureArticle` rows via DB constraint
- `POST /litreview/search-history/clear` — deletes all search records for the current user
- Both routes log the deletion to the audit trail as `AuditActionType.USER_DELETE`

#### UI (`app/templates/litreview/history.html`)
- **Per-row Delete button** added next to "View results →" on each search card — submits a POST form with JS confirmation dialog
- **"Clear All" button** added to the page header alongside "New Search" — only shown when the history list is non-empty; JS confirmation required before submission
- Both buttons include CSRF token

#### DPIA update
- `docs/DPIA.md` updated to v1.4; R8 marked **MITIGATED**; Appendix A checklist items ticked

---

### Fix: Full Privacy Policy disclosure for LitReview and KnowHow (DPIA Sec 6)

**Problem:** The Privacy Policy (v1.0) did not disclose LitReview search behaviour data, article interaction profiling, the planned notes field, KnowHow authorship attribution, or retention periods for any of the new tables.

**Solution (Privacy Policy v1.1, 22/03/2026):**

- **`docs/PRIVACY_POLICY.md`** and **`app/templates/main/privacy.html`** updated:
  - **Section 3.3 (new)** — LitReview: search history, article interaction records (limited behavioural profiling), planned notes field (dormant, not yet in UI)
  - **Section 3.4 (new)** — KnowHow: authored articles and links attributed to user by name; content restriction warning referenced
  - **Section 4 (Legal Basis table)** — three new rows: LitReview search history (Art. 6(1)(b)/(f)), LitReview article interactions (Art. 6(1)(f)), KnowHow content (Art. 6(1)(b)/(f))
  - **Section 5 (Retention)** — explicit retention periods added: LitReview search/interactions 365 days (automated), cached article metadata 7-day TTL, saved articles on user request, KnowHow until admin/author deletion; self-service deletion link added

- **DPIA.md updated to v1.5**: R9 classified as **dormant** (notes field not in any UI); Section 2 processing activities table retention columns updated; Section 6 remaining open checkboxes ticked; Section 4.2 residual risks updated; Section 4A "Action required" resolved

---
