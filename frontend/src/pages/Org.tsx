import { FormEvent, useEffect, useMemo, useState } from 'react';
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
  const portalName = isCompany ? 'Company' : 'Academic';
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [apps, setApps] = useState<Application[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [matches, setMatches] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loadingMatches, setLoadingMatches] = useState(false);

  async function load() {
    setError('');
    try {
      const [opportunityData, applicationData, skillData] = await Promise.all([
        api<Opportunity[]>('/opportunities'),
        api<Application[]>('/applications'),
        api<Skill[]>('/skills'),
      ]);

      setOpps(opportunityData.filter((x) => x.owner_id === userId));
      setApps(applicationData);
      setSkills(skillData);
    } catch (e: any) {
      setError(e.message || 'Unable to load organization data.');
    }
  }

  useEffect(() => {
    load();
  }, [userId]);

  async function createOpportunity(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    setNotice('');

    // Capture the form before the async API call.
    // React's event currentTarget can become null after await.
    const formElement = e.currentTarget;

    try {
      const form = new FormData(formElement);
      const raw = String(form.get('requirements') || '');
      const requirements = raw
        .split(',')
        .map((part) => part.trim())
        .filter(Boolean)
        .map((part) => {
          const [name, level] = part.split(':').map((x) => x.trim());
          const skill = skills.find(
            (x) => x.name.toLowerCase() === name.toLowerCase(),
          );
          if (!skill) return null;
          const requiredLevel = Math.max(
            0,
            Math.min(100, Number(level) || 70),
          );
          return { skill_id: skill.id, required_level: requiredLevel };
        })
        .filter(Boolean);

      if (!requirements.length) {
        throw new Error('Add at least one valid skill requirement.');
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
      setNotice('Opportunity published successfully. Students can now see it.');
      await load();
    } catch (e: any) {
      setError(e.message || 'Could not publish opportunity.');
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

  const selectedOpportunity = useMemo(
    () => opps.find((x) => x.id === selected),
    [opps, selected],
  );

  const relevantApps = apps.filter((x) =>
    opps.some((o) => o.id === x.opportunity_id),
  );

  if (error && !opps.length && !apps.length) {
    return <div className="error">{error}</div>;
  }

  if (page === 'Company Profile' || page === 'Profile') {
    return (
      <Card>
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}
        <div className="section-title">{portalName} profile</div>
        <p className="muted form-intro">
          Keep your organization details current so students and candidates see
          accurate information.
        </p>
        <ProfileForm role={role} onSaved={(message) => setNotice(message)} />
      </Card>
    );
  }

  if (page === 'Post Opportunity' || page === 'Post Research/Project') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}
        <Card>
          <div className="section-title">
            {isCompany ? 'Create opportunity' : 'Create research / project opportunity'}
          </div>
          <p className="muted form-intro">
            Define the skills you actually need. SkillNova will use these requirements
            to rank students using verified evidence.
          </p>
          <form className="grid-form" onSubmit={createOpportunity}>
            <label>
              Title
              <input
                name="title"
                placeholder={isCompany ? 'AI/ML Intern' : 'AI-assisted Drug Discovery Project'}
                required
              />
            </label>
            <label>
              Type
              <select name="type" defaultValue={isCompany ? 'Internship' : 'Research Project'}>
                <option>Internship</option>
                <option>Job</option>
                <option>Research Project</option>
                <option>Mentorship</option>
              </select>
            </label>
            <label>
              Location
              <input name="location" placeholder="Remote / Chennai" defaultValue="Remote" />
            </label>
            <label className="full">
              Description
              <textarea name="description" placeholder="What will the student work on?" />
            </label>
            <label className="full">
              Required skills
              <span className="muted">Format: Python:80, Machine Learning:85</span>
              <input
                name="requirements"
                placeholder="Python:80, Machine Learning:85, Git:70"
                required
              />
            </label>
            <button className="primary">Publish opportunity</button>
          </form>
        </Card>
      </div>
    );
  }

  if (page === 'Opportunities') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}
        <div className="hero">
          <div>
            <div className="eyebrow">{isCompany ? 'EMPLOYER INTELLIGENCE' : 'ACADEMIC INTELLIGENCE'}</div>
            <h2>Your published opportunities</h2>
            <p>Every opportunity is connected to skill requirements and the live candidate graph.</p>
          </div>
          <button
            className="primary"
            onClick={() => setPage(isCompany ? 'Post Opportunity' : 'Post Research/Project')}
          >
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
                    <div className="muted">
                      {o.opportunity_type} · {o.location} · {o.requirements.length} required skills
                    </div>
                    <div className="chips" style={{ marginTop: 8 }}>
                      {o.requirements.map((r) => (
                        <span className="chip" key={r.skill_id}>
                          {r.skill} {r.required_level}%
                        </span>
                      ))}
                    </div>
                  </div>
                  <button className="secondary" onClick={() => viewMatches(o.id)}>
                    View matches
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <Empty
              title="No opportunities yet"
              body="Create and publish your first opportunity to start receiving skill-based matches."
            />
          )}
        </Card>
      </div>
    );
  }

  if (page === 'Matched Students') {
    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}
        <Card>
          <div className="section-title">Find matched students</div>
          <p className="muted form-intro">
            Candidates are ranked using verified skills, requirement coverage and readiness.
          </p>
          {opps.length ? (
            <div className="list">
              {opps.map((o) => (
                <div className="gap-row" key={o.id}>
                  <div className="grow">
                    <strong>{o.title}</strong>
                    <div className="muted">{o.requirements.length} required skills</div>
                  </div>
                  <button className="secondary" onClick={() => viewMatches(o.id)}>
                    Find candidates
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <Empty title="No opportunities" body="Publish an opportunity first." />
          )}
        </Card>

        {selected && (
          <Card>
            <div className="section-title">
              Candidate ranking{selectedOpportunity ? ` · ${selectedOpportunity.title}` : ''}
            </div>
            {loadingMatches ? (
              <p className="muted">Calculating live skill matches…</p>
            ) : matches.length ? (
              <div className="list">
                {matches.map((candidate) => (
                  <div className="candidate" key={candidate.student_id}>
                    <div className="grow">
                      <strong>{candidate.name}</strong>
                      <div className="muted">
                        {candidate.email} · {candidate.verified_skills} verified skills · {candidate.readiness}% readiness
                      </div>
                      <div className="chips" style={{ marginTop: 8 }}>
                        {candidate.matched_skills.length ? (
                          candidate.matched_skills.map((skill) => (
                            <span className="chip" key={skill}>✓ {skill}</span>
                          ))
                        ) : (
                          <span className="muted">No requirements fully met yet</span>
                        )}
                      </div>
                      {candidate.missing_skills.length > 0 && (
                        <div className="muted" style={{ marginTop: 8 }}>
                          Needs: {candidate.missing_skills.map((x) => `${x.skill} (${x.current}/${x.required})`).join(' · ')}
                        </div>
                      )}
                    </div>
                    <div className="candidate-score">{candidate.score}%</div>
                  </div>
                ))}
              </div>
            ) : (
              <Empty title="No student data yet" body="Students will appear here once they have profiles and skills." />
            )}
          </Card>
        )}
      </div>
    );
  }

  if (page === 'Applications') {
    return (
      <Card>
        {error && <div className="error">{error}</div>}
        {notice && <div className="success-banner">✓ {notice}</div>}
        <div className="section-title">Incoming applications</div>
        <p className="muted form-intro">
          Review applicants and move them through your hiring or research workflow.
        </p>
        {relevantApps.length ? (
          <div className="list">
            {relevantApps.map((application) => (
              <div className="candidate" key={application.id}>
                <div className="grow">
                  <strong>{application.student_name || 'Student'}</strong>
                  <div className="muted">
                    {application.student_email} · {application.opportunity_title} · Applied {new Date(application.created_at).toLocaleDateString()}
                  </div>
                </div>
                <select
                  value={application.status}
                  onChange={(e) => updateStatus(application.id, e.target.value)}
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
          <Empty title="No applications" body="Student applications will appear here after someone applies to your opportunities." />
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
          <div className="eyebrow">{isCompany ? 'EMPLOYER INTELLIGENCE' : 'ACADEMIC INTELLIGENCE'}</div>
          <h2>{isCompany ? 'Find skills, not just resumes.' : 'Find students aligned to research.'}</h2>
          <p>
            {isCompany
              ? 'Create opportunities and rank students using verified skills, readiness and the same skill graph used by students.'
              : 'Create research opportunities and discover students using verified skills, readiness and evidence.'}
          </p>
        </div>
        <button
          className="primary"
          onClick={() => setPage(isCompany ? 'Post Opportunity' : 'Post Research/Project')}
        >
          + Create opportunity
        </button>
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
                <div className="grow">
                  <strong>{o.title}</strong>
                  <div className="muted">{o.opportunity_type} · {o.location}</div>
                </div>
                <button className="secondary" onClick={() => viewMatches(o.id)}>
                  View matches
                </button>
              </div>
            ))}
          </div>
        ) : (
          <Empty title="Start the ecosystem" body="Publish your first opportunity to activate skill-based candidate matching." />
        )}
      </Card>
    </div>
  );
}

function ProfileForm({ role, onSaved }: { role: Role; onSaved: (message: string) => void }) {
  const [profile, setProfile] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api<any>('/profiles/me').then(setProfile).catch(() => setProfile(null));
  }, []);

  if (!profile) return <p className="muted">Loading profile…</p>;

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    try {
      const form = new FormData(e.currentTarget);
      await api('/profiles/me', {
        method: 'PUT',
        body: JSON.stringify({
          name: form.get('name'),
          education: form.get('education'),
          year_degree: form.get('year_degree'),
          career_interests: form.get('interests'),
          research_experience: form.get('research'),
          achievements: form.get('achievements'),
        }),
      });
      onSaved(`${role === 'company' ? 'Company' : 'Academic'} profile saved.`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="grid-form" onSubmit={save}>
      <label>
        {role === 'company' ? 'Organisation name' : 'Name'}
        <input name="name" defaultValue={profile.name} required />
      </label>
      <label>
        {role === 'company' ? 'Industry / field' : 'Department / field'}
        <input name="education" defaultValue={profile.education} />
      </label>
      <label>
        {role === 'company' ? 'Designation' : 'Designation'}
        <input name="year_degree" defaultValue={profile.year_degree} />
      </label>
      <label>Interests<input name="interests" defaultValue={profile.career_interests} /></label>
      <label className="full">{role === 'company' ? 'Hiring focus' : 'Research focus'}<textarea name="research" defaultValue={profile.research_experience} /></label>
      <label className="full">Achievements / notes<textarea name="achievements" defaultValue={profile.achievements} /></label>
      <button className="primary" disabled={saving}>{saving ? 'Saving…' : 'Save profile'}</button>
    </form>
  );
}
