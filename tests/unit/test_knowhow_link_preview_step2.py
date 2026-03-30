"""
Tests for Feature 11 Step 2 — SSRF-safe OG data fetcher.

All tests call ``_fetch_og_data(url)`` from ``app.knowhow.og_utils`` directly
(no HTTP test client, no database).  Network I/O is fully mocked:

  - ``socket.getaddrinfo`` is patched to control the resolved IP.
  - ``httpx.get`` is patched to return a configurable fake response.

These tests will fail to *collect* (ModuleNotFoundError) until Step 2 is
implemented — that is the expected red state.

Test plan
─────────
  Scheme validation
    - http:// URL → rejected, all-None returned
    - ftp:// URL → rejected
    - file:// URL → rejected
    - data: URL → rejected
    - URL with no scheme → rejected
    - https:// URL → accepted and proceeds to DNS check

  SSRF — blocked IPs (DNS resolves to a private address)
    - Loopback IPv4 127.0.0.1 → all-None
    - Loopback IPv6 ::1 → all-None
    - Private 10.0.0.1 → all-None
    - Private 172.16.0.1 → all-None
    - Private 192.168.1.1 → all-None
    - Link-local IPv4 169.254.1.1 → all-None
    - Link-local IPv6 fe80::1 → all-None

  SSRF — allowed IPs (DNS resolves to a public address)
    - Public IP 93.184.216.34 → fetch is attempted

  OG tag extraction (public IP + mocked HTML response)
    - og:title is extracted
    - og:description is extracted
    - og:image is extracted
    - All three extracted together
    - og:title absent → falls back to <title> element
    - og:title absent and <title> absent → og_title is None
    - og:description absent → og_description is None
    - og:image absent → og_image_url is None
    - og:title with surrounding whitespace is stripped
    - og:description with surrounding whitespace is stripped

  Return shape
    - Result always has exactly the keys og_title, og_description, og_image_url
    - Keys are present even when scheme is rejected
    - Keys are present when SSRF is blocked
    - Keys are present when a network error occurs

  Error resilience (all return all-None silently)
    - httpx.TimeoutException → all-None
    - httpx.ConnectError → all-None
    - httpx.RequestError → all-None
    - DNS failure (socket.gaierror) → all-None
    - Non-200 HTTP status with no OG tags → all-None
"""
import socket
import ipaddress
import pytest
from unittest.mock import patch, MagicMock

from app.knowhow.og_utils import _fetch_og_data


# ── HTML fixtures ─────────────────────────────────────────────────────────────

_FULL_OG_HTML = """
<html><head>
  <meta property="og:title" content="OG Page Title"/>
  <meta property="og:description" content="OG page description."/>
  <meta property="og:image" content="https://example.com/thumb.png"/>
</head><body>Body text.</body></html>
"""

_TITLE_FALLBACK_HTML = """
<html><head>
  <title>Plain Title</title>
</head><body>Content.</body></html>
"""

_NO_META_HTML = """
<html><head></head><body>Minimal page.</body></html>
"""

_WHITESPACE_OG_HTML = """
<html><head>
  <meta property="og:title" content="  Padded Title  "/>
  <meta property="og:description" content="  Padded desc.  "/>
</head></html>
"""

_PARTIAL_OG_HTML = """
<html><head>
  <meta property="og:title" content="Title Only"/>
</head></html>
"""


# ── Mock helpers ──────────────────────────────────────────────────────────────

def _fake_response(html=_FULL_OG_HTML, status_code=200):
    """Return a MagicMock that mimics an httpx.Response."""
    resp = MagicMock()
    resp.text = html
    resp.status_code = status_code
    return resp


def _dns_returning(ip_str):
    """Return a getaddrinfo side_effect that always resolves to *ip_str*."""
    def _impl(host, *args, **kwargs):
        return [(None, None, None, None, (ip_str, 0))]
    return _impl


# Public IP used whenever we want the fetch to proceed past the SSRF check.
_PUBLIC_IP   = '93.184.216.34'    # example.com
_PUBLIC_DNS  = _dns_returning(_PUBLIC_IP)


# ── Scheme validation ─────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSchemeValidation:
    """Non-https schemes must be rejected before any DNS or network call."""

    def test_http_scheme_rejected(self):
        result = _fetch_og_data('http://example.com/page')
        assert result == {'og_title': None, 'og_description': None, 'og_image_url': None}

    def test_ftp_scheme_rejected(self):
        result = _fetch_og_data('ftp://example.com/file.txt')
        assert result == {'og_title': None, 'og_description': None, 'og_image_url': None}

    def test_file_scheme_rejected(self):
        result = _fetch_og_data('file:///etc/passwd')
        assert result == {'og_title': None, 'og_description': None, 'og_image_url': None}

    def test_data_scheme_rejected(self):
        result = _fetch_og_data('data:text/html,<h1>hi</h1>')
        assert result == {'og_title': None, 'og_description': None, 'og_image_url': None}

    def test_no_scheme_rejected(self):
        result = _fetch_og_data('example.com/page')
        assert result == {'og_title': None, 'og_description': None, 'og_image_url': None}

    @patch('app.knowhow.og_utils.socket.getaddrinfo', side_effect=_PUBLIC_DNS)
    @patch('app.knowhow.og_utils.httpx.get', return_value=_fake_response(_NO_META_HTML))
    def test_https_scheme_accepted(self, mock_get, mock_dns):
        """https:// must pass the scheme check and reach the network layer."""
        _fetch_og_data('https://example.com/page')
        mock_dns.assert_called_once()
        mock_get.assert_called_once()


# ── SSRF — blocked IPs ────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSsrfBlockedIPs:
    """Private / loopback / link-local IPs must be blocked; no HTTP fetch made."""

    def _assert_blocked(self, ip_str):
        with patch('app.knowhow.og_utils.socket.getaddrinfo',
                   side_effect=_dns_returning(ip_str)) as mock_dns, \
             patch('app.knowhow.og_utils.httpx.get') as mock_get:
            result = _fetch_og_data('https://target.internal/')
        assert result == {'og_title': None, 'og_description': None, 'og_image_url': None}
        mock_get.assert_not_called()

    def test_loopback_ipv4_blocked(self):
        self._assert_blocked('127.0.0.1')

    def test_loopback_ipv6_blocked(self):
        self._assert_blocked('::1')

    def test_private_10_blocked(self):
        self._assert_blocked('10.0.0.1')

    def test_private_172_16_blocked(self):
        self._assert_blocked('172.16.0.1')

    def test_private_192_168_blocked(self):
        self._assert_blocked('192.168.1.1')

    def test_link_local_ipv4_blocked(self):
        self._assert_blocked('169.254.1.1')

    def test_link_local_ipv6_blocked(self):
        self._assert_blocked('fe80::1')


# ── SSRF — allowed IPs ────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSsrfAllowedIPs:
    """A public IP must pass the SSRF check and attempt the HTTP fetch."""

    @patch('app.knowhow.og_utils.socket.getaddrinfo', side_effect=_PUBLIC_DNS)
    @patch('app.knowhow.og_utils.httpx.get', return_value=_fake_response(_NO_META_HTML))
    def test_public_ip_allows_fetch(self, mock_get, mock_dns):
        _fetch_og_data('https://example.com/page')
        mock_get.assert_called_once()


# ── OG tag extraction ─────────────────────────────────────────────────────────

@pytest.mark.unit
class TestOgExtraction:
    """OG meta tags should be extracted from the response HTML."""

    def _call(self, html):
        with patch('app.knowhow.og_utils.socket.getaddrinfo',
                   side_effect=_PUBLIC_DNS), \
             patch('app.knowhow.og_utils.httpx.get',
                   return_value=_fake_response(html)):
            return _fetch_og_data('https://example.com/page')

    def test_og_title_extracted(self):
        result = self._call(_FULL_OG_HTML)
        assert result['og_title'] == 'OG Page Title'

    def test_og_description_extracted(self):
        result = self._call(_FULL_OG_HTML)
        assert result['og_description'] == 'OG page description.'

    def test_og_image_url_extracted(self):
        result = self._call(_FULL_OG_HTML)
        assert result['og_image_url'] == 'https://example.com/thumb.png'

    def test_all_three_fields_extracted_together(self):
        result = self._call(_FULL_OG_HTML)
        assert result['og_title']       == 'OG Page Title'
        assert result['og_description'] == 'OG page description.'
        assert result['og_image_url']   == 'https://example.com/thumb.png'

    def test_og_title_absent_falls_back_to_title_element(self):
        result = self._call(_TITLE_FALLBACK_HTML)
        assert result['og_title'] == 'Plain Title'

    def test_og_title_absent_and_no_title_element_gives_none(self):
        result = self._call(_NO_META_HTML)
        assert result['og_title'] is None

    def test_og_description_absent_gives_none(self):
        result = self._call(_PARTIAL_OG_HTML)
        assert result['og_description'] is None

    def test_og_image_absent_gives_none(self):
        result = self._call(_PARTIAL_OG_HTML)
        assert result['og_image_url'] is None

    def test_og_title_whitespace_stripped(self):
        result = self._call(_WHITESPACE_OG_HTML)
        assert result['og_title'] == 'Padded Title'

    def test_og_description_whitespace_stripped(self):
        result = self._call(_WHITESPACE_OG_HTML)
        assert result['og_description'] == 'Padded desc.'


# ── Return shape ──────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestReturnShape:
    """_fetch_og_data must always return a dict with exactly the three OG keys."""

    _EXPECTED_KEYS = {'og_title', 'og_description', 'og_image_url'}

    def test_return_shape_on_scheme_rejection(self):
        result = _fetch_og_data('http://example.com/')
        assert set(result.keys()) == self._EXPECTED_KEYS

    def test_return_shape_on_ssrf_block(self):
        with patch('app.knowhow.og_utils.socket.getaddrinfo',
                   side_effect=_dns_returning('192.168.0.1')):
            result = _fetch_og_data('https://internal.example.com/')
        assert set(result.keys()) == self._EXPECTED_KEYS

    @patch('app.knowhow.og_utils.socket.getaddrinfo', side_effect=_PUBLIC_DNS)
    @patch('app.knowhow.og_utils.httpx.get', return_value=_fake_response(_FULL_OG_HTML))
    def test_return_shape_on_successful_fetch(self, mock_get, mock_dns):
        result = _fetch_og_data('https://example.com/')
        assert set(result.keys()) == self._EXPECTED_KEYS

    def test_return_shape_on_network_error(self):
        import httpx
        with patch('app.knowhow.og_utils.socket.getaddrinfo',
                   side_effect=_PUBLIC_DNS), \
             patch('app.knowhow.og_utils.httpx.get',
                   side_effect=httpx.RequestError('err')):
            result = _fetch_og_data('https://example.com/')
        assert set(result.keys()) == self._EXPECTED_KEYS


# ── Error resilience ──────────────────────────────────────────────────────────

@pytest.mark.unit
class TestErrorResilience:
    """Any exception during fetch must be swallowed; all-None is returned."""

    _NULL = {'og_title': None, 'og_description': None, 'og_image_url': None}

    def _call_with_fetch_error(self, exc):
        with patch('app.knowhow.og_utils.socket.getaddrinfo',
                   side_effect=_PUBLIC_DNS), \
             patch('app.knowhow.og_utils.httpx.get', side_effect=exc):
            return _fetch_og_data('https://example.com/page')

    def test_timeout_returns_all_none(self):
        import httpx
        result = self._call_with_fetch_error(httpx.TimeoutException('timeout'))
        assert result == self._NULL

    def test_connect_error_returns_all_none(self):
        import httpx
        result = self._call_with_fetch_error(httpx.ConnectError('refused'))
        assert result == self._NULL

    def test_request_error_returns_all_none(self):
        import httpx
        result = self._call_with_fetch_error(httpx.RequestError('fail'))
        assert result == self._NULL

    def test_dns_failure_returns_all_none(self):
        with patch('app.knowhow.og_utils.socket.getaddrinfo',
                   side_effect=socket.gaierror('Name or service not known')):
            result = _fetch_og_data('https://nonexistent.example.com/')
        assert result == self._NULL

    def test_non_200_status_with_no_og_tags_returns_all_none(self):
        with patch('app.knowhow.og_utils.socket.getaddrinfo',
                   side_effect=_PUBLIC_DNS), \
             patch('app.knowhow.og_utils.httpx.get',
                   return_value=_fake_response('<html><body>Not Found</body></html>',
                                               status_code=404)):
            result = _fetch_og_data('https://example.com/missing')
        assert result == self._NULL
