from datetime import datetime, timezone
from typing import Annotated
import uuid

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .supabase_client import admin_client
from .auth import get_current_user, get_profile, require_role
from .schemas import AssignmentCreate, CourseCreate, GradeCreate, FeedbackCreate
from .utils import ALLOWED_TYPES, safe_filename, submission_status

app = FastAPI(title="Cloud Assignment Portal API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


def one(table: str, record_id: str):
    result = admin_client.table(table).select("*").eq("id", record_id).single().execute()
    if not result.data:
        raise HTTPException(404, f"{table[:-1].title() if table.endswith('s') else table} not found")
    return result.data


def course_or_404(course_id: str):
    return one("courses", course_id)


def assignment_or_404(assignment_id: str):
    return one("assignments", assignment_id)


@app.get("/health")
def health():
    return {"status": "ok", "service": "cloud-assignment-portal-api", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/me")
def me(profile=Depends(get_profile)):
    return profile


@app.get("/api/v1/courses")
def list_courses(profile=Depends(get_profile)):
    result = admin_client.table("courses").select("*").order("code").execute()
    return result.data or []


@app.post("/api/v1/courses")
def create_course(payload: CourseCreate, profile=Depends(require_role("teacher"))):
    result = admin_client.table("courses").insert({**payload.model_dump(), "teacher_id": profile["id"]}).execute()
    return result.data[0]


@app.get("/api/v1/assignments")
def list_assignments(
    course_id: str | None = Query(default=None),
    profile=Depends(get_profile),
):
    query = admin_client.table("assignments").select("*").order("due_at")
    if course_id:
        query = query.eq("course_id", course_id)
    result = query.execute()
    assignments = result.data or []
    if profile["role"] == "teacher":
        assignments = [a for a in assignments if a["teacher_id"] == profile["id"]]
    return assignments


@app.post("/api/v1/assignments")
def create_assignment(payload: AssignmentCreate, profile=Depends(require_role("teacher"))):
    course = course_or_404(payload.course_id)
    if course["teacher_id"] != profile["id"]:
        raise HTTPException(403, "You do not own this course")
    data = payload.model_dump(mode="json")
    data["teacher_id"] = profile["id"]
    result = admin_client.table("assignments").insert(data).execute()
    return result.data[0]


@app.get("/api/v1/assignments/{assignment_id}")
def get_assignment(assignment_id: str, profile=Depends(get_profile)):
    assignment = assignment_or_404(assignment_id)
    if profile["role"] == "teacher" and assignment["teacher_id"] != profile["id"]:
        raise HTTPException(403, "Not your assignment")
    return assignment


@app.post("/api/v1/assignments/{assignment_id}/submissions")
async def submit_assignment(
    assignment_id: str,
    upload: UploadFile = File(...),
    user=Depends(get_current_user),
    profile=Depends(get_profile),
):
    if profile["role"] != "student":
        raise HTTPException(403, "Only students can submit assignments")
    assignment = assignment_or_404(assignment_id)
    existing_result = (
        admin_client.table("submissions")
        .select("*")
        .eq("assignment_id", assignment_id)
        .eq("student_id", profile["id"])
        .order("version", desc=True)
        .execute()
    )
    existing = existing_result.data or []
    if existing and not assignment["allow_resubmission"]:
        raise HTTPException(409, "Resubmission is disabled for this assignment")
    now = datetime.now(timezone.utc)
    due = datetime.fromisoformat(assignment["due_at"].replace("Z", "+00:00"))
    if now > due and not assignment["allow_late_submission"]:
        raise HTTPException(409, "The assignment deadline has passed")
    if upload.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Unsupported file type. Use PDF, DOCX, ZIP or TXT.")
    content = await upload.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")

    version = (existing[0]["version"] + 1) if existing else 1
    filename = safe_filename(upload.filename or "submission.bin")
    object_path = f"{assignment_id}/{profile['id']}/{version}-{uuid.uuid4().hex}-{filename}"
    try:
        admin_client.storage.from_(settings.storage_bucket).upload(
            object_path, content, {"content-type": upload.content_type or "application/octet-stream", "upsert": "false"}
        )
    except Exception as exc:
        raise HTTPException(502, "Cloud file storage upload failed") from exc

    result = admin_client.table("submissions").insert({
        "assignment_id": assignment_id,
        "student_id": profile["id"],
        "original_filename": filename,
        "storage_path": object_path,
        "content_type": upload.content_type or "application/octet-stream",
        "file_size": len(content),
        "version": version,
        "submitted_at": now.isoformat(),
    }).execute()
    return result.data[0]


@app.get("/api/v1/submissions/my")
def my_submissions(profile=Depends(require_role("student"))):
    result = admin_client.table("submissions").select("*").eq("student_id", profile["id"]).order("submitted_at", desc=True).execute()
    submissions = result.data or []
    for submission in submissions:
        fb = admin_client.table("feedback").select("comment,created_at").eq("submission_id", submission["id"]).order("created_at", desc=True).limit(1).execute()
        submission["feedback"] = fb.data[0]["comment"] if fb.data else None
    return submissions


@app.get("/api/v1/assignments/{assignment_id}/submissions")
def teacher_submissions(assignment_id: str, profile=Depends(require_role("teacher"))):
    assignment = assignment_or_404(assignment_id)
    if assignment["teacher_id"] != profile["id"]:
        raise HTTPException(403, "Not your assignment")
    result = admin_client.table("submissions").select("*").eq("assignment_id", assignment_id).order("submitted_at", desc=True).execute()
    return result.data or []


@app.get("/api/v1/submissions/{submission_id}/download")
def download_submission(submission_id: str, profile=Depends(get_profile)):
    submission = one("submissions", submission_id)
    assignment = assignment_or_404(submission["assignment_id"])
    allowed = profile["id"] == submission["student_id"] or (profile["role"] == "teacher" and profile["id"] == assignment["teacher_id"])
    if not allowed:
        raise HTTPException(403, "You do not have access to this file")
    try:
        result = admin_client.storage.from_(settings.storage_bucket).create_signed_url(submission["storage_path"], 900)
        return {"url": result["signedURL"] if "signedURL" in result else result.get("signed_url")}
    except Exception as exc:
        raise HTTPException(502, "Could not create secure download link") from exc


@app.patch("/api/v1/submissions/{submission_id}/grade")
def grade_submission(submission_id: str, payload: GradeCreate, profile=Depends(require_role("teacher"))):
    submission = one("submissions", submission_id)
    assignment = assignment_or_404(submission["assignment_id"])
    if assignment["teacher_id"] != profile["id"]:
        raise HTTPException(403, "Not your submission to grade")
    if payload.marks > assignment["max_marks"]:
        raise HTTPException(422, "Marks exceed the assignment maximum")
    result = admin_client.table("submissions").update({"marks": payload.marks}).eq("id", submission_id).execute()
    if payload.feedback.strip():
        admin_client.table("feedback").insert({
            "submission_id": submission_id,
            "teacher_id": profile["id"],
            "comment": payload.feedback.strip(),
        }).execute()
    return result.data[0]


@app.get("/api/v1/submissions/{submission_id}/feedback")
def get_feedback(submission_id: str, profile=Depends(get_profile)):
    submission = one("submissions", submission_id)
    assignment = assignment_or_404(submission["assignment_id"])
    allowed = profile["id"] == submission["student_id"] or (profile["role"] == "teacher" and profile["id"] == assignment["teacher_id"])
    if not allowed:
        raise HTTPException(403, "Not authorized")
    result = admin_client.table("feedback").select("*, teacher:profiles(full_name)").eq("submission_id", submission_id).order("created_at").execute()
    return result.data or []


@app.post("/api/v1/submissions/{submission_id}/feedback")
def add_feedback(submission_id: str, payload: FeedbackCreate, profile=Depends(require_role("teacher"))):
    submission = one("submissions", submission_id)
    assignment = assignment_or_404(submission["assignment_id"])
    if assignment["teacher_id"] != profile["id"]:
        raise HTTPException(403, "Not authorized")
    result = admin_client.table("feedback").insert({"submission_id": submission_id, "teacher_id": profile["id"], "comment": payload.comment}).execute()
    return result.data[0]
