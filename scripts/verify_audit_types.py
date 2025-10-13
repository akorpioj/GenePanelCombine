"""Verify export template audit types were added to database"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    result = db.session.execute(text(
        """SELECT e::text 
           FROM unnest(enum_range(NULL::auditactiontype)) AS e
           WHERE e::text LIKE '%EXPORT_TEMPLATE%';"""
    ))
    values = [row[0] for row in result]
    expected = ['PANEL_EXPORT_TEMPLATE_CREATE', 'PANEL_EXPORT_TEMPLATE_UPDATE', 'PANEL_EXPORT_TEMPLATE_DELETE']
    
    print('\n=== Export Template Audit Types Verification ===\n')
    print(f'Found enum values: {values}\n')
    
    if all(v in values for v in expected):
        print('✅ All export template audit types added successfully')
        for v in expected:
            print(f'   ✓ {v}')
    else:
        print('❌ Some audit types missing')
        print(f'   Found: {values}')
        print(f'   Expected: {expected}')
    
    print('\n')
