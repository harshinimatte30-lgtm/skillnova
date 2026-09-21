import { FormEvent, useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api';
import { Card, Stat, Progress, Empty } from '../components/UI';
import { Profile, Skill, RoleOption } from '../types';
import './assessment-ui.css';

type EvidenceType = 'project' | 'certificate' | 'course';

type StudentSkill = {
  id: number;
  skill_id: number;
  skill: string;
  category: string;
  proficiency: number;
  verified: boolean;
  evidence_count: number;
};

type GapItem = {
  skill_id: number;
  skill: string;
  current: number;
  required: number;
  gap: number;
  category: string;
  alternative_group: string | null;
  verified: boolean;
};

type GapResponse = {
  target_role: {
    id: number;
    name: string;
  } | null;
  readiness: number;
  active_gaps: number;
  core: GapItem[];
  recommended: GapItem[];
  alternatives: GapItem[];
  advanced: GapItem[];
};

type EvidenceItem = {
  id: number;
  kind: string;
  title: string;
  url?: string | null;
};

type PortfolioData = {
  profile: {
    name: string;
    education: string;
    year_degree: string;
    target_role: string | null;
  };
  skills: any[];
  projects: any[];
  certificates: any[];
  courses: any[];
};

type StudentDocument = {
  id: number;
  student_id: number;
  title: string;
  document_type: string;
  description: string;
  issuer: string;
  issued_on: string;
  url: string;
  visibility: 'Private' | 'Academician' | 'Industry' | string;
  verification_status: 'Pending' | 'Verified' | 'Rejected' | string;
  rejection_reason: string;
  linked_internship_id?: number | null;
  linked_collaboration_id?: number | null;
  verified_at?: string | null;
};

type Opportunity = {
  id: number;
  title: string;
  description: string;
  opportunity_type: string;
  location: string;
  created_at?: string;
  match_percentage?: number;
  eligible?: boolean;
  eligibility_reasons?: string[];
  matched_skills?: string[];
  missing_skills?: { skill: string; current: number; required: number; gap: number }[];
  academic_eligibility?: {
    education_ok: boolean;
    year_ok: boolean;
    cgpa_ok: boolean;
    required_education: string;
    minimum_year?: number | null;
    minimum_cgpa?: number | null;
    student_education: string;
    student_year: string;
    student_cgpa?: number | null;
    notes?: string;
  };
  requirements: {
    skill_id: number;
    skill: string;
    required_level: number;
    student_level?: number;
    gap?: number;
    meets_requirement?: boolean;
    verified?: boolean;
  }[];
};

type Application = {
  id: number;
  opportunity_id: number;
  title: string;
  company: string;
  status: string;
  created_at: string;
};

type Internship = {
  id: number;
  opportunity_id: number;
  opportunity_title: string;
  student_id: number;
  company_name: string;
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

type LearningResource = {
  title: string;
  platform: string;
  level: string;
  duration: string;
  type: string;
  url: string;
};

type LearningRecommendation = {
  skill_id: number;
  skill: string;
  gap: number;
  current: number;
  required: number;
  priority: string;
  resource: LearningResource;
};

type IndustryLearningProgram = {
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
  skills: {
    skill_id: number;
    skill: string;
    category?: string;
  }[];
  enrollment?: {
    id: number;
    learning_program_id: number;
    student_id: number;
    status: 'Enrolled' | 'In Progress' | 'Completed' | 'Cancelled' | string;
    enrolled_at?: string | null;
    completed_at?: string | null;
    certificate_url?: string;
  } | null;
};

type CareerRoadmapItem = {
  skill_id: number;
  skill: string;
  current: number;
  required: number;
  gap: number;
  category: string;
  alternative_group: string | null;
  verified: boolean;
  status: string;
  action: string;
  reason: string;
};

type CareerPath = {
  role_id: number;
  role_name: string;
  description: string;
  readiness: number;
  core_total: number;
  core_matched: number;
  core_partial: number;
  core_missing: number;
  matched_skills: string[];
  next_skill: string | null;
  next_skill_gap: number;
  roadmap: CareerRoadmapItem[];
};

type CareerPathsResponse = {
  target_role_id: number | null;
  target_role: string | null;
  student_skills: {
    skill_id: number;
    skill: string;
    category: string;
    current: number;
    verified: boolean;
  }[];
  paths: CareerPath[];
};

type AssessmentQuestion = {
  id: number;
  skill_id?: number | null;
  category: string;
  question: string;
  options: { A: string; B: string; C: string; D: string };
  order: number;
};

type AssessmentStartResponse = {
  status: 'started' | 'in_progress' | 'already_submitted';
  attempt_id: number;
  assessment_id: number;
  role_id: number;
  test_type?: string;
  difficulty?: string;
  year?: string;
  title?: string;
  description?: string;
  total_questions?: number;
  questions?: AssessmentQuestion[];
  message?: string;
};

type AssessmentResult = {
  status: 'SUBMITTED';
  attempt_id: number;
  assessment_id: number;
  role_id?: number;
  title: string;
  description: string;
  total_questions: number;
  overall_status: 'Strong' | 'Developing' | 'Needs Improvement' | 'Not Assessed';
  skill_results: { skill_id: number; skill: string; status: 'Strong' | 'Developing' | 'Needs Improvement' | 'Not Assessed' }[];
  questions: { question_id: number; skill_id?: number | null; category: string; question: string; selected_option: string; correct_option: string; is_correct: boolean; explanation?: string }[];
};

function SkillComparisonGraph({ items }: { items: GapItem[] }) {
  const data = items.slice(0, 8);

  if (!data.length) {
    return (
      <div className="muted" style={{ padding: '24px 0' }}>
        No core skill data available yet.
      </div>
    );
  }

  const size = 420;
  const center = size / 2;
  const radius = 145;
  const levels = [25, 50, 75, 100];
  const count = data.length;

  const point = (value: number, index: number) => {
    const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count;
    const r = (Math.max(0, Math.min(100, value)) / 100) * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  const polygonPoints = (valueKey: 'current' | 'required') =>
    data
      .map((item, index) => {
        const p = point(item[valueKey], index);
        return `${p.x},${p.y}`;
      })
      .join(' ');

  const labelPoint = (index: number) => {
    const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count;
    const r = radius + 34;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
      angle,
    };
  };

  return (
    <div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(320px, 1.1fr) minmax(240px, 0.9fr)',
          gap: 24,
          alignItems: 'center',
        }}
      >
        <div style={{ overflowX: 'auto' }}>
          <svg
            viewBox={`0 0 ${size} ${size}`}
            width="100%"
            role="img"
            aria-label="Radar chart comparing current and required levels for core skills"
            style={{ minWidth: 320, maxWidth: 500, display: 'block', margin: '0 auto' }}
          >
            {levels.map((level) => (
              <polygon
                key={level}
                points={data
                  .map((_, index) => {
                    const p = point(level, index);
                    return `${p.x},${p.y}`;
                  })
                  .join(' ')}
                fill="none"
                stroke="currentColor"
                strokeWidth="1"
                opacity="0.12"
              />
            ))}

            {data.map((_, index) => {
              const p = point(100, index);
              return (
                <line
                  key={`axis-${index}`}
                  x1={center}
                  y1={center}
                  x2={p.x}
                  y2={p.y}
                  stroke="currentColor"
                  strokeWidth="1"
                  opacity="0.10"
                />
              );
            })}

            <polygon
              points={polygonPoints('required')}
              fill="currentColor"
              fillOpacity="0.10"
              stroke="currentColor"
              strokeOpacity="0.35"
              strokeWidth="2"
            />

            <polygon
              points={polygonPoints('current')}
              fill="currentColor"
              fillOpacity="0.24"
              stroke="currentColor"
              strokeWidth="2.5"
            />

            {data.map((item, index) => {
              const current = point(item.current, index);
              const required = point(item.required, index);
              const label = labelPoint(index);
              const anchor =
                Math.abs(Math.cos(label.angle)) < 0.25
                  ? 'middle'
                  : Math.cos(label.angle) > 0
                    ? 'start'
                    : 'end';

              return (
                <g key={item.skill_id}>
                  <title>
                    {item.skill}: Current {item.current}%, Required {item.required}%, Gap {item.gap}%
                  </title>
                  <circle cx={current.x} cy={current.y} r="4.5" fill="currentColor" />
                  <circle cx={required.x} cy={required.y} r="3" fill="currentColor" opacity="0.45" />
                  <text
                    x={label.x}
                    y={label.y}
                    textAnchor={anchor}
                    dominantBaseline="middle"
                    fontSize="10.5"
                    fontWeight="700"
                    fill="currentColor"
                  >
                    {item.skill.length > 20 ? `${item.skill.slice(0, 19)}…` : item.skill}
                  </text>
                </g>
              );
            })}

            <text
              x={center}
              y={center - 5}
              textAnchor="middle"
              fontSize="22"
              fontWeight="800"
              fill="currentColor"
            >
              {Math.round(data.reduce((sum, item) => sum + item.current, 0) / data.length)}%
            </text>
            <text
              x={center}
              y={center + 15}
              textAnchor="middle"
              fontSize="10"
              fill="currentColor"
              opacity="0.62"
            >
              current average
            </text>
          </svg>
        </div>

        <div style={{ display: 'grid', gap: 10 }}>
          <div
            style={{
              display: 'flex',
              gap: 8,
              alignItems: 'center',
              fontSize: 12,
              fontWeight: 700,
            }}
          >
            <span style={{ width: 11, height: 11, borderRadius: 3, background: 'currentColor', opacity: 0.75 }} />
            Current level
          </div>
          <div
            style={{
              display: 'flex',
              gap: 8,
              alignItems: 'center',
              fontSize: 12,
              fontWeight: 700,
            }}
          >
            <span style={{ width: 11, height: 11, borderRadius: 3, background: 'currentColor', opacity: 0.28 }} />
            Required level
          </div>

          <div style={{ marginTop: 8, display: 'grid', gap: 12 }}>
            {data.map((item) => (
              <div key={`bar-${item.skill_id}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, fontSize: 12 }}>
                  <strong>{item.skill}</strong>
                  <span className="muted">
                    {item.current}% / {item.required}%
                  </span>
                </div>
                <div
                  style={{
                    position: 'relative',
                    height: 8,
                    marginTop: 6,
                    borderRadius: 999,
                    background: 'rgba(15,23,42,0.08)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      width: `${Math.max(0, Math.min(100, item.required))}%`,
                      borderRadius: 999,
                      background: 'currentColor',
                      opacity: 0.25,
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      width: `${Math.max(0, Math.min(100, item.current))}%`,
                      borderRadius: 999,
                      background: 'currentColor',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="muted" style={{ fontSize: 12, lineHeight: 1.55, marginTop: 4 }}>
            The radar shows the shape of your current skill profile against the target role. The bars beside it make each individual gap easy to compare.
          </div>
        </div>
      </div>
    </div>
  );
}

function ReadinessGraph({ value }: { value: number }) {
  const readiness = Math.max(0, Math.min(100, value || 0));
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const dash = (readiness / 100) * circumference;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap' }}>
      <div style={{ width: 170, height: 170, flex: '0 0 170px' }}>
        <svg viewBox="0 0 170 170" width="170" height="170" role="img" aria-label={`Core readiness ${readiness}%`}>
          <circle
            cx="85"
            cy="85"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="14"
            opacity="0.10"
          />
          <circle
            cx="85"
            cy="85"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circumference - dash}`}
            transform="rotate(-90 85 85)"
          />
          <text x="85" y="82" textAnchor="middle" fontSize="28" fontWeight="700" fill="currentColor">
            {readiness}%
          </text>
          <text x="85" y="103" textAnchor="middle" fontSize="11" fill="currentColor" opacity="0.65">
            ready
          </text>
        </svg>
      </div>

      <div>
        <strong style={{ fontSize: 18 }}>Core readiness</strong>
        <p className="muted" style={{ margin: '6px 0 0' }}>
          Calculated from the current core-skill requirements for your target role.
        </p>
      </div>
    </div>
  );
}

export default function Student({
  page,
  setPage,
}: {
  page: string;
  setPage: (p: string) => void;
}) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [studentSkills, setStudentSkills] = useState<StudentSkill[]>([]);
  const [roles, setRoles] = useState<RoleOption[]>([]);
  const [careerPaths, setCareerPaths] = useState<CareerPath[]>([]);
  const [selectedCareerRoleId, setSelectedCareerRoleId] = useState<number | null>(null);
  const [gap, setGap] = useState<GapResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [apps, setApps] = useState<Application[]>([]);
  const [learningRecommendations, setLearningRecommendations] =
    useState<LearningRecommendation[]>([]);
  const [academicCgpa, setAcademicCgpa] = useState<number | null>(null);

  const [industryPrograms, setIndustryPrograms] =
    useState<IndustryLearningProgram[]>([]);
  const [internships, setInternships] = useState<Internship[]>([]);
  const [documents, setDocuments] = useState<StudentDocument[]>([]);
  const [documentBusy, setDocumentBusy] = useState<number | null>(null);
  const [documentType, setDocumentType] = useState('Certificate');
  const [documentVisibility, setDocumentVisibility] = useState<'Private' | 'Academician' | 'Industry'>('Academician');
  const [internshipBusy, setInternshipBusy] = useState<number | null>(null);
  const [learningProgramBusy, setLearningProgramBusy] =
    useState<number | null>(null);

  const [assessment, setAssessment] =
  useState<AssessmentStartResponse | null>(null);

const [assessmentResult, setAssessmentResult] =
  useState<AssessmentResult | null>(null);

const [assessmentLoading, setAssessmentLoading] =
  useState(false);

const [assessmentSubmitting, setAssessmentSubmitting] =
  useState(false);

const [assessmentAnswers, setAssessmentAnswers] =
  useState<Record<string, string>>({});

const [assessmentError, setAssessmentError] =
  useState('');

  const [assessmentType, setAssessmentType] = useState<'Role-specific' | 'Aptitude' | 'Soft Skills'>('Role-specific');
  const [assessmentDifficulty, setAssessmentDifficulty] = useState<'Easy' | 'Medium' | 'Hard'>('Medium');
  const [assessmentYear, setAssessmentYear] = useState('2nd Year');
  const [assessmentQuestionIndex, setAssessmentQuestionIndex] = useState(0);

  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const [saving, setSaving] = useState(false);
  const [savingSkill, setSavingSkill] = useState(false);

  const [selectedSkill, setSelectedSkill] = useState('');

  const [evidenceFor, setEvidenceFor] = useState<number | null>(null);
  const [evidenceType, setEvidenceType] =
    useState<EvidenceType>('project');

  const [portfolioType, setPortfolioType] =
    useState<EvidenceType>('project');

  /*
   * ============================================================
   * LOAD ALL STUDENT DATA
   * ============================================================
   *
   * These endpoints match the current backend.
   */

  async function load() {
    setError('');

    try {
      const [
        p,
        s,
        r,
        studentSkillData,
        gapData,
        portfolioData,
        opportunityData,
        applicationData,
        learningData,
        industryProgramData,
        internshipData,
        documentData,
        careerPathData,
        academicRecordData,
      ] = await Promise.all([
        api<Profile>('/profile'),
        api<Skill[]>('/skills'),
        api<RoleOption[]>('/roles'),
        api<StudentSkill[]>('/student/skills'),
        api<GapResponse>('/student/skill-gap'),
        api<PortfolioData>('/portfolio'),
        api<Opportunity[]>('/student/opportunities/matches'),
        api<Application[]>('/student/applications'),
        api<LearningRecommendation[]>('/student/learning'),
        api<IndustryLearningProgram[]>('/learning-programs'),
        api<Internship[]>('/student/internships'),
        api<StudentDocument[]>('/student/documents'),
        api<CareerPathsResponse>('/student/career-paths'),
        api<{ cgpa: number | null }>('/student/academic-record'),
      ]);

      setProfile(p);
      if (p.year_degree) setAssessmentYear(p.year_degree);
      setSkills(s);
      setRoles(r);
      setStudentSkills(studentSkillData);
      setGap(gapData);
      setPortfolio(portfolioData);
      setOpps(opportunityData);
      setApps(applicationData);
      setLearningRecommendations(Array.isArray(learningData) ? learningData : []);
      setIndustryPrograms(Array.isArray(industryProgramData) ? industryProgramData : []);
      setInternships(Array.isArray(internshipData) ? internshipData : []);
      setDocuments(Array.isArray(documentData) ? documentData : []);
      const loadedCareerPaths = Array.isArray(careerPathData?.paths) ? careerPathData.paths : [];
      setCareerPaths(loadedCareerPaths);
      setSelectedCareerRoleId(
        careerPathData?.target_role_id ?? loadedCareerPaths[0]?.role_id ?? null
      );
      setAcademicCgpa(academicRecordData?.cgpa ?? null);
    } catch (e: any) {
      setError(
        e.message ||
          'Unable to load your SkillNova data.'
      );
    }
  }
    /*
   * ============================================================
   * START STUDENT ASSESSMENT
   * ============================================================
   */

  async function startAssessment() {
    if (!profile?.target_role_id) { setAssessmentError('Please select a target role in My Profile first.'); return; }
    setAssessmentLoading(true); setAssessmentError(''); setAssessmentResult(null); setAssessmentQuestionIndex(0);
    try {
      const params = new URLSearchParams({
        test_type: assessmentType,
        difficulty: assessmentDifficulty,
        year: profile.year_degree || ''
      });
      const data = await api<AssessmentStartResponse>(`/student/assessment/${profile.target_role_id}/start?${params.toString()}`, { method: 'POST' });
      setAssessment(data); setAssessmentAnswers({});
    } catch (e: any) { setAssessmentError(e.message || 'Unable to start the assessment.'); }
    finally { setAssessmentLoading(false); }
  }

  async function submitAssessment() {
    if (!assessment?.attempt_id || !assessment.questions?.length) return;
    if (assessment.questions.some((q) => !assessmentAnswers[String(q.id)])) { setAssessmentError('Please answer every question before submitting.'); return; }
    setAssessmentSubmitting(true); setAssessmentError('');
    try {
      const result = await api<AssessmentResult>(`/student/assessment/attempt/${assessment.attempt_id}/submit`, { method: 'POST', body: JSON.stringify({ answers: assessmentAnswers }) });
      setAssessmentResult(result); setAssessment(null);
    } catch (e: any) { setAssessmentError(e.message || 'Unable to submit the assessment.'); }
    finally { setAssessmentSubmitting(false); }
  }

  function resetAssessmentView() { setAssessment(null); setAssessmentResult(null); setAssessmentAnswers({}); setAssessmentQuestionIndex(0); setAssessmentError(''); }

  useEffect(() => {
    load();
  }, []);

  /*
   * ============================================================
   * HELPERS
   * ============================================================
   */

  const selectedSkillName = useMemo(
    () =>
      skills.find(
        (s) => String(s.id) === selectedSkill
      )?.name || '',
    [skills, selectedSkill]
  );

  const allEvidence = useMemo(() => {
    if (!portfolio) return [];

    return [
      ...portfolio.projects.map((x) => ({
        type: 'Project',
        title: x.title,
        meta: x.description,
        url: x.url,
      })),

      ...portfolio.certificates.map((x) => ({
        type: 'Certificate',
        title: x.title,
        meta: x.issuer,
        url: x.url,
      })),

      ...portfolio.courses.map((x) => ({
        type: 'Course',
        title: x.title,
        meta: x.provider,
        url: x.url,
      })),
    ];
  }, [portfolio]);

  const selectedCareerPath = useMemo(
    () =>
      careerPaths.find(
        (path) => path.role_id === selectedCareerRoleId
      ) || careerPaths[0] || null,
    [careerPaths, selectedCareerRoleId]
  );

  const selectedCareerRoadmap = useMemo(
    () => selectedCareerPath?.roadmap || [],
    [selectedCareerPath]
  );

  const activeCoreGaps =
    gap?.core?.filter((x) => x.gap > 0) || [];

  /*
   * Learning recommendations come from the backend's curated AYUSH learning
   * catalogue. The backend ranks them from the student's CORE skill gaps, so
   * the page never sends the student to a generic Google search.
   */

  const learning = learningRecommendations;

  if (error && !profile) {
    return <div className="error">{error}</div>;
  }

  if (!profile) {
    return (
      <Card>
        Loading your SkillNova profile…
      </Card>
    );
  }

  /*
   * ============================================================
   * NOTIFICATIONS
   * ============================================================
   */

  function flash(message: string) {
    setNotice(message);

    window.setTimeout(() => {
      setNotice('');
    }, 2600);
  }

  /*
   * ============================================================
   * PROFILE
   * ============================================================
   */

  async function saveProfile(
    e: FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();

    setSaving(true);
    setError('');

    try {
      const f = new FormData(e.currentTarget);

      await api('/profile', {
        method: 'PUT',

        body: JSON.stringify({
          name: f.get('name'),
          education: f.get('education'),
          year_degree: f.get('year_degree'),

          target_role_id:
            Number(f.get('target_role_id')) || null,

          career_interests:
            f.get('career_interests'),
            research_experience:
            profile?.research_experience || '',
            achievements:
            profile?.achievements || '',
        }),
      });

      const rawCgpa = f.get('cgpa');
      await api('/student/academic-record', {
        method: 'PUT',
        body: JSON.stringify({ cgpa: rawCgpa === '' ? null : Number(rawCgpa) }),
      });

      await load();

      flash(
        'Profile updated. Skill intelligence recalculated.'
      );
    } catch (e: any) {
      setError(
        e.message ||
          'Could not save profile.'
      );
    } finally {
      setSaving(false);
    }
  }

  /*
   * ============================================================
   * ADD SKILL
   * ============================================================
   *
   * IMPORTANT:
   * There is NO proficiency slider.
   *
   * Students simply select a skill.
   * Evidence verifies it.
   */

  async function addSkill(
    e: FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();

    if (!selectedSkill) return;

    setSavingSkill(true);
    setError('');

    try {
      await api('/student/skills', {
        method: 'POST',

        body: JSON.stringify({
          skill_id: Number(selectedSkill),
        }),
      });

      await load();

      flash(
        `${selectedSkillName} added. Add evidence to verify it.`
      );

      setSelectedSkill('');
    } catch (e: any) {
      setError(
        e.message ||
          'Could not add skill.'
      );
    } finally {
      setSavingSkill(false);
    }
  }

  /*
   * ============================================================
   * DELETE SKILL
   * ============================================================
   */

  async function deleteSkill(
    skillId: number
  ) {
    try {
      await api(
        `/student/skills/${skillId}`,
        {
          method: 'DELETE',
        }
      );

      await load();

      flash(
        'Skill removed and analysis updated.'
      );
    } catch (e: any) {
      setError(
        e.message ||
          'Could not delete skill.'
      );
    }
  }

  /*
   * ============================================================
   * ADD EVIDENCE TO SKILL
   * ============================================================
   *
   * ONE evidence item is enough to verify a skill.
   */

  async function saveSkillEvidence(
    e: FormEvent<HTMLFormElement>,
    skillId: number
  ) {
    e.preventDefault();
    setError('');

    try {
      const f = new FormData(e.currentTarget);

      await api(
        `/student/skills/${skillId}/evidence`,
        {
          method: 'POST',

          body: JSON.stringify({
            kind: evidenceType,
            title: f.get('title'),
            url: f.get('url'),
          }),
        }
      );

      setEvidenceFor(null);

      await load();

      flash(
        'Evidence added. Skill verified.'
      );
    } catch (e: any) {
      setError(
        e.message ||
          'Could not save evidence.'
      );
    }
  }

  /*
   * ============================================================
   * PORTFOLIO EVIDENCE
   * ============================================================
   */

  async function savePortfolioEvidence(
    e: FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();
    setError('');
    const formElement = e.currentTarget;

    try {
      const f = new FormData(formElement);

      const payload: any = {
        title: f.get('title'),
        url: f.get('url'),
      };

      if (portfolioType === 'project') {
        payload.description =
          f.get('description');

        await api('/student/projects', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }

      if (portfolioType === 'certificate') {
        payload.issuer =
          f.get('issuer');

        await api('/student/certificates', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }

      if (portfolioType === 'course') {
        payload.provider =
          f.get('provider');

        await api('/student/courses', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }

      await load();

      flash(
        `${portfolioType[0].toUpperCase() +
          portfolioType.slice(1)} added to your portfolio.`
      );

      formElement.reset();
    } catch (e: any) {
      setError(
        e.message ||
          'Could not save evidence.'
      );
    }
  }

  async function saveStudentDocument(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    const formElement = e.currentTarget;
    try {
      const f = new FormData(formElement);
      const created = await api<StudentDocument>('/student/documents', {
        method: 'POST',
        body: JSON.stringify({
          title: f.get('documentTitle'),
          document_type: documentType,
          description: f.get('documentDescription') || '',
          issuer: f.get('documentIssuer') || '',
          issued_on: f.get('documentIssuedOn') || '',
          url: f.get('documentUrl') || '',
          visibility: documentVisibility,
        }),
      });
      setDocuments((items) => [created, ...items]);
      formElement.reset();
      setDocumentType('Certificate');
      setDocumentVisibility('Academician');
      flash('Document added to your secure portfolio vault.');
    } catch (e: any) {
      setError(e.message || 'Could not add document.');
    }
  }

  async function deleteStudentDocument(id: number) {
    setDocumentBusy(id);
    setError('');
    try {
      await api(`/student/documents/${id}`, { method: 'DELETE' });
      setDocuments((items) => items.filter((item) => item.id !== id));
      flash('Document removed.');
    } catch (e: any) {
      setError(e.message || 'Could not remove document.');
    } finally {
      setDocumentBusy(null);
    }
  }

  /*
   * ============================================================
   * INDUSTRY LEARNING PROGRAMS
   * ============================================================
   */

  async function updateStudentInternship(id: number, payload: Record<string, unknown>) {
    setInternshipBusy(id);
    setError('');
    try {
      const updated = await api<Internship>(`/internships/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
      setInternships((items) => items.map((item) => item.id === id ? updated : item));
    } catch (e: any) {
      setError(e.message || 'Unable to update internship.');
    } finally {
      setInternshipBusy(null);
    }
  }

  async function updateStudentMilestone(milestoneId: number, internshipId: number, status: string) {
    try {
      const updated = await api<Internship>(`/internships/milestones/${milestoneId}`, { method: 'PATCH', body: JSON.stringify({ status }) });
      setInternships((items) => items.map((item) => item.id === internshipId ? updated : item));
    } catch (e: any) {
      setError(e.message || 'Unable to update milestone.');
    }
  }

  async function enrollInLearningProgram(programId: number) {
    setLearningProgramBusy(programId);
    setError('');
    try {
      await api(`/learning-programs/${programId}/enroll`, {
        method: 'POST',
        body: JSON.stringify({ learning_program_id: programId }),
      });
      await load();
      flash('Enrolled in the AYUSH learning program.');
    } catch (e: any) {
      setError(e.message || 'Could not enroll in the learning program.');
    } finally {
      setLearningProgramBusy(null);
    }
  }

  async function updateLearningProgramStatus(
    enrollmentId: number,
    programId: number,
    status: 'Enrolled' | 'In Progress' | 'Completed' | 'Cancelled'
  ) {
    setLearningProgramBusy(programId);
    setError('');
    try {
      await api(`/learning-programs/enrollments/${enrollmentId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      await load();
      flash(
        status === 'Completed'
          ? 'Learning program marked as completed.'
          : `Learning program status updated to ${status}.`
      );
    } catch (e: any) {
      setError(e.message || 'Could not update the learning program.');
    } finally {
      setLearningProgramBusy(null);
    }
  }

  /*
   * ============================================================
   * APPLY
   * ============================================================
   */

  async function apply(
    opportunityId: number
  ) {
    try {
      await api(
        `/opportunities/${opportunityId}/apply`,
        {
          method: 'POST',
        }
      );

      await load();

      flash(
        'Application submitted.'
      );
    } catch (e: any) {
      setError(
        e.message ||
          'Could not submit application.'
      );
    }
  }

  /*
   * ============================================================
   * MY PROFILE
   * ============================================================
   */

  const renderProfile = () => (
    <div className="stack">
      {notice && (
        <div className="success-banner">
          ✓ {notice}
        </div>
      )}

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      <Card>
        <div className="section-title">
          Profile
        </div>

        <p className="muted form-intro">
          Keep your profile current.
          Your target role powers the
          SkillNova intelligence engine.
        </p>

        <form
          className="grid-form"
          onSubmit={saveProfile}
          autoComplete="off"
        >
          <label>
            Name

            <input
              name="name"
              defaultValue={profile.name || ''}
              autoComplete="off"
              required
            />
          </label>

          <label>
            Education

            <select
              name="education"
              defaultValue={profile.education || ''}
              autoComplete="off"
              required
            >
              <option value="">Select education</option>
              <option value="B.Sc">B.Sc</option>
              <option value="B.Sc (Hons.)">B.Sc (Hons.)</option>
              <option value="B.Tech">B.Tech</option>
              <option value="B.E.">B.E.</option>
              <option value="B.Pharm">B.Pharm</option>
              <option value="BAMS">BAMS</option>
              <option value="BHMS">BHMS</option>
              <option value="BUMS">BUMS</option>
              <option value="BSMS">BSMS</option>
              <option value="M.Sc">M.Sc</option>
              <option value="M.Tech">M.Tech</option>
              <option value="M.Pharm">M.Pharm</option>
              <option value="M.D. / M.S.">M.D. / M.S.</option>
              <option value="Ph.D.">Ph.D.</option>
              <option value="Other">Other</option>
            </select>
          </label>

          <label>
            Current year of study
            <select name="year_degree" defaultValue={profile.year_degree || ''} autoComplete="off" required>
              <option value="">Select year</option>
              <option value="1st Year">1st Year</option>
              <option value="2nd Year">2nd Year</option>
              <option value="3rd Year">3rd Year</option>
              <option value="4th Year">4th Year</option>
            </select>
          </label>

          <label>
            Current CGPA

            <input
              name="cgpa"
              type="number"
              min="0"
              max="10"
              step="0.01"
              defaultValue={academicCgpa ?? ''}
              placeholder="e.g. 8.20"
              autoComplete="off"
            />
            <span className="muted" style={{ display: 'block', marginTop: 5 }}>
              Used only when an opportunity specifies a minimum CGPA.
            </span>
          </label>

          <label>
            Target role

            <select
              name="target_role_id"
              defaultValue={profile.target_role_id || ''}
              autoComplete="off"
              required
            >
              <option value="">
                Select a role
              </option>

              {roles.map((r) => (
                <option
                  key={r.id}
                  value={r.id}
                >
                  {r.name}
                </option>
              ))}
            </select>
          </label>

          <label className="full">
            Career interests

            <textarea
              name="career_interests"
              defaultValue={
                profile.career_interests
              }
              placeholder="e.g. herbal formulation, pharmacognosy, research…"
            />
          </label>

          <button
            className="primary"
            disabled={saving}
          >
            {saving
              ? 'Saving…'
              : 'Save profile & recalculate'}
          </button>
        </form>
      </Card>

      <Card>
        <div className="evidence-header">
          <div>
            <div className="section-title">
              Portfolio evidence
            </div>

            <p className="muted">
              Add projects, certificates
              and courses to your portfolio.
            </p>
          </div>

          <div className="evidence-count">
            {allEvidence.length} saved
          </div>
        </div>

        <div className="evidence-tabs">
          {(
            [
              'project',
              'certificate',
              'course',
            ] as EvidenceType[]
          ).map((t) => (
            <button
              type="button"
              className={
                portfolioType === t
                  ? 'selected'
                  : ''
              }
              onClick={() =>
                setPortfolioType(t)
              }
              key={t}
            >
              {t === 'project'
                ? 'Projects'
                : t === 'certificate'
                ? 'Certificates'
                : 'Courses'}
            </button>
          ))}
        </div>

        <form
          className="evidence-builder"
          onSubmit={
            savePortfolioEvidence
          }
        >
          <div className="evidence-form-grid">
            <label>
              {portfolioType === 'project'
                ? 'Project title'
                : portfolioType ===
                  'certificate'
                ? 'Certificate name'
                : 'Course name'}

              <input
                name="title"
                required
                placeholder={
                  portfolioType ===
                  'project'
                    ? 'e.g. SkillNova platform'
                    : portfolioType ===
                      'certificate'
                    ? 'e.g. Python certificate'
                    : 'e.g. Data Science with Python'
                }
              />
            </label>

            {portfolioType ===
              'project' && (
              <label>
                Description

                <input
                  name="description"
                  placeholder="What did you build?"
                />
              </label>
            )}

            {portfolioType ===
              'certificate' && (
              <label>
                Issuer

                <input
                  name="issuer"
                  placeholder="Issuing organisation"
                />
              </label>
            )}

            {portfolioType ===
              'course' && (
              <label>
                Provider

                <input
                  name="provider"
                  placeholder="IIT / SWAYAM / Coursera…"
                />
              </label>
            )}

            <label>
              Evidence link

              <input
                name="url"
                placeholder="https://…"
              />
            </label>
          </div>

          <button className="primary">
            Add {portfolioType}
          </button>
        </form>

        <div className="section-title saved-title">
          Saved evidence
        </div>

        {allEvidence.length ? (
          <div className="evidence-list">
            {allEvidence.map(
              (x, i) => (
                <div
                  className="evidence-item"
                  key={`${x.type}-${x.title}-${i}`}
                >
                  <div className="evidence-icon">
                    {x.type[0]}
                  </div>

                  <div className="grow">
                    <strong>
                      {x.title}
                    </strong>

                    <div className="muted">
                      {x.type}
                      {x.meta
                        ? ` · ${x.meta}`
                        : ''}
                    </div>
                  </div>

                  {x.url && (
                    <a
                      className="text-link"
                      href={x.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open ↗
                    </a>
                  )}
                </div>
              )
            )}
          </div>
        ) : (
          <Empty
            title="No evidence yet"
            body="Add a project, certificate or course above."
          />
        )}
      </Card>
    </div>
  );

  /*
   * ============================================================
   * MY SKILLS
   * ============================================================
   */

  const renderMySkills = () => (
    <div className="stack">
      {notice && (
        <div className="success-banner">
          ✓ {notice}
        </div>
      )}

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      <Card>
        <div className="section-title">
          Build your skill profile
        </div>

        <p className="muted form-intro">
          Select the skills you have.
          You do not rate yourself.
          Attach at least one project,
          certificate or course to verify
          a skill.
        </p>

        <form
          className="skill-builder"
          onSubmit={addSkill}
        >
          <label className="skill-picker">
            Skill

            <select
              value={selectedSkill}
              onChange={(e) =>
                setSelectedSkill(
                  e.target.value
                )
              }
              required
            >
              <option value="">
                Choose a skill
              </option>

              {skills.map((s) => (
                <option
                  key={s.id}
                  value={s.id}
                >
                  {s.name} · {s.category}
                </option>
              ))}
            </select>
          </label>

          <div className="muted">
            Evidence determines
            verification.
          </div>

          <button
            className="primary"
            disabled={savingSkill}
          >
            {savingSkill
              ? 'Saving…'
              : 'Add skill'}
          </button>
        </form>
      </Card>

      <Card>
        <div className="section-title">
          Your live skill profile
        </div>

        {studentSkills.length ? (
          <div className="skill-cards">
            {studentSkills.map((s) => (
              <div
                className="skill-card"
                key={s.id}
              >
                <div className="skill-card-top">
                  <div>
                    <strong>
                      {s.skill}
                    </strong>

                    <div className="muted">
                      {s.verified
                        ? '✓ Verified'
                        : 'Evidence required'}
                    </div>
                  </div>

                  <button
                    type="button"
                    className="ghost danger"
                    onClick={() =>
                      deleteSkill(s.skill_id)
                    }
                  >
                    Delete
                  </button>
                </div>

                <Progress
                  value={
                    s.verified ? 100 : 0
                  }
                />

                <div className="skill-card-actions">
                  <span className="muted">
                    {s.evidence_count}{' '}
                    evidence item
                    {s.evidence_count ===
                    1
                      ? ''
                      : 's'}
                  </span>

                  <button
                    type="button"
                    className="secondary"
                    onClick={() =>
                      setEvidenceFor(
                        evidenceFor ===
                          s.id
                          ? null
                          : s.id
                      )
                    }
                  >
                    + Evidence
                  </button>
                </div>

                {evidenceFor === s.id && (
                  <form
                    className="mini-evidence"
                    onSubmit={(e) =>
                      saveSkillEvidence(
                        e,
                        s.skill_id
                      )
                    }
                  >
                    <select
                      value={
                        evidenceType
                      }
                      onChange={(e) =>
                        setEvidenceType(
                          e.target
                            .value as EvidenceType
                        )
                      }
                    >
                      <option value="project">
                        Project
                      </option>

                      <option value="certificate">
                        Certificate
                      </option>

                      <option value="course">
                        Course
                      </option>
                    </select>

                    <input
                      name="title"
                      placeholder="Evidence title"
                      required
                    />

                    <input
                      name="url"
                      placeholder="Link"
                    />

                    <button className="primary">
                      Attach
                    </button>
                  </form>
                )}
              </div>
            ))}
          </div>
        ) : (
          <Empty
            title="No skills yet"
            body="Add your first skill above."
          />
        )}
      </Card>
    </div>
  );

  /* ============================================================
   * SKILL ASSESSMENT
   * ============================================================ */
  const assessmentQuestions = assessment?.questions || [];
  const currentAssessmentQuestion = assessmentQuestions[assessmentQuestionIndex];

  const assessmentCards = [
    {
      type: 'Role-specific' as const,
      title: 'Role-Specific Assessment',
      subtitle: 'AYUSH technical & role knowledge',
      description: 'Test the concepts and professional reasoning required for your selected AYUSH target role.',
      icon: '✦',
      tone: 'blue',
    },
    {
      type: 'Aptitude' as const,
      title: 'Aptitude Assessment',
      subtitle: 'Logical & analytical reasoning',
      description: 'Measure quantitative, logical and research-oriented problem solving.',
      icon: '◇',
      tone: 'purple',
    },
    {
      type: 'Soft Skills' as const,
      title: 'Soft Skills Assessment',
      subtitle: 'Professional judgement & communication',
      description: 'Evaluate communication, teamwork, integrity and workplace decision-making.',
      icon: '◎',
      tone: 'teal',
    },
  ];

  const statusTone = (status: string) => {
    if (status === 'Strong') return 'green';
    if (status === 'Developing') return 'amber';
    if (status === 'Needs Improvement') return 'red';
    return 'blue';
  };

  const renderAssessmentResult = () => {
    if (!assessmentResult) return null;

    const areas = ['Technical', 'Soft Skills', 'Aptitude']
      .map((category) => {
        const items = assessmentResult.questions.filter((q) => q.category === category);
        return {
          category,
          items,
          correct: items.filter((q) => q.is_correct).length,
        };
      })
      .filter((x) => x.items.length);

    const missed = assessmentResult.questions.filter((q) => !q.is_correct);

    return (
      <div className="stack">
        <div className="page-intro">
          <div>
            <div className="eyebrow">Assessment complete</div>
            <h2>Your Assessment Results</h2>
            <p>See where your concepts are strong and what you should strengthen next.</p>
          </div>
          <button className="primary" onClick={resetAssessmentView}>Retake assessment</button>
        </div>

        <Card>
          <div style={{display:'grid',gridTemplateColumns:'1.2fr repeat(3,1fr)',gap:14,alignItems:'stretch'}}>
            <div className="assessment-result-hero">
              <div className="assessment-result-icon">✓</div>
              <div>
                <div className="muted">Overall assessment</div>
                <strong>{assessmentResult.overall_status}</strong>
                <p className="muted" style={{margin:'4px 0 0'}}>Your skill profile has been updated from this attempt.</p>
              </div>
            </div>
            {areas.map((a) => (
              <div key={a.category} className="assessment-stat-card">
                <div className="muted">{a.category}</div>
                <strong>{a.correct}/{a.items.length}</strong>
                <span>correct</span>
              </div>
            ))}
          </div>
        </Card>

        {assessmentResult.skill_results.length > 0 && (
          <Card>
            <div className="section-title">Strong points & skill gaps</div>
            <p className="muted">These findings are derived from your answers, not self-rated proficiency.</p>
            <div className="assessment-result-grid">
              {assessmentResult.skill_results.map((r) => (
                <div key={r.skill_id} className={`assessment-result-card ${statusTone(r.status)}`}>
                  <div className="assessment-result-card-head">
                    <strong>{r.skill}</strong>
                    <span className={`assessment-pill ${statusTone(r.status)}`}>{r.status}</span>
                  </div>
                  <p>
                    {r.status === 'Strong'
                      ? 'Strong conceptual understanding demonstrated. Keep applying this skill in real projects.'
                      : r.status === 'Developing'
                      ? 'The foundation is present. Strengthen application, reasoning and scenario-based practice.'
                      : 'Review the core concepts and practise applied problems before your next attempt.'}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        )}

        <Card>
          <div className="section-title">Concepts to strengthen</div>
          <p className="muted">Missed questions are explained so the result is actionable rather than just a score.</p>
          {missed.length ? (
            <div className="concept-list">
              {missed.map((q, i) => (
                <div key={q.question_id} className="concept-card">
                  <div className="concept-index">{i + 1}</div>
                  <div className="grow">
                    <div className="eyebrow">{q.category}</div>
                    <strong>{q.question}</strong>
                    <div className="concept-answer-row">
                      <span>Your answer: <b>{q.selected_option}</b></span>
                      <span>Correct: <b className="text-success">{q.correct_option}</b></span>
                    </div>
                    {q.explanation && <p className="muted">{q.explanation}</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="success-banner">Excellent — you did not miss any concepts in this attempt.</div>
          )}
        </Card>

        <Card>
          <div className="section-title">What next?</div>
          <div className="assessment-next-grid">
            <button className="assessment-next-card" onClick={resetAssessmentView}>
              <strong>Take another assessment</strong>
              <span>Change test type or difficulty and retake.</span>
            </button>
            <button className="assessment-next-card" onClick={() => setPage('Skill Gap')}>
              <strong>View your skill gaps</strong>
              <span>See which role requirements need attention.</span>
            </button>
            <button className="assessment-next-card" onClick={() => setPage('Learning')}>
              <strong>Open learning recommendations</strong>
              <span>Turn identified gaps into a learning plan.</span>
            </button>
          </div>
        </Card>

        <Card>
          <div className="section-title">Answer review</div>
          <p className="muted">Your selected answer, correct answer and explanation are available after submission.</p>
          <div className="answer-review-list">
            {assessmentResult.questions.map((q, i) => (
              <div key={q.question_id} className={`answer-review ${q.is_correct ? 'correct' : 'incorrect'}`}>
                <div className="answer-review-number">{i + 1}</div>
                <div className="grow">
                  <div className="eyebrow">{q.category}</div>
                  <strong>{q.question}</strong>
                  <p className="muted">Your answer: <b>{q.selected_option}</b> · Correct answer: <b>{q.correct_option}</b></p>
                  {q.explanation && <p className="muted">{q.explanation}</p>}
                </div>
                <span className={`assessment-pill ${q.is_correct ? 'green' : 'red'}`}>{q.is_correct ? 'Correct' : 'Incorrect'}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    );
  };

  const renderAssessment = () => {
    if (!profile.target_role_id) {
      return (
        <div className="stack">
          <div className="page-intro">
            <div><div className="eyebrow">Skill intelligence platform</div><h2>Assessment</h2><p>Choose your academic year and target role before starting an assessment.</p></div>
          </div>
          <Card>
            <div className="empty-state-panel">
              <div className="assessment-icon blue">✦</div>
              <div>
                <div className="section-title">Set up your assessment profile</div>
                <p className="muted">Select your target AYUSH role in My Profile. Your academic year is fixed here from My Profile and is used to calibrate question depth. Only test type and difficulty can be changed here.</p>
                <button className="primary" onClick={() => setPage('My Profile')}>Go to My Profile →</button>
              </div>
            </div>
          </Card>
        </div>
      );
    }

    if (assessmentResult) return renderAssessmentResult();

    if (assessmentLoading) {
      return (
        <div className="stack">
          <div className="page-intro"><div><div className="eyebrow">Skill intelligence platform</div><h2>Assessment</h2><p>Preparing your selected quiz…</p></div></div>
          <Card><div className="loading-panel"><div className="loading-spinner"/><strong>Building your assessment</strong><p className="muted">Questions are being calibrated for {assessmentYear}, {assessmentDifficulty} difficulty and your selected test type.</p></div></Card>
        </div>
      );
    }

    if (!assessment) {
      return (
        <div className="stack">
          <div className="page-intro">
            <div>
              <div className="eyebrow">Skill intelligence platform</div>
              <h2>Assessment</h2>
              <p>Measure your knowledge, reasoning and professional skills through focused AYUSH assessments.</p>
            </div>
          </div>

          {assessmentError && <div className="error">{assessmentError}</div>}

          <Card>
            <div className="assessment-setup-head">
              <div>
                <div className="section-title">Assessment setup</div>
                <p className="muted">Target role: <strong>{profile.target_role}</strong></p>
              </div>
              <span className="chip">AYUSH</span>
            </div>
            <div className="assessment-filters">
              <label>
                <span>Current year of study</span>
                <select
                  value={profile?.year_degree || assessmentYear}
                  disabled
                  aria-label="Current year of study from My Profile"
                  title="This year is taken from My Profile and cannot be changed here."
                >
                  <option value={profile?.year_degree || assessmentYear}>
                    {profile?.year_degree || assessmentYear}
                  </option>
                </select>
              </label>
              <label>
                <span>Test type</span>
                <select value={assessmentType} onChange={e => setAssessmentType(e.target.value as any)}>
                  <option>Role-specific</option>
                  <option>Aptitude</option>
                  <option>Soft Skills</option>
                </select>
              </label>
              <label>
                <span>Difficulty level</span>
                <select value={assessmentDifficulty} onChange={e => setAssessmentDifficulty(e.target.value as any)}>
                  <option>Easy</option>
                  <option>Medium</option>
                  <option>Hard</option>
                </select>
              </label>
            </div>
          </Card>

          <div className="assessment-card-grid">
            {assessmentCards.map((card) => {
              const selected = assessmentType === card.type;
              return (
                <Card key={card.type} className={`assessment-choice-card ${selected ? 'selected' : ''}`}>
                  <div className={`assessment-icon ${card.tone}`}>{card.icon}</div>
                  <div className="assessment-choice-copy">
                    <div className="assessment-choice-top">
                      <span className="eyebrow">{card.subtitle}</span>
                      {selected && <span className="assessment-pill blue">Selected</span>}
                    </div>
                    <h3>{card.title}</h3>
                    <p>{card.description}</p>
                    <div className="assessment-choice-meta">
                      <span>{assessmentDifficulty}</span>
                      <span>{assessmentYear}</span>
                      <span>MCQ</span>
                    </div>
                    <button className={selected ? 'primary' : 'secondary'} onClick={() => setAssessmentType(card.type)}>
                      {selected ? 'Selected' : 'Select test'}
                    </button>
                  </div>
                </Card>
              );
            })}
          </div>

          <Card className="assessment-launch-card">
            <div>
              <div className="eyebrow">Ready to begin?</div>
              <h3>{assessmentType} · {assessmentDifficulty}</h3>
              <p className="muted">Questions will be calibrated for a {assessmentYear} student and your target role.</p>
            </div>
            <button className="primary launch-button" onClick={startAssessment}>Take quiz →</button>
          </Card>
        </div>
      );
    }

    if (!currentAssessmentQuestion) return null;
    const selected = assessmentAnswers[String(currentAssessmentQuestion.id)];
    const progress = ((assessmentQuestionIndex + 1) / assessmentQuestions.length) * 100;

    return (
      <div className="stack">
        <div className="page-intro">
          <div>
            <div className="eyebrow">{assessmentType} · {assessmentDifficulty} · {assessmentYear}</div>
            <h2>{profile.target_role}</h2>
            <p>Choose the best answer. You can move between questions before submitting.</p>
          </div>
          <button className="secondary" onClick={resetAssessmentView}>Exit quiz</button>
        </div>

        {assessmentError && <div className="error">{assessmentError}</div>}

        <Card className="quiz-shell">
          <div className="quiz-progress-head">
            <div><strong>Question {assessmentQuestionIndex + 1}</strong><span> of {assessmentQuestions.length}</span></div>
            <span>{Object.keys(assessmentAnswers).length}/{assessmentQuestions.length} answered</span>
          </div>
          <div className="progress-track"><div className="progress-fill" style={{width:`${progress}%`}}/></div>

          <div className="quiz-card">
            <div className="quiz-meta">
              <span className="assessment-pill blue">{currentAssessmentQuestion.category}</span>
              <span className="assessment-pill purple">{assessmentDifficulty}</span>
              <span className="muted">Question {assessmentQuestionIndex + 1}</span>
            </div>
            <h3>{currentAssessmentQuestion.question}</h3>
            <div className="quiz-options">
              {(['A','B','C','D'] as const).map((o) => (
                <label key={o} className={`quiz-option ${selected === o ? 'selected' : ''}`}>
                  <input type="radio" name={`q-${currentAssessmentQuestion.id}`} checked={selected === o} onChange={() => setAssessmentAnswers(p => ({...p, [String(currentAssessmentQuestion.id)]: o}))}/>
                  <span className="option-letter">{o}</span>
                  <span>{currentAssessmentQuestion.options[o]}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="quiz-navigation">
            <button className="secondary" disabled={assessmentQuestionIndex === 0} onClick={() => setAssessmentQuestionIndex(x => Math.max(0, x - 1))}>← Previous</button>
            <div className="question-dots">
              {assessmentQuestions.map((q, i) => <button key={q.id} className={i === assessmentQuestionIndex ? 'active' : assessmentAnswers[String(q.id)] ? 'answered' : ''} onClick={() => setAssessmentQuestionIndex(i)} aria-label={`Question ${i + 1}`}>{i + 1}</button>)}
            </div>
            {assessmentQuestionIndex < assessmentQuestions.length - 1 ? (
              <button className="primary" disabled={!selected} onClick={() => setAssessmentQuestionIndex(x => x + 1)}>Next question →</button>
            ) : (
              <button className="primary" disabled={assessmentSubmitting || !selected} onClick={submitAssessment}>{assessmentSubmitting ? 'Submitting…' : 'Submit assessment ✓'}</button>
            )}
          </div>
        </Card>
      </div>
    );
  };

  /*
   * ============================================================
   * SKILL GAP
   * ============================================================
   *
   * ONLY CORE participates in readiness
   * and gap calculation.
   *
   * All other categories are displayed
   * separately for guidance.
   */

  const renderGapItem = (
    g: GapItem
  ) => (
    <div
      className="gap-row"
      key={g.skill_id}
    >
      <div className="grow">
        <strong>{g.skill}</strong>

        <div className="muted">
          Current {g.current}% · Required{' '}
          {g.required}%
        </div>

        <Progress
          value={g.current}
        />
      </div>

      <strong>
        {g.gap > 0
          ? `Gap ${g.gap}`
          : '✓ Ready'}
      </strong>
    </div>
  );

  const renderGapSection = (
    title: string,
    items: GapItem[],
    description: string
  ) => (
    <div className="gap-section">
      <div className="section-title">
        {title}
      </div>

      <p className="muted">
        {description}
      </p>

      {items.length ? (
        <div className="list">
          {items.map(renderGapItem)}
        </div>
      ) : (
        <div className="muted">
          No skills in this category.
        </div>
      )}
    </div>
  );

  const renderSkillGap = () => (
    <div className="stack">
      {error && (
        <div className="error">
          {error}
        </div>
      )}

      <Card>
        <div className="section-title">
          Skill-gap engine
        </div>

        <div className="engine-summary">
          <div>
            <div className="muted">
              Target role
            </div>

            <strong>
              {gap?.target_role?.name ||
                'Not selected'}
            </strong>
          </div>

          <div>
            <div className="muted">
              Core readiness
            </div>

            <strong>
              {gap?.readiness || 0}%
            </strong>
          </div>

          <div>
            <div className="muted">
              Active core gaps
            </div>

            <strong>
              {gap?.active_gaps || 0}
            </strong>
          </div>
        </div>
      </Card>

      {!gap?.target_role ? (
        <Card>
          <Empty
            title="Set a target role"
            body="Choose a target role in My Profile to generate the required skill pathway."
          />
        </Card>
      ) : (
        <>
          <Card>
            <div className="section-title">
              Current vs required skills
            </div>
            <p className="muted" style={{ marginTop: 0 }}>
              Your live core-skill levels compared with the requirements of your target role.
            </p>
            <SkillComparisonGraph items={gap.core} />
          </Card>

          <Card>
            {renderGapSection(
              'Core Skills',
              gap.core,
              'These skills define your readiness score and the main skill-gap analysis.'
            )}
          </Card>

          <Card>
            {renderGapSection(
              'Recommended Skills',
              gap.recommended,
              'Useful skills that strengthen your profile but do not affect core readiness.'
            )}
          </Card>

          <Card>
            {renderGapSection(
              'Alternative Skills',
              gap.alternatives,
              'Alternative technologies that can substitute for related skills.'
            )}
          </Card>

          <Card>
            {renderGapSection(
              'Advanced / Optional',
              gap.advanced,
              'Advanced skills that can strengthen your profile but are not required for core readiness.'
            )}
          </Card>
        </>
      )}
    </div>
  );

  /*
   * ============================================================
   * LEARNING
   * ============================================================
   */

  const getLearningResourceUrl = (resource: LearningResource) => {
    const rawUrl = (resource.url || '').trim();
    const platform = (resource.platform || '').toLowerCase();

    if (platform.includes('swayam') || /swayam\.gov\.in/i.test(rawUrl)) {
      const alreadySearchable = /searchText=/i.test(rawUrl);
      const looksLikeCoursePage = /\/course\//i.test(rawUrl) || /\/courses\//i.test(rawUrl);

      if (!alreadySearchable && !looksLikeCoursePage) {
        const query = resource.title.replace(/^learn\s+/i, '').trim() || resource.title;
        return `https://swayam.gov.in/search_courses?searchText=${encodeURIComponent(query)}`;
      }
    }

    return rawUrl;
  };

  const renderLearning = () => (
    <div className="stack">
      {error && <div className="error">{error}</div>}
      {notice && <div className="success-banner">✓ {notice}</div>}

      <Card>
        <div className="section-title">Personalized learning plan</div>
        <p className="muted">
          Courses are selected from your highest-priority CORE skill gaps.
          Each recommendation shows the skill gap it addresses and the learning platform.
        </p>

        {learning.length ? (
          <div className="list">
            {learning.map((item, index) => (
              <div className="learning" key={`${item.skill}-${index}`} style={{ alignItems: 'flex-start' }}>
                <div className="rank">{index + 1}</div>
                <div className="grow">
                  <strong>Build {item.skill}</strong>
                  <div className="muted" style={{ marginTop: 4 }}>
                    Gap {item.gap}% · Current {item.current}% · Required {item.required}% · {item.priority} priority
                  </div>
                  <Progress value={item.current} />

                  <div style={{ display: 'grid', gap: 10, marginTop: 14 }}>
                    <div style={{ border: '1px solid #e2e8f0', borderRadius: 10, padding: 13, background: '#fbfdff' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                        <div>
                          <strong style={{ fontSize: 14 }}>{item.resource.title}</strong>
                          <div className="muted" style={{ marginTop: 4 }}>
                            {item.resource.platform} · {item.resource.type} · {item.resource.level} · {item.resource.duration}
                          </div>
                        </div>
                        <a
                          className="secondary"
                          href={getLearningResourceUrl(item.resource)}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {item.resource.platform.toLowerCase().includes('swayam') ? 'Find exact course on SWAYAM' : 'View course'}
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Empty title="No active core gaps" body="Select a target AYUSH role and complete assessments to generate personalized learning recommendations." />
        )}
      </Card>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <div>
            <div className="section-title">AYUSH Industry Learning Programs</div>
            <p className="muted" style={{ marginTop: 5 }}>
              Discover training, certifications, workshops and mentorship programs published by AYUSH industry partners.
            </p>
          </div>
          <span className="chip">{industryPrograms.length} programs</span>
        </div>

        {industryPrograms.length ? (
          <div className="list" style={{ marginTop: 18 }}>
            {industryPrograms.map((program) => {
              const enrollment = program.enrollment;
              const busy = learningProgramBusy === program.id;

              return (
                <div
                  className="opportunity"
                  key={program.id}
                  style={{ alignItems: 'flex-start' }}
                >
                  <div className="grow">
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                      <strong>{program.title}</strong>
                      <span className="chip">{program.program_type}</span>
                    </div>

                    <div className="muted" style={{ marginTop: 5 }}>
                      {program.owner_name || 'AYUSH industry partner'}
                      {program.ayush_focus ? ` · ${program.ayush_focus}` : ''}
                    </div>

                    {program.description && (
                      <p style={{ margin: '9px 0 0', lineHeight: 1.55 }}>
                        {program.description}
                      </p>
                    )}

                    <div className="chips" style={{ marginTop: 10 }}>
                      {program.duration && <span className="chip">Duration: {program.duration}</span>}
                      {program.delivery_mode && <span className="chip">{program.delivery_mode}</span>}
                      {program.certificate_available && <span className="chip">Certificate</span>}
                      {program.registration_deadline && (
                        <span className="chip">Deadline: {program.registration_deadline}</span>
                      )}
                    </div>

                    {program.skills.length > 0 && (
                      <div style={{ marginTop: 11 }}>
                        <div className="muted" style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>
                          Skills developed
                        </div>
                        <div className="chips">
                          {program.skills.map((skill) => (
                            <span className="chip" key={skill.skill_id}>{skill.skill}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {program.eligibility && (
                      <div className="muted" style={{ marginTop: 10, fontSize: 12 }}>
                        <strong>Eligibility:</strong> {program.eligibility}
                      </div>
                    )}
                  </div>

                  <div style={{ minWidth: 150, display: 'grid', gap: 8 }}>
                    {!enrollment ? (
                      <button
                        type="button"
                        className="primary"
                        disabled={busy}
                        onClick={() => enrollInLearningProgram(program.id)}
                      >
                        {busy ? 'Enrolling…' : 'Enroll'}
                      </button>
                    ) : (
                      <>
                        <span
                          className="chip"
                          style={{
                            textAlign: 'center',
                            justifyContent: 'center',
                            padding: '9px 10px',
                            fontWeight: 800,
                          }}
                        >
                          {enrollment.status}
                        </span>

                        {enrollment.status === 'Enrolled' && (
                          <button
                            type="button"
                            className="secondary"
                            disabled={busy}
                            onClick={() => updateLearningProgramStatus(enrollment.id, program.id, 'In Progress')}
                          >
                            {busy ? 'Updating…' : 'Start program'}
                          </button>
                        )}

                        {enrollment.status === 'In Progress' && (
                          <button
                            type="button"
                            className="primary"
                            disabled={busy}
                            onClick={() => updateLearningProgramStatus(enrollment.id, program.id, 'Completed')}
                          >
                            {busy ? 'Updating…' : 'Mark completed'}
                          </button>
                        )}

                        {enrollment.status === 'Completed' && (
                          <div className="muted" style={{ fontSize: 12, textAlign: 'center' }}>
                            ✓ Completed
                            {enrollment.completed_at
                              ? ` · ${new Date(enrollment.completed_at).toLocaleDateString()}`
                              : ''}
                          </div>
                        )}
                      </>
                    )}

                    {program.registration_url && (
                      <a
                        className="secondary"
                        href={program.registration_url}
                        target="_blank"
                        rel="noreferrer"
                        style={{ textAlign: 'center', textDecoration: 'none' }}
                      >
                        Program details ↗
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <Empty
            title="No industry learning programs yet"
            body="AYUSH training, certification, workshop and mentorship programs published by industry partners will appear here."
          />
        )}
      </Card>
    </div>
  );

  /*
   * ============================================================
   * OPPORTUNITIES
   * ============================================================
   */

  const renderOpportunities = () => (
    <div className="stack">
      {error && <div className="error">{error}</div>}

      <Card>
        <div className="section-title">AYUSH opportunity marketplace</div>
        <p className="muted form-intro">
          SkillNova checks your verified skills against each opportunity and explains
          what you already meet, what is missing, and whether you can apply now.
        </p>

        {opps.length ? (
          <div className="list">
            {opps.map((o) => {
              const application = apps.find((a) => a.opportunity_id === o.id);
              const applied = Boolean(application);
              const eligible = o.eligible !== false;
              const missing = o.missing_skills || [];
              const matched = o.matched_skills || [];

              return (
                <div className="opportunity" key={o.id}>
                  <div className="grow">
                    <strong>{o.title}</strong>
                    <div className="muted">
                      {o.opportunity_type} · {o.location}
                      {typeof o.match_percentage === 'number'
                        ? ` · ${o.match_percentage}% skill match`
                        : ''}
                    </div>

                    <p>{o.description}</p>

                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                      <span className="chip">
                        {eligible ? '✓ Eligible now' : '⚠ Skill gap'}
                      </span>
                      {matched.length > 0 && (
                        <span className="chip">{matched.length} requirements met</span>
                      )}
                      {missing.length > 0 && (
                        <span className="chip">{missing.length} to build</span>
                      )}
                    </div>

                    {o.academic_eligibility && (
                      <div style={{ marginTop: 12, padding: '10px 12px', border: '1px solid #e3e9ef', borderRadius: 8 }}>
                        <strong style={{ fontSize: 12 }}>Academic eligibility</strong>
                        <div style={{ display: 'grid', gap: 5, marginTop: 7, fontSize: 12 }}>
                          <span>{o.academic_eligibility.required_education || 'Any education'} · {o.academic_eligibility.education_ok ? '✓ education met' : '⚠ education requirement not met'}</span>
                          <span>{o.academic_eligibility.minimum_year ? `Year ${o.academic_eligibility.minimum_year}+ required` : 'Any academic year'} · {o.academic_eligibility.year_ok ? '✓ year met' : '⚠ year requirement not met'}</span>
                          <span>{o.academic_eligibility.minimum_cgpa != null ? `CGPA ${o.academic_eligibility.minimum_cgpa.toFixed(2)}+ required` : 'No CGPA requirement'} · {o.academic_eligibility.cgpa_ok ? '✓ CGPA met' : o.academic_eligibility.minimum_cgpa != null ? '⚠ CGPA requirement not met / not provided' : '✓ not required'}</span>
                        </div>
                        {o.academic_eligibility.notes && <div className="muted" style={{ marginTop: 7 }}>{o.academic_eligibility.notes}</div>}
                      </div>
                    )}

                    <div style={{ marginTop: 12 }}>
                      <strong style={{ fontSize: 12 }}>Explainable skill match</strong>
                      <div style={{ display: 'grid', gap: 7, marginTop: 8 }}>
                        {o.requirements.map((r) => (
                          <div
                            key={r.skill_id}
                            style={{
                              display: 'grid',
                              gridTemplateColumns: 'minmax(0,1fr) auto',
                              gap: 10,
                              alignItems: 'center',
                              padding: '8px 10px',
                              border: '1px solid #e3e9ef',
                              borderRadius: 8,
                            }}
                          >
                            <div>
                              <strong style={{ fontSize: 13 }}>{r.skill}</strong>
                              <div className="muted">
                                {r.student_level ?? 0}% current · {r.required_level}% required
                                {r.verified ? ' · verified' : ' · not verified'}
                              </div>
                            </div>
                            <span style={{
                              fontSize: 12,
                              fontWeight: 700,
                              color: r.meets_requirement ? '#28734a' : '#a54b3f',
                            }}>
                              {r.meets_requirement
                                ? 'Meets'
                                : `Gap ${r.gap ?? Math.max(r.required_level - (r.student_level ?? 0), 0)}%`}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {!eligible && (
                      <div style={{ marginTop: 10 }} className="muted">
                        <strong>What to build next:</strong>{' '}
                        {missing.map((x) => `${x.skill} (${x.gap}% gap)`).join(' · ')}
                      </div>
                    )}
                  </div>

                  <button
                    type="button"
                    className={applied || !eligible ? "secondary" : "primary"}
                    disabled={applied || !eligible}
                    onClick={() => apply(o.id)}
                    aria-label={
                      applied
                        ? `Applied to ${o.title}`
                        : !eligible
                          ? `Not currently eligible for ${o.title}`
                          : `Apply to ${o.title}`
                    }
                  >
                    {applied ? '✓ Applied' : eligible ? 'Apply' : 'Not eligible'}
                  </button>
                </div>
              );
            })}
          </div>
        ) : (
          <Empty
            title="No opportunities yet"
            body="Published AYUSH opportunities will appear here."
          />
        )}
      </Card>
    </div>
  );


  /*
   * ============================================================
   * APPLICATIONS
   * ============================================================
   */

  const renderApplications = () => (
    <Card>
      <div className="section-title">
        Applications
      </div>

      {apps.length ? (
        <div className="list">
          {apps.map((a) => (
            <div
              className="gap-row"
              key={a.id}
            >
              <div className="grow">
                <strong>
                  {a.title}
                </strong>

                <div className="muted">
                  {a.company} · Applied{' '}
                  {new Date(
                    a.created_at
                  ).toLocaleDateString()}
                </div>
              </div>

              <span className="status">
                {a.status}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <Empty
          title="No applications"
          body="Apply to an opportunity to track it here."
        />
      )}
    </Card>
  );

  /*
   * ============================================================
   * PORTFOLIO
   * ============================================================
   */

  const renderPortfolio = () => (
    <div className="portfolio">
      <Card>
        <div className="portfolio-head">
          <div>
            <div className="eyebrow">
              SkillNova portfolio
            </div>

            <h2>
              {profile.name ||
                'Student'}
            </h2>

            <p>
              {profile.education ||
                'Education not added'}

              {profile.year_degree
                ? ` · ${profile.year_degree}`
                : ''}
            </p>

            <p>
              Target role ·{' '}
              {profile.target_role ||
                'Not set'}
            </p>
          </div>

          <div className="readiness">
            <strong>
              {gap?.readiness || 0}%
            </strong>

            <span>
              core readiness
            </span>
          </div>
        </div>
      </Card>

      <div className="two-col">
        <Card>
          <div className="section-title">
            Skills
          </div>

          {studentSkills.length ? (
            studentSkills.map((s) => (
              <div
                className="portfolio-skill"
                key={s.id}
              >
                <span>
                  {s.skill}
                </span>

                <span>
                  {s.verified
                    ? 'Verified'
                    : 'Unverified'}
                </span>
              </div>
            ))
          ) : (
            <Empty
              title="No skills added"
              body="Build your skill profile to populate your portfolio."
            />
          )}
        </Card>

        <Card>
          <div className="section-title">
            Projects & credentials
          </div>

          {allEvidence.length ? (
            allEvidence.map(
              (x, i) => (
                <div
                  className="line-item"
                  key={`${x.type}-${x.title}-${i}`}
                >
                  <strong>
                    {x.type}
                  </strong>{' '}
                  · {x.title}

                  {x.meta && (
                    <div className="muted">
                      {x.meta}
                    </div>
                  )}
                </div>
              )
            )
          ) : (
            <Empty
              title="No evidence yet"
              body="Add projects, certificates or courses from My Profile."
            />
          )}
        </Card>
      </div>
    </div>
  );

  /*
   * ============================================================
   * PERSONALIZED CAREER PATHS
   * ============================================================
   */

  const renderInternships = () => (
    <div className="stack">
      {error && <div className="error">{error}</div>}
      <Card>
        <div className="eyebrow">YOUR AYUSH INTERNSHIP JOURNEY</div>
        <h2>Internships & field experience</h2>
        <p className="muted form-intro">Track your internship from selection to milestones, mentor feedback and completion evidence.</p>
      </Card>
      {internships.length ? internships.map((internship) => (
        <Card key={internship.id}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
            <div className="grow">
              <div className="eyebrow">{internship.company_name || 'AYUSH industry partner'}</div>
              <h3 style={{ margin: '5px 0' }}>{internship.opportunity_title}</h3>
              <div className="muted">Mentor · {internship.mentor_name || 'Not assigned yet'}</div>
            </div>
            <div style={{ minWidth: 180 }}>
              <strong>{internship.progress_percent}%</strong><div className="muted">progress</div>
              <div className="progress" style={{ marginTop: 8 }}><span style={{ width: `${internship.progress_percent}%` }} /></div>
              <div className="status" style={{ marginTop: 8 }}>{internship.status}</div>
            </div>
          </div>
          <div className="two-col" style={{ marginTop: 18 }}>
            <div><div className="muted">Start</div><strong>{internship.start_date ? new Date(internship.start_date).toLocaleDateString() : 'Not set'}</strong></div>
            <div><div className="muted">Expected completion</div><strong>{internship.expected_end_date ? new Date(internship.expected_end_date).toLocaleDateString() : 'Not set'}</strong></div>
          </div>
          <div style={{ marginTop: 20 }}>
            <label style={{ fontWeight: 700 }}>My progress</label>
            <input style={{ width: '100%', marginTop: 10 }} type="range" min="0" max="100" value={internship.progress_percent} onChange={(e) => setInternships((items) => items.map((x) => x.id === internship.id ? { ...x, progress_percent: Number(e.target.value) } : x))} onMouseUp={(e) => updateStudentInternship(internship.id, { progress_percent: Number((e.target as HTMLInputElement).value), status: Number((e.target as HTMLInputElement).value) === 100 ? 'Completed' : 'Ongoing' })} />
          </div>
          <div style={{ marginTop: 20 }}>
            <div className="section-title">Milestones</div>
            {internship.milestones.length ? internship.milestones.map((milestone) => (
              <div className="gap-row" key={milestone.id}>
                <div className="grow"><strong>{milestone.title}</strong><div className="muted">{milestone.description}</div></div>
                <select className="input" value={milestone.status} onChange={(e) => updateStudentMilestone(milestone.id, internship.id, e.target.value)}>
                  <option>Pending</option><option>In Progress</option><option>Completed</option>
                </select>
              </div>
            )) : <div className="muted">Your internship manager has not added milestones yet.</div>}
          </div>
          <div style={{ marginTop: 20 }}>
            <div className="section-title">Mentor feedback</div>
            {internship.feedback.length ? internship.feedback.map((item) => (
              <div className="gap-row" key={item.id}><div><strong>{item.author_name || item.author_role}</strong><div className="muted">{item.feedback}</div></div>{item.rating ? <span className="status">{item.rating}/5</span> : null}</div>
            )) : <div className="muted">Feedback will appear here as your mentor reviews your work.</div>}
          </div>
          {(internship.certificate_url || internship.report_url || internship.status === 'Completed') && (
            <div style={{ marginTop: 20 }} className="chips">
              {internship.certificate_url && <a className="chip" href={internship.certificate_url} target="_blank" rel="noreferrer">Certificate</a>}
              {internship.report_url && <a className="chip" href={internship.report_url} target="_blank" rel="noreferrer">Completion report</a>}
              {internship.status === 'Completed' && !internship.certificate_url && <span className="chip">Completion recorded</span>}
            </div>
          )}
        </Card>
      )) : <Card><Empty title="No internships yet" body="When an AYUSH industry partner selects you for an internship or apprenticeship, its lifecycle will appear here." /></Card>}
    </div>
  );

  const renderCareerPaths = () => {
    const strongSkills = selectedCareerRoadmap.filter(
      (item) => item.status === 'Already strong'
    );
    const learningSteps = selectedCareerRoadmap.filter(
      (item) => item.status !== 'Already strong'
    );

    return (
      <div className="stack">
        {error && <div className="error">{error}</div>}

        <div className="hero">
          <div>
            <div className="eyebrow">YOUR PERSONALIZED AYUSH ROADMAP</div>
            <h2>Roles you can build toward — one skill at a time.</h2>
            <p>
              SkillNova compares your current evidence-backed skills with the
              AYUSH role framework, then turns the gaps into a step-by-step
              learning path that changes as your profile changes.
            </p>
          </div>
          <button className="primary" onClick={() => setPage('My Skills')}>
            Update my skills
          </button>
        </div>

        {!careerPaths.length ? (
          <Card>
            <Empty
              title="Your career paths are being built"
              body="Add skills to your profile and complete an assessment so SkillNova can personalize your roles and roadmap."
            />
          </Card>
        ) : (
          <>
            <Card>
              <div className="section-title">
                Roles that match your current skill profile
              </div>
              <p className="muted" style={{ marginTop: 0 }}>
                These are learning-path matches, not hiring eligibility
                decisions. The recommendations update when your skills or
                evidence change.
              </p>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                  gap: 14,
                  marginTop: 18,
                }}
              >
                {careerPaths.slice(0, 8).map((path) => {
                  const selected = path.role_id === selectedCareerRoleId;
                  const target = path.role_id === profile?.target_role_id;

                  return (
                    <button
                      key={path.role_id}
                      type="button"
                      onClick={() => setSelectedCareerRoleId(path.role_id)}
                      style={{
                        textAlign: 'left',
                        border: selected
                          ? '2px solid currentColor'
                          : '1px solid rgba(15,23,42,0.12)',
                        borderRadius: 16,
                        background: selected ? 'rgba(15,23,42,0.035)' : 'white',
                        padding: 18,
                        cursor: 'pointer',
                        color: 'inherit',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          gap: 12,
                          alignItems: 'flex-start',
                        }}
                      >
                        <div>
                          <strong style={{ fontSize: 16 }}>{path.role_name}</strong>
                          {target && (
                            <span
                              style={{
                                display: 'inline-block',
                                marginLeft: 8,
                                fontSize: 11,
                                fontWeight: 700,
                                padding: '4px 7px',
                                borderRadius: 999,
                                background: 'rgba(15,23,42,0.08)',
                              }}
                            >
                              Your target
                            </span>
                          )}
                        </div>
                        <strong style={{ fontSize: 18 }}>{path.readiness}%</strong>
                      </div>

                      <div
                        style={{
                          height: 7,
                          borderRadius: 999,
                          background: 'rgba(15,23,42,0.10)',
                          marginTop: 14,
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            width: `${Math.max(0, Math.min(100, path.readiness))}%`,
                            height: '100%',
                            borderRadius: 999,
                            background: 'currentColor',
                          }}
                        />
                      </div>

                      <p className="muted" style={{ margin: '12px 0 0' }}>
                        {path.core_matched} of {path.core_total} core skills met
                        {path.next_skill
                          ? ` · Next: ${path.next_skill}`
                          : ' · Core foundation is complete'}
                      </p>

                      {path.matched_skills.length > 0 && (
                        <div style={{ marginTop: 12, fontSize: 12 }}>
                          <span className="muted">You already bring: </span>
                          {path.matched_skills.slice(0, 3).join(' · ')}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </Card>

            {selectedCareerPath && (
              <>
                <Card>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      gap: 18,
                      flexWrap: 'wrap',
                    }}
                  >
                    <div style={{ maxWidth: 760 }}>
                      <div className="eyebrow">SELECTED CAREER PATH</div>
                      <div className="section-title" style={{ fontSize: 25 }}>
                        {selectedCareerPath.role_name}
                      </div>
                      <p className="muted" style={{ marginTop: 6 }}>
                        {selectedCareerPath.description ||
                          'A personalized AYUSH role pathway based on your current skills.'}
                      </p>
                    </div>

                    <div
                      style={{
                        minWidth: 150,
                        textAlign: 'center',
                        padding: 14,
                        borderRadius: 14,
                        background: 'rgba(15,23,42,0.04)',
                      }}
                    >
                      <div className="muted" style={{ fontSize: 12 }}>
                        Current alignment
                      </div>
                      <strong style={{ fontSize: 30 }}>
                        {selectedCareerPath.readiness}%
                      </strong>
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                      gap: 10,
                      marginTop: 18,
                    }}
                  >
                    <div className="gap-mini">
                      <div>
                        <strong>{selectedCareerPath.core_matched}</strong>
                        <div className="muted">Core skills met</div>
                      </div>
                    </div>
                    <div className="gap-mini">
                      <div>
                        <strong>{selectedCareerPath.core_partial}</strong>
                        <div className="muted">Core skills to strengthen</div>
                      </div>
                    </div>
                    <div className="gap-mini">
                      <div>
                        <strong>{selectedCareerPath.core_missing}</strong>
                        <div className="muted">Core skills to start</div>
                      </div>
                    </div>
                  </div>
                </Card>

                {strongSkills.length > 0 && (
                  <Card>
                    <div className="section-title">Your starting foundation</div>
                    <p className="muted" style={{ marginTop: 0 }}>
                      These skills already meet this role's current core
                      requirement. Use them as the foundation for the next steps.
                    </p>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                        gap: 10,
                        marginTop: 14,
                      }}
                    >
                      {strongSkills.map((item) => (
                        <div className="gap-mini" key={`strong-${item.skill_id}`}>
                          <div>
                            <strong>{item.skill}</strong>
                            <div className="muted">
                              {item.current}% current · {item.required}% required
                            </div>
                          </div>
                          <span>✓</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                <Card>
                  <div className="section-title">Your skill-by-skill roadmap</div>
                  <p className="muted" style={{ marginTop: 0 }}>
                    Follow the steps in order. When a skill reaches the required
                    level, the next step becomes your focus. There is no fixed
                    timeline — your roadmap moves when your skill profile moves.
                  </p>

                  {learningSteps.length ? (
                    <div style={{ marginTop: 20 }}>
                      {learningSteps.map((item, index) => (
                        <div
                          key={`${selectedCareerPath.role_id}-${item.skill_id}-${item.category}`}
                          style={{
                            display: 'grid',
                            gridTemplateColumns: '44px minmax(0, 1fr)',
                            gap: 14,
                            position: 'relative',
                            paddingBottom: index === learningSteps.length - 1 ? 0 : 22,
                          }}
                        >
                          {index < learningSteps.length - 1 && (
                            <div
                              style={{
                                position: 'absolute',
                                left: 21,
                                top: 42,
                                bottom: 0,
                                width: 2,
                                background: 'rgba(15,23,42,0.10)',
                              }}
                            />
                          )}

                          <div
                            style={{
                              width: 42,
                              height: 42,
                              borderRadius: '50%',
                              display: 'grid',
                              placeItems: 'center',
                              fontWeight: 800,
                              background: 'rgba(15,23,42,0.07)',
                              position: 'relative',
                              zIndex: 1,
                            }}
                          >
                            {index + 1}
                          </div>

                          <div
                            style={{
                              border: '1px solid rgba(15,23,42,0.10)',
                              borderRadius: 14,
                              padding: 16,
                              background: 'white',
                            }}
                          >
                            <div
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                gap: 12,
                                alignItems: 'flex-start',
                                flexWrap: 'wrap',
                              }}
                            >
                              <div>
                                <div
                                  style={{
                                    fontSize: 11,
                                    fontWeight: 800,
                                    letterSpacing: '.06em',
                                    textTransform: 'uppercase',
                                    opacity: 0.65,
                                  }}
                                >
                                  {item.status}
                                </div>
                                <strong style={{ fontSize: 18 }}>{item.skill}</strong>
                              </div>
                              <span
                                style={{
                                  padding: '6px 9px',
                                  borderRadius: 999,
                                  fontSize: 12,
                                  fontWeight: 700,
                                  background: 'rgba(15,23,42,0.06)',
                                }}
                              >
                                {item.current}% → {item.required}%
                              </span>
                            </div>

                            <p style={{ margin: '10px 0 5px' }}>{item.action}</p>
                            <div className="muted" style={{ fontSize: 13 }}>
                              {item.reason}
                              {item.verified && ' · Academically verified'}
                            </div>

                            {item.gap > 0 && (
                              <div className="muted" style={{ marginTop: 8, fontSize: 12 }}>
                                Current gap: {item.gap} points · Category: {item.category}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <Empty
                      title="Your core foundation is complete"
                      body="Explore the advanced skills in this role or select another career path to see a different roadmap."
                    />
                  )}
                </Card>

                <Card>
                  <div className="section-title">How this roadmap changes for you</div>
                  <div className="two-col" style={{ marginTop: 14 }}>
                    <div>
                      <strong>When you add a skill</strong>
                      <p className="muted">
                        The current level is recalculated and that skill can move
                        from a learning step into your foundation.
                      </p>
                    </div>
                    <div>
                      <strong>When you add evidence</strong>
                      <p className="muted">
                        Evidence-backed levels and verification can change your
                        role alignment and reorder the next skills to build.
                      </p>
                    </div>
                  </div>
                </Card>
              </>
            )}
          </>
        )}
      </div>
    );
  };

  /*
   * ============================================================
   * DASHBOARD
   * ============================================================
   */

  const renderDashboard = () => (
    <div className="stack">
      {notice && (
        <div className="success-banner">
          ✓ {notice}
        </div>
      )}

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      <div className="hero">
        <div>
          <div className="eyebrow">
            Your live skill intelligence
          </div>

          <h2>
            Build toward the role
            you want.
          </h2>

          <p>
            Evidence-backed skills,
            core skill gaps, learning
            priorities and opportunities
            in one place.
          </p>
        </div>

        <button
          className="primary"
          onClick={() =>
            setPage('My Profile')
          }
        >
          Complete profile
        </button>
      </div>

      <div className="stats">
        <Stat
          label="Core readiness"
          value={`${gap?.readiness || 0}%`}
          sub="Based only on core skills"
        />

        <Stat
          label="Verified skills"
          value={
            studentSkills.filter(
              (s) => s.verified
            ).length
          }
        />

        <Stat
          label="Core skill gaps"
          value={
            gap?.active_gaps || 0
          }
        />

        <Stat
          label="Applications"
          value={apps.length}
        />
      </div>

      <Card>
        <div className="section-title">
          Overall skill readiness
        </div>
        <p className="muted" style={{ marginTop: 0 }}>
          Your readiness updates whenever your verified skills or target-role requirements change.
        </p>
        <ReadinessGraph value={gap?.readiness || 0} />
      </Card>

      <div className="two-col">
        <Card>
          <div className="section-title">
            Top core gaps
          </div>

          {activeCoreGaps.length ? (
            activeCoreGaps
              .slice()
              .sort(
                (a, b) =>
                  b.gap - a.gap
              )
              .slice(0, 4)
              .map((g) => (
                <div
                  className="gap-mini"
                  key={g.skill_id}
                >
                  <div>
                    <strong>
                      {g.skill}
                    </strong>

                    <div className="muted">
                      {g.current}% →{' '}
                      {g.required}%
                    </div>
                  </div>

                  <span>
                    {g.gap} gap
                  </span>
                </div>
              ))
          ) : (
            <Empty
              title="No active core gaps"
              body="Choose a target role and add evidence-backed skills."
            />
          )}
        </Card>

        <Card>
          <div className="section-title">
            Portfolio evidence
          </div>

          {allEvidence.length ? (
            allEvidence
              .slice(0, 4)
              .map((x, i) => (
                <div
                  className="gap-mini"
                  key={`${x.type}-${x.title}-${i}`}
                >
                  <div>
                    <strong>
                      {x.title}
                    </strong>

                    <div className="muted">
                      {x.type}
                    </div>
                  </div>

                  <span>
                    ✓
                  </span>
                </div>
              ))
          ) : (
            <Empty
              title="No evidence yet"
              body="Add projects, certificates or courses."
            />
          )}
        </Card>
      </div>
      <Card>
        <div className="section-title">Secure document vault</div>
        <p className="muted">Store certificates, reports, resumes and academic records with controlled visibility. Documents marked for Academician or Industry access remain discoverable only through authorized SkillNova views.</p>
        <form className="evidence-builder" onSubmit={saveStudentDocument}>
          <div className="evidence-form-grid">
            <label>
              Document title
              <input name="documentTitle" required placeholder="e.g. AYUSH Research Internship Certificate" />
            </label>
            <label>
              Document type
              <select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                <option>Certificate</option>
                <option>Internship Report</option>
                <option>Resume</option>
                <option>Academic Record</option>
                <option>Project Report</option>
                <option>Research Output</option>
                <option>Other</option>
              </select>
            </label>
            <label>
              Issuer / institution
              <input name="documentIssuer" placeholder="University, AYUSH organisation, company…" />
            </label>
            <label>
              Issued on
              <input name="documentIssuedOn" placeholder="YYYY-MM-DD" />
            </label>
            <label>
              Document link
              <input name="documentUrl" placeholder="Secure/private document URL" />
            </label>
            <label>
              Access
              <select value={documentVisibility} onChange={(e) => setDocumentVisibility(e.target.value as 'Private' | 'Academician' | 'Industry')}>
                <option value="Private">Private</option>
                <option value="Academician">Academician</option>
                <option value="Industry">Industry</option>
              </select>
            </label>
            <label>
              Description
              <input name="documentDescription" placeholder="What does this document prove?" />
            </label>
          </div>
          <button className="primary">Add to document vault</button>
        </form>

        <div className="section-title saved-title">Documents</div>
        {documents.length ? documents.map((document) => (
          <div className="gap-row" key={document.id}>
            <div className="grow">
              <strong>{document.title}</strong>
              <div className="muted">{document.document_type}{document.issuer ? ` · ${document.issuer}` : ''} · {document.visibility}</div>
              <div className="muted">Verification: {document.verification_status}{document.rejection_reason ? ` · ${document.rejection_reason}` : ''}</div>
            </div>
            <div className="actions">
              {document.url && <a className="button secondary" href={document.url} target="_blank" rel="noreferrer">Open</a>}
              <button className="button secondary" disabled={documentBusy === document.id} onClick={() => deleteStudentDocument(document.id)}>Remove</button>
            </div>
          </div>
        )) : <Empty title="No documents yet" body="Add certificates, reports, resumes or academic records to complete your portfolio." />}
      </Card>

      <Card>
        <div className="section-title">Internship experience</div>
        {internships.length ? internships.slice(0, 4).map((internship) => (
          <div className="gap-row" key={internship.id}>
            <div className="grow">
              <strong>{internship.opportunity_title}</strong>
              <div className="muted">{internship.company_name} · {internship.status} · {internship.progress_percent}% complete</div>
            </div>
            {internship.status === 'Completed' && <span className="status">Completed</span>}
          </div>
        )) : <Empty title="No internship experience yet" body="Completed AYUSH internships will become part of your portfolio automatically." />}
      </Card>
    </div>
  );

  /*
   * ============================================================
   * PAGE ROUTER
   * ============================================================
   */

  if (page === 'My Profile') {
    return renderProfile();
  }

  if (page === 'My Skills') {
    return renderMySkills();
  }

  if (page === 'Assessment') {
    return renderAssessment();
  }

  if (page === 'Skill Gap') {
    return renderSkillGap();
  }

  if (page === 'Learning') {
    return renderLearning();
  }

  if (page === 'Career Paths') {
    return renderCareerPaths();
  }

  if (page === 'Internships') {
    return renderInternships();
  }

  if (page === 'Opportunities') {
    return renderOpportunities();
  }

  if (page === 'Applications') {
    return renderApplications();
  }

  if (page === 'Portfolio') {
    return renderPortfolio();
  }

  return renderDashboard();
}