from sqlalchemy.orm import Session
from app.models.models import GradingResult

def save_grading_result(db: Session, scholarship_id: int, student_id: str, grade: float, reason: str):
    grading_result = GradingResult(
        scholarship_id=scholarship_id,
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

# def save_grading_results(db: Session, results: list[StudentResult]):
#     notifications = []

#     for result in results:
#         student = get_student_by_id(db, result.id)
#         if not student:
#             continue  # Skip if student doesn't exist

#         grading_result = GradingResult(
#             student_id=student.id,
#             grade=result.grade,
#             reason=result.reason
#         )
#         db.add(grading_result)

#         # Prepare notification
#         if result.reason:  # Rejected student
#             notifications.append(Notification(
#                 student_id=student.id,
#                 name=student.name,
#                 email=student.email,
#                 status="Rejected",
#                 details=result.reason
#             ))
#         else:  # Accepted student
#             notifications.append(Notification(
#                 student_id=student.id,
#                 name=student.name,
#                 email=student.email,
#                 status="Accepted",
#                 details=f"Grade: {result.grade}"
#             ))

#     db.commit()
#     return notifications