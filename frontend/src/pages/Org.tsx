import { FormEvent, useEffect, useMemo, useState, type CSSProperties } from 'react';
import { api } from '../lib/api';
import { Card, Stat, Empty } from '../components/UI';
import { Role, Skill } from '../types';

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
  created_at?: string;
  requirements: { skill_id: number; skill: string; required_level: number }[];
};

type Candidate = {
  student_id: number;
  name: string;
  email: string;
  score: number;
  readiness: number;
  verified_skills: number;
  matched_skills: string[];
  missing_skills: { skill: string; current: number; required: number; gap: number }[];
  skill_comparisons?: {
    skill_id: number;
    skill: string;
    current: number;
    required: number;
    gap: number;
    meets_requirement: boolean;
    verified: boolean;
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

type Internship = {
  id: number;
  application_id: number;
  opportunity_id: number;
  opportunity_title: string;
  student_id: number;
  student_name: string;
  student_email: string;
  company_id: number;
  mentor_name: string;
  mentor_email: string;
  status: string;
  progress_percent: number;
  start_date?: string | null;
  expected_end_date?: string | null;
  actual_end_date?: string | null;
  summary: string;
  certificate_url: string;
  report_url: string;
  milestones: { id: number; title: string; description: string; due_date?: string | null; status: string; completed_at?: string | null }[];
  feedback: { id: number; author_name: string; author_role: string; rating?: number | null; feedback: string; created_at: string }[];
};

type CompanyProfile = {
  name?: string;
  education?: string;
  year_degree?: string;
  career_interests?: string;
  research_experience?: string;
  achievements?: string;
};

type CompanyVerification = {
  status: string;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  notes?: string;
};

type FacultyOpportunity = { id:number; owner_id:number; owner_name?:string; title:string; description:string; opportunity_type:string; ayush_focus:string; location:string; delivery_mode:string; duration:string; eligibility:string; registration_url:string; status:string; skills:{skill_id:number;skill?:string}[]; };

type FacultyOpportunityApplication = { id:number; academician_id:number; academician_name:string; academician_email:string; status:string; message:string; created_at:string; };

type Collaboration = {
  id:number; title:string; collaboration_type:string; ayush_focus:string; objective:string; status:string;
  owner:{id:number;name:string;email:string}; academician:{id:number;name:string;email:string};
  milestones:{id:number;title:string;description:string;due_date?:string|null;status:string;completed_at?:string|null}[];
  feedback:{id:number;author:{id:number;name:string;email:string};feedback_type:string;comments:string;created_at:string}[];
  outputs:{id:number;title:string;output_type:string;description:string;url:string;verified:boolean;created_at:string}[];
};

type LearningProgram = {
  id: number;
  owner_id: number;
  owner_name?: string;
  title: string;
  description: string;
  program_type: string;
  ayush_focus: string;
  duration: string;
  delivery_mode: string;
  eligibility: string;
  registration_deadline?: string | null;
  certificate_available: boolean;
  registration_url: string;
  status: string;
  created_at?: string;
  skills: { skill_id: number; skill?: string }[];
  enrollment_count?: number;
};


const companyIndustryOptions = [
  'AYUSH Pharmaceuticals & Herbal Products',
  'Ayurvedic Hospitals & Clinics',
  'Medicinal Plants & Pharmacognosy',
  'Herbal Formulation & Manufacturing',
  'Quality Control & Testing',
  'Research & Development',
  'Wellness & Yoga Services',
  'Regulatory & Documentation',
  'AYUSH Education & Training',
];

const ayushFocusOptions = [
  'Ayurveda',
  'Yoga & Naturopathy',
  'Unani',
  'Siddha',
  'Homoeopathy',
  'Sowa-Rigpa',
  'Medicinal Plants & Herbal Products',
  'AYUSH Drug Development',
  'Quality Control & Standardization',
  'Clinical & Translational Research',
];

const ayushSkillHints = [
  'Pharmacognosy',
  'Quality Control',
  'Regulatory Compliance',
  'Herbal Formulation',
  'Medicinal Plant Identification',
  'AYUSH Systems Overview',
  'Documentation',
  'Data Analysis',
];

const learningProgramTypes = [
  'Training',
  'Certification',
  'Workshop',
  'Mentorship',
  'Industry Learning Program',
];

const learningAyushFocusOptions = [
  'Ayurveda',
  'Yoga & Naturopathy',
  'Unani',
  'Siddha',
  'Homoeopathy',
  'Sowa-Rigpa',
  'Medicinal Plants & Pharmacognosy',
  'AYUSH Drug Development',
  'Quality Control & Standardization',
  'Clinical & Translational Research',
  'AYUSH Regulatory & Documentation',
];

const fieldStyle: CSSProperties = {
  display: 'block',
  fontSize: 14,
  fontWeight: 700,
  color: '#182433',
};

const inputStyle: CSSProperties = {
  width: '100%',
  boxSizing: 'border-box',
  marginTop: 8,
  padding: '13px 14px',
  border: '1px solid #d9e1e9',
  borderRadius: 9,
  background: '#fff',
  color: '#182433',
  fontSize: 14,
  outline: 'none',
};

const helperStyle: CSSProperties = {
  display: 'block',
  marginTop: 6,
  color: '#70829a',
  fontSize: 12,
  fontWeight: 500,
};

const twoColumnStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)',
  gap: 18,
};

export default function Org({
  role,
  page,
  setPage,
  userId,
}: {
  role: Role;
  page: string;
  setPage: (p: string) => void;
  userId: number;
}) {
  const isCompany = role === 'company';
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [apps, setApps] = useState<Application[]>([]);
  const [learningPrograms, setLearningPrograms] = useState<LearningProgram[]>([]);
  const [internships, setInternships] = useState<Internship[]>([]);
  const [internshipBusy, setInternshipBusy] = useState<number | null>(null);
  const [milestoneDraft, setMilestoneDraft] = useState<Record<number, string>>({});
  const [feedbackDraft, setFeedbackDraft] = useState<Record<number, string>>({});
  const [skills, setSkills] = useState<Skill[]>([]);
  const [matches, setMatches] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [selectedSkillIds, setSelectedSkillIds] = useState<number[]>([]);
  const [requiredLevels, setRequiredLevels] = useState<Record<number, number>>({});
  const [programSkillIds, setProgramSkillIds] = useState<number[]>([]);
  const [programPublishing, setProgramPublishing] = useState(false);
  const [facultyOpportunities, setFacultyOpportunities] = useState<FacultyOpportunity[]>([]);
  const [facultyApplications, setFacultyApplications] = useState<FacultyOpportunityApplication[]>([]);
  const [facultySkillIds, setFacultySkillIds] = useState<number[]>([]);
  const [selectedFacultyOpportunity, setSelectedFacultyOpportunity] = useState<number | null>(null);
  const [collaborations, setCollaborations] = useState<Collaboration[]>([]);
  const [collabDraft, setCollabDraft] = useState<Record<number,string>>({});
  const [collaborationFeedbackDraft, setCollaborationFeedbackDraft] = useState<Record<number,string>>({});
  const [outputDraft, setCollaborationOutputDraft] = useState<Record<number,string>>({});

  async function load() {
    setError('');
    try {
      const [opportunityData, applicationData, skillData, learningProgramData, internshipData, facultyOpportunityData, collaborationData] = await Promise.all([
        api<Opportunity[]>('/opportunities'),
        api<Application[]>('/applications'),
        api<Skill[]>('/skills'),
        api<LearningProgram[]>('/industry/learning-programs/mine'),
        api<Internship[]>('/internships'),
        api<FacultyOpportunity[]>('/faculty-opportunities/mine'),
        api<Collaboration[]>('/collaborations'),
      ]);
      setOpps(opportunityData.filter((x) => x.owner_id === userId));
      setApps(applicationData);
      setSkills(skillData);
      setLearningPrograms(learningProgramData || []);
      setInternships(internshipData || []);
      setFacultyOpportunities(facultyOpportunityData || []);
      setCollaborations(collaborationData || []);
    } catch (e: any) {
      setError(e.message || 'Unable to load company data.');
    }
  }

  useEffect(() => {
    load();
  }, [userId]);

  function addSkill(skillId: number) {
    if (!skillId || selectedSkillIds.includes(skillId)) return;
    setSelectedSkillIds((current) => [...current, skillId]);
    setRequiredLevels((current) => ({ ...current, [skillId]: 80 }));
  }

  function removeSkill(skillId: number) {
    setSelectedSkillIds((current) => current.filter((id) => id !== skillId));
    setRequiredLevels((current) => {
      const next = { ...current };
      delete next[skillId];
      return next;
    });
  }

  function setSkillRequiredLevel(skillId: number, level: number) {
    const safeLevel = Math.max(1, Math.min(100, Math.round(level || 0)));
    setRequiredLevels((current) => ({ ...current, [skillId]: safeLevel }));
  }

  async function createOpportunity(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    setNotice('');
    setPublishing(true);

    // React does not guarantee e.currentTarget after an awaited request.
    // Capture the form element before the API call so reset() is always safe.
    const formElement = e.currentTarget;
    try {
      const form = new FormData(formElement);
      const selectedSkills = selectedSkillIds
        .map((skillId) => skills.find((skill) => skill.id === skillId))
        .filter(Boolean) as Skill[];

      if (!selectedSkills.length) {
        throw new Error('Select at least one AYUSH skill requirement.');
      }

      const locationType = String(form.get('location_type') || '');
      const locationPlace = String(form.get('location_place') || '').trim();
      if (!locationType) {
        throw new Error('Select a location mode.');
      }
      if (!locationPlace) {
        throw new Error('Enter the city or facility location.');
      }

      const location = `${locationType} — ${locationPlace}`;

      // The backend stores a required level for each skill and uses it
      // during explainable candidate matching. 80% is the default, but
      // organisations can define a different threshold per skill.
      const requirements = selectedSkills.map((skill) => ({
        skill_id: skill.id,
        required_level: requiredLevels[skill.id] ?? 80,
      }));

      const createdOpportunity = await api<{ id: number }>('/opportunities', {
        method: 'POST',
        body: JSON.stringify({
          title: form.get('title'),
          description: form.get('description'),
          opportunity_type: form.get('type'),
          location,
          requirements,
        }),
      });

      await api(`/opportunities/${createdOpportunity.id}/eligibility`, {
        method: 'PATCH',
        body: JSON.stringify({
          required_education: form.get('required_education'),
          minimum_year: form.get('minimum_year') || null,
          minimum_cgpa: form.get('minimum_cgpa') || null,
          eligibility_notes: form.get('eligibility_notes'),
        }),
      });

      formElement.reset();
      setSelectedSkillIds([]);
      setRequiredLevels({});
      setNotice('Opportunity published successfully. Students can now see it.');
      await load();
    } catch (e: any) {
      setError(e.message || 'Could not publish opportunity.');
    } finally {
      setPublishing(false);
    }
  }

  function addProgramSkill(skillId: number) {
    if (!skillId || programSkillIds.includes(skillId)) return;
    setProgramSkillIds((current) => [...current, skillId]);
  }

  function removeProgramSkill(skillId: number) {
    setProgramSkillIds((current) => current.filter((id) => id !== skillId));
  }


  async function createFacultyOpportunity(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError(''); setNotice('');
    try {
      if (!facultySkillIds.length) throw new Error('Select at least one AYUSH skill connected to this opportunity.');
      const form = new FormData(e.currentTarget);
      await api('/faculty-opportunities', { method:'POST', body:JSON.stringify({
        title:form.get('title'), description:form.get('description'), opportunity_type:form.get('opportunity_type'), ayush_focus:form.get('ayush_focus'),
        location:form.get('location'), delivery_mode:form.get('delivery_mode'), duration:form.get('duration'), eligibility:form.get('eligibility'),
        registration_url:form.get('registration_url'), skills:facultySkillIds,
      }) });
      setFacultySkillIds([]); setNotice('Faculty opportunity published successfully.'); await load(); setPage('Faculty Programs');
    } catch(e:any) { setError(e.message || 'Could not publish the faculty opportunity.'); }
  }

  async function loadFacultyApplications(opportunityId:number) {
    setSelectedFacultyOpportunity(opportunityId); setError('');
    try { setFacultyApplications(await api<FacultyOpportunityApplication[]>(`/faculty-opportunities/${opportunityId}/applications`)); }
    catch(e:any) { setError(e.message || 'Could not load faculty applications.'); }
  }

  async function updateFacultyApplication(applicationId:number, status:string) {
    try { await api(`/faculty-opportunity-applications/${applicationId}`, {method:'PATCH', body:JSON.stringify({status})}); setNotice('Faculty application updated.'); if(selectedFacultyOpportunity) await loadFacultyApplications(selectedFacultyOpportunity); }
    catch(e:any) { setError(e.message || 'Could not update faculty application.'); }
  }

  async function createLearningProgram(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    setNotice('');
    setProgramPublishing(true);

    const formElement = e.currentTarget;

    try {
      const form = new FormData(formElement);

      if (!programSkillIds.length) {
        throw new Error('Select at least one AYUSH skill the program will develop.');
      }

      const skillsPayload = programSkillIds.map((skillId) => ({
        skill_id: skillId,
      }));

      await api('/industry/learning-programs', {
        method: 'POST',
        body: JSON.stringify({
          title: form.get('title'),
          description: form.get('description'),
          program_type: form.get('program_type'),
          ayush_focus: form.get('ayush_focus'),
          duration: form.get('duration'),
          delivery_mode: form.get('delivery_mode'),
          eligibility: form.get('eligibility'),
          skills: skillsPayload,
          registration_deadline: form.get('registration_deadline') || null,
          certificate_available: form.get('certificate_available') === 'on',
          registration_url: form.get('registration_url'),
        }),
      });

      formElement.reset();
      setProgramSkillIds([]);
      setNotice('AYUSH learning program published successfully.');
      await load();
    } catch (e: any) {
      setError(e.message || 'Could not publish the learning program.');
    } finally {
      setProgramPublishing(false);
    }
  }

  async function viewMatches(opportunityId: number) {
    setSelected(opportunityId);
    setLoadingMatches(true);
    setError('');
    try {
      const data = await api<Candidate[]>(`/opportunities/${opportunityId}/matches`);
      setMatches(data);
    } catch (e: any) {
      setError(e.message || 'Could not load candidate matches.');
    } finally {
      setLoadingMatches(false);
    }
  }

  async function updateStatus(applicationId: number, status: string) {
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

  async function updateInternship(id: number, payload: Record<string, unknown>) {
    setInternshipBusy(id);
    setError('');
    try {
      const updated = await api<Internship>(`/internships/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
      setInternships((items) => items.map((item) => item.id === id ? updated : item));
      setNotice('Internship lifecycle updated.');
    } catch (e: any) {
      setError(e.message || 'Unable to update internship.');
    } finally {
      setInternshipBusy(null);
    }
  }

  async function addMilestone(internship: Internship) {
    const title = (milestoneDraft[internship.id] || '').trim();
    if (!title) return;
    setInternshipBusy(internship.id);
    try {
      const updated = await api<Internship>(`/internships/${internship.id}/milestones`, {
        method: 'POST',
        body: JSON.stringify({ title, description: 'Internship checkpoint' }),
      });
      setInternships((items) => items.map((item) => item.id === internship.id ? updated : item));
      setMilestoneDraft((draft) => ({ ...draft, [internship.id]: '' }));
    } catch (e: any) {
      setError(e.message || 'Unable to add milestone.');
    } finally {
      setInternshipBusy(null);
    }
  }

  async function updateMilestone(internship: Internship, milestoneId: number, status: string) {
    try {
      const updated = await api<Internship>(`/internships/milestones/${milestoneId}`, { method: 'PATCH', body: JSON.stringify({ status }) });
      setInternships((items) => items.map((item) => item.id === internship.id ? updated : item));
    } catch (e: any) {
      setError(e.message || 'Unable to update milestone.');
    }
  }

  async function addFeedback(internship: Internship) {
    const feedback = (feedbackDraft[internship.id] || '').trim();
    if (!feedback) return;
    try {
      const updated = await api<Internship>(`/internships/${internship.id}/feedback`, {
        method: 'POST',
        body: JSON.stringify({ feedback }),
      });
      setInternships((items) => items.map((item) => item.id === internship.id ? updated : item));
      setFeedbackDraft((draft) => ({ ...draft, [internship.id]: '' }));
    } catch (e: any) {
      setError(e.message || 'Unable to save feedback.');
    }
  }

  async function startCollaboration(applicationId:number){
    try{const updated=await api<Collaboration>(`/faculty-opportunity-applications/${applicationId}/start-collaboration`,{method:'POST'});setCollaborations(xs=>{const found=xs.some(x=>x.id===updated.id);return found?xs.map(x=>x.id===updated.id?updated:x):[updated,...xs]});setNotice('Collaboration started.');}catch(e:any){setError(e.message||'Could not start collaboration.');}
  }
  async function updateCollaboration(id:number,payload:Record<string,unknown>){
    try{const updated=await api<Collaboration>(`/collaborations/${id}`,{method:'PATCH',body:JSON.stringify(payload)});setCollaborations(xs=>xs.map(x=>x.id===id?updated:x));setNotice('Collaboration updated.');}catch(e:any){setError(e.message||'Could not update collaboration.');}
  }
  async function addCollaborationMilestone(item:Collaboration){const title=(collabDraft[item.id]||'').trim();if(!title)return;try{const updated=await api<Collaboration>(`/collaborations/${item.id}/milestones`,{method:'POST',body:JSON.stringify({title,description:'Collaboration milestone'})});setCollaborations(xs=>xs.map(x=>x.id===item.id?updated:x));setCollabDraft(d=>({...d,[item.id]:''}));}catch(e:any){setError(e.message||'Could not add milestone.');}}
  async function updateCollaborationMilestone(item:Collaboration,id:number,status:string){try{const updated=await api<Collaboration>(`/collaboration-milestones/${id}`,{method:'PATCH',body:JSON.stringify({status})});setCollaborations(xs=>xs.map(x=>x.id===item.id?updated:x));}catch(e:any){setError(e.message||'Could not update milestone.');}}
  async function addCollaborationFeedback(item:Collaboration){const comments=(collaborationFeedbackDraft[item.id]||'').trim();if(!comments)return;try{const updated=await api<Collaboration>(`/collaborations/${item.id}/feedback`,{method:'POST',body:JSON.stringify({comments,feedback_type:'Progress'})});setCollaborations(xs=>xs.map(x=>x.id===item.id?updated:x));setCollaborationFeedbackDraft(d=>({...d,[item.id]:''}));}catch(e:any){setError(e.message||'Could not save feedback.');}}
  async function addCollaborationOutput(item:Collaboration){const title=(outputDraft[item.id]||'').trim();if(!title)return;try{const updated=await api<Collaboration>(`/collaborations/${item.id}/outputs`,{method:'POST',body:JSON.stringify({title,output_type:'Research output',description:'Collaboration deliverable'})});setCollaborations(xs=>xs.map(x=>x.id===item.id?updated:x));setCollaborationOutputDraft(d=>({...d,[item.id]:''}));}catch(e:any){setError(e.message||'Could not add output.');}}

  const selectedOpportunity = useMemo(
    () => opps.find((x) => x.id === selected),
    [opps, selected],
  );

  const relevantApps = apps.filter((x) =>
    opps.some((o) => o.id === x.opportunity_id),
  );

  if (page === 'Company Profile' || page === 'Profile') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}
        <Card>
          <div className="section-title">Company profile</div>
          <p className="muted form-intro">
            Keep your organisation details current so students and candidates see accurate AYUSH-sector information.
          </p>
          <ProfileForm role={role} userId={userId} onSaved={(message) => setNotice(message)} />
        </Card>
      </div>
    );
  }

  if (page === 'Post Opportunity') {
    const selectedSkills = selectedSkillIds
      .map((skillId) => skills.find((skill) => skill.id === skillId))
      .filter(Boolean) as Skill[];

    return (
      <div className="stack" style={{ maxWidth: 1400 }}>
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}

        <Card>
          <div style={{ padding: 2 }}>
            <div className="section-title" style={{ fontSize: 19, marginBottom: 4 }}>
              Create AYUSH opportunity
            </div>
            <p className="muted form-intro" style={{ marginBottom: 22 }}>
              Post internships, projects, jobs or collaborations in the AYUSH sector. Add the skills required so SkillNova can match you with the right students.
            </p>

            <form onSubmit={createOpportunity} autoComplete="off">
              <div style={twoColumnStyle}>
                <label style={fieldStyle}>
                  Title <span aria-hidden="true">*</span>
                  <input
                    name="title"
                    autoComplete="off"
                    style={inputStyle}
                    placeholder="e.g. AYUSH Product Development Internship"
                    required
                  />
                </label>

                <label style={fieldStyle}>
                  Opportunity type <span aria-hidden="true">*</span>
                  <select name="type" style={inputStyle} defaultValue="" autoComplete="off">
                    <option value="" disabled>Select type</option>
                    <option>Internship</option>
                    <option>Apprenticeship</option>
                    <option>Placement</option>
                    <option>Project</option>
                    <option>Job</option>
                    <option>Collaboration</option>
                    <option>Research</option>
                    <option>Mentorship</option><option>Faculty Internship</option><option>Industrial Training for Faculty</option><option>Faculty Development Programme (FDP)</option><option>Consultancy</option><option>Guest Lecture</option><option>Innovation Challenge</option><option>Live Industry Project</option>
                  </select>
                  <span style={helperStyle}>Internship, Project, Job, Collaboration, Research, etc.</span>
                </label>
              </div>

              <div style={{ ...twoColumnStyle, marginTop: 18 }}>
                <div>
                  <label style={fieldStyle}>
                    Location <span aria-hidden="true">*</span>
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'minmax(150px, 0.42fr) minmax(0, 1fr)', gap: 10, marginTop: 8 }}>
                    <select name="location_type" style={{ ...inputStyle, marginTop: 0 }} defaultValue="" autoComplete="off">
                      <option value="" disabled>Select type</option>
                      <option value="On-site">On-site</option>
                      <option value="Hybrid">Hybrid</option>
                      <option value="Remote">Remote</option>
                    </select>
                    <input
                      name="location_place"
                      autoComplete="off"
                      style={{ ...inputStyle, marginTop: 0 }}
                      placeholder="City / facility (e.g. Hyderabad)"
                    />
                  </div>
                  <span style={helperStyle}>Choose how the student will work, then add the city or AYUSH facility.</span>
                </div>

                <label style={fieldStyle}>
                  Application deadline
                  <input name="deadline" type="date" style={inputStyle} autoComplete="off" />
                </label>
              </div>

              <label style={{ ...fieldStyle, marginTop: 18 }}>
                Description <span aria-hidden="true">*</span>
                <textarea
                  name="description"
                  autoComplete="off"
                  style={{ ...inputStyle, minHeight: 112, resize: 'vertical', lineHeight: 1.5 }}
                  placeholder="Describe the opportunity, responsibilities, learning outcomes, and any other details..."
                  required
                />
              </label>

              <div style={{ ...twoColumnStyle, marginTop: 18 }}>
                <label style={fieldStyle}>
                  Minimum education
                  <select name="required_education" style={inputStyle} defaultValue="">
                    <option value="">Any education</option>
                    <option value="B.Sc, B.Sc (Hons.)">B.Sc / B.Sc (Hons.)</option>
                    <option value="B.Pharm, B.Pharm (Hons.)">B.Pharm</option>
                    <option value="BAMS">BAMS</option>
                    <option value="BHMS">BHMS</option>
                    <option value="BUMS">BUMS</option>
                    <option value="BSMS">BSMS</option>
                    <option value="M.Sc, M.Pharm, M.Tech">Postgraduate</option>
                    <option value="Ph.D.">Ph.D.</option>
                  </select>
                  <span style={helperStyle}>Used by SkillNova's eligibility engine.</span>
                </label>

                <label style={fieldStyle}>
                  Minimum academic year
                  <select name="minimum_year" style={inputStyle} defaultValue="">
                    <option value="">Any year</option>
                    <option value="1">1st Year or above</option>
                    <option value="2">2nd Year or above</option>
                    <option value="3">3rd Year or above</option>
                    <option value="4">4th Year</option>
                  </select>
                </label>
              </div>

              <div style={{ ...twoColumnStyle, marginTop: 18 }}>
                <label style={fieldStyle}>
                  Minimum CGPA
                  <input name="minimum_cgpa" type="number" min="0" max="10" step="0.01" style={inputStyle} placeholder="e.g. 7.0" />
                  <span style={helperStyle}>Leave blank if there is no CGPA requirement.</span>
                </label>
                <label style={fieldStyle}>
                  Eligibility notes
                  <input name="eligibility_notes" style={inputStyle} placeholder="e.g. Prior herbal formulation experience preferred" />
                </label>
              </div>

              <div style={{ marginTop: 18 }}>
                <label style={fieldStyle}>
                  Required AYUSH skills <span aria-hidden="true">*</span>
                  <select
                    style={inputStyle}
                    value=""
                    autoComplete="off"
                    onChange={(e) => addSkill(Number(e.target.value))}
                  >
                    <option value="">Select required skills</option>
                    {skills
                      .filter((skill) => !selectedSkillIds.includes(skill.id))
                      .map((skill) => (
                        <option key={skill.id} value={skill.id}>{skill.name}</option>
                      ))}
                  </select>
                </label>
                <span style={helperStyle}>
                  Choose the key AYUSH skills needed for this opportunity. Set the minimum level for each skill. Only core skills are used for matching.
                </span>

                <div style={{ display: 'grid', gap: 9, marginTop: 11 }}>
                  {selectedSkills.map((skill) => (
                    <div
                      key={skill.id}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'minmax(0, 1fr) 150px auto',
                        alignItems: 'center',
                        gap: 12,
                        padding: '10px 12px',
                        border: '1px solid #dce6ef',
                        borderRadius: 10,
                        background: '#f8fbff',
                      }}
                    >
                      <div>
                        <strong style={{ color: '#25578a', fontSize: 13 }}>{skill.name}</strong>
                        <div style={{ color: '#70829a', fontSize: 11, marginTop: 3 }}>Minimum verified competency</div>
                      </div>
                      <label style={{ ...fieldStyle, fontSize: 12 }}>
                        Required level
                        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginTop: 5 }}>
                          <input
                            type="number"
                            min={1}
                            max={100}
                            value={requiredLevels[skill.id] ?? 80}
                            onChange={(e) => setSkillRequiredLevel(skill.id, Number(e.target.value))}
                            style={{ ...inputStyle, marginTop: 0, padding: '8px 9px' }}
                            aria-label={`Required level for ${skill.name}`}
                          />
                          <span style={{ color: '#52657a', fontSize: 12 }}>%</span>
                        </div>
                      </label>
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => removeSkill(skill.id)}
                        aria-label={`Remove ${skill.name}`}
                        style={{ padding: '8px 11px' }}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>

                {!selectedSkills.length && (
                  <div style={{ marginTop: 10, color: '#8a98a8', fontSize: 12 }}>
                    Suggested AYUSH skills: {ayushSkillHints.join(' · ')}
                  </div>
                )}
              </div>

              <div style={{ marginTop: 18, maxWidth: 'calc(50% - 9px)' }}>
                <label style={fieldStyle}>
                  Stipend / Compensation
                  <input name="compensation" style={inputStyle} placeholder="e.g. ₹10,000/month or Unpaid" autoComplete="off" />
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 26 }}>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => {
                    setSelectedSkillIds([]);
                    setRequiredLevels({});
                    setPage('Dashboard');
                  }}
                  style={{ padding: '11px 20px' }}
                >
                  Cancel
                </button>
                <button className="primary" type="submit" style={{ padding: '11px 22px' }} disabled={publishing}>
                  {publishing ? 'Publishing…' : 'Publish opportunity'}
                </button>
              </div>
            </form>
          </div>
        </Card>
      </div>
    );
  }

  if (page === 'Learning Programs') {
    const selectedProgramSkills = programSkillIds
      .map((skillId) => skills.find((skill) => skill.id === skillId))
      .filter(Boolean) as Skill[];

    return (
      <div className="stack" style={{ maxWidth: 1400 }}>
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}

        <div className="hero">
          <div>
            <div className="eyebrow">AYUSH INDUSTRY LEARNING</div>
            <h2>Industry Learning Programs</h2>
            <p>
              Publish AYUSH training, certification, workshops and mentorship programs
              that help students close skill gaps and build industry-ready evidence.
            </p>
          </div>
          <button className="primary" onClick={() => setPage('Create Learning Program')}>
            + Create learning program
          </button>
        </div>

        <Card>
          <div className="section-title">Your published programs</div>
          {learningPrograms.length ? (
            <div className="list">
              {learningPrograms.map((program) => (
                <div className="gap-row" key={program.id}>
                  <div className="grow">
                    <strong>{program.title}</strong>
                    <div className="muted">
                      {program.program_type} · {program.ayush_focus || 'AYUSH'} · {program.delivery_mode}
                      {program.duration ? ` · ${program.duration}` : ''}
                    </div>
                    <div className="chips" style={{ marginTop: 8 }}>
                      {(program.skills || []).map((item) => (
                        <span className="chip" key={item.skill_id}>
                          {item.skill || skills.find((s) => s.id === item.skill_id)?.name || `Skill ${item.skill_id}`}
                        </span>
                      ))}
                    </div>
                    <div className="muted" style={{ marginTop: 8 }}>
                      {program.certificate_available ? 'Certificate available' : 'Participation program'}
                      {program.enrollment_count !== undefined ? ` · ${program.enrollment_count} enrolled` : ''}
                      {program.status ? ` · ${program.status}` : ''}
                    </div>
                  </div>
                  {program.registration_url && (
                    <a
                      className="secondary"
                      href={program.registration_url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ textDecoration: 'none' }}
                    >
                      Registration link
                    </a>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <Empty
              title="No learning programs yet"
              body="Create your first AYUSH training or certification program so students can discover and enroll in it."
            />
          )}
        </Card>
      </div>
    );
  }

  if (page === 'Create Learning Program') {
    const selectedProgramSkills = programSkillIds
      .map((skillId) => skills.find((skill) => skill.id === skillId))
      .filter(Boolean) as Skill[];

    return (
      <div className="stack" style={{ maxWidth: 1400 }}>
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}

        <Card>
          <div style={{ padding: 2 }}>
            <div className="section-title" style={{ fontSize: 19, marginBottom: 4 }}>
              Create AYUSH learning program
            </div>
            <p className="muted form-intro" style={{ marginBottom: 22 }}>
              Offer structured industry learning that develops specific AYUSH skills.
              Students will be able to discover the program and enroll through SkillNova.
            </p>

            <form onSubmit={createLearningProgram} autoComplete="off">
              <div style={twoColumnStyle}>
                <label style={fieldStyle}>
                  Program title <span aria-hidden="true">*</span>
                  <input
                    name="title"
                    autoComplete="off"
                    style={inputStyle}
                    placeholder="e.g. Herbal Formulation & Quality Control Training"
                    required
                  />
                </label>

                <label style={fieldStyle}>
                  Program type <span aria-hidden="true">*</span>
                  <select name="program_type" style={inputStyle} defaultValue="Training" required>
                    {learningProgramTypes.map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div style={{ ...twoColumnStyle, marginTop: 18 }}>
                <label style={fieldStyle}>
                  AYUSH focus <span aria-hidden="true">*</span>
                  <select name="ayush_focus" style={inputStyle} defaultValue="" required>
                    <option value="" disabled>Select AYUSH focus</option>
                    {learningAyushFocusOptions.map((focus) => (
                      <option key={focus} value={focus}>{focus}</option>
                    ))}
                  </select>
                </label>

                <label style={fieldStyle}>
                  Duration
                  <input
                    name="duration"
                    autoComplete="off"
                    style={inputStyle}
                    placeholder="e.g. 6 weeks / 30 hours"
                  />
                </label>
              </div>

              <div style={{ ...twoColumnStyle, marginTop: 18 }}>
                <label style={fieldStyle}>
                  Delivery mode <span aria-hidden="true">*</span>
                  <select name="delivery_mode" style={inputStyle} defaultValue="Remote" required>
                    <option>Remote</option>
                    <option>On-site</option>
                    <option>Hybrid</option>
                  </select>
                </label>

                <label style={fieldStyle}>
                  Registration deadline
                  <input name="registration_deadline" type="date" style={inputStyle} />
                </label>
              </div>

              <label style={{ ...fieldStyle, marginTop: 18 }}>
                Description <span aria-hidden="true">*</span>
                <textarea
                  name="description"
                  autoComplete="off"
                  style={{ ...inputStyle, minHeight: 120, resize: 'vertical', lineHeight: 1.5 }}
                  placeholder="Describe the training content, learning outcomes, practical exposure and AYUSH industry context..."
                  required
                />
              </label>

              <label style={{ ...fieldStyle, marginTop: 18 }}>
                Eligibility
                <textarea
                  name="eligibility"
                  autoComplete="off"
                  style={{ ...inputStyle, minHeight: 82, resize: 'vertical', lineHeight: 1.5 }}
                  placeholder="e.g. B.Sc./B.Pharm/BAMS/BHMS students with basic pharmacognosy knowledge"
                />
              </label>

              <div style={{ marginTop: 18 }}>
                <label style={fieldStyle}>
                  Skills developed <span aria-hidden="true">*</span>
                  <select
                    style={inputStyle}
                    value=""
                    onChange={(e) => addProgramSkill(Number(e.target.value))}
                    autoComplete="off"
                  >
                    <option value="">Select skills developed by this program</option>
                    {skills
                      .filter((skill) => !programSkillIds.includes(skill.id))
                      .map((skill) => (
                        <option key={skill.id} value={skill.id}>{skill.name}</option>
                      ))}
                  </select>
                </label>
                <span style={helperStyle}>
                  These skills connect the program to SkillNova's AYUSH skill-gap and learning pathway.
                </span>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 11 }}>
                  {selectedProgramSkills.map((skill) => (
                    <span
                      className="chip"
                      key={skill.id}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '7px 10px' }}
                    >
                      {skill.name}
                      <button
                        type="button"
                        onClick={() => removeProgramSkill(skill.id)}
                        aria-label={`Remove ${skill.name}`}
                        style={{
                          border: 0,
                          background: 'transparent',
                          cursor: 'pointer',
                          padding: 0,
                          fontWeight: 800,
                          color: '#64748b',
                        }}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>

                {!selectedProgramSkills.length && (
                  <div style={{ marginTop: 10, color: '#8a98a8', fontSize: 12 }}>
                    Suggested: Pharmacognosy · Quality Control · Regulatory Compliance · Medicinal Plant Identification · Documentation · Data Analysis
                  </div>
                )}
              </div>

              <div style={{ ...twoColumnStyle, marginTop: 18 }}>
                <label style={fieldStyle}>
                  Registration URL
                  <input
                    name="registration_url"
                    type="url"
                    autoComplete="off"
                    style={inputStyle}
                    placeholder="https://..."
                  />
                </label>

                <label style={{ ...fieldStyle, display: 'flex', alignItems: 'center', gap: 10, marginTop: 31 }}>
                  <input
                    name="certificate_available"
                    type="checkbox"
                    style={{ width: 17, height: 17 }}
                  />
                  Certificate available on completion
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 26 }}>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => {
                    setProgramSkillIds([]);
                    setPage('Learning Programs');
                  }}
                  style={{ padding: '11px 20px' }}
                >
                  Cancel
                </button>
                <button className="primary" type="submit" disabled={programPublishing} style={{ padding: '11px 22px' }}>
                  {programPublishing ? 'Publishing…' : 'Publish learning program'}
                </button>
              </div>
            </form>
          </div>
        </Card>
      </div>
    );
  }


  if (page === 'Faculty Programs') {
    return <div className="stack" style={{maxWidth:1400}}>{error&&<div className="error">{error}</div>}{notice&&<div className="success-banner">✓ {notice}</div>}
      <div className="hero"><div><div className="eyebrow">AYUSH ACADEMIA–INDUSTRY COLLABORATION</div><h2>Faculty programs</h2><p>Offer faculty internships, industrial training, FDPs, consultancy, collaborative research, guest lectures, innovation challenges and live industry projects.</p></div><button className="primary" onClick={()=>setPage('Create Faculty Program')}>+ Create faculty program</button></div>
      <Card><div className="section-title">Your faculty programs</div>{facultyOpportunities.length?<div className="list">{facultyOpportunities.map(o=><div className="gap-row" key={o.id}><div className="grow"><strong>{o.title}</strong><div className="muted">{o.opportunity_type} · {o.ayush_focus} · {o.delivery_mode} · {o.location}</div><div className="chips" style={{marginTop:8}}>{o.skills.map(s=><span className="chip" key={s.skill_id}>{s.skill}</span>)}</div></div><button className="secondary" onClick={()=>loadFacultyApplications(o.id)}>View faculty applications</button></div>)}</div>:<Empty title="No faculty programs yet" body="Create an AYUSH academia–industry program to start receiving faculty applications."/>}</Card>
      {selectedFacultyOpportunity!==null&&<Card><div className="section-title">Faculty applications</div>{facultyApplications.length?<div className="list">{facultyApplications.map(a=><div className="candidate" key={a.id}><div className="grow"><strong>{a.academician_name}</strong><div className="muted">{a.academician_email} · {a.message}</div></div><div style={{display:'flex',gap:8,flexWrap:'wrap'}}><span className="chip">{a.status}</span>{a.status==='Applied'||a.status==='Under Review'?<><button className="secondary" onClick={()=>updateFacultyApplication(a.id,'Under Review')}>Review</button><button className="primary" onClick={()=>updateFacultyApplication(a.id,'Accepted')}>Accept</button><button className="secondary" onClick={()=>updateFacultyApplication(a.id,'Rejected')}>Reject</button></>:a.status==='Accepted'?<button className="primary" onClick={()=>startCollaboration(a.id)}>Start collaboration</button>:null}</div></div>)}</div>:<Empty title="No applications yet" body="Faculty applications will appear here when academic professionals apply."/>}</Card>}
    </div>;
  }

  if (page === 'Create Faculty Program') {
    return <div className="stack" style={{maxWidth:1100}}><Card><div className="section-title">Create AYUSH faculty opportunity</div><p className="muted form-intro">Publish a faculty-facing academia–industry opportunity with its AYUSH focus and connected skills.</p><form className="grid-form" onSubmit={createFacultyOpportunity} autoComplete="off">
      <label>Title<input name="title" placeholder="e.g. Faculty Industrial Training in Herbal Quality Control" required /></label>
      <label>Opportunity type<select name="opportunity_type"><option>Faculty Internship</option><option>Industrial Training for Faculty</option><option>Faculty Development Programme (FDP)</option><option>Consultancy</option><option>Collaborative Research</option><option>Guest Lecture</option><option>Innovation Challenge</option><option>Live Industry Project</option></select></label>
      <label>AYUSH focus<select name="ayush_focus"><option>Ayurveda</option><option>Yoga & Naturopathy</option><option>Unani</option><option>Siddha</option><option>Homoeopathy</option><option>Sowa-Rigpa</option><option>Medicinal Plants & Pharmacognosy</option><option>AYUSH Drug Development</option><option>Quality Control & Standardization</option><option>Clinical & Translational Research</option></select></label>
      <label>Location<input name="location" placeholder="Hyderabad / Remote / AYUSH facility" required /></label>
      <label>Delivery mode<select name="delivery_mode"><option>Hybrid</option><option>On-site</option><option>Remote</option></select></label><label>Duration<input name="duration" placeholder="e.g. 2 weeks / 30 hours" /></label>
      <label className="full">Eligibility<textarea name="eligibility" placeholder="Who can participate?" /></label><label className="full">Description<textarea name="description" placeholder="Describe objectives, faculty contribution, expected outputs and AYUSH context." required /></label><label className="full">Registration / details URL<input name="registration_url" type="url" placeholder="https://..." /></label>
      <label className="full">Connected AYUSH skills<select value="" onChange={e=>{const id=Number(e.target.value);if(id&&!facultySkillIds.includes(id))setFacultySkillIds(x=>[...x,id]);}}><option value="">Select a skill</option>{skills.filter(s=>!facultySkillIds.includes(s.id)).map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select><div className="chips" style={{marginTop:8}}>{facultySkillIds.map(id=>{const s=skills.find(x=>x.id===id);return s?<span className="chip" key={id}>{s.name} <button type="button" onClick={()=>setFacultySkillIds(x=>x.filter(v=>v!==id))}>×</button></span>:null})}</div></label>
      <button className="primary">Publish faculty program</button></form></Card></div>;
  }

  if (page === 'Opportunities') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}
        <div className="hero">
          <div>
            <div className="eyebrow">AYUSH INDUSTRY INTELLIGENCE</div>
            <h2>Your published opportunities</h2>
            <p>Every AYUSH opportunity is connected to skill requirements and the live candidate graph.</p>
          </div>
          <button className="primary" onClick={() => setPage('Post Opportunity')}>
            + Create opportunity
          </button>
        </div>
        <Card>
          <div className="section-title">Your opportunities</div>
          {opps.length ? (
            <div className="list">
              {opps.map((o) => (
                <div className="gap-row" key={o.id}>
                  <div className="grow">
                    <strong>{o.title}</strong>
                    <div className="muted">{o.opportunity_type} · {o.location} · {o.requirements.length} required skills</div>
                    <div className="chips" style={{ marginTop: 8 }}>
                      {o.requirements.map((r) => <span className="chip" key={r.skill_id}>{r.skill} · {r.required_level}%</span>)}
                    </div>
                  </div>
                  <button className="secondary" onClick={() => viewMatches(o.id)}>View matches</button>
                </div>
              ))}
            </div>
          ) : (
            <Empty title="No opportunities yet" body="Create and publish your first AYUSH opportunity to start receiving skill-based matches." />
          )}
        </Card>
      </div>
    );
  }

  if (page === 'Matched Students' || page === 'Candidate Matching') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        <Card>
          <div className="section-title">Candidate Matching</div>
          <p className="muted form-intro">Compare students against industry-defined AYUSH requirements using verified skills, readiness and explainable gaps.</p>
          {opps.length ? (
            <div className="list">
              {opps.map((o) => (
                <div className="gap-row" key={o.id}>
                  <div className="grow"><strong>{o.title}</strong><div className="muted">{o.requirements.length} required AYUSH skills</div></div>
                  <button className="secondary" onClick={() => viewMatches(o.id)}>Find candidates</button>
                </div>
              ))}
            </div>
          ) : <Empty title="No opportunities" body="Publish an AYUSH opportunity first." />}
        </Card>

        {selected && (
          <Card>
            <div className="section-title">Candidate ranking{selectedOpportunity ? ` · ${selectedOpportunity.title}` : ''}</div>
            {loadingMatches ? <p className="muted">Calculating live skill matches…</p> : matches.length ? (
              <div className="list">
                {matches.map((candidate) => (
                  <div className="candidate" key={candidate.student_id}>
                    <div className="grow">
                      <strong>{candidate.name}</strong>
                      <div className="muted">{candidate.email} · {candidate.verified_skills} verified skills · {candidate.readiness}% readiness</div>
                      <div style={{ marginTop: 12 }}>
                        <strong style={{ fontSize: 12 }}>Skill-by-skill comparison</strong>
                        <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
                          {(candidate.skill_comparisons || []).map((x) => (
                            <div
                              key={x.skill_id}
                              style={{
                                display: 'grid',
                                gridTemplateColumns: 'minmax(0, 1fr) auto auto',
                                alignItems: 'center',
                                gap: 12,
                                padding: '9px 11px',
                                border: '1px solid #e3e9ef',
                                borderRadius: 9,
                                background: x.meets_requirement ? '#f6fbf8' : '#fff9f7',
                              }}
                            >
                              <div>
                                <strong style={{ fontSize: 13 }}>{x.skill}</strong>
                                <div className="muted" style={{ marginTop: 2 }}>
                                  {x.verified ? 'Academically verified' : 'Not verified'}
                                </div>
                              </div>
                              <strong style={{ fontSize: 13 }}>{x.current}% / {x.required}%</strong>
                              <span style={{ fontSize: 12, fontWeight: 700, color: x.meets_requirement ? '#28734a' : '#a54b3f' }}>
                                {x.meets_requirement ? 'Meets' : `Gap ${x.gap}%`}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {candidate.missing_skills.length > 0 && (
                        <div style={{ marginTop: 10 }}>
                          <span className="muted">Missing requirements: </span>
                          <span className="muted">
                            {candidate.missing_skills.map((x) => `${x.skill} (${x.current}% / ${x.required}%)`).join(' · ')}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="candidate-score">{candidate.score}%</div>
                  </div>
                ))}
              </div>
            ) : <Empty title="No student data yet" body="Students will appear here once they have profiles, assessed skills and academic verification." />}
          </Card>
        )}
      </div>
    );
  }

  if (page === 'Internships') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}
        <Card>
          <div className="eyebrow">AYUSH INTERNSHIP LIFECYCLE</div>
          <h2>Manage active internships</h2>
          <p className="muted form-intro">
            Move selected students from onboarding to active work, milestones, mentor feedback and completion records.
          </p>
        </Card>
        {internships.length ? internships.map((internship) => (
          <Card key={internship.id}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
              <div className="grow">
                <div className="eyebrow">{internship.opportunity_title}</div>
                <h3 style={{ margin: '5px 0' }}>{internship.student_name}</h3>
                <div className="muted">{internship.student_email}</div>
              </div>
              <div style={{ minWidth: 180 }}>
                <strong>{internship.progress_percent}% complete</strong>
                <div className="progress" style={{ marginTop: 8 }}><span style={{ width: `${internship.progress_percent}%` }} /></div>
                <div className="status" style={{ marginTop: 8 }}>{internship.status}</div>
              </div>
            </div>

            <div className="two-col" style={{ marginTop: 18 }}>
              <label style={fieldStyle}>Mentor name<input style={inputStyle} value={internship.mentor_name} onChange={(e) => setInternships((items) => items.map((x) => x.id === internship.id ? { ...x, mentor_name: e.target.value } : x))} onBlur={() => updateInternship(internship.id, { mentor_name: internship.mentor_name })} /></label>
              <label style={fieldStyle}>Mentor email<input style={inputStyle} value={internship.mentor_email} onChange={(e) => setInternships((items) => items.map((x) => x.id === internship.id ? { ...x, mentor_email: e.target.value } : x))} onBlur={() => updateInternship(internship.id, { mentor_email: internship.mentor_email })} /></label>
              <label style={fieldStyle}>Start date<input style={inputStyle} type="date" value={internship.start_date ? internship.start_date.slice(0, 10) : ''} onChange={(e) => updateInternship(internship.id, { start_date: e.target.value })} /></label>
              <label style={fieldStyle}>Expected completion<input style={inputStyle} type="date" value={internship.expected_end_date ? internship.expected_end_date.slice(0, 10) : ''} onChange={(e) => updateInternship(internship.id, { expected_end_date: e.target.value })} /></label>
            </div>

            <div style={{ marginTop: 18 }}>
              <label style={fieldStyle}>Progress</label>
              <input style={{ width: '100%', marginTop: 10 }} type="range" min="0" max="100" value={internship.progress_percent} onChange={(e) => setInternships((items) => items.map((x) => x.id === internship.id ? { ...x, progress_percent: Number(e.target.value) } : x))} onMouseUp={(e) => updateInternship(internship.id, { progress_percent: Number((e.target as HTMLInputElement).value), status: Number((e.target as HTMLInputElement).value) === 100 ? 'Completed' : 'Ongoing' })} />
            </div>

            <div style={{ marginTop: 20 }}>
              <div className="section-title">Milestones</div>
              {internship.milestones.map((milestone) => (
                <div className="gap-row" key={milestone.id}>
                  <div className="grow"><strong>{milestone.title}</strong><div className="muted">{milestone.description}</div></div>
                  <select style={{ ...inputStyle, width: 150, marginTop: 0 }} value={milestone.status} onChange={(e) => updateMilestone(internship, milestone.id, e.target.value)}>
                    <option>Pending</option><option>In Progress</option><option>Completed</option>
                  </select>
                </div>
              ))}
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <input style={inputStyle} placeholder="Add a milestone: literature review, formulation testing..." value={milestoneDraft[internship.id] || ''} onChange={(e) => setMilestoneDraft((draft) => ({ ...draft, [internship.id]: e.target.value }))} />
                <button className="secondary" disabled={internshipBusy === internship.id} onClick={() => addMilestone(internship)}>Add</button>
              </div>
            </div>

            <div style={{ marginTop: 20 }}>
              <div className="section-title">Mentor feedback</div>
              {internship.feedback.map((item) => <div className="gap-row" key={item.id}><div><strong>{item.author_name || item.author_role}</strong><div className="muted">{item.feedback}</div></div></div>)}
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <input style={inputStyle} placeholder="Record mentor feedback or guidance" value={feedbackDraft[internship.id] || ''} onChange={(e) => setFeedbackDraft((draft) => ({ ...draft, [internship.id]: e.target.value }))} />
                <button className="secondary" onClick={() => addFeedback(internship)}>Save</button>
              </div>
            </div>

            <div style={{ marginTop: 20, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button className="secondary" disabled={internshipBusy === internship.id} onClick={() => updateInternship(internship.id, { status: 'Ongoing' })}>Start internship</button>
              <button className="primary" disabled={internshipBusy === internship.id} onClick={() => updateInternship(internship.id, { status: 'Completed', progress_percent: 100 })}>Mark completed</button>
            </div>
          </Card>
        )) : <Card><Empty title="No active internships" body="Select a student for an Internship or Apprenticeship opportunity and the lifecycle record will appear here." /></Card>}
      </div>
    );
  }

  if (page === 'Applications') {
    return (
      <Card>
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}
        <div className="section-title">Applications</div>
        <p className="muted form-intro">Review students who applied to your AYUSH opportunities and move them through the hiring or collaboration workflow.</p>
        {relevantApps.length ? (
          <div className="list">
            {relevantApps.map((application) => (
              <div className="candidate" key={application.id}>
                <div className="grow">
                  <strong>{application.student_name || 'Student'}</strong>
                  <div className="muted">{application.student_email} · {application.opportunity_title} · Applied {new Date(application.created_at).toLocaleDateString()}</div>
                  <div className="muted" style={{ marginTop: 6 }}>Status: <strong>{application.status}</strong></div>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                  <button className="secondary" onClick={() => updateStatus(application.id, 'Under Review')}>Review</button>
                  <button className="secondary" onClick={() => updateStatus(application.id, 'Shortlisted')}>Shortlist</button>
                  <button className="primary" onClick={() => updateStatus(application.id, 'Selected')}>Select</button>
                  <button className="secondary" onClick={() => updateStatus(application.id, 'Rejected')}>Reject</button>
                </div>
              </div>
            ))}
          </div>
        ) : <Empty title="No applications" body="Student applications will appear here after someone applies to your AYUSH opportunities." />}
      </Card>
    );
  }

  if (page === 'Collaborations') {
    return <div className="stack">
      {error&&<div className="error">{error}</div>}{notice&&<div className="success-banner">✓ {notice}</div>}
      <div className="hero"><div><div className="eyebrow">AYUSH ACADEMIA × INDUSTRY</div><h2>Collaboration management</h2><p>Turn accepted faculty opportunities into structured collaborations with objectives, milestones, feedback and evidence of outputs.</p></div></div>
      {collaborations.length?collaborations.map(item=><Card key={item.id}>
        <div style={{display:'flex',justifyContent:'space-between',gap:16,alignItems:'flex-start'}}><div><div className="section-title">{item.title}</div><div className="muted">{item.collaboration_type} · {item.ayush_focus} · Faculty: {item.academician.name}</div></div><select value={item.status} onChange={e=>updateCollaboration(item.id,{status:e.target.value})}><option>Planned</option><option>Active</option><option>On Hold</option><option>Completed</option><option>Cancelled</option></select></div>
        <p className="muted" style={{marginTop:10}}>{item.objective}</p>
        <div className="two-col"><div><div className="section-title">Milestones</div>{item.milestones.map(m=><div className="gap-row" key={m.id}><div className="grow"><strong>{m.title}</strong><div className="muted">{m.description}</div></div><select value={m.status} onChange={e=>updateCollaborationMilestone(item,m.id,e.target.value)}><option>Planned</option><option>In Progress</option><option>Completed</option><option>Blocked</option></select></div>)}<div style={{display:'flex',gap:8,marginTop:10}}><input value={collabDraft[item.id]||''} onChange={e=>setCollabDraft(d=>({...d,[item.id]:e.target.value}))} placeholder="Add milestone"/><button className="secondary" onClick={()=>addCollaborationMilestone(item)}>Add</button></div></div>
        <div><div className="section-title">Outputs</div>{item.outputs.length?item.outputs.map(o=><div className="gap-row" key={o.id}><div className="grow"><strong>{o.title}</strong><div className="muted">{o.output_type}</div></div><span className="chip">{o.verified?'Verified':'Recorded'}</span></div>):<div className="muted">No outputs recorded.</div>}<div style={{display:'flex',gap:8,marginTop:10}}><input value={outputDraft[item.id]||''} onChange={e=>setCollaborationOutputDraft(d=>({...d,[item.id]:e.target.value}))} placeholder="Add output"/><button className="secondary" onClick={()=>addCollaborationOutput(item)}>Add</button></div></div></div>
        <div className="section-title" style={{marginTop:18}}>Progress feedback</div>{item.feedback.map(f=><div className="muted" key={f.id} style={{padding:'8px 0',borderBottom:'1px solid #edf1f5'}}><strong>{f.author.name}</strong> · {f.feedback_type}<br/>{f.comments}</div>)}<div style={{display:'flex',gap:8,marginTop:10}}><input value={collaborationFeedbackDraft[item.id]||''} onChange={e=>setCollaborationFeedbackDraft(d=>({...d,[item.id]:e.target.value}))} placeholder="Record mentor / partner feedback"/><button className="secondary" onClick={()=>addCollaborationFeedback(item)}>Save feedback</button></div>
      </Card>):<Empty title="No collaborations yet" body="Accept a faculty application and start a collaboration to begin tracking the work here."/>}
    </div>;
  }

  return (
    <div className="stack">
      {error && <div className="error">{error}</div>}
      {notice && <div className="success-banner">✓ {notice}</div>}
      <div className="hero">
        <div>
          <div className="eyebrow">AYUSH INDUSTRY INTELLIGENCE</div>
          <h2>Find verified AYUSH skills, not just resumes.</h2>
          <p>Create AYUSH opportunities and compare candidates using verified skills, readiness and the same skill graph used by students.</p>
        </div>
        <button className="primary" onClick={() => setPage('Post Opportunity')}>+ Create opportunity</button>
      </div>
      <div className="stats">
        <Stat label="Published opportunities" value={opps.length} />
        <Stat label="Applications" value={relevantApps.length} />
        <Stat label="Skill taxonomy" value={skills.length} />
      </div>
      <Card>
        <div className="section-title">Your opportunities</div>
        {opps.length ? (
          <div className="list">
            {opps.slice(0, 5).map((o) => (
              <div className="gap-row" key={o.id}>
                <div className="grow"><strong>{o.title}</strong><div className="muted">{o.opportunity_type} · {o.location}</div></div>
                <button className="secondary" onClick={() => viewMatches(o.id)}>View matches</button>
              </div>
            ))}
          </div>
        ) : <Empty title="Start your AYUSH talent ecosystem" body="Publish your first opportunity to activate skill-based candidate matching." />}
      </Card>
    </div>
  );
}

function ProfileForm({ role, userId, onSaved }: { role: Role; userId: number; onSaved: (message: string) => void }) {
  const [profile, setProfile] = useState<CompanyProfile>({});
  const [saving, setSaving] = useState(false);
  const [profileError, setProfileError] = useState('');
  const [verification, setVerification] = useState<CompanyVerification>({ status: 'Not Submitted' });
  const [verificationBusy, setVerificationBusy] = useState(false);

  useEffect(() => {
    api<CompanyProfile>('/profile')
      .then((data) => setProfile(data || {}))
      .catch((e: any) => setProfileError(e.message || 'Profile could not be loaded. You can still enter the details below.'));
  }, []);

  useEffect(() => {
    if (role !== 'company') return;
    api<CompanyVerification>('/company/verification')
      .then((data) => setVerification(data || { status: 'Not Submitted' }))
      .catch(() => setVerification({ status: 'Not Submitted' }));
  }, [role, userId]);

  async function submitVerification() {
    setVerificationBusy(true);
    setProfileError('');
    try {
      const data = await api<CompanyVerification & { message?: string }>('/company/verification', { method: 'POST' });
      setVerification(data);
      onSaved(data.message || 'Company verification submitted for review.');
    } catch (e: any) {
      setProfileError(e.message || 'Could not submit company verification.');
    } finally {
      setVerificationBusy(false);
    }
  }

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setProfileError('');
    try {
      const form = new FormData(e.currentTarget);
      await api('/profile', {
        method: 'PUT',
        body: JSON.stringify({
          name: form.get('organisation_name'),
          education: form.get('industry_field'),
          year_degree: form.get('designation'),
          career_interests: form.get('ayush_focus'),
          research_experience: form.get('collaboration_focus'),
          achievements: form.get('organisation_notes'),
        }),
      });
      setProfile({
        name: String(form.get('organisation_name') || ''),
        education: String(form.get('industry_field') || ''),
        year_degree: String(form.get('designation') || ''),
        career_interests: String(form.get('ayush_focus') || ''),
        research_experience: String(form.get('collaboration_focus') || ''),
        achievements: String(form.get('organisation_notes') || ''),
      });
      onSaved(`${role === 'company' ? 'Company' : 'Academic'} profile saved.`);
    } catch (e: any) {
      setProfileError(e.message || 'Could not save profile.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="grid-form" onSubmit={save} autoComplete="off">
      {profileError && <div className="error full">{profileError}</div>}
      <label>
        Organisation name
        <input name="organisation_name" autoComplete="off" defaultValue={profile.name || ''} placeholder="e.g. AYUSH Herbal Research Centre" required />
      </label>
      <label>
        Industry / field
        <select name="industry_field" autoComplete="off" defaultValue={profile.education || ''} style={inputStyle}>
          <option value="">Select industry / field</option>
          {profile.education && !companyIndustryOptions.includes(profile.education) && (
            <option value={profile.education}>{profile.education}</option>
          )}
          {companyIndustryOptions.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
        <small style={helperStyle}>Choose the main AYUSH-sector area your organisation operates in.</small>
      </label>
      <label>
        Designation
        <input name="designation" autoComplete="off" defaultValue={profile.year_degree || ''} placeholder="e.g. HR / R&D / Research Coordinator" />
      </label>
      <label>
        AYUSH focus
        <select name="ayush_focus" autoComplete="off" defaultValue={profile.career_interests || ''} style={inputStyle}>
          <option value="">Select AYUSH focus</option>
          {profile.career_interests && !ayushFocusOptions.includes(profile.career_interests) && (
            <option value={profile.career_interests}>{profile.career_interests}</option>
          )}
          {ayushFocusOptions.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
        <small style={helperStyle}>Select the primary AYUSH system or research focus relevant to your opportunities.</small>
      </label>
      <label className="full">
        Hiring / collaboration focus
        <textarea name="collaboration_focus" autoComplete="off" defaultValue={profile.research_experience || ''} placeholder="Describe the AYUSH roles, research areas or student projects your organisation works on." />
      </label>
      <label className="full">
        Organisation notes
        <textarea name="organisation_notes" autoComplete="off" defaultValue={profile.achievements || ''} placeholder="Certifications, facilities, research programmes, or other relevant information." />
      </label>
      <button className="primary" disabled={saving}>{saving ? 'Saving…' : 'Save company profile'}</button>

      {role === 'company' && (
        <div className="full" style={{ marginTop: 8, padding: 18, border: '1px solid #d9e4ef', borderRadius: 12, background: '#f8fbff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: 16, fontWeight: 800, color: '#182433' }}>Company verification</div>
              <div style={{ marginTop: 5, color: '#70829a', fontSize: 13, lineHeight: 1.5 }}>
                Submit your completed AYUSH organisation profile for admin verification. Verified organisations can be trusted by students when they publish opportunities.
              </div>
            </div>
            <span style={{ padding: '7px 11px', borderRadius: 999, background: verification.status === 'Verified' ? '#e6f6ed' : verification.status === 'Pending Review' ? '#fff5df' : verification.status === 'Rejected' ? '#fdecec' : '#edf2f7', color: verification.status === 'Verified' ? '#197044' : verification.status === 'Pending Review' ? '#8a5a00' : verification.status === 'Rejected' ? '#a33333' : '#52657a', fontSize: 12, fontWeight: 800, whiteSpace: 'nowrap' }}>
              {verification.status}
            </span>
          </div>
          {verification.notes && <div style={{ marginTop: 12, fontSize: 12, color: '#64748b' }}>{verification.notes}</div>}
          {verification.status !== 'Verified' && verification.status !== 'Pending Review' && (
            <button type="button" className="primary" style={{ marginTop: 14, maxWidth: 280 }} onClick={submitVerification} disabled={verificationBusy || saving}>
              {verificationBusy ? 'Submitting…' : 'Submit for verification'}
            </button>
          )}
          {verification.status === 'Pending Review' && (
            <div style={{ marginTop: 12, fontSize: 12, color: '#70829a' }}>Your request is waiting for an administrator to review the organisation details.</div>
          )}
          {verification.status === 'Verified' && (
            <div style={{ marginTop: 12, fontSize: 12, color: '#197044', fontWeight: 700 }}>✓ Organisation verified by SkillNova administration.</div>
          )}
        </div>
      )}
    </form>
  );
}
