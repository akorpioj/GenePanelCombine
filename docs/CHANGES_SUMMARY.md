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

