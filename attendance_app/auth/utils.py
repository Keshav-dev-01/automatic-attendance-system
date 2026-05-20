from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def login_required_with_role(*allowed_roles):
    """Decorator to check if user is logged in and has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))
            
            if allowed_roles:
                # Check if current user's role is in allowed_roles
                # allowed_roles can contain strings or UserRole enum values
                allowed_role_names = [
                    role.value if hasattr(role, 'value') else str(role)
                    for role in allowed_roles
                ]
                if current_user.role not in allowed_role_names:
                    flash('You do not have permission to access this page.', 'danger')
                    return redirect(url_for('student.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
