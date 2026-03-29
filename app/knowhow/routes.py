"""Routes for the Knowhow blueprint"""

import re
from functools import wraps
import nh3
from markupsafe import escape, Markup
from flask import render_template, request, flash, redirect, url_for, abort, make_response, jsonify
from flask_login import login_required, current_user
from . import knowhow_bp
from ..audit_service import AuditService
from ..models import db, KnowhowLink, KnowhowArticle, KnowhowCategory, KnowhowSubcategory, KnowhowBookmark, UserRole

# ── Constants ──────────────────────────────────────────────────────────────────

_URL_RE = re.compile(r'^https?://', re.IGNORECASE)
_MAX_CONTENT_BYTES = 500 * 1024

# ── HTML sanitization (stored XSS protection) ─────────────────────────────────
# Allowlist covers all tags and attributes produced by Quill 1.3.7.
_QUILL_TAGS = {
    "p", "h1", "h2", "h3", "h4",
    "strong", "em", "u", "s",
    "a", "code", "pre", "blockquote",
    "ul", "ol", "li", "br", "hr", "span", "img",
}
# Per-tag attribute allowlist; class+style needed for Quill's alignment/indent helpers.
_BASE_ATTRS = {"class", "style"}
_QUILL_ATTRS: dict[str, set[str]] = {tag: _BASE_ATTRS for tag in _QUILL_TAGS}
_QUILL_ATTRS["a"]   = _BASE_ATTRS | {"href", "target"}
_QUILL_ATTRS["img"] = _BASE_ATTRS | {"src", "alt", "width", "height"}


def _sanitize_content(html: str) -> str:
    """Strip non-allowlisted tags/attributes from Quill HTML before persisting."""
    return nh3.clean(
        html,
        tags=_QUILL_TAGS,
        attributes=_QUILL_ATTRS,
        link_rel="noopener noreferrer",
        strip_comments=True,
    )

# Predefined colour palette: (hex, display_name)
PALETTE = [
    ('#0369a1', 'Sky Blue'),
    ('#4338ca', 'Indigo'),
    ('#0f766e', 'Teal'),
    ('#7e22ce', 'Purple'),
    ('#d97706', 'Amber'),
    ('#0e7490', 'Cyan'),
    ('#be123c', 'Rose'),
    ('#15803d', 'Green'),
    ('#c2410c', 'Orange'),
    ('#1e3a8a', 'Deep Blue'),
    ('#374151', 'Gray'),
    ('#be185d', 'Pink'),
]
_PALETTE_HEX = {h for h, _ in PALETTE}

# Seeded on first use if the categories table is empty
_DEFAULT_CATEGORIES = [
    {'slug': 'gene_panels',            'label': 'Gene Panels',                        'color': '#0369a1', 'position': 0},
    {'slug': 'variant_interpretation', 'label': 'Variant Interpretation',             'color': '#4338ca', 'position': 1},
    {'slug': 'clinical_genomics_tools','label': 'Clinical Genomics Tools',            'color': '#0f766e', 'position': 2},
    {'slug': 'phenotype_genotype',     'label': 'Phenotype–Genotype Correlation',     'color': '#7e22ce', 'position': 3},
    {'slug': 'report_writing',         'label': 'Report Writing',                     'color': '#d97706', 'position': 4},
    {'slug': 'mdt_workflow',           'label': 'MDT & Clinical Workflow',            'color': '#0e7490', 'position': 5},
    {'slug': 'regulation_ethics',      'label': 'Regulation & Ethics',                'color': '#be123c', 'position': 6},
    {'slug': 'literature_evidence',    'label': 'Literature & Evidence',              'color': '#15803d', 'position': 7},
    {'slug': 'lab_methods',            'label': 'Genetics Laboratory Methods',        'color': '#c2410c', 'position': 8},
    {'slug': 'finnish_genetics',       'label': 'The Finnish Genetic Landscape',      'color': '#1e3a8a', 'position': 9},
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated


def _seed_categories():
    """Seed the 10 default categories on first use (idempotent)."""
    if KnowhowCategory.query.count() == 0:
        for data in _DEFAULT_CATEGORIES:
            db.session.add(KnowhowCategory(**data))
        db.session.commit()


def _get_categories():
    """Return all categories ordered by position, seeding defaults if necessary."""
    _seed_categories()
    return KnowhowCategory.query.order_by(
        KnowhowCategory.position.asc(), KnowhowCategory.id.asc()
    ).all()


def _subcategories_json(categories):
    """Flat JSON-serialisable list of all subcategories with their category slug."""
    return [
        {'id': sub.id, 'label': sub.label, 'category_slug': cat.slug}
        for cat in categories
        for sub in cat.subcategories
    ]


def _validate_subcategory(sub_id_raw, category):
    """Return (subcategory_id_or_None, error_msg_or_None)."""
    if not sub_id_raw:
        return None, None
    try:
        sub_id = int(sub_id_raw)
    except ValueError:
        return None, 'Invalid subcategory.'
    sub = KnowhowSubcategory.query.get(sub_id)
    if not sub or sub.category_id != category.id:
        return None, 'Invalid subcategory.'
    return sub_id, None


# ── Index ──────────────────────────────────────────────────────────────────────

_KNOWHOW_SORT_COOKIE = 'knowhow_sort'
_VALID_SORTS = {'position', 'label_asc', 'label_desc', 'most_content', 'recently_updated'}
_SEARCH_RESULT_LIMIT = 50
_SNIPPET_RADIUS = 120  # plain-text chars either side of the match


# ── Search helpers ─────────────────────────────────────────────────────────────

def _safe_like(q: str) -> str:
    """Escape SQL LIKE wildcards so user input is treated as a literal string."""
    return q.replace('\\', '\\\\').replace('%', r'\%').replace('_', r'\_')


def _strip_html(html: str) -> str:
    """Remove HTML tags and collapse whitespace to produce plain text."""
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html)).strip()


def _highlight(text: str, query: str) -> Markup:
    """HTML-escape *text* then wrap each occurrence of *query* in a <mark> tag."""
    escaped = str(escape(text))
    marked = re.sub(
        r'(?i)(' + re.escape(query) + r')',
        r'<mark class="bg-yellow-200 rounded px-0.5">\1</mark>',
        escaped,
    )
    return Markup(marked)


def _snippet(html: str, query: str) -> Markup:
    """Extract a short highlighted plain-text excerpt from HTML article content."""
    plain = _strip_html(html)
    idx = plain.lower().find(query.lower())
    if idx == -1:
        excerpt = plain[:_SNIPPET_RADIUS * 2]
        prefix = suffix = ''
    else:
        start = max(0, idx - _SNIPPET_RADIUS)
        end = min(len(plain), idx + len(query) + _SNIPPET_RADIUS)
        prefix = '\u2026' if start > 0 else ''
        suffix = '\u2026' if end < len(plain) else ''
        excerpt = prefix + plain[start:end] + suffix
    return _highlight(excerpt, query)


@knowhow_bp.route('/', methods=['GET'])
@login_required
def index():
    """KnowHow landing page"""
    AuditService.log_view('page', 'knowhow_index', 'Viewed Knowhow index page')

    # Prefer explicit query param; fall back to saved cookie; then default
    sort = request.args.get('sort')
    if sort not in _VALID_SORTS:
        sort = request.cookies.get(_KNOWHOW_SORT_COOKIE, 'position')
    if sort not in _VALID_SORTS:
        sort = 'position'

    categories = _get_categories()  # always position-sorted initially

    all_articles = KnowhowArticle.query.order_by(KnowhowArticle.created_at.desc()).all()
    all_links    = KnowhowLink.query.order_by(KnowhowLink.created_at.asc()).all()

    # Apply category sort
    if sort == 'label_asc':
        categories = sorted(categories, key=lambda c: c.label.lower())
    elif sort == 'label_desc':
        categories = sorted(categories, key=lambda c: c.label.lower(), reverse=True)
    elif sort == 'most_content':
        from collections import Counter
        counts = Counter(
            [a.category for a in all_articles] + [lnk.category for lnk in all_links]
        )
        categories = sorted(categories, key=lambda c: counts.get(c.slug, 0), reverse=True)
    elif sort == 'recently_updated':
        import datetime
        latest: dict = {}
        for a in all_articles:
            t = a.updated_at or a.created_at
            if t and (a.category not in latest or t > latest[a.category]):
                latest[a.category] = t
        for lnk in all_links:
            t = lnk.created_at
            if t and (lnk.category not in latest or t > latest[lnk.category]):
                latest[lnk.category] = t
        epoch = datetime.datetime.min
        categories = sorted(categories, key=lambda c: latest.get(c.slug, epoch), reverse=True)
    # 'position': already sorted by _get_categories()

    # {category_slug: {None | subcategory_id: [item, ...]}}
    articles_map: dict = {}
    for a in all_articles:
        articles_map.setdefault(a.category, {}).setdefault(a.subcategory_id, []).append(a)

    links_map: dict = {}
    for lnk in all_links:
        links_map.setdefault(lnk.category, {}).setdefault(lnk.subcategory_id, []).append(lnk)

    resp = make_response(render_template(
        'knowhow/index.html',
        categories=categories,
        articles_map=articles_map,
        links_map=links_map,
        subcategories_json=_subcategories_json(categories),
        sort=sort,
    ))
    # Persist the chosen sort for future sessions (1 year, httponly)
    resp.set_cookie(_KNOWHOW_SORT_COOKIE, sort,
                    max_age=365 * 24 * 60 * 60, httponly=True, samesite='Lax')
    return resp


# ── Category detail ───────────────────────────────────────────────────────────

@knowhow_bp.route('/category/<slug>', methods=['GET'])
@login_required
def category(slug):
    """Category detail page — all content for one category."""
    cat = KnowhowCategory.query.filter_by(slug=slug).first_or_404()
    AuditService.log_view('knowhow_category', slug, f'Viewed KnowHow category: {cat.label}')

    articles = KnowhowArticle.query.filter_by(category=slug).order_by(KnowhowArticle.created_at.asc()).all()
    links    = KnowhowLink.query.filter_by(category=slug).order_by(KnowhowLink.created_at.asc()).all()

    articles_map: dict = {}
    for a in articles:
        articles_map.setdefault(a.subcategory_id, []).append(a)

    links_map: dict = {}
    for lnk in links:
        links_map.setdefault(lnk.subcategory_id, []).append(lnk)

    subcategories_json = [
        {'id': sub.id, 'label': sub.label, 'category_slug': cat.slug}
        for sub in cat.subcategories
    ]

    return render_template('knowhow/category.html',
                           category=cat,
                           articles_map=articles_map,
                           links_map=links_map,
                           subcategories_json=subcategories_json)


# ── Search ─────────────────────────────────────────────────────────────────────

@knowhow_bp.route('/search', methods=['GET'])
@login_required
def search():
    """Full-text search across KnowHow articles and links."""
    q = request.args.get('q', '').strip()

    article_results = []
    link_results = []

    if len(q) >= 2:
        pattern = f'%{_safe_like(q)}%'

        articles = (KnowhowArticle.query
                    .filter(db.or_(
                        KnowhowArticle.title.ilike(pattern),
                        KnowhowArticle.content.ilike(pattern),
                    ))
                    .order_by(KnowhowArticle.created_at.desc())
                    .limit(_SEARCH_RESULT_LIMIT)
                    .all())

        links = (KnowhowLink.query
                 .filter(db.or_(
                     KnowhowLink.description.ilike(pattern),
                     KnowhowLink.url.ilike(pattern),
                 ))
                 .order_by(KnowhowLink.created_at.desc())
                 .limit(_SEARCH_RESULT_LIMIT)
                 .all())

        categories = {c.slug: c for c in KnowhowCategory.query.all()}

        for a in articles:
            article_results.append({
                'article': a,
                'category': categories.get(a.category),
                'title_hl': _highlight(a.title, q),
                'snippet': _snippet(a.content, q),
            })

        for lnk in links:
            link_results.append({
                'link': lnk,
                'category': categories.get(lnk.category),
                'desc_hl': _highlight(lnk.description, q),
            })

        AuditService.log_view('knowhow_search', q[:256],
                              f'Searched KnowHow: {q[:256]!r}')

    return render_template('knowhow/search.html',
                           q=q,
                           article_results=article_results,
                           link_results=link_results)


# ── Links ──────────────────────────────────────────────────────────────────────

@knowhow_bp.route('/links', methods=['POST'])
@login_required
def add_link():
    cat_slug    = request.form.get('category', '').strip()
    url         = request.form.get('url', '').strip()
    description = request.form.get('description', '').strip()
    sub_id_raw  = request.form.get('subcategory_id', '').strip()

    category = KnowhowCategory.query.filter_by(slug=cat_slug).first()
    if not category:
        flash('Invalid category.', 'danger')
        return redirect(url_for('knowhow.index'))
    if not _URL_RE.match(url):
        flash('URL must start with http:// or https://', 'danger')
        return redirect(url_for('knowhow.index'))
    if len(url) > 2048:
        flash('URL is too long (max 2048 characters).', 'danger')
        return redirect(url_for('knowhow.index'))
    if len(description) < 3 or len(description) > 512:
        flash('Description must be between 3 and 512 characters.', 'danger')
        return redirect(url_for('knowhow.index'))

    subcategory_id, err = _validate_subcategory(sub_id_raw, category)
    if err:
        flash(err, 'danger')
        return redirect(url_for('knowhow.index'))

    db.session.add(KnowhowLink(
        category=cat_slug, url=url, description=description,
        user_id=current_user.id, subcategory_id=subcategory_id,
    ))
    db.session.commit()
    flash('Link added.', 'success')
    return redirect(url_for('knowhow.index') + f'#{cat_slug}')


@knowhow_bp.route('/links/<int:link_id>/delete', methods=['POST'])
@login_required
def delete_link(link_id):
    link = KnowhowLink.query.get_or_404(link_id)
    if link.user_id != current_user.id and current_user.role not in (UserRole.ADMIN, UserRole.EDITOR):
        abort(403)
    category = link.category
    db.session.delete(link)
    db.session.commit()
    flash('Link removed.', 'success')
    return redirect(url_for('knowhow.index') + f'#{category}')


# ── Articles ───────────────────────────────────────────────────────────────────

@knowhow_bp.route('/articles/new', methods=['GET'])
@login_required
def new_article():
    categories = _get_categories()
    return render_template('knowhow/article_editor.html',
                           article=None,
                           categories=categories,
                           subcategories_json=_subcategories_json(categories))


@knowhow_bp.route('/articles', methods=['POST'])
@login_required
def create_article():
    title      = request.form.get('title', '').strip()
    summary    = request.form.get('summary', '').strip() or None
    cat_slug   = request.form.get('category', '').strip()
    content    = request.form.get('content', '')
    sub_id_raw = request.form.get('subcategory_id', '').strip()

    categories = _get_categories()
    category   = KnowhowCategory.query.filter_by(slug=cat_slug).first()

    def _err(msg):
        flash(msg, 'danger')
        return render_template('knowhow/article_editor.html', article=None,
                               categories=categories,
                               subcategories_json=_subcategories_json(categories))

    if not title or len(title) > 256:
        return _err('Title is required (max 256 chars).')
    if summary and len(summary) > 512:
        return _err('Summary must be 512 characters or fewer.')
    if not category:
        return _err('Please select a valid category.')
    if len(content.encode('utf-8')) > _MAX_CONTENT_BYTES:
        return _err('Article content is too large (max 500 KB).')

    content = _sanitize_content(content)

    subcategory_id, err = _validate_subcategory(sub_id_raw, category)
    if err:
        return _err(err)

    article = KnowhowArticle(title=title, summary=summary, category=cat_slug, content=content,
                             user_id=current_user.id, subcategory_id=subcategory_id)
    db.session.add(article)
    db.session.commit()
    flash('Article published.', 'success')
    return redirect(url_for('knowhow.view_article', article_id=article.id))


@knowhow_bp.route('/articles/<int:article_id>', methods=['GET'])
@login_required
def view_article(article_id):
    article = KnowhowArticle.query.get_or_404(article_id)
    AuditService.log_view('knowhow_article', str(article_id),
                          f'Viewed KnowHow article: {article.title}')
    category    = KnowhowCategory.query.filter_by(slug=article.category).first()
    subcategory = (KnowhowSubcategory.query.get(article.subcategory_id)
                   if article.subcategory_id else None)
    bookmarked  = KnowhowBookmark.query.filter_by(
        user_id=current_user.id, article_id=article_id).first() is not None
    return render_template('knowhow/article_view.html',
                           article=article, category=category,
                           subcategory=subcategory, bookmarked=bookmarked)


@knowhow_bp.route('/articles/<int:article_id>/edit', methods=['GET'])
@login_required
def edit_article(article_id):
    article = KnowhowArticle.query.get_or_404(article_id)
    if article.user_id != current_user.id and current_user.role not in (UserRole.ADMIN, UserRole.EDITOR):
        abort(403)
    categories = _get_categories()
    return render_template('knowhow/article_editor.html',
                           article=article, categories=categories,
                           subcategories_json=_subcategories_json(categories))


@knowhow_bp.route('/articles/<int:article_id>/edit', methods=['POST'])
@login_required
def update_article(article_id):
    article = KnowhowArticle.query.get_or_404(article_id)
    if article.user_id != current_user.id and current_user.role not in (UserRole.ADMIN, UserRole.EDITOR):
        abort(403)

    title      = request.form.get('title', '').strip()
    summary    = request.form.get('summary', '').strip() or None
    cat_slug   = request.form.get('category', '').strip()
    content    = request.form.get('content', '')
    sub_id_raw = request.form.get('subcategory_id', '').strip()

    category = KnowhowCategory.query.filter_by(slug=cat_slug).first()

    if not title or len(title) > 256:
        flash('Title is required (max 256 chars).', 'danger')
        return redirect(url_for('knowhow.edit_article', article_id=article_id))
    if summary and len(summary) > 512:
        flash('Summary must be 512 characters or fewer.', 'danger')
        return redirect(url_for('knowhow.edit_article', article_id=article_id))
    if not category:
        flash('Please select a valid category.', 'danger')
        return redirect(url_for('knowhow.edit_article', article_id=article_id))
    if len(content.encode('utf-8')) > _MAX_CONTENT_BYTES:
        flash('Article content is too large (max 500 KB).', 'danger')
        return redirect(url_for('knowhow.edit_article', article_id=article_id))

    content = _sanitize_content(content)

    subcategory_id, err = _validate_subcategory(sub_id_raw, category)
    if err:
        flash(err, 'danger')
        return redirect(url_for('knowhow.edit_article', article_id=article_id))

    article.title          = title
    article.summary        = summary
    article.category       = cat_slug
    article.content        = content
    article.subcategory_id = subcategory_id
    db.session.commit()
    flash('Article updated.', 'success')
    return redirect(url_for('knowhow.view_article', article_id=article.id))


@knowhow_bp.route('/articles/<int:article_id>/bookmark', methods=['POST'])
@login_required
def toggle_bookmark(article_id):
    """Toggle a personal bookmark on a KnowHow article. Returns JSON."""
    article = KnowhowArticle.query.get_or_404(article_id)
    existing = KnowhowBookmark.query.filter_by(
        user_id=current_user.id, article_id=article_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'bookmarked': False})
    bookmark = KnowhowBookmark(user_id=current_user.id, article_id=article_id)
    db.session.add(bookmark)
    db.session.commit()
    AuditService.log_view('knowhow_bookmark', str(article_id),
                          f'Bookmarked KnowHow article: {article.title}')
    return jsonify({'bookmarked': True})


@knowhow_bp.route('/bookmarks', methods=['GET'])
@login_required
def bookmarks():
    """Personal reading list — all bookmarked articles for the current user."""
    rows = (KnowhowBookmark.query
            .filter_by(user_id=current_user.id)
            .order_by(KnowhowBookmark.created_at.desc())
            .all())
    articles = [b.article for b in rows]
    # Build a category lookup so we can show category labels
    slugs = {a.category for a in articles}
    categories = {c.slug: c for c in KnowhowCategory.query.filter(
        KnowhowCategory.slug.in_(slugs)).all()} if slugs else {}
    AuditService.log_view('knowhow_bookmarks', 'list', 'Viewed KnowHow reading list')
    return render_template('knowhow/bookmarks.html',
                           articles=articles, categories=categories)


@knowhow_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    article = KnowhowArticle.query.get_or_404(article_id)
    if article.user_id != current_user.id and current_user.role not in (UserRole.ADMIN, UserRole.EDITOR):
        abort(403)
    category = article.category
    db.session.delete(article)
    db.session.commit()
    flash('Article deleted.', 'success')
    return redirect(url_for('knowhow.index') + f'#{category}')


# ── Admin: Category & Subcategory management ───────────────────────────────────

@knowhow_bp.route('/admin', methods=['GET'])
@login_required
@_admin_required
def admin_categories():
    categories = _get_categories()
    return render_template('knowhow/admin_categories.html',
                           categories=categories, palette=PALETTE)


@knowhow_bp.route('/admin/categories', methods=['POST'])
@login_required
@_admin_required
def create_category():
    label       = request.form.get('label', '').strip()
    slug        = request.form.get('slug', '').strip().lower()
    color       = request.form.get('color', '#0369a1').strip()
    description = request.form.get('description', '').strip() or None

    if not label or len(label) > 128:
        flash('Label is required (max 128 chars).', 'danger')
        return redirect(url_for('knowhow.admin_categories'))
    if not re.match(r'^[a-z0-9_]{1,64}$', slug):
        flash('Slug: lowercase letters, digits and underscores only (max 64).', 'danger')
        return redirect(url_for('knowhow.admin_categories'))
    if KnowhowCategory.query.filter_by(slug=slug).first():
        flash(f'Slug "{slug}" already exists.', 'danger')
        return redirect(url_for('knowhow.admin_categories'))
    if color not in _PALETTE_HEX:
        flash('Invalid colour selection.', 'danger')
        return redirect(url_for('knowhow.admin_categories'))

    max_pos = (db.session.query(db.func.max(KnowhowCategory.position)).scalar() or -1)
    db.session.add(KnowhowCategory(label=label, slug=slug, color=color,
                                   description=description, position=max_pos + 1))
    db.session.commit()
    flash(f'Category "{label}" created.', 'success')
    return redirect(url_for('knowhow.admin_categories'))


@knowhow_bp.route('/admin/categories/<int:cat_id>/edit', methods=['POST'])
@login_required
@_admin_required
def update_category(cat_id):
    category    = KnowhowCategory.query.get_or_404(cat_id)
    label       = request.form.get('label', '').strip()
    color       = request.form.get('color', '').strip()
    description = request.form.get('description', '').strip() or None
    position    = request.form.get('position', '').strip()

    if not label or len(label) > 128:
        flash('Label is required (max 128 chars).', 'danger')
        return redirect(url_for('knowhow.admin_categories'))
    if color not in _PALETTE_HEX:
        flash('Invalid colour.', 'danger')
        return redirect(url_for('knowhow.admin_categories'))

    category.label       = label
    category.color       = color
    category.description = description
    if position.isdigit():
        category.position = int(position)
    db.session.commit()
    flash('Category updated.', 'success')
    return redirect(url_for('knowhow.admin_categories'))


@knowhow_bp.route('/admin/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
@_admin_required
def delete_category(cat_id):
    category = KnowhowCategory.query.get_or_404(cat_id)
    label = category.label
    db.session.delete(category)
    db.session.commit()
    flash(f'Category "{label}" deleted. Associated articles/links are hidden until reassigned.', 'warning')
    return redirect(url_for('knowhow.admin_categories'))


@knowhow_bp.route('/admin/categories/<int:cat_id>/subcategories', methods=['POST'])
@login_required
@_admin_required
def create_subcategory(cat_id):
    category = KnowhowCategory.query.get_or_404(cat_id)
    label = request.form.get('label', '').strip()
    if not label or len(label) > 128:
        flash('Subcategory label is required (max 128 chars).', 'danger')
        return redirect(url_for('knowhow.admin_categories'))
    max_pos = (db.session.query(db.func.max(KnowhowSubcategory.position))
               .filter(KnowhowSubcategory.category_id == cat_id).scalar() or -1)
    db.session.add(KnowhowSubcategory(category_id=cat_id, label=label, position=max_pos + 1))
    db.session.commit()
    flash(f'Subcategory "{label}" added to {category.label}.', 'success')
    return redirect(url_for('knowhow.admin_categories'))


@knowhow_bp.route('/admin/subcategories/<int:sub_id>/edit', methods=['POST'])
@login_required
@_admin_required
def update_subcategory(sub_id):
    sub   = KnowhowSubcategory.query.get_or_404(sub_id)
    label = request.form.get('label', '').strip()
    if not label or len(label) > 128:
        flash('Label is required (max 128 chars).', 'danger')
        return redirect(url_for('knowhow.admin_categories'))
    sub.label = label
    db.session.commit()
    flash('Subcategory updated.', 'success')
    return redirect(url_for('knowhow.admin_categories'))


@knowhow_bp.route('/admin/subcategories/<int:sub_id>/delete', methods=['POST'])
@login_required
@_admin_required
def delete_subcategory(sub_id):
    sub   = KnowhowSubcategory.query.get_or_404(sub_id)
    label = sub.label
    db.session.delete(sub)
    db.session.commit()
    flash(f'Subcategory "{label}" deleted. Associated articles/links reverted to general category.', 'warning')
    return redirect(url_for('knowhow.admin_categories'))
