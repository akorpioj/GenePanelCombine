"""
SSRF-safe Open Graph data fetcher for Feature 11 — Link Preview Cards.

Public API
----------
_fetch_og_data(url: str) -> dict
    Fetch Open Graph metadata from *url* and return a dict with the keys
    ``og_title``, ``og_description``, and ``og_image_url``.  Any value may
    be None.  The function never raises — it silently returns all-None on
    any error (bad scheme, SSRF-blocked IP, network failure, parse error).
"""
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

_NULL_RESULT = {'og_title': None, 'og_description': None, 'og_image_url': None}

_USER_AGENT  = 'KnowHow-Preview/1.0'
_TIMEOUT     = 5  # seconds


# ── IP safety check ───────────────────────────────────────────────────────────

def _is_safe_ip(ip_str: str) -> bool:
    """Return True only if *ip_str* is a public, routable address."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return not (addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_multicast or addr.is_reserved or addr.is_unspecified)


# ── Minimal HTML parser ───────────────────────────────────────────────────────

class _OGParser(HTMLParser):
    """Extract og:title, og:description, og:image and <title> from HTML."""

    def __init__(self):
        super().__init__()
        self.og_title       = None
        self.og_description = None
        self.og_image       = None
        self._in_title      = False
        self._title_text    = []

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self._in_title = True
            return
        if tag != 'meta':
            return
        attr_dict = dict(attrs)
        prop    = attr_dict.get('property', '')
        content = attr_dict.get('content', '').strip()
        if prop == 'og:title':
            self.og_title = content or None
        elif prop == 'og:description':
            self.og_description = content or None
        elif prop == 'og:image':
            self.og_image = content or None

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self._title_text.append(data)

    @property
    def title_element(self):
        text = ''.join(self._title_text).strip()
        return text or None


# ── Public function ───────────────────────────────────────────────────────────

def _fetch_og_data(url: str) -> dict:
    """
    Fetch OG metadata from *url* with SSRF protection.

    Rules:
    - Only ``https://`` scheme is accepted.
    - The hostname is resolved with ``socket.getaddrinfo`` before opening
      any connection; private / loopback / link-local IPs are rejected.
    - Fetched with ``httpx.get`` (timeout 5 s, no redirects).
    - ``og:title`` falls back to ``<title>`` when absent.
    - Returns all-None silently on any error.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme != 'https':
            return dict(_NULL_RESULT)

        hostname = parsed.hostname
        if not hostname:
            return dict(_NULL_RESULT)

        # Resolve *before* connecting — DNS-rebinding protection.
        try:
            addr_infos = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            return dict(_NULL_RESULT)

        for info in addr_infos:
            ip = info[4][0]
            if not _is_safe_ip(ip):
                return dict(_NULL_RESULT)

        response = httpx.get(
            url,
            timeout=_TIMEOUT,
            follow_redirects=False,
            headers={'User-Agent': _USER_AGENT},
        )

        parser = _OGParser()
        parser.feed(response.text)

        og_title = parser.og_title or parser.title_element

        return {
            'og_title':       og_title,
            'og_description': parser.og_description,
            'og_image_url':   parser.og_image,
        }

    except Exception:
        return dict(_NULL_RESULT)
