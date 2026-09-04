import { FormEvent, useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api';
import { Card, Stat, Progress, Empty } from '../components/UI';
import { Profile, Skill, RoleOption } from '../types';

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

type Opportunity = {
  id: number;
  title: string;
  description: string;
  opportunity_type: string;
  location: string;
  created_at?: string;
  requirements: {
    skill_id: number;
    skill: string;
    required_level: number;
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


function SkillComparisonGraph({ items }: { items: GapItem[] }) {
  const data = items;

  if (!data.length) {
    return (
      <div className="muted" style={{ padding: '24px 0' }}>
        No core skill data available yet.
      </div>
    );
  }

  const chartWidth = 760;
  const chartHeight = 330;
  const margin = { top: 30, right: 24, bottom: 78, left: 48 };
  const innerWidth = chartWidth - margin.left - margin.right;
  const innerHeight = chartHeight - margin.top - margin.bottom;
  const groupWidth = innerWidth / data.length;
  const barWidth = Math.min(24, Math.max(12, groupWidth * 0.22));
  const gap = Math.max(5, barWidth * 0.3);
  const scaleY = (value: number) =>
    margin.top + innerHeight -
    (Math.max(0, Math.min(100, value)) / 100) * innerHeight;

  return (
    <div style={{ overflowX: 'auto' }}>
      <svg
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        width="100%"
        role="img"
        aria-label="Current versus required skill levels by core skill"
        style={{ minWidth: 650, display: 'block' }}
      >
        {[0, 25, 50, 75, 100].map((tick) => {
          const y = scaleY(tick);
          return (
            <g key={tick}>
              <line
                x1={margin.left}
                x2={chartWidth - margin.right}
                y1={y}
                y2={y}
                stroke="currentColor"
                opacity="0.10"
              />
              <text
                x={margin.left - 10}
                y={y + 4}
                textAnchor="end"
                fontSize="11"
                fill="currentColor"
                opacity="0.65"
              >
                {tick}%
              </text>
            </g>
          );
        })}

        {data.map((item, index) => {
          const centerX = margin.left + groupWidth * index + groupWidth / 2;
          const requiredHeight =
            (Math.max(0, Math.min(100, item.required)) / 100) * innerHeight;
          const currentHeight =
            (Math.max(0, Math.min(100, item.current)) / 100) * innerHeight;
          const requiredX = centerX - barWidth - gap / 2;
          const currentX = centerX + gap / 2;
          const requiredY = scaleY(item.required);
          const currentY = scaleY(item.current);

          return (
            <g key={item.skill_id}>
              <title>
                {item.skill}: Current {item.current}%, Required {item.required}%, Gap {item.gap}%
              </title>

              <rect
                x={requiredX}
                y={requiredY}
                width={barWidth}
                height={requiredHeight}
                rx="4"
                fill="currentColor"
                opacity="0.30"
              />

              <rect
                x={currentX}
                y={currentY}
                width={barWidth}
                height={currentHeight}
                rx="4"
                fill="currentColor"
              />

              <text
                x={centerX}
                y={chartHeight - margin.bottom + 22}
                textAnchor="middle"
                fontSize="11"
                fontWeight="600"
                fill="currentColor"
              >
                {item.skill.length > 14 ? `${item.skill.slice(0, 13)}…` : item.skill}
              </text>
            </g>
          );
        })}

        <line
          x1={margin.left}
          x2={chartWidth - margin.right}
          y1={margin.top + innerHeight}
          y2={margin.top + innerHeight}
          stroke="currentColor"
          opacity="0.22"
        />

        <g transform={`translate(${margin.left}, ${chartHeight - 18})`}>
          <rect width="12" height="12" rx="2" fill="currentColor" opacity="0.30" />
          <text x="18" y="10" fontSize="11" fill="currentColor" opacity="0.75">
            Required
          </text>
          <rect x="82" width="12" height="12" rx="2" fill="currentColor" />
          <text x="100" y="10" fontSize="11" fill="currentColor" opacity="0.75">
            Current
          </text>
        </g>
      </svg>
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
  const [gap, setGap] = useState<GapResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [apps, setApps] = useState<Application[]>([]);

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
      ] = await Promise.all([
        api<Profile>('/profile'),
        api<Skill[]>('/skills'),
        api<RoleOption[]>('/roles'),
        api<StudentSkill[]>('/student/skills'),
        api<GapResponse>('/student/skill-gap'),
        api<PortfolioData>('/portfolio'),
        api<Opportunity[]>('/opportunities'),
        api<Application[]>('/student/applications'),
      ]);

      setProfile(p);
      setSkills(s);
      setRoles(r);
      setStudentSkills(studentSkillData);
      setGap(gapData);
      setPortfolio(portfolioData);
      setOpps(opportunityData);
      setApps(applicationData);
    } catch (e: any) {
      setError(
        e.message ||
          'Unable to load your SkillNova data.'
      );
    }
  }

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

  const activeCoreGaps =
    gap?.core?.filter((x) => x.gap > 0) || [];

  /*
   * Learning recommendations are generated from CORE gaps.
   *
   * We do not need a separate backend /learning endpoint.
   */

  const learning = useMemo(() => {
    return [...activeCoreGaps]
      .sort((a, b) => b.gap - a.gap)
      .map((x) => ({
        skill: x.skill,
        gap: x.gap,
        current: x.current,
        required: x.required,
        url:
          `https://www.google.com/search?q=` +
          encodeURIComponent(
            `learn ${x.skill}`
          ),
      }));
  }, [gap]);

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

    try {
      const f = new FormData(e.currentTarget);

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

      e.currentTarget.reset();
    } catch (e: any) {
      setError(
        e.message ||
          'Could not save evidence.'
      );
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
        >
          <label>
            Name

            <input
              name="name"
              defaultValue={profile.name}
            />
          </label>

          <label>
            Education

            <input
              name="education"
              defaultValue={
                profile.education
              }
              placeholder="B.Tech / B.Sc / M.Sc"
            />
          </label>

          <label>
            Year / degree

            <input
              name="year_degree"
              defaultValue={
                profile.year_degree
              }
              placeholder="2nd year"
            />
          </label>

          <label>
            Target role

            <select
              name="target_role_id"
              defaultValue={
                profile.target_role_id || ''
              }
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
              placeholder="AI, research, data, software…"
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

  const renderLearning = () => (
    <div className="stack">
      {error && (
        <div className="error">
          {error}
        </div>
      )}

      <Card>
        <div className="section-title">
          Learning priorities
        </div>

        <div className="muted">
          Recommendations are generated
          from your highest-priority CORE
          skill gaps.
        </div>

        {learning.length ? (
          <div className="list">
            {learning.map(
              (x, i) => (
                <div
                  className="learning"
                  key={x.skill}
                >
                  <div className="rank">
                    {i + 1}
                  </div>

                  <div className="grow">
                    <strong>
                      Build {x.skill}
                    </strong>

                    <div className="muted">
                      Gap {x.gap} · Current{' '}
                      {x.current}% · Required{' '}
                      {x.required}%
                    </div>

                    <Progress
                      value={x.current}
                    />
                  </div>

                  <a
                    className="secondary"
                    href={x.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Explore
                  </a>
                </div>
              )
            )}
          </div>
        ) : (
          <Empty
            title="No active core gaps"
            body="You are currently meeting all core requirements or have not selected a target role."
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
      {error && (
        <div className="error">
          {error}
        </div>
      )}

      <Card>
        <div className="section-title">
          Opportunity marketplace
        </div>

        {opps.length ? (
          <div className="list">
            {opps.map((o) => (
              <div
                className="opportunity"
                key={o.id}
              >
                <div className="grow">
                  <strong>
                    {o.title}
                  </strong>

                  <div className="muted">
                    {o.opportunity_type}
                    {' · '}
                    {o.location}
                  </div>

                  <p>
                    {o.description}
                  </p>

                  <div className="chips">
                    {o.requirements.map(
                      (r) => (
                        <span
                          className="chip"
                          key={r.skill_id}
                        >
                          {r.skill}{' '}
                          {r.required_level}%
                        </span>
                      )
                    )}
                  </div>
                </div>

                <button
                  className="primary"
                  onClick={() =>
                    apply(o.id)
                  }
                >
                  Apply
                </button>
              </div>
            ))}
          </div>
        ) : (
          <Empty
            title="No opportunities yet"
            body="Published opportunities will appear here."
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

  if (page === 'Skill Gap') {
    return renderSkillGap();
  }

  if (page === 'Learning') {
    return renderLearning();
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