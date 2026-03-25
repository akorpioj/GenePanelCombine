# Data Protection Impact Assessment (DPIA)
**Application:** PanelMerge
**Version:** 1.4  
**Date Completed:** 12/10/2025  
**Last Updated:** 22/03/2026 (v1.1: LitReview and KnowHow added; v1.2: R12 XSS fixed, R7 NCBI transfer disclosed, R8 retention+self-service deletion, Privacy Policy v1.1 published; v1.3: Saved Panels system, security infrastructure, and visit/activity tables documented; v1.4: retention routes for visit/suspicious_activity/panel_download tables, PanelGene.user_notes UI warning, Privacy Policy v1.2 published with Sections 3.5–3.7)
**Controller:** Anita Korpioja
**Contact:** anita.korpioja@gmail.com  
**Location of Processing:** Finland (EU)  
**Repository:** https://github.com/akorpioj/GenePanelCombine  

---

## 1. Purpose and Scope

The purpose of this DPIA is to assess and document the privacy risks associated with the processing of data in the **PanelMerge** web application.

PanelMerge is a research and diagnostic support tool designed to merge and compare **gene panel lists** from user-uploaded files and publicly available databases (e.g., PanelApp). It is primarily intended for healthcare and research professionals, but does not handle identifiable patient data in its current version.

This DPIA assesses the **current deployment** and has been updated incrementally to reflect the following additions:
- **LitReview** (v1.1) — a PubMed literature search module that stores per-user search history, cached article metadata, and personal notes on articles.
- **KnowHow** (v1.1) — a community knowledge base where authenticated users author and share articles and links, attributed to them by name.
- **Saved Panels system** (v1.3) — a panel library allowing users to create, version, annotate, and share named gene panel collections, with attributed change history and collaboration records.

These additions introduce **new personal data processing activities** that are materially different from the original scope, including user behavioural data, user-generated content, an outbound data transfer to a US-based third-party service (NCBI PubMed API), and comprehensive security infrastructure (session tracking, suspicious activity detection, visit logging).

---

## 2. Description of Processing Activities

| **Processing Activity** | **Description** | **Data Subjects** | **Data Types** | **Source of Data** | **Storage Location** | **Duration / Retention** |
|---------------------------|-----------------|------------------|----------------|--------------------|----------------------|--------------------------|
| File uploads | Users upload gene panel files (Excel/CSV/TSV) | None (no identifiable individuals) | Gene names and identifiers | User upload | Temp server memory or folder | Deleted after session (~1 hour) |
| Public API access | Retrieve gene panel data from PanelApp APIs | None | Publicly available panel data | External API | Cached temporarily | Deleted after use |
| Session management | Store session cookies and technical metadata | Users (indirectly) | IP, browser headers, cookies | Browser → Flask session | Session memory | Deleted on session end |
| Logging | Record access and errors for diagnostics | Users (indirectly) | Timestamp, route, possibly IP | Server logs | Cloud/VM logs | Max 90 days |
| User authentication (if enabled) | Manage admin/user accounts | Registered users | Name, email, password hash, role | User input | Database | Until account deletion |
| Backups | Backup configuration, logs | System-level | Potentially includes above | Server snapshots | Cloud backup storage | Encrypted, rotated, per retention policy |
| **LitReview: search history** | Each PubMed search is saved with the logged-in user's ID, the gene/keyword query, search parameters, result count, and timestamp | Registered users | User ID (FK), search query text, filters (JSON), timestamps | User input + system | PostgreSQL database (`literature_searches` table) | **365-day retention** — purged by `flask litreview cleanup`; self-service deletion available; account deletion CASCADEs |
| **LitReview: article metadata cache** | PubMed article metadata (PMID, title, abstract, author names, journal, DOI, MeSH terms, publication types) is fetched from NCBI and stored locally | Researchers (authors of articles — publicly named, third parties) | PubMed ID, title, abstract, author name strings, journal, DOI, MeSH terms, keywords, gene mentions | NCBI PubMed API (USA) | PostgreSQL database (`literature_articles` table) | 7-day cache TTL per article; refreshed on access; no hard maximum |
| **LitReview: article interaction tracking** | Per-user actions on articles — viewed, saved, view count, personal notes (field reserved, not yet in UI) — are recorded | Registered users | User ID (FK), article ID (FK), is_saved, is_viewed, view_count, free-text notes (not yet exposed), detailed timestamps | User actions + system | PostgreSQL database (`user_article_actions` table) | Unsaved interactions purged after **365 days** by `flask litreview cleanup`; saved records retained until deleted by user or account closure; account deletion CASCADEs |
| **LitReview: PubMed API call** | Gene/keyword search terms and PMID lists are transmitted to NCBI's Entrez API (USA) to retrieve article data; the registered admin email address and tool name are sent with every request | Registered users (search terms), admin (email) | Search query text, PMID list, admin email, IP address (implicit in HTTP) | User input | NCBI servers, USA | Controlled by NCBI's own privacy policy; not retained by PanelMerge |
| **LitReview: export downloads** | Users can download their search results as CSV or Excel files, containing article metadata including author names | Registered users, third-party article authors | Rank, PMID, title, author names, journal, year, DOI, abstract, MeSH terms | Database + user action | User's local device (browser download) | No server retention after download; data leaves the system |
| **KnowHow: articles** | Authenticated users write and publish knowledge base articles (rich HTML via Quill editor, up to 500 KB); articles are attributed to the author by first name or username and visible to all logged-in users | Registered users | User ID (FK), title, rich HTML content, category, timestamps, author display name | User input | PostgreSQL database (`knowhow_articles` table) | Persists until deleted by owner, ADMIN, or EDITOR role; no automated retention limit |
| **KnowHow: links** | Authenticated users contribute external links with descriptions; each link is attributed to the submitting user's name | Registered users | User ID (FK), URL, description, category, timestamp, author display name | User input | PostgreSQL database (`knowhow_links` table) | Persists until deleted by owner, ADMIN, or EDITOR role; no automated retention limit |
| **KnowHow: category/subcategory management** | Admins create and manage knowledge categories and subcategories | Admin users only | Category label, slug, colour, description, position | Admin input | PostgreSQL database (`knowhow_categories`, `knowhow_subcategories` tables) | Persists until admin deletes; no personal data beyond admin action timestamps |
| **Saved panels: library** | Registered users create and save named gene panel collections with descriptions, tags, and visibility settings (PRIVATE / SHARED / PUBLIC) | Registered users | User ID (FK as `owner_id`), panel name, description, tags (JSON), visibility, timestamps, last_accessed_at | User input | PostgreSQL database (`saved_panels` table) | Until deleted by owner or account closure (CASCADE); no automated retention limit |
| **Saved panels: gene annotations** | Each gene in a saved panel can carry user-authored notes and a custom confidence value | Registered users | User ID (FK as `added_by_id`), gene symbol, `user_notes` (free text), `custom_confidence`, `is_modified`, `added_at` timestamp | User input | PostgreSQL database (`panel_genes` table) | Until panel is deleted; user_notes could contain clinical observations |
| **Saved panels: version control** | Every change to a saved panel creates a numbered version attributed to the author, with a user-provided change comment and a changes summary | Registered users | User ID (FK as `created_by_id`), version number, comment (text), changes_summary, created_at | User action | PostgreSQL database (`panel_versions`, `panel_version_metadata` tables) | Per `PanelRetentionPolicy` (configurable per panel); no global automated purge |
| **Saved panels: change tracking** | Individual gene-level and metadata changes are stored with encrypted before/after values and the responsible user | Registered users | User ID (FK as `changed_by_id`), `old_value` (encrypted), `new_value` (encrypted), `change_reason` (text), `changed_at` | User action | PostgreSQL database (`panel_changes` table) | Per panel retention policy; no global automated purge; values encrypted at rest |
| **Saved panels: sharing and collaboration** | Panel owners can share panels with specific users at defined permission levels, with optional expiration | Registered users | Owner user ID, recipient user ID, panel ID, permission level (VIEW / COMMENT / EDIT / ADMIN), expiration timestamp, share_token | User action | PostgreSQL database (`panel_shares` table) | Until revoked or expiry; account deletion CASCADEs |
| **Saved panels: version tags and branches** | Users can tag specific versions and create branches for parallel panel development | Registered users | User ID (FK as `created_by_id`, `merged_by_id`), tag name, branch name, timestamps | User action | PostgreSQL database (`panel_version_tags`, `panel_version_branches` tables) | Per panel retention policy |
| **Export templates** | Users save personalised export format preferences (file format, column selection, filename pattern) for repeated use | Registered users | User ID (FK), template name, format, filename_pattern, column selection (JSON), usage_count, last_used_at | User input | PostgreSQL database (`export_templates` table) | Until manually deleted; account deletion CASCADEs; no automated retention limit |
| **Panel download tracking** | Each gene panel output download is logged with user identity, IP address, download date, and panel configuration | Registered users | User ID (FK), IP address, download_date, panel_ids (JSON), gene_count | System | PostgreSQL database (`panel_download` table) | No automated retention limit defined |
| **Session management (extended)** | Active logins are tracked; users can view and revoke sessions from their profile page | Registered users | Session token (hashed), creation time, IP address, user agent (device/browser), last_activity | System | Redis (live sessions) + database session table | Deleted on logout, revocation, or Redis TTL expiry |
| **Login and security statistics** | Login attempts, timestamps, IP addresses, and account lockout states are tracked per user | Registered users | `last_login`, `login_count`, `last_ip_address`, `failed_login_attempts`, `locked_until` | System | PostgreSQL database (`user` table) | Retained in user record until account deletion |
| **Suspicious activity detection** | Logins from unusual countries, times, or devices are flagged via ML anomaly detection; geolocation lookups are performed on login IPs | Registered users | User ID (FK), email, IP address, country, city, user_agent, activity_type, timestamp, alert_triggered, alert_reason | System (`ml_anomaly_detector.py`, `suspicious_activity_utils.py`) | PostgreSQL database (`suspicious_activity` table) | No automated retention limit defined |
| **Visit tracking** | All HTTP page requests are logged with IP address, URL path, user agent, and visit date | All visitors including unauthenticated | IP address, URL path, user agent string, visit_date | Server (Flask `before_request`) | PostgreSQL database (`visit` table) | No automated retention limit defined |
| **Audit logging (comprehensive)** | All significant user and admin actions are logged with encrypted field values, resource identifiers, and session context | Registered users + admin | User ID, username, IP address, user agent, session_id, resource_type, resource_id, old_values (encrypted), new_values (encrypted), details (encrypted), action type | System | PostgreSQL database (`audit_log` table) | Admin-configurable deletion (`POST /admin/audit-logs/delete-old`); no automated default purge |
| **User profile: extended fields** | User profile stores encrypted name/organisation plus display preferences | Registered users | first_name (encrypted), last_name (encrypted), organization (encrypted), timezone_preference, time_format_preference | User input | PostgreSQL database (`user` table) | Until account deletion |

---

## 3. Necessity and Proportionality

| **Principle** | **Assessment** |
|----------------|----------------|
| **Purpose limitation** | Data is processed to support gene panel workflows, literature research, and professional knowledge sharing. LitReview search history supports the user's own research continuity. KnowHow content supports professional development. No unrelated processing identified. |
| **Data minimization** | LitReview stores the minimum needed (search term, result metadata). However, storing detailed behavioural data (per-article view counts, timestamps, notes) goes beyond strictly necessary — consider whether full interaction tracking is needed, or whether only "saved" status is sufficient. KnowHow stores user-generated content linked to the author. |
| **Storage limitation** | Original activities retain strict limits (uploads < 1 hour, logs ≤ 90 days). LitReview search history and `user_article_actions` are now purged after **365 days** (`flask litreview cleanup`; 22/03/2026). **Remaining gap:** The `saved_panels`, `panel_versions`, `panel_changes`, `panel_shares`, `visit`, `suspicious_activity`, and `panel_download` tables have no automated retention limits and accumulate personal data indefinitely. |
| **Accuracy** | Article metadata is sourced from NCBI PubMed and cached for 7 days. KnowHow content is user-authored and may contain inaccuracies; no editorial review process. |
| **Integrity & confidentiality** | HTTPS enforced, hashed and salted credentials. KnowHow article HTML is sanitized server-side using `nh3.clean()` (v0.3.3, Quill allowlist) before DB storage — the `\| safe` in templates is now safe by construction (fix applied 22/03/2026). Sensitive fields in `AuditLog` and `PanelChange` are encrypted at rest using `EncryptedField` / `EncryptedJSONField`. Saved panel change values (`old_value`, `new_value`) are also encrypted before storage. |
| **Transparency** | Privacy Policy updated to v1.1 (22/03/2026): LitReview search history, article interactions, KnowHow attribution, NCBI transfer, and retention periods for LitReview tables are now disclosed. **Remaining gap:** The Saved Panels system, visit tracking, suspicious activity detection, login statistics, and panel download logging are not yet disclosed in the Privacy Policy. |
| **User rights enablement** | Users can request deletion via anita.korpioja@gmail.com. Account deletion cascades to all associated data. Self-service LitReview history deletion has been added (22/03/2026). Users can delete individual saved panels via the panel library UI. **Gap:** No self-service mechanism for deleting export templates, visit records, suspicious activity logs, or panel download history. |
| **Data transfer controls** | LitReview transmits gene search queries and PMID lists to NCBI (USA) — legal basis documented as Art. 49(1)(b), Privacy Policy Section 8.2 updated, on-screen notice added (22/03/2026). No other external data transfers identified. Saved Panels, KnowHow, and security infrastructure are entirely internal. |

**Conclusion:**  
The core gene panel processing remains necessary and proportionate. LitReview and KnowHow personal data processing risks have been substantially mitigated (XSS fixed, NCBI transfer disclosed, retention enforced). The **Saved Panels system** introduces the most significant remaining privacy considerations: attributed versioned panel histories, collaboration records, and automated change tracking that together create a detailed profile of each user's panel-editing activity. Retention schedules, gene note warnings, and Privacy Policy disclosure for saved panels are the most urgent remaining gaps.

---

## 4. Risk Assessment

### 4.1 Identified Risks

| **Risk ID** | **Risk Description** | **Likelihood** | **Impact** | **Risk Level** | **Mitigation Measures** |
|--------------|---------------------|----------------|-------------|----------------|--------------------------|
| R1 | User accidentally uploads patient-identifiable data (e.g., sample IDs) | Medium | High | **Medium–High** | Display clear upload disclaimer; restrict allowed file types; delete files after session; consider regex-based content checks. |
| R2 | IP addresses in server logs could identify users | Medium | Low | **Medium** | Anonymize IPs in logs; restrict log access; limit retention to 90 days. |
| R3 | External APIs log or retain requests | Low | Medium | **Low** | Use public APIs that do not log identifiable info; no identifiers transmitted. |
| R4 | Unauthorized admin access | Low | Medium | **Low** | Enforce bcrypt/Argon2 password hashing; strong passwords; limited admin accounts. |
| R5 | Future introduction of clinical or genetic patient data | Low (current), High (future) | High | **High (if future)** | Require new DPIA and explicit consent mechanism; implement pseudonymization and encryption. |
| R6 | Backup or export leak | Low | Medium | **Low** | Encrypt backups; control access; auto-rotate backups. |
| **R7** | **LitReview search terms sent to NCBI (USA) — international transfer outside EU** — **MITIGATED** | ~~High (every search)~~ | ~~Medium~~ | **~~Medium–High~~ Low–Medium** | **Disclosure applied 22/03/2026**: Legal basis documented as Art. 49(1)(b) GDPR (transfer necessary for the service explicitly requested by the user). Privacy Policy (Section 8.2) updated to name NCBI as a third-country recipient, explain what data is sent, cite the legal basis, and link to NCBI’s own privacy policy. On-screen notice added to the LitReview search page (amber info banner) informing users before they submit. Residual risk is accepted given the public-service nature of NCBI and the user’s explicit action. |
| **R8** | **LitReview search history is personal data with no retention limit** — **MITIGATED** | ~~High (active now)~~ | ~~Medium~~ | **~~Medium~~ Low** | **Fix applied 22/03/2026**: Retention period defined as **365 days** (`_RETENTION_DAYS = 365` in `app/litreview/routes.py`). `flask litreview cleanup` CLI command added — deletes `LiteratureSearch` records older than the cutoff and `UserArticleAction` records older than the cutoff where `is_saved=False` (explicitly saved articles are preserved). Self-service routes added: `POST /litreview/search/<id>/delete` and `POST /litreview/search-history/clear`. Delete and Clear All buttons added to `history.html`. All deletions logged as `AuditActionType.USER_DELETE`. |
| **R9** | **UserArticleAction.notes may contain sensitive clinical content** — **DORMANT (not yet active)** | ~~Medium~~ | High | **Low (currently dormant)** | The `notes` free-text field in `user_article_actions` is reserved for personal notes on articles but is **not currently exposed in any application UI** — no template or route renders or accepts notes input. The risk is therefore dormant. **When a notes UI is implemented**, a clear data minimisation warning must be displayed at the point of entry. Consider field-level encryption for the notes column if clinical use is anticipated. |
| **R10** | **Behavioural profiling of users' research activity** | High (active now) | Medium | **Medium** | `user_article_actions` records per-article view counts, first/last viewed timestamps, and save status for every user. This creates a detailed longitudinal profile of each user's research behaviour. Mitigation: Assess whether full interaction tracking is required or whether only save/unsave is needed; limit retention of view-count history. |
| **R11** | **KnowHow article content could contain sensitive information** | Medium | High | **Medium–High** | The Quill rich-text editor allows up to 500 KB of free-form HTML. Users could inadvertently include patient case notes, clinical observations, or other sensitive content. Content is visible to all logged-in users. Mitigation: Add a clear notice in the article editor that no patient-identifiable data should be entered; consider content moderation for sensitive terms. |
| **R12** | **Stored XSS risk from Quill HTML rendered with `\| safe`** — **MITIGATED** | ~~Medium~~ | ~~High~~ | **~~Medium–High~~ Low** | **Fix applied 22/03/2026**: `app/knowhow/routes.py` now calls `nh3.clean()` (v0.3.3) with a Quill 1.3.7 tag/attribute allowlist in both `create_article()` and `update_article()` before persisting content. All non-allowlisted tags (including `<script>`, `<iframe>`, event handlers) are stripped. The `| safe` in `article_view.html` is now safe by construction. `nh3>=0.2.14` added to `requirements.txt`. |
| **R13** | **User identity attribution in KnowHow is visible to all logged-in users** | High (active now) | Low | **Low–Medium** | Every KnowHow article and link is publicly attributed (by first name or username) to the creating user. All logged-in users can see who wrote what. Mitigation: Acceptable given professional context; ensure users are informed of this attribution during onboarding or in the Privacy Policy. |
| **R14** | **No automated retention limit for KnowHow articles/links or LitReview interaction data** | High (active now) | Medium | **Medium** | Content and interaction data accumulates indefinitely; no scheduled purge exists for inactive accounts or old data. Mitigation: Define retention policies; implement scheduled tasks to delete data (search history, article interactions, orphaned content) for accounts that have been inactive or deleted beyond a set period. |
| **R15** | **PubMed article author names stored in app database** | Low | Low | **Low** | `literature_articles.authors` stores the names of researchers from published PubMed articles. These are public, but storing them in the app's own DB makes PanelMerge a secondary processor of that data. Mitigation: Low risk given these are publicly-published names; no action required beyond acknowledging this in the Privacy Policy. |
| **R16** | **Saved panel sharing reveals professional relationships and co-authorship patterns** | Medium | Medium | **Medium** | The `panel_shares` table records the owner, recipient, permission level, and timestamps for every panel share. The `panel_versions` and `panel_changes` tables attribute every edit to a user. Together these create a detailed record of professional collaborations and work patterns within the application. Mitigation: Disclose this in the Privacy Policy; consider whether sharing metadata needs a retention limit independent of the panel itself. |
| **R17** | **PanelGene.user_notes could contain clinical or patient observations** | Medium | High | **Medium–High** | The `user_notes` field in `panel_genes` allows free-text annotations on individual genes within a saved panel. A clinician could inadvertently record patient-linked observations (e.g. gene variant notes referencing specific cases). Notes are private to the panel owner but are exposed to anyone the panel is shared with. Mitigation: Add a UI warning at the gene notes input field; warn at panel share time that notes will be visible to recipients. |
| **R18** | **Suspicious activity detection involves automated geolocation profiling on every login** | High (on every login) | Medium | **Medium** | `app/ml_anomaly_detector.py` and `app/suspicious_activity_utils.py` perform geolocation lookups (country, city) on login IP addresses. Results are stored in the `suspicious_activity` table indefinitely. This constitutes automated processing that creates a geolocation profile of each user. No retention limit is defined. Mitigation: Define a short retention period (e.g., 90 days) for `suspicious_activity` records; document in Privacy Policy; ensure processing is proportionate to the security benefit. |
| **R19** | **Visit tracking logs every HTTP request with IP address and no retention limit** | High (every page request) | Medium | **Medium** | The `visit` table records `ip_address`, `path`, and `user_agent` for every HTTP request, including unauthenticated visitors. There is no automated retention limit. Over time, this creates a detailed browsing history per IP that could re-identify users. Mitigation: Apply the same 90-day retention limit used for server logs; implement scheduled deletion; document in Privacy Policy. |
| **R20** | **Panel version history and change records accumulate indefinitely with user attribution** | High (active now) | Medium | **Medium** | `PanelVersion`, `PanelChange`, `PanelVersionBranch`, and `PanelVersionTag` records persist indefinitely unless an explicit `PanelRetentionPolicy` is created per panel. There is no global automated purge. Over time this creates a permanent attributed history of every change a user has made to their panels. Mitigation: Define a default retention policy for panel version records; consider anonymising `changed_by_id` after account deletion rather than hard-deleting, to preserve panel integrity. |
| **R21** | **No retention limits for `visit`, `suspicious_activity`, and `panel_download` tables** | High (active now) | Medium | **Medium** | Three tables store IP addresses and personal data with no automated deletion: `visit` (page-level browsing), `suspicious_activity` (geolocation + anomaly flags), `panel_download` (user + IP + panels downloaded). This could constitute indefinite retention of identifiable data without a documented legal basis. Mitigation: Apply 90-day retention to `visit` and `suspicious_activity`; define a retention period for `panel_download` consistent with audit requirements; implement CLI cleanup commands for all three tables. |

---

### 4.2 Residual Risks After Mitigation

With the original processing activities, residual risk remains **Low to Medium**. With the addition of LitReview and KnowHow, two areas are elevated:

- **R12 (Stored XSS)** has been **resolved** (22/03/2026): `nh3` server-side sanitization applied — risk now **Low**.
- **R7 (NCBI transfer)** has been **addressed** (22/03/2026): legal basis (Art. 49(1)(b)) documented, Privacy Policy Section 8 updated, on-screen notice added to the LitReview search page — risk now **Low–Medium** (accepted).
- **R8 (LitReview retention)** has been **resolved** (22/03/2026): `_RETENTION_DAYS=365` constant, `flask litreview cleanup` CLI, self-service delete routes and history UI — risk now **Low**.
- **R9 (notes field)** is **dormant**: the notes field is not currently exposed in any UI — no user can write notes, so the risk is not active. Risk will require re-evaluation if a notes UI is implemented.
- **R10, R14** (LitReview behavioural profiling, KnowHow retention) remain open.
- **R16–R21** (Saved Panels collaboration records, gene notes, geolocation profiling, visit tracking, panel version history, no-retention tables) are **newly identified and open**: Privacy Policy disclosure and retention limits required.
- Overall residual risk with proposed mitigations: **Low–Medium** for original and LitReview/KnowHow scope. **Medium** for the Saved Panels system and security infrastructure tables until retention policies are defined.

---

## 4A. International Data Transfers

| **Transfer** | **Recipient** | **Country** | **Legal Basis** | **Data Transferred** | **Safeguards / Notes** |
|--------------|--------------|-------------|-----------------|----------------------|------------------------|
| PanelApp API | Genomics England / NHS | United Kingdom | UK adequacy decision (Art. 45 GDPR) | Gene panel names, IDs — no personal data | No personal data; low risk |
| **NCBI PubMed Entrez API** | **National Center for Biotechnology Information (NIH/NLM)** | **USA** | **No EU–US adequacy decision in force for government services** | **User's gene/keyword search query, PMID batches, admin email (`Entrez.email`), IP address (implicit)** | **No SCCs in place. NCBI is a US federal agency subject to US law (FISMA, potentially FISA). NCBI's own privacy policy (nlm.nih.gov/web_policies) states they may log tool and email fields. This transfer should be reviewed under Art. 46 GDPR (appropriate safeguards) or Art. 49(1)(b) (necessary for contract performance). Until safeguards are formalised, users should be informed that searches are processed by NCBI in the USA.** |

**Action required:** ~~Update the Privacy Policy to disclose the NCBI transfer.~~ **DONE** (22/03/2026 — Privacy Policy Section 8.2 added; Art. 49(1)(b) legal basis documented; LitReview search page notice added).

---

## 5. Consultation and Review

No supervisory authority consultation is required under Article 36, as the processing is not high-risk.

This DPIA should be reviewed:

- **Annually**, or  
- **Whenever new features** are introduced that change data processing (e.g., user accounts expansion, analytics, or patient data).

---

## 6. Data Protection by Design and by Default

PanelMerge adheres to Privacy by Design principles:

- **Default non-personal processing** (gene names only).  
- **Minimal data collection**: no identifiers required for core functionality.  
- **Sandboxed file uploads**: isolated, auto-deleted.  
- **Secure defaults**: HTTPS, CSRF protection, secure cookies.  
- **Logging limited and anonymized**.  
- **No unnecessary cookies or analytics tracking.**

**Gaps introduced by LitReview and KnowHow (actions required):**

- [x] **Server-side HTML sanitization for KnowHow articles** *(fixed 22/03/2026)*: `nh3.clean()` with Quill 1.3.7 allowlist applied in both `create_article()` and `update_article()` in `app/knowhow/routes.py`. `nh3>=0.2.14` added to `requirements.txt`.
- [x] **Retention schedules** *(fixed 22/03/2026)*: `_RETENTION_DAYS = 365` constant defined; `flask litreview cleanup` CLI command added — removes `LiteratureSearch` records and unsaved `UserArticleAction` records older than the cutoff; saved articles are preserved.
- [x] **Self-service search history deletion** *(fixed 22/03/2026)*: `POST /litreview/search/<id>/delete` and `POST /litreview/search-history/clear` routes added; per-row Delete button and Clear All button added to `history.html`.
- [x] **Notes field warning** *(deferred — dormant risk)*: The `user_article_actions.notes` field is defined in the database schema but is **not currently exposed in any application UI**. No template or route allows users to enter notes. The R9 risk is therefore dormant. When a notes UI is implemented, a patient-data warning must be added at the point of entry (see R9 in the risk table). The equivalent warning for the KnowHow editor has already been added (see Appendix A).
- [x] **Privacy Policy update** *(completed 22/03/2026)*: Sections 3.3, 3.4 and 5 updated in both `docs/PRIVACY_POLICY.md` (v1.1) and `app/templates/main/privacy.html` to disclose LitReview search history, article interaction profiling, future notes field, KnowHow authorship attribution, NCBI transfer (Section 8.2), and retention periods for all new tables.
- [x] **LitReview search page disclosure** *(completed 22/03/2026)*: amber notice banner added to `app/templates/litreview/search.html` above the search form, citing Art. 49(1)(b) and linking to the Privacy Policy.

---

## 7. DPIA Conclusion and Sign-off

| **Criteria** | **Result** |
|---------------|------------|
| Processing involves personal data | **Yes** — LitReview (search history, interaction tracking, notes) and KnowHow (user-attributed content) involve personal data of registered users |
| Processing involves special categories | No — but notes and KnowHow content *could* contain health-related information if users are not warned |
| Large-scale or automated profiling | **Low-scale** — interaction tracking (view counts, timestamps) constitutes limited behavioural profiling |
| High-risk to individuals' rights and freedoms | **Low–Medium** — no high-risk processing under Art. 35(3); risks are manageable with proposed mitigations |
| DPIA required under Art. 35 | **No** — not required at present, but this assessment should be reviewed if user numbers scale significantly |
| DPIA required in future expansions | **Yes** — if patient, genetic, or clinical identifiers are introduced; also if ML/AI-based analysis of search patterns is implemented |
| International transfer disclosed | **Yes** — NCBI/PubMed transfer documented in Privacy Policy Section 8.2; Art. 49(1)(b) legal basis applied; on-screen notice added to LitReview search page (22/03/2026) |

**Final Assessment (v1.1):**  
The addition of LitReview and KnowHow **materially increases the personal data processing scope** of PanelMerge. The risks introduced are manageable but require concrete action, particularly:
1. ~~**Fix the stored XSS vulnerability** in KnowHow article rendering~~ **DONE** (R12 — resolved 22/03/2026, `nh3` sanitization applied).
2. ~~**Disclose and review the NCBI international transfer**~~ **DONE** (R7 — resolved 22/03/2026, Privacy Policy Section 8.2 added, on-screen notice on LitReview search page, Art. 49(1)(b) legal basis documented).
3. ~~**Define and implement retention schedules** for search history and interaction data~~ **DONE** (R8 — resolved 22/03/2026: `_RETENTION_DAYS=365`, `flask litreview cleanup` CLI, self-service delete routes, history page UI updated).
4. ~~**Update the Privacy Policy**~~ **DONE** (22/03/2026: Privacy Policy v1.1 published — Sections 3.3, 3.4 and 5 added for LitReview, KnowHow, NCBI transfer, and retention periods).
5. **Document the Saved Panels system** in both the Privacy Policy and this DPIA — versioned panel history, collaboration records, change tracking with encryption, and retention policy for `saved_panels`, `panel_versions`, `panel_changes`, `panel_shares`, `visit`, `suspicious_activity`, and `panel_download` tables (open as of 22/03/2026).

A further DPIA update **must be conducted** before any of the following:
- Enabling the `gene_mentions` / `UserArticleAction.notes` fields for clinical or diagnostic workflows involving patient data.
- Implementing ML-based analysis of search history.
- Increasing the user base to large-scale processing levels.

---

### **Sign-off**

| Role | Name | Date | Signature |
|-------|------|------|------------|
| Data Controller | Anita Korpioja | 12/10/2025 | |
| Updated (v1.1) | Anita Korpioja | 22/03/2026 | |
| Updated (v1.2) | Anita Korpioja | 22/03/2026 | |
| Updated (v1.3) | Anita Korpioja | 22/03/2026 | |
| Reviewer / Auditor | [Optional] | [Insert date] | |

---

## Appendix A — Checklist Summary

- [x] Data inventory and classification complete  
- [x] Risk areas identified  
- [x] Mitigation measures implemented (original scope)  
- [x] Residual risk acceptable (original scope)  
- [x] No DPIA required currently  
- [x] DPIA framework established for future high-risk processing  

**v1.1 additions:**
- [x] LitReview processing activities documented  
- [x] KnowHow processing activities documented  
- [x] NCBI international transfer identified and documented  
- [x] **Privacy Policy updated for new activities** *(22/03/2026 — Section 8 restructured; NCBI transfer Section 8.2 added with Art. 49(1)(b) legal basis)*
- [x] **LitReview search page disclosure** *(22/03/2026 — amber notice banner added to search.html)*
- [x] Server-side HTML sanitization implemented for KnowHow *(nh3, 22/03/2026)*  
- [x] LitReview search history retention schedule defined and implemented *(22/03/2026 — `flask litreview cleanup`, `_RETENTION_DAYS=365`, saved articles preserved)*  
- [x] Self-service search history deletion route added *(22/03/2026 — per-row Delete and Clear All in history.html)*  
- [x] **Notes / content editor UI warning added** *(22/03/2026 — red warning banner added to KnowHow article editor above the Quill content field, visible to all users before they write)*  
- [x] **LitReview notes field (R9) assessed** *(22/03/2026 — field exists in DB but not exposed in any UI; risk is dormant; warning required when notes UI is built)*  
- [x] **Privacy Policy v1.1 published** *(22/03/2026 — Sections 3.3, 3.4 and 5 added covering LitReview search behaviour, article interactions, KnowHow authorship, and retention periods for all new tables)*

**v1.3 additions (new gaps identified 22/03/2026):**
- [x] **Saved Panels system documented in Privacy Policy** *(22/03/2026 — Privacy Policy v1.2: Section 3.5 added covering panel library, versioning, change tracking, collaboration records, and gene annotations)*
- [x] **Retention limit for `panel_versions` / `panel_changes` / `panel_shares`** *(22/03/2026 — policy defined: records retained until panel deletion or account closure; cascade deletion documented in Privacy Policy Section 3.5 and Section 5)*
- [x] **Retention limit for `visit` table** *(22/03/2026 — 90-day admin-triggered purge implemented: `POST /admin/visit-logs/delete-old` route added to auth/routes.py; delete button added to audit_logs admin page)*
- [x] **Retention limit for `suspicious_activity` table** *(22/03/2026 — 90-day admin-triggered purge implemented: `POST /admin/suspicious-activity/delete-old` route added; delete button and modal added to admin_suspicious_activity.html; geolocation processing documented in Privacy Policy Section 3.6)*
- [x] **Retention limit for `panel_download` table** *(22/03/2026 — 12-month admin-triggered purge implemented: `POST /admin/panel-downloads/delete-old` route added; delete button added to audit_logs admin page)*
- [x] **PanelGene.user_notes warning** *(22/03/2026 — amber privacy notice added below Gene List textarea in panel creation/edit modal (_my_panels.html); visibility hint added below visibility dropdown warning that annotations are visible to share recipients)*
- [x] **Export template and panel download processing disclosed in Privacy Policy** *(22/03/2026 — Privacy Policy v1.2: Section 3.7 added covering panel export templates and download logging; Section 4 table updated with new rows; Section 5 retention updated)*

---

## Appendix B — LitReview: Personal Data Fields Reference

| Table | Column | Nature | Personal Data? | Notes |
|-------|--------|--------|----------------|-------|
| `literature_searches` | `user_id` | FK to `user.id` | Yes — links search to individual | |
| `literature_searches` | `query` | Text | Yes — reveals user's research focus | No independent retention limit |
| `literature_searches` | `filters` | JSON | Yes (indirectly) | Includes max_results and type |
| `literature_searches` | `created_at` | Timestamp | Yes (indirectly) | Reveals when user was active |
| `literature_articles` | `authors` | JSON list of strings | Yes — public researcher names | Source: NCBI; cached locally |
| `user_article_actions` | `user_id` | FK | Yes | |
| `user_article_actions` | `is_viewed`, `view_count` | Behavioural | Yes — profiling of reading habits | |
| `user_article_actions` | `notes` | Free text | Yes — **highest risk field** | May contain clinical/patient references |
| `user_article_actions` | `first_viewed_at`, `last_viewed_at` | Timestamps | Yes — granular behavioural data | |

## Appendix C — KnowHow: Personal Data Fields Reference

| Table | Column | Nature | Personal Data? | Notes |
|-------|--------|--------|----------------|-------|
| `knowhow_articles` | `user_id` | FK to `user.id` | Yes — authorship attribution | Displayed as first_name or username |
| `knowhow_articles` | `title` | Text | Potentially | User-authored |
| `knowhow_articles` | `content` | Rich HTML (up to 500 KB) | Potentially | Sanitized server-side with `nh3` (Quill allowlist) before DB storage (fix applied 22/03/2026); `\| safe` in template is now safe by construction; could still contain patient info if user deliberately includes it — UI warning recommended |
| `knowhow_articles` | `created_at`, `updated_at` | Timestamps | Yes (indirectly) | |
| `knowhow_links` | `user_id` | FK | Yes — attribution | Displayed as first_name or username |
| `knowhow_links` | `url` | String | Low | User-contributed external URL |
| `knowhow_links` | `description` | String | Potentially | User-authored text |
| `knowhow_categories` / `knowhow_subcategories` | All columns | Admin-managed labels | No personal data | |

## Appendix D — Saved Panels: Personal Data Fields Reference

| Table | Column | Nature | Personal Data? | Notes |
|-------|--------|--------|----------------|-------|
| `saved_panels` | `owner_id` | FK to `user.id` | Yes — links panel to individual | |
| `saved_panels` | `name`, `description` | Text | Potentially | User-authored; could name clinical contexts |
| `saved_panels` | `tags` | JSON | Possibly | User-defined labels |
| `saved_panels` | `visibility` | Enum | Yes (indirectly) | PRIVATE/SHARED/PUBLIC affects who can read |
| `saved_panels` | `last_accessed_at` | Timestamp | Yes (indirectly) | Reveals user activity timing |
| `panel_genes` | `added_by_id` | FK to `user.id` | Yes — authorship attribution | |
| `panel_genes` | `user_notes` | Free text | Yes — **high risk** | User may enter clinical observations; visible to all panel collaborators |
| `panel_genes` | `custom_confidence` | Integer | Low | User annotation |
| `panel_versions` | `created_by_id` | FK to `user.id` | Yes | Every version permanently attributed to a user |
| `panel_versions` | `comment` | Text | Potentially | User-authored change message |
| `panel_versions` | `created_at` | Timestamp | Yes (indirectly) | Reveals user activity timing |
| `panel_changes` | `changed_by_id` | FK to `user.id` | Yes | Every change attributed to a user |
| `panel_changes` | `old_value` | Text (encrypted) | Yes | Encrypted gene/metadata value before change |
| `panel_changes` | `new_value` | Text (encrypted) | Yes | Encrypted gene/metadata value after change |
| `panel_changes` | `change_reason` | Text | Potentially | User-authored explanation of change |
| `panel_shares` | `shared_by_id`, `shared_with_user_id` | FK to `user.id` | Yes — reveals professional relationships | |
| `panel_shares` | `permission_level` | Enum | Yes (indirectly) | Reveals level of trust between users |
| `panel_shares` | `expires_at` | Timestamp | Yes (indirectly) | |
| `panel_version_tags` | `created_by_id` | FK to `user.id` | Yes | |
| `panel_version_branches` | `created_by_id`, `merged_by_id` | FK to `user.id` | Yes | Both creation and merge attributed |
| `export_templates` | `user_id` | FK to `user.id` | Yes | |
| `export_templates` | `name`, `filename_pattern` | Text | Potentially | User-authored |
| `export_templates` | `usage_count`, `last_used_at` | Statistics | Yes (indirectly) | Reveals usage behaviour |
| `panel_download` | `user_id` | FK to `user.id` | Yes | |
| `panel_download` | `ip_address` | String | Yes | Downloads logged with IP |
| `panel_download` | `download_date` | Timestamp | Yes | |

## Appendix E — Security Infrastructure: Personal Data Fields Reference

| Table | Column | Nature | Personal Data? | Notes |
|-------|--------|--------|----------------|-------|
| `suspicious_activity` | `user_id` (FK), `email` | Identity | Yes | |
| `suspicious_activity` | `ip_address` | Network | Yes | |
| `suspicious_activity` | `country`, `city` | Geolocation | Yes — location data | Derived by ML detector from IP; could constitute special category if health-linked |
| `suspicious_activity` | `user_agent` | Technical | Yes (indirectly) | Device fingerprinting |
| `suspicious_activity` | `timestamp` | Timestamp | Yes | Activity patterns |
| `visit` | `ip_address` | Network | Yes | All visitors including unauthenticated |
| `visit` | `path` | URL | Yes (indirectly) | Browsing history |
| `visit` | `user_agent` | Technical | Yes (indirectly) | |
| `visit` | `visit_date` | Timestamp | Yes | |
| `audit_log` | `user_id`, `username` | Identity | Yes | |
| `audit_log` | `ip_address`, `user_agent`, `session_id` | Technical | Yes | |
| `audit_log` | `old_values`, `new_values`, `details` | Encrypted JSON | Yes | Encrypted at rest with `EncryptedJSONField` |
| `user` | `last_login`, `login_count`, `last_ip_address` | Statistics | Yes | Retained in user record |
| `user` | `failed_login_attempts`, `locked_until` | Security state | Yes (indirectly) | Account lockout tracking |

