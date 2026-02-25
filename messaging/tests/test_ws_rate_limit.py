from __future__ import annotations

import asyncio
import pytest
from channels.testing import WebsocketCommunicator
from django.test import Client
from django.contrib.auth.models import User
from courses.models import Course, Enrolment
from config.asgi import application


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_ws_rate_limit_allows_up_to_five_messages(event_loop):
    teacher = User.objects.create_user(username="tWS", password="pw")
    course = Course.objects.create(owner=teacher, title="WS", description="")

    # Login via Django test client to get session cookie for AuthMiddlewareStack
    client = Client()
    assert client.login(username="tWS", password="pw")
    sessionid = client.cookies.get("sessionid").value
    headers = [(b"cookie", f"sessionid={sessionid}".encode())]

    communicator = WebsocketCommunicator(application, f"/ws/chat/course/{course.id}/", headers=headers)
    connected, _ = await communicator.connect()
    assert connected

    # Send 6 quick messages; rate limiter should drop at least one
    for i in range(6):
        await communicator.send_json_to({"message": f"m{i}"})
    await asyncio.sleep(0.2)

    # Read echoes (up to a timeout)
    received = []
    try:
        while True:
            msg = await asyncio.wait_for(communicator.receive_json_from(), timeout=0.2)
            received.append(msg)
            if len(received) >= 6:
                break
    except Exception:
        pass

    await communicator.disconnect()
    # Expect at most 5 within the 5-second window
    assert len(received) <= 5

