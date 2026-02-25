from __future__ import annotations

from django.utils.deprecation import MiddlewareMixin


class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """Add a basic Content-Security-Policy header.

    This policy is intentionally modest to avoid breaking inline styles
    in templates. It can be tightened further as inline styles/scripts
    are removed.
    """

    def process_response(self, request, response):  # noqa: D401
        csp = (
            "default-src 'self'; "
            "img-src 'self' https://api.dicebear.com data:; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )
        response["Content-Security-Policy"] = csp
        return response

