from sqlalchemy.orm import Session
from app.models.models import GradingResult, SubmissionCompleted
from app.models.models import Application, ScholarshipJury

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
