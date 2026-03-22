# Data Protection Impact Assessment (DPIA)
**Application:** PanelMerge
**Version:** 1.1  
**Date Completed:** 12/10/2025  
**Last Updated:** 22/03/2026 (LitReview and KnowHow blueprints added)
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
| **LitReview: search history** | Each PubMed search is saved with the logged-in user's ID, the gene/keyword query, search parameters, result count, and timestamp | Registered users | User ID (FK), search query text, filters (JSON), timestamps | User input + system | PostgreSQL database (`literature_searches` table) | Persists until account deletion (CASCADE); no independent retention limit |
| **LitReview: article metadata cache** | PubMed article metadata (PMID, title, abstract, author names, journal, DOI, MeSH terms, publication types) is fetched from NCBI and stored locally | Researchers (authors of articles — publicly named, third parties) | PubMed ID, title, abstract, author name strings, journal, DOI, MeSH terms, keywords, gene mentions | NCBI PubMed API (USA) | PostgreSQL database (`literature_articles` table) | 7-day cache TTL per article; refreshed on access; no hard maximum |
| **LitReview: article interaction tracking** | Per-user actions on articles — viewed, saved, view count, personal notes — are recorded | Registered users | User ID (FK), article ID (FK), is_saved, is_viewed, view_count, free-text notes, detailed timestamps | User actions + system | PostgreSQL database (`user_article_actions` table) | Persists until account deletion (CASCADE); no independent retention limit |
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
| **R7** | **LitReview search terms sent to NCBI (USA) — international transfer outside EU** | High (every search) | Medium | **Medium–High** | NCBI is a US government service with no EU adequacy decision. Every gene search by a logged-in user transmits the query plus the admin's registered email to NCBI servers. Mitigation: Document this transfer; assess whether NCBI's standard terms and FISMA compliance are sufficient; consider notifying users that their search terms are sent to NCBI; explore caching-first patterns to reduce API call frequency. |
| **R8** | **LitReview search history is personal data with no retention limit** | High (active now) | Medium | **Medium** | Each user's gene search history reveals research focus and potentially clinical specialisation. No automated deletion schedule exists. Mitigation: Define a retention period (e.g., 12 months) and implement scheduled deletion; provide a self-service "clear search history" function. |
| **R9** | **UserArticleAction.notes may contain sensitive clinical content** | Medium | High | **Medium–High** | The `notes` free-text field in `user_article_actions` is explicitly intended for personal notes on scientific articles. A user could write patient-identifying or clinical observations here, creating unintended storage of sensitive data. Mitigation: Add a UI notice warning users not to record patient-identifiable information in notes; consider field-level encryption for the notes column. |
| **R10** | **Behavioural profiling of users' research activity** | High (active now) | Medium | **Medium** | `user_article_actions` records per-article view counts, first/last viewed timestamps, and save status for every user. This creates a detailed longitudinal profile of each user's research behaviour. Mitigation: Assess whether full interaction tracking is required or whether only save/unsave is needed; limit retention of view-count history. |
| **R11** | **KnowHow article content could contain sensitive information** | Medium | High | **Medium–High** | The Quill rich-text editor allows up to 500 KB of free-form HTML. Users could inadvertently include patient case notes, clinical observations, or other sensitive content. Content is visible to all logged-in users. Mitigation: Add a clear notice in the article editor that no patient-identifiable data should be entered; consider content moderation for sensitive terms. |
| **R12** | **Stored XSS risk from Quill HTML rendered with `\| safe`** | Medium | High | **Medium–High** | `article_view.html` renders `article.content \| safe`, bypassing Jinja2 auto-escaping. If an attacker (or a compromised account) submits malicious HTML/JavaScript via the Quill editor, it will execute in the browsers of all other users who view that article. Mitigation: Sanitize Quill HTML server-side before storage using a library such as `bleach` or `nh3`; define an allowlist of permitted HTML tags and attributes. |
| **R13** | **User identity attribution in KnowHow is visible to all logged-in users** | High (active now) | Low | **Low–Medium** | Every KnowHow article and link is publicly attributed (by first name or username) to the creating user. All logged-in users can see who wrote what. Mitigation: Acceptable given professional context; ensure users are informed of this attribution during onboarding or in the Privacy Policy. |
| **R14** | **No automated retention limit for KnowHow articles/links or LitReview interaction data** | High (active now) | Medium | **Medium** | Content and interaction data accumulates indefinitely; no scheduled purge exists for inactive accounts or old data. Mitigation: Define retention policies; implement scheduled tasks to delete data (search history, article interactions, orphaned content) for accounts that have been inactive or deleted beyond a set period. |
| **R15** | **PubMed article author names stored in app database** | Low | Low | **Low** | `literature_articles.authors` stores the names of researchers from published PubMed articles. These are public, but storing them in the app's own DB makes PanelMerge a secondary processor of that data. Mitigation: Low risk given these are publicly-published names; no action required beyond acknowledging this in the Privacy Policy. |

---

### 4.2 Residual Risks After Mitigation

With the original processing activities, residual risk remains **Low to Medium**. With the addition of LitReview and KnowHow, two areas are elevated:

- **R7 (NCBI transfer) and R12 (Stored XSS)** are the most urgent items. R7 requires documentation and user notice; R12 requires a code fix (server-side HTML sanitization).
- **R8, R9, R10, R14** (retention and sensitive notes) require policy decisions and scheduled deletion.
- Overall residual risk with proposed mitigations: **Medium**, reduced from **Medium–High** if R12 is fixed promptly.

---

## 4A. International Data Transfers

| **Transfer** | **Recipient** | **Country** | **Legal Basis** | **Data Transferred** | **Safeguards / Notes** |
|--------------|--------------|-------------|-----------------|----------------------|------------------------|
| PanelApp API | Genomics England / NHS | United Kingdom | UK adequacy decision (Art. 45 GDPR) | Gene panel names, IDs — no personal data | No personal data; low risk |
| **NCBI PubMed Entrez API** | **National Center for Biotechnology Information (NIH/NLM)** | **USA** | **No EU–US adequacy decision in force for government services** | **User's gene/keyword search query, PMID batches, admin email (`Entrez.email`), IP address (implicit)** | **No SCCs in place. NCBI is a US federal agency subject to US law (FISMA, potentially FISA). NCBI's own privacy policy (nlm.nih.gov/web_policies) states they may log tool and email fields. This transfer should be reviewed under Art. 46 GDPR (appropriate safeguards) or Art. 49(1)(b) (necessary for contract performance). Until safeguards are formalised, users should be informed that searches are processed by NCBI in the USA.** |

**Action required:** Update the Privacy Policy to disclose the NCBI transfer. Assess whether the transfer qualifies under Art. 49(1)(b) (performance of a contract with the data subject) given that users explicitly choose to search PubMed. Add a brief disclosure to the LitReview search page.

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

- [ ] **Server-side HTML sanitization for KnowHow articles**: Quill HTML must be sanitized before DB storage (e.g., using `bleach`/`nh3` with an allowlist). Currently raw HTML is stored and rendered with `| safe`.
- [ ] **Retention schedules**: Implement scheduled deletion for LitReview search history (suggested: 12 months after creation) and `user_article_actions` (suggested: 12 months after last activity).
- [ ] **Self-service search history deletion**: Add a route allowing users to delete their own search history records.
- [ ] **Notes field warning**: Add UI notice on article detail page warning users not to record patient-identifiable information in personal notes.
- [ ] **Privacy Policy update**: Disclose LitReview data (search history, interaction tracking, notes), KnowHow attribution, NCBI API transfer, and retention periods for all new tables.
- [ ] **LitReview search page disclosure**: Add a brief notice that search terms are sent to NCBI (USA) for processing.

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
| International transfer disclosed | **Partially** — NCBI transfer is operational but not yet disclosed in Privacy Policy |

**Final Assessment (v1.1):**  
The addition of LitReview and KnowHow **materially increases the personal data processing scope** of PanelMerge. The risks introduced are manageable but require concrete action, particularly:
1. **Fix the stored XSS vulnerability** in KnowHow article rendering (R12 — code change).
2. **Disclose and review the NCBI international transfer** (R7 — policy + user notice).
3. **Define and implement retention schedules** for search history and interaction data (R8, R14).
4. **Update the Privacy Policy** to accurately describe all new processing activities.

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
- [ ] Privacy Policy updated for new activities  
- [ ] Server-side HTML sanitization implemented for KnowHow  
- [ ] LitReview search history retention schedule defined and implemented  
- [ ] Self-service search history deletion route added  
- [ ] Notes field UI warning added  

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
| `knowhow_articles` | `content` | Rich HTML (up to 500 KB) | Potentially — **highest risk field** | Rendered `\| safe`; no sanitization currently; could contain patient info |
| `knowhow_articles` | `created_at`, `updated_at` | Timestamps | Yes (indirectly) | |
| `knowhow_links` | `user_id` | FK | Yes — attribution | Displayed as first_name or username |
| `knowhow_links` | `url` | String | Low | User-contributed external URL |
| `knowhow_links` | `description` | String | Potentially | User-authored text |
| `knowhow_categories` / `knowhow_subcategories` | All columns | Admin-managed labels | No personal data | |

