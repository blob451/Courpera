from __future__ import annotations

import hashlib
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def avatar_url(user, size: int = 48) -> str:
    """Return a deterministic DiceBear avatar URL for a user.

    Uses user.pk and a salt; does not expose e‑mail/username.
    """
    try:
        seed_src = f"{getattr(user, 'pk', '0')}:{getattr(settings, 'AVATAR_SEED_SALT', 'courpera')}"
        seed = hashlib.sha256(seed_src.encode()).hexdigest()
        # Serve avatars via a same-origin proxy endpoint to avoid ORB blocking
        return f"/accounts/avatar/{getattr(user, 'pk', 0)}/{size}/?seed={seed}&size={size}"
    except Exception:
        return ""
