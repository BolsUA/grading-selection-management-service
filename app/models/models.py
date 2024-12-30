from sqlmodel import SQLModel, Field
from typing import Optional

class GradingResult(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    scholarship_id: int
    student_id: str
    grade: Optional[float] = None  # Grade is optional for rejected students
    reason: Optional[str] = None   # Reason is required for rejected students
