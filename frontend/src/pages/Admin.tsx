import { useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api';
import { Card, Stat, Empty } from '../components/UI';

type Analytics = {
  students: { total: number; assessed: number; unassessed: number };
  faculty: number;
  industry_partners: number;
  readiness: number;
  assessment: { attempts: number; average_score: number };
  skills: { total_assessed: number; verified: number };
  evidence: { submitted: number; verified: number; pending: number; rejected: number };
  opportunities: { total: number; internships: number; research: number };
  applications: {
    total: number; applied: number; under_review: number; shortlisted: number;
    selected: number; ongoing: number; done: number;
  };
  industry_demand: { skill: string; requests: number }[];
  skill_gaps: { skill: string; average_gap: number; students: number }[];
};

type Student = {
  student_id: number;
  name: string;
  email: string;
  education: string;
  year_degree: string;
  target_role: string | null;
  readiness: number;
  verified_skill_count: number;
  core_gaps: { skill: string; current: number; required: number; gap: number }[];
};


type OutcomeAnalytics = {
  internships: {
    total: number;
    not_started: number;
    ongoing: number;
    completed: number;
    cancelled: number;
    average_progress: number;
    mentor_feedback: number;
    milestones: number;
    completed_milestones: number;
  };
  learning_programs: {
    programs: number;
    enrollments: number;
    enrolled: number;
    in_progress: number;
    completed: number;
    cancelled: number;
    certificate_programs: number;
    types: { type: string; count: number }[];
  };
  collaborations: {
    total: number;
    planned: number;
    active: number;
    on_hold: number;
    completed: number;
    cancelled: number;
    milestones: number;
    completed_milestones: number;
    outputs: number;
    verified_outputs: number;
  };
  faculty_opportunities: {
    total: number;
    applications: number;
    accepted: number;
    under_review: number;
    rejected: number;
    types: { type: string; count: number }[];
  };
  documents: {
    total: number;
    pending: number;
    verified: number;
    rejected: number;
  };
  applications: {
    total: number;
    applied: number;
    under_review: number;
    shortlisted: number;
    selected: number;
    ongoing: number;
    done: number;
  };
  opportunity_types: { type: string; count: number }[];
};

type Verification = {
  id: number;
  user_id: number;
  email: string;
  organisation_name: string;
  industry: string;
  ayush_focus: string;
  status: string;
  submitted_at?: string | null;
  notes?: string;
};

const barStyle = (value: number) => ({
  width: `${Math.max(0, Math.min(100, value))}%`,
  height: 8,
  borderRadius: 999,
  background: '#2563eb',
});

function SectionTitle({ title, body }: { title: string; body?: string }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <h2 style={{ margin: 0, fontSize: 20 }}>{title}</h2>
      {body && <p className="muted" style={{ margin: '5px 0 0' }}>{body}</p>}
    </div>
  );
}

export default function Admin({
  page,
  setPage,
}: {
  page: string;
  setPage: (p: string) => void;
}) {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [outcomes, setOutcomes] = useState<OutcomeAnalytics | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [verification, setVerification] = useState<Verification[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [skills, setSkills] = useState<{ id: number; name: string; category: string }[]>([]);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [analyticsData, outcomeData, studentData, verificationData, userData, skillData, opportunityData] = await Promise.all([
        api<Analytics>('/admin/analytics'),
        api<OutcomeAnalytics>('/admin/outcome-analytics'),
        api<Student[]>('/academician/students'),
        api<Verification[]>('/admin/company-verification'),
        api<any[]>('/admin/users'),
        api<{ id: number; name: string; category: string }[]>('/skills'),
        api<any[]>('/opportunities'),
      ]);
      setAnalytics(analyticsData);
      setOutcomes(outcomeData);
      setStudents(Array.isArray(studentData) ? studentData : []);
      setVerification(Array.isArray(verificationData) ? verificationData : []);
      setUsers(Array.isArray(userData) ? userData : []);
      setSkills(Array.isArray(skillData) ? skillData : []);
      setOpportunities(Array.isArray(opportunityData) ? opportunityData : []);
    } catch (e: any) {
      setError(e.message || 'Unable to load institution analytics.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function reviewCompany(userId: number, status: string) {
    setError('');
    setNotice('');
    try {
      await api(`/admin/company-verification/${userId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      setNotice(`Company verification marked ${status}.`);
      await load();
    } catch (e: any) {
      setError(e.message || 'Could not update company verification.');
    }
  }

  const filteredStudents = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return students;
    return students.filter((student) =>
      [student.name, student.email, student.education, student.year_degree, student.target_role || '']
        .join(' ')
        .toLowerCase()
        .includes(q),
    );
  }, [students, search]);

  if (loading && !analytics) return <Card>Loading institution intelligence…</Card>;

  if (!analytics) {
    return <Card><div className="error">{error || 'Institution analytics unavailable.'}</div></Card>;
  }

  const a = analytics;

  function dashboard() {
    return (
      <div className="stack">
        <div className="page-heading">
          <div>
            <div className="eyebrow">INSTITUTION INTELLIGENCE</div>
            <h1>AYUSH Institution Dashboard</h1>
            <p className="muted">Monitor student capability, skill development, verification, industry demand and placement activity.</p>
          </div>
        </div>

        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}

        <div className="stats">
          <Stat label="Total Students" value={a.students.total} sub={`${a.students.assessed} assessed`} />
          <Stat label="Students Assessed" value={a.students.assessed} sub={`${a.students.unassessed} not assessed`} />
          <Stat label="Skills Verified" value={a.skills.verified} sub={`${a.skills.total_assessed} assessed skill records`} />
          <Stat label="Avg. Readiness" value={`${a.readiness}%`} sub="Across current student profiles" />
        </div>

        <div className="two-col">
          <Card>
            <SectionTitle title="Skill Development" body="Live counts from student assessment and verification data." />
            {[
              ['Total enrolled', a.students.total],
              ['Took assessment', a.students.assessed],
              ['Evidence submitted', a.evidence.submitted],
              ['Skills verified', a.evidence.verified],
            ].map(([label, value]) => (
              <div className="gap-mini" key={String(label)}>
                <strong>{label}</strong><span>{value}</span>
              </div>
            ))}
          </Card>

          <Card>
            <SectionTitle title="Assessment Analytics" body="Server-recorded assessment attempts and scores." />
            <div className="stats" style={{ marginBottom: 0 }}>
              <Stat label="Submitted attempts" value={a.assessment.attempts} />
              <Stat label="Average score" value={`${a.assessment.average_score}%`} />
            </div>
          </Card>
        </div>

        <div className="two-col">
          <Card>
            <SectionTitle title="Evidence Verification" />
            {[
              ['Submitted', a.evidence.submitted],
              ['Verified', a.evidence.verified],
              ['Pending', a.evidence.pending],
              ['Rejected', a.evidence.rejected],
            ].map(([label, value]) => (
              <div className="gap-mini" key={String(label)}>
                <strong>{label}</strong><span>{value}</span>
              </div>
            ))}
          </Card>
          <Card>
            <SectionTitle title="Placements & Internships" body="Application pipeline from the live opportunity database." />
            {[
              ['Applied', a.applications.applied],
              ['Under Review', a.applications.under_review],
              ['Shortlisted', a.applications.shortlisted],
              ['Selected', a.applications.selected],
              ['Ongoing', a.applications.ongoing],
              ['Done', a.applications.done],
            ].map(([label, value]) => (
              <div className="gap-mini" key={String(label)}>
                <strong>{label}</strong><span>{value}</span>
              </div>
            ))}
          </Card>
        </div>

        <div className="two-col">
          <Card>
            <SectionTitle title="Top Institutional Skill Gaps" body="Aggregated from students' core target-role requirements." />
            {a.skill_gaps.length ? a.skill_gaps.slice(0, 6).map((item) => (
              <div key={item.skill} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <strong>{item.skill}</strong>
                  <span className="muted">{item.students} students · {item.average_gap} pt avg gap</span>
                </div>
                <div style={{ marginTop: 7, background: '#e9eef5', borderRadius: 999, height: 8 }}>
                  <div style={barStyle(item.average_gap)} />
                </div>
              </div>
            )) : <Empty title="No core skill gaps" body="Student target roles and assessments will populate this section." />}
          </Card>

          <Card>
            <SectionTitle title="Industry Demand — Most Requested Skills" body="Counted from requirements on posted AYUSH opportunities." />
            {a.industry_demand.length ? a.industry_demand.slice(0, 6).map((item) => (
              <div key={item.skill} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <strong>{item.skill}</strong><span className="muted">{item.requests} request{item.requests === 1 ? '' : 's'}</span>
                </div>
                <div style={{ marginTop: 7, background: '#e9eef5', borderRadius: 999, height: 8 }}>
                  <div style={barStyle((item.requests / Math.max(1, a.industry_demand[0]?.requests || 1)) * 100)} />
                </div>
              </div>
            )) : <Empty title="No opportunity demand yet" body="Publish AYUSH opportunities with required skills to populate this section." />}
          </Card>
        </div>


        {outcomes && (
          <Card>
            <SectionTitle
              title="AYUSH Ecosystem Outcomes"
              body="Live participation and completion signals from internships, learning, collaborations and verified documents."
            />
            <div className="stats">
              <Stat label="Internships" value={outcomes.internships.total} sub={`${outcomes.internships.completed} completed`} />
              <Stat label="Learning Enrollments" value={outcomes.learning_programs.enrollments} sub={`${outcomes.learning_programs.completed} completed`} />
              <Stat label="Collaborations" value={outcomes.collaborations.total} sub={`${outcomes.collaborations.completed} completed`} />
              <Stat label="Verified Documents" value={outcomes.documents.verified} sub={`${outcomes.documents.pending} pending`} />
            </div>
          </Card>
        )}

        <Card>
          <SectionTitle title="Institution Snapshot" />
          <div className="tags">
            <span>{a.faculty} academicians</span>
            <span>{a.industry_partners} industry partners</span>
            <span>{a.opportunities.total} opportunities</span>
            <span>{a.opportunities.internships} internships</span>
            <span>{a.opportunities.research} research opportunities</span>
          </div>
        </Card>
      </div>
    );
  }

  function studentsPage() {
    return (
      <div className="stack">
        <div className="page-heading">
          <div><div className="eyebrow">STUDENT ANALYTICS</div><h1>Students</h1><p className="muted">Review institution-wide AYUSH student readiness, assessed skills and core gaps.</p></div>
        </div>
        {error && <div className="error">{error}</div>}
        <Card>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search students, programme or target AYUSH role…" style={{ width: '100%', boxSizing: 'border-box', padding: 12, border: '1px solid #d9e1e9', borderRadius: 9, marginBottom: 16 }} />
          {filteredStudents.length ? filteredStudents.map((student) => (
            <div key={student.student_id} style={{ padding: '16px 0', borderBottom: '1px solid #edf1f5' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
                <div>
                  <strong style={{ fontSize: 16 }}>{student.name}</strong>
                  <div className="muted">{student.email}</div>
                  <div className="muted">{student.education || 'Programme not specified'} · {student.year_degree || 'Year not specified'}</div>
                  <div style={{ marginTop: 7 }}>{student.target_role || 'No target AYUSH role selected'}</div>
                </div>
                <div style={{ minWidth: 190 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Readiness</span><strong>{student.readiness}%</strong></div>
                  <div style={{ marginTop: 7, background: '#e9eef5', borderRadius: 999, height: 8 }}><div style={barStyle(student.readiness)} /></div>
                  <div className="muted" style={{ marginTop: 8 }}>{student.verified_skill_count} verified skills · {student.core_gaps.length} core gaps</div>
                </div>
              </div>
            </div>
          )) : <Empty title="No students found" body="Try a different search term." />}
        </Card>
      </div>
    );
  }

  function skillAnalytics() {
    return (
      <div className="stack">
        <div className="page-heading"><div><div className="eyebrow">SKILL INTELLIGENCE</div><h1>Skill Analytics</h1><p className="muted">Compare institutional skill gaps with actual AYUSH industry demand.</p></div></div>
        <div className="two-col">
          <Card><SectionTitle title="Institutional Core Gaps" />{a.skill_gaps.map((x) => <div className="gap-mini" key={x.skill}><div><strong>{x.skill}</strong><div className="muted">Average gap: {x.average_gap} points</div></div><span>{x.students} students</span></div>)}</Card>
          <Card><SectionTitle title="AYUSH Industry Demand" />{a.industry_demand.map((x) => <div className="gap-mini" key={x.skill}><strong>{x.skill}</strong><span>{x.requests} opportunities</span></div>)}</Card>
        </div>
      </div>
    );
  }

  function placements() {
    return (
      <div className="stack">
        <div className="page-heading"><div><div className="eyebrow">PLACEMENT & INTERNSHIP ANALYTICS</div><h1>Placements</h1><p className="muted">Track the AYUSH opportunity and application pipeline across the institution.</p></div></div>
        <div className="stats">
          <Stat label="Opportunities" value={a.opportunities.total} />
          <Stat label="Internships" value={a.opportunities.internships} />
          <Stat label="Applications" value={a.applications.total} />
          <Stat label="Selected" value={a.applications.selected} />
        </div>
        <Card><SectionTitle title="Application Pipeline" />{[
          ['Applied', a.applications.applied], ['Under Review', a.applications.under_review], ['Shortlisted', a.applications.shortlisted], ['Selected', a.applications.selected], ['Ongoing', a.applications.ongoing], ['Done', a.applications.done],
        ].map(([label, value]) => <div className="gap-mini" key={String(label)}><strong>{label}</strong><span>{value}</span></div>)}</Card>
      </div>
    );
  }

  function companyVerification() {
    return (
      <div className="stack">
        <div className="page-heading"><div><div className="eyebrow">INDUSTRY GOVERNANCE</div><h1>Company Verification</h1><p className="muted">Review AYUSH organisation verification requests submitted by industry users.</p></div></div>
        {notice && <div className="success-banner">✓ {notice}</div>}
        {error && <div className="error">{error}</div>}
        <Card>
          {verification.length ? verification.map((item) => (
            <div key={item.id} style={{ padding: '18px 0', borderBottom: '1px solid #edf1f5' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 18, flexWrap: 'wrap' }}>
                <div>
                  <strong style={{ fontSize: 16 }}>{item.organisation_name || 'Unnamed organisation'}</strong>
                  <div className="muted">{item.email}</div>
                  <div style={{ marginTop: 6 }}>{item.industry || 'Industry not specified'}</div>
                  <div className="muted">AYUSH focus: {item.ayush_focus || 'Not specified'}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span className="tag">{item.status}</span>
                  {item.status === 'Pending Review' && <>
                    <button className="primary" onClick={() => reviewCompany(item.user_id, 'Verified')}>Approve</button>
                    <button className="secondary" onClick={() => reviewCompany(item.user_id, 'Needs More Information')}>Request info</button>
                    <button className="secondary" onClick={() => reviewCompany(item.user_id, 'Rejected')}>Reject</button>
                  </>}
                </div>
              </div>
            </div>
          )) : <Empty title="No company verification requests" body="Submitted AYUSH organisation verification requests will appear here." />}
        </Card>
      </div>
    );
  }

  function usersPage() {
    const counts = users.reduce((acc: Record<string, number>, u) => {
      acc[u.role] = (acc[u.role] || 0) + 1;
      return acc;
    }, {});
    return (
      <div className="stack">
        <div className="page-heading"><div><div className="eyebrow">USER ADMINISTRATION</div><h1>Users</h1><p className="muted">Institution-wide SkillNova accounts across the AYUSH ecosystem.</p></div></div>
        <div className="stats">
          <Stat label="Students" value={counts.student || 0} />
          <Stat label="Academicians" value={counts.academician || 0} />
          <Stat label="Industry" value={counts.company || 0} />
          <Stat label="Admins" value={counts.admin || 0} />
        </div>
        <Card>
          <SectionTitle title="Registered Users" body="Live account records from the platform database." />
          {users.length ? users.map((u) => (
            <div key={u.id} className="gap-mini">
              <div><strong>{u.name || 'Profile not completed'}</strong><div className="muted">{u.email}</div></div>
              <span className="tag">{u.role === 'company' ? 'Industry' : u.role}</span>
            </div>
          )) : <Empty title="No users found" body="Registered SkillNova accounts will appear here." />}
        </Card>
      </div>
    );
  }

  function companiesPage() {
    const companies = users.filter((u) => u.role === 'company');
    return (
      <div className="stack">
        <div className="page-heading"><div><div className="eyebrow">INDUSTRY DIRECTORY</div><h1>Companies</h1><p className="muted">AYUSH organisations participating in internships, research and hiring.</p></div></div>
        <div className="stats">
          <Stat label="Industry Accounts" value={companies.length} />
          <Stat label="Verified" value={verification.filter((v) => v.status === 'Verified').length} />
          <Stat label="Pending Review" value={verification.filter((v) => v.status === 'Pending Review').length} />
          <Stat label="Opportunities" value={opportunities.filter((o) => o.owner_role === 'company').length} />
        </div>
        <Card>
          <SectionTitle title="AYUSH Industry Partners" body="Company details and verification state are loaded from the database." />
          {companies.length ? companies.map((u) => {
            const v = verification.find((x) => x.user_id === u.id);
            return <div key={u.id} className="gap-mini">
              <div><strong>{u.name || 'Organisation profile not completed'}</strong><div className="muted">{u.email}</div></div>
              <span className="tag">{v?.status || 'Not Submitted'}</span>
            </div>;
          }) : <Empty title="No industry accounts" body="AYUSH industry organisations will appear after registration." />}
        </Card>
      </div>
    );
  }

  function academiciansPage() {
    const academics = users.filter((u) => u.role === 'academician');
    return (
      <div className="stack">
        <div className="page-heading"><div><div className="eyebrow">ACADEMIC DIRECTORY</div><h1>Academicians</h1><p className="muted">Faculty participating in AYUSH skill verification, research and mentoring.</p></div></div>
        <div className="stats">
          <Stat label="Academicians" value={academics.length} />
          <Stat label="Research Opportunities" value={opportunities.filter((o) => o.owner_role === 'academician' && (o.opportunity_type || '').toLowerCase().includes('research')).length} />
          <Stat label="Academic Opportunities" value={opportunities.filter((o) => o.owner_role === 'academician').length} />
          <Stat label="Verified Skills" value={a.skills.verified} />
        </div>
        <Card>
          <SectionTitle title="AYUSH Academic Community" body="Faculty accounts connected to the verification and research workflow." />
          {academics.length ? academics.map((u) => (
            <div key={u.id} className="gap-mini">
              <div><strong>{u.name || 'Academic profile not completed'}</strong><div className="muted">{u.email}</div></div>
              <span className="tag">Academician</span>
            </div>
          )) : <Empty title="No academicians found" body="Registered academician accounts will appear here." />}
        </Card>
      </div>
    );
  }

  function skillsPage() {
    const categories = skills.reduce((acc: Record<string, number>, s) => {
      acc[s.category] = (acc[s.category] || 0) + 1;
      return acc;
    }, {});
    return (
      <div className="stack">
        <div className="page-heading"><div><div className="eyebrow">AYUSH SKILL TAXONOMY</div><h1>Skills</h1><p className="muted">The competency vocabulary used for assessments, skill gaps and opportunity requirements.</p></div></div>
        <div className="stats">
          <Stat label="Skills" value={skills.length} />
          <Stat label="Categories" value={Object.keys(categories).length} />
          <Stat label="Assessed Records" value={a.skills.total_assessed} />
          <Stat label="Verified Records" value={a.skills.verified} />
        </div>
        <Card>
          <SectionTitle title="AYUSH Competency Catalogue" body="Live skills from the shared SkillNova taxonomy." />
          {skills.length ? skills.map((s) => <div key={s.id} className="gap-mini"><strong>{s.name}</strong><span className="tag">{s.category}</span></div>) : <Empty title="No skills found" body="The AYUSH skill taxonomy is empty." />}
        </Card>
      </div>
    );
  }

  function opportunitiesPage() {
    return (
      <div className="stack">
        <div className="page-heading"><div><div className="eyebrow">AYUSH OPPORTUNITY DIRECTORY</div><h1>Opportunities</h1><p className="muted">Institution-wide internships, research projects and industry opportunities.</p></div></div>
        <div className="stats">
          <Stat label="All Opportunities" value={opportunities.length} />
          <Stat label="Internships" value={a.opportunities.internships} />
          <Stat label="Research" value={a.opportunities.research} />
          <Stat label="Applications" value={a.applications.total} />
        </div>
        <Card>
          <SectionTitle title="Published AYUSH Opportunities" body="Opportunities are loaded from the live opportunity database." />
          {opportunities.length ? opportunities.map((o) => <div key={o.id} style={{padding:'16px 0',borderBottom:'1px solid #edf1f5'}}><div style={{display:'flex',justifyContent:'space-between',gap:16,flexWrap:'wrap'}}><div><strong>{o.title}</strong><div className="muted">{o.owner_name || 'Organisation'} · {o.opportunity_type} · {o.location}</div><div style={{marginTop:6}}>{o.requirements?.length || 0} required skills</div></div><span className="tag">{o.owner_role === 'company' ? 'Industry' : 'Academia'}</span></div></div>) : <Empty title="No opportunities" body="Published AYUSH opportunities will appear here." />}
        </Card>
      </div>
    );
  }

  function analyticsPage() {
    const o = outcomes;
    return (
      <div className="stack">
        <div className="page-heading">
          <div>
            <div className="eyebrow">INSTITUTIONAL OUTCOME ANALYTICS</div>
            <h1>Analytics</h1>
            <p className="muted">
              Track how AYUSH students move from assessment and skill development into
              learning, internships, collaborations and verified professional evidence.
            </p>
          </div>
        </div>

        <div className="stats">
          <Stat label="Assessment Attempts" value={a.assessment.attempts} />
          <Stat label="Average Score" value={`${a.assessment.average_score}%`} />
          <Stat label="Selected Applications" value={a.applications.selected} />
          <Stat label="Completed Applications" value={a.applications.done} />
        </div>

        <div className="two-col">
          <Card>
            <SectionTitle
              title="Internship Outcomes"
              body="Lifecycle records created after student selection."
            />
            {o ? [
              ['Total internships', o.internships.total],
              ['Not started', o.internships.not_started],
              ['Ongoing', o.internships.ongoing],
              ['Completed', o.internships.completed],
              ['Average progress', `${o.internships.average_progress}%`],
              ['Mentor feedback records', o.internships.mentor_feedback],
              ['Completed milestones', `${o.internships.completed_milestones}/${o.internships.milestones}`],
            ].map(([label, value]) => (
              <div className="gap-mini" key={String(label)}>
                <strong>{label}</strong><span>{value}</span>
              </div>
            )) : <Empty title="Internship analytics unavailable" body="The internship lifecycle endpoint has not returned data yet." />}
          </Card>

          <Card>
            <SectionTitle
              title="Industry Learning"
              body="Training, certification, workshop and mentorship participation."
            />
            {o ? [
              ['Programs published', o.learning_programs.programs],
              ['Total enrollments', o.learning_programs.enrollments],
              ['Enrolled', o.learning_programs.enrolled],
              ['In progress', o.learning_programs.in_progress],
              ['Completed', o.learning_programs.completed],
              ['Certificate programs', o.learning_programs.certificate_programs],
            ].map(([label, value]) => (
              <div className="gap-mini" key={String(label)}>
                <strong>{label}</strong><span>{value}</span>
              </div>
            )) : <Empty title="Learning analytics unavailable" body="Published AYUSH learning programs will populate this section." />}
          </Card>
        </div>

        <div className="two-col">
          <Card>
            <SectionTitle
              title="Academia–Industry Collaborations"
              body="Structured faculty/industry collaborations and their outputs."
            />
            {o ? [
              ['Total collaborations', o.collaborations.total],
              ['Active', o.collaborations.active],
              ['Planned', o.collaborations.planned],
              ['Completed', o.collaborations.completed],
              ['Completed milestones', `${o.collaborations.completed_milestones}/${o.collaborations.milestones}`],
              ['Outputs', o.collaborations.outputs],
              ['Verified outputs', o.collaborations.verified_outputs],
            ].map(([label, value]) => (
              <div className="gap-mini" key={String(label)}>
                <strong>{label}</strong><span>{value}</span>
              </div>
            )) : <Empty title="Collaboration analytics unavailable" body="Collaboration records will appear after faculty/industry work begins." />}
          </Card>

          <Card>
            <SectionTitle
              title="Professional Evidence"
              body="Student documents and evidence moving through institutional verification."
            />
            {o ? [
              ['Documents submitted', o.documents.total],
              ['Pending review', o.documents.pending],
              ['Verified', o.documents.verified],
              ['Rejected', o.documents.rejected],
              ['Verified skill records', a.skills.verified],
              ['Evidence pending', a.evidence.pending],
            ].map(([label, value]) => (
              <div className="gap-mini" key={String(label)}>
                <strong>{label}</strong><span>{value}</span>
              </div>
            )) : <Empty title="Document analytics unavailable" body="Student portfolio documents will populate this section." />}
          </Card>
        </div>

        <div className="two-col">
          <Card>
            <SectionTitle
              title="Faculty Engagement"
              body="Faculty-facing AYUSH opportunities and application outcomes."
            />
            {o ? [
              ['Faculty opportunities', o.faculty_opportunities.total],
              ['Faculty applications', o.faculty_opportunities.applications],
              ['Accepted', o.faculty_opportunities.accepted],
              ['Under review', o.faculty_opportunities.under_review],
              ['Rejected', o.faculty_opportunities.rejected],
            ].map(([label, value]) => (
              <div className="gap-mini" key={String(label)}>
                <strong>{label}</strong><span>{value}</span>
              </div>
            )) : <Empty title="Faculty analytics unavailable" body="Faculty opportunity activity will appear here." />}
          </Card>

          <Card>
            <SectionTitle
              title="Student Opportunity Pipeline"
              body="Current application progression across AYUSH opportunities."
            />
            {[
              ['Applied', a.applications.applied],
              ['Under Review', a.applications.under_review],
              ['Shortlisted', a.applications.shortlisted],
              ['Selected', a.applications.selected],
              ['Ongoing', a.applications.ongoing],
              ['Done', a.applications.done],
            ].map(([label, value]) => (
              <div className="gap-mini" key={String(label)}>
                <strong>{label}</strong><span>{value}</span>
              </div>
            ))}
          </Card>
        </div>

        {o && (
          <div className="two-col">
            <Card>
              <SectionTitle title="Learning Program Mix" body="Published AYUSH learning formats." />
              {o.learning_programs.types.length
                ? o.learning_programs.types.map((x) => (
                    <div className="gap-mini" key={x.type}>
                      <strong>{x.type}</strong><span>{x.count}</span>
                    </div>
                  ))
                : <Empty title="No learning programs yet" body="Industry partners can publish AYUSH learning programs from the Industry portal." />}
            </Card>

            <Card>
              <SectionTitle title="Faculty Opportunity Mix" body="Types of academia–industry opportunities being offered." />
              {o.faculty_opportunities.types.length
                ? o.faculty_opportunities.types.map((x) => (
                    <div className="gap-mini" key={x.type}>
                      <strong>{x.type}</strong><span>{x.count}</span>
                    </div>
                  ))
                : <Empty title="No faculty opportunities yet" body="Publish faculty-facing AYUSH opportunities to populate this section." />}
            </Card>
          </div>
        )}

        <div className="two-col">
          <Card>
            <SectionTitle title="Institutional Core Skill Gaps" />
            {a.skill_gaps.length
              ? a.skill_gaps.map((x) => (
                  <div className="gap-mini" key={x.skill}>
                    <div><strong>{x.skill}</strong><div className="muted">{x.students} students affected</div></div>
                    <span>{x.average_gap} pt gap</span>
                  </div>
                ))
              : <Empty title="No skill gaps yet" body="Student target roles will populate this analysis." />}
          </Card>

          <Card>
            <SectionTitle title="AYUSH Industry Demand" />
            {a.industry_demand.length
              ? a.industry_demand.map((x) => (
                  <div className="gap-mini" key={x.skill}>
                    <strong>{x.skill}</strong><span>{x.requests} requests</span>
                  </div>
                ))
              : <Empty title="No industry demand yet" body="Published opportunities with required skills will populate this analysis." />}
          </Card>
        </div>
      </div>
    );
  }

  // IMPORTANT: these names must match the Admin sidebar exactly.
  // Previously only four internal page names were handled, so every other
  // sidebar selection fell through to dashboard(), making all screens look identical.
  if (page === 'Admin Dashboard' || page === 'Dashboard') return dashboard();
  if (page === 'Users') return usersPage();
  if (page === 'Students') return studentsPage();
  if (page === 'Companies') return companiesPage();
  if (page === 'Academicians') return academiciansPage();
  if (page === 'Skills') return skillsPage();
  if (page === 'Opportunities') return opportunitiesPage();
  if (page === 'Analytics') return analyticsPage();
  // Backward-compatible names used by older navigation versions.
  if (page === 'Skill Analytics') return skillAnalytics();
  if (page === 'Placements') return placements();
  if (page === 'Company Verification') return companyVerification();
  return dashboard();
}
