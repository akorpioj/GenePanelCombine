# PanelMerge — GDPR Compliance and Data Protection Policy

**Last Updated:** 25/03/2026  
**Version:** 1.2 (Saved Panels, Security Infrastructure, and Panel Exports disclosed; retention periods extended; DPIA v1.4)  
**Controller:** Anita Korpioja  
**Contact:** anita.korpioja@gmail.com  

---

## 1. Introduction

This document outlines the data protection and privacy practices of **PanelMerge** (the “Application”), in accordance with the **General Data Protection Regulation (EU) 2016/679 (GDPR)** and relevant national legislation.  

PanelMerge is a web-based tool designed to combine and compare gene panels from multiple public databases and user-provided lists. The Application emphasizes data minimization and privacy by design: it does **not** require personal identifiers, patient information, or other sensitive personal data to function.

This policy explains what data may be processed, how it is handled, and which measures are implemented to ensure compliance with GDPR principles.

---

## 2. Data Controller and Contact

**Data Controller:**  
Anita Korpioja
**Email:** [anita.korpioja@gmail.com](mailto:anita.korpioja@gmail.com)

If you have questions regarding this policy or your rights under GDPR, please contact the Controller using the email above.

---

## 3. Categories of Data Processed

### 3.1 Non-Personal Data

The core function of PanelMerge involves processing **non-personal** scientific data such as:
- Gene names and identifiers (e.g., HGNC symbols)  
- Gene panel lists from public repositories (e.g., Genomics England PanelApp, PanelApp Australia)  
- Anonymous file uploads (Excel, CSV, TSV) containing gene symbols  

These datasets **do not contain personal data** and therefore are not subject to GDPR obligations beyond standard information security.

### 3.2 Personal Data (Minimal)

In limited circumstances, PanelMerge may process minimal personal data, such as:
- **IP address** and browser metadata (for session management and security logging)  
- **User account data** (if an authenticated version is deployed) including:
  - Name or alias  
  - Email address  
  - Role (admin, user, developer)  
  - Password hash (never stored in plaintext)

Such data is only collected to support core technical or administrative functions and is **never used for marketing or profiling**.

### 3.3 LitReview: Literature Search Behaviour Data

The **LitReview** feature processes the following personal data for registered users:

- **Search history**: each PubMed search is stored with your search query text, filters (article type, date range, maximum results), result count, and creation timestamp. This data is linked to your user account and may indirectly reveal your clinical or research focus.
- **Article interaction records**: your article-viewing activity (viewed/not viewed status, view count, first and last viewed timestamps) and save status are recorded. This constitutes limited behavioural profiling of your research activity.
- **Personal notes** (planned feature, not yet available): a notes field is reserved in the database schema for future use. It is not currently exposed in the application interface. When implemented, a data minimisation warning will be shown at the point of entry.

**Retention:** Search history and unsaved article interaction records are automatically deleted after **365 days** from creation. Explicitly saved article records are retained until you delete them or close your account. You can delete individual searches or your entire history at any time from your [Search History](/litreview/history) page.

### 3.4 KnowHow: User-Attributed Content

The **KnowHow** knowledge base processes:

- **Authored articles**: articles you publish are attributed to you by first name or username and are visible to all logged-in users. Article title, content (HTML, sanitized server-side with `nh3`), category, and timestamps are stored alongside your user ID.
- **Submitted links**: external links you contribute are attributed to your name and are visible to all logged-in users.

**Content restriction**: KnowHow articles and links must not contain patient-identifiable or other sensitive personal data. A warning is displayed in the article editor before you write.

**Retention:** KnowHow articles and links persist until deleted by you, an editor, or an administrator. No automated retention period currently applies to KnowHow content.

---

### 3.5 Saved Panels: Panel Library and Collaboration

The **Saved Panels** feature (Panel Library) processes the following data for registered users:

- **Panel records**: panel name, description, tags, status (Active/Draft/Archived), visibility (Private/Shared/Public), and timestamps, linked to your user account.
- **Gene annotations** (`user_notes`): free-text annotations you attach to individual genes within a panel. These notes are user-supplied and linked to your user account. They must not contain patient-identifiable information.
- **Version history**: each panel edit creates a version snapshot recording the full gene list, change summary, and the user ID of the person who made the change.
- **Change log**: individual change records (genes added or removed) are stored with your user ID and a timestamp.
- **Panel shares**: when you share a panel with another user, a share record is created storing both user IDs, the permission level granted, and the share creation timestamp.
- **Access metadata**: last-accessed timestamps are updated each time a panel is viewed.

> **Gene annotations privacy notice:** Gene annotations (user notes) attached to a panel are visible to any user the panel is shared with, and to all logged-in users if the panel is set to Public. Do not enter patient-identifiable or sensitive information in gene annotations.

**Retention:** Panel records, versions, changes, and shares persist until you delete the panel or close your account. Full account deletion cascades to all panels and associated version, change, gene annotation, and share records owned by you.

---

### 3.6 Security Infrastructure: Visit Logs, Login Statistics, and Geolocation

PanelMerge operates several security monitoring subsystems that automatically collect personal data:

- **Visit logs**: IP address, visited path, browser user agent string, and timestamp are recorded for every HTTP request (authenticated and unauthenticated).
- **Suspicious activity log**: IP address, email address (if supplied), geolocation data (city and country derived from IP), browser user agent, activity type (e.g., failed password reset), alert trigger status, and timestamp are recorded when anomalous authentication behaviour is detected.
- **Login statistics**: per-user login count, last login date, and last login IP address are maintained in the user record for security monitoring.
- **Session records**: active session tokens and associated IP addresses are stored to enforce session limits and detect session anomalies.

IP-derived geolocation (city and country) is used solely for security alerting (detecting logins from unusual locations). Location data is not used for marketing or behavioural profiling.

**Retention:** Visit logs are retained for a maximum of **90 days**. Suspicious activity records are retained for a maximum of **90 days**. Both are subject to administrator-triggered purge via the Admin panel in accordance with GDPR Art. 5(1)(e).

---

### 3.7 Panel Exports and Download Logging

When you download a gene panel (export gene lists to Excel, CSV, or other formats), the application may log:

- **Panel download records**: your user ID (if authenticated), IP address, the panel IDs and list types downloaded, gene count, and download timestamp.
- **Export templates**: if you save a named export configuration (template), the template name and format settings are stored linked to your user account. Export templates contain no special-category data.

**Retention:** Panel download records are retained for a maximum of **12 months** to support audit trail requirements, then purged by the administrator. Export templates persist until you delete them.

---

## 4. Purpose and Legal Basis for Processing

| Data Type | Purpose of Processing | Legal Basis under GDPR |
|------------|----------------------|------------------------|
| Session data (IP, user agent, cookies) | Technical operation, security, error handling | Legitimate interest (Art. 6(1)(f)) |
| Uploaded gene panel files | Combine and analyze gene lists | Not personal data (outside GDPR scope) |
| User account data (email, password hash) | Authentication, access control, app administration | Consent or performance of a contract (Art. 6(1)(a) or (b)) |
| Logs and analytics (if enabled) | Performance monitoring and troubleshooting | Legitimate interest (Art. 6(1)(f)) |
| LitReview search queries and search history | Recording searches to display past searches and support result re-use | Performance of a contract / legitimate interest (Art. 6(1)(b) and (f)) |
| LitReview article interaction records (view status, save status, timestamps) | Supporting search result management and limited personalisation | Legitimate interest (Art. 6(1)(f)) |
| KnowHow articles and links (attributed to author by name) | Enabling professional knowledge sharing among registered users | Performance of a contract / legitimate interest (Art. 6(1)(b) and (f)) |
| Saved panel records, gene annotations, version history, change log, panel shares | Enabling panel library, versioning, and collaboration between users | Performance of a contract / legitimate interest (Art. 6(1)(b) and (f)) |
| Visit logs (IP address, path, user agent, timestamp) | Security monitoring, fraud detection, intrusion detection | Legitimate interest (Art. 6(1)(f)); retained maximum 90 days |
| Suspicious activity records (IP, email, geolocation, activity type, timestamp) | Detection and investigation of authentication anomalies and account abuse | Legitimate interest (Art. 6(1)(f)); retained maximum 90 days |
| Panel download records (IP, user ID, panel details, timestamp) | Audit trail for data export activity | Legitimate interest (Art. 6(1)(f)); retained maximum 12 months |
| Export templates (template name, format settings) | Saving user export preferences for convenience | Performance of a contract / legitimate interest (Art. 6(1)(b) and (f)) |

---

## 5. Data Minimization and Retention

- Only the minimum data required for functionality is collected.  
- Uploaded files are processed **in-memory or temporarily on the server** and deleted automatically after the session ends or within 1 hour.  
- User account data is stored only as long as the account remains active.  
- Logs are retained for a maximum of **90 days**, after which they are automatically deleted or anonymized.  
- Backups are encrypted and follow the same retention limits as the primary data.
- **LitReview search history and unsaved article interactions**: retained for a maximum of **365 days** from the date of creation; deleted automatically by scheduled maintenance run via `flask litreview cleanup`.
- **LitReview saved article records** (`is_saved=True`): retained until deleted by you or until account closure. Saving an article prevents automated deletion.
- **PubMed article metadata cache**: each article is cached locally for **7 days** and refreshed automatically on access.
- **KnowHow articles and links**: retained until deleted by the author, an editor, or an administrator.
- **Self-service deletion**: you can delete individual LitReview searches or clear your entire search history from your [Search History](/litreview/history) page. Full account deletion cascades to remove all associated LitReview and interaction data.
- **Visit logs**: retained for a maximum of **90 days**, then permanently deleted by the administrator via the Admin panel.
- **Suspicious activity records**: retained for a maximum of **90 days**, then permanently deleted by the administrator via the Admin panel. Records may be retained longer if required for an active security investigation.
- **Panel download records**: retained for a maximum of **12 months** to support audit trail requirements, then permanently deleted by the administrator.
- **Saved panel records and gene annotations**: retained until you delete the panel or close your account. Cascade deletion removes all version history, change log entries, gene annotations, and share records associated with the panel.
- **Export templates**: retained until you delete them. Full account deletion removes all your export templates.

---

## 6. Data Subject Rights

Where applicable, users (data subjects) have the following rights under GDPR:

- **Right of access:** to obtain confirmation and a copy of personal data.  
- **Right to rectification:** to correct inaccurate or incomplete data.  
- **Right to erasure (“right to be forgotten”)**.  
- **Right to restriction of processing.**  
- **Right to data portability.**  
- **Right to object** to processing based on legitimate interest.  
- **Right to lodge a complaint** with a supervisory authority (in Finland: *Tietosuojavaltuutetun toimisto*).

Requests can be made by email to [anita.korpioja@gmail.com](mailto:anita.korpioja@gmail.com). All requests are handled within the statutory timeframe (one month).

---

## 7. Security Measures

PanelMerge implements a range of technical and organizational measures to ensure confidentiality, integrity, and availability of data:

- HTTPS / TLS encryption for all data in transit  
- Encrypted database and file storage for any data at rest  
- Strong authentication (hashed and salted passwords)  
- CSRF and session security mechanisms  
- Role-based access control (for admin features)  
- Automated log rotation and restricted access to logs  
- Regular patching, code review, and vulnerability scanning  
- Automatic deletion of temporary uploads after processing  
- Isolated execution environment for file uploads (sandboxing)  
- Secure backups with encryption and limited access

---

## 8. Data Sharing and Third Parties

### 8.1 Genomics England PanelApp
PanelMerge retrieves publicly available gene panel data from the Genomics England PanelApp API (United Kingdom). The UK benefits from an EU adequacy decision under Art. 45 GDPR. No personal data is transmitted in these requests.

### 8.2 NCBI PubMed (USA) — International Data Transfer
The **Literature Review (LitReview)** feature allows users to search the PubMed database operated by the **National Center for Biotechnology Information (NCBI)**, a division of the US National Institutes of Health (NIH), located in Bethesda, Maryland, **United States of America**.

When you submit a literature search, the following data is transmitted to NCBI servers:
- Your **search query** (gene name, keyword, or author name)
- A **list of PubMed article IDs (PMIDs)** for article detail retrieval
- A **tool identifier** (`PanelMerge-LitReview`) and an administrator **contact email address** required by the NCBI Entrez API terms of use
- Your **IP address** (inherent in any HTTP request)

**Legal basis for this transfer:** This transfer is necessary to perform the PubMed search service you have explicitly requested (Art. 49(1)(b) GDPR — transfer necessary for the performance of a contract between the data subject and the controller, or for the implementation of pre-contractual measures taken at the data subject's request).

**Important:** The United States does not have a general EU adequacy decision. NCBI is a US federal government agency and is not subject to the EU–US Data Privacy Framework. NCBI's own privacy and data policies apply to data processed on their systems; see [https://www.nlm.nih.gov/web_policies.html](https://www.nlm.nih.gov/web_policies.html). PanelMerge transmits the minimum data required by the Entrez API; no account credentials, names, or other personal profile data are ever sent to NCBI.

You may choose not to use the LitReview search feature to avoid this transfer.

### 8.3 General
No data is sold or shared for commercial purposes. No personal data is shared with any third party other than as described above.

---

## 9. Cookies and Tracking

The application uses only **essential cookies** required for:
- Maintaining user sessions  
- Securing authenticated requests  

No analytics or tracking cookies are used by default.  
If non-essential cookies (e.g., for analytics) are introduced, a consent banner will be provided to obtain explicit opt-in consent in compliance with GDPR and ePrivacy Directive requirements.

---

## 10. Data Breach Notification

In the unlikely event of a personal data breach, the following procedures will apply:
- The Controller will assess the impact within 72 hours  
- The relevant supervisory authority will be notified if the breach is likely to result in a risk to the rights and freedoms of natural persons  
- Affected users will be informed if the breach poses a high risk  
- Incident details and corrective actions will be documented

---

## 11. Data Protection Impact Assessments (DPIA)

A DPIA will be performed prior to introducing any new processing activities that involve:
- Sensitive (special category) data such as genetic or health information  
- Large-scale profiling or monitoring  
- High-risk automated processing  

The DPIA will assess potential risks and document mitigation measures before deployment.

---

## 12. Sub-Processors and Hosting

The application may be deployed using GDPR-compliant cloud infrastructure providers (e.g., Google Cloud, AWS, or other EU-based providers).  
All sub-processors are bound by written data processing agreements (DPAs) ensuring compliance with GDPR Article 28.

---

## 13. Privacy by Design and Default

All development follows principles of **Privacy by Design and by Default**, including:
- Minimizing data collection  
- Default anonymization of data where feasible  
- Clear separation of personal and non-personal datasets  
- Secure coding practices  
- Regular internal privacy reviews

---

## 14. Accountability and Governance

- A single responsible person (Data Controller) is accountable for GDPR compliance  
- Records of Processing Activities (RoPA) are maintained  
- Privacy and security documentation are reviewed annually or upon significant system changes  
- Personnel (if any) receive GDPR and secure-coding training

---

## 15. Changes to This Policy

This policy may be updated periodically to reflect:
- Regulatory changes  
- Feature updates or new data processing activities  
- Feedback from supervisory authorities or users  

The updated version will be published on the official project page or included in the application’s Privacy section, with revision date clearly indicated.

---

## 16. Contact and Complaints

If you have concerns or wish to exercise your data protection rights, please contact:

**Email:** [anita.korpioja@gmail.com](mailto:anita.korpioja@gmail.com)  

**Supervisory Authority:**  
Tietosuojavaltuutetun toimisto (Office of the Data Protection Ombudsman, Finland)  
[https://tietosuoja.fi/en/home](https://tietosuoja.fi/en/home)

---

## Appendix A — Summary of Compliance Controls

| Control Area | Implementation |
|---------------|----------------|
| HTTPS / TLS | Enforced across entire app |
| File Uploads | Processed in sandbox, auto-deleted |
| Encryption | Data at rest and in transit |
| Retention | Temporary; logs ≤ 90 days |
| Access Control | Role-based; hashed passwords |
| DPIA | Required for clinical data processing |
| Data Subject Rights | Email-based request handling |
| Third Parties | PanelApp (UK, adequacy): no personal data. NCBI/PubMed (USA, Art. 49(1)(b)): search query + tool email transmitted when LitReview is used |
| Cookies | Essential only; future consent mechanism |
| Documentation | RoPA + privacy documentation maintained |
