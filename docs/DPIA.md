# Data Protection Impact Assessment (DPIA)
**Application:** PanelMerge
**Version:** 1.2  
**Date Completed:** 12/10/2025  
**Last Updated:** 22/03/2026 (LitReview and KnowHow blueprints added; R12 XSS fix applied; R7 NCBI transfer disclosed; R8 retention schedule & self-service deletion implemented; R9 noted as dormant; Privacy Policy v1.1 with full LitReview/KnowHow disclosure)
**Controller:** Anita Korpioja
**Contact:** anita.korpioja@gmail.com  
**Location of Processing:** Finland (EU)  
**Repository:** https://github.com/akorpioj/GenePanelCombine  

---

## 1. Purpose and Scope

The purpose of this DPIA is to assess and document the privacy risks associated with the processing of data in the **PanelMerge** web application.

PanelMerge is a research and diagnostic support tool designed to merge and compare **gene panel lists** from user-uploaded files and publicly available databases (e.g., PanelApp). It is primarily intended for healthcare and research professionals, but does not handle identifiable patient data in its current version.

This DPIA assesses the **current deployment** and has been updated (v1.1) to reflect two new features:
- **LitReview** — a PubMed literature search module that stores per-user search history, cached article metadata, and personal notes on articles.
- **KnowHow** — a community knowledge base where authenticated users author and share articles and links, attributed to them by name.

These additions introduce **new personal data processing activities** that are materially different from the original scope, including user behavioural data, user-generated content, and an outbound data transfer to a US-based third-party service (NCBI PubMed API).

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

---

## 3. Necessity and Proportionality

| **Principle** | **Assessment** |
|----------------|----------------|
| **Purpose limitation** | Data is processed to support gene panel workflows, literature research, and professional knowledge sharing. LitReview search history supports the user's own research continuity. KnowHow content supports professional development. No unrelated processing identified. |
| **Data minimization** | LitReview stores the minimum needed (search term, result metadata). However, storing detailed behavioural data (per-article view counts, timestamps, notes) goes beyond strictly necessary — consider whether full interaction tracking is needed, or whether only "saved" status is sufficient. KnowHow stores user-generated content linked to the author. |
| **Storage limitation** | Original activities retain strict limits (uploads < 1 hour, logs ≤ 90 days). **New gap:** LitReview search history and `user_article_actions` have no independent retention limit — they persist indefinitely until account deletion. KnowHow content also has no automated expiry. Retention schedules should be defined for these. |
| **Accuracy** | Article metadata is sourced from NCBI PubMed and cached for 7 days. KnowHow content is user-authored and may contain inaccuracies; no editorial review process. |
| **Integrity & confidentiality** | HTTPS enforced, hashed credentials. KnowHow article HTML content is rendered with `\| safe` in templates — this bypasses Jinja2 auto-escaping and creates a stored XSS risk if Quill output is not separately sanitized server-side. |
| **Transparency** | Privacy Policy at `/privacy` must be updated to describe LitReview and KnowHow data processing, the NCBI API transfer, and retention practices for new tables. |
| **User rights enablement** | Users can request deletion via anita.korpioja@gmail.com. Account deletion cascades to search history and article actions. However, there is no self-service mechanism for users to delete their own search history or article interaction records short of full account deletion. |
| **Data transfer controls** | **New: LitReview transmits gene search queries and PMID lists to NCBI (USA).** This is a transfer to a third country without adequacy status. See Section 4A (International Transfers). KnowHow has no external data transfers. |

**Conclusion:**  
The core gene panel processing remains necessary and proportionate. The new LitReview and KnowHow features introduce more significant personal data processing. Retention limits and HTML sanitization are the most urgent gaps to address.

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

---

### 4.2 Residual Risks After Mitigation

With the original processing activities, residual risk remains **Low to Medium**. With the addition of LitReview and KnowHow, two areas are elevated:

- **R12 (Stored XSS)** has been **resolved** (22/03/2026): `nh3` server-side sanitization applied — risk now **Low**.
- **R7 (NCBI transfer)** has been **addressed** (22/03/2026): legal basis (Art. 49(1)(b)) documented, Privacy Policy Section 8 updated, on-screen notice added to the LitReview search page — risk now **Low–Medium** (accepted).
- **R8 (LitReview retention)** has been **resolved** (22/03/2026): `_RETENTION_DAYS=365` constant, `flask litreview cleanup` CLI, self-service delete routes and history UI — risk now **Low**.
- **R9 (notes field)** is **dormant**: the notes field is not currently exposed in any UI — no user can write notes, so the risk is not active. Risk will require re-evaluation if a notes UI is implemented.
- **R10, R14** (behavioural profiling, KnowHow retention) remain open: future policy decisions required.
- Overall residual risk with proposed mitigations: **Low–Medium** (reduced now that R7, R8, and R12 are resolved).

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

**Final Assessment (v1.4):**  
The addition of LitReview and KnowHow **materially increases the personal data processing scope** of PanelMerge. The risks introduced are manageable but require concrete action, particularly:
1. ~~**Fix the stored XSS vulnerability** in KnowHow article rendering~~ **DONE** (R12 — resolved 22/03/2026, `nh3` sanitization applied).
2. ~~**Disclose and review the NCBI international transfer**~~ **DONE** (R7 — resolved 22/03/2026, Privacy Policy Section 8.2 added, on-screen notice on LitReview search page, Art. 49(1)(b) legal basis documented).
3. ~~**Define and implement retention schedules** for search history and interaction data~~ **DONE** (R8 — resolved 22/03/2026: `_RETENTION_DAYS=365`, `flask litreview cleanup` CLI, self-service delete routes, history page UI updated).
4. **Update the Privacy Policy** to accurately describe all new processing activities — done for NCBI transfer; full retention period wording still to be added.

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

