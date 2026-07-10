from application import create_app, celery
from application.tasks import _create_user, add, _create_user
from application.extensions import mail

app = create_app()

@app.route('/add/<int:x>/<int:y>/')
def index(x, y):
    task = add.delay(x, y)  # Call the Celery task asynchronously
    return f"Task submitted with ID: {task.id}"

@app.route('/create_user/<username>/')
def create_user(username):
    task = _create_user.delay(username)
    return f"<a href='/task_result/{task.id}'>Task submitted with ID: {task.id}</a>"

@app.route('/task_status/<task_id>/')
def task_status(task_id):
    task = celery.AsyncResult(task_id)
    return f"Task status: {task.status}"

@app.route('/task_result/<task_id>/')
def task_result(task_id):
    task = celery.AsyncResult(task_id)
    return f"Task result: {task.result}"

@app.route('/send_email/')
def send_email():
    recipient = "develop.test.0.0.0.0@gmail.com"
    subject = "Test Email"
    body = "This is a test email sent from the Celery task."
    mail.send_message(subject=subject, recipients=[recipient], body=body)
    return f"Email sent to {recipient} successfully."

if __name__ == '__main__':
    app.run(debug=True)