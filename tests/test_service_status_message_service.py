from __future__ import annotations

import pytest

from metaeditor_safetensors.services.status_message_service import (
    DEFAULT_TIMEOUT_MS,
    StatusLevel,
    StatusMessage,
    StatusMessageService,
)


@pytest.fixture
def service():
    return StatusMessageService()


def test_post_invokes_listener(service):
    received: list[StatusMessage] = []
    service.add_listener(received.append)

    service.post("hello", level=StatusLevel.SUCCESS, timeout_ms=123)

    assert len(received) == 1
    assert received[0].text == "hello"
    assert received[0].level is StatusLevel.SUCCESS
    assert received[0].timeout_ms == 123


def test_post_defaults_when_timeout_unspecified(service):
    received: list[StatusMessage] = []
    service.add_listener(received.append)

    service.post("hi", level=StatusLevel.WARNING)

    assert received[-1].timeout_ms == DEFAULT_TIMEOUT_MS[StatusLevel.WARNING]


def test_info_success_warning_error_helpers(service, mocker):
    post = mocker.spy(service, "post")

    service.info("info")
    service.success("ok")
    service.warning("warn")
    service.error("fail", timeout_ms=0)

    assert post.call_count == 4
    post.assert_any_call("info", level=StatusLevel.INFO, timeout_ms=None)
    post.assert_any_call("ok", level=StatusLevel.SUCCESS, timeout_ms=None)
    post.assert_any_call("warn", level=StatusLevel.WARNING, timeout_ms=None)
    post.assert_any_call("fail", level=StatusLevel.ERROR, timeout_ms=0)


def test_add_listener_idempotent(service):
    calls = []
    service.add_listener(calls.append)
    service.add_listener(calls.append)

    service.post("ping")
    assert len(calls) == 1


def test_remove_listener(service):
    calls = []
    service.add_listener(calls.append)
    service.remove_listener(calls.append)

    service.post("ping")
    assert not calls


def test_clear_posts_blank_message(service):
    calls = []
    service.add_listener(calls.append)

    service.clear()

    assert calls[-1].text == ""
    assert calls[-1].timeout_ms == 0
