from sqlalchemy.orm import Session
from app.models.models import Student, GradingResult
from app.schemas.schemas import StudentResult, Notification
from sqlmodel import select

def get_student_by_id(db: Session, student_id: int) -> Student:
    statement = select(Student).where(Student.id == student_id)
    result = db.exec(statement).first()
    return result

def save_grading_results(db: Session, results: list[StudentResult]):
    notifications = []

    for result in results:
        student = get_student_by_id(db, result.id)
        if not student:
            continue  # Skip if student doesn't exist

        grading_result = GradingResult(
            student_id=student.id,
            grade=result.grade,
            reason=result.reason
        )
        db.add(grading_result)

        # Prepare notification
        if result.reason:  # Rejected student
            notifications.append(Notification(
                student_id=student.id,
                name=student.name,
                email=student.email,
                status="Rejected",
                details=result.reason
            ))
        else:  # Accepted student
            notifications.append(Notification(
                student_id=student.id,
                name=student.name,
                email=student.email,
                status="Accepted",
                details=f"Grade: {result.grade}"
            ))

    db.commit()
    return notifications