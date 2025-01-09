from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum

class UserResponse(str, Enum):
    accept = "Accepted"
    reject = "Declined"

class GradingResult(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    application_id: int
    scholarship_id: int
    jury_id: str
    student_id: str
    grade: Optional[float] = None  # Grade is optional for rejected students
    reason: Optional[str] = None   # Reason is required for rejected students
    user_response: Optional[UserResponse] = Field(default=None)

class SubmissionCompleted(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    scholarship_id: int
