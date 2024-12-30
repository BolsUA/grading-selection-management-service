from sqlalchemy.orm import Session
from app.models.models import GradingResult

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