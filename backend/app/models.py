from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Float,
    ForeignKey,
    Text,
    DateTime,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


# ============================================================
# USER
# ============================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255)
    )

    role: Mapped[str] = mapped_column(
        String(30),
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    profile: Mapped["Profile"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )


# ============================================================
# PROFILE
# ============================================================

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True
    )

    name: Mapped[str] = mapped_column(
        String(120),
        default=""
    )

    education: Mapped[str] = mapped_column(
        String(255),
        default=""
    )

    year_degree: Mapped[str] = mapped_column(
        String(120),
        default=""
    )

    target_role_id: Mapped[int | None] = mapped_column(
        ForeignKey("roles.id"),
        nullable=True
    )

    career_interests: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    research_experience: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    achievements: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    user: Mapped[User] = relationship(
        back_populates="profile"
    )

    target_role: Mapped["Role | None"] = relationship()

    skills: Mapped[list["StudentSkill"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    projects: Mapped[list["Project"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    certificates: Mapped[list["Certificate"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    courses: Mapped[list["Course"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan"
    )


# ============================================================
# SKILLS
# ============================================================

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        index=True
    )

    category: Mapped[str] = mapped_column(
        String(100),
        default="General"
    )


# ============================================================
# STUDENT SKILLS
# ============================================================

class StudentSkill(Base):
    __tablename__ = "student_skills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    profile_id: Mapped[int] = mapped_column(
        ForeignKey(
            "profiles.id",
            ondelete="CASCADE"
        )
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "skills.id",
            ondelete="CASCADE"
        )
    )

    # Internal calculated proficiency.
    # This is derived from assessment results.
    # It should NOT be directly entered by the student.
    proficiency: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    profile: Mapped[Profile] = relationship(
        back_populates="skills"
    )

    skill: Mapped[Skill] = relationship()

    assessments: Mapped[list["SkillAssessment"]] = relationship(
        back_populates="student_skill",
        cascade="all, delete-orphan"
    )

    history: Mapped[list["SkillHistory"]] = relationship(
        back_populates="student_skill",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "skill_id",
            name="uq_student_skill"
        ),
    )


# ============================================================
# LEGACY / EXISTING SKILL ASSESSMENT
# ============================================================
# Kept for backward compatibility with the existing application.
# The new MCQ assessment workflow is implemented below using
# Assessment, AssessmentQuestion, AssessmentAttempt,
# AssessmentResponse and SkillAssessmentResult.

class SkillAssessment(Base):
    __tablename__ = "skill_assessments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    student_skill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "student_skills.id",
            ondelete="CASCADE"
        )
    )

    score: Mapped[int] = mapped_column(
        Integer
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=10
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    student_skill: Mapped[StudentSkill] = relationship(
        back_populates="assessments"
    )


# ============================================================
# SKILL HISTORY
# ============================================================

class SkillHistory(Base):
    __tablename__ = "skill_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    student_skill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "student_skills.id",
            ondelete="CASCADE"
        )
    )

    proficiency: Mapped[int] = mapped_column(
        Integer
    )

    source: Mapped[str] = mapped_column(
        String(50),
        default="assessment"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    student_skill: Mapped[StudentSkill] = relationship(
        back_populates="history"
    )


# ============================================================
# NEW ASSESSMENT SYSTEM
# ============================================================

class Assessment(Base):
    """
    A role-specific assessment.

    Example:
        AYUSH Research Assistant Assessment
        AYUSH Product Development Associate Assessment
    """

    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey(
            "roles.id",
            ondelete="CASCADE"
        )
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    role: Mapped["Role"] = relationship()

    questions: Mapped[list["AssessmentQuestion"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan"
    )

    attempts: Mapped[list["AssessmentAttempt"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            name="uq_assessment_role"
        ),
    )


# ============================================================
# ASSESSMENT QUESTIONS
# ============================================================

class AssessmentQuestion(Base):
    """
    MCQ question.

    category values:
        Technical
        Soft Skills
        Aptitude

    skill_id connects a question to the skill it assesses.
    """

    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    assessment_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessments.id",
            ondelete="CASCADE"
        )
    )

    skill_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "skills.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    category: Mapped[str] = mapped_column(
        String(50)
    )

    question: Mapped[str] = mapped_column(
        Text
    )

    option_a: Mapped[str] = mapped_column(
        Text
    )

    option_b: Mapped[str] = mapped_column(
        Text
    )

    option_c: Mapped[str] = mapped_column(
        Text
    )

    option_d: Mapped[str] = mapped_column(
        Text
    )

    # Stored on backend only.
    # Never send this field to the student before submission.
    correct_option: Mapped[str] = mapped_column(
        String(1)
    )

    explanation: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    assessment: Mapped[Assessment] = relationship(
        back_populates="questions"
    )

    skill: Mapped["Skill | None"] = relationship()

    responses: Mapped[list["AssessmentResponse"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "order_index",
            name="uq_assessment_question_order"
        ),
    )


# ============================================================
# ASSESSMENT ATTEMPT
# ============================================================

class AssessmentAttempt(Base):
    """
    Represents one student's attempt at one role assessment.

    IMPORTANT:
    A student can attempt a particular role assessment only once.
    """

    __tablename__ = "assessment_attempts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        )
    )

    assessment_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessments.id",
            ondelete="CASCADE"
        )
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="IN_PROGRESS"
    )

    score: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # Stable configuration key for one role/year/test-type/difficulty quiz.
    # This allows one student to take different assessment configurations
    # without changing the legacy Assessment table structure.
    configuration_key: Mapped[str] = mapped_column(
        String(100),
        default="legacy",
        index=True
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    student: Mapped[User] = relationship()

    assessment: Mapped[Assessment] = relationship(
        back_populates="attempts"
    )

    responses: Mapped[list["AssessmentResponse"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan"
    )

    skill_results: Mapped[list["SkillAssessmentResult"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        # One attempt per student per assessment configuration.
        # Configuration is role + profile year + test type + difficulty.
        UniqueConstraint(
            "student_id",
            "assessment_id",
            "configuration_key",
            name="uq_student_assessment_config_attempt"
        ),
    )


# ============================================================
# ASSESSMENT RESPONSE
# ============================================================

class AssessmentResponse(Base):
    """
    Stores the student's selected answer for each MCQ.

    is_correct is calculated by the backend.
    """

    __tablename__ = "assessment_responses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessment_attempts.id",
            ondelete="CASCADE"
        )
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessment_questions.id",
            ondelete="CASCADE"
        )
    )

    selected_option: Mapped[str | None] = mapped_column(
        String(1),
        nullable=True
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    answered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    attempt: Mapped[AssessmentAttempt] = relationship(
        back_populates="responses"
    )

    question: Mapped[AssessmentQuestion] = relationship(
        back_populates="responses"
    )

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_attempt_question_response"
        ),
    )


# ============================================================
# SKILL-WISE ASSESSMENT RESULT
# ============================================================

class SkillAssessmentResult(Base):
    """
    Stores the result of an assessment for an individual skill.

    status values:
        Strong
        Developing
        Needs Improvement
        Not Assessed

    Numeric score is kept internally for calculations.
    The student-facing UI should primarily show the status.
    """

    __tablename__ = "skill_assessment_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessment_attempts.id",
            ondelete="CASCADE"
        )
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "skills.id",
            ondelete="CASCADE"
        )
    )

    correct_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # Internal percentage used by the matching/readiness engine.
    score: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    status: Mapped[str] = mapped_column(
        String(40),
        default="Not Assessed"
    )

    attempt: Mapped[AssessmentAttempt] = relationship(
        back_populates="skill_results"
    )

    skill: Mapped[Skill] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "skill_id",
            name="uq_attempt_skill_result"
        ),
    )


# ============================================================
# EVIDENCE
# ============================================================

class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    student_skill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "student_skills.id",
            ondelete="CASCADE"
        )
    )

    kind: Mapped[str] = mapped_column(
        String(80)
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    url: Mapped[str] = mapped_column(
        String(500),
        default=""
    )


# ============================================================
# PROJECT
# ============================================================

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    profile_id: Mapped[int] = mapped_column(
        ForeignKey(
            "profiles.id",
            ondelete="CASCADE"
        )
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    url: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    profile: Mapped[Profile] = relationship(
        back_populates="projects"
    )


# ============================================================
# CERTIFICATE
# ============================================================

class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    profile_id: Mapped[int] = mapped_column(
        ForeignKey(
            "profiles.id",
            ondelete="CASCADE"
        )
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    issuer: Mapped[str] = mapped_column(
        String(255),
        default=""
    )

    url: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    profile: Mapped[Profile] = relationship(
        back_populates="certificates"
    )


# ============================================================
# COURSE
# ============================================================

class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    profile_id: Mapped[int] = mapped_column(
        ForeignKey(
            "profiles.id",
            ondelete="CASCADE"
        )
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    provider: Mapped[str] = mapped_column(
        String(255),
        default=""
    )

    url: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    profile: Mapped[Profile] = relationship(
        back_populates="courses"
    )


# ============================================================
# CAREER ROLE
# ============================================================

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True
    )

    description: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    requirements: Mapped[list["RoleSkillRequirement"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan"
    )


# ============================================================
# ROLE SKILL REQUIREMENTS
# ============================================================

class RoleSkillRequirement(Base):
    __tablename__ = "role_skill_requirements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey(
            "roles.id",
            ondelete="CASCADE"
        )
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "skills.id",
            ondelete="CASCADE"
        )
    )

    # Internal competency requirement level.
    required_level: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    category: Mapped[str] = mapped_column(
        String(50),
        default="Core"
    )

    alternative_group: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    role: Mapped[Role] = relationship(
        back_populates="requirements"
    )

    skill: Mapped[Skill] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "skill_id",
            name="uq_role_skill"
        ),
    )


# ============================================================
# OPPORTUNITIES
# ============================================================

class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        )
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    opportunity_type: Mapped[str] = mapped_column(
        String(80),
        default="Internship"
    )

    location: Mapped[str] = mapped_column(
        String(255),
        default="Remote"
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Published"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    owner: Mapped[User] = relationship()

    requirements: Mapped[
        list["OpportunitySkillRequirement"]
    ] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan"
    )


# ============================================================
# OPPORTUNITY SKILL REQUIREMENTS
# ============================================================

class StudentAcademicRecord(Base):
    __tablename__ = "student_academic_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)


class OpportunityEligibility(Base):
    __tablename__ = "opportunity_eligibility"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    required_education: Mapped[str] = mapped_column(String(255), default="")
    minimum_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minimum_cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    eligibility_notes: Mapped[str] = mapped_column(Text, default="")


class OpportunitySkillRequirement(Base):
    __tablename__ = "opportunity_skill_requirements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey(
            "opportunities.id",
            ondelete="CASCADE"
        )
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "skills.id",
            ondelete="CASCADE"
        )
    )

    required_level: Mapped[int] = mapped_column(
        Integer
    )

    opportunity: Mapped[Opportunity] = relationship(
        back_populates="requirements"
    )

    skill: Mapped[Skill] = relationship()




# ============================================================
# ACADEMIA–INDUSTRY FACULTY OPPORTUNITIES
# ============================================================

class FacultyOpportunity(Base):
    """Industry/academic opportunities intended for faculty and academic professionals."""

    __tablename__ = "faculty_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    opportunity_type: Mapped[str] = mapped_column(String(100), default="Collaborative Research")
    ayush_focus: Mapped[str] = mapped_column(String(150), default="AYUSH")
    location: Mapped[str] = mapped_column(String(255), default="Remote")
    delivery_mode: Mapped[str] = mapped_column(String(50), default="Hybrid")
    duration: Mapped[str] = mapped_column(String(120), default="")
    eligibility: Mapped[str] = mapped_column(Text, default="")
    registration_url: Mapped[str] = mapped_column(String(1000), default="")
    status: Mapped[str] = mapped_column(String(50), default="Published")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped[User] = relationship()
    skills: Mapped[list["FacultyOpportunitySkill"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    applications: Mapped[list["FacultyOpportunityApplication"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )


class FacultyOpportunitySkill(Base):
    __tablename__ = "faculty_opportunity_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("faculty_opportunities.id", ondelete="CASCADE"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"))

    opportunity: Mapped[FacultyOpportunity] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship()

    __table_args__ = (UniqueConstraint("opportunity_id", "skill_id", name="uq_faculty_opportunity_skill"),)


class FacultyOpportunityApplication(Base):
    __tablename__ = "faculty_opportunity_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("faculty_opportunities.id", ondelete="CASCADE"))
    academician_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="Applied")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    opportunity: Mapped[FacultyOpportunity] = relationship(back_populates="applications")
    academician: Mapped[User] = relationship()

    __table_args__ = (UniqueConstraint("opportunity_id", "academician_id", name="uq_faculty_opportunity_applicant"),)



# ============================================================
# ACADEMIA-INDUSTRY COLLABORATION LIFECYCLE
# ============================================================

class Collaboration(Base):
    """A structured collaboration created from an accepted faculty opportunity."""
    __tablename__ = "collaborations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("faculty_opportunities.id", ondelete="SET NULL"), nullable=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("faculty_opportunity_applications.id", ondelete="SET NULL"), nullable=True, unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    academician_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    collaboration_type: Mapped[str] = mapped_column(String(100), default="Collaborative Research")
    ayush_focus: Mapped[str] = mapped_column(String(150), default="AYUSH")
    objective: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="Planned")
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expected_end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completion_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    academician: Mapped[User] = relationship(foreign_keys=[academician_id])
    opportunity: Mapped[FacultyOpportunity | None] = relationship()
    application: Mapped[FacultyOpportunityApplication | None] = relationship()
    milestones: Mapped[list["CollaborationMilestone"]] = relationship(back_populates="collaboration", cascade="all, delete-orphan")
    feedback: Mapped[list["CollaborationFeedback"]] = relationship(back_populates="collaboration", cascade="all, delete-orphan")
    outputs: Mapped[list["CollaborationOutput"]] = relationship(back_populates="collaboration", cascade="all, delete-orphan")


class CollaborationMilestone(Base):
    __tablename__ = "collaboration_milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collaboration_id: Mapped[int] = mapped_column(ForeignKey("collaborations.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Planned")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    collaboration: Mapped[Collaboration] = relationship(back_populates="milestones")


class CollaborationFeedback(Base):
    __tablename__ = "collaboration_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collaboration_id: Mapped[int] = mapped_column(ForeignKey("collaborations.id", ondelete="CASCADE"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    feedback_type: Mapped[str] = mapped_column(String(50), default="Progress")
    comments: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    collaboration: Mapped[Collaboration] = relationship(back_populates="feedback")
    author: Mapped[User] = relationship()


class CollaborationOutput(Base):
    __tablename__ = "collaboration_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collaboration_id: Mapped[int] = mapped_column(ForeignKey("collaborations.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    output_type: Mapped[str] = mapped_column(String(100), default="Report")
    description: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(1000), default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    collaboration: Mapped[Collaboration] = relationship(back_populates="outputs")


# ============================================================
# INTERNSHIP LIFECYCLE
# ============================================================

class InternshipRecord(Base):
    """Lifecycle record created after a student is selected for an internship."""

    __tablename__ = "internship_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        unique=True,
    )

    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE")
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    mentor_name: Mapped[str] = mapped_column(String(255), default="")
    mentor_email: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(50), default="Not Started")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expected_end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    summary: Mapped[str] = mapped_column(Text, default="")
    certificate_url: Mapped[str] = mapped_column(String(500), default="")
    report_url: Mapped[str] = mapped_column(String(500), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    application: Mapped["Application"] = relationship()
    opportunity: Mapped["Opportunity"] = relationship()
    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    company: Mapped["User"] = relationship(foreign_keys=[company_id])
    milestones: Mapped[list["InternshipMilestone"]] = relationship(
        back_populates="internship", cascade="all, delete-orphan"
    )
    feedback: Mapped[list["InternshipFeedback"]] = relationship(
        back_populates="internship", cascade="all, delete-orphan"
    )


class InternshipMilestone(Base):
    """Ordered work checkpoints for an active internship."""

    __tablename__ = "internship_milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    internship_id: Mapped[int] = mapped_column(
        ForeignKey("internship_records.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Pending")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    internship: Mapped[InternshipRecord] = relationship(back_populates="milestones")


class InternshipFeedback(Base):
    """Mentor, company, academic or student feedback attached to an internship."""

    __tablename__ = "internship_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    internship_id: Mapped[int] = mapped_column(
        ForeignKey("internship_records.id", ondelete="CASCADE")
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    author_role: Mapped[str] = mapped_column(String(50), default="company")
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    internship: Mapped[InternshipRecord] = relationship(back_populates="feedback")
    author: Mapped["User"] = relationship()


# ============================================================
# INDUSTRY LEARNING PROGRAMS
# ============================================================

class LearningProgram(Base):
    """
    AYUSH-focused learning program published by an industry partner.

    Examples:
        AYUSH Drug Quality Control Training
        Herbal Formulation Workshop
        Medicinal Plant Identification Certification
        AYUSH Regulatory Documentation Workshop
        Industry Mentorship Program
    """

    __tablename__ = "learning_programs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        )
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    program_type: Mapped[str] = mapped_column(
        String(80),
        default="Training"
    )

    ayush_focus: Mapped[str] = mapped_column(
        String(255),
        default=""
    )

    duration: Mapped[str] = mapped_column(
        String(120),
        default=""
    )

    delivery_mode: Mapped[str] = mapped_column(
        String(50),
        default="Remote"
    )

    eligibility: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    registration_deadline: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    certificate_available: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    registration_url: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Published"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    owner: Mapped[User] = relationship()

    skills: Mapped[list["LearningProgramSkill"]] = relationship(
        back_populates="learning_program",
        cascade="all, delete-orphan"
    )

    enrollments: Mapped[list["LearningProgramEnrollment"]] = relationship(
        back_populates="learning_program",
        cascade="all, delete-orphan"
    )


# ============================================================
# LEARNING PROGRAM SKILLS
# ============================================================

class LearningProgramSkill(Base):
    """
    Skills that students can develop through a learning program.
    """

    __tablename__ = "learning_program_skills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    learning_program_id: Mapped[int] = mapped_column(
        ForeignKey(
            "learning_programs.id",
            ondelete="CASCADE"
        )
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "skills.id",
            ondelete="CASCADE"
        )
    )

    learning_program: Mapped[LearningProgram] = relationship(
        back_populates="skills"
    )

    skill: Mapped[Skill] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "learning_program_id",
            "skill_id",
            name="uq_learning_program_skill"
        ),
    )


# ============================================================
# LEARNING PROGRAM ENROLLMENT
# ============================================================

class LearningProgramEnrollment(Base):
    """
    Student participation and completion record for a learning program.

    Status values can include:
        Enrolled
        In Progress
        Completed
        Cancelled
    """

    __tablename__ = "learning_program_enrollments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    learning_program_id: Mapped[int] = mapped_column(
        ForeignKey(
            "learning_programs.id",
            ondelete="CASCADE"
        )
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        )
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Enrolled"
    )

    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    certificate_url: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    learning_program: Mapped[LearningProgram] = relationship(
        back_populates="enrollments"
    )

    student: Mapped[User] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "learning_program_id",
            "student_id",
            name="uq_learning_program_enrollment"
        ),
    )



# ============================================================
# APPLICATION
# ============================================================

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey(
            "opportunities.id",
            ondelete="CASCADE"
        )
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        )
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Applied"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    opportunity: Mapped[Opportunity] = relationship()

    student: Mapped[User] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "opportunity_id",
            "student_id",
            name="uq_application"
        ),
    )


# ============================================================
# STUDENT DOCUMENT MANAGEMENT
# ============================================================

class StudentDocument(Base):
    __tablename__ = "student_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    title: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(80), default="Certificate")
    description: Mapped[str] = mapped_column(Text, default="")
    issuer: Mapped[str] = mapped_column(String(255), default="")
    issued_on: Mapped[str] = mapped_column(String(40), default="")
    url: Mapped[str] = mapped_column(String(1000), default="")
    visibility: Mapped[str] = mapped_column(String(40), default="Academician")
    verification_status: Mapped[str] = mapped_column(String(40), default="Pending")
    rejection_reason: Mapped[str] = mapped_column(Text, default="")
    linked_internship_id: Mapped[int | None] = mapped_column(
        ForeignKey("internship_records.id", ondelete="SET NULL"), nullable=True
    )
    linked_collaboration_id: Mapped[int | None] = mapped_column(
        ForeignKey("collaborations.id", ondelete="SET NULL"), nullable=True
    )
    verified_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    student: Mapped[User] = relationship(foreign_keys=[student_id])
    verifier: Mapped[User | None] = relationship(foreign_keys=[verified_by])

