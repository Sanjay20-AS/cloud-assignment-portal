from datetime import datetime, timezone
import re
import uuid

ALLOWED_TYPES = {
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def utcnow():
    return datetime.now(timezone.utc)


def safe_filename(name: str) -> str:
    name = name.replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name[:120] or f"submission-{uuid.uuid4().hex}.bin"


def submission_status(submission: dict, assignment: dict) -> str:
    if submission.get("marks") is not None:
        return "graded"
    submitted = datetime.fromisoformat(submission["submitted_at"].replace("Z", "+00:00")) if isinstance(submission["submitted_at"], str) else submission["submitted_at"]
    due = datetime.fromisoformat(assignment["due_at"].replace("Z", "+00:00")) if isinstance(assignment["due_at"], str) else assignment["due_at"]
    return "late" if submitted > due else "submitted"
