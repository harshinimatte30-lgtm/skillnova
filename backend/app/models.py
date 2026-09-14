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
        # ONE attempt per student per role assessment
        UniqueConstraint(
            "student_id",
            "assessment_id",
            name="uq_student_assessment_attempt"
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
