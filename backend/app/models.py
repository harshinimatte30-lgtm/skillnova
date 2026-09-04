from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    education: Mapped[str] = mapped_column(String(255), default="")
    year_degree: Mapped[str] = mapped_column(String(120), default="")
    target_role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)
    career_interests: Mapped[str] = mapped_column(Text, default="")
    research_experience: Mapped[str] = mapped_column(Text, default="")
    achievements: Mapped[str] = mapped_column(Text, default="")
    user: Mapped[User] = relationship(back_populates="profile")
    target_role: Mapped["Role | None"] = relationship()
    skills: Mapped[list["StudentSkill"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    certificates: Mapped[list["Certificate"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    courses: Mapped[list["Course"]] = relationship(back_populates="profile", cascade="all, delete-orphan")

class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(100), default="General")

class StudentSkill(Base):
    __tablename__ = "student_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE")
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE")
    )

    # Current calculated proficiency
    proficiency: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped[Profile] = relationship(back_populates="skills")
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

class SkillAssessment(Base):
    __tablename__ = "skill_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    student_skill_id: Mapped[int] = mapped_column(
        ForeignKey("student_skills.id", ondelete="CASCADE")
    )

    score: Mapped[int] = mapped_column(Integer)
    total_questions: Mapped[int] = mapped_column(Integer, default=10)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    student_skill: Mapped[StudentSkill] = relationship(
        back_populates="assessments"
    )
class SkillHistory(Base):
    __tablename__ = "skill_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    student_skill_id: Mapped[int] = mapped_column(
        ForeignKey("student_skills.id", ondelete="CASCADE")
    )

    proficiency: Mapped[int] = mapped_column(Integer)

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

class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_skill_id: Mapped[int] = mapped_column(ForeignKey("student_skills.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(500), default="")

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    profile: Mapped[Profile] = relationship(back_populates="projects")

class Certificate(Base):
    __tablename__ = "certificates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    issuer: Mapped[str] = mapped_column(String(255), default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    profile: Mapped[Profile] = relationship(back_populates="certificates")

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(255), default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    profile: Mapped[Profile] = relationship(back_populates="courses")

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[list["RoleSkillRequirement"]] = relationship(back_populates="role", cascade="all, delete-orphan")

class RoleSkillRequirement(Base):
    __tablename__ = "role_skill_requirements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE")
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE")
    )

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

class Opportunity(Base):
    __tablename__ = "opportunities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    opportunity_type: Mapped[str] = mapped_column(String(80), default="Internship")
    location: Mapped[str] = mapped_column(String(255), default="Remote")
    status: Mapped[str] = mapped_column(String(50), default="Published")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[User] = relationship()
    requirements: Mapped[list["OpportunitySkillRequirement"]] = relationship(back_populates="opportunity", cascade="all, delete-orphan")

class OpportunitySkillRequirement(Base):
    __tablename__ = "opportunity_skill_requirements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"))
    required_level: Mapped[int] = mapped_column(Integer)
    opportunity: Mapped[Opportunity] = relationship(back_populates="requirements")
    skill: Mapped[Skill] = relationship()

class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(50), default="Applied")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    opportunity: Mapped[Opportunity] = relationship()
    student: Mapped[User] = relationship()
    __table_args__ = (UniqueConstraint("opportunity_id", "student_id", name="uq_application"),)
