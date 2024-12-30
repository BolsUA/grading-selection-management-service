import os
from typing import Annotated, Dict, Union
from app.crud import crud_grading
import jwt
import pika
import json
import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.schemas.schemas import GradeRequest, Notification, SubmitRequest
from app.db.session import get_db
from app.core.config import settings
from jwt import PyJWKClient

router = APIRouter()

oauth2_scheme = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    token = credentials.credentials
    try:
        # Fetch public keys from AWS Cognito
        jwks_client = PyJWKClient(settings.COGNITO_KEYS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and validate the token
        payload = jwt.decode(token, signing_key.key, algorithms=["RS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

TokenDep = Annotated[Dict, Depends(verify_token)]

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

@router.post("/grade")
def grade_student(
    _: TokenDep,
    grade_data: GradeRequest,
    db: Session = Depends(get_db),
):
    grade = grade_data.grade
    scholarship_id = grade_data.scholarship_id
    student_id = grade_data.student_id

    finalGrade = grade if isinstance(grade, float) else None
    reason = grade if isinstance(grade, str) else None

    crud_grading.save_grading_result(db, scholarship_id, student_id, finalGrade, reason)

    return {"message": "Student graded successfully."}

@router.post("/submit")
def submit_results(
    _: TokenDep,
    submit_data: SubmitRequest,
    db: Session = Depends(get_db)
):
    notifications = []

    grading_results = crud_grading.get_grading_results(db, submit_data.scholarship_id)
    student_ids = [result.student_id for result in grading_results]
    # TODO: Change the URL to the correct domain
    students = requests.post(f"http://host.docker.internal:8000/people/internal/users/bulk", json={"user_ids": student_ids}).json()

    for result in grading_results:
        student = next((student for student in students if student["id"] == result.student_id), None)
        if student is None:
            continue

        status = "Accepted" if result.grade else "Rejected"
        details = f"Grade: {result.grade}" if result.grade else result.reason

        notifications.append(Notification(
            student_id=result.student_id,
            name=student["name"],
            email=student["email"],
            status=status,
            details=details
        ))

    send_to_rabbitmq(notifications)

    return {"message": "Results submitted successfully."}