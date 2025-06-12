from flask import render_template, redirect, url_for, flash, request

from app.main.routes import get_all_panels_from_api
from . import admin_bp # Import the Blueprint object defined in __init__.py

from ..models import User, db
from flask_login import current_user, login_user, logout_user, login_required
from ..extensions import limiter

# Admin routes
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@admin_bp.route('/admin')
@login_required
@limiter.limit("60 per hour")
def dashboard():
    from ..models import Visit, PanelDownload
    from datetime import datetime, timedelta
    from sqlalchemy import func, desc

    # Get cache info
    cache_info = {
        'last_refresh': getattr(get_all_panels_from_api, 'cache_time', None),
        'next_refresh': getattr(get_all_panels_from_api, 'next_refresh', None),
        'panel_count': len(getattr(get_all_panels_from_api, 'cache', [])) if getattr(get_all_panels_from_api, 'cache', None) else 0
    }

    # Get visit statistics
    today = datetime.utcnow().date()
    last_week = today - timedelta(days=7)
    
    visits_today = Visit.query.filter(func.date(Visit.visit_date) == today).count()
    visits_last_week = Visit.query.filter(Visit.visit_date >= last_week).count()
    unique_visitors = Visit.query.with_entities(Visit.ip_address).distinct().count()

    # Get download statistics
    downloads_today = PanelDownload.query.filter(func.date(PanelDownload.download_date) == today).count()
    downloads_last_week = PanelDownload.query.filter(PanelDownload.download_date >= last_week).count()
    
    # Get most downloaded panels
    recent_downloads = PanelDownload.query\
        .filter(PanelDownload.download_date >= last_week)\
        .order_by(desc(PanelDownload.download_date))\
        .limit(10)\
        .all()

    stats = {
        'visits_today': visits_today,
        'visits_last_week': visits_last_week,
        'unique_visitors': unique_visitors,
        'downloads_today': downloads_today,
        'downloads_last_week': downloads_last_week,
        'recent_downloads': recent_downloads
    }

    return render_template('admin.html', cache_info=cache_info, stats=stats)

@admin_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        flash('All password fields are required', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Update the password
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password successfully updated', 'success')
    return redirect(url_for('admin.dashboard'))
