"""
This blueprint handles cross-roles controlled routes and user management functionalities. It includes endpoints for retrieving all users, retrieving a specific user, retrieving users for a specific trek, creating staff members, and activating/deactivating users.
"""

from flask import Blueprint, request, jsonify, session, g
from ..extensions import db, cache
from ..models import *
from .helpers import require_roles, require_assigned_staff
from sqlalchemy import select

user_bp = Blueprint('users', __name__)

###########################################
# USER MANAGEMENT ROUTES (ADMIN ONLY)
###########################################

# GET ALL THE USERS (ADMIN ONLY)
@user_bp.route('/all')
@require_roles('admin')
def all_users():
    """
    Get all users (admin only)
    """
    stmt = select(User)
    users = db.session.execute(stmt).scalars().all()
    exports = [user.export('email', 'first_name', 'last_name', 'role') for user in users]
    return jsonify({'users': exports}), 200

# GET A SPECIFIC USER (ADMIN ONLY)
@user_bp.route('/<int:user_id>', methods=['GET'])
@require_roles('admin')
@cache.cached(timeout=300, key_prefix=lambda: f'user_info_{request.view_args["user_id"]}')  # Cache the result for 5 minutes
def get_user(user_id):
    """
    Get a specific user by ID (admin, trek staff, and trekker)
    This is specifically for viewing other users' information, not for the logged-in user to view their own info.
    To view one's own info, use the /me endpoint in auth.py
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    else:
        exports = user.export('email', 'first_name', 'last_name', 'role')
        return jsonify({'user_info': exports}), 200

# UPDATE A SPECIFIC USER (ADMIN ONLY)
@user_bp.route('/<int:user_id>', methods=['PATCH'])
@require_roles('admin')
def update_user(user_id):
    """
    Update a specific user's information (admin only)
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = g.data
    first_name = data.get('first_name')
    last_name = data.get('last_name')

    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while updating the user'}), 500
    
    cache.delete(f'user_info_{user_id}')  # Invalidate the cache for this specific user

    return jsonify({'message': 'User updated successfully'}), 200

# DEACTIVATE A SPECIFIC USER (ADMIN ONLY)
@user_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@require_roles('admin')
def deactivate_user(user_id):
    """
    Deactivate a user (admin only)
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if user.is_admin:
        return jsonify({'error': 'Cannot deactivate an admin user'}), 403
    user.is_active = False

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while deactivating the user'}), 500
    
    cache.delete(f'user_info_{user_id}')  # Invalidate the cache for this specific user
    return jsonify({'message': 'User deactivated successfully'}), 200

# ACTIVATE A SPECIFIC USER (ADMIN ONLY)
@user_bp.route('/<int:user_id>/activate', methods=['POST'])
@require_roles('admin')
def activate_user(user_id):
    """
    Activate a user (admin only)
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user.is_active = True

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while activating the user'}), 500
    
    cache.delete(f'user_info_{user_id}')  # Invalidate the cache for this specific user
    return jsonify({'message': 'User activated successfully'}), 200

######################################################
# TREK-USER RELATED ROUTES (ADMIN AND TREK STAFF ONLY)
######################################################

# CREATE A NEW STAFF MEMBER (ADMIN ONLY)
@user_bp.route('/create_staff', methods=['POST'])
@require_roles('admin')
def create_staff():
    """
    create a new staff member (admin only)
    """
    data = g.data
    email_string = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    user = db.session.scalar(
    select(User).where(User.email == email_string)
    )
    if user:
        return jsonify({'error': 'User with this email already exists'}), 409
    
    user = User(
        email=email_string,
        first_name=first_name,
        last_name=last_name
    )
    user.set_password(data.get('password'))
    user.make_staff()
    db.session.add(user)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while creating the staff member'}), 500
    
    exports = user.export('email', 'first_name', 'last_name', 'role')
    return jsonify({'message': 'Staff member created successfully', 'user': exports}), 201

# GET ALL USERS FOR A SPECIFIC TREK (ADMIN AND TREK STAFF ONLY)
@user_bp.route('/trek/<int:trek_id>', methods=['GET'])
@require_assigned_staff("trek_id")
def get_trek_users(trek_id):
    """
    Get all users for a specific trek (admin and trek staff only)
    """
    stmt = select(User).join(User.bookings).where(Booking.trek_id == trek_id).distinct()
    users = db.session.execute(stmt).scalars().all()
    exports = [user.export('email', 'first_name', 'last_name', 'role') for user in users]
    return jsonify({'users': exports}), 200


# GET ALL THE USERS FOR ALL THE TREKS FOR A SPECIFIC TREK STAFF (ADMIN AND TREK STAFF ONLY)
@user_bp.route('/trek_staff/<int:staff_id>', methods=['GET'])
@require_roles('admin', 'trek_staff')
def get_staff_trek_users(staff_id):
    """
    Get all the users for all the treks for a specific trek staff (admin and trek staff only)
    """
    if session.get("user")["role"] == "trek_staff" and session.get("user")["id"] != staff_id:
        return jsonify({"message": "Forbidden"}), 403
    
    stmt = select(User).join(User.bookings).join(Booking.trek).where(Trek.staff_user_id == staff_id).distinct()
    users = db.session.execute(stmt).scalars().all()
    exports = [user.export('email', 'first_name', 'last_name', 'role') for user in users]
    return jsonify({'users': exports}), 200
