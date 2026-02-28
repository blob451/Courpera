from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def get_item(d, key):
    try:
        return d.get(key)
    except Exception:
        return None


@register.filter
def time_until(dt):
    """Return a compact relative time until the given datetime.

    Formats like '2d 3h', '3h 15m', or '0m' when within a minute.
    If dt is None, returns an empty string. If dt is in the past, returns '0m'.
    """
    if not dt:
        return ""
    try:
        now = timezone.now()
        delta = dt - now
        seconds = int(delta.total_seconds())
        if seconds <= 0:
            return "0m"
        minutes = seconds // 60
        days, rem_mins = divmod(minutes, 1440)
        hours, mins = divmod(rem_mins, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if not days and mins and hours < 6:
            # Show minutes when under 6 hours to add precision
            parts.append(f"{mins}m")
        if not parts:
            parts.append("0m")
        return " ".join(parts)
    except Exception:
        return ""
