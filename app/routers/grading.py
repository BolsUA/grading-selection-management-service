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
from app.models.models import GradingResult, UserResponse
from app.schemas.schemas import GradeRequest, Notification, SubmitRequest, UserAppResponseNotification
from app.db.session import get_db
from app.core.config import settings
from jwt import PyJWKClient
import boto3
import json
import logging
from apscheduler.schedulers.background import BackgroundScheduler

router = APIRouter()

oauth2_scheme = HTTPBearer()


TO_GRADING_QUEUE_URL = str(os.getenv("TO_GRADING_QUEUE_URL"))
APP_GRADING_QUEUE_URL = str(os.getenv("APP_GRADING_QUEUE_URL"))
AWS_ACESS_KEY_ID = str(os.getenv("AWS_ACCESS_KEY_ID"))
AWS_SECRET_ACCESS_KEY = str(os.getenv("AWS_SECRET_ACCESS_KEY"))
REGION = str(os.getenv("REGION"))

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
        notification_dict = notification.dict()
        
        # Send to notification_queue
        channel.basic_publish(
            exchange='',
            routing_key='notification_queue',
            body=json.dumps(notification_dict),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        # Send to grading_queue
        channel.basic_publish(
            exchange='',
            routing_key='grading_queue',
            body=json.dumps(notification_dict),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    connection.close()
    print("Connection to RabbitMQ closed")

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/grades")
def get_grades(
    token: TokenDep,
    scholarship_id: int,
    db: Session = Depends(get_db)
):
    jury_id = token["sub"]
    results = crud_grading.get_grading_results_by_jury(db, scholarship_id, jury_id)

    return results

@router.post("/grade")
def grade_student(
    token: TokenDep,
    grade_data: GradeRequest,
    db: Session = Depends(get_db),
):
    grade = grade_data.grade
    application_id = grade_data.application_id
    scholarship_id = grade_data.scholarship_id
    student_id = grade_data.student_id

    finalGrade = grade if isinstance(grade, float) else None
    reason = grade if isinstance(grade, str) else None

    result = crud_grading.save_grading_result(db, token, application_id, scholarship_id, student_id, finalGrade, reason)

    if not result:
        raise HTTPException(status_code=400, detail="Student already graded.")

    return {"message": "Student graded successfully."}

@router.post("/submit")
def submit_results(
    _: TokenDep,
    submit_data: SubmitRequest,
    db: Session = Depends(get_db)
):
    if crud_grading.check_scholarship_completed(db, submit_data.scholarship_id):
        return {"message": "Results already submitted for this scholarship."}

    notifications = []
    message = { "applications": [] }

    # Fetch all grading results for the scholarship
    grading_results = crud_grading.get_grading_results(db, submit_data.scholarship_id)

    if not grading_results:
        return {"message": "No grading results found for this scholarship."}

    # Group grading results by application_id
    grouped_results = {}
    for result in grading_results:
        grouped_results.setdefault(result.application_id, []).append(result)

    final_results = []
    for application_id, results in grouped_results.items():
        # Check if all juries have graded this application
        total_juries = crud_grading.get_jury_amount_by_scholarship(db, submit_data.scholarship_id)
        all_juries_graded = len(results) == total_juries
        if not all_juries_graded:
            return {"message": "Not all juries have graded all applications."}

        # Determine the final status of the application
        rejected_reasons = [result.reason for result in results if result.grade is None]
        if rejected_reasons:
            # Application is rejected if any jury rejected it
            final_results.append({
                "application_id": application_id,
                "student_id": results[0].student_id,
                "status": "Rejected",
                "reason": "; ".join(rejected_reasons)  # Combine all rejection reasons
            })
        else:
            # Compute average grade for accepted applications
            average_grade = sum(result.grade for result in results) / len(results)
            final_results.append({
                "application_id": application_id,
                "student_id": results[0].student_id,
                "status": "Accepted",
                "grade": average_grade
            })

    # Notify students about their results
    student_ids = [result["student_id"] for result in final_results]
    students = crud_grading.get_users(student_ids)
    # students = requests.post(
    #     f"http://host.docker.internal:8000/people/internal/users/bulk",
    #     json={"user_ids": student_ids}
    # ).json()

    for result in final_results:
        student = next((student for student in students if student["id"] == result["student_id"]), None)
        if not student:
            continue

        status = result["status"]
        details = (
            f"Grade: {result['grade']:.2f}" if "grade" in result else result["reason"]
        )

        message["applications"].append({
            "application_id": result["application_id"],
            "status": status,
            "grade": result.get("grade", None),
            "reason": result.get("reason", None)
        })

        notifications.append(Notification(
            student_id=student["id"],
            name=student["name"],
            email=student["email"],
            status=status,
            details=details
        ))

    # Send notifications to RabbitMQ
    send_to_sqs(message)
    send_to_rabbitmq(notifications)
    crud_grading.save_scholarship_completed(db, submit_data.scholarship_id)
    return {"message": "Results submitted successfully."}

@router.put("/{application_id}/response", response_model=GradingResult)
def update_application_response(_: TokenDep, application_id: int, user_response: UserResponse, db: Session = Depends(get_db)):
    response = False if user_response == UserResponse.reject else True
    send_to_rabbitmq([UserAppResponseNotification(application_id=application_id, response=response)])
    return crud_grading.update_application_response(db, application_id, user_response)

@router.get("/applications/{scholarship_id}")
def get_applications_by_scholarship(
    scholarship_id: int,
    db: Session = Depends(get_db)
):
    applications = crud_grading.get_applications_by_scholarship(db, scholarship_id)
    return applications

### SQS HANDLING ###

sqs = boto3.client(
    'sqs',
    aws_access_key_id=AWS_ACESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION
)

def process_message(message):
    body = json.loads(message['Body'])
    # Create an application based on the received message and commit it to the db
    crud_grading.save_scholarship_jury(
        db=next(get_db()), 
        scholarship_id=body['scholarship_id'], 
        juryamount=len(body['jury_ids'])
    )
    
    for application in body['applications']:
        crud_grading.save_application(
            db=next(get_db()),
            scholarship_id=application['scholarship_id'],
            user_id=application['user_id'],
            name=application['name']
        )
    

def send_to_sqs(message: dict):
    response = sqs.send_message(
        QueueUrl=APP_GRADING_QUEUE_URL,
        MessageBody=json.dumps(message),
    )
    print(f"Message sent to SQS: {response['MessageId']}")
    return response

def receive_message():
    response = sqs.receive_message(
        QueueUrl=TO_GRADING_QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5,
    )
    messages = response.get('Messages', [])
    for message in messages:
        body = json.loads(message['Body'])
        logging.info(f"Received message: {body}")
        process_message(message)
        # Delete the message from the queue
        # sqs.delete_message(
        #     QueueUrl=TO_GRADING_QUEUE_URL,
        #     ReceiptHandle=message['ReceiptHandle']
        # )

scheduler = BackgroundScheduler()
scheduler.add_job(receive_message, 'interval', seconds=2, max_instances=10)
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
scheduler.start()
