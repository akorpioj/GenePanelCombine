# Data Protection Impact Assessment (DPIA)
**Application:** PanelMerge
**Version:** 1.0  
**Date Completed:** 12/10/2025
**Controller:** Anita Korpioja
**Contact:** anita.korpioja@gmail.com  
**Location of Processing:** Finland (EU)  
**Repository:** https://github.com/akorpioj/GenePanelCombine  

---

## 1. Purpose and Scope

The purpose of this DPIA is to assess and document the privacy risks associated with the processing of data in the **PanelMerge** web application.

PanelMerge is a research and diagnostic support tool designed to merge and compare **gene panel lists** from user-uploaded files and publicly available databases (e.g., PanelApp). It is primarily intended for healthcare and research professionals, but does not handle identifiable patient data in its current version.

This DPIA assesses the **current deployment** (non-personal data only) and provides a framework for future versions that may involve **genetic or clinical information**.

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

---

## 3. Necessity and Proportionality

| **Principle** | **Assessment** |
|----------------|----------------|
| **Purpose limitation** | Data is processed solely for combining gene panels and supporting research workflows. No unrelated processing. |
| **Data minimization** | The app collects only essential technical data (session cookies, IPs). Uploaded files are non-personal and deleted promptly. |
| **Storage limitation** | Retention strictly limited — uploads < 1 hour, logs ≤ 90 days. |
| **Accuracy** | Data accuracy depends on user input and public API data; irrelevant for personal data accuracy as no identifiers are stored. |
| **Integrity & confidentiality** | HTTPS enforced, hashed credentials, sandboxed uploads, encrypted backups. |
| **Transparency** | A clear Privacy Policy is provided via `/privacy`. |
| **User rights enablement** | Users can contact the controller (anita.korpioja@gmail.com) for any access or deletion requests. |
| **Data transfer controls** | External APIs receive no personal data; potential cross-border transfers limited to public, non-identifiable data. |

**Conclusion:**  
The processing activities are necessary and proportionate to the legitimate purpose of combining and comparing gene panels.

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

---

### 4.2 Residual Risks After Mitigation

After implementing the above measures, the remaining risk is considered **Low to Medium** and acceptable for the current scope of processing.

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
- **Minimal data collection**: no identifiers required.  
- **Sandboxed file uploads**: isolated, auto-deleted.  
- **Secure defaults**: HTTPS, CSRF protection, secure cookies.  
- **Logging limited and anonymized**.  
- **No unnecessary cookies or analytics tracking.**

---

## 7. DPIA Conclusion and Sign-off

| **Criteria** | **Result** |
|---------------|------------|
| Processing involves personal data | Minimal (technical only) |
| Processing involves special categories | No |
| Large-scale or automated profiling | No |
| High-risk to individuals’ rights and freedoms | No (current version) |
| DPIA required under Art. 35 | **No** — not required at present |
| DPIA required in future expansions | **Yes** — if patient, genetic, or clinical identifiers introduced |

**Final Assessment:**  
The processing activities of PanelMerge **do not pose a high risk** under current functionality.  
A new DPIA **must be conducted** before any extension of the application to handle **personal genetic or clinical data**.

---

### **Sign-off**

| Role | Name | Date | Signature |
|-------|------|------|------------|
| Data Controller | Anita Korpioja | 12/10/2025 | |
| Reviewer / Auditor | [Optional] | [Insert date] | |

---

## Appendix A — Checklist Summary

- [x] Data inventory and classification complete  
- [x] Risk areas identified  
- [x] Mitigation measures implemented  
- [x] Residual risk acceptable  
- [x] No DPIA required currently  
- [x] DPIA framework established for future high-risk processing  

