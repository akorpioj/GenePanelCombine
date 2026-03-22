"""
Top-level Flask-RESTX API object.

Mounted at /api/v1 — Swagger UI is available at /api/v1/docs
"""

from flask_restx import Api

authorizations = {
    'session': {
        'type': 'apiKey',
        'in': 'cookie',
        'name': 'session',
        'description': 'Standard Flask session cookie (login via the web UI first)',
    }
}

api = Api(
    title='PanelMerge API',
    version='1.0',
    description=(
        'REST API for PanelMerge — gene panel management and literature search. '
        'All endpoints require an active session (log in via the web UI).'
    ),
    doc='/docs',               # Swagger UI at /api/v1/docs
    authorizations=authorizations,
    security='session',
    prefix='/api/v1',
)
