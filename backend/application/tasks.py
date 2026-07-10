from .extensions import celery, db
from .models import User

@celery.task(name="add", bind=True)
def add(self, x, y):
    """A simple Celery task to add two numbers."""
    try:
        if x == 0 or y == 0:
            raise ValueError("Both x and y must be non-zero.")
    except ValueError as e:
        # Log the error or handle it as needed
        print(f"Error in add task: {e}")
        self.retry(exc=e, countdown=5, max_retries=3)  # Retry after 5 seconds, up to 3 times
    return x + y

@celery.task(name="task_create_user", bind=True)
def _create_user(self, username):
    """A Celery task to create a new user in the database."""
    try:
        # Create a new user instance
        new_user = User(username=username)
        db.session.add(new_user)
        db.session.commit()
        
    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error in create_user task: {e}")
        self.retry(exc=e, countdown=5, max_retries=3)  # Retry after 5 seconds, up to 3 times
    return f"User '{username}' created successfully."

@celery.task(name="print_hello")
def print_hello():
    """A simple Celery task to print a hello message."""
    print("Hello from Celery!")
    return "Hello from Celery!"

@celery.task(name="send_email", bind=True)
def send_email(self, recipient, subject, body):
    """A Celery task to send an email."""
    try:
        
        pass
    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error in send_email task: {e}")
        self.retry(exc=e, countdown=5, max_retries=3)  # Retry after 5 seconds, up to 3 times
    return f"Email sent to {recipient} successfully."