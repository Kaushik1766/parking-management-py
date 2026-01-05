DB_ERROR = 1001
VALIDATION_ERROR = 1002
UNEXPECTED_ERROR = 1003
UNAUTHORIZED_ERROR = 1004

class WebException(Exception):
    def __init__(self, status_code: int, message: str, error_code: int ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
