import { FormEvent, useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api';
import { Card, Stat, Empty } from '../components/UI';

type StudentRecord = {
  student_id: number;
  name: string;
  email: string;
  education: string;
  year_degree: string;
  target_role: string | null;
  career_interests: string;
  research_experience: string;
  achievements: string;
  readiness: number;
  verified_skills: {
    skill_id: number;
    skill: string;
    proficiency: number;
  }[];
  verified_skill_count: number;
  skill_gaps: {
    skill: string;
    current: number;
    required: number;
    gap: number;
  }[];
  core_skills: {
    skill: string;
    current: number;
    required: number;
    gap: number;
  }[];
  projects: number;
  certificates: number;
  courses: number;
};

type StudentDocument = {
  id: number;
  student_id: number;
  student_name?: string;
  title: string;
  document_type: string;
  issuer: string;
  issued_on: string;
  url: string;
  visibility: string;
  verification_status: string;
  rejection_reason: string;
  created_at?: string;
};

type Opportunity = {
  id: number;
  owner_id: number;
  owner_role?: string;
  owner_name?: string;
  title: string;
  description: string;
  opportunity_type: string;
  location: string;
  status: string;
  requirements: {
    skill_id: number;
    skill: string;
    required_level: number;
  }[];
};

type Candidate = {
  student_id: number;
  name: string;
  email: string;
  score: number;
  readiness: number;
  verified_skills: number;
  matched_skills: string[];
  missing_skills: {
    skill: string;
    current: number;
    required: number;
    gap: number;
  }[];
};

type Application = {
  id: number;
  opportunity_id: number;
  opportunity_title: string;
  student_id: number;
  student_email: string;
  student_name: string;
  status: string;
  created_at: string;
};

type Profile = {
  name: string;
  education: string;
  year_degree: string;
  career_interests: string;
  research_experience: string;
  achievements: string;
};

type FacultyOpportunity = {
  id: number; owner_id: number; owner_role?: string; owner_name?: string;
  title: string; description: string; opportunity_type: string; ayush_focus: string;
  location: string; delivery_mode: string; duration: string; eligibility: string;
  registration_url: string; status: string;
  skills: { skill_id: number; skill: string; category?: string }[];
  application?: { id: number; academician_id: number; status: string; message: string; created_at: string } | null;
};
type FacultyApplication = {
  id: number; opportunity_id: number; title: string; opportunity_type: string; owner_name: string;
  status: string; message: string; created_at: string;
};

type Collaboration = {
  id:number; title:string; collaboration_type:string; ayush_focus:string; objective:string; status:string;
  start_date?:string|null; expected_end_date?:string|null; actual_end_date?:string|null; completion_summary:string;
  owner:{id:number;name:string;email:string}; academician:{id:number;name:string;email:string};
  milestones:{id:number;title:string;description:string;due_date?:string|null;status:string;completed_at?:string|null}[];
  feedback:{id:number;author:{id:number;name:string;email:string};feedback_type:string;comments:string;created_at:string}[];
  outputs:{id:number;title:string;output_type:string;description:string;url:string;verified:boolean;created_at:string}[];
};

type VerificationItem = {
  student_id: number;
  student_name: string;
  student_email: string;
  skill_id: number;
  skill: string;
  category: string;
  proficiency: number;
  status: string;
  evidence: {
    id: number;
    kind: string;
    title: string;
    url: string;
  }[];
};

export default function Academician({
  page,
  setPage,
  userId,
}: {
  page: string;
  setPage: (p: string) => void;
  userId: number;
}) {
  const [students, setStudents] = useState<StudentRecord[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [skills, setSkills] = useState<{ id: number; name: string; category: string }[]>([]);

  const [selectedStudent, setSelectedStudent] = useState<StudentRecord | null>(null);
  const [selectedOpportunity, setSelectedOpportunity] = useState<number | null>(null);
  const [matches, setMatches] = useState<Candidate[]>([]);

  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [saving, setSaving] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [verificationQueue, setVerificationQueue] = useState<VerificationItem[]>([]);
  const [documentQueue, setDocumentQueue] = useState<StudentDocument[]>([]);
  const [documentBusy, setDocumentBusy] = useState<number | null>(null);
  const [reviewingSkill, setReviewingSkill] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [facultyOpportunities, setFacultyOpportunities] = useState<FacultyOpportunity[]>([]);
  const [facultyApplications, setFacultyApplications] = useState<FacultyApplication[]>([]);
  const [facultyBusy, setFacultyBusy] = useState<number | null>(null);
  const [collaborations, setCollaborations] = useState<Collaboration[]>([]);
  const [collabDraft, setCollabDraft] = useState<Record<number,string>>({});
  const [outputDraft, setOutputDraft] = useState<Record<number,string>>({});
  const [feedbackDraft, setFeedbackDraft] = useState<Record<number,string>>({});
  const [facultySkillIds, setFacultySkillIds] = useState<number[]>([]);
  const [skillRequirements, setSkillRequirements] = useState<
    { skillId: string; requiredLevel: string }[]
  >([
    { skillId: '', requiredLevel: '70' },
  ]);

  async function load() {
    setError('');
    try {
      const [studentData, opportunityData, applicationData, profileData, skillData, verificationData, documentData, facultyOpportunityData, facultyApplicationData, collaborationData] =
        await Promise.all([
          api<StudentRecord[]>('/academician/students'),
          api<Opportunity[]>('/opportunities'),
          api<Application[]>('/applications'),
          api<Profile>('/profile'),
          api<{ id: number; name: string; category: string }[]>('/skills'),
          api<VerificationItem[]>('/academician/verification-queue'),
          api<StudentDocument[]>('/academician/document-verification'),
          api<FacultyOpportunity[]>('/faculty-opportunities'),
          api<FacultyApplication[]>('/academician/faculty-opportunities/applications'),
          api<Collaboration[]>('/collaborations'),
        ]);

      const normalizedStudentData: StudentRecord[] = Array.isArray(studentData)
        ? studentData.map((student: any) => ({
            student_id: Number(student?.student_id ?? student?.id ?? 0),
            name: student?.name || student?.email || 'Unnamed student',
            email: student?.email || '',
            education: student?.education || '',
            year_degree: student?.year_degree || '',
            target_role: student?.target_role || null,
            career_interests: student?.career_interests || '',
            research_experience: student?.research_experience || '',
            achievements: student?.achievements || '',
            readiness: Number(student?.readiness ?? 0),
            verified_skills: Array.isArray(student?.verified_skills)
              ? student.verified_skills.map((skill: any) => ({
                  skill_id: Number(skill?.skill_id ?? skill?.id ?? 0),
                  skill: skill?.skill || '',
                  proficiency: Number(skill?.proficiency ?? 0),
                }))
              : [],
            verified_skill_count: Number(
              student?.verified_skill_count ??
                (Array.isArray(student?.verified_skills)
                  ? student.verified_skills.length
                  : 0),
            ),
            skill_gaps: Array.isArray(student?.skill_gaps)
              ? student.skill_gaps
              : Array.isArray(student?.core_gaps)
                ? student.core_gaps
                : [],
            core_skills: Array.isArray(student?.core_skills)
              ? student.core_skills
              : Array.isArray(student?.core_gaps)
                ? student.core_gaps
                : [],
            projects: Number(student?.projects ?? student?.project_count ?? 0),
            certificates: Number(
              student?.certificates ?? student?.certificate_count ?? 0,
            ),
            courses: Number(student?.courses ?? student?.course_count ?? 0),
          }))
        : [];

      setStudents(normalizedStudentData);
      setOpportunities(opportunityData);
      setApplications(applicationData);
      setProfile(profileData);
      setSkills(skillData);
      setVerificationQueue(verificationData);
      setDocumentQueue(documentData || []);
      setFacultyOpportunities(facultyOpportunityData || []);
      setFacultyApplications(facultyApplicationData || []);
      setCollaborations(collaborationData || []);
    } catch (e: any) {
      setError(e.message || 'Unable to load academician data.');
    } finally {
      setLoading(false);
    }
  }

  async function verifyDocument(id: number, status: 'Verified' | 'Rejected') {
    setDocumentBusy(id);
    setError('');
    try {
      const updated = await api<StudentDocument>(`/academician/documents/${id}/verify`, {
        method: 'PATCH',
        body: JSON.stringify({ status, reason: status === 'Rejected' ? 'Please provide a clearer or valid document.' : '' }),
      });
      setDocumentQueue((items) => items.filter((item) => item.id !== updated.id));
      setNotice(status === 'Verified' ? 'Document verified.' : 'Document rejected.');
    } catch (e: any) {
      setError(e.message || 'Could not update document verification.');
    } finally {
      setDocumentBusy(null);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const myOpportunities = useMemo(
    () =>
      opportunities.filter(
        (x) => x.owner_id === userId && x.status === 'Published',
      ),
    [opportunities, userId],
  );

  const filteredStudents = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return students;

    return students.filter((student) =>
      [
        student.name,
        student.email,
        student.education,
        student.year_degree,
        student.target_role || '',
        student.career_interests,
        student.research_experience,
        ...(Array.isArray(student.verified_skills)
          ? student.verified_skills.map((x) => x.skill)
          : []),
      ]
        .join(' ')
        .toLowerCase()
        .includes(q),
    );
  }, [students, search]);

  const averageReadiness = students.length
    ? Math.round(students.reduce((sum, s) => sum + s.readiness, 0) / students.length)
    : 0;

  const totalVerifiedSkills = students.reduce(
    (sum, student) => sum + student.verified_skill_count,
    0,
  );

  async function saveProfile(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');

    try {
      const form = new FormData(e.currentTarget);

      await api('/profile', {
        method: 'PUT',
        body: JSON.stringify({
          name: form.get('name'),
          education: form.get('education'),
          year_degree: form.get('year_degree'),
          career_interests: form.get('career_interests'),
          research_experience: form.get('research_experience'),
          achievements: form.get('achievements'),
        }),
      });

      setProfileSaved(true);
      setNotice('Academician profile saved successfully.');
      await load();
    } catch (e: any) {
      setError(e.message || 'Could not save profile.');
    } finally {
      setSaving(false);
    }
  }

  async function createOpportunity(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    setNotice('');

    try {
      const formElement = e.currentTarget;
      const form = new FormData(formElement);

      const requirements = skillRequirements
        .filter((item) => item.skillId)
        .map((item) => ({
          skill_id: Number(item.skillId),
          required_level: Number(item.requiredLevel) || 70,
        }));

      if (!requirements.length) {
        throw new Error('Select at least one AYUSH skill requirement.');
      }

      await api('/opportunities', {
        method: 'POST',
        body: JSON.stringify({
          title: form.get('title'),
          description: form.get('description'),
          opportunity_type: form.get('type'),
          location: form.get('location') || 'Remote',
          requirements,
        }),
      });

      formElement.reset();
      setSkillRequirements([{ skillId: '', requiredLevel: '70' }]);
      setNotice('Research/project opportunity published successfully.');
      await load();
      setPage('Opportunities');
    } catch (e: any) {
      setError(e.message || 'Could not publish opportunity.');
    }
  }


  async function applyFacultyOpportunity(opportunityId: number) {
    setFacultyBusy(opportunityId);
    setError(''); setNotice('');
    try {
      await api(`/faculty-opportunities/${opportunityId}/apply`, {
        method: 'POST', body: JSON.stringify({ message: 'I would like to participate in this AYUSH academia–industry opportunity.' }),
      });
      setNotice('Application submitted to the opportunity owner.');
      await load();
    } catch (e: any) { setError(e.message || 'Could not submit the faculty opportunity application.'); }
    finally { setFacultyBusy(null); }
  }

  async function createFacultyOpportunity(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError(''); setNotice('');
    const form = new FormData(e.currentTarget);
    try {
      if (!facultySkillIds.length) throw new Error('Select at least one AYUSH skill connected to this opportunity.');
      await api('/faculty-opportunities', { method: 'POST', body: JSON.stringify({
        title: form.get('title'), description: form.get('description'), opportunity_type: form.get('opportunity_type'),
        ayush_focus: form.get('ayush_focus'), location: form.get('location'), delivery_mode: form.get('delivery_mode'),
        duration: form.get('duration'), eligibility: form.get('eligibility'), registration_url: form.get('registration_url'), skills: facultySkillIds,
      }) });
      setFacultySkillIds([]); setNotice('Academia–industry opportunity published successfully.'); await load(); setPage('Faculty Opportunities');
    } catch (e: any) { setError(e.message || 'Could not publish the faculty opportunity.'); }
  }

  async function updateCollaboration(id:number, payload:Record<string,unknown>) {
    try {
      const updated = await api<Collaboration>(`/collaborations/${id}`, {method:'PATCH', body:JSON.stringify(payload)});
      setCollaborations(items=>items.map(x=>x.id===id?updated:x)); setNotice('Collaboration updated.');
    } catch(e:any){ setError(e.message||'Could not update collaboration.'); }
  }

  async function addCollaborationMilestone(item:Collaboration) {
    const title=(collabDraft[item.id]||'').trim(); if(!title) return;
    try { const updated=await api<Collaboration>(`/collaborations/${item.id}/milestones`,{method:'POST',body:JSON.stringify({title,description:'Collaboration milestone'})}); setCollaborations(xs=>xs.map(x=>x.id===item.id?updated:x)); setCollabDraft(d=>({...d,[item.id]:''})); }
    catch(e:any){setError(e.message||'Could not add milestone.');}
  }

  async function updateCollaborationMilestone(item:Collaboration,milestoneId:number,status:string){
    try {const updated=await api<Collaboration>(`/collaboration-milestones/${milestoneId}`,{method:'PATCH',body:JSON.stringify({status})});setCollaborations(xs=>xs.map(x=>x.id===item.id?updated:x));}catch(e:any){setError(e.message||'Could not update milestone.');}
  }

  async function addCollaborationFeedback(item:Collaboration){
    const comments=(feedbackDraft[item.id]||'').trim(); if(!comments)return;
    try{const updated=await api<Collaboration>(`/collaborations/${item.id}/feedback`,{method:'POST',body:JSON.stringify({comments,feedback_type:'Progress'})});setCollaborations(xs=>xs.map(x=>x.id===item.id?updated:x));setFeedbackDraft(d=>({...d,[item.id]:''}));}catch(e:any){setError(e.message||'Could not save feedback.');}
  }

  async function addCollaborationOutput(item:Collaboration){
    const title=(outputDraft[item.id]||'').trim(); if(!title)return;
    try {const updated=await api<Collaboration>(`/collaborations/${item.id}/outputs`,{method:'POST',body:JSON.stringify({title,output_type:'Research output',description:'Collaboration deliverable'})});setCollaborations(xs=>xs.map(x=>x.id===item.id?updated:x));setOutputDraft(d=>({...d,[item.id]:''}));}catch(e:any){setError(e.message||'Could not add output.');}
  }

  async function reviewSkill(
    item: VerificationItem,
    action: 'approve' | 'reject' | 'request_more_evidence',
  ) {
    const key = `${item.student_id}-${item.skill_id}`;
    setReviewingSkill(key);
    setError('');
    setNotice('');

    try {
      await api(`/academician/students/${item.student_id}/skills/${item.skill_id}/review`, {
        method: 'POST',
        body: JSON.stringify({ action }),
      });

      const messages = {
        approve: 'Skill evidence approved and the skill is now academically verified.',
        reject: 'Skill evidence rejected.',
        request_more_evidence: 'More evidence requested from the student.',
      };
      setNotice(messages[action]);
      await load();
    } catch (e: any) {
      setError(e.message || 'Could not update the verification status.');
    } finally {
      setReviewingSkill(null);
    }
  }

  async function viewMatches(opportunityId: number) {
    setSelectedOpportunity(opportunityId);
    setLoadingMatches(true);
    setError('');

    try {
      const data = await api<Candidate[]>(
        `/opportunities/${opportunityId}/matches`,
      );
      setMatches(data);
      setPage('Matched Students');
    } catch (e: any) {
      setError(e.message || 'Could not calculate student matches.');
    } finally {
      setLoadingMatches(false);
    }
  }

  async function updateApplicationStatus(applicationId: number, status: string) {
    try {
      await api(`/applications/${applicationId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });

      setNotice('Application status updated.');
      await load();
    } catch (e: any) {
      setError(e.message || 'Could not update application.');
    }
  }

  if (loading) {
    return <Card>Loading academician intelligence…</Card>;
  }

  if (page === 'Profile') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}

        <Card>
          <div className="section-title">Academician profile</div>
          <p className="muted form-intro">
            Keep your academic and research information current so students can
            understand your research focus.
          </p>

          <form
            className="grid-form"
            onSubmit={saveProfile}
            onChange={() => setProfileSaved(false)}
            autoComplete="off"
          >
            <label>
              Name
              <input
                name="name"
                defaultValue={profile?.name || ''}
                autoComplete="off"
                required
              />
            </label>

            <label>
              AYUSH discipline
              <select
                name="education"
                defaultValue={profile?.education || ''}
                autoComplete="off"
              >
                <option value="">Select AYUSH discipline</option>
                <option value="Ayurveda">Ayurveda</option>
                <option value="Yoga & Naturopathy">Yoga & Naturopathy</option>
                <option value="Unani">Unani</option>
                <option value="Siddha">Siddha</option>
                <option value="Homoeopathy">Homoeopathy</option>
                <option value="Sowa-Rigpa">Sowa-Rigpa</option>
                <option value="Pharmacognosy">Pharmacognosy</option>
                <option value="Medicinal Plants">Medicinal Plants</option>
                <option value="AYUSH Pharmaceutical Sciences">AYUSH Pharmaceutical Sciences</option>
                <option value="Quality Control">Quality Control</option>
                <option value="Clinical Research">Clinical Research</option>
                <option value="Traditional Medicine Documentation">Traditional Medicine Documentation</option>
                <option value="Other AYUSH field">Other AYUSH field</option>
              </select>
            </label>

            <label>
              Designation
              <select
                name="year_degree"
                defaultValue={profile?.year_degree || ''}
                autoComplete="off"
              >
                <option value="">Select designation</option>
                <option value="Professor">Professor</option>
                <option value="Associate Professor">Associate Professor</option>
                <option value="Assistant Professor">Assistant Professor</option>
                <option value="Research Scholar">Research Scholar</option>
                <option value="Clinical Faculty">Clinical Faculty</option>
                <option value="Research Scientist">Research Scientist</option>
                <option value="AYUSH Practitioner">AYUSH Practitioner</option>
              </select>
            </label>

            <label>
              Primary research focus
              <select
                name="career_interests"
                defaultValue={profile?.career_interests || ''}
                autoComplete="off"
              >
                <option value="">Select research focus</option>
                <option value="Medicinal Plants & Pharmacognosy">Medicinal Plants & Pharmacognosy</option>
                <option value="Herbal Formulation & Standardization">Herbal Formulation & Standardization</option>
                <option value="AYUSH Clinical Research">AYUSH Clinical Research</option>
                <option value="Quality Control & Evaluation">Quality Control & Evaluation</option>
                <option value="Traditional Medicine Documentation">Traditional Medicine Documentation</option>
                <option value="Phytochemistry & Natural Products">Phytochemistry & Natural Products</option>
                <option value="AYUSH Drug Development">AYUSH Drug Development</option>
                <option value="Yoga & Naturopathy Research">Yoga & Naturopathy Research</option>
                <option value="Integrative AYUSH Research">Integrative AYUSH Research</option>
              </select>
            </label>

            <label className="full">
              Research experience
              <textarea
                name="research_experience"
                defaultValue={profile?.research_experience || ''}
                placeholder="Describe your AYUSH research areas, publications, laboratory or field experience."
              />
            </label>

            <label className="full">
              Achievements / notes
              <textarea
                name="achievements"
                defaultValue={profile?.achievements || ''}
                placeholder="Publications, conferences, awards, research projects, collaborations..."
              />
            </label>

            <button
              className={`primary ${profileSaved ? 'profile-saved' : ''}`}
              disabled={saving || profileSaved}
              type="submit"
            >
              {saving ? 'Saving…' : profileSaved ? '✓ Saved' : 'Save changes'}
            </button>
          </form>
        </Card>
      </div>
    );
  }

  if (page === 'Verification Queue') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}

        <div className="hero">
          <div>
            <div className="eyebrow">EVIDENCE VERIFICATION</div>
            <h2>Review student skill evidence.</h2>
            <p>
              Open the student's submitted evidence, then approve, reject, or
              request additional evidence. Approval records the academic verification status for the submitted skill evidence.
            </p>
          </div>
          <div className="candidate-score">{verificationQueue.length} pending</div>
        </div>

        <div className="stats">
          <Stat label="Pending reviews" value={verificationQueue.length} />
          <Stat
            label="With evidence links"
            value={verificationQueue.filter((item) => item.evidence.some((entry) => entry.url)).length}
          />
          <Stat
            label="Students represented"
            value={new Set(verificationQueue.map((item) => item.student_id)).size}
          />
          <Stat
            label="Skills awaiting review"
            value={new Set(verificationQueue.map((item) => item.skill_id)).size}
          />
        </div>

        <Card>
          {verificationQueue.length ? (
            <div className="list">
              {verificationQueue.map((item) => {
                const key = `${item.student_id}-${item.skill_id}`;
                const busy = reviewingSkill === key;
                const links = item.evidence.filter((entry) => entry.url);

                return (
                  <div className="candidate" key={key}>
                    <div className="grow">
                      <strong>{item.skill}</strong>
                      <div className="muted">
                        {item.student_name} · {item.student_email}
                      </div>
                      <div className="chips" style={{ marginTop: 8 }}>
                        <span className="chip">{item.category}</span>
                                                <span className="chip">{item.status}</span>
                      </div>

                      <div style={{ marginTop: 14 }}>
                        <strong>Submitted evidence</strong>
                        {links.length ? (
                          <div className="list" style={{ marginTop: 8 }}>
                            {links.map((entry) => (
                              <a
                                key={entry.id}
                                href={entry.url}
                                target="_blank"
                                rel="noreferrer"
                                className="secondary"
                                style={{ display: 'inline-block', width: 'fit-content' }}
                              >
                                📄 {entry.title || 'Open evidence'} →
                              </a>
                            ))}
                          </div>
                        ) : (
                          <p className="muted">No evidence link available.</p>
                        )}
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                      <button
                        type="button"
                        className="primary"
                        disabled={busy || !links.length}
                        onClick={() => reviewSkill(item, 'approve')}
                      >
                        {busy ? 'Updating…' : '✓ Approve'}
                      </button>
                      <button
                        type="button"
                        className="secondary"
                        disabled={busy}
                        onClick={() => reviewSkill(item, 'request_more_evidence')}
                      >
                        Request more
                      </button>
                      <button
                        type="button"
                        className="secondary"
                        disabled={busy}
                        onClick={() => reviewSkill(item, 'reject')}
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <Empty
              title="Verification queue is clear"
              body="There are no student skill submissions waiting for academic review."
            />
          )}
        </Card>

        <Card>
          <div className="section-title">Document verification</div>
          <p className="muted">Review student certificates, internship reports, resumes and academic records before they become verified portfolio evidence.</p>
          {documentQueue.length ? (
            <div className="list">
              {documentQueue.map((item) => (
                <div className="candidate" key={item.id}>
                  <div className="grow">
                    <strong>{item.title}</strong>
                    <div className="muted">{item.student_name} · {item.document_type}{item.issuer ? ` · ${item.issuer}` : ''}</div>
                    <div className="chips" style={{ marginTop: 8 }}>
                      <span className="chip">{item.visibility}</span>
                      <span className="chip">Pending</span>
                    </div>
                    {item.url && (
                      <a href={item.url} target="_blank" rel="noreferrer" className="secondary" style={{ display: 'inline-block', marginTop: 10, width: 'fit-content' }}>
                        📄 Open document →
                      </a>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                    <button className="primary" disabled={documentBusy === item.id} onClick={() => verifyDocument(item.id, 'Verified')}>
                      {documentBusy === item.id ? 'Updating…' : '✓ Verify'}
                    </button>
                    <button className="secondary" disabled={documentBusy === item.id} onClick={() => verifyDocument(item.id, 'Rejected')}>Reject</button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Empty title="Document queue is clear" body="No student documents are waiting for academic review." />
          )}
        </Card>
      </div>
    );
  }

  if (page === 'Students') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}

        <div className="hero">
          <div>
            <div className="eyebrow">STUDENT DISCOVERY</div>
            <h2>Find students by skills and readiness.</h2>
            <p>
              Search the live student database using verified skills, target
              roles, education and research interests.
            </p>
          </div>
        </div>

        <div className="stats">
          <Stat label="Students" value={students.length} />
          <Stat label="Average readiness" value={`${averageReadiness}%`} />
          <Stat label="Verified skills" value={totalVerifiedSkills} />
          <Stat
            label="Students with gaps"
            value={students.filter((s) => s.skill_gaps.length > 0).length}
          />
        </div>

        <Card>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, skill, target role, education or research interest..."
          />
        </Card>

        <div className="two-col">
          <Card>
            <div className="section-title">
              Students ({filteredStudents.length})
            </div>

            {filteredStudents.length ? (
              <div className="list">
                {filteredStudents.map((student) => (
                  <button
                    key={student.student_id}
                    type="button"
                    className="candidate"
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      border: 0,
                      cursor: 'pointer',
                    }}
                    onClick={() => setSelectedStudent(student)}
                  >
                    <div className="grow">
                      <strong>{student.name}</strong>
                      <div className="muted">
                        {student.email} · {student.target_role || 'Target role not set'}
                      </div>
                      <div className="chips" style={{ marginTop: 8 }}>
                        {student.verified_skills.slice(0, 4).map((skill) => (
                          <span className="chip" key={skill.skill_id}>
                            ✓ {skill.skill}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="candidate-score">
                      {student.readiness}%
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <Empty
                title="No students found"
                body="Try another search term."
              />
            )}
          </Card>

          <Card>
            {selectedStudent ? (
              <div>
                <div className="section-title">{selectedStudent.name}</div>
                <p className="muted">{selectedStudent.email}</p>

                <div className="stats">
                  <Stat label="Readiness" value={`${selectedStudent.readiness}%`} />
                  <Stat
                    label="Verified skills"
                    value={selectedStudent.verified_skill_count}
                  />
                  <Stat label="Projects" value={selectedStudent.projects} />
                </div>

                <div className="section-title" style={{ marginTop: 20 }}>
                  Profile
                </div>

                <div className="gap-mini">
                  <span>Education</span>
                  <strong>
                    {selectedStudent.education || 'Not provided'}
                  </strong>
                </div>
                <div className="gap-mini">
                  <span>Year / degree</span>
                  <strong>
                    {selectedStudent.year_degree || 'Not provided'}
                  </strong>
                </div>
                <div className="gap-mini">
                  <span>Target role</span>
                  <strong>
                    {selectedStudent.target_role || 'Not selected'}
                  </strong>
                </div>

                <div className="section-title" style={{ marginTop: 20 }}>
                  Verified skills
                </div>

                {selectedStudent.verified_skills?.length ? (
                  <div className="chips">
                    {selectedStudent.verified_skills.map((skill) => (
                      <span className="chip" key={skill.skill_id}>
                        ✓ {skill.skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="muted">No verified skills yet.</p>
                )}

                <div className="section-title" style={{ marginTop: 20 }}>
                  Top core skill gaps
                </div>

                {selectedStudent.skill_gaps?.length ? (
                  <div className="list">
                    {selectedStudent.skill_gaps.slice(0, 5).map((gap) => (
                      <div className="gap-row" key={gap.skill}>
                        <div>
                          <strong>{gap.skill}</strong>
                          <div className="muted">
                            Current {gap.current}% · Required {gap.required}%
                          </div>
                        </div>
                        <span className="status">{gap.gap}% gap</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="muted">No active core skill gaps.</p>
                )}

                {selectedStudent.research_experience && (
                  <>
                    <div className="section-title" style={{ marginTop: 20 }}>
                      Research experience
                    </div>
                    <p className="muted">
                      {selectedStudent.research_experience}
                    </p>
                  </>
                )}
              </div>
            ) : (
              <Empty
                title="Select a student"
                body="Choose a student from the list to inspect their profile."
              />
            )}
          </Card>
        </div>
      </div>
    );
  }

  if (page === 'Post Research/Project') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}

        <Card>
          <div className="section-title">Create research / project opportunity</div>
          <p className="muted form-intro">
            Define the skills required for your research project. SkillNova
            will use these requirements to rank suitable students.
          </p>

          <form className="grid-form" onSubmit={createOpportunity} autoComplete="off">
            <label>
              Opportunity title
              <input
                name="title"
                placeholder="Herbal Formulation Standardization Research Project"
                autoComplete="off"
                required
              />
            </label>

            <label>
              Type
              <select name="type" defaultValue="" required>
                <option value="">Select opportunity type</option>
                <option value="Research Project">Research Project</option>
                <option>Mentorship</option>
                <option>Internship</option>
                <option>Project</option>
              </select>
            </label>

            <label>
              Location
              <input
                name="location"
                placeholder="e.g. UOH campus / AYUSH research centre / Remote"
                autoComplete="off"
                required
              />
            </label>

            <label className="full">
              Description
              <textarea
                name="description"
                placeholder="Describe the research problem, expected work and outcomes."
                required
              />
            </label>

            <div className="full skill-builder">
              <div className="skill-builder-head">
                <div>
                  <label>Required AYUSH skills</label>
                  <span className="muted">Select the AYUSH skills required for this opportunity.</span>
                </div>
                <button
                  type="button"
                  className="secondary skill-add"
                  onClick={() =>
                    setSkillRequirements((current) => [
                      ...current,
                      { skillId: '', requiredLevel: '70' },
                    ])
                  }
                >
                  + Add skill
                </button>
              </div>

              <div className="skill-builder-list">
                {skillRequirements.map((requirement, index) => (
                  <div className="skill-builder-row" key={`${index}-${requirement.skillId}`}>
                    <select
                      value={requirement.skillId}
                      onChange={(event) =>
                        setSkillRequirements((current) =>
                          current.map((item, itemIndex) =>
                            itemIndex === index
                              ? { ...item, skillId: event.target.value }
                              : item,
                          ),
                        )
                      }
                      required={index === 0}
                      aria-label={`Required skill ${index + 1}`}
                    >
                      <option value="">Select an AYUSH skill</option>
                      {skills
                        .filter(
                          (skill) =>
                            skill.category !== 'Alternative' &&
                            skill.category !== 'Advanced/Optional',
                        )
                        .map((skill) => (
                          <option key={skill.id} value={skill.id}>
                            {skill.name}
                          </option>
                        ))}
                    </select>



                    {skillRequirements.length > 1 && (
                      <button
                        type="button"
                        className="skill-remove"
                        onClick={() =>
                          setSkillRequirements((current) =>
                            current.filter((_, itemIndex) => itemIndex !== index),
                          )
                        }
                        aria-label={`Remove skill ${index + 1}`}
                        title="Remove skill"
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <button className="primary">Publish research opportunity</button>
          </form>
        </Card>
      </div>
    );
  }


  if (page === 'Faculty Opportunities') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}
        <div className="hero">
          <div><div className="eyebrow">AYUSH ACADEMIA–INDUSTRY COLLABORATION</div><h2>Faculty opportunities</h2><p>Discover and apply for faculty internships, industrial training, FDPs, consultancy, collaborative research, guest lectures, innovation challenges and live industry projects.</p></div>
          <button className="primary" onClick={() => setPage('Create Faculty Opportunity')}>+ Create opportunity</button>
        </div>
        <Card><div className="section-title">Open academia–industry opportunities</div>
          {facultyOpportunities.length ? <div className="list">{facultyOpportunities.map((item) => <div className="gap-row" key={item.id}>
            <div className="grow"><strong>{item.title}</strong><div className="muted">{item.opportunity_type} · {item.ayush_focus} · {item.delivery_mode} · {item.location}</div>
              <p className="muted" style={{ marginTop: 7 }}>{item.description}</p>
              <div className="chips">{item.skills.map((s) => <span className="chip" key={s.skill_id}>{s.skill}</span>)}</div>
              <div className="muted" style={{ marginTop: 7 }}>{item.duration || 'Flexible duration'}{item.eligibility ? ` · ${item.eligibility}` : ''}</div>
            </div>
            <div>{item.application ? <span className="chip">{item.application.status}</span> : <button className="secondary" disabled={facultyBusy === item.id} onClick={() => applyFacultyOpportunity(item.id)}>{facultyBusy === item.id ? 'Applying…' : 'Apply'}</button>}</div>
          </div>)}</div> : <Empty title="No faculty opportunities yet" body="Industry and academic partners can publish AYUSH faculty opportunities here." />}
        </Card>
        <Card><div className="section-title">My faculty applications</div>{facultyApplications.length ? <div className="list">{facultyApplications.map((a) => <div className="gap-row" key={a.id}><div className="grow"><strong>{a.title}</strong><div className="muted">{a.opportunity_type} · {a.owner_name}</div></div><span className="chip">{a.status}</span></div>)}</div> : <Empty title="No applications yet" body="Applications you submit to faculty opportunities will appear here." />}</Card>
      </div>
    );
  }

  if (page === 'Create Faculty Opportunity') {
    return <div className="stack"><Card><div className="section-title">Create AYUSH academia–industry opportunity</div><p className="muted form-intro">Publish a faculty-facing collaboration or professional development opportunity.</p>
      <form className="grid-form" onSubmit={createFacultyOpportunity} autoComplete="off">
        <label>Title<input name="title" placeholder="e.g. Faculty Internship in AYUSH Quality Control" required /></label>
        <label>Opportunity type<select name="opportunity_type" defaultValue="Collaborative Research">
          <option>Faculty Internship</option><option>Industrial Training for Faculty</option><option>Faculty Development Programme (FDP)</option><option>Consultancy</option><option>Collaborative Research</option><option>Guest Lecture</option><option>Innovation Challenge</option><option>Live Industry Project</option>
        </select></label>
        <label>AYUSH focus<select name="ayush_focus" defaultValue="Ayurveda"><option>Ayurveda</option><option>Yoga & Naturopathy</option><option>Unani</option><option>Siddha</option><option>Homoeopathy</option><option>Sowa-Rigpa</option><option>Medicinal Plants & Pharmacognosy</option><option>AYUSH Drug Development</option><option>Quality Control & Standardization</option><option>Clinical & Translational Research</option></select></label>
        <label>Location<input name="location" placeholder="Hyderabad / Remote / AYUSH research centre" required /></label>
        <label>Delivery mode<select name="delivery_mode"><option>Hybrid</option><option>On-site</option><option>Remote</option></select></label>
        <label>Duration<input name="duration" placeholder="e.g. 4 weeks / 30 hours" /></label>
        <label className="full">Eligibility<textarea name="eligibility" placeholder="e.g. AYUSH faculty, researchers or academic professionals with relevant teaching/research experience." /></label>
        <label className="full">Description<textarea name="description" placeholder="Describe the collaboration, expected contribution, learning outcomes and deliverables." required /></label>
        <label className="full">Registration / details URL<input name="registration_url" type="url" placeholder="https://..." /></label>
        <label className="full">Connected AYUSH skills<select value="" onChange={(e) => { const id=Number(e.target.value); if(id && !facultySkillIds.includes(id)) setFacultySkillIds(x=>[...x,id]); }}><option value="">Select a skill</option>{skills.filter(s=>!facultySkillIds.includes(s.id)).map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select><div className="chips" style={{marginTop:8}}>{facultySkillIds.map(id=>{const s=skills.find(x=>x.id===id); return s ? <span className="chip" key={id}>{s.name} <button type="button" onClick={()=>setFacultySkillIds(x=>x.filter(v=>v!==id))}>×</button></span> : null;})}</div></label>
        <button className="primary">Publish faculty opportunity</button>
      </form>
    </Card></div>;
  }

  if (page === 'Opportunities') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}

        <div className="hero">
          <div>
            <div className="eyebrow">ACADEMIC OPPORTUNITIES</div>
            <h2>Your research and project opportunities.</h2>
            <p>
              Published opportunities are connected to the live student skill
              graph.
            </p>
          </div>

          <button
            className="primary"
            onClick={() => setPage('Post Research/Project')}
          >
            + Create opportunity
          </button>
        </div>

        <Card>
          <div className="section-title">Published opportunities</div>

          {myOpportunities.length ? (
            <div className="list">
              {myOpportunities.map((opportunity) => (
                <div className="gap-row" key={opportunity.id}>
                  <div className="grow">
                    <strong>{opportunity.title}</strong>
                    <div className="muted">
                      {opportunity.opportunity_type} · {opportunity.location}
                    </div>

                    <div className="chips" style={{ marginTop: 8 }}>
                      {opportunity.requirements.map((requirement) => (
                        <span className="chip" key={requirement.skill_id}>
                          {requirement.skill}
                        </span>
                      ))}
                    </div>
                  </div>

                  <button
                    className="secondary"
                    onClick={() => viewMatches(opportunity.id)}
                  >
                    View matches
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <Empty
              title="No opportunities yet"
              body="Create your first research or project opportunity."
            />
          )}
        </Card>
      </div>
    );
  }

  if (page === 'Matched Students') {
    const selected = opportunities.find((x) => x.id === selectedOpportunity);

    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}

        <Card>
          <div className="section-title">Matched students</div>
          <p className="muted form-intro">
            Students are ranked using verified skill coverage and readiness.
          </p>

          {myOpportunities.length ? (
            <div className="list">
              {myOpportunities.map((opportunity) => (
                <div className="gap-row" key={opportunity.id}>
                  <div className="grow">
                    <strong>{opportunity.title}</strong>
                    <div className="muted">
                      {opportunity.requirements.length} required skills
                    </div>
                  </div>

                  <button
                    className="secondary"
                    onClick={() => viewMatches(opportunity.id)}
                  >
                    Find students
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <Empty
              title="No opportunities"
              body="Publish a research/project opportunity first."
            />
          )}
        </Card>

        {selectedOpportunity !== null && (
          <Card>
            <div className="section-title">
              Candidate ranking
              {selected ? ` · ${selected.title}` : ''}
            </div>

            {loadingMatches ? (
              <p className="muted">Calculating live student matches…</p>
            ) : matches.length ? (
              <div className="list">
                {matches.map((candidate) => (
                  <div className="candidate" key={candidate.student_id}>
                    <div className="grow">
                      <strong>{candidate.name}</strong>
                      <div className="muted">
                        {candidate.email} · {candidate.verified_skills} verified
                        skills · {candidate.readiness}% readiness
                      </div>

                      <div className="chips" style={{ marginTop: 8 }}>
                        {candidate.matched_skills.map((skill) => (
                          <span className="chip" key={skill}>
                            ✓ {skill}
                          </span>
                        ))}
                      </div>

                      {candidate.missing_skills.length > 0 && (
                        <div className="muted" style={{ marginTop: 8 }}>
                          Needs:{' '}
                          {candidate.missing_skills
                            .map(
                              (x) =>
                                `${x.skill} (${x.current}/${x.required})`,
                            )
                            .join(' · ')}
                        </div>
                      )}
                    </div>

                    <div className="candidate-score">{candidate.score}%</div>
                  </div>
                ))}
              </div>
            ) : (
              <Empty
                title="No student data yet"
                body="Students will appear when profiles and skills are available."
              />
            )}
          </Card>
        )}
      </div>
    );
  }

  if (page === 'Collaborations') {
    return <div className="stack">
      {error && <div className="error">{error}</div>}{notice && <div className="success-banner">✓ {notice}</div>}
      <div className="hero"><div><div className="eyebrow">AYUSH ACADEMIA × INDUSTRY</div><h2>Collaborations</h2><p>Track accepted academia–industry work from agreed objectives through milestones, feedback and documented outputs.</p></div></div>
      {collaborations.length ? collaborations.map(item=><Card key={item.id}>
        <div style={{display:'flex',justifyContent:'space-between',gap:16,alignItems:'flex-start'}}><div><div className="section-title">{item.title}</div><div className="muted">{item.collaboration_type} · {item.ayush_focus} · Partner: {item.owner.name}</div></div><select value={item.status} onChange={e=>updateCollaboration(item.id,{status:e.target.value})}><option>Planned</option><option>Active</option><option>On Hold</option><option>Completed</option><option>Cancelled</option></select></div>
        <p className="muted" style={{marginTop:10}}>{item.objective}</p>
        <div className="two-col"><div><div className="section-title">Milestones</div>{item.milestones.map(m=><div className="gap-row" key={m.id}><div className="grow"><strong>{m.title}</strong><div className="muted">{m.description}</div></div><select value={m.status} onChange={e=>updateCollaborationMilestone(item,m.id,e.target.value)}><option>Planned</option><option>In Progress</option><option>Completed</option><option>Blocked</option></select></div>)}<div style={{display:'flex',gap:8,marginTop:10}}><input value={collabDraft[item.id]||''} onChange={e=>setCollabDraft(d=>({...d,[item.id]:e.target.value}))} placeholder="Add next milestone"/><button className="secondary" onClick={()=>addCollaborationMilestone(item)}>Add</button></div></div>
        <div><div className="section-title">Outputs</div>{item.outputs.length?item.outputs.map(o=><div className="gap-row" key={o.id}><div className="grow"><strong>{o.title}</strong><div className="muted">{o.output_type}</div></div><span className="chip">{o.verified?'Verified':'Recorded'}</span></div>):<div className="muted">No outputs recorded yet.</div>}<div style={{display:'flex',gap:8,marginTop:10}}><input value={outputDraft[item.id]||''} onChange={e=>setOutputDraft(d=>({...d,[item.id]:e.target.value}))} placeholder="Add research output"/><button className="secondary" onClick={()=>addCollaborationOutput(item)}>Add</button></div></div></div>
        <div className="section-title" style={{marginTop:18}}>Feedback</div>{item.feedback.length?item.feedback.map(f=><div className="muted" key={f.id} style={{padding:'8px 0',borderBottom:'1px solid #edf1f5'}}><strong>{f.author.name}</strong> · {f.feedback_type}<br/>{f.comments}</div>):<div className="muted">No feedback recorded yet.</div>}<div style={{display:'flex',gap:8,marginTop:10}}><input value={feedbackDraft[item.id]||''} onChange={e=>setFeedbackDraft(d=>({...d,[item.id]:e.target.value}))} placeholder="Record partner / progress feedback"/><button className="secondary" onClick={()=>addCollaborationFeedback(item)}>Save feedback</button></div>
      </Card>):<Empty title="No active collaborations" body="When an accepted faculty opportunity is started by its owner, the collaboration will appear here."/>}
    </div>;
  }

  if (page === 'Applications') {
    const relevantApplications = applications.filter((application) =>
      opportunities.some((opportunity) => opportunity.id === application.opportunity_id),
    );

    return (
      <Card>
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}

        <div className="section-title">Research applications</div>
        <p className="muted form-intro">
          Review students who applied to your research and project opportunities.
        </p>

        {relevantApplications.length ? (
          <div className="list">
            {relevantApplications.map((application) => (
              <div className="candidate" key={application.id}>
                <div className="grow">
                  <strong>{application.student_name || 'Student'}</strong>
                  <div className="muted">
                    {application.student_email} · {application.opportunity_title}
                  </div>
                  <div className="muted">
                    Applied {new Date(application.created_at).toLocaleDateString()}
                  </div>
                </div>

                <select
                  value={application.status}
                  onChange={(e) =>
                    updateApplicationStatus(application.id, e.target.value)
                  }
                >
                  <option>Applied</option>
                  <option>Under Review</option>
                  <option>Shortlisted</option>
                  <option>Interview</option>
                  <option>Selected</option>
                  <option>Rejected</option>
                </select>
              </div>
            ))}
          </div>
        ) : (
          <Empty
            title="No applications"
            body="Applications will appear here when students apply to your opportunities."
          />
        )}
      </Card>
    );
  }

  return (
    <div className="stack">
      {error && <div className="error">{error}</div>}
      {notice && <div className="success-banner">✓ {notice}</div>}

      <div className="hero">
        <div>
          <div className="eyebrow">ACADEMICIAN PORTAL</div>
          <h2>Connect research with the right students.</h2>
          <p>
            Discover students through verified skills, readiness and skill gaps,
            then create research opportunities that automatically match them.
          </p>
        </div>

        <button
          className="primary"
          onClick={() => setPage('Post Research/Project')}
        >
          + Post research
        </button>
      </div>

      <Card>
        <div className="section-title">Verification queue</div>
        <p className="muted">
          {verificationQueue.length
            ? `${verificationQueue.length} student skill submission${verificationQueue.length === 1 ? '' : 's'} waiting for evidence review.`
            : 'No student skill submissions are waiting for review.'}
        </p>
        <button className="secondary" onClick={() => setPage('Verification Queue')}>
          Review evidence →
        </button>
      </Card>

      <div className="stats">
        <Stat label="Students" value={students.length} />
        <Stat label="Average readiness" value={`${averageReadiness}%`} />
        <Stat label="Verified skills" value={totalVerifiedSkills} />
        <Stat label="Evidence pending" value={verificationQueue.length} />
      </div>

      <div className="two-col">
        <Card>
          <div className="section-title">Student discovery</div>
          <p className="muted">
            Search students by skill, target role, education or research
            interests.
          </p>
          <button className="secondary" onClick={() => setPage('Students')}>
            Find students →
          </button>
        </Card>

        <Card>
          <div className="section-title">Research matching</div>
          <p className="muted">
            Publish a research/project opportunity and compare candidates using
            verified skill coverage.
          </p>
          <button
            className="secondary"
            onClick={() => setPage('Post Research/Project')}
          >
            Create opportunity →
          </button>
        </Card>
      </div>

      <Card>
        <div className="section-title">Top student matches</div>

        {students.length ? (
          <div className="list">
            {students.slice(0, 5).map((student) => (
              <div className="candidate" key={student.student_id}>
                <div className="grow">
                  <strong>{student.name}</strong>
                  <div className="muted">
                    {student.target_role || 'Target role not set'} ·{' '}
                    {student.verified_skill_count} verified skills
                  </div>
                </div>
                <div className="candidate-score">{student.readiness}%</div>
              </div>
            ))}
          </div>
        ) : (
          <Empty
            title="No students yet"
            body="Student profiles will appear here after registration."
          />
        )}
      </Card>
    </div>
  );
}
