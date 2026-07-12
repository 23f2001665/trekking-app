"""
This blueprint handles all the routes related to treks, including creating, updating, deleting, and retrieving trek information. 
It does not include user management functionalities, which are handled in the users.py blueprint.
It also not include booking management functionalities, which are handled in the bookings.py blueprint.
"""

from flask import Blueprint, request, jsonify, session, g
from ..extensions import db, cache
from ..models import *
from sqlalchemy import select
from ..models import TrekStatus, UserRoleName, enum_values
from .helpers import require_roles

from datetime import datetime

trek_bp = Blueprint('trek', __name__)

# VIEW ALL TREKS ADMIN, TREKKER AND STAFF ASSOCIATED TREKS FOR STAFF
@trek_bp.route('/all', methods=['GET'])
@require_roles('admin', 'trek_staff', 'trekker')
@cache.cached(timeout=300, key_prefix=lambda: f'all_treks_{session.get("user")["id"]}')  # Cache the result for 5 minutes
def all_treks():
    """
    Get all treks for admin and staff associated treks for staff
    """
    current_user = session.get('user')

    if current_user['role'] == 'admin' or current_user['role'] == 'trekker':
        stmt = select(Trek)
    elif current_user['role'] == 'trek_staff':
        stmt = select(Trek).where(Trek.staff_user_id == current_user['id'])
    else:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    treks = db.session.execute(stmt).scalars().all()
    # exporting all the data of the trek, including the staff_id and other details
    exports = [trek.export() for trek in treks]
    return jsonify({'treks': exports}), 200

# GET A SPECIFIC TREK INFORMATION (ADMIN AND STAFF)
@trek_bp.route('/<int:trek_id>', methods=['GET'])
@require_roles('admin', 'trek_staff', 'trekker')
@cache.cached(timeout=300, key_prefix=lambda: f'trek_info_{request.view_args["trek_id"]}')  # Cache the result for 5 minutes
def get_trek(trek_id):
    """
    Get a specific trek by ID (admin and staff)
    """
    current_user = session.get('user')
    trek = db.session.get(Trek, trek_id)

    if current_user['role'] == 'trek_staff':
        if not trek or trek.staff_user_id != current_user['id']:
            return jsonify({'error': 'Unauthorized access'}), 404
    
    if not trek:
        return jsonify({'error': 'Trek not found'}), 404
    else:
        exports = trek.export()
        return jsonify({'trek_info': exports}), 200

# UPDATE A SPECIFIC TREK INFORMATION (ADMIN AND STAFF)
@trek_bp.route('/<int:trek_id>', methods=['PATCH'])
@require_roles('admin', 'trek_staff')
def update_trek(trek_id):
    """
    Update a specific trek by ID (admin and staff) except for status, staff_id, and created_at
    """
    current_user = session.get('user')
    trek = db.session.get(Trek, trek_id)

    if current_user['role'] == 'trek_staff':
        if not trek or trek.staff_user_id != current_user['id']:
            return jsonify({'error': 'Unauthorized access'}), 404
    
    if not trek:
        return jsonify({'error': 'Trek not found'}), 404

    data = g.data

    # Update the trek details based on the provided data
    title_string = data.get('title', '')
    if title_string and len(title_string) > 0:
        trek.title = title_string

    trek.description = data.get('description', trek.description)

    location_string = data.get('location', '')
    if location_string and len(location_string) > 0:
        trek.location = location_string

    capacity_string = data.get('capacity', '')
    if capacity_string.isdigit() and int(capacity_string) < trek.seats_booked:
        return jsonify({'error': 'Capacity cannot be less than total bookings'}), 400
    trek.capacity = int(data.get('capacity', trek.capacity)) if capacity_string.isdigit() and int(capacity_string) > 0 else trek.capacity

    price_string = data.get('price', '')
    if price_string and float(price_string) >= 0: # can raise ValueError
        trek.price = float(price_string)

    start_date_str = data.get('start_date', '')
    end_date_str = data.get('end_date', '')
    if start_date_str:
        trek.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    if end_date_str:
        trek.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    if not (trek.start_date and trek.end_date and trek.start_date <= trek.end_date):
        return jsonify({'error': 'Date format or value error'}), 400
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while updating the trek'}), 500
    
    cache.delete(f'trek_info_{trek_id}')  # Invalidate the cache for this specific trek
    cache.delete(f'all_treks_{current_user["id"]}')  # Invalidate the cache for all treks for this user
    return jsonify({'message': 'Trek updated successfully'}), 200

# UPDATE A SPECIFIC TREK STATUS (ADMIN AND STAFF)
@trek_bp.route('/<int:trek_id>/status', methods=['PATCH'])
@require_roles('admin', 'trek_staff')
def update_trek_status(trek_id):
    """
    Update the status of a specific trek by ID (admin and staff)
    """
    current_user = session.get('user')
    trek = db.session.get(Trek, trek_id)

    if current_user['role'] == 'trek_staff':
        if not trek or trek.staff_user_id != current_user['id']:
            return jsonify({'error': 'Unauthorized access'}), 404
    
    if not trek:
        return jsonify({'error': 'Trek not found'}), 404

    data = g.data
    new_status = data.get('status')

    if new_status not in set(enum_values(TrekStatus)):
        return jsonify({'error': 'Invalid status value'}), 400

    if new_status == "open":
        trek.open()
    
    if new_status == "completed":
        trek.complete()

    if new_status == "cancelled":
        # For all the associated bookings, mark as cancelled
        for booking in trek.bookings:
            booking.cancel()
        trek.cancel()

    try:
        db.session.commit()    
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while updating the trek status'}), 500

    cache.delete(f'trek_info_{trek_id}')  # Invalidate the cache for this specific trek
    return jsonify({'message': 'Trek status updated successfully'}), 200

# CHANGE THE ASSGNED STAFF OF A SPECIFIC TREK (ADMIN ONLY)
@trek_bp.route('/<int:trek_id>/assign_staff', methods=['PATCH'])
@require_roles('admin')
def assign_staff(trek_id):
    """
    Change the assigned staff of a specific trek by ID (admin only)
    """
    trek = db.session.get(Trek, trek_id)

    if not trek:
        return jsonify({'error': 'Trek not found'}), 404

    data = g.data
    new_staff_id = data.get('staff_id')

    if not new_staff_id or not new_staff_id.isdigit() or int(new_staff_id) <= 0:
        return jsonify({'error': 'Invalid staff ID'}), 400

    # Check if the new staff ID exists and is a trek staff
    staff_user = db.session.get(User, new_staff_id)
    if not staff_user or staff_user.role != UserRoleName.TREK_STAFF:
        return jsonify({'error': 'Staff user not found or not a trek staff'}), 404

    trek.staff_user_id = new_staff_id

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while updating the trek staff'}), 500

    cache.delete(f'trek_info_{trek_id}')  # Invalidate the cache for this specific trek
    return jsonify({'message': 'Trek staff updated successfully'}), 200

# CREATE A NEW TREK (ADMIN ONLY)
@trek_bp.route('/create', methods=['POST'])
@require_roles('admin')
def create_trek():
    """
    Create a new trek (admin only)
    """
    data = g.data
    if {'title', 'description', 'location', 'capacity', 'price', 'start_date', 'end_date'}.issubset(set(data.keys())) is False:
        return jsonify({'error': 'Missing required fields'}), 400
    
    title_string = data.get('title', '')
    description_string = data.get('description', '')
    location_string = data.get('location', '')
    capacity_string = data.get('capacity', '')
    price_string = data.get('price', '')
    start_date_str = data.get('start_date', '')
    end_date_str = data.get('end_date', '')
    staff_id_string = data.get('staff_id', '')
    staff_id = None # just to avoid UnboundLocalError in case staff_id_string is not provided or invalid

    if title_string and len(title_string) > 0:
        title = title_string
    if description_string and len(description_string) > 0:
        description = description_string
    if location_string and len(location_string) > 0:
        location = location_string
    if capacity_string.isdigit() and int(capacity_string) > 0:
        capacity = int(capacity_string)
    if price_string and float(price_string) >= 0:  #let's just keep this
        price = float(price_string)
    if staff_id_string.isdigit() and int(staff_id_string) > 0:
        staff_id = int(staff_id_string)

    staff = db.session.scalar(
    select(User).where(
        User.id == staff_id,
        User.role == UserRoleName.TREK_STAFF
        )
    )

    if staff is None:
        return jsonify({'error': 'Invalid staff user'}), 400
    staff_id = staff.id  # It should be valid here

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    if not (start_date and end_date and start_date <= end_date):
        return jsonify({'error': 'Date format or value error'}), 400
    
    if not (title and description and location and capacity and price and start_date_str and end_date_str):
        return jsonify({'error': 'Missing required fields'}), 400
    
    existing_trek = db.session.scalar(
        select(Trek).where(
            Trek.title == title,
            Trek.location == location,
            Trek.start_date == start_date,
        )
    )

    if existing_trek:
        return jsonify({'error': 'Trek with the same details already exists'}), 400

    trek = Trek(title=title, description=description, location=location, capacity=capacity, price=price, start_date=start_date, end_date=end_date, staff_user_id=staff_id)
    db.session.add(trek)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while creating the trek'}), 500

    return jsonify({'message': 'Trek created successfully'}), 201
    
# # DELETE A SPECIFIC TREK (ADMIN ONLY) # I am not sure if we should allow this, because it will delete all the associated bookings as well. So I am commenting this out for now. 
# @trek_bp.route('/<int:trek_id>', methods=['DELETE'])
# @require_roles('admin')
# def delete_trek(trek_id):
#     """
#     Delete a specific trek by ID (admin only)
#     """
#     trek = db.session.get(Trek, trek_id)

#     if not trek:
#         return jsonify({'error': 'Trek not found'}), 404

#     db.session.delete(trek)
#     db.session.commit()
    
#     cache.delete(f'trek_info_{trek_id}')  # Invalidate the cache for this specific trek
#     return jsonify({'message': 'Trek deleted successfully'}), 200