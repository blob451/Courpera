from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.db import connection
from django.test.utils import CaptureQueriesContext

from courses.models import Course, Enrolment
from materials.models import Material
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
def test_notifications_recent_limit_and_ordering():
    t = User.objects.create_user(username="nlim", password="pw")
    t.profile.role = "teacher"; t.profile.save(update_fields=["role"])
    s = User.objects.create_user(username="nlim_s", password="pw")
    s.profile.role = "student"; s.profile.save(update_fields=["role"])
    c = Course.objects.create(owner=t, title="Nlim", description="")
    Enrolment.objects.create(course=c, student=s)  # notify teacher
    # upload material to notify students
    f = SimpleUploadedFile("a.pdf", b"%PDF-1.4\n", content_type="application/pdf")
    Material.objects.create(course=c, uploaded_by=t, title="Doc", file=f)

    ct = Client(); assert ct.login(username="nlim", password="pw")
    r = ct.get("/activity/notifications/recent/?limit=1")
    assert r.status_code == 200
    data = r.json()
    assert len(data.get("results", [])) == 1
    # Newest-first ordering is expected
    r_all = ct.get("/activity/notifications/recent/?limit=10")
    items = r_all.json().get("results", [])
    created = [i.get("created_at") for i in items]
    assert created == sorted(created, reverse=True)


@pytest.mark.django_db
def test_notifications_recent_query_budget():
    t = User.objects.create_user(username="nbud", password="pw")
    t.profile.role = "teacher"; t.profile.save(update_fields=["role"])
    s = User.objects.create_user(username="nbud_s", password="pw")
    s.profile.role = "student"; s.profile.save(update_fields=["role"])
    c = Course.objects.create(owner=t, title="Nbud", description="")
    Enrolment.objects.create(course=c, student=s)
    ct = Client(); assert ct.login(username="nbud", password="pw")
    with CaptureQueriesContext(connection) as ctx:
        r = ct.get("/activity/notifications/recent/?limit=5")
        assert r.status_code == 200
    assert len(ctx.captured_queries) <= 5

