# KnowHow — Implementation Reference

_Last updated: 25/03/2026_

This document describes the current implementation of the KnowHow knowledge base module in full technical detail.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Database Models](#2-database-models)
3. [Routes & Validation](#3-routes--validation)
4. [Helper Functions](#4-helper-functions)
5. [Template Reference](#5-template-reference)
6. [Security Controls](#6-security-controls)
7. [Access Control Matrix](#7-access-control-matrix)
8. [Audit Logging](#8-audit-logging)
9. [Cookie & Session State](#9-cookie--session-state)
10. [Default Data](#10-default-data)

---

## 1. Architecture Overview

| Item | Detail |
|------|--------|
| Blueprint name | `knowhow` |
| URL prefix | `/knowhow` |
| Blueprint file | `app/knowhow/__init__.py` |
| Routes file | `app/knowhow/routes.py` |
| Templates | `app/templates/knowhow/` |
| Auth requirement | All routes require `@login_required` |

The blueprint is registered in `app/__init__.py` with no additional configuration.

---

## 2. Database Models

### KnowhowCategory

**Table:** `knowhow_categories`

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | Integer | PK | — |
| `slug` | String(64) | UNIQUE, NOT NULL | — |
| `label` | String(128) | NOT NULL | — |
| `color` | String(32) | NOT NULL | `'#0369a1'` |
| `description` | Text | nullable | `null` |
| `position` | Integer | NOT NULL | `0` |
| `created_at` | DateTime | — | `datetime.datetime.now` |

**Relationships:**

- `subcategories` → `KnowhowSubcategory`, one-to-many, `cascade='all, delete-orphan'`, ordered by `position`

**Notes:**
- `slug` is the stable identifier used as a foreign key by `KnowhowArticle.category` and `KnowhowLink.category` (stored as a string, not a DB FK — allows category deletion without orphaning content)
- 10 default categories are seeded idempotently on first use (see [§10](#10-default-data))

---

### KnowhowSubcategory

**Table:** `knowhow_subcategories`

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | Integer | PK | — |
| `category_id` | Integer | FK → `knowhow_categories.id` ON DELETE CASCADE, NOT NULL | — |
| `label` | String(128) | NOT NULL | — |
| `position` | Integer | NOT NULL | `0` |
| `created_at` | DateTime | — | `datetime.datetime.now` |

**Relationships:**

- `category` backref from `KnowhowCategory.subcategories`
- `articles` backref from `KnowhowArticle.subcategory` (lazy `dynamic`)
- `links` backref from `KnowhowLink.subcategory` (lazy `dynamic`)

**Notes:**
- Deleting a subcategory sets `subcategory_id = NULL` on all its articles and links (they revert to root level within their category)

---

### KnowhowArticle

**Table:** `knowhow_articles`

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | Integer | PK | — |
| `title` | String(256) | NOT NULL | — |
| `summary` | String(512) | nullable | `null` |
| `category` | String(64) | NOT NULL, INDEX | — |
| `content` | Text | NOT NULL | `''` |
| `user_id` | Integer | FK → `user.id` ON DELETE CASCADE, NOT NULL | — |
| `subcategory_id` | Integer | FK → `knowhow_subcategories.id` ON DELETE SET NULL, nullable | `null` |
| `created_at` | DateTime | NOT NULL | `datetime.datetime.now` |
| `updated_at` | DateTime | NOT NULL, `onupdate=datetime.datetime.now` | `datetime.datetime.now` |

**Relationships:**

- `user` → `User`, backref `knowhow_articles` (lazy `dynamic`)
- `subcategory` → `KnowhowSubcategory`, backref `articles` (lazy `dynamic`)

**Notes:**
- `category` stores the slug string (not a DB FK); if the category is deleted, articles become hidden but are not deleted
- `summary` is a short plain-text teaser (max 512 chars) displayed beneath article titles in the index and category detail views; optional
- `content` stores Quill-generated HTML, sanitized by `nh3` before storage (see [§6](#6-security-controls))
- `updated_at` auto-updates on any `db.session.commit()` that touches the row

---

### KnowhowLink

**Table:** `knowhow_links`

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | Integer | PK | — |
| `category` | String(64) | NOT NULL, INDEX | — |
| `url` | String(2048) | NOT NULL | — |
| `description` | String(512) | NOT NULL | — |
| `user_id` | Integer | FK → `user.id` ON DELETE CASCADE, NOT NULL | — |
| `subcategory_id` | Integer | FK → `knowhow_subcategories.id` ON DELETE SET NULL, nullable | `null` |
| `created_at` | DateTime | NOT NULL | `datetime.datetime.now` |

**Relationships:**

- `user` → `User`, backref `knowhow_links` (lazy `dynamic`)
- `subcategory` → `KnowhowSubcategory`, backref `links` (lazy `dynamic`)

---

## 3. Routes & Validation

### Public routes (any authenticated user)

#### `GET /knowhow/`  — `knowhow.index`

Landing page showing all categories and their content.

- Fetches all articles (`ORDER BY created_at DESC`) and all links
- Builds `articles_map` and `links_map`: `{category_slug: {subcategory_id | None: [items]}}`
- Applies the selected sort to the category list (see § below)
- **Sort resolution order:** `?sort=` query param → `knowhow_sort` cookie → default `'position'`
- Invalid sort values are silently replaced with `'position'`
- Sets the `knowhow_sort` cookie (1 year, `httponly`, `SameSite=Lax`) on every response
- Index shows at most **3 articles per bucket**; a "+ N more — see all" link appears if there are more

**Sort options:**

| Value | Behaviour |
|-------|-----------|
| `position` | Admin-defined position (default) |
| `label_asc` | Category label A → Z (case-insensitive) |
| `label_desc` | Category label Z → A |
| `most_content` | Categories with most articles + links first |
| `recently_updated` | Categories whose most recent article/link is newest first |

---

#### `GET /knowhow/category/<slug>`  — `knowhow.category`

Shows all content for one category. Returns 404 for unknown slugs.

- Fetches articles and links filtered by slug
- Builds `articles_map` and `links_map` keyed by `subcategory_id` (no truncation — all articles shown)

---

#### `GET /knowhow/search`  — `knowhow.search`

Full-text search across articles and links.

- Requires query param `?q=`; minimum 2 characters (enforced in route)
- Searches `KnowhowArticle.title` and `KnowhowArticle.content` via `ILIKE`
- Searches `KnowhowLink.description` and `KnowhowLink.url` via `ILIKE`
- Returns up to 50 articles and 50 links, ordered `created_at DESC`
- User input is sanitised via `_safe_like()` before building the `LIKE` pattern

---

#### `GET /knowhow/articles/new`  — `knowhow.new_article`

Renders a blank article editor.

---

#### `POST /knowhow/articles`  — `knowhow.create_article`

Creates a new article.

**Validation:**

| Field | Rule |
|-------|------|
| `title` | Required; max 256 chars |
| `summary` | Optional; max 512 chars; stripped of leading/trailing whitespace |
| `category` | Required; must exist as a `KnowhowCategory.slug` |
| `content` | UTF-8 size ≤ 500 KB; sanitized via `_sanitize_content()` |
| `subcategory_id` | Optional; if provided, must exist and belong to the selected category |

On success: redirects to `knowhow.view_article`.  
On failure: re-renders the editor with a flash error.

---

#### `GET /knowhow/articles/<id>`  — `knowhow.view_article`

Displays a published article. Returns 404 if not found.

---

#### `GET /knowhow/articles/<id>/edit`  — `knowhow.edit_article`

Renders the article editor prefilled. Returns 403 if the current user is not the author, ADMIN, or EDITOR.

---

#### `POST /knowhow/articles/<id>/edit`  — `knowhow.update_article`

Updates an existing article. Same validation rules as `create_article`. 403 if not authorised.

---

#### `POST /knowhow/articles/<id>/delete`  — `knowhow.delete_article`

Deletes an article. 403 if not authorised. Redirects to `knowhow.index` with category anchor.

---

#### `POST /knowhow/links`  — `knowhow.add_link`

Adds a community link to a category.

**Validation:**

| Field | Rule |
|-------|------|
| `category` | Must exist as a `KnowhowCategory.slug` |
| `url` | Must match `^https?://`; max 2048 chars |
| `description` | 3–512 chars |
| `subcategory_id` | Optional; if provided, must belong to the selected category |

Redirects to `knowhow.index` with category anchor.

---

#### `POST /knowhow/links/<id>/delete`  — `knowhow.delete_link`

Deletes a link. 403 if the current user is not the owner, ADMIN, or EDITOR.

---

### Admin-only routes

All routes below require `@_admin_required` in addition to `@login_required` (returns 403 otherwise).

| Route | Method | Action |
|-------|--------|--------|
| `/knowhow/admin` | GET | Render admin panel |
| `/knowhow/admin/categories` | POST | Create category (label, slug, palette colour, optional description) |
| `/knowhow/admin/categories/<id>/edit` | POST | Update label, colour, position, description |
| `/knowhow/admin/categories/<id>/delete` | POST | Delete category (orphaned articles/links hidden but not deleted) |
| `/knowhow/admin/categories/<id>/subcategories` | POST | Create subcategory |
| `/knowhow/admin/subcategories/<id>/edit` | POST | Update subcategory label |
| `/knowhow/admin/subcategories/<id>/delete` | POST | Delete subcategory (articles/links revert to root) |

**Category creation validation:**

| Field | Rule |
|-------|------|
| `label` | Required; max 128 chars |
| `slug` | Must match `^[a-z0-9_]{1,64}$`; must be unique |
| `color` | Must be one of the 12 palette hex values |
| `description` | Optional; max 512 chars |

**Position assignment:** On creation, `position = max(existing positions) + 1`.

---

## 4. Helper Functions

All helpers live at module level in `app/knowhow/routes.py`.

### `_admin_required(f)`

Decorator. Calls `abort(403)` if `current_user.is_admin()` returns `False`.

### `_seed_categories()`

Idempotent. Inserts the 10 default categories only if `KnowhowCategory.query.count() == 0`.

### `_get_categories()`

Calls `_seed_categories()` then returns all categories ordered by `position ASC, id ASC`.

### `_subcategories_json(categories)`

Returns a flat Python list (JSON-serialisable):
```python
[{'id': sub.id, 'label': sub.label, 'category_slug': cat.slug}
 for cat in categories for sub in cat.subcategories]
```
Passed to templates as `subcategories_json` for the Add Link modal's JavaScript filter.

### `_validate_subcategory(sub_id_raw, category)`

Returns `(subcategory_id_or_None, error_msg_or_None)`.  
Validates that `sub_id_raw` is a valid integer pointing to a subcategory whose `category_id` matches `category.id`.

### `_safe_like(q: str) -> str`

Escapes `\`, `%`, `_` in user input for use in SQL `LIKE`/`ILIKE` patterns.

### `_strip_html(html: str) -> str`

Removes all HTML tags with `re.sub(r'<[^>]+>', ...)` and collapses whitespace. Used to produce snippet text from stored Quill HTML.

### `_highlight(text: str, query: str) -> Markup`

1. Escapes `text` with `markupsafe.escape` (prevents XSS)
2. Wraps each case-insensitive occurrence of `query` in:
   ```html
   <mark class="bg-yellow-200 rounded px-0.5">…</mark>
   ```
3. Returns a `markupsafe.Markup` instance (safe to render with `| safe` in templates)

### `_snippet(html: str, query: str) -> Markup`

1. Strips HTML to plain text with `_strip_html()`
2. Finds the first occurrence of `query` (case-insensitive)
3. Extracts `±120` characters around the match
4. Prepends/appends `…` if the excerpt doesn't start/end at the text boundary
5. Passes the excerpt through `_highlight()`  
6. Falls back to the first 240 chars of plain text if the query is not found

---

## 5. Template Reference

### `knowhow/index.html`

**Extends:** `base.html`  
**Context:** `categories`, `articles_map`, `links_map`, `subcategories_json`, `sort`

Key sections:
- **Header** — title, description, search form, Back to Main Page link
- **Actions bar** — New Article button, sort selector, Manage Categories button (admin only)
- **Category cards** — one card per category; root articles (max 3) + root links + subcategory folders (max 3 articles each)
- **Contribute info box** — usage hint at the bottom
- **Add Link modal** — shared by all category `+` buttons

---

### `knowhow/category.html`

**Extends:** `base.html`  
**Context:** `category`, `articles_map`, `links_map`, `subcategories_json`

Like the index card for one category, but without the 3-article truncation. Shows all articles and links. Includes the Add Link modal.

---

### `knowhow/article_view.html`

**Extends:** `base.html`  
**Context:** `article`, `category`, `subcategory`

- Breadcrumb: `KnowHow › [Category] › [Subcategory] › Article Title`
- Breadcrumb category/subcategory links point to `knowhow.category`
- Article body rendered with `{{ article.content | safe }}` inside `.knowhow-article-body`
- Inline `<style>` block styles Quill output (h1–h3, p, ul, ol, blockquote, pre, code, a)

---

### `knowhow/article_editor.html`

**Extends:** `base.html`  
**Context:** `article` (or None), `categories`, `subcategories_json`

- Loads Quill 1.3.7 from jsDelivr CDN
- Toolbar: h1/h2/h3, bold, italic, underline, strikethrough, blockquote, code-block, ordered list, bullet list, link, clean
- PII/patient data warning banner (red)
- On submit: copies `quill.root.innerHTML` into `<input id="contentInput">`
- Delete button (edit mode only) — shows confirmation then submits to `delete_article`

---

### `knowhow/search.html`

**Extends:** `base.html`  
**Context:** `q`, `article_results`, `link_results`

- Search input pre-filled with `q`
- States: idle (no query), no results, results
- Articles grouped separately from links
- `title_hl`, `desc_hl`, `snippet` rendered with `| safe` (values are `markupsafe.Markup`)
- Category colour badges inline via `style="background-color: {{ r.category.color }}"`

---

### `knowhow/admin_categories.html`

**Extends:** `base.html`  
**Context:** `categories`, `palette`

- Add category form (label, slug, colour picker with preview, description)
- Per-category: edit form (toggle), delete button, subcategory list with add/edit/delete
- JavaScript: `togglePanel(id)`, `syncPreview(previewId, hex)`

---

### `knowhow/_links.html`

Partial fragment (not a standalone page). Renders articles and community links for a category. Uses `section_category`, `articles`, `links` context. Used from: external template includes only.

---

## 6. Security Controls

### HTML Sanitisation (Stored XSS Protection)

All article content passes through `_sanitize_content()` before being written to the database:

```python
nh3.clean(
    html,
    tags=_QUILL_TAGS,          # 18-element allowlist
    attributes=_QUILL_ATTRS,   # Per-tag attribute allowlist
    link_rel="noopener noreferrer",
    strip_comments=True,
)
```

**Allowed tags:** `p`, `h1`–`h4`, `strong`, `em`, `u`, `s`, `a`, `code`, `pre`, `blockquote`, `ul`, `ol`, `li`, `br`, `hr`, `span`, `img`

**Attribute allowlist per tag:**

| Tag(s) | Allowed attributes |
|--------|-------------------|
| All | `class`, `style` |
| `a` | + `href`, `rel`, `target` |
| `img` | + `src`, `alt`, `width`, `height` |

`rel` is force-set to `"noopener noreferrer"` by `nh3` regardless of input.

### Search Injection Protection

`_safe_like()` escapes `\`, `%`, and `_` before building LIKE patterns, preventing wildcard injection via the search input.

### Search Result Highlighting (XSS-safe)

`_highlight()` calls `markupsafe.escape()` on all text before inserting `<mark>` tags. The resulting `Markup` object is used with `| safe` in templates — safe because all user-controlled content has been escaped already.

### URL Validation

Links must match `^https?://` (enforced in `add_link()`). Maximum URL length: 2048 chars.

### Content Size Limit

Article content must be ≤ 500 KB when UTF-8 encoded (`len(content.encode('utf-8')) > _MAX_CONTENT_BYTES` check).

### Access Control

- Edit/delete of articles and links: owner, or `UserRole.ADMIN` / `UserRole.EDITOR`
- All admin management routes: `UserRole.ADMIN` only (via `@_admin_required`)
- All routes: `@login_required`

---

## 7. Access Control Matrix

| Action | VIEWER | USER | EDITOR | ADMIN |
|--------|--------|------|--------|-------|
| View index / categories / articles | ✅ | ✅ | ✅ | ✅ |
| Search | ✅ | ✅ | ✅ | ✅ |
| Create article | ✅ | ✅ | ✅ | ✅ |
| Add link | ✅ | ✅ | ✅ | ✅ |
| Edit own article/link | ✅ | ✅ | ✅ | ✅ |
| Edit any article/link | ❌ | ❌ | ✅ | ✅ |
| Delete own article/link | ✅ | ✅ | ✅ | ✅ |
| Delete any article/link | ❌ | ❌ | ✅ | ✅ |
| Manage categories & subcategories | ❌ | ❌ | ❌ | ✅ |

---

## 8. Audit Logging

`AuditService.log_view()` is called in the following routes:

| Route | Resource type | Resource ID | Message |
|-------|--------------|------------|---------|
| `index()` | `'page'` | `'knowhow_index'` | `'Viewed Knowhow index page'` |
| `category(slug)` | `'knowhow_category'` | `slug` | `'Viewed KnowHow category: <label>'` |
| `view_article(id)` | `'knowhow_article'` | `str(article_id)` | `'Viewed KnowHow article: <title>'` |
| `search()` | `'knowhow_search'` | `q[:256]` | `'Searched KnowHow: <q>'` |

---

## 9. Cookie & Session State

| Cookie | Value | Expiry | Flags | Purpose |
|--------|-------|--------|-------|---------|
| `knowhow_sort` | One of the 5 valid sort keys | 1 year (`max_age=31536000`) | `httponly=True`, `samesite='Lax'` | Persist category sort preference across sessions |

The cookie is written on every successful load of `knowhow.index`, regardless of whether the sort changed.

---

## 10. Default Data

10 categories are seeded into `knowhow_categories` on the first request to any KnowHow route if the table is empty (`KnowhowCategory.query.count() == 0`).

| Slug | Label | Colour | Position |
|------|-------|--------|----------|
| `gene_panels` | Gene Panels | `#0369a1` Sky Blue | 0 |
| `variant_interpretation` | Variant Interpretation | `#4338ca` Indigo | 1 |
| `clinical_genomics_tools` | Clinical Genomics Tools | `#0f766e` Teal | 2 |
| `phenotype_genotype` | Phenotype–Genotype Correlation | `#7e22ce` Purple | 3 |
| `report_writing` | Report Writing | `#d97706` Amber | 4 |
| `mdt_workflow` | MDT & Clinical Workflow | `#0e7490` Cyan | 5 |
| `regulation_ethics` | Regulation & Ethics | `#be123c` Rose | 6 |
| `literature_evidence` | Literature & Evidence | `#15803d` Green | 7 |
| `lab_methods` | Genetics Laboratory Methods | `#c2410c` Orange | 8 |
| `finnish_genetics` | The Finnish Genetic Landscape | `#1e3a8a` Deep Blue | 9 |

**Colour palette** (available in admin panel):

| Hex | Name |
|-----|------|
| `#0369a1` | Sky Blue |
| `#4338ca` | Indigo |
| `#0f766e` | Teal |
| `#7e22ce` | Purple |
| `#d97706` | Amber |
| `#0e7490` | Cyan |
| `#be123c` | Rose |
| `#15803d` | Green |
| `#c2410c` | Orange |
| `#1e3a8a` | Deep Blue |
| `#374151` | Gray |
| `#be185d` | Pink |

---

## 11. Key Constants (routes.py)

| Constant | Value | Purpose |
|----------|-------|---------|
| `_URL_RE` | `^https?://` (case-insensitive) | Link URL validation |
| `_MAX_CONTENT_BYTES` | `512000` (500 KB) | Article content size limit |
| `_KNOWHOW_SORT_COOKIE` | `'knowhow_sort'` | Cookie name for sort preference |
| `_VALID_SORTS` | `{'position', 'label_asc', 'label_desc', 'most_content', 'recently_updated'}` | Whitelist for sort parameter |
| `_SEARCH_RESULT_LIMIT` | `50` | Max results per type in search |
| `_SNIPPET_RADIUS` | `120` | Chars either side of match in snippet |
