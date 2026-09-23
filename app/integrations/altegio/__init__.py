from app.integrations.altegio.client import AltegioClient
from app.integrations.altegio.exceptions import (
    AltegioAuthenticationError,
    AltegioRequestError,
    AltegioUnavailable,
)

__all__ = [
    "AltegioAuthenticationError",
    "AltegioClient",
    "AltegioRequestError",
    "AltegioUnavailable",
]

