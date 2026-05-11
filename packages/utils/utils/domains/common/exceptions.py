from fastapi import status
class DomainError(Exception):
    code = "domain_error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

class DuplicateEmail(DomainError):
    code = "duplicate_email"
    status_code = status.HTTP_409_CONFLICT

class DuplicateUsername(DomainError):
    code = "duplicate_username"
    status_code = status.HTTP_409_CONFLICT

class Conflict(DomainError):
    code = "conflict"
    status_code = status.HTTP_409_CONFLICT

class DatabaseConflict(DomainError):
    code = "db_conflict"
    status_code = status.HTTP_409_CONFLICT

class NotFound(DomainError):
    code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND

class ValidationFailed(DomainError):
    code = "validation_failed"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

class Unauthorized(DomainError):
    code = "unauthorized"
    status_code = status.HTTP_401_UNAUTHORIZED

class Forbidden(DomainError):
    code = "forbidden"
    status_code = status.HTTP_403_FORBIDDEN

class NotSupported(DomainError):
    code = "not_supported"
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
