import logging
import pytest


@pytest.fixture(autouse=True)
def silence_django_request_logger():
    """Reduce noise from expected 4xx in passing tests.

    Many tests intentionally exercise 400/403 paths to validate security
    and input handling. Django logs these at WARNING via 'django.request'.
    Lower that logger to ERROR during tests to avoid clutter.
    """
    logger = logging.getLogger("django.request")
    old = logger.level
    logger.setLevel(logging.ERROR)
    try:
        yield
    finally:
        logger.setLevel(old)

