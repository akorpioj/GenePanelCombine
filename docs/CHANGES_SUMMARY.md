# Summary of Changes: v1.5.3

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
- `docs/DPIA.md` updated to v1.2; R8 marked **MITIGATED**; Appendix A checklist items ticked

---

### Fix: Full Privacy Policy disclosure for LitReview and KnowHow (DPIA Sec 6)

**Problem:** The Privacy Policy (v1.0) did not disclose LitReview search behaviour data, article interaction profiling, the planned notes field, KnowHow authorship attribution, or retention periods for any of the new tables.

**Solution (Privacy Policy v1.1, 22/03/2026):**

- **`docs/PRIVACY_POLICY.md`** and **`app/templates/main/privacy.html`** updated:
  - **Section 3.3 (new)** — LitReview: search history, article interaction records (limited behavioural profiling), planned notes field (dormant, not yet in UI)
  - **Section 3.4 (new)** — KnowHow: authored articles and links attributed to user by name; content restriction warning referenced
  - **Section 4 (Legal Basis table)** — three new rows: LitReview search history (Art. 6(1)(b)/(f)), LitReview article interactions (Art. 6(1)(f)), KnowHow content (Art. 6(1)(b)/(f))
  - **Section 5 (Retention)** — explicit retention periods added: LitReview search/interactions 365 days (automated), cached article metadata 7-day TTL, saved articles on user request, KnowHow until admin/author deletion; self-service deletion link added

- **DPIA.md updated to v1.2**: R9 classified as **dormant** (notes field not in any UI); Section 2 processing activities table retention columns updated; Section 6 remaining open checkboxes ticked; Section 4.2 residual risks updated; Section 4A "Action required" resolved

---

### GDPR: DPIA v1.3 — Saved Panels and Security Infrastructure gaps documented

**Context:** A full re-review of the codebase against the existing DPIA v1.2 identified 15+ undocumented processing activities: the Saved Panels library system (10 database models), visit tracking, geolocation profiling in suspicious activity detection, panel download logging, export templates, session management, and login statistics.

**`docs/DPIA.md` updated to v1.3:**
- 14 new processing activity rows added to Section 2 (Saved panels library, shared panels, version control, change log, gene annotations, panel exports, export templates, panel download tracking, session management, login statistics, suspicious activity detection, geolocation profiling, visit tracking, failed login tracking)
- Section 3 necessity/proportionality assessment expanded
- 6 new risks documented: R16–R21 (panel sharing reveals professional relationships; `user_notes` could contain patient data; geolocation profiling; visit log IP accumulation; unbounded version/change history; no retention limit on visit/suspicious_activity/panel_download tables)
- Section 4.2 residual risks updated
- Appendix D added: Saved Panels data fields reference
- Appendix E added: Security infrastructure data fields reference
- 7 open action items added to Appendix A "v1.3 additions" checklist

---

### Fix: DPIA v1.4 action items — Saved Panels, retention, Privacy Policy v1.2 (25/03/2026)

All 7 open items from the DPIA v1.4 "v1.3 additions" checklist implemented.

#### Admin retention routes for visit logs, suspicious activity, and panel download logs (`app/auth/routes.py`)

Three new admin-only `POST` routes added, following the exact pattern of `POST /admin/audit-logs/delete-old`:

- **`POST /admin/visit-logs/delete-old`** (`auth.delete_old_visit_logs`)
  - Deletes `Visit` records where `visit_date < cutoff`
  - Period options: 1, 2, or 3 months (recommended: 3 months / 90-day GDPR limit)
  - Logs deletion via `AuditService.log_admin_action`

- **`POST /admin/suspicious-activity/delete-old`** (`auth.delete_old_suspicious_activity`)
  - Deletes `SuspiciousActivity` records where `timestamp < cutoff`
  - Period options: 1, 2, or 3 months
  - Redirects back to the Suspicious Activity Monitor page

- **`POST /admin/panel-downloads/delete-old`** (`auth.delete_old_panel_downloads`)
  - Deletes `PanelDownload` records where `download_date < cutoff`
  - Period options: 3, 6, or 12 months (recommended: 12 months for audit trail compliance)
  - Logs deletion via `AuditService.log_admin_action`

#### Admin UI changes

- **Audit Logs page (`app/templates/auth/audit_logs.html`)**:
  - Two new buttons added to the action bar: **"Delete Old Visit Logs"** (orange) and **"Delete Old Downloads Log"** (yellow)
  - Each opens its own modal with a GDPR context note, period radio buttons, CSRF token, and a JS `confirm()` dialog before submission

- **Suspicious Activity Monitor (`app/templates/auth/admin_suspicious_activity.html`)**:
  - **"Delete Old Records"** button added to the page header
  - Modal with GDPR context note, period radio buttons (1/2/3 months), CSRF token, and JS confirm function

#### PanelGene `user_notes` UI warnings (`app/templates/auth/_my_panels.html`)

Two notices added to the panel creation/edit modal:

1. **Amber privacy notice** below the Gene List textarea:
   - *"Privacy notice: If per-gene annotations or notes are added to this panel, they will be visible to any user this panel is shared with or made public to. Do not include patient-identifiable information in gene notes."*

2. **Visibility dropdown hint** below the Visibility selector:
   - *"Shared or Public: gene annotations (user notes) on this panel will be visible to recipients."*

#### Privacy Policy updated to v1.2

Both **`app/templates/main/privacy.html`** and **`docs/PRIVACY_POLICY.md`** updated:

- **Section 3.5 (new)** — Saved Panels: panel library records, gene annotations (`user_notes`), version history snapshots, change log entries, panel share records; amber warning about annotations visibility; cascade deletion on account close
- **Section 3.6 (new)** — Security Infrastructure: visit logs (IP, path, user agent, timestamp), suspicious activity records (IP, email, geolocation city/country, activity type), login statistics (login count, last IP), session records; clarification that geolocation is used only for security alerting, not profiling
- **Section 3.7 (new)** — Panel Exports and Download Logging: download records (IP, user ID, panel IDs, timestamps), export templates (name, format settings)
- **Section 4 (Legal Basis table)** — 5 new rows: Saved Panels (Art. 6(1)(b)/(f)), visit logs (Art. 6(1)(f), 90 days), suspicious activity (Art. 6(1)(f), 90 days), panel download records (Art. 6(1)(f), 12 months), export templates (Art. 6(1)(b)/(f))
- **Section 5 (Retention)** — 5 new bullet points: visit logs 90 days, suspicious activity 90 days, panel download records 12 months, saved panels/gene annotations until panel or account deletion (cascade), export templates until deleted

#### DPIA updated to v1.4

- All 7 `[ ]` checklist items under **"v1.3 additions"** ticked with implementation notes and dates
- Version header bumped from **1.3 → 1.4**
- Last Updated extended to record v1.4 changes
