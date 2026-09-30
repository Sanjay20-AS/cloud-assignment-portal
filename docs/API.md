# REST API examples

All protected requests use:

```http
Authorization: Bearer <SUPABASE_ACCESS_TOKEN>
```

## Create assignment

```http
POST /api/v1/assignments
Content-Type: application/json

{
  "course_id": "COURSE_UUID",
  "title": "Cloud Architecture Report",
  "description": "Explain a cloud deployment architecture.",
  "due_at": "2026-12-15T18:00:00Z",
  "max_marks": 100,
  "allow_resubmission": true,
  "allow_late_submission": false
}
```

## Upload submission

```http
POST /api/v1/assignments/ASSIGNMENT_UUID/submissions
Content-Type: multipart/form-data

upload=<assignment.pdf>
```

## Grade

```http
PATCH /api/v1/submissions/SUBMISSION_UUID/grade
Content-Type: application/json

{
  "marks": 86,
  "feedback": "Good architecture diagram. Explain the security boundary in more detail."
}
```
