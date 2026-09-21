from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional


# ============================================================
# AUTH
# ============================================================

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: str
    name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    name: str

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# PROFILE
# ============================================================

class ProfileIn(BaseModel):
    name: str = ""
    education: str = ""
    year_degree: str = ""
    target_role_id: Optional[int] = None
    career_interests: str = ""
    research_experience: str = ""
    achievements: str = ""


# ============================================================
# SKILLS
# ============================================================

class SkillIn(BaseModel):
    skill_id: int

    # Students do not directly set their skill level.
    # The backend updates the internal value from assessment results.
    proficiency: int = Field(default=0, ge=0, le=100)


# ============================================================
# EVIDENCE
# ============================================================

class EvidenceIn(BaseModel):
    kind: str
    title: str
    url: str = ""


# ============================================================
# PORTFOLIO ITEMS
# ============================================================

class ItemIn(BaseModel):
    title: str
    description: str = ""
    issuer: str = ""
    provider: str = ""
    url: str = ""


# ============================================================
# OPPORTUNITY REQUIREMENTS
# ============================================================

class RequirementIn(BaseModel):
    skill_id: int
    required_level: int = Field(ge=0, le=100)


# ============================================================
# INDUSTRY OPPORTUNITIES
# ============================================================

class OpportunityIn(BaseModel):
    title: str
    description: str = ""
    opportunity_type: str = "Internship"
    location: str = "Remote"
    requirements: list[RequirementIn] = Field(default_factory=list)


class ApplicationStatusIn(BaseModel):
    status: str


# ============================================================
# INDUSTRY LEARNING PROGRAMS
# ============================================================

class LearningProgramSkillIn(BaseModel):
    skill_id: int


class LearningProgramIn(BaseModel):
    """
    Industry-published learning opportunity.

    Supported program types:
        Training
        Certification
        Workshop
        Mentorship
    """

    title: str = Field(min_length=1, max_length=255)

    description: str = ""

    program_type: str = "Training"

    # AYUSH domain focus.
    ayush_focus: str = ""

    # Example:
    # "4 weeks", "6 sessions", "2 months"
    duration: str = ""

    # On-site / Hybrid / Remote
    delivery_mode: str = "Remote"

    # Who can participate.
    eligibility: str = ""

    # Skills covered by the program.
    skills: list[LearningProgramSkillIn] = Field(default_factory=list)

    # Optional registration/application deadline.
    registration_deadline: Optional[str] = None

    # Whether the organisation provides a completion certificate.
    certificate_available: bool = False

    # External registration or learning-resource link.
    registration_url: str = ""


class LearningProgramOut(BaseModel):
    id: int
    owner_id: int

    title: str
    description: str

    program_type: str
    ayush_focus: str
    duration: str
    delivery_mode: str
    eligibility: str

    registration_deadline: Optional[str] = None

    certificate_available: bool
    registration_url: str

    status: str

    skills: list[LearningProgramSkillIn] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# LEARNING PROGRAM ENROLLMENT
# ============================================================

class LearningProgramEnrollmentIn(BaseModel):
    learning_program_id: int


class LearningProgramEnrollmentStatusIn(BaseModel):
    status: str


class LearningProgramEnrollmentOut(BaseModel):
    id: int
    learning_program_id: int
    student_id: int

    status: str

    enrolled_at: Optional[str] = None
    completed_at: Optional[str] = None

    certificate_url: str = ""

    model_config = ConfigDict(from_attributes=True)