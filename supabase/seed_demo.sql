-- Run after creating/promoting teacher@example.com.
do $$
declare teacher_uuid uuid;
course_uuid uuid;
begin
  select id into teacher_uuid from public.profiles where id=(select id from auth.users where email='teacher@example.com') and role='teacher';
  if teacher_uuid is null then raise exception 'Promote teacher@example.com to teacher first'; end if;
  insert into public.courses(code,name,description,teacher_id)
  values ('CSB301','Cloud Computing','Cloud architecture, storage, APIs and deployment.',teacher_uuid)
  on conflict(code) do update set teacher_id=excluded.teacher_id
  returning id into course_uuid;
  insert into public.assignments(course_id,teacher_id,title,description,due_at,max_marks,allow_resubmission,allow_late_submission)
  values(course_uuid,teacher_uuid,'Cloud Architecture Report','Submit a PDF report explaining the architecture of a cloud-hosted student portal.',now()+interval '14 days',100,true,false);
end $$;
