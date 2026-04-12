from flask import render_template
from flask_login import login_required

from . import genie_bp


@genie_bp.route('/')
@login_required
def index():
    """Genie home page."""
    return render_template('genie/index.html')
