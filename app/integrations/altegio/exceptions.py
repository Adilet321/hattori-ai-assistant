class AltegioRequestError(Exception):
    """Altegio rejected a valid HTTP request with a client error."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AltegioAuthenticationError(AltegioRequestError):
    """Altegio rejected the configured credentials or their permissions."""


class AltegioUnavailable(Exception):
    """Altegio could not be reached or returned a server-side failure."""

