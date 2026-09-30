import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { supabase } from './supabase';
import { api } from './api';
import './styles.css';

function Auth({ onReady }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ email:'student@example.com', password:'Password123!', full_name:'' });
  const [error, setError] = useState('');
  async function submit(e) {
    e.preventDefault(); setError('');
    try {
      if (mode === 'register') {
        const { data, error } = await supabase.auth.signUp({ email:form.email, password:form.password, options:{data:{full_name:form.full_name}} });
        if (error) throw error;
        if (!data.session) { setError('Registration successful. Check email confirmation, then sign in.'); return; }
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email:form.email, password:form.password });
        if (error) throw error;
      }
      onReady();
    } catch (err) { setError(err.message); }
  }
  return <div className="auth-shell"><div className="card auth-card"><div className="brand">☁️ AssignmentCloud</div><h1>{mode==='login'?'Sign in':'Create student account'}</h1><p className="muted">Cloud-Based Student Assignment Submission & Feedback Portal</p>
    <form onSubmit={submit}>
      {mode==='register' && <input required placeholder="Full name" value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/>} 
      <input required type="email" placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/>
      <input required minLength="8" type="password" placeholder="Password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>
      <button>{mode==='login'?'Sign in':'Register as student'}</button>
    </form>
    {error && <div className="alert">{error}</div>}
    <button className="link-btn" onClick={()=>setMode(mode==='login'?'register':'login')}>{mode==='login'?'New student? Register':'Already registered? Sign in'}</button>
  </div></div>
}

function Layout({profile, children, onLogout}) {
  return <>
    <header>
      <div className="brand">☁️ AssignmentCloud</div>
      <div>
        {profile?.full_name || 'Student'}
        <span className="pill">{profile?.role || 'student'}</span>
        <button className="ghost" onClick={onLogout}>Logout</button>
      </div>
    </header>

    <main>{children}</main>
  </>;
}

function StudentDashboard() {
  const [assignments,setAssignments]=useState([]), [subs,setSubs]=useState([]), [file,setFile]=useState({}), [msg,setMsg]=useState('');
  async function load(){ setAssignments(await api('/api/v1/assignments')); setSubs(await api('/api/v1/submissions/my')); }
  useEffect(()=>{load()},[]);
  async function submit(id){ if(!file[id]) return setMsg('Choose a file first.'); const fd=new FormData(); fd.append('upload',file[id]); try{await api(`/api/v1/assignments/${id}/submissions`,{method:'POST',body:fd});setMsg('Assignment uploaded successfully.');load()}catch(e){setMsg(e.message)} }
  async function download(id){const x=await api(`/api/v1/submissions/${id}/download`);window.open(x.url,'_blank')}
  return <section><div className="hero"><div><h1>Student dashboard</h1><p>Submit work, track versions, and review teacher feedback.</p></div></div>{msg&&<div className="alert">{msg}</div>}<h2>Assignments</h2><div className="grid">{assignments.map(a=><div className="card" key={a.id}><div className="row"><h3>{a.title}</h3><span className="pill">{a.max_marks} marks</span></div><p>{a.description}</p><small>Due: {new Date(a.due_at).toLocaleString()}</small><div className="upload"><input type="file" accept=".pdf,.docx,.zip,.txt" onChange={e=>setFile({...file,[a.id]:e.target.files[0]})}/><button onClick={()=>submit(a.id)}>Submit</button></div></div>)}</div><h2>My submissions</h2><div className="card table-wrap"><table><thead><tr><th>File</th><th>Version</th><th>Submitted</th><th>Status</th><th>Marks</th><th>Feedback</th><th></th></tr></thead><tbody>{subs.map(s=><tr key={s.id}><td>{s.original_filename}</td><td>v{s.version}</td><td>{new Date(s.submitted_at).toLocaleString()}</td><td><span className="pill">{s.marks==null?'submitted':'graded'}</span></td><td>{s.marks ?? '—'}</td><td>{s.feedback || 'No feedback yet'}</td><td><button className="ghost" onClick={()=>download(s.id)}>Download</button></td></tr>)}</tbody></table></div></section>
}

function TeacherDashboard() {
  const [courses,setCourses]=useState([]), [assignments,setAssignments]=useState([]), [selected,setSelected]=useState(null), [subs,setSubs]=useState([]), [grade,setGrade]=useState({});
  const [newA,setNewA]=useState({course_id:'',title:'',description:'',due_at:'',max_marks:100,allow_resubmission:true,allow_late_submission:false});
  async function load(){const [c,a]=await Promise.all([api('/api/v1/courses'),api('/api/v1/assignments')]);setCourses(c);setAssignments(a);if(!newA.course_id&&c[0])setNewA(x=>({...x,course_id:c[0].id}))}
  useEffect(()=>{load()},[]);
  async function create(e){e.preventDefault();await api('/api/v1/assignments',{method:'POST',body:JSON.stringify({...newA,due_at:new Date(newA.due_at).toISOString()})});setNewA(x=>({...x,title:'',description:''}));load()}
  async function view(a){setSelected(a);setSubs(await api(`/api/v1/assignments/${a.id}/submissions`))}
  async function saveGrade(s){await api(`/api/v1/submissions/${s.id}/grade`,{method:'PATCH',body:JSON.stringify({marks:Number(grade[s.id]?.marks),feedback:grade[s.id]?.feedback||''})});view(selected)}
  async function download(id){const x=await api(`/api/v1/submissions/${id}/download`);window.open(x.url,'_blank')}
  return <section><div className="hero"><div><h1>Teacher dashboard</h1><p>Create assignments and grade student submissions.</p></div></div><div className="split"><div className="card"><h2>Create assignment</h2><form onSubmit={create}><select required value={newA.course_id} onChange={e=>setNewA({...newA,course_id:e.target.value})}>{courses.map(c=><option key={c.id} value={c.id}>{c.code} — {c.name}</option>)}</select><input required placeholder="Assignment title" value={newA.title} onChange={e=>setNewA({...newA,title:e.target.value})}/><textarea placeholder="Description" value={newA.description} onChange={e=>setNewA({...newA,description:e.target.value})}/><label>Deadline<input required type="datetime-local" value={newA.due_at} onChange={e=>setNewA({...newA,due_at:e.target.value})}/></label><label>Maximum marks<input type="number" min="1" value={newA.max_marks} onChange={e=>setNewA({...newA,max_marks:e.target.value})}/></label><label><input type="checkbox" checked={newA.allow_resubmission} onChange={e=>setNewA({...newA,allow_resubmission:e.target.checked})}/> Allow resubmission</label><label><input type="checkbox" checked={newA.allow_late_submission} onChange={e=>setNewA({...newA,allow_late_submission:e.target.checked})}/> Allow late submission</label><button>Create assignment</button></form></div><div className="card"><h2>Your assignments</h2>{assignments.map(a=><button className="list-item" key={a.id} onClick={()=>view(a)}><strong>{a.title}</strong><span>{new Date(a.due_at).toLocaleString()}</span></button>)}</div></div>{selected&&<div className="card"><div className="row"><h2>Submissions: {selected.title}</h2><button className="ghost" onClick={()=>setSelected(null)}>Close</button></div>{subs.length===0?<p className="muted">No submissions yet.</p>:<div className="table-wrap"><table><thead><tr><th>Student</th><th>File</th><th>Version</th><th>Marks</th><th>Feedback</th><th></th></tr></thead><tbody>{subs.map(s=><tr key={s.id}><td>{s.student_id.slice(0,8)}…</td><td>{s.original_filename}</td><td>v{s.version}</td><td><input className="small-input" type="number" value={grade[s.id]?.marks ?? s.marks ?? ''} onChange={e=>setGrade({...grade,[s.id]:{...grade[s.id],marks:e.target.value}})}/></td><td><textarea className="small-area" value={grade[s.id]?.feedback ?? ''} placeholder="Feedback" onChange={e=>setGrade({...grade,[s.id]:{...grade[s.id],feedback:e.target.value}})}/></td><td><button onClick={()=>download(s.id)}>File</button><button onClick={()=>saveGrade(s)}>Save</button></td></tr>)}</tbody></table></div>}</div>}</section>
}

function App(){const [session,setSession]=useState(null),[profile,setProfile]=useState(null),[loading,setLoading]=useState(true);async function ready(){const {data:{session}}=await supabase.auth.getSession();setSession(session);if(session)setProfile(await api('/api/v1/me'));setLoading(false)}useEffect(()=>{ready();const {data:{subscription}}=supabase.auth.onAuthStateChange(()=>ready());return()=>subscription.unsubscribe()},[]);async function logout(){await supabase.auth.signOut();setSession(null);setProfile(null)}if(loading)return <div className="center">Loading…</div>;if(!session)return <Auth onReady={ready}/>;return <Layout profile={profile} onLogout={logout}>{profile?.role==='teacher'?<TeacherDashboard/>:<StudentDashboard/>}</Layout>}
createRoot(document.getElementById('root')).render(<App/>);
