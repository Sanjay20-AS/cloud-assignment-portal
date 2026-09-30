-- Cloud-Based Student Assignment Submission & Feedback Portal
-- Run in Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null default 'Student',
  role text not null default 'student' check (role in ('student','teacher')),
  created_at timestamptz not null default now()
);

create table if not exists public.courses (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  description text not null default '',
  teacher_id uuid not null references public.profiles(id),
  created_at timestamptz not null default now()
);

create table if not exists public.assignments (
  id uuid primary key default gen_random_uuid(),
  course_id uuid not null references public.courses(id) on delete cascade,
  teacher_id uuid not null references public.profiles(id),
  title text not null,
  description text not null default '',
  due_at timestamptz not null,
  max_marks integer not null default 100 check (max_marks > 0 and max_marks <= 1000),
  allow_resubmission boolean not null default true,
  allow_late_submission boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.submissions (
  id uuid primary key default gen_random_uuid(),
  assignment_id uuid not null references public.assignments(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  original_filename text not null,
  storage_path text not null unique,
  content_type text not null,
  file_size bigint not null check (file_size > 0),
  version integer not null default 1 check (version > 0),
  marks integer,
  submitted_at timestamptz not null default now(),
  unique (assignment_id, student_id, version)
);

create table if not exists public.feedback (
  id uuid primary key default gen_random_uuid(),
  submission_id uuid not null references public.submissions(id) on delete cascade,
  teacher_id uuid not null references public.profiles(id),
  comment text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_assignments_course on public.assignments(course_id);
create index if not exists idx_assignments_teacher on public.assignments(teacher_id);
create index if not exists idx_submissions_student on public.submissions(student_id);
create index if not exists idx_submissions_assignment on public.submissions(assignment_id);
create index if not exists idx_feedback_submission on public.feedback(submission_id);

-- Automatically provision every newly registered account as a student.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, role)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', 'Student'), 'student')
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

-- RLS: the API uses the server-side service key, but these rules provide defense-in-depth
-- if you later expose Supabase Data API operations directly to the frontend.
alter table public.profiles enable row level security;
alter table public.courses enable row level security;
alter table public.assignments enable row level security;
alter table public.submissions enable row level security;
alter table public.feedback enable row level security;

drop policy if exists profiles_self on public.profiles;
create policy profiles_self on public.profiles for select to authenticated using (id = auth.uid());

drop policy if exists courses_authenticated_read on public.courses;
create policy courses_authenticated_read on public.courses for select to authenticated using (true);

drop policy if exists assignments_authenticated_read on public.assignments;
create policy assignments_authenticated_read on public.assignments for select to authenticated using (true);

drop policy if exists submissions_student_read on public.submissions;
create policy submissions_student_read on public.submissions for select to authenticated using (student_id = auth.uid());

drop policy if exists feedback_student_read on public.feedback;
create policy feedback_student_read on public.feedback for select to authenticated using (
  exists (select 1 from public.submissions s where s.id = submission_id and s.student_id = auth.uid())
);

-- Private bucket. The backend generates short-lived signed URLs.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'assignment-submissions', 'assignment-submissions', false, 10485760,
  array['application/pdf','application/zip','application/x-zip-compressed','text/plain','application/vnd.openxmlformats-officedocument.wordprocessingml.document']
)
on conflict (id) do update set public = false, file_size_limit = 10485760;

-- Storage RLS is intentionally restrictive because the FastAPI service is the trusted storage client.
drop policy if exists no_direct_submission_uploads on storage.objects;
create policy no_direct_submission_uploads on storage.objects for insert to authenticated
with check (false);

drop policy if exists no_direct_submission_reads on storage.objects;
create policy no_direct_submission_reads on storage.objects for select to authenticated
using (false);

-- Demo teacher setup:
-- 1. Register teacher@example.com through the same login page.
-- 2. Run the following UPDATE once.
-- UPDATE public.profiles SET role='teacher', full_name='Dr. Meera Kumar'
-- WHERE id=(SELECT id FROM auth.users WHERE email='teacher@example.com');
