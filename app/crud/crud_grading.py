import os
import boto3
from sqlalchemy.orm import Session
from app.models.models import GradingResult, SubmissionCompleted
from app.schemas.schemas import UsersBulkRequest, UserResponse, User
from app.models.models import Application, ScholarshipJury
from fastapi import HTTPException
from app.core.config import settings

cognito_client = boto3.client('cognito-idp',
    region_name=os.getenv('AWS_REGION')
)

def save_grading_result(db: Session, token, application_id: int, scholarship_id: int, student_id: str, grade: float, reason: str):
    jury_id = token["sub"]

    # Check if the jury has already graded the student
    existing_result = db.query(GradingResult).filter(
        GradingResult.application_id == application_id,
        GradingResult.scholarship_id == scholarship_id,
        GradingResult.jury_id == jury_id,
        GradingResult.student_id == student_id
    ).first()

    if existing_result:
        return False

    grading_result = GradingResult(
        application_id=application_id,
        scholarship_id=scholarship_id,
        jury_id=jury_id,
        student_id=student_id,
        grade=grade,
        reason=reason
    )
    db.add(grading_result)
    db.commit()
    db.refresh(grading_result)

    return grading_result

def get_grading_results(db: Session, scholarship_id: int):
    return db.query(GradingResult).filter(GradingResult.scholarship_id == scholarship_id).all()

def get_grading_results_by_jury(db: Session, scholarship_id: int, jury_id: str):
    return db.query(GradingResult).filter(
        GradingResult.scholarship_id == scholarship_id,
        GradingResult.jury_id == jury_id
    ).all()

def save_grading_result(db: Session, token, application_id: int, scholarship_id: int, student_id: str, grade: float, reason: str):
    jury_id = token["sub"]

    # Check if the jury has already graded the student
    existing_result = db.query(GradingResult).filter(
        GradingResult.application_id == application_id,
        GradingResult.scholarship_id == scholarship_id,
        GradingResult.jury_id == jury_id,
        GradingResult.student_id == student_id
    ).first()

    if existing_result:
        return False

    # Save the grading result
    grading_result = GradingResult(
        application_id=application_id,
        scholarship_id=scholarship_id,
        jury_id=jury_id,
        student_id=student_id,
        grade=grade,
        reason=reason
    )
    db.add(grading_result)
    db.commit()
    db.refresh(grading_result)

    return grading_result

def save_scholarship_completed(db: Session, scholarship_id: int):
    submission_completed = SubmissionCompleted(
        scholarship_id=scholarship_id
    )
    db.add(submission_completed)
    db.commit()
    db.refresh(submission_completed)
    return submission_completed

def check_scholarship_completed(db: Session, scholarship_id: int):
    return db.query(SubmissionCompleted).filter(SubmissionCompleted.scholarship_id == scholarship_id).first()

def update_application_response(db: Session, application_id: int, user_response: UserResponse):
    db_application = db.query(GradingResult).filter(GradingResult.application_id == application_id).first()
    db_application.user_response = user_response 
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

def save_application(db: Session, scholarship_id: int, user_id: str, name: str):
    application = Application(
        scholarship_id=scholarship_id,
        user_id=user_id,
        name=name
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application

def save_scholarship_jury(db: Session, scholarship_id: int, juryamount: int):
    scholarship_jury = ScholarshipJury(
        scholarship_id=scholarship_id,
        juryamount=juryamount
    )
    db.add(scholarship_jury)
    db.commit()
    db.refresh(scholarship_jury)
    return scholarship_jury

def get_applications_by_scholarship(db: Session, scholarship_id: int):
    return db.query(Application).filter(Application.scholarship_id == scholarship_id).all()

def get_jury_amount_by_scholarship(db: Session, scholarship_id: int):
    scholarship_jury = db.query(ScholarshipJury).filter(ScholarshipJury.scholarship_id == scholarship_id).first()
    if scholarship_jury:
        return scholarship_jury.juryamount
    return None

async def get_users(user_ids: list):
    users = []
    for user_id in user_ids:
        try:
            user = await get_user_info(user_id)
            if user:
                users.append(user)
        except HTTPException:
            pass  # Skip users that are not found
    
    return users

async def get_user_info(user_id: str):
    try:
        response = cognito_client.admin_get_user(
            UserPoolId=settings.USER_POOL_ID,
            Username=user_id
        )
        
        attributes = {
            attr['Name']: attr['Value']
            for attr in response['UserAttributes']
        }

        groups_response = cognito_client.admin_list_groups_for_user(
            UserPoolId=settings.USER_POOL_ID,
            Username=user_id
        )
        
        return User(
            id=response['Username'],
            name=attributes.get('name', response['Username']),
            email=attributes.get('email', ''),
            groups=[group['GroupName'] for group in groups_response['Groups']]
        )
    except Exception:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
