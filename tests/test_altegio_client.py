from collections.abc import Callable

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.integrations.altegio import (
    AltegioAuthenticationError,
    AltegioClient,
    AltegioRequestError,
    AltegioUnavailable,
)


def altegio_settings() -> Settings:
    return Settings(
        _env_file=None,
        altegio_base_url="https://altegio.test",
        altegio_api_token=SecretStr("partner-token"),
        altegio_user_token=SecretStr("user-token"),
        altegio_branch_id="branch-1",
        altegio_services_path="/branches/{branch_id}/services",
        altegio_masters_path="/branches/{branch_id}/masters",
        altegio_available_slots_path="/branches/{branch_id}/slots",
        altegio_create_booking_path="/branches/{branch_id}/bookings",
        altegio_cancel_booking_path="/branches/{branch_id}/bookings/{booking_id}",
        altegio_cancel_booking_method="DELETE",
    )


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> AltegioClient:
    return AltegioClient(altegio_settings(), transport=httpx.MockTransport(handler))


def test_get_services_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/branches/branch-1/services"
        assert request.headers["Authorization"] == "Bearer partner-token, User user-token"
        return httpx.Response(200, json={"data": [{"id": 1}]})

    with make_client(handler) as client:
        assert client.get_services() == {"data": [{"id": 1}]}


def test_get_masters_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/branches/branch-1/masters"
        return httpx.Response(200, json={"data": [{"id": 2}]})

    with make_client(handler) as client:
        assert client.get_masters() == {"data": [{"id": 2}]}


def test_get_available_slots_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["date"] == "2026-09-24"
        return httpx.Response(200, json={"data": ["10:00", "11:00"]})

    with make_client(handler) as client:
        result = client.get_available_slots(params={"date": "2026-09-24"})

    assert result == {"data": ["10:00", "11:00"]}


def test_create_booking_success() -> None:
    payload = {"customer_id": 1, "starts_at": "2026-09-24T10:00:00+05:00"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/branches/branch-1/bookings"
        assert request.content == httpx.Request("POST", "https://x", json=payload).content
        return httpx.Response(201, json={"data": {"id": 10}})

    with make_client(handler) as client:
        assert client.create_booking(payload) == {"data": {"id": 10}}


def test_cancel_booking_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/branches/branch-1/bookings/10"
        return httpx.Response(200, json={"data": {"id": 10, "cancelled": True}})

    with make_client(handler) as client:
        result = client.cancel_booking(10)

    assert result == {"data": {"id": 10, "cancelled": True}}


@pytest.mark.parametrize("status_code", [401, 403])
def test_authentication_errors(status_code: int) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "unauthorized"})

    with make_client(handler) as client:
        with pytest.raises(AltegioAuthenticationError) as error:
            client.get_services()

    assert error.value.status_code == status_code


@pytest.mark.parametrize("status_code", [500, 502, 503])
def test_server_errors_raise_unavailable(status_code: int) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "temporary failure"})

    with make_client(handler) as client:
        with pytest.raises(AltegioUnavailable):
            client.get_services()


def test_timeout_raises_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("request timed out", request=request)

    with make_client(handler) as client:
        with pytest.raises(AltegioUnavailable, match="request timed out"):
            client.get_services()


def test_other_client_error_raises_request_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"error": "invalid request"})

    with make_client(handler) as client:
        with pytest.raises(AltegioRequestError) as error:
            client.create_booking({"invalid": True})

    assert error.value.status_code == 422

