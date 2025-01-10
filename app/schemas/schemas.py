from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class UserResponse(str, Enum):
    accept = "Accepted"
    reject = "Declined"

class Notification(BaseModel):
    student_id: str
    name: str
    email: str
    status: str  # "Accepted" or "Rejected"
    details: Optional[str] = None  # Either grade or rejection reason

class UserAppResponseNotification(BaseModel):
    application_id: int
    response: bool

class GradeRequest(BaseModel):
    application_id: int
    scholarship_id: int
    student_id: str
    grade: Union[float, str]

class SubmitRequest(BaseModel):
    scholarship_id: int

class UserBasic(BaseModel):
    id: str
    name: str

class User(UserBasic):
    email: str
    groups: List[str]

class UsersBulkRequest(BaseModel):
    user_ids: List[str]
