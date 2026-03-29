# Summary of Changes: v1.5.5

## Fix: nh3 panic when saving KnowHow articles (29/03/2026)

Saving or updating a KnowHow article crashed the server with a Rust `PanicException` from the `ammonia` library (backend used by `nh3`):

```
assertion failed: self.tag_attributes.get("a").and_then(|a| a.get("rel")).is_none()
```

**Root cause:** `ammonia` owns the `rel` attribute on `<a>` elements — it injects `rel="noopener noreferrer"` itself when the `link_rel` parameter is set. Its internal assertion fires if `rel` also appears in `tag_attributes`. The `_QUILL_ATTRS["a"]` allowlist included `"rel"`, which triggered the conflict.

**Fix:** Removed `"rel"` from `_QUILL_ATTRS["a"]`. The `link_rel="noopener noreferrer"` argument to `nh3.clean()` continues to enforce the secure `rel` value on all sanitized links.

**Files changed:** `app/knowhow/routes.py`

---

## Feature: KnowHow category description display (29/03/2026)

Completed Feature 9 from `KNOWHOW_FUTURE_FEATURES.md`. `KnowhowCategory` already has a `description` field editable via the admin panel, but it was never shown to regular users on the category detail page.

**User-facing behaviour:**
- When a category has a description set, it now appears immediately below the coloured header bar on the category detail page (`/knowhow/category/<slug>`)
- Rendered as a light grey strip (`bg-gray-50`) with small italic text and a bottom border
- Categories without a description are unaffected — the block is entirely hidden

**Implementation details:**
- Single `{% if category.description %}…{% endif %}` block added to `category.html` after the closing `</div>` of the coloured header
- No route, model, or DB changes required

**Files changed:** `app/templates/knowhow/category.html`

---

## Feature: KnowHow bookmarks / reading list (29/03/2026)

Implemented Feature 3 from `KNOWHOW_FUTURE_FEATURES.md`. Users can now bookmark any KnowHow article to a personal reading list accessible from the KnowHow index.

**User-facing behaviour:**
- Every article view page shows a **Save / Saved** bookmark button (hollow/filled star) in the header alongside the Edit button; clicking toggles the bookmark without a page reload
- **My Reading List** link (amber, bookmark icon) added to the KnowHow index header
- Reading list page (`/knowhow/bookmarks`) shows all bookmarked articles newest-first with category colour badges, optional summaries, and an inline remove button per row
- Removing a bookmark from the reading list page removes the row from the DOM immediately; empty-state message appears when the list becomes empty
- Bookmarks are per-user; users cannot see each other's reading lists

**Implementation details:**
- `KnowhowBookmark(id, user_id FK CASCADE, article_id FK CASCADE, created_at)` added to `app/models.py`; `UniqueConstraint` on `(user_id, article_id)` prevents duplicates
- Alembic migration `0bd52c3d4e36_add_knowhow_bookmarks.py` generated and applied via `flask db upgrade`
- `POST /knowhow/articles/<id>/bookmark` — toggle route returning `{bookmarked: true/false}` JSON; bookmark additions are audit-logged
- `GET /knowhow/bookmarks` — reading list route; passes articles and a category slug→object dict for badge rendering
- `view_article()` extended to pass `bookmarked` bool to the template
- Client-side toggle uses `fetch()` with `credentials: 'same-origin'`; button class, icon fill, label text, and `title` attribute all updated in-place
- New template: `app/templates/knowhow/bookmarks.html`

**Files changed:** `app/models.py`, `app/knowhow/routes.py`, `app/templates/knowhow/article_view.html`, `app/templates/knowhow/index.html`, `app/templates/knowhow/bookmarks.html` *(new)*, `migrations/versions/0bd52c3d4e36_add_knowhow_bookmarks.py` *(new)*

---
