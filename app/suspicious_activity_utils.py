"""
Helper functions for suspicious activity detection
Includes IP geolocation and pattern analysis
"""

import requests
from flask import current_app


def get_ip_geolocation(ip_address):
    """
    Get geolocation data for an IP address using ip-api.com (free, no key required)
    
    Args:
        ip_address: IP address to lookup
        
    Returns:
        dict: {'country': str, 'city': str} or {'country': None, 'city': None} if failed
    """
    # Skip for localhost/private IPs
    if ip_address in ['127.0.0.1', 'localhost', '::1'] or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
        return {'country': 'Local', 'city': 'Local'}
    
    try:
        # Use free ip-api.com service (rate limited to 45 requests/minute)
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=2  # Quick timeout to not slow down requests
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country'),
                    'city': data.get('city')
                }
    except Exception as e:
        current_app.logger.warning(f"Failed to get geolocation for {ip_address}: {e}")
    
    return {'country': None, 'city': None}


def get_client_ip(request):
    """
    Get the real client IP address from request, considering proxies
    
    Args:
        request: Flask request object
        
    Returns:
        str: Client IP address
    """
    # Check for proxy headers (in order of preference)
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs, take the first one
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr or '127.0.0.1'
