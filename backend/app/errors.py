"""Application error type and the standard JSON error body."""


class AppError(Exception):
    """An expected, user-presentable error."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def error_body(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}
