from __future__ import annotations

import pytest
from django.test import Client


@pytest.mark.django_db
def test_csp_has_expected_directives():
    c = Client()
    r = c.get("/")
    assert r.status_code == 200
    csp = r.headers.get("Content-Security-Policy", "")
    assert csp
    # No unsafe-inline
    assert "'unsafe-inline'" not in csp
    # DiceBear and data images allowed
    assert "img-src" in csp and ("dicebear" in csp or "api.dicebear.com" in csp)
    assert "data:" in csp
    # Allow ws/wss for Channels
    assert "connect-src" in csp and ("ws:" in csp or "wss:" in csp)
    # Disallow framing
    assert "frame-ancestors 'none'" in csp

