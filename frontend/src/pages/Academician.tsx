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
  core_gaps: {
    skill_id: number;
    skill: string;
    current: number;
    required: number;
    gap: number;
  }[];
  project_count: number;
  certificate_count: number;
  course_count: number;
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

type StudentPortfolio = {
  student: {
    id: number; email: string; name: string; education: string; year_degree: string;
    target_role: string | null; career_interests: string; research_experience: string;
    achievements: string; readiness: number;
  };
  skills: {
    id: number; skill_id: number; skill: string; category: string; proficiency: number;
    verified: boolean; academic_verified: boolean;
    evidence: { id: number; kind: string; title: string; url: string }[];
  }[];
  projects: { id: number; title: string; description: string; url: string }[];
  certificates: { id: number; title: string; issuer: string; url: string }[];
  courses: { id: number; title: string; provider: string; url: string }[];
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
  const [studentPortfolio, setStudentPortfolio] = useState<StudentPortfolio | null>(null);
  const [loadingPortfolio, setLoadingPortfolio] = useState(false);
  const [verifyingSkill, setVerifyingSkill] = useState<number | null>(null);
  const [reviewedSkills, setReviewedSkills] = useState<Record<number, boolean>>({});
  const [selectedOpportunity, setSelectedOpportunity] = useState<number | null>(null);
  const [matches, setMatches] = useState<Candidate[]>([]);

  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load() {
    setError('');
    try {
      const [studentData, opportunityData, applicationData, profileData, skillData] =
        await Promise.all([
          api<StudentRecord[]>('/academician/students'),
          api<Opportunity[]>('/opportunities'),
          api<Application[]>('/applications'),
          api<Profile>('/profile'),
          api<{ id: number; name: string; category: string }[]>('/skills'),
        ]);

      setStudents(studentData);
      setOpportunities(opportunityData);
      setApplications(applicationData);
      setProfile(profileData);
      setSkills(skillData);
    } catch (e: any) {
      setError(e.message || 'Unable to load academician data.');
    } finally {
      setLoading(false);
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
        ...(student.verified_skills || []).map((x) => x.skill),
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

          return {
            skill_id: skill.id,
            required_level: Math.max(0, Math.min(100, Number(level) || 70)),
          };
        })
        .filter(Boolean);

      if (!requirements.length) {
        throw new Error('Add at least one valid skill requirement from the SkillNova taxonomy.');
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
      setNotice('Research/project opportunity published successfully.');
      await load();
      setPage('Opportunities');
    } catch (e: any) {
      setError(e.message || 'Could not publish opportunity.');
    }
  }

  async function inspectStudent(student: StudentRecord) {
    setSelectedStudent(student);
    setStudentPortfolio(null);
    setLoadingPortfolio(true);
    setError('');
    try {
      const data = await api<StudentPortfolio>(
        `/academician/students/${student.student_id}/portfolio`,
      );
      setStudentPortfolio(data);
    } catch (e: any) {
      setError(e.message || 'Could not load student portfolio.');
    } finally {
      setLoadingPortfolio(false);
    }
  }

  async function reviewEvidence(skillId: number, evidence: { url: string }[]) {
    const validLinks = evidence.map((x) => x.url).filter(Boolean);
    if (!validLinks.length) {
      setError('This skill has no evidence link to review yet.');
      return;
    }

    validLinks.forEach((url) => window.open(url, '_blank', 'noopener,noreferrer'));
    setReviewedSkills((current) => ({ ...current, [skillId]: true }));
    setNotice('Evidence opened for review. Verify the skill after checking it.');
  }

  async function verifySkill(studentId: number, skillId: number) {
    const skill = studentPortfolio?.skills.find((x) => x.skill_id === skillId);
    if (!skill?.evidence?.some((x) => x.url)) {
      setError('Verification requires submitted evidence with a link.');
      return;
    }
    if (!reviewedSkills[skillId]) {
      setError('Review the submitted evidence first, then verify the skill.');
      return;
    }

    setVerifyingSkill(skillId);
    setError('');
    setNotice('');
    try {
      await api(`/academician/students/${studentId}/skills/${skillId}/verify`, {
        method: 'POST',
      });
      const portfolio = await api<StudentPortfolio>(
        `/academician/students/${studentId}/portfolio`,
      );
      setStudentPortfolio(portfolio);
      const updated = await api<StudentRecord[]>('/academician/students');
      setStudents(updated);
      const refreshed = updated.find((x) => x.student_id === studentId);
      if (refreshed) setSelectedStudent(refreshed);
      setNotice('Skill verified. Student readiness and matching have been recalculated.');
    } catch (e: any) {
      setError(e.message || 'Could not verify skill.');
    } finally {
      setVerifyingSkill(null);
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
      setMatches(Array.isArray(data) ? data : []);
      // We are already on Matched Students when this button is clicked.
      // Only navigate when the action was triggered from another page.
      if (page !== 'Matched Students') {
        setPage('Matched Students');
      }
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

          <form className="grid-form" onSubmit={saveProfile}>
            <label>
              Name
              <input name="name" defaultValue={profile?.name || ''} required />
            </label>

            <label>
              Department / field
              <input
                name="education"
                defaultValue={profile?.education || ''}
                placeholder="Computer Science / AI"
              />
            </label>

            <label>
              Designation
              <input
                name="year_degree"
                defaultValue={profile?.year_degree || ''}
                placeholder="Professor / Associate Professor"
              />
            </label>

            <label>
              Research interests
              <input
                name="career_interests"
                defaultValue={profile?.career_interests || ''}
                placeholder="AI, ML, computer vision..."
              />
            </label>

            <label className="full">
              Research experience
              <textarea
                name="research_experience"
                defaultValue={profile?.research_experience || ''}
                placeholder="Describe your research areas and experience."
              />
            </label>

            <label className="full">
              Achievements / notes
              <textarea
                name="achievements"
                defaultValue={profile?.achievements || ''}
                placeholder="Publications, awards, labs, projects..."
              />
            </label>

            <button className="primary" disabled={saving}>
              {saving ? 'Saving…' : 'Save profile'}
            </button>
          </form>
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
            value={students.filter((s) => s.core_gaps.length > 0).length}
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
                    onClick={() => inspectStudent(student)}
                  >
                    <div className="grow">
                      <strong>{student.name}</strong>
                      <div className="muted">
                        {student.email} · {student.target_role || 'Target role not set'}
                      </div>
                      <div className="chips" style={{ marginTop: 8 }}>
                        {(student.verified_skills || []).slice(0, 4).map((skill) => (
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

                {loadingPortfolio ? (
                  <p className="muted">Loading student portfolio…</p>
                ) : (
                  <>
                    <div className="stats">
                      <Stat
                        label="Readiness"
                        value={`${studentPortfolio?.student.readiness ?? selectedStudent.readiness}%`}
                      />
                      <Stat
                        label="Verified skills"
                        value={studentPortfolio?.skills.filter((x) => x.verified).length ?? selectedStudent.verified_skill_count}
                      />
                      <Stat
                        label="Projects"
                        value={studentPortfolio?.projects.length ?? selectedStudent.project_count}
                      />
                    </div>

                    <div className="section-title" style={{ marginTop: 20 }}>Profile</div>
                    <div className="gap-mini"><span>Education</span><strong>{selectedStudent.education || 'Not provided'}</strong></div>
                    <div className="gap-mini"><span>Year / degree</span><strong>{selectedStudent.year_degree || 'Not provided'}</strong></div>
                    <div className="gap-mini"><span>Target role</span><strong>{selectedStudent.target_role || 'Not selected'}</strong></div>

                    <div className="section-title" style={{ marginTop: 20 }}>Skill verification</div>
                    {studentPortfolio?.skills.length ? (
                      <div className="list">
                        {studentPortfolio.skills.map((skill) => (
                          <div className="gap-row" key={skill.id}>
                            <div className="grow">
                              <strong>{skill.skill}</strong>
                              <div className="muted">{skill.category} · {skill.proficiency}%</div>
                              {skill.evidence.length > 0 ? (
                                <div className="stack" style={{ marginTop: 8, gap: 6 }}>
                                  {skill.evidence.map((evidence) => (
                                    <div key={evidence.id} className="gap-mini">
                                      <div>
                                        <strong>{evidence.title}</strong>
                                        <div className="muted">{evidence.kind}</div>
                                      </div>
                                      {evidence.url ? (
                                        <a
                                          className="text-link"
                                          href={evidence.url}
                                          target="_blank"
                                          rel="noreferrer"
                                          onClick={() => setReviewedSkills((current) => ({ ...current, [skill.skill_id]: true }))}
                                        >
                                          Open ↗
                                        </a>
                                      ) : (
                                        <span className="muted">No link</span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div className="muted" style={{ marginTop: 6 }}>No evidence submitted yet.</div>
                              )}
                            </div>
                            {skill.academic_verified ? (
                              <span className="chip">✓ Academically verified</span>
                            ) : skill.evidence.some((x) => x.url) ? (
                              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                {!reviewedSkills[skill.skill_id] && (
                                  <button
                                    type="button"
                                    className="secondary"
                                    onClick={() => reviewEvidence(skill.skill_id, skill.evidence)}
                                  >
                                    Review evidence ↗
                                  </button>
                                )}
                                <button
                                  type="button"
                                  className="secondary"
                                  disabled={verifyingSkill === skill.skill_id || !reviewedSkills[skill.skill_id]}
                                  onClick={() => verifySkill(selectedStudent.student_id, skill.skill_id)}
                                >
                                  {verifyingSkill === skill.skill_id ? 'Verifying…' : reviewedSkills[skill.skill_id] ? 'Verify skill' : 'Review first'}
                                </button>
                              </div>
                            ) : (
                              <span className="muted">Awaiting evidence</span>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="muted">No skills added by this student yet.</p>
                    )}

                    <div className="section-title" style={{ marginTop: 20 }}>Portfolio</div>
                    {studentPortfolio && (
                      <div className="list">
                        {studentPortfolio.projects.map((project) => (
                          <div className="gap-row" key={`project-${project.id}`}>
                            <div><strong>{project.title}</strong><div className="muted">Project · {project.description || 'No description'}</div></div>
                            {project.url && <a className="secondary" href={project.url} target="_blank" rel="noreferrer">Open</a>}
                          </div>
                        ))}
                        {studentPortfolio.certificates.map((certificate) => (
                          <div className="gap-row" key={`certificate-${certificate.id}`}>
                            <div><strong>{certificate.title}</strong><div className="muted">Certificate · {certificate.issuer || 'Issuer not provided'}</div></div>
                            {certificate.url && <a className="secondary" href={certificate.url} target="_blank" rel="noreferrer">Open</a>}
                          </div>
                        ))}
                        {studentPortfolio.courses.map((course) => (
                          <div className="gap-row" key={`course-${course.id}`}>
                            <div><strong>{course.title}</strong><div className="muted">Course · {course.provider || 'Provider not provided'}</div></div>
                            {course.url && <a className="secondary" href={course.url} target="_blank" rel="noreferrer">Open</a>}
                          </div>
                        ))}
                        {!studentPortfolio.projects.length && !studentPortfolio.certificates.length && !studentPortfolio.courses.length && (
                          <p className="muted">No portfolio items added yet.</p>
                        )}
                      </div>
                    )}

                    <div className="section-title" style={{ marginTop: 20 }}>Top core skill gaps</div>
                    {selectedStudent.core_gaps.length ? (
                      <div className="list">
                        {selectedStudent.core_gaps.slice(0, 5).map((gap) => (
                          <div className="gap-row" key={gap.skill}>
                            <div><strong>{gap.skill}</strong><div className="muted">Current {gap.current}% · Required {gap.required}%</div></div>
                            <span className="status">{gap.gap}% gap</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="muted">No active core skill gaps.</p>
                    )}

                    {selectedStudent.research_experience && (
                      <>
                        <div className="section-title" style={{ marginTop: 20 }}>Research experience</div>
                        <p className="muted">{selectedStudent.research_experience}</p>
                      </>
                    )}
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

          <form className="grid-form" onSubmit={createOpportunity}>
            <label>
              Opportunity title
              <input
                name="title"
                placeholder="AI-assisted Drug Discovery Project"
                required
              />
            </label>

            <label>
              Type
              <select name="type" defaultValue="Research Project">
                <option>Research Project</option>
                <option>Mentorship</option>
                <option>Internship</option>
                <option>Project</option>
              </select>
            </label>

            <label>
              Location
              <input name="location" defaultValue="Remote" />
            </label>

            <label className="full">
              Description
              <textarea
                name="description"
                placeholder="Describe the research problem, expected work and outcomes."
              />
            </label>

            <label className="full">
              Required skills
              <span className="muted">
                Format: Python:80, Machine Learning:85
              </span>
              <input
                name="requirements"
                placeholder="Python:80, Machine Learning:85, Git:70"
                required
              />
            </label>

            <button className="primary">Publish research opportunity</button>
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
                          {requirement.skill} {requirement.required_level}%
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

      <div className="stats">
        <Stat label="Students" value={students.length} />
        <Stat label="Average readiness" value={`${averageReadiness}%`} />
        <Stat label="Verified skills" value={totalVerifiedSkills} />
        <Stat label="Opportunities" value={myOpportunities.length} />
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
