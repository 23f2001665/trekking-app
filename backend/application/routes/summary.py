"""
In this blueprint we handle summary management functionalities. It includes endpoints for retrieving summary information for treks, bookings, and users. The routes are protected based on user roles (admin, staff, and trekker) to ensure that only authorized users can access summary information.
"""

from flask import Blueprint, jsonify, session, Response
from sqlalchemy import select, func, and_
from .helpers import require_roles, require_assigned_staff
from ..extensions import db
from ..models import Booking, Trek, User, UserRoleName, TrekStatus, BookingStatus
from ..tasks import send_report


summary_bp = Blueprint('summary', __name__)



# ============================================================================
# USERS ENDPOINTS
# ============================================================================

@summary_bp.route('/users', methods=['GET'])
@require_roles('admin')
def all_users_summary():
    """
    Get summary information for all users (admin only).
    Single query using conditional aggregates.
    """
    result = db.session.execute(
    select(
        func.count().label("total"),
        func.count().filter(User.is_active).label("active"),
        func.count().filter(~User.is_active).label("inactive"),
        func.count().filter(
            and_(User.is_active, User.role == UserRoleName.TREKKER)
        ).label("active_trekkers"),
        func.count().filter(
            and_(~User.is_active, User.role == UserRoleName.TREKKER)
        ).label("inactive_trekkers"),
        func.count().filter(
            and_(User.is_active, User.role == UserRoleName.TREK_STAFF)
        ).label("active_staff"),
        func.count().filter(
            and_(~User.is_active, User.role == UserRoleName.TREK_STAFF)
        ).label("inactive_staff"),
        func.count().filter(User.role == UserRoleName.ADMIN).label("admins"),
        )
    ).one()
    print(result)
    
    return jsonify({
        'user_summary': {
            'total_users': result.total,
            'active_users': result.active,
            'inactive_users': result.inactive,
            'active_trekkers': result.active_trekkers,
            'inactive_trekkers': result.inactive_trekkers,
            'active_staff': result.active_staff,
            'inactive_staff': result.inactive_staff,
            'admins': result.admins,
        }
    }), 200


@summary_bp.route('/trek/<int:trek_id>/users', methods=['GET'])
@require_assigned_staff('trek_id')
def trek_users_summary(trek_id):
    """
    Get summary for all unique users associated with a trek.
    Uses DISTINCT to avoid duplicates from multiple bookings.
    """
    result = db.session.execute(
        select(
            func.count(User.id.distinct()).filter(User.is_active).label('active'),
            func.count(User.id.distinct()).filter(~User.is_active).label('inactive'),
        ).select_from(User).join(Booking).where(Booking.trek_id == trek_id)
    ).one()
    
    return jsonify({
        'trek_users_summary': {
            'active_users': result.active,
            'inactive_users': result.inactive
        }
    }), 200


# ============================================================================
# TREK ENDPOINTS
# ============================================================================

@summary_bp.route('/treks', methods=['GET'])
@require_roles('admin', 'trek_staff')
def treks_summary():
    """
    Get summary for all treks (filtered by staff if applicable).
    Single query with conditional aggregates for all statuses.
    """
    current_user = session.get('user')
    
    result = db.session.execute(
    select(
        func.count().label("total"),
        func.count().filter(Trek.status == TrekStatus.DRAFT).label("draft"),
        func.count().filter(Trek.status == TrekStatus.OPEN).label("open"),
        func.count().filter(Trek.status == TrekStatus.COMPLETED).label("completed"),
        func.count().filter(Trek.status == TrekStatus.CANCELLED).label("cancelled"),
        )
        .where(
            Trek.staff_user_id == current_user["id"]
            if current_user["role"] == "trek_staff"
            else True
        )
    ).one()
    total = result.total if result.total is not None else 0
    
    return jsonify({
        'treks_summary': {
            'total_treks': total,
            'draft_treks': result.draft,
            'open_treks': result.open,
            'completed_treks': result.completed,
            'cancelled_treks': result.cancelled
        }
    }), 200


# ============================================================================
# BOOKING ENDPOINTS
# ============================================================================

@summary_bp.route('/bookings', methods=['GET'])
@require_roles('admin', 'trek_staff', 'trekker')
def bookings_summary():
    current_user = session.get('user')

    query = select(
        func.count().label('total'),
        func.count().filter(
            Booking.status == BookingStatus.BOOKED
        ).label('booked'),
        func.count().filter(
            Booking.status == BookingStatus.CANCELLED
        ).label('cancelled'),
    ).select_from(Booking)

    if current_user['role'] == 'trek_staff':
        query = (
            query.join(Trek)
            .where(Trek.staff_user_id == current_user['id'])
        )
    elif current_user['role'] == 'trekker':
        query = query.where(
            Booking.trekker_user_id == current_user['id']
        )

    result = db.session.execute(query).one()

    return jsonify({
        "bookings_summary": {
            "total_bookings": result.total,
            "booked_bookings": result.booked,
            "cancelled_bookings": result.cancelled,
        }
    }), 200

@summary_bp.route('/trek/<int:trek_id>/bookings', methods=['GET'])
@require_assigned_staff('trek_id')
def trek_bookings_summary(trek_id):

    result = db.session.execute(
        select(
            func.count().label("total"),
            func.count().filter(
                Booking.status == BookingStatus.BOOKED
            ).label("booked"),
            func.count().filter(
                Booking.status == BookingStatus.CANCELLED
            ).label("cancelled"),
        )
        .select_from(Booking)
        .where(Booking.trek_id == trek_id)
    ).one()

    return jsonify({
        "trek_bookings_summary": {
            "total_bookings": result.total,
            "booked_bookings": result.booked,
            "cancelled_bookings": result.cancelled,
        }
    }), 200


# Booking for trekker is already covered in the '/bookings' endpoint.
@summary_bp.route('/user/<int:user_id>/bookings', methods=['GET'])
@require_roles('admin', 'trek_staff')
def user_bookings_summary(user_id):

    current_user = session.get('user')

    if not db.session.get(User, user_id):
        return jsonify({"error": "User not found"}), 404

    query = (
        select(
            func.count().label("total"),
            func.count().filter(
                Booking.status == BookingStatus.BOOKED
            ).label("booked"),
            func.count().filter(
                Booking.status == BookingStatus.CANCELLED
            ).label("cancelled"),
        )
        .select_from(Booking)
        .where(Booking.trekker_user_id == user_id)
    )

    if current_user["role"] == "trek_staff":
        query = (
            query.join(Trek)
            .where(Trek.staff_user_id == current_user["id"])
        )

    result = db.session.execute(query).one()

    return jsonify({
        "user_bookings_summary": {
            "total_bookings": result.total,
            "booked_bookings": result.booked,
            "cancelled_bookings": result.cancelled,
        }
    }), 200


# report routes

@summary_bp.route('/export', methods=['GET'])
@require_roles('trekker')
def request_export():
    """
    Request an export of the user's trek and booking history.
    This will trigger a background task to generate the report.
    """
    current_user = session.get('user')
    
    # Trigger the Celery task to generate the report
    task = send_report.delay(current_user['id'])
    
    return jsonify({'message': 'Report generation initiated. You will receive an email once it is ready.', 'task_id': task.id}), 202

@summary_bp.route('/export/<task_id>', methods=['GET'])
@require_roles('trekker')
def check_export_status(task_id):
    """
    Check the status of the export task.
    """
    task = send_report.AsyncResult(task_id)
    
    if task.state == 'SUCCESS':
        return Response(task.result, mimetype='text/csv', headers={
                "Content-Disposition": "attachment; filename=history.csv"
            })
    elif task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'status': str(task.info),  # Exception info
        }
    else:
        response = {
            'state': task.state,
        }
    
    return response, 200
