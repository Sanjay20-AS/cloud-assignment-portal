# ☁️ Cloud-Based Student Assignment Submission & Feedback Portal

An industry-oriented cloud computing project demonstrating authentication, RBAC, REST APIs, managed PostgreSQL, private object storage, secure file downloads, deployment, containerization, testing, and GitHub-based CI.

## 1. What this project demonstrates

| Cloud concept | Implementation |
|---|---|
| Cloud-hosted application | Vercel frontend + Render FastAPI backend |
| Cloud authentication | Supabase Auth (email/password) |
| Authorization / RBAC | FastAPI dependencies + `profiles.role` |
| Cloud database | Supabase PostgreSQL |
| Cloud object storage | Private Supabase Storage bucket |
| REST API | FastAPI `/api/v1/*` |
| File upload | Multipart upload -> private bucket |
| File download | Short-lived signed URL |
| Assignment management | Teacher create/list/view assignments |
| Feedback | Teacher grading + feedback table |
| Scalability | Stateless API, managed DB/storage, CDN/static frontend |
| Security | JWT validation, service-key isolation, RLS, MIME/size validation, signed URLs, CORS |
| Testing | Pytest + GitHub Actions |
| DevOps | Dockerfile + GitHub CI + Git-based deployment |

## 2. Architecture

```text
                         Internet
                            |
              +-------------+-------------+
              |                           |
        Vercel / Static UI           Render / FastAPI
           React + Vite                  REST API
              |                           |
              | JWT                       | service-side access
              +-------------+-------------+
                            |
                     Supabase Platform
              +-------------+-------------+
              |             |             |
           Auth          Postgres       Storage
        users/JWT       metadata       private files
                                          |
                                   signed download URL
```

### Request flow: student submission

1. Student signs in using Supabase Auth.
2. Browser receives an access token.
3. Browser sends `Authorization: Bearer <token>` to FastAPI.
4. FastAPI validates the token using Supabase Auth.
5. FastAPI reads the student's role from `profiles`.
6. API checks assignment deadline/resubmission rules and file type/size.
7. API uploads the file to a **private** Storage bucket.
8. API writes submission metadata to PostgreSQL.
9. Teacher later receives a short-lived signed URL for an authorized download.

## 3. Free-tier strategy

The reference deployment is designed for a student project without paid cloud infrastructure:

- Supabase Free: Auth + PostgreSQL + Storage.
- Vercel Hobby: React static frontend.
- Render Free: FastAPI backend.
- GitHub: source control and CI.

Free tiers have limits and can change. Check the providers' current pricing before deployment. The repository also supports local development using the Supabase CLI/Docker, so the application does not depend on paid resources.

## 4. Folder structure

```text
cloud-assignment-portal/
├── backend/
│   ├── app/
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── supabase_client.py
│   │   └── utils.py
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api.js
│   │   ├── main.jsx
│   │   ├── styles.css
│   │   └── supabase.js
│   ├── package.json
│   └── .env.example
├── supabase/
│   ├── schema.sql
│   └── seed_demo.sql
├── docs/
├── .github/workflows/ci.yml
├── docker-compose.local.yml
└── README.md
```

## 5. Supabase setup

### A. Create project

Create a Supabase project on the Free plan.

### B. Run database setup

Open **SQL Editor** and run:

```text
supabase/schema.sql
```

This creates:

- `profiles`
- `courses`
- `assignments`
- `submissions`
- `feedback`
- indexes
- new-user profile trigger
- RLS policies
- private `assignment-submissions` Storage bucket

### C. Create demo users

Register these through the application:

```text
Teacher: teacher@example.com
Student: student@example.com
Password: Password123!
```

For a classroom demo, use dummy accounts only.

The trigger creates new accounts as students. After registering the teacher, run:

```sql
UPDATE public.profiles
SET role='teacher', full_name='Dr. Meera Kumar'
WHERE id=(SELECT id FROM auth.users WHERE email='teacher@example.com');
```

Then run:

```text
supabase/seed_demo.sql
```

### D. Authentication setting for a simple classroom demo

For the easiest demo, configure email/password authentication so registration can immediately establish a session. If email confirmation is enabled, students must confirm their email before logging in.

## 6. Backend setup

```bash
cd backend
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Copy environment file:

```bash
copy .env.example .env
```

Edit `.env`:

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_OR_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
STORAGE_BUCKET=assignment-submissions
FRONTEND_URL=http://localhost:5173
MAX_UPLOAD_MB=10
ENVIRONMENT=development
```

**Never commit `.env` or the service-role key.**

Run:

```bash
uvicorn app.main:app --reload --port 8000
```

API documentation:

```text
http://localhost:8000/docs
```

## 7. Frontend setup

```bash
cd frontend
npm install
copy .env.example .env
```

Set:

```env
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_OR_ANON_KEY
VITE_API_URL=http://localhost:8000
```

Run:

```bash
npm run dev
```

Open the Vite URL shown in the terminal.

## 8. Local-only alternative

If you do not want to use a hosted Supabase project during development, use the Supabase CLI with Docker:

```bash
supabase init
supabase start
```

Then apply `supabase/schema.sql` to the local project and use the local API URL/keys printed by `supabase start` in the environment files.

This gives you local versions of Auth, Postgres and Storage while keeping the application architecture the same. Docker is therefore a useful local alternative to paid cloud services.

## 9. API endpoints

### Authentication

Authentication is handled by Supabase Auth. FastAPI validates the Supabase access token.

### Application API

```text
GET    /health
GET    /api/v1/me
GET    /api/v1/courses
POST   /api/v1/courses
GET    /api/v1/assignments
POST   /api/v1/assignments
GET    /api/v1/assignments/{assignment_id}
POST   /api/v1/assignments/{assignment_id}/submissions
GET    /api/v1/submissions/my
GET    /api/v1/assignments/{assignment_id}/submissions
GET    /api/v1/submissions/{submission_id}/download
PATCH  /api/v1/submissions/{submission_id}/grade
GET    /api/v1/submissions/{submission_id}/feedback
POST   /api/v1/submissions/{submission_id}/feedback
```

## 10. Security model

### Authentication

Supabase Auth issues the access token. FastAPI validates the token server-side.

### Authorization

A profile has exactly one application role:

```text
student
teacher
```

Teacher-only endpoints use a FastAPI role dependency.

### Service key isolation

The Supabase service-role key is used only by FastAPI. It is never included in React's environment variables.

### File security

Assignment files are stored in a private bucket. The API verifies whether the requesting user owns the submission or teaches the related assignment before creating a 15-minute signed URL.

### Upload validation

The backend checks:

- allowed MIME type
- maximum 10 MB size
- safe filename
- assignment deadline
- resubmission rule
- role

### Database security

Postgres RLS is enabled on application tables. Storage is private and direct client access is intentionally restricted because the FastAPI service is the trusted storage client.

## 11. Scalability explanation for viva

The system is designed as a stateless API:

- React frontend can be served through a CDN.
- FastAPI instances do not keep uploaded files on local disk.
- Uploaded files are stored in object storage.
- Submission metadata is in managed PostgreSQL.
- Multiple FastAPI instances can serve requests without sharing local state.
- Database indexes support common assignment/submission lookups.
- Signed URLs prevent the API from becoming a file-streaming bottleneck.

A future production version could add a queue for virus scanning, asynchronous notifications, caching, database connection pooling and background workers.

## 12. Testing

Run:

```bash
cd backend
pytest -q
```

The repository also includes GitHub Actions CI that installs Python dependencies and executes the test suite.

## 13. GitHub proof-of-work checklist

For a strong GitHub submission, include:

- architecture diagram
- screenshots of student and teacher dashboards
- API Swagger screenshot
- Supabase database/storage screenshots with secrets hidden
- deployment URLs in the README
- test results
- GitHub Actions badge
- sample API requests/responses
- security design section
- cloud architecture explanation
- demo video/GIF if allowed
- commit history showing incremental development

Do **not** upload:

```text
.env
Supabase service-role key
real student information
real assignment files
passwords
private tokens
```

## 14. Suggested demo sequence

1. Open deployed frontend.
2. Sign in as teacher.
3. Show course and assignment.
4. Create a new assignment.
5. Sign in as student in another browser/incognito window.
6. Upload a dummy PDF.
7. Show submission metadata in Supabase Postgres.
8. Show the object in the private Storage bucket.
9. Return to teacher dashboard.
10. Open the submission and download through the signed URL.
11. Enter marks and feedback.
12. Return to student dashboard.
13. Show marks and feedback.
14. Open `/docs` and demonstrate the REST API.
15. Show GitHub Actions test results.

## 15. Important limitation for the student demo

This is a course project, not a production university LMS. The teacher account is provisioned manually for safety. In a production system, staff identity would normally be controlled by institutional identity/SSO and administrative workflows.
