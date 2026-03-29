# Summary of Changes: v1.5.6

## KnowHow Draft / Publish Workflow (Feature 5)

### Step 1 — `is_draft` DB column
- Added `is_draft = Boolean(nullable=False, default=False, server_default='false')` to `KnowhowArticle`
- Alembic migration generated and applied; all existing articles default to `is_draft=False` (published)

### Step 2 — Article editor: "Save as Draft" button
- Single submit button in `article_editor.html` replaced with two buttons: **Save as draft** (`action=draft`) and **Publish article** / **Publish changes** (`action=publish`)
- `create_article()` and `update_article()` routes read `action = request.form.get('action', 'publish')` and set `is_draft` accordingly
- Flash messages distinguish between `'Draft saved.'` and `'Article published.'` / `'Article updated.'`

### Step 3 — Draft filter on list routes
- `_draft_filter()` helper added to `routes.py`: ADMIN/EDITOR see all articles; USER role sees published articles plus their own drafts
- Applied to `index()`, `category()`, `search()`, and `tag_articles()` routes

### Step 4 — DRAFT badges in templates
- `article_view.html`: red `DRAFT` pill badge added next to the `<h1>` title; amber "not yet public" warning banner shown above the header — both conditional on `article.is_draft`
- `index.html` and `category.html`: small red `DRAFT` label added after the article title on article cards, conditional on `article.is_draft`

### Step 5 — "My Drafts" shortcut page
- New `GET /knowhow/drafts` route: USER sees their own drafts; EDITOR/ADMIN see all users' drafts; ordered by `updated_at DESC`
- New template `app/templates/knowhow/drafts.html`: article list with DRAFT badge and Edit button per row; empty state
- `index()` queries `user_draft_count` and passes it to `index.html`; a conditional "My Drafts" link (red, with count badge) appears in the index header only when `user_draft_count > 0`

### Tests
- 57 unit tests across 5 test files (`test_knowhow_draft_step1–5.py`), all passing


