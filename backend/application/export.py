import csv
from io import StringIO
from datetime import date, timedelta
from sqlalchemy import func, select
from .extensions import db
from .models import Booking, Trek, User

def convert_to_csv(rows, headers):
    output = StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=headers,
        extrasaction="ignore"
    )

    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue()


def export_data(app,user_id=None):
    """
    Export the history of treks, bookings, and users based on the role of the user.
    """
    stmt = (
    select(
        Booking.trekker_user_id.label("user_id"),
        Trek.title.label("trek_title"),
        Trek.location.label("trek_location"),
        Trek.start_date.label("trek_start_date"),
        Trek.end_date.label("trek_end_date"),
        Booking.created_at.label("booking_created_at"),
        Booking.status.value.label("booking_status"),
    )
    .join(Booking.trek)
    .where(Booking.trekker_user_id == user_id)
    )

    rows = db.session.execute(stmt).mappings().all()

    rows = [
        {
            **row,
            "booking_status": row["booking_status"].value,
        }
        for row in rows
    ]

    headers = [
        "user_id",
        "trek_title",
        "trek_location",
        "trek_start_date",
        "trek_end_date",
        "booking_created_at",
        "booking_status",
    ]

    csv_data = convert_to_csv(rows, headers)

    return csv_data

# daily email, for upcoming treks and bookings for the next day, for current trekker
def get_daily_mail_data(user_id):
    """
    Fetch the upcoming treks and bookings for the next day for the current trekker.
    """
    tomorrow = date.today() + timedelta(days=1)
    stmt = (
        select(
            Booking.trekker_user_id.label("user_id"),
            Trek.title.label("trek_title"),
            Trek.location.label("trek_location"),
            Trek.start_date.label("trek_start_date"),
            Trek.end_date.label("trek_end_date"),
        )
        .join(Trek, Booking.trek_id == Trek.id)
        .where(
            Booking.trekker_user_id == user_id,
            Trek.start_date == tomorrow,
        )
    )
    rows = db.session.execute(stmt).mappings().all()
    return rows



# Admin recieves a monthly email with all the treks and bookings for the month, for all the trekkers
def get_monthly_report_data():
    """
    Get the data to send a monthly email to the admin with all the treks and bookings for the month.

    Generate the monthly activity report.

    Returns:
    {
        "total_treks": ...,
        "total_participants": ...,
        "popular_treks": [
            {"name": "...", "bookings": ...},
            ...
        ]
    }
    """

    today = date.today()
    first_day_of_current = today.replace(day=1)
    last_day_of_previous = first_day_of_current - timedelta(days=1)
    first_day_of_month = last_day_of_previous.replace(day=1)
    last_day_of_month = last_day_of_previous
    year_month = first_day_of_month.strftime("%B %Y")  # e.g., "January 2024"

    
    
    # Number of treks conducted
    total_treks = db.session.scalar(
        select(func.count())
        .select_from(Trek)
        .where(
            Trek.start_date >= first_day_of_month,
            Trek.start_date <= last_day_of_month,
        )
    )

    # Number of unique trekkers who participated
    total_participants = db.session.scalar(
        select(func.count(func.distinct(Booking.trekker_user_id)))
        .join(Trek, Booking.trek_id == Trek.id)
        .where(
            Trek.start_date >= first_day_of_month,
            Trek.start_date <= last_day_of_month,
        )
    )

    # Top 5 Popular treks (ordered by booking count)
    popular_treks = db.session.execute(
        select(
            Trek.title.label("name"),
            func.count(Booking.id).label("bookings"),
        )
        .join(Booking, Booking.trek_id == Trek.id)
        .where(
            Trek.start_date >= first_day_of_month,
            Trek.start_date <= last_day_of_month,
        )
        .group_by(Trek.id, Trek.title)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
    ).mappings().all()

    return {
        "total_treks": total_treks,
        "total_participants": total_participants,
        "popular_treks": popular_treks,
    }, year_month