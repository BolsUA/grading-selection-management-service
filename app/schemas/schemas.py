from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class StudentResult(BaseModel):
    id: int
    grade: Optional[float] = None  # Grade is optional for rejected students
    reason: Optional[str] = None   # Reason is required for rejected students

class Notification(BaseModel):
    student_id: int
    name: str
    email: str
    status: str  # "Accepted" or "Rejected"
    details: Optional[str] = None  # Either grade or rejection reason
