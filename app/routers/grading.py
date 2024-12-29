import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.models import Student
from app.schemas.schemas import Notification
from sqlmodel import select
from app.db.session import get_db
import pika
import json

router = APIRouter()

def send_to_rabbitmq(notifications: list):
    # Use RabbitMQ host from environment variables
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
    channel = connection.channel()

    # Declare the queues
    channel.queue_declare(queue='notification_queue', durable=True)  # For email worker
    channel.queue_declare(queue='grading_queue', durable=True)      # For grading consumer

    # Publish each notification to both queues
    for notification in notifications:
        # Send to notification_queue
        channel.basic_publish(
            exchange='',
            routing_key='notification_queue',
            body=json.dumps(notification.dict()),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        # Send to grading_queue
        channel.basic_publish(
            exchange='',
            routing_key='grading_queue',
            body=json.dumps(notification.dict()),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    connection.close()

@router.post("/submit_results")
def submit_results(db: Session = Depends(get_db)):
    # Fetch all dummy students from the database
    students = db.execute(select(Student)).scalars().all()

    # Prepare notifications
    notifications = []
    for student in students:
        status = "Accepted" if student.id % 2 == 1 else "Rejected"
        details = f"Grade: {15 + student.id}" if status == "Accepted" else "Not qualified"

        notifications.append(Notification(
            student_id=student.id,
            name=student.name,
            email=student.email,
            status=status,
            details=details
        ))

    # Send notifications to RabbitMQ
    send_to_rabbitmq(notifications)

    return {"message": "Dummy results submitted successfully and notifications queued."}
