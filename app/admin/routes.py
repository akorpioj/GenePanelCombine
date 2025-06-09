from flask import render_template, redirect, url_for, flash, request

from app.main.routes import get_all_panels_from_api
from . import admin_bp # Import the Blueprint object defined in __init__.py

from ..models import User
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
    cache_info = {
        'last_refresh': getattr(get_all_panels_from_api, 'cache_time', None),
        'next_refresh': getattr(get_all_panels_from_api, 'next_refresh', None),
        'panel_count': len(getattr(get_all_panels_from_api, 'cache', [])) if getattr(get_all_panels_from_api, 'cache', None) else 0
    }
    return render_template('admin.html', cache_info=cache_info)
