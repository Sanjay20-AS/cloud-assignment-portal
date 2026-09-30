from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class CourseCreate(BaseModel):
    code: str = Field(min_length=2, max_length=20)
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)

class AssignmentCreate(BaseModel):
    course_id: str
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(default="", max_length=3000)
    due_at: datetime
    max_marks: int = Field(default=100, ge=1, le=1000)
    allow_resubmission: bool = True
    allow_late_submission: bool = False

class GradeCreate(BaseModel):
    marks: int = Field(ge=0, le=1000)
    feedback: str = Field(default="", max_length=5000)

class FeedbackCreate(BaseModel):
    comment: str = Field(min_length=1, max_length=5000)

class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    role: str

class AssignmentOut(BaseModel):
    id: str
    course_id: str
    title: str
    description: str
    due_at: datetime
    max_marks: int
    allow_resubmission: bool
    allow_late_submission: bool
    created_at: datetime

class SubmissionOut(BaseModel):
    id: str
    assignment_id: str
    student_id: str
    original_filename: str
    content_type: str
    file_size: int
    version: int
    submitted_at: datetime
    status: str
    marks: int | None = None
    feedback: str | None = None
