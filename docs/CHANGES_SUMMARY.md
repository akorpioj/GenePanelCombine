# Summary of Changes: v1.5.4

---

## Feature: KnowHow category sort order (25/03/2026)

Added a sort selector to the KnowHow index page allowing users to reorder categories. The selected sort is persisted in a browser cookie so it is remembered across sessions.

**Sort options:**
- **Custom order** — admin-defined position (default)
- **A → Z** — category label alphabetical ascending
- **Z → A** — category label alphabetical descending
- **Most content first** — categories with the highest combined article + link count appear first
- **Recently updated** — categories whose most recent article edit or link addition appears first

**Implementation details:**
- Sort applied in `app/knowhow/routes.py` `index()` after fetching categories; server-side Python sort on the list returned by `_get_categories()`
- `_VALID_SORTS` whitelist validated on every request; invalid values silently fall back to `position`
- Preference persisted in `knowhow_sort` cookie (1-year expiry, `httponly`, `SameSite=Lax`) via `make_response` + `set_cookie`
- Priority order: explicit `?sort=` query param → saved cookie → default (`position`)
- Sort selector `<select onchange="this.form.submit()">` submits a GET form on change — no JavaScript framework needed
- `sort` context variable passed to template to keep the selected option highlighted

**Files changed:** `app/knowhow/routes.py`, `app/templates/knowhow/index.html`

---
