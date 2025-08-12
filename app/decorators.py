from functools import wraps
from flask import abort
from flask_login import current_user
from .models import ProgramAdmin
from . import db

def admin_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        program_admin = db.session.get(ProgramAdmin, (current_user.program_id, current_user.id))
        if not program_admin:
            return abort(403)
        return f(*args, **kwargs)
    return wrapper