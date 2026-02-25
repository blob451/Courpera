from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """App configuration for accounts (roles, profiles)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

