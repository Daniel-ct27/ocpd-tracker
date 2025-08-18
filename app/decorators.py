from functools import wraps
from flask import abort
from flask_login import current_user


def admin_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.role.lower() not in  {"liason","admin"}:
            return abort(403)
        return f(*args, **kwargs)
    return wrapper