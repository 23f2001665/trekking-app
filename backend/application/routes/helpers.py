import datetime
from functools import wraps
from flask import session, jsonify
from ..extensions import db
from ..models import Trek

def require_roles(*allowed_roles):
    """
    Check if the logged-in user has one of the allowed roles.
    If not, return a 403 Forbidden response.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = session.get("user")

            if user is None:
                return jsonify({"message": "Login required"}), 401

            if user["role"] not in allowed_roles:
                return jsonify({"message": "Forbidden"}), 403

            return view(*args, **kwargs)

        return wrapper
    return decorator

# path parameter can be used as kwargs in the view function, so we can access it using kwargs.get("trek_id")
def require_assigned_staff(param_name):
    """
    Check if the logged-in user is either an admin or the assigned trek staff for the trek specified by the path parameter.
    If not, return a 403 Forbidden response.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = session.get("user")

            if user is None:
                return jsonify({"message": "Login required"}), 401

            if user["role"] not in ("admin", "trek_staff"):
                return jsonify({"message": "Forbidden"}), 403

            trek_id = kwargs.get(param_name)
            if trek_id is None:
                return jsonify({"message": "Trek ID is required"}), 400

            trek = db.session.get(Trek, trek_id)
            if trek is None:
                return jsonify({"message": "Trek not found"}), 404

            if user["role"] == "trek_staff" and trek.staff_user_id != user["id"]:
                return jsonify({"message": "Forbidden"}), 403

            return view(*args, **kwargs)

        return wrapper
    return decorator
