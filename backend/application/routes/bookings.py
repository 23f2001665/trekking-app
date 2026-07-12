"""
In this blueprint we handle booking management functionalities. It includes endpoints for creating a booking, retrieving all bookings, retrieving a specific booking, updating a booking, and deleting a booking. The routes are protected based on user roles (admin, staff, and trekker) to ensure that only authorized users can access or modify booking information.
"""

from flask import Blueprint, request, jsonify, session, g
from ..extensions import db
from ..models import *
from sqlalchemy import select
from .helpers import require_roles

booking_bp = Blueprint('booking', __name__)

# All BOOKINGS IN THE SYSTEM (ADMIN, STAFF, AND TREKKER)
@booking_bp.route('/all', methods=['GET'])
@require_roles('admin', 'trek_staff', 'trekker')
def all_bookings():
    """
    Get all bookings for admin and staff associated bookings for staff
    """
    current_user = session.get('user')

    if current_user['role'] == 'admin':
        stmt = select(Booking)
    elif current_user['role'] == 'trek_staff':
        stmt = select(Booking).join(Trek).where(Trek.staff_user_id == current_user['id'])
    elif current_user['role'] == 'trekker':
        stmt = select(Booking).where(Booking.trekker_user_id == current_user['id'])
    else:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    bookings = db.session.execute(stmt).scalars().all()
    exports = [booking.export() for booking in bookings]
    return jsonify({'bookings': exports}), 200

# GET A SPECIFIC BOOKING INFORMATION (ADMIN, STAFF, AND TREKKER)
@booking_bp.route('/<int:booking_id>', methods=['GET'])
@require_roles('admin', 'trek_staff', 'trekker')
def get_booking(booking_id):
    """
    Get a specific booking by ID (admin, staff, and trekker)
    """
    current_user = session.get('user')
    booking = db.session.get(Booking, booking_id)

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    if current_user['role'] == 'trek_staff':
        if booking.trek.staff_user_id != current_user['id']:
            return jsonify({'error': 'Unauthorized access'}), 403
    elif current_user['role'] == 'trekker':
        if booking.trekker_user_id != current_user['id']:
            return jsonify({'error': 'Unauthorized access'}), 403

    exports = booking.export()
    return jsonify({'booking_info': exports}), 200

# ALL BOOKING FOR A TREK(ADMIN, STAFF, AND TREKKER)
@booking_bp.route('/trek/<int:trek_id>', methods=['GET'])
@require_roles('admin', 'trek_staff')
def get_bookings_for_trek(trek_id):
    """
    Get all bookings for a specific trek by trek ID (admin, staff, and trekker)
    """
    current_user = session.get('user')
    trek = db.session.get(Trek, trek_id)

    if not trek:
        return jsonify({'error': 'Trek not found'}), 404

    if current_user['role'] == 'trek_staff':
        if trek.staff_user_id != current_user['id']:
            return jsonify({'error': 'Unauthorized access'}), 403

    bookings = db.session.execute(select(Booking).where(Booking.trek_id == trek_id)).scalars().all()
    exports = [booking.export() for booking in bookings]
    return jsonify({'bookings': exports}), 200

# All booking for a particular user (admin, staff, and trekker)
@booking_bp.route('/user/<int:user_id>', methods=['GET'])
@require_roles('admin', 'trek_staff', 'trekker')
def get_bookings_for_user(user_id):
    """
    Get all bookings for a specific user by user ID (admin, staff, and trekker)
    """
    current_user = session.get('user')
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if current_user['role'] == 'trek_staff':
        # Staff can only view bookings for users associated with their treks
        stmt = select(Booking).join(Trek).where(
            Booking.trekker_user_id == user_id,
            Trek.staff_user_id == current_user['id']
        )
    elif current_user['role'] == 'trekker':
        # Trekkers can only view their own bookings
        if current_user['id'] != user_id:
            return jsonify({'error': 'Unauthorized access'}), 403
        stmt = select(Booking).where(Booking.trekker_user_id == user_id)
    else:
        # Admin can view all bookings for any user
        stmt = select(Booking).where(Booking.trekker_user_id == user_id)

    bookings = db.session.execute(stmt).scalars().all()
    exports = [booking.export() for booking in bookings]
    return jsonify({'bookings': exports}), 200

# Create a new booking (trekker)
@booking_bp.route('/create', methods=['POST'])
@require_roles('trekker')
def create_booking():
    data = g.data

    trek_id = data.get('trek_id')
    if not trek_id or not trek_id.isdigit() or int(trek_id) <= 0:
        return jsonify({'error': 'Invalid trek ID'}), 400
    trekker_user_id = session.get('user')['id']
    notes = data.get('notes')

    trek = db.session.execute(
        select(Trek).where(Trek.id == trek_id).with_for_update()
    ).scalar_one_or_none()

    if not trek:
        return jsonify({'error': 'Trek not found'}), 404

    if not trek.is_open or trek.is_full:
        return jsonify({'error': 'Trek is not available for booking'}), 400

    existing_booking = db.session.execute(
        select(Booking).where(
            Booking.trek_id == trek_id,
            Booking.trekker_user_id == trekker_user_id
        ).with_for_update()
    ).scalar_one_or_none()

    if existing_booking:
        return jsonify({'error': 'You have already booked this trek'}), 400

    booking = Booking(
        trek_id=trek_id,
        trekker_user_id=trekker_user_id,
        price_at_booking=trek.price,
        notes=notes
    )
    db.session.add(booking)

    try:
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while creating the booking'}), 500

    return jsonify({'message': 'Booking created successfully'}), 201

# update notes/status of a booking (admin, staff)
@booking_bp.route('/<int:booking_id>', methods=['PATCH'])
@require_roles('admin', 'trek_staff', 'trekker')
def update_booking(booking_id):
    """
    Update a specific booking by ID (admin, staff, and trekker)
    """
    current_user = session.get('user')
    booking = db.session.get(Booking, booking_id)

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    if current_user['role'] == 'trek_staff':
        if booking.trek.staff_user_id != current_user['id']:
            return jsonify({'error': 'Unauthorized access'}), 403
    
    if current_user['role'] == 'trekker':
        if booking.trekker_user_id != current_user['id']:
            return jsonify({'error': 'Unauthorized access'}), 403

    data = g.data
    status = data.get('status')

    if status == 'cancelled':
        booking.cancel()
    elif status is not None:
        return jsonify({'error': 'Invalid status update'}), 400

    notes = data.get('notes')
    if notes is not None and isinstance(notes, str) and booking.is_booked:
        booking.notes = notes

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while updating the booking'}), 500
    
    return jsonify({'message': 'Booking updated successfully'}), 200


