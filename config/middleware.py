from __future__ import annotations

from django.utils.deprecation import MiddlewareMixin


class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """Add a basic Content-Security-Policy header.

    This policy avoids inline scripts/styles to reduce XSS risk. Inline
    styles in templates may be blocked; templates should prefer classes
    and external CSS/JS.
    """

    def process_response(self, request, response):  # noqa: D401
        csp = (
            "default-src 'self'; "
            "img-src 'self' https://api.dicebear.com data:; "
            "script-src 'self'; "
            "style-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )
        response["Content-Security-Policy"] = csp
        return response
