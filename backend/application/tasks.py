from .extensions import celery, db, mail, Message
from .export import export_data, get_daily_mail_data, get_monthly_report_data
from .models import User, UserRoleName
from flask import render_template, current_app as app
from sqlalchemy import select

@celery.task(name="send_report", bind=True, max_retries=3, default_retry_delay=3)
def send_report(self, user_id):
    """A Celery task to send a report to a user."""
    try:
        export_result = export_data(app, user_id)
        return export_result
    except Exception as e:
        print(f"Error generating report: {e}")
        raise self.retry(exc=e, countdown=3)

@celery.task(name="send_daily_email", bind=True)     
def send_daily_email(self):
    """
    Send a daily email to the users with upcoming treks and bookings for the next day.
    """
    for user_id in db.session.scalars(select(User.id).where(User.role == UserRoleName.TREKKER)).all():
        rows = get_daily_mail_data(user_id)
        if not rows:
            print(f"No upcoming treks for user_id: {user_id}")
            continue  # No upcoming treks for tomorrow

        # Fetch user email
        user = db.session.get(User, user_id)
        if not user:
            print(f"User with id {user_id} not found.")
            continue # User not found

        # Send email using Celery task
        msg = Message(
            subject="Upcoming Treks and Bookings for Tomorrow",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email],
            html=render_template('daily_email.html', user=user, treks=rows)
        )
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error sending email to user {user_id}: {e}")
    print("Mail sending task completed.")

# send montly report to admin via email
@celery.task(name="send_monthly_email", bind=True)
def send_monthly_email(self):
    """
    Send a monthly email to the admin with all the treks and bookings for the month.
    """
    # Fetch admin email
    admin_user = db.session.scalars(select(User).where(User.role == UserRoleName.ADMIN)).first()
    if not admin_user:
        print("Admin user not found.")
        return  # Admin user not found

    # Generate monthly report data
    report_data, year_month = get_monthly_report_data()

    # Send email using Celery task
    msg = Message(
        subject="Monthly Trekking Report",
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[admin_user.email],
        html=render_template('monthly_email.html', **report_data, year_month=year_month)
    )
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending monthly report email to admin: {e}")
