# PanelMerge — GDPR Compliance and Data Protection Policy

**Last Updated:** 12/10/2025  
**Version:** 1.0  
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

---

## 4. Purpose and Legal Basis for Processing

| Data Type | Purpose of Processing | Legal Basis under GDPR |
|------------|----------------------|------------------------|
| Session data (IP, user agent, cookies) | Technical operation, security, error handling | Legitimate interest (Art. 6(1)(f)) |
| Uploaded gene panel files | Combine and analyze gene lists | Not personal data (outside GDPR scope) |
| User account data (email, password hash) | Authentication, access control, app administration | Consent or performance of a contract (Art. 6(1)(a) or (b)) |
| Logs and analytics (if enabled) | Performance monitoring and troubleshooting | Legitimate interest (Art. 6(1)(f)) |

---

## 5. Data Minimization and Retention

- Only the minimum data required for functionality is collected.  
- Uploaded files are processed **in-memory or temporarily on the server** and deleted automatically after the session ends or within 1 hour.  
- User account data is stored only as long as the account remains active.  
- Logs are retained for a maximum of **90 days**, after which they are automatically deleted or anonymized.  
- Backups are encrypted and follow the same retention limits as the primary data.

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

PanelMerge interacts with external, publicly available APIs (e.g., PanelApp).  
No personal data is transmitted to these services.  

If future integrations involve data transfers outside the EEA, such transfers will comply with Chapter V of the GDPR through appropriate safeguards such as Standard Contractual Clauses (SCCs).  

No data is sold or shared for commercial purposes.

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
| Third Parties | Limited to public APIs (non-personal) |
| Cookies | Essential only; future consent mechanism |
| Documentation | RoPA + privacy documentation maintained |
