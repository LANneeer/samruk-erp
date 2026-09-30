class DomainError(Exception):
    code = "domain_error"
    status_code = 500 #INTERNAL_SERVER_ERROR

class DuplicateEmail(DomainError):
    code = "duplicate_email"
    status_code = 409 #CONFLICT

class DuplicateUsername(DomainError):
    code = "duplicate_username"
    status_code = 409 #CONFLICT

class Conflict(DomainError):
    code = "conflict"
    status_code = 409 #CONFLICT

class DatabaseConflict(DomainError):
    code = "db_conflict"
    status_code = 409 #CONFLICT

class NotFound(DomainError):
    code = "not_found"
    status_code = 404 #NOT_FOUND

class ValidationFailed(DomainError):
    code = "validation_failed"
    status_code = 422 #UNPROCESSABLE_ENTITY

class Unauthorized(DomainError):
    code = "unauthorized"
    status_code = 401 #UNAUTHORIZED

class Forbidden(DomainError):
    code = "forbidden"
    status_code = 403 #FORBIDDEN

class NotSupported(DomainError):
    code = "not_supported"
    status_code = 415 #UNSUPPORTED_MEDIA_TYPE
