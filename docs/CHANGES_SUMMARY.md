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
