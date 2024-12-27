from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.sql import func
import enum

class Student(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    email: str

class GradingResult(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    grade: Optional[float] = None  # Grade is optional for rejected students
    reason: Optional[str] = None   # Reason is required for rejected students
