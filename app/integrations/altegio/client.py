from collections.abc import Mapping
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.integrations.altegio.endpoints import AltegioEndpointPaths
from app.integrations.altegio.exceptions import (
    AltegioAuthenticationError,
    AltegioRequestError,
    AltegioUnavailable,
)


class AltegioClient:
    """Synchronous HTTP adapter for the configured Altegio API surface."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        settings = settings or get_settings()
        if not settings.altegio_base_url:
            raise ValueError("ALTEGIO_BASE_URL is required")
        if settings.altegio_api_token is None:
            raise ValueError("ALTEGIO_API_TOKEN is required")

        self._branch_id = settings.altegio_branch_id
        self._endpoints = AltegioEndpointPaths.from_settings(settings)
        partner_token = settings.altegio_api_token.get_secret_value()
        authorization = f"Bearer {partner_token}"
        if settings.altegio_user_token is not None:
            authorization += f", User {settings.altegio_user_token.get_secret_value()}"

        self._http = httpx.Client(
            base_url=settings.altegio_base_url,
            headers={
                "Accept": settings.altegio_accept_header,
                "Authorization": authorization,
                "Content-Type": "application/json",
            },
            timeout=settings.altegio_timeout_seconds,
            transport=transport,
        )

    def get_services(self) -> Any:
        path = self._render(self._endpoints.services)
        return self._request("GET", path)

    def get_masters(self) -> Any:
        path = self._render(self._endpoints.masters)
        return self._request("GET", path)

    def get_available_slots(self, *, params: Mapping[str, object] | None = None) -> Any:
        path = self._render(self._endpoints.available_slots)
        return self._request("GET", path, params=params)

    def create_booking(self, payload: Mapping[str, object]) -> Any:
        path = self._render(self._endpoints.create_booking)
        return self._request("POST", path, json=payload)

    def cancel_booking(
        self,
        booking_id: str | int,
        *,
        payload: Mapping[str, object] | None = None,
    ) -> Any:
        path = self._render(self._endpoints.cancel_booking, booking_id=booking_id)
        request_options = {"json": payload} if payload is not None else {}
        return self._request(self._endpoints.cancel_booking_method, path, **request_options)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "AltegioClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _render(self, path: str, **values: object) -> str:
        return self._endpoints.render(path, branch_id=self._branch_id, **values)

    def _request(self, method: str, path: str, **kwargs: object) -> Any:
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise AltegioUnavailable(f"Altegio request failed: {exc}") from exc

        if response.status_code in (401, 403):
            raise AltegioAuthenticationError(
                f"Altegio authentication failed with HTTP {response.status_code}",
                status_code=response.status_code,
            )
        if response.status_code >= 500:
            raise AltegioUnavailable(
                f"Altegio is unavailable: HTTP {response.status_code}"
            )
        if 400 <= response.status_code < 500:
            raise AltegioRequestError(
                f"Altegio rejected the request with HTTP {response.status_code}",
                status_code=response.status_code,
            )
        if response.status_code == 204 or not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise AltegioRequestError("Altegio returned an invalid JSON response") from exc
