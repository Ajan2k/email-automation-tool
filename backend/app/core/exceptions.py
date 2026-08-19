class AppError(Exception):
    """Base application error."""

    status_code = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    status_code = 404


class PermissionDeniedError(AppError):
    status_code = 403


class ValidationError(AppError):
    status_code = 422


class ExternalServiceError(AppError):
    status_code = 502
