from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Render the public landing page.

    The content is intentionally brief for Stage 1, serving as a working
    sanity check for the scaffold. Additional links and panels are added
    in later stages once the API and authentication are introduced.
    """
    ctx = {
        "app_name": "Courpera",
        "tagline": "A streamlined, server‑rendered e‑learning application.",
    }
    return render(request, "index.html", ctx)

