from dataclasses import dataclass

from app.core.config import Settings


@dataclass(frozen=True)
class AltegioEndpointPaths:
    """Version-specific Altegio paths kept outside the HTTP client methods."""

    services: str
    masters: str
    available_slots: str
    create_booking: str
    cancel_booking: str
    cancel_booking_method: str

    @classmethod
    def from_settings(cls, settings: Settings) -> "AltegioEndpointPaths":
        values = {
            "services": settings.altegio_services_path,
            "masters": settings.altegio_masters_path,
            "available_slots": settings.altegio_available_slots_path,
            "create_booking": settings.altegio_create_booking_path,
            "cancel_booking": settings.altegio_cancel_booking_path,
            "cancel_booking_method": settings.altegio_cancel_booking_method,
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ValueError(f"Missing Altegio endpoint settings: {', '.join(missing)}")
        return cls(**values)  # type: ignore[arg-type]

    def render(self, path: str, *, branch_id: str | None, **values: object) -> str:
        if "{branch_id}" in path and not branch_id:
            raise ValueError("ALTEGIO_BRANCH_ID is required by the configured endpoint path")
        return path.format(branch_id=branch_id, **values)

