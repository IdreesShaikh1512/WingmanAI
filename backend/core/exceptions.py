"""Domain exceptions. Caught at the API layer and mapped to safe HTTP responses."""


class WingmanError(Exception):
    """Base exception for all domain errors."""


class EmailAlreadyRegisteredError(WingmanError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")


class InvalidCredentialsError(WingmanError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InvalidTokenError(WingmanError):
    def __init__(self, reason: str = "Invalid or expired token") -> None:
        super().__init__(reason)


class UserNotFoundError(WingmanError):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"User not found: {user_id}")
