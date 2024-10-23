# shoe/decorators.py

from functools import wraps
from flask import session, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the route is for a buyer
        if "buyer_id" not in session:
            if request.endpoint.startswith('admin_'):
                return redirect(url_for('admin_login'))  # Redirect to admin login for admin routes
            else:
                return redirect(url_for('buyer_login'))  # Redirect to buyer login for user routes
        return f(*args, **kwargs)
    return decorated_function
