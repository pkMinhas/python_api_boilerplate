from passlib.context import CryptContext
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims
from functools import wraps
from application_error import ApplicationError
from constants import JwtClaims

# Used for password operations
password_context = CryptContext(schemes=["sha256_crypt"])


# Custom decorator that verifies the JWT is present in
# the request, as well as ensuring that it has the isAdmin claim
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        is_admin = claims.get(JwtClaims.IS_ADMIN, False)
        if not is_admin:
            raise ApplicationError("Admin only endpoint!", 403)
        else:
            return fn(*args, **kwargs)
    return wrapper


def super_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        is_super_admin = claims.get(JwtClaims.IS_SUPER_ADMIN, False)
        if not is_super_admin:
            raise ApplicationError("Super-Admin only endpoint!", 403)
        else:
            return fn(*args, **kwargs)
    return wrapper
