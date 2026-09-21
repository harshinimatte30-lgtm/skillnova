from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import Table, Column, Integer, String, DateTime, Text

from .db import Base, engine, get_db, settings
from .models import (
    User,
    Profile,
    Skill,
    StudentSkill,
    Evidence,
    Project,
    Certificate,
    Course,
    Role,
    RoleSkillRequirement,
    Opportunity,
    OpportunitySkillRequirement,
    OpportunityEligibility,
    StudentAcademicRecord,
    Application,
    AssessmentAttempt,
    SkillAssessmentResult,
    LearningProgram,
    LearningProgramSkill,
    LearningProgramEnrollment,
    InternshipRecord,
    InternshipMilestone,
    InternshipFeedback,
    FacultyOpportunity,
    FacultyOpportunitySkill,
    FacultyOpportunityApplication,
    Collaboration,
    CollaborationMilestone,
    CollaborationFeedback,
    CollaborationOutput,
    StudentDocument,
)
from .schemas import (
    RegisterIn,
    LoginIn,
    UserOut,
    ProfileIn,
    SkillIn,
    EvidenceIn,
    ItemIn,
    OpportunityIn,
    ApplicationStatusIn,
    LearningProgramIn,
    LearningProgramOut,
    LearningProgramEnrollmentIn,
    LearningProgramEnrollmentStatusIn,
    LearningProgramEnrollmentOut,
)
from .security import (
    hash_password,
    verify_password,
    create_token,
)

from .student.assessment import router as student_assessment_router




class StudentDocumentIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    document_type: str = "Certificate"
    description: str = ""
    issuer: str = ""
    issued_on: str = ""
    url: str = ""
    visibility: str = "Academician"
    linked_internship_id: int | None = None
    linked_collaboration_id: int | None = None


class StudentDocumentUpdateIn(BaseModel):
    title: str | None = None
    document_type: str | None = None
    description: str | None = None
    issuer: str | None = None
    issued_on: str | None = None
    url: str | None = None
    visibility: str | None = None
    linked_internship_id: int | None = None
    linked_collaboration_id: int | None = None


class StudentDocumentVerificationIn(BaseModel):
    status: str
    reason: str = ""


class FacultyOpportunityIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    opportunity_type: str = "Collaborative Research"
    ayush_focus: str = "AYUSH"
    location: str = "Remote"
    delivery_mode: str = "Hybrid"
    duration: str = ""
    eligibility: str = ""
    registration_url: str = ""
    skills: list[int] = Field(default_factory=list)


class FacultyOpportunityApplicationIn(BaseModel):
    message: str = ""


class FacultyOpportunityApplicationStatusIn(BaseModel):
    status: str


# ============================================================
# INTERNSHIP LIFECYCLE SCHEMAS
# ============================================================

class InternshipUpdateIn(BaseModel):
    status: str | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    mentor_name: str | None = None
    mentor_email: str | None = None
    start_date: str | None = None
    expected_end_date: str | None = None
    actual_end_date: str | None = None
    summary: str | None = None
    certificate_url: str | None = None
    report_url: str | None = None


class InternshipMilestoneIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    due_date: str | None = None


class InternshipMilestoneUpdateIn(BaseModel):
    status: str


class InternshipFeedbackIn(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    feedback: str = ""


app = FastAPI(title="SkillNova API")


# Persistent company verification requests. This lives in the same database as
# the rest of SkillNova, so verification status survives server restarts.
company_verification_requests = Table(
    "company_verification_requests",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, nullable=False, unique=True),
    Column("status", String(40), nullable=False, default="Not Submitted"),
    Column("submitted_at", DateTime, nullable=True),
    Column("reviewed_at", DateTime, nullable=True),
    Column("reviewer_id", Integer, nullable=True),
    Column("notes", Text, nullable=False, default=""),
)

app.include_router(student_assessment_router)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    settings.frontend_origin,
    "http://localhost:5173",
    "http://localhost:5174",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROLE SKILL TAXONOMY
#
# category:
#   Core
#   Recommended
#   Alternative
#   Advanced/Optional
#
# ONLY CORE SKILLS are used for readiness and skill-gap graph.
# ============================================================

# ============================================================
# AYUSH ROLE + SKILL TAXONOMY
#
# SkillNova demo taxonomy for AYUSH academia-industry
# collaboration, skill assessment and opportunity matching.
#
# These are demo competency profiles, not official
# Ministry of Ayush competency standards.
#
# Categories:
#   Core
#   Recommended
#   Alternative
#   Advanced/Optional
#
# ONLY CORE SKILLS are used for readiness and skill-gap graph.
# ============================================================

SEED_ROLES = {

    # ========================================================
    # AYURVEDA
    # ========================================================

    "Ayurveda Research Assistant": [
        ("Ayurveda Fundamentals", 85, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Literature Review", 80, "Core", None),
        ("Scientific Writing", 80, "Core", None),
        ("Data Analysis", 70, "Core", None),

        ("Ayurvedic Pharmacology", 70, "Recommended", None),
        ("Clinical Research", 70, "Recommended", None),
        ("Statistics", 70, "Recommended", None),
        ("Research Ethics", 75, "Recommended", None),
        ("Documentation", 75, "Recommended", None),

        ("Excel", 70, "Alternative", "Data Analysis"),
        ("Python", 60, "Alternative", "Data Analysis"),

        ("Evidence Synthesis", 70, "Advanced/Optional", None),
        ("Systematic Review", 65, "Advanced/Optional", None),
    ],

    "Ayurveda Clinical Research Associate": [
        ("Ayurveda Fundamentals", 85, "Core", None),
        ("Clinical Research", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Research Ethics", 85, "Core", None),
        ("Clinical Documentation", 85, "Core", None),

        ("Good Clinical Practice", 80, "Recommended", None),
        ("Biostatistics", 75, "Recommended", None),
        ("Pharmacovigilance", 70, "Recommended", None),
        ("Data Management", 70, "Recommended", None),
        ("Scientific Writing", 75, "Recommended", None),

        ("Epidemiology", 70, "Alternative", "Biostatistics"),
        ("Statistics", 70, "Alternative", "Biostatistics"),

        ("Clinical Trial Coordination", 75, "Advanced/Optional", None),
        ("Evidence Synthesis", 65, "Advanced/Optional", None),
    ],

    "Ayurveda Drug Development Associate": [
        ("Ayurveda Fundamentals", 80, "Core", None),
        ("Drug Development", 90, "Core", None),
        ("Formulation Development", 85, "Core", None),
        ("Quality Control", 85, "Core", None),
        ("Research Methodology", 75, "Core", None),

        ("Pharmacognosy", 75, "Recommended", None),
        ("Phytochemistry", 75, "Recommended", None),
        ("Pharmacology", 70, "Recommended", None),
        ("Toxicology", 70, "Recommended", None),
        ("Scientific Writing", 65, "Recommended", None),

        ("Ayurvedic Pharmacology", 70, "Alternative", "Pharmacology"),
        ("Quality Assurance", 75, "Alternative", "Quality Control"),

        ("Preclinical Research", 75, "Advanced/Optional", None),
        ("Product Development", 75, "Advanced/Optional", None),
    ],

    "Ayurveda Pharmacognosy Research Associate": [
        ("Ayurveda Fundamentals", 75, "Core", None),
        ("Pharmacognosy", 90, "Core", None),
        ("Medicinal Plant Identification", 90, "Core", None),
        ("Research Methodology", 80, "Core", None),
        ("Scientific Documentation", 80, "Core", None),

        ("Phytochemistry", 80, "Recommended", None),
        ("Botany", 75, "Recommended", None),
        ("Medicinal Plant Survey", 80, "Recommended", None),
        ("Plant Authentication", 80, "Recommended", None),
        ("Data Analysis", 65, "Recommended", None),

        ("Herbal Garden Management", 65, "Alternative", "Medicinal Plant Survey"),
        ("Biodiversity Documentation", 65, "Alternative", "Medicinal Plant Survey"),

        ("Ethnobotany", 75, "Advanced/Optional", None),
        ("Plant Tissue Culture", 65, "Advanced/Optional", None),
    ],

    "Ayurveda Pharmacology Research Associate": [
        ("Ayurveda Fundamentals", 75, "Core", None),
        ("Pharmacology", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Preclinical Research", 85, "Core", None),
        ("Data Analysis", 75, "Core", None),

        ("Toxicology", 80, "Recommended", None),
        ("Biostatistics", 70, "Recommended", None),
        ("Ayurvedic Pharmacology", 80, "Recommended", None),
        ("Scientific Writing", 70, "Recommended", None),
        ("Research Ethics", 70, "Recommended", None),

        ("Biochemistry", 70, "Alternative", "Pharmacology"),
        ("Molecular Biology", 70, "Alternative", "Pharmacology"),

        ("Mechanistic Research", 75, "Advanced/Optional", None),
        ("Network Pharmacology", 70, "Advanced/Optional", None),
    ],

    "Ayurveda Quality & Standardization Associate": [
        ("Ayurveda Fundamentals", 75, "Core", None),
        ("Quality Control", 90, "Core", None),
        ("Drug Standardization", 90, "Core", None),
        ("Documentation", 85, "Core", None),
        ("Quality Assurance", 85, "Core", None),

        ("Pharmacognosy", 75, "Recommended", None),
        ("Phytochemistry", 75, "Recommended", None),
        ("Analytical Methods", 75, "Recommended", None),
        ("Good Manufacturing Practice", 80, "Recommended", None),
        ("Scientific Writing", 65, "Recommended", None),

        ("Regulatory Compliance", 75, "Alternative", "Quality Assurance"),
        ("Laboratory Documentation", 75, "Alternative", "Documentation"),

        ("Stability Studies", 70, "Advanced/Optional", None),
        ("Method Validation", 70, "Advanced/Optional", None),
    ],

    "Ayurveda Medicinal Plant Research Associate": [
        ("Ayurveda Fundamentals", 75, "Core", None),
        ("Medicinal Plant Identification", 90, "Core", None),
        ("Medicinal Plant Research", 90, "Core", None),
        ("Research Methodology", 80, "Core", None),
        ("Scientific Documentation", 80, "Core", None),

        ("Pharmacognosy", 80, "Recommended", None),
        ("Botany", 75, "Recommended", None),
        ("Ethnobotany", 75, "Recommended", None),
        ("Plant Authentication", 80, "Recommended", None),
        ("Data Analysis", 65, "Recommended", None),

        ("Biodiversity Documentation", 70, "Alternative", "Scientific Documentation"),
        ("Medicinal Plant Survey", 80, "Alternative", "Medicinal Plant Research"),

        ("Herbal Cultivation", 70, "Advanced/Optional", None),
        ("Conservation Research", 70, "Advanced/Optional", None),
    ],

    "Ayurveda Literary Research & Documentation Associate": [
        ("Ayurveda Fundamentals", 80, "Core", None),
        ("Literary Research", 90, "Core", None),
        ("Documentation", 90, "Core", None),
        ("Literature Review", 85, "Core", None),
        ("Scientific Writing", 85, "Core", None),

        ("Classical Text Analysis", 85, "Recommended", None),
        ("Manuscript Documentation", 80, "Recommended", None),
        ("Digital Humanities", 65, "Recommended", None),
        ("Research Methodology", 70, "Recommended", None),
        ("Translation Skills", 70, "Recommended", None),

        ("Sanskrit", 70, "Alternative", "Translation Skills"),
        ("English Academic Writing", 75, "Alternative", "Scientific Writing"),

        ("AYUSH Informatics", 70, "Advanced/Optional", None),
        ("Medical History", 75, "Advanced/Optional", None),
    ],

    # ========================================================
    # AYUSH CLINICAL / DATA / PUBLIC HEALTH
    # ========================================================

    "AYUSH Clinical Documentation Associate": [
        ("AYUSH Systems Overview", 80, "Core", None),
        ("Clinical Documentation", 90, "Core", None),
        ("Data Management", 85, "Core", None),
        ("Documentation", 90, "Core", None),
        ("Research Ethics", 80, "Core", None),

        ("Clinical Research", 75, "Recommended", None),
        ("Medical Terminology", 75, "Recommended", None),
        ("Data Quality", 80, "Recommended", None),
        ("Scientific Writing", 70, "Recommended", None),
        ("Digital Health Records", 70, "Recommended", None),

        ("Excel", 70, "Alternative", "Data Management"),
        ("Database Fundamentals", 65, "Alternative", "Data Management"),

        ("AYUSH Informatics", 70, "Advanced/Optional", None),
        ("Health Information Management", 70, "Advanced/Optional", None),
    ],

    "AYUSH Clinical Data Associate": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("Clinical Data Management", 90, "Core", None),
        ("Data Analysis", 85, "Core", None),
        ("Research Methodology", 80, "Core", None),
        ("Data Quality", 85, "Core", None),

        ("Biostatistics", 80, "Recommended", None),
        ("Clinical Research", 75, "Recommended", None),
        ("Database Fundamentals", 75, "Recommended", None),
        ("Excel", 75, "Recommended", None),
        ("Research Ethics", 75, "Recommended", None),

        ("Python", 65, "Alternative", "Data Analysis"),
        ("R", 65, "Alternative", "Data Analysis"),

        ("Epidemiology", 75, "Advanced/Optional", None),
        ("Health Informatics", 70, "Advanced/Optional", None),
    ],

    "AYUSH Research Data Analyst": [
        ("AYUSH Systems Overview", 70, "Core", None),
        ("Data Analysis", 90, "Core", None),
        ("Statistics", 90, "Core", None),
        ("Research Methodology", 80, "Core", None),
        ("Scientific Writing", 75, "Core", None),

        ("Python", 75, "Recommended", None),
        ("Excel", 80, "Recommended", None),
        ("Data Visualization", 75, "Recommended", None),
        ("Biostatistics", 80, "Recommended", None),
        ("Research Ethics", 70, "Recommended", None),

        ("R", 75, "Alternative", "Python"),
        ("SQL", 65, "Alternative", "Data Analysis"),

        ("Machine Learning", 65, "Advanced/Optional", None),
        ("Epidemiology", 75, "Advanced/Optional", None),
    ],

    "AYUSH Public Health & Epidemiology Associate": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("Public Health", 90, "Core", None),
        ("Epidemiology", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Data Analysis", 80, "Core", None),

        ("Biostatistics", 80, "Recommended", None),
        ("Community Health", 85, "Recommended", None),
        ("Health Survey Methods", 80, "Recommended", None),
        ("Scientific Writing", 70, "Recommended", None),
        ("Research Ethics", 80, "Recommended", None),

        ("Statistics", 75, "Alternative", "Biostatistics"),
        ("Excel", 70, "Alternative", "Data Analysis"),

        ("Health Policy", 70, "Advanced/Optional", None),
        ("Implementation Research", 70, "Advanced/Optional", None),
    ],

    "AYUSH Pharmacovigilance Associate": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("Pharmacovigilance", 90, "Core", None),
        ("Drug Safety", 90, "Core", None),
        ("Clinical Documentation", 80, "Core", None),
        ("Data Management", 80, "Core", None),

        ("Clinical Research", 75, "Recommended", None),
        ("Adverse Event Reporting", 85, "Recommended", None),
        ("Research Ethics", 80, "Recommended", None),
        ("Scientific Writing", 70, "Recommended", None),
        ("Data Analysis", 70, "Recommended", None),

        ("Statistics", 70, "Alternative", "Data Analysis"),
        ("Biostatistics", 70, "Alternative", "Data Analysis"),

        ("Risk Assessment", 75, "Advanced/Optional", None),
        ("Safety Signal Detection", 70, "Advanced/Optional", None),
    ],

    # ========================================================
    # AYUSH PRODUCT / INDUSTRY
    # ========================================================

    "AYUSH Product Development Associate": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("Product Development", 90, "Core", None),
        ("Formulation Development", 90, "Core", None),
        ("Quality Control", 80, "Core", None),
        ("Research Methodology", 75, "Core", None),

        ("Drug Standardization", 80, "Recommended", None),
        ("Pharmacognosy", 70, "Recommended", None),
        ("Phytochemistry", 70, "Recommended", None),
        ("Good Manufacturing Practice", 80, "Recommended", None),
        ("Scientific Documentation", 75, "Recommended", None),

        ("Quality Assurance", 80, "Alternative", "Quality Control"),
        ("Regulatory Compliance", 70, "Alternative", "Quality Control"),

        ("Stability Studies", 70, "Advanced/Optional", None),
        ("Technology Transfer", 70, "Advanced/Optional", None),
    ],

    "AYUSH Quality Control Associate": [
        ("AYUSH Systems Overview", 70, "Core", None),
        ("Quality Control", 90, "Core", None),
        ("Analytical Methods", 90, "Core", None),
        ("Drug Standardization", 85, "Core", None),
        ("Laboratory Documentation", 85, "Core", None),

        ("Pharmacognosy", 75, "Recommended", None),
        ("Phytochemistry", 80, "Recommended", None),
        ("Quality Assurance", 80, "Recommended", None),
        ("Good Manufacturing Practice", 80, "Recommended", None),
        ("Method Validation", 75, "Recommended", None),

        ("Regulatory Compliance", 70, "Alternative", "Quality Assurance"),
        ("Scientific Documentation", 75, "Alternative", "Laboratory Documentation"),

        ("Stability Studies", 75, "Advanced/Optional", None),
        ("Instrumental Analysis", 75, "Advanced/Optional", None),
    ],

    "AYUSH Regulatory & Compliance Associate": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("Regulatory Compliance", 90, "Core", None),
        ("Documentation", 90, "Core", None),
        ("Drug Standardization", 75, "Core", None),
        ("Quality Assurance", 80, "Core", None),

        ("Good Manufacturing Practice", 85, "Recommended", None),
        ("Quality Control", 75, "Recommended", None),
        ("Scientific Writing", 70, "Recommended", None),
        ("Research Ethics", 75, "Recommended", None),
        ("Product Development", 65, "Recommended", None),

        ("Regulatory Documentation", 85, "Alternative", "Documentation"),
        ("Laboratory Documentation", 70, "Alternative", "Documentation"),

        ("Intellectual Property Awareness", 70, "Advanced/Optional", None),
        ("Technology Transfer", 65, "Advanced/Optional", None),
    ],

    "AYUSH Research Project Coordinator": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("Research Project Management", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Documentation", 90, "Core", None),
        ("Scientific Communication", 80, "Core", None),

        ("Clinical Research", 70, "Recommended", None),
        ("Data Management", 75, "Recommended", None),
        ("Research Ethics", 80, "Recommended", None),
        ("Scientific Writing", 75, "Recommended", None),
        ("Stakeholder Management", 80, "Recommended", None),

        ("Project Management", 80, "Alternative", "Research Project Management"),
        ("Excel", 70, "Alternative", "Data Management"),

        ("Grant Writing", 70, "Advanced/Optional", None),
        ("Research Funding", 65, "Advanced/Optional", None),
    ],

    # ========================================================
    # MICROBIOLOGY / BIOTECH / FUNDAMENTAL RESEARCH
    # ========================================================

    "AYUSH Microbiology Research Associate": [
        ("AYUSH Systems Overview", 70, "Core", None),
        ("Microbiology", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Laboratory Techniques", 90, "Core", None),
        ("Data Analysis", 70, "Core", None),

        ("Biochemistry", 80, "Recommended", None),
        ("Molecular Biology", 75, "Recommended", None),
        ("Scientific Writing", 75, "Recommended", None),
        ("Research Ethics", 75, "Recommended", None),
        ("Quality Control", 70, "Recommended", None),

        ("Biotechnology", 80, "Alternative", "Molecular Biology"),
        ("Phytochemistry", 65, "Alternative", "Biochemistry"),

        ("Microbial Biotechnology", 75, "Advanced/Optional", None),
        ("Molecular Diagnostics", 70, "Advanced/Optional", None),
    ],

    "AYUSH Biotechnology Research Associate": [
        ("AYUSH Systems Overview", 65, "Core", None),
        ("Biotechnology", 90, "Core", None),
        ("Molecular Biology", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Data Analysis", 75, "Core", None),

        ("Biochemistry", 80, "Recommended", None),
        ("Microbiology", 80, "Recommended", None),
        ("Scientific Writing", 75, "Recommended", None),
        ("Research Ethics", 75, "Recommended", None),
        ("Laboratory Techniques", 80, "Recommended", None),

        ("Bioinformatics", 70, "Alternative", "Data Analysis"),
        ("Statistics", 70, "Alternative", "Data Analysis"),

        ("Network Pharmacology", 70, "Advanced/Optional", None),
        ("Molecular Modeling", 65, "Advanced/Optional", None),
    ],

    "AYUSH Fundamental Research Associate": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("Fundamental Research", 90, "Core", None),
        ("Research Methodology", 90, "Core", None),
        ("Scientific Writing", 85, "Core", None),
        ("Data Analysis", 75, "Core", None),

        ("Biochemistry", 75, "Recommended", None),
        ("Molecular Biology", 75, "Recommended", None),
        ("Statistics", 75, "Recommended", None),
        ("Research Ethics", 80, "Recommended", None),
        ("Literature Review", 80, "Recommended", None),

        ("Bioinformatics", 70, "Alternative", "Data Analysis"),
        ("Biotechnology", 70, "Alternative", "Fundamental Research"),

        ("Systems Biology", 70, "Advanced/Optional", None),
        ("Network Pharmacology", 70, "Advanced/Optional", None),
    ],

    # ========================================================
    # OTHER AYUSH SYSTEMS
    # ========================================================

    "Yoga & Naturopathy Research Associate": [
        ("Yoga & Naturopathy Fundamentals", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Clinical Research", 80, "Core", None),
        ("Public Health", 75, "Core", None),
        ("Scientific Writing", 75, "Core", None),

        ("Health Promotion", 85, "Recommended", None),
        ("Lifestyle Research", 80, "Recommended", None),
        ("Statistics", 70, "Recommended", None),
        ("Research Ethics", 80, "Recommended", None),
        ("Data Analysis", 65, "Recommended", None),

        ("Biostatistics", 70, "Alternative", "Statistics"),
        ("Community Health", 75, "Alternative", "Public Health"),

        ("Mind-Body Research", 75, "Advanced/Optional", None),
        ("Preventive Health Research", 75, "Advanced/Optional", None),
    ],

    "Siddha Research Associate": [
        ("Siddha Fundamentals", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Literature Review", 80, "Core", None),
        ("Scientific Writing", 80, "Core", None),
        ("Data Analysis", 70, "Core", None),

        ("Clinical Research", 75, "Recommended", None),
        ("Medicinal Plant Research", 75, "Recommended", None),
        ("Drug Standardization", 75, "Recommended", None),
        ("Research Ethics", 80, "Recommended", None),
        ("Documentation", 75, "Recommended", None),

        ("Statistics", 70, "Alternative", "Data Analysis"),
        ("Biostatistics", 70, "Alternative", "Data Analysis"),

        ("Pharmacognosy", 75, "Advanced/Optional", None),
        ("Pharmacology", 70, "Advanced/Optional", None),
    ],

    "Unani Research Associate": [
        ("Unani Fundamentals", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Literature Review", 80, "Core", None),
        ("Scientific Writing", 80, "Core", None),
        ("Data Analysis", 70, "Core", None),

        ("Clinical Research", 75, "Recommended", None),
        ("Medicinal Plant Research", 75, "Recommended", None),
        ("Drug Standardization", 75, "Recommended", None),
        ("Research Ethics", 80, "Recommended", None),
        ("Documentation", 75, "Recommended", None),

        ("Statistics", 70, "Alternative", "Data Analysis"),
        ("Biostatistics", 70, "Alternative", "Data Analysis"),

        ("Pharmacognosy", 75, "Advanced/Optional", None),
        ("Pharmacology", 70, "Advanced/Optional", None),
    ],

    "Homoeopathy Research Associate": [
        ("Homoeopathy Fundamentals", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Clinical Research", 80, "Core", None),
        ("Scientific Writing", 80, "Core", None),
        ("Data Analysis", 70, "Core", None),

        ("Evidence Synthesis", 75, "Recommended", None),
        ("Research Ethics", 80, "Recommended", None),
        ("Documentation", 75, "Recommended", None),
        ("Statistics", 70, "Recommended", None),
        ("Literature Review", 80, "Recommended", None),

        ("Biostatistics", 70, "Alternative", "Statistics"),
        ("Public Health", 65, "Alternative", "Clinical Research"),

        ("Systematic Review", 70, "Advanced/Optional", None),
        ("Clinical Data Management", 65, "Advanced/Optional", None),
    ],

    "Sowa-Rigpa Research Associate": [
        ("Sowa-Rigpa Fundamentals", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Clinical Research", 80, "Core", None),
        ("Medicinal Plant Research", 80, "Core", None),
        ("Scientific Writing", 75, "Core", None),

        ("Public Health", 70, "Recommended", None),
        ("Literature Review", 80, "Recommended", None),
        ("Research Ethics", 80, "Recommended", None),
        ("Documentation", 80, "Recommended", None),
        ("Data Analysis", 65, "Recommended", None),

        ("Statistics", 70, "Alternative", "Data Analysis"),
        ("Ethnobotany", 70, "Alternative", "Medicinal Plant Research"),

        ("Trans-Himalayan Medicinal Plants", 80, "Advanced/Optional", None),
        ("Traditional Medicine Documentation", 75, "Advanced/Optional", None),
    ],

    # ========================================================
    # CROSS-AYUSH DIGITAL / KNOWLEDGE ROLES
    # ========================================================

    "AYUSH Evidence Synthesis & Scientific Writing Associate": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("Evidence Synthesis", 90, "Core", None),
        ("Literature Review", 90, "Core", None),
        ("Scientific Writing", 90, "Core", None),
        ("Research Methodology", 85, "Core", None),

        ("Systematic Review", 85, "Recommended", None),
        ("Meta-analysis", 70, "Recommended", None),
        ("Statistics", 70, "Recommended", None),
        ("Research Ethics", 75, "Recommended", None),
        ("Documentation", 80, "Recommended", None),

        ("Biostatistics", 70, "Alternative", "Statistics"),
        ("Data Analysis", 70, "Alternative", "Statistics"),

        ("Academic Publishing", 80, "Advanced/Optional", None),
        ("Research Protocol Development", 75, "Advanced/Optional", None),
    ],

    "AYUSH Health Informatics Associate": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("Health Informatics", 90, "Core", None),
        ("Data Management", 85, "Core", None),
        ("Data Analysis", 80, "Core", None),
        ("Documentation", 80, "Core", None),

        ("Digital Health Records", 80, "Recommended", None),
        ("Database Fundamentals", 75, "Recommended", None),
        ("Health Data Standards", 70, "Recommended", None),
        ("AYUSH Informatics", 80, "Recommended", None),
        ("Data Quality", 80, "Recommended", None),

        ("SQL", 75, "Alternative", "Database Fundamentals"),
        ("Python", 70, "Alternative", "Data Analysis"),

        ("Clinical Decision Support", 70, "Advanced/Optional", None),
        ("Interoperability", 70, "Advanced/Optional", None),
    ],

    "AYUSH Digital Knowledge & Research Portal Associate": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("AYUSH Informatics", 90, "Core", None),
        ("Documentation", 90, "Core", None),
        ("Literary Research", 80, "Core", None),
        ("Digital Content Management", 85, "Core", None),

        ("Research Methodology", 70, "Recommended", None),
        ("Scientific Writing", 75, "Recommended", None),
        ("Data Management", 75, "Recommended", None),
        ("Metadata Management", 75, "Recommended", None),
        ("Digital Humanities", 70, "Recommended", None),

        ("Database Fundamentals", 70, "Alternative", "Data Management"),
        ("Web Content Management", 70, "Alternative", "Digital Content Management"),

        ("AYUSH Research Portal Management", 75, "Advanced/Optional", None),
        ("Digital Preservation", 75, "Advanced/Optional", None),
    ],

    "AYUSH Nutrition & Wellness Research Associate": [
        ("AYUSH Systems Overview", 75, "Core", None),
        ("Nutrition & Wellness", 90, "Core", None),
        ("Research Methodology", 80, "Core", None),
        ("Public Health", 75, "Core", None),
        ("Data Analysis", 65, "Core", None),

        ("Health Promotion", 85, "Recommended", None),
        ("Lifestyle Research", 80, "Recommended", None),
        ("Community Health", 75, "Recommended", None),
        ("Scientific Writing", 70, "Recommended", None),
        ("Research Ethics", 75, "Recommended", None),

        ("Statistics", 65, "Alternative", "Data Analysis"),
        ("Biostatistics", 65, "Alternative", "Data Analysis"),

        ("Preventive Health Research", 75, "Advanced/Optional", None),
        ("Health Behaviour Research", 70, "Advanced/Optional", None),
    ],

    "AYUSH Education & Training Content Associate": [
        ("AYUSH Systems Overview", 85, "Core", None),
        ("Scientific Communication", 90, "Core", None),
        ("Educational Content Development", 90, "Core", None),
        ("Documentation", 80, "Core", None),
        ("Scientific Writing", 85, "Core", None),

        ("Digital Content Management", 80, "Recommended", None),
        ("Literature Review", 75, "Recommended", None),
        ("Research Methodology", 65, "Recommended", None),
        ("Presentation Skills", 80, "Recommended", None),
        ("Instructional Design", 75, "Recommended", None),

        ("Video Content Development", 65, "Alternative", "Digital Content Management"),
        ("Technical Writing", 75, "Alternative", "Scientific Writing"),

        ("E-Learning Development", 75, "Advanced/Optional", None),
        ("AYUSH Informatics", 70, "Advanced/Optional", None),
    ],

    "AYUSH Medicinal Plant Survey Associate": [
        ("AYUSH Systems Overview", 70, "Core", None),
        ("Medicinal Plant Survey", 90, "Core", None),
        ("Medicinal Plant Identification", 90, "Core", None),
        ("Ethnobotany", 85, "Core", None),
        ("Field Documentation", 90, "Core", None),

        ("Pharmacognosy", 80, "Recommended", None),
        ("Botany", 80, "Recommended", None),
        ("Biodiversity Documentation", 80, "Recommended", None),
        ("Research Methodology", 75, "Recommended", None),
        ("Data Collection", 80, "Recommended", None),

        ("Geographic Information Systems", 65, "Alternative", "Field Documentation"),
        ("Digital Mapping", 65, "Alternative", "Field Documentation"),

        ("Herbal Cultivation", 70, "Advanced/Optional", None),
        ("Conservation Research", 75, "Advanced/Optional", None),
    ],

    "AYUSH Community Health Research Associate": [
        ("AYUSH Systems Overview", 80, "Core", None),
        ("Community Health", 90, "Core", None),
        ("Public Health", 85, "Core", None),
        ("Research Methodology", 85, "Core", None),
        ("Data Collection", 85, "Core", None),

        ("Epidemiology", 75, "Recommended", None),
        ("Health Survey Methods", 80, "Recommended", None),
        ("Data Analysis", 70, "Recommended", None),
        ("Research Ethics", 85, "Recommended", None),
        ("Scientific Writing", 70, "Recommended", None),

        ("Statistics", 70, "Alternative", "Data Analysis"),
        ("Biostatistics", 70, "Alternative", "Data Analysis"),

        ("Health Promotion", 80, "Advanced/Optional", None),
        ("Implementation Research", 70, "Advanced/Optional", None),
    ],

    "AYUSH Traditional Knowledge Documentation Associate": [
        ("AYUSH Systems Overview", 85, "Core", None),
        ("Traditional Knowledge Documentation", 90, "Core", None),
        ("Literary Research", 85, "Core", None),
        ("Field Documentation", 85, "Core", None),
        ("Scientific Writing", 80, "Core", None),

        ("Ethnobotany", 75, "Recommended", None),
        ("Manuscript Documentation", 80, "Recommended", None),
        ("Literature Review", 80, "Recommended", None),
        ("Research Ethics", 85, "Recommended", None),
        ("Digital Preservation", 70, "Recommended", None),

        ("Medical History", 75, "Alternative", "Literary Research"),
        ("Documentation", 80, "Alternative", "Field Documentation"),

        ("AYUSH Informatics", 70, "Advanced/Optional", None),
        ("Intellectual Property Awareness", 65, "Advanced/Optional", None),
    ],
}


# ============================================================
# AYUSH SKILL MASTER LIST
# ============================================================

SEED_SKILLS = [

    # --------------------------------------------------------
    # AYUSH SYSTEM KNOWLEDGE
    # --------------------------------------------------------

    ("AYUSH Systems Overview", "AYUSH"),
    ("Ayurveda Fundamentals", "Ayurveda"),
    ("Ayurvedic Pharmacology", "Ayurveda"),
    ("Yoga & Naturopathy Fundamentals", "Yoga & Naturopathy"),
    ("Siddha Fundamentals", "Siddha"),
    ("Unani Fundamentals", "Unani"),
    ("Homoeopathy Fundamentals", "Homoeopathy"),
    ("Sowa-Rigpa Fundamentals", "Sowa-Rigpa"),

    # --------------------------------------------------------
    # RESEARCH
    # --------------------------------------------------------

    ("Research Methodology", "Research"),
    ("Clinical Research", "Research"),
    ("Research Ethics", "Research"),
    ("Research Project Management", "Research"),
    ("Research Protocol Development", "Research"),
    ("Evidence Synthesis", "Research"),
    ("Systematic Review", "Research"),
    ("Meta-analysis", "Research"),
    ("Literature Review", "Research"),
    ("Literary Research", "Research"),
    ("Fundamental Research", "Research"),
    ("Preclinical Research", "Research"),
    ("Implementation Research", "Research"),
    ("Grant Writing", "Research"),
    ("Research Funding", "Research"),
    ("Research Data Collection", "Research"),

    # --------------------------------------------------------
    # SCIENTIFIC COMMUNICATION / DOCUMENTATION
    # --------------------------------------------------------

    ("Scientific Writing", "Scientific Communication"),
    ("Scientific Communication", "Scientific Communication"),
    ("Documentation", "Documentation"),
    ("Scientific Documentation", "Documentation"),
    ("Clinical Documentation", "Documentation"),
    ("Laboratory Documentation", "Documentation"),
    ("Regulatory Documentation", "Documentation"),
    ("Field Documentation", "Documentation"),
    ("Manuscript Documentation", "Documentation"),
    ("Technical Writing", "Scientific Communication"),
    ("Presentation Skills", "Soft Skills"),

    # --------------------------------------------------------
    # CLINICAL / HEALTH RESEARCH
    # --------------------------------------------------------

    ("Good Clinical Practice", "Clinical Research"),
    ("Clinical Trial Coordination", "Clinical Research"),
    ("Clinical Data Management", "Clinical Research"),
    ("Clinical Decision Support", "Health Informatics"),
    ("Medical Terminology", "Clinical Research"),
    ("Pharmacovigilance", "Drug Safety"),
    ("Drug Safety", "Drug Safety"),
    ("Adverse Event Reporting", "Drug Safety"),
    ("Risk Assessment", "Drug Safety"),
    ("Safety Signal Detection", "Drug Safety"),

    # --------------------------------------------------------
    # DRUG / PHARMACEUTICAL RESEARCH
    # --------------------------------------------------------

    ("Drug Development", "Pharmaceutical Research"),
    ("Formulation Development", "Pharmaceutical Research"),
    ("Product Development", "Pharmaceutical Research"),
    ("Technology Transfer", "Pharmaceutical Research"),
    ("Drug Standardization", "Quality & Standardization"),
    ("Quality Control", "Quality & Standardization"),
    ("Quality Assurance", "Quality & Standardization"),
    ("Good Manufacturing Practice", "Quality & Standardization"),
    ("Analytical Methods", "Quality & Standardization"),
    ("Method Validation", "Quality & Standardization"),
    ("Stability Studies", "Quality & Standardization"),
    ("Regulatory Compliance", "Regulatory"),
    ("Laboratory Techniques", "Laboratory Research"),

    # --------------------------------------------------------
    # PHARMACOGNOSY / MEDICINAL PLANTS
    # --------------------------------------------------------

    ("Pharmacognosy", "Medicinal Plants"),
    ("Phytochemistry", "Medicinal Plants"),
    ("Medicinal Plant Research", "Medicinal Plants"),
    ("Medicinal Plant Survey", "Medicinal Plants"),
    ("Medicinal Plant Identification", "Medicinal Plants"),
    ("Plant Authentication", "Medicinal Plants"),
    ("Ethnobotany", "Medicinal Plants"),
    ("Botany", "Medicinal Plants"),
    ("Biodiversity Documentation", "Medicinal Plants"),
    ("Herbal Cultivation", "Medicinal Plants"),
    ("Conservation Research", "Medicinal Plants"),
    ("Plant Tissue Culture", "Medicinal Plants"),
    ("Trans-Himalayan Medicinal Plants", "Medicinal Plants"),

    # --------------------------------------------------------
    # PHARMACOLOGY / TOXICOLOGY / LIFE SCIENCES
    # --------------------------------------------------------

    ("Pharmacology", "Pharmacology"),
    ("Toxicology", "Pharmacology"),
    ("Mechanistic Research", "Pharmacology"),
    ("Network Pharmacology", "Pharmacology"),
    ("Biochemistry", "Life Sciences"),
    ("Molecular Biology", "Life Sciences"),
    ("Microbiology", "Life Sciences"),
    ("Biotechnology", "Life Sciences"),
    ("Microbial Biotechnology", "Life Sciences"),
    ("Molecular Diagnostics", "Life Sciences"),
    ("Systems Biology", "Life Sciences"),
    ("Bioinformatics", "Life Sciences"),
    ("Molecular Modeling", "Life Sciences"),

    # --------------------------------------------------------
    # DATA / STATISTICS
    # --------------------------------------------------------

    ("Data Analysis", "Data"),
    ("Data Management", "Data"),
    ("Data Quality", "Data"),
    ("Data Collection", "Data"),
    ("Data Visualization", "Data"),
    ("Statistics", "Data"),
    ("Biostatistics", "Data"),
    ("Epidemiology", "Public Health"),
    ("Public Health", "Public Health"),
    ("Community Health", "Public Health"),
    ("Health Promotion", "Public Health"),
    ("Health Survey Methods", "Public Health"),
    ("Lifestyle Research", "Public Health"),
    ("Preventive Health Research", "Public Health"),
    ("Health Policy", "Public Health"),
    ("Health Behaviour Research", "Public Health"),
    ("Nutrition & Wellness", "Public Health"),

    # --------------------------------------------------------
    # DIGITAL / INFORMATICS
    # --------------------------------------------------------

    ("AYUSH Informatics", "Digital Health"),
    ("Health Informatics", "Digital Health"),
    ("Digital Health Records", "Digital Health"),
    ("Health Data Standards", "Digital Health"),
    ("Database Fundamentals", "Digital Health"),
    ("Digital Content Management", "Digital Health"),
    ("Digital Humanities", "Digital Health"),
    ("Metadata Management", "Digital Health"),
    ("Digital Preservation", "Digital Health"),
    ("Web Content Management", "Digital Health"),
    ("AYUSH Research Portal Management", "Digital Health"),
    ("Interoperability", "Digital Health"),

    # --------------------------------------------------------
    # EDUCATION / CONTENT
    # --------------------------------------------------------

    ("Educational Content Development", "Education"),
    ("Instructional Design", "Education"),
    ("E-Learning Development", "Education"),
    ("Video Content Development", "Education"),

    # --------------------------------------------------------
    # SOFT SKILLS
    # --------------------------------------------------------

    ("Communication", "Soft Skills"),
    ("Teamwork", "Soft Skills"),
    ("Problem Solving", "Soft Skills"),
    ("Critical Thinking", "Soft Skills"),
    ("Scientific Reasoning", "Soft Skills"),
    ("Stakeholder Management", "Soft Skills"),
    ("Leadership", "Soft Skills"),
    ("Time Management", "Soft Skills"),
    ("Adaptability", "Soft Skills"),
    ("Professional Ethics", "Soft Skills"),

    # --------------------------------------------------------
    # APTITUDE
    # --------------------------------------------------------

    ("Quantitative Aptitude", "Aptitude"),
    ("Logical Reasoning", "Aptitude"),
    ("Research Aptitude", "Aptitude"),
    ("Data Interpretation", "Aptitude"),
    ("Analytical Reasoning", "Aptitude"),

    # --------------------------------------------------------
    # GENERAL RESEARCH / ACADEMIC SKILLS
    # --------------------------------------------------------

    ("English Academic Writing", "Academic"),
    ("Translation Skills", "Academic"),
    ("Classical Text Analysis", "Academic"),
    ("Sanskrit", "Language"),
    ("Medical History", "Academic"),
    ("Traditional Medicine Documentation", "Academic"),
    ("Intellectual Property Awareness", "Professional"),
    ("Regulatory Awareness", "Professional"),
    ("Stakeholder Communication", "Professional"),
    ("Project Management", "Professional"),
]
# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    Base.metadata.create_all(bind=engine)

    db = Session(bind=engine)

    try:
        # ----------------------------------------------------
        # Seed skills
        # ----------------------------------------------------
        for skill_name, category in SEED_SKILLS:
            skill = (
                db.query(Skill)
                .filter(Skill.name == skill_name)
                .first()
            )

            if not skill:
                db.add(
                    Skill(
                        name=skill_name,
                        category=category,
                    )
                )

        db.commit()

        # ----------------------------------------------------
        # Seed roles + taxonomy
        # ----------------------------------------------------
        for role_name, taxonomy in SEED_ROLES.items():

            role = (
                db.query(Role)
                .filter(Role.name == role_name)
                .first()
            )

            if not role:
                role = Role(
                    name=role_name,
                    description=f"Skill pathway for {role_name}.",
                )
                db.add(role)
                db.commit()
                db.refresh(role)

            # Existing requirements are rebuilt so that
            # taxonomy changes are reflected.
            db.query(RoleSkillRequirement).filter(
                RoleSkillRequirement.role_id == role.id
            ).delete(
                synchronize_session=False
            )

            for (
                skill_name,
                required_level,
                category,
                alternative_group,
            ) in taxonomy:

                skill = (
                    db.query(Skill)
                    .filter(Skill.name == skill_name)
                    .first()
                )

                if not skill:
                    skill = Skill(
                        name=skill_name,
                        category="General",
                    )
                    db.add(skill)
                    db.commit()
                    db.refresh(skill)

                db.add(
                    RoleSkillRequirement(
                        role_id=role.id,
                        skill_id=skill.id,
                        required_level=required_level,
                        category=category,
                        alternative_group=alternative_group,
                    )
                )

            db.commit()

    finally:
        db.close()


init_db()


# ============================================================
# HELPERS
# ============================================================

def get_user_from_token(token: str, db: Session):
    """
    Decode the token using the existing security layer.

    The existing create_token function is kept unchanged.
    """

    try:
        from .security import decode_token

        payload = decode_token(token)

        user_id = payload.get("sub")

        if not user_id:
            return None

        return db.query(User).filter(
            User.id == int(user_id)
        ).first()

    except Exception:
        return None

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
        )

    token = authorization.split(" ", 1)[1]

    user = get_user_from_token(token, db)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    return user


def profile_for(db: Session, user: User):
    profile = (
        db.query(Profile)
        .filter(Profile.user_id == user.id)
        .first()
    )

    if not profile:
        profile = Profile(
            user_id=user.id,
            name="",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile


def get_student_skill(
    db: Session,
    profile_id: int,
    skill_id: int,
):
    return (
        db.query(StudentSkill)
        .filter(
            StudentSkill.profile_id == profile_id,
            StudentSkill.skill_id == skill_id,
        )
        .first()
    )


def evidence_proficiency(db: Session, student_skill: StudentSkill):
    """
    Proficiency comes from assessment results.
    Evidence/academic verification is a separate status.
    """
    return max(0, min(int(student_skill.proficiency or 0), 100))


def has_evidence(
    db: Session,
    student_skill: StudentSkill,
) -> bool:
    """Return True when the student has submitted at least one evidence item."""
    return (
        db.query(Evidence)
        .filter(Evidence.student_skill_id == student_skill.id)
        .count()
        > 0
    )


def academic_review_status(
    db: Session,
    student_skill: StudentSkill,
) -> str:
    """Return the current academic review state for a student skill."""
    entries = (
        db.query(Evidence)
        .filter(Evidence.student_skill_id == student_skill.id)
        .order_by(Evidence.id.desc())
        .all()
    )
    if any((entry.kind or '').lower() == 'academic_verification' for entry in entries):
        return 'Verified'
    for entry in entries:
        kind = (entry.kind or '').lower()
        if kind == 'academic_rejected':
            return 'Rejected'
        if kind == 'needs_more_evidence':
            return 'Needs More Evidence'
        if kind not in {'academic_verification', 'academic_rejected', 'needs_more_evidence'}:
            return 'Under Review'
    return 'Pending Evidence'


def has_academic_verification(
    db: Session,
    student_skill: StudentSkill,
) -> bool:
    """Return True only after an academician/admin verification record exists."""
    return (
        db.query(Evidence)
        .filter(
            Evidence.student_skill_id == student_skill.id,
            Evidence.kind == "academic_verification",
        )
        .count()
        > 0
    )


def calculate_readiness(db: Session, profile: Profile) -> int:
    """Calculate readiness from the target role's CORE skills only."""
    role = profile.target_role
    if not role:
        return 0

    core = [r for r in role.requirements if r.category == "Core" and r.required_level > 0]
    if not core:
        return 0

    values = []
    for req in core:
        student_skill = get_student_skill(db, profile.id, req.skill_id)
        current = evidence_proficiency(db, student_skill) if student_skill else 0
        values.append(min(current / req.required_level, 1) * 100)

    return round(sum(values) / len(values)) if values else 0



def opportunity_eligibility_payload(db: Session, opportunity: Opportunity):
    record = (
        db.query(OpportunityEligibility)
        .filter(OpportunityEligibility.opportunity_id == opportunity.id)
        .first()
    )
    if not record:
        return {
            "required_education": "",
            "minimum_year": None,
            "minimum_cgpa": None,
            "eligibility_notes": "",
        }
    return {
        "required_education": record.required_education or "",
        "minimum_year": record.minimum_year,
        "minimum_cgpa": record.minimum_cgpa,
        "eligibility_notes": record.eligibility_notes or "",
    }


def get_student_cgpa(db: Session, user_id: int):
    record = (
        db.query(StudentAcademicRecord)
        .filter(StudentAcademicRecord.user_id == user_id)
        .first()
    )
    return record.cgpa if record else None


def parse_year_number(value: str) -> int | None:
    text = (value or "").strip().lower()
    for number in (4, 3, 2, 1):
        if f"{number}th year" in text or f"{number}nd year" in text or f"{number}rd year" in text or f"{number}st year" in text:
            return number
    return None


def evaluate_opportunity_eligibility(
    db: Session,
    profile: Profile,
    opportunity: Opportunity,
):
    """
    Explainable skill-based eligibility for a student and opportunity.

    Eligibility is based only on the opportunity's structured skill
    requirements. Each required skill is compared with the student's
    current assessment-derived level and its academic verification state.
    """
    comparisons = []
    matched_skills = []
    missing_skills = []
    reasons = []

    requirements = list(opportunity.requirements or [])

    for req in requirements:
        skill_name = req.skill.name if req.skill else f"Skill {req.skill_id}"
        required = max(0, int(req.required_level or 0))

        student_skill = get_student_skill(db, profile.id, req.skill_id)
        current = evidence_proficiency(db, student_skill) if student_skill else 0
        verified = (
            has_academic_verification(db, student_skill)
            if student_skill
            else False
        )

        gap = max(required - current, 0)
        meets = current >= required
        review_status = (
            academic_review_status(db, student_skill)
            if student_skill
            else "No Skill Record"
        )

        comparisons.append({
            "skill_id": req.skill_id,
            "skill": skill_name,
            "current": current,
            "required": required,
            "gap": gap,
            "meets": meets,
            "verified": verified,
            "review_status": review_status,
        })

        if meets:
            matched_skills.append(skill_name)
        else:
            missing_skills.append({
                "skill_id": req.skill_id,
                "skill": skill_name,
                "current": current,
                "required": required,
                "gap": gap,
                "verified": verified,
            })

    if not requirements:
        reasons.append("No mandatory skill requirements are configured for this opportunity.")
        eligible = True
    else:
        eligible = all(item["meets"] for item in comparisons)

        if eligible:
            reasons.append("All required skills meet the configured minimum levels.")
        else:
            reasons.append(
                f"{len(missing_skills)} required skill"
                f"{'' if len(missing_skills) == 1 else 's'} still need to be strengthened."
            )

    eligibility = (
        db.query(OpportunityEligibility)
        .filter(OpportunityEligibility.opportunity_id == opportunity.id)
        .first()
    )
    education_ok = True
    year_ok = True
    cgpa_ok = True
    academic_reasons = []

    if eligibility:
        required_education = (eligibility.required_education or "").strip()
        if required_education and required_education.lower() not in {"any", "any degree", "any education"}:
            allowed = [x.strip().lower() for x in required_education.split(",") if x.strip()]
            student_education = (profile.education or "").strip().lower()
            education_ok = any(
                student_education == item or item in student_education or student_education in item
                for item in allowed
            )
            if education_ok:
                academic_reasons.append(f"Education requirement met: {profile.education}.")
            else:
                academic_reasons.append(f"Education requirement: {required_education}.")

        if eligibility.minimum_year:
            student_year = parse_year_number(profile.year_degree or "")
            year_ok = student_year is not None and student_year >= eligibility.minimum_year
            if year_ok:
                academic_reasons.append(f"Year requirement met: {profile.year_degree}.")
            else:
                academic_reasons.append(f"Minimum academic year: {eligibility.minimum_year}.")

        if eligibility.minimum_cgpa is not None:
            cgpa = get_student_cgpa(db, profile.user_id)
            cgpa_ok = cgpa is not None and float(cgpa) >= float(eligibility.minimum_cgpa)
            if cgpa is None:
                academic_reasons.append("CGPA is not provided in the student academic record.")
            elif cgpa_ok:
                academic_reasons.append(f"CGPA requirement met: {float(cgpa):.2f}.")
            else:
                academic_reasons.append(f"Minimum CGPA: {float(eligibility.minimum_cgpa):.2f}.")

    eligible = eligible and education_ok and year_ok and cgpa_ok
    reasons.extend(academic_reasons)

    verified_skill_count = sum(
        1 for item in comparisons if item["verified"]
    )

    return {
        "eligible": eligible,
        "reasons": reasons,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_comparisons": comparisons,
        "verified_skill_count": verified_skill_count,
        "required_skill_count": len(requirements),
        "matched_skill_count": len(matched_skills),
        "academic_eligibility": {
            "education_ok": education_ok,
            "year_ok": year_ok,
            "cgpa_ok": cgpa_ok,
            "required_education": eligibility.required_education if eligibility else "",
            "minimum_year": eligibility.minimum_year if eligibility else None,
            "minimum_cgpa": eligibility.minimum_cgpa if eligibility else None,
            "student_education": profile.education or "",
            "student_year": profile.year_degree or "",
            "student_cgpa": get_student_cgpa(db, profile.user_id),
            "notes": eligibility.eligibility_notes if eligibility else "",
        },
    }

# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================================
# AUTH
# ============================================================

@app.post("/auth/register")
def register(
    data: RegisterIn,
    db: Session = Depends(get_db),
):
    role = data.role.lower()

    if role not in {
        "student",
        "company",
        "academician",
        "admin",
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    existing = (
        db.query(User)
        .filter(
            User.email == data.email.lower()
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(
        Profile(
            user_id=user.id,
            name=data.name,
        )
    )

    db.commit()

    return {
        "token": create_token(user),
        "user": UserOut(
            id=user.id,
            email=user.email,
            role=user.role,
            name=data.name,
        ),
    }


@app.post("/auth/login")
def login(
    data: LoginIn,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(
            User.email == data.email.lower()
        )
        .first()
    )

    if (
        not user
        or not verify_password(
            data.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    profile = profile_for(db, user)

    return {
        "token": create_token(user),
        "user": UserOut(
            id=user.id,
            email=user.email,
            role=user.role,
            name=profile.name,
        ),
    }


# ============================================================
# PROFILE
# ============================================================

@app.get("/profile")
def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "name": profile.name,
        "education": profile.education,
        "year_degree": profile.year_degree,
        "target_role_id": profile.target_role_id,
        "target_role": (
            profile.target_role.name
            if profile.target_role
            else None
        ),
        "career_interests": profile.career_interests,
        "research_experience": profile.research_experience,
        "achievements": profile.achievements,
    }


@app.put("/profile")
def update_profile(
    data: ProfileIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    profile.name = data.name
    profile.education = data.education
    profile.year_degree = data.year_degree
    profile.target_role_id = data.target_role_id
    profile.career_interests = data.career_interests
    profile.research_experience = data.research_experience
    profile.achievements = data.achievements

    db.commit()
    db.refresh(profile)

    return {
        "message": "Profile updated",
        "profile": {
            "id": profile.id,
            "name": profile.name,
            "education": profile.education,
            "year_degree": profile.year_degree,
            "target_role_id": profile.target_role_id,
            "target_role": (
                profile.target_role.name
                if profile.target_role
                else None
            ),
        },
    }


# ============================================================
# ROLES
# ============================================================

@app.get("/roles")
def get_roles(
    db: Session = Depends(get_db),
):
    roles = (
    db.query(Role)
    .filter(Role.name.in_(SEED_ROLES.keys()))
    .order_by(Role.name)
    .all()
    )

    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
        }
        for role in roles
    ]



@app.get("/student/career-paths")
def student_career_paths(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Build personalized AYUSH career paths from the student's current
    evidence-backed skills and the live role-skill taxonomy.

    This endpoint intentionally does not hardcode a student's roles. Every
    path is calculated from the current database skill levels and role
    requirements, so adding/changing skills or role requirements updates the
    roadmap automatically.
    """
    if user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access career paths",
        )

    profile = profile_for(db, user)

    current_skills = {}
    current_skill_meta = {}

    for item in profile.skills:
        level = evidence_proficiency(db, item)
        current_skills[item.skill_id] = level
        current_skill_meta[item.skill_id] = {
            "skill_id": item.skill_id,
            "skill": item.skill.name,
            "category": item.skill.category,
            "current": level,
            "verified": has_academic_verification(db, item),
        }

    roles = (
        db.query(Role)
        .filter(Role.name.in_(SEED_ROLES.keys()))
        .order_by(Role.name)
        .all()
    )

    paths = []

    for role in roles:
        requirements = (
            db.query(RoleSkillRequirement)
            .filter(RoleSkillRequirement.role_id == role.id)
            .all()
        )

        core = [r for r in requirements if r.category == "Core"]
        recommended = [r for r in requirements if r.category == "Recommended"]
        advanced = [
            r for r in requirements
            if r.category not in {"Core", "Recommended", "Alternative"}
        ]
        alternatives = [r for r in requirements if r.category == "Alternative"]

        def requirement_item(req):
            current = current_skills.get(req.skill_id, 0)
            required = req.required_level or 0
            gap = max(required - current, 0)
            return {
                "skill_id": req.skill_id,
                "skill": req.skill.name,
                "current": current,
                "required": required,
                "gap": gap,
                "category": req.category,
                "alternative_group": req.alternative_group,
                "verified": current_skill_meta.get(req.skill_id, {}).get("verified", False),
            }

        core_items = [requirement_item(r) for r in core]
        recommended_items = [requirement_item(r) for r in recommended]
        alternative_items = [requirement_item(r) for r in alternatives]
        advanced_items = [requirement_item(r) for r in advanced]

        if core_items:
            readiness_values = [
                min(item["current"] / item["required"], 1) * 100
                for item in core_items
                if item["required"] > 0
            ]
            readiness = round(sum(readiness_values) / len(readiness_values)) if readiness_values else 0
        else:
            readiness = 0

        matched = [
            item for item in core_items
            if item["current"] >= item["required"] and item["required"] > 0
        ]
        partial = [
            item for item in core_items
            if 0 < item["current"] < item["required"]
        ]
        missing = [
            item for item in core_items
            if item["current"] <= 0
        ]

        # Build a sequential learning roadmap. Existing core strengths are
        # surfaced first, then unmet core skills, then recommended skills,
        # then optional advanced skills. Within each learning stage, the
        # largest current gap is brought forward so the next action is clear.
        roadmap = []

        for item in sorted(
            matched,
            key=lambda x: (-x["current"], x["skill"]),
        ):
            roadmap.append({
                **item,
                "status": "Already strong",
                "action": "Use this skill as a foundation for the next step.",
                "reason": "You already meet the current core requirement for this role.",
            })

        unmet_core = [
            item for item in core_items
            if item["gap"] > 0
        ]
        unmet_core.sort(
            key=lambda x: (
                0 if x["current"] == 0 else 1,
                -x["gap"],
                x["required"],
                x["skill"],
            )
        )

        for item in unmet_core:
            roadmap.append({
                **item,
                "status": "Learn next",
                "action": "Build this core skill before moving deeper into the path.",
                "reason": (
                    "Core requirement not yet reached."
                    if item["current"] == 0
                    else "Your current level is below the role requirement."
                ),
            })

        unmet_recommended = [
            item for item in recommended_items
            if item["gap"] > 0
        ]
        unmet_recommended.sort(
            key=lambda x: (-x["gap"], x["required"], x["skill"])
        )

        for item in unmet_recommended:
            roadmap.append({
                **item,
                "status": "Build after core",
                "action": "Add this supporting skill after your core foundation is stronger.",
                "reason": "This skill supports stronger performance in the role.",
            })

        unmet_advanced = [
            item for item in advanced_items
            if item["gap"] > 0
        ]
        unmet_advanced.sort(
            key=lambda x: (-x["gap"], x["required"], x["skill"])
        )

        for item in unmet_advanced:
            roadmap.append({
                **item,
                "status": "Advanced",
                "action": "Explore this after the core and supporting skills are established.",
                "reason": "Optional advanced capability for deeper specialization.",
            })

        # Keep the payload compact while still giving the UI enough steps to
        # present a meaningful path. The full requirement lists remain
        # available through /roles/{role_id} if needed later.
        roadmap = roadmap[:12]

        matched_skill_names = [item["skill"] for item in core_items if item["current"] > 0]
        next_step = next(
            (item for item in roadmap if item["status"] != "Already strong"),
            None,
        )

        paths.append({
            "role_id": role.id,
            "role_name": role.name,
            "description": role.description,
            "readiness": readiness,
            "core_total": len(core_items),
            "core_matched": len(matched),
            "core_partial": len(partial),
            "core_missing": len(missing),
            "matched_skills": matched_skill_names[:6],
            "next_skill": next_step["skill"] if next_step else None,
            "next_skill_gap": next_step["gap"] if next_step else 0,
            "roadmap": roadmap,
        })

    paths.sort(
        key=lambda item: (
            item["role_id"] == profile.target_role_id,
            item["readiness"],
            item["core_matched"],
            -item["core_missing"],
            item["role_name"],
        ),
        reverse=True,
    )

    return {
        "target_role_id": profile.target_role_id,
        "target_role": (
            profile.target_role.name
            if profile.target_role
            else None
        ),
        "student_skills": list(current_skill_meta.values()),
        "paths": paths,
    }


@app.get("/roles/{role_id}")
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
):
    role = (
        db.query(Role)
        .filter(Role.id == role_id)
        .first()
    )

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found",
        )

    requirements = (
        db.query(RoleSkillRequirement)
        .filter(
            RoleSkillRequirement.role_id == role.id
        )
        .all()
    )

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "skills": [
            {
                "skill_id": req.skill_id,
                "skill": req.skill.name,
                "required_level": req.required_level,
                "category": req.category,
                "alternative_group": req.alternative_group,
            }
            for req in requirements
        ],
    }


# ============================================================
# SKILLS
# ============================================================

@app.get("/skills")
def get_skills(
    db: Session = Depends(get_db),
):
    skills = (
        db.query(Skill)
        .order_by(Skill.category, Skill.name)
        .all()
    )

    return [
        {
            "id": skill.id,
            "name": skill.name,
            "category": skill.category,
        }
        for skill in skills
    ]


@app.get("/student/skills")
def get_student_skills(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    result = []

    for student_skill in profile.skills:

        proficiency = evidence_proficiency(db, student_skill)
        evidence_count = (
            db.query(Evidence)
            .filter(Evidence.student_skill_id == student_skill.id)
            .count()
        )
        academic_verified = has_academic_verification(db, student_skill)

        result.append(
            {
                "id": student_skill.id,
                "skill_id": student_skill.skill_id,
                "skill": student_skill.skill.name,
                "category": student_skill.skill.category,
                "proficiency": proficiency,
                "verified": academic_verified,
                "academic_verified": academic_verified,
                "evidence_count": evidence_count,
            }
        )

    return result


@app.post("/student/skills")
def add_student_skill(
    data: SkillIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    skill = (
        db.query(Skill)
        .filter(Skill.id == data.skill_id)
        .first()
    )

    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    existing = get_student_skill(
        db,
        profile.id,
        skill.id,
    )

    if existing:
        return {
            "message": "Skill already exists",
            "skill_id": existing.skill_id,
        }

    # IMPORTANT:
    # data.proficiency is ignored.
    # Students do not self-rate.
    student_skill = StudentSkill(
        profile_id=profile.id,
        skill_id=skill.id,
        proficiency=0,
    )

    db.add(student_skill)
    db.commit()
    db.refresh(student_skill)

    return {
        "message": "Skill added. Complete an assessment and submit evidence for academic verification.",
        "skill_id": skill.id,
        "proficiency": 0,
        "verified": False,
    }


@app.delete("/student/skills/{skill_id}")
def delete_student_skill(
    skill_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    student_skill = get_student_skill(
        db,
        profile.id,
        skill_id,
    )

    if not student_skill:
        raise HTTPException(
            status_code=404,
            detail="Student skill not found",
        )

    db.delete(student_skill)
    db.commit()

    return {"message": "Skill deleted"}


# ============================================================
# EVIDENCE
# ============================================================

@app.post("/student/skills/{skill_id}/evidence")
def add_evidence(
    skill_id: int,
    data: EvidenceIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    student_skill = get_student_skill(
        db,
        profile.id,
        skill_id,
    )

    if not student_skill:
        raise HTTPException(
            status_code=404,
            detail="Student skill not found",
        )

    evidence = Evidence(
        student_skill_id=student_skill.id,
        kind=data.kind,
        title=data.title,
        url=data.url,
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    proficiency = evidence_proficiency(db, student_skill)
    academic_verified = has_academic_verification(db, student_skill)

    return {
        "message": "Evidence submitted for academic verification",
        "id": evidence.id,
        "proficiency": proficiency,
        "verified": academic_verified,
        "academic_verified": academic_verified,
        "evidence_count": (
            db.query(Evidence)
            .filter(Evidence.student_skill_id == student_skill.id)
            .count()
        ),
    }


@app.get("/student/skills/{skill_id}/evidence")
def get_evidence(
    skill_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    student_skill = get_student_skill(
        db,
        profile.id,
        skill_id,
    )

    if not student_skill:
        raise HTTPException(
            status_code=404,
            detail="Student skill not found",
        )

    evidence = (
        db.query(Evidence)
        .filter(
            Evidence.student_skill_id
            == student_skill.id
        )
        .all()
    )

    return [
        {
            "id": item.id,
            "kind": item.kind,
            "title": item.title,
            "url": item.url,
        }
        for item in evidence
    ]


# ============================================================
# STUDENT LEARNING RECOMMENDATIONS
#
# Recommendations are generated from the student's target role and
# assessment-derived proficiency. Only CORE role requirements are used,
# so learning is driven by actual skill gaps rather than a generic search.
# ============================================================

AYUSH_LEARNING_RESOURCES = {
    "Pharmacognosy": {
        "title": "Pharmacognosy and Phytochemistry",
        "platform": "NPTEL",
        "level": "Advanced",
        "duration": "12 weeks",
        "type": "Course",
        "url": "https://nptel.ac.in/courses/103101787",
    },
    "Phytochemistry": {
        "title": "Pharmacognosy & Metabolic Engineering",
        "platform": "NPTEL",
        "level": "Advanced",
        "duration": "12 weeks",
        "type": "Course",
        "url": "https://www.nptel.ac.in/courses/102105342",
    },
    "Scientific Writing": {
        "title": "Writing in the Sciences",
        "platform": "Coursera",
        "level": "Intermediate",
        "duration": "Approx. 8 hours",
        "type": "Course",
        "url": "https://www.coursera.org/learn/sciwrite",
    },
    "Data Analysis": {
        "title": "Data Analysis with Python",
        "platform": "Coursera",
        "level": "Intermediate",
        "duration": "Flexible",
        "type": "Course",
        "url": "https://www.coursera.org/learn/data-analysis-with-python",
    },
    "Statistics": {
        "title": "Data Analysis with Python",
        "platform": "Coursera",
        "level": "Intermediate",
        "duration": "Flexible",
        "type": "Course",
        "url": "https://www.coursera.org/learn/data-analysis-with-python",
    },
}


@app.get("/student/learning")
def student_learning(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access learning recommendations",
        )

    profile = profile_for(db, user)

    if not profile.target_role_id:
        return []

    role = (
        db.query(Role)
        .filter(Role.id == profile.target_role_id)
        .first()
    )

    if not role:
        return []

    # Assessment-derived proficiency only. Evidence verification does not
    # increase the student's proficiency percentage.
    student_skills = {
        item.skill_id: evidence_proficiency(db, item)
        for item in profile.skills
    }

    core_requirements = [
        requirement
        for requirement in role.requirements
        if requirement.category == "Core"
        and requirement.required_level > 0
    ]

    recommendations = []

    for requirement in core_requirements:
        current = int(student_skills.get(requirement.skill_id, 0))
        required = int(requirement.required_level)
        gap = max(required - current, 0)

        # Do not recommend learning for skills that already meet the role
        # requirement.
        if gap <= 0:
            continue

        skill_name = requirement.skill.name
        resource = AYUSH_LEARNING_RESOURCES.get(skill_name)

        if resource is None:
            resource = {
                "title": f"Learn {skill_name}",
                "platform": "SWAYAM",
                "level": "Intermediate",
                "duration": "Self-paced",
                "type": "Course search",
                "url": "https://swayam.gov.in/",
            }

        if gap >= 30:
            priority = "High"
        elif gap >= 15:
            priority = "Medium"
        else:
            priority = "Low"

        recommendations.append({
            "skill_id": requirement.skill_id,
            "skill": skill_name,
            "current": current,
            "required": required,
            "gap": gap,
            "priority": priority,
            "resource": resource,
        })

    recommendations.sort(
        key=lambda item: (
            item["gap"],
            item["required"],
        ),
        reverse=True,
    )

    return recommendations[:8]


# ============================================================
# SKILL GAP
#
# ONLY CORE SKILLS participate in:
#   - readiness
#   - active gaps
#   - gap score
#   - graph calculation
#
# Recommended / Alternative / Advanced are informational.
# ============================================================

@app.get("/student/skill-gap")
def skill_gap(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    if not profile.target_role_id:
        return {
            "target_role": None,
            "readiness": 0,
            "active_gaps": 0,
            "core": [],
            "recommended": [],
            "alternatives": [],
            "advanced": [],
        }

    role = (
        db.query(Role)
        .filter(Role.id == profile.target_role_id)
        .first()
    )

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Target role not found",
        )

    requirements = (
        db.query(RoleSkillRequirement)
        .filter(
            RoleSkillRequirement.role_id == role.id
        )
        .all()
    )

    student_skills = {
        item.skill_id: evidence_proficiency(
            db,
            item,
        )
        for item in profile.skills
    }

    core = []
    recommended = []
    alternatives = []
    advanced = []

    for req in requirements:

        current = student_skills.get(
            req.skill_id,
            0,
        )

        gap = max(
            req.required_level - current,
            0,
        )

        item = {
            "skill_id": req.skill_id,
            "skill": req.skill.name,
            "current": current,
            "required": req.required_level,
            "gap": gap,
            "category": req.category,
            "alternative_group": req.alternative_group,
            "verified": (
                has_academic_verification(db, get_student_skill(db, profile.id, req.skill_id))
                if get_student_skill(db, profile.id, req.skill_id)
                else False
            ),
        }

        if req.category == "Core":
            core.append(item)

        elif req.category == "Recommended":
            recommended.append(item)

        elif req.category == "Alternative":
            alternatives.append(item)

        else:
            advanced.append(item)

    # --------------------------------------------------------
    # READINESS
    #
    # CORE ONLY
    #
    # Each core skill contributes according to:
    #
    # current / required
    #
    # capped at 100%.
    # --------------------------------------------------------

    if core:

        readiness_values = [
            min(
                item["current"]
                / item["required"],
                1,
            )
            * 100
            for item in core
            if item["required"] > 0
        ]

        readiness = round(
            sum(readiness_values)
            / len(readiness_values)
        )

    else:
        readiness = 0

    active_gaps = sum(
        1
        for item in core
        if item["gap"] > 0
    )

    return {
        "target_role": {
            "id": role.id,
            "name": role.name,
        },
        "readiness": readiness,
        "active_gaps": active_gaps,

        # Used by the graph
        "core": core,

        # Displayed separately
        "recommended": recommended,
        "alternatives": alternatives,
        "advanced": advanced,
    }


# ============================================================
# INTERNSHIP LIFECYCLE
# ============================================================

def _parse_optional_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must use YYYY-MM-DD format")


def internship_payload(record: InternshipRecord):
    return {
        "id": record.id,
        "application_id": record.application_id,
        "opportunity_id": record.opportunity_id,
        "opportunity_title": record.opportunity.title if record.opportunity else "",
        "student_id": record.student_id,
        "student_name": (
            record.student.profile.name
            if record.student and record.student.profile and record.student.profile.name
            else (record.student.email if record.student else "")
        ),
        "student_email": record.student.email if record.student else "",
        "company_id": record.company_id,
        "company_name": (
            record.company.profile.name
            if record.company and record.company.profile and record.company.profile.name
            else (record.company.email if record.company else "")
        ),
        "mentor_name": record.mentor_name,
        "mentor_email": record.mentor_email,
        "status": record.status,
        "progress_percent": record.progress_percent,
        "start_date": record.start_date,
        "expected_end_date": record.expected_end_date,
        "actual_end_date": record.actual_end_date,
        "summary": record.summary,
        "certificate_url": record.certificate_url,
        "report_url": record.report_url,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "milestones": [
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "due_date": item.due_date,
                "status": item.status,
                "completed_at": item.completed_at,
            }
            for item in sorted(record.milestones, key=lambda x: x.id)
        ],
        "feedback": [
            {
                "id": item.id,
                "author_id": item.author_id,
                "author_role": item.author_role,
                "author_name": (
                    item.author.profile.name
                    if item.author and item.author.profile and item.author.profile.name
                    else (item.author.email if item.author else "")
                ),
                "rating": item.rating,
                "feedback": item.feedback,
                "created_at": item.created_at,
            }
            for item in sorted(record.feedback, key=lambda x: x.created_at, reverse=True)
        ],
    }


def _get_internship(record_id: int, db: Session):
    record = db.query(InternshipRecord).filter(InternshipRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Internship record not found")
    return record


def _can_manage_internship(record: InternshipRecord, user: User):
    return user.role == "admin" or user.id in {record.company_id, record.student_id}


@app.get("/internships")
def get_internships(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(InternshipRecord).order_by(InternshipRecord.created_at.desc())
    if user.role == "student":
        query = query.filter(InternshipRecord.student_id == user.id)
    elif user.role in {"company", "academician"}:
        if user.role == "company":
            query = query.filter(InternshipRecord.company_id == user.id)
    elif user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return [internship_payload(item) for item in query.all()]


@app.get("/internships/{internship_id}")
def get_internship(
    internship_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = _get_internship(internship_id, db)
    if not _can_manage_internship(record, user) and user.role not in {"academician", "admin"}:
        raise HTTPException(status_code=403, detail="Not authorized")
    return internship_payload(record)


@app.post("/applications/{application_id}/internship")
def create_internship_from_application(
    application_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    opportunity = application.opportunity
    if user.role != "admin" and opportunity.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the opportunity owner can start an internship")
    if application.status not in {"Selected", "Ongoing"}:
        raise HTTPException(status_code=400, detail="Select the student before starting the internship")
    if (opportunity.opportunity_type or "").lower() not in {"internship", "apprenticeship", "industrial training"}:
        raise HTTPException(status_code=400, detail="This application is not an internship or industrial-training opportunity")
    existing = db.query(InternshipRecord).filter(InternshipRecord.application_id == application.id).first()
    if existing:
        return internship_payload(existing)
    record = InternshipRecord(
        application_id=application.id,
        opportunity_id=application.opportunity_id,
        student_id=application.student_id,
        company_id=opportunity.owner_id,
        status="Not Started",
    )
    db.add(record)
    application.status = "Ongoing"
    db.commit()
    db.refresh(record)
    return internship_payload(record)


@app.patch("/internships/{internship_id}")
def update_internship(
    internship_id: int,
    data: InternshipUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = _get_internship(internship_id, db)
    if not _can_manage_internship(record, user):
        raise HTTPException(status_code=403, detail="Not authorized")

    for field in ["status", "progress_percent", "mentor_name", "mentor_email", "summary", "certificate_url", "report_url"]:
        value = getattr(data, field)
        if value is not None:
            setattr(record, field, value)

    if data.start_date is not None:
        record.start_date = _parse_optional_date(data.start_date)
    if data.expected_end_date is not None:
        record.expected_end_date = _parse_optional_date(data.expected_end_date)
    if data.actual_end_date is not None:
        record.actual_end_date = _parse_optional_date(data.actual_end_date)

    if record.status == "Ongoing" and record.progress_percent == 0:
        record.progress_percent = 1
    if record.status == "Completed":
        record.progress_percent = 100
        if not record.actual_end_date:
            record.actual_end_date = datetime.utcnow()
        record.application.status = "Completed"
    elif record.status == "Cancelled":
        record.application.status = "Rejected"

    db.commit()
    db.refresh(record)
    return internship_payload(record)


@app.post("/internships/{internship_id}/milestones")
def add_internship_milestone(
    internship_id: int,
    data: InternshipMilestoneIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = _get_internship(internship_id, db)
    if user.role not in {"company", "admin"} or (user.role != "admin" and record.company_id != user.id):
        raise HTTPException(status_code=403, detail="Only the internship manager can add milestones")
    milestone = InternshipMilestone(
        internship_id=record.id,
        title=data.title,
        description=data.description,
        due_date=_parse_optional_date(data.due_date),
    )
    db.add(milestone)
    db.commit()
    db.refresh(record)
    return internship_payload(record)


@app.patch("/internships/milestones/{milestone_id}")
def update_internship_milestone(
    milestone_id: int,
    data: InternshipMilestoneUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    milestone = db.query(InternshipMilestone).filter(InternshipMilestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    record = milestone.internship
    if not _can_manage_internship(record, user):
        raise HTTPException(status_code=403, detail="Not authorized")
    if data.status not in {"Pending", "In Progress", "Completed"}:
        raise HTTPException(status_code=400, detail="Invalid milestone status")
    milestone.status = data.status
    milestone.completed_at = datetime.utcnow() if data.status == "Completed" else None
    db.commit()
    db.refresh(record)
    return internship_payload(record)


@app.post("/internships/{internship_id}/feedback")
def add_internship_feedback(
    internship_id: int,
    data: InternshipFeedbackIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = _get_internship(internship_id, db)
    if not _can_manage_internship(record, user) and user.role not in {"academician", "admin"}:
        raise HTTPException(status_code=403, detail="Not authorized")
    feedback = InternshipFeedback(
        internship_id=record.id,
        author_id=user.id,
        author_role=user.role,
        rating=data.rating,
        feedback=data.feedback,
    )
    db.add(feedback)
    db.commit()
    db.refresh(record)
    return internship_payload(record)


@app.get("/student/internships")
def student_internships(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")
    records = db.query(InternshipRecord).filter(InternshipRecord.student_id == user.id).order_by(InternshipRecord.created_at.desc()).all()
    return [internship_payload(item) for item in records]


# ============================================================
# SECURE DOCUMENT MANAGEMENT
# ============================================================

def student_document_payload(item: StudentDocument):
    return {
        "id": item.id,
        "student_id": item.student_id,
        "student_name": (
            item.student.profile.name
            if item.student and item.student.profile and item.student.profile.name
            else (item.student.email if item.student else "")
        ),
        "title": item.title,
        "document_type": item.document_type,
        "description": item.description,
        "issuer": item.issuer,
        "issued_on": item.issued_on,
        "url": item.url,
        "visibility": item.visibility,
        "verification_status": item.verification_status,
        "rejection_reason": item.rejection_reason,
        "linked_internship_id": item.linked_internship_id,
        "linked_collaboration_id": item.linked_collaboration_id,
        "verified_by": item.verified_by,
        "verified_at": item.verified_at,
        "created_at": item.created_at,
    }


@app.get("/student/documents")
def student_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access their documents")
    rows = (
        db.query(StudentDocument)
        .filter(StudentDocument.student_id == user.id)
        .order_by(StudentDocument.created_at.desc())
        .all()
    )
    return [student_document_payload(row) for row in rows]


@app.post("/student/documents")
def create_student_document(
    payload: StudentDocumentIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can add documents")
    if payload.visibility not in {"Private", "Academician", "Industry"}:
        raise HTTPException(status_code=400, detail="Invalid document visibility")
    item = StudentDocument(
        student_id=user.id,
        title=payload.title.strip(),
        document_type=payload.document_type.strip() or "Other",
        description=payload.description.strip(),
        issuer=payload.issuer.strip(),
        issued_on=payload.issued_on.strip(),
        url=payload.url.strip(),
        visibility=payload.visibility,
        linked_internship_id=payload.linked_internship_id,
        linked_collaboration_id=payload.linked_collaboration_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return student_document_payload(item)


@app.patch("/student/documents/{document_id}")
def update_student_document(
    document_id: int,
    payload: StudentDocumentUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(StudentDocument).filter(StudentDocument.id == document_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")
    if user.role != "student" or item.student_id != user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own documents")
    if payload.visibility is not None and payload.visibility not in {"Private", "Academician", "Industry"}:
        raise HTTPException(status_code=400, detail="Invalid document visibility")
    for field in [
        "title", "document_type", "description", "issuer", "issued_on", "url",
        "visibility", "linked_internship_id", "linked_collaboration_id"
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(item, field, value.strip() if isinstance(value, str) else value)
    # Any edited document goes back through verification.
    item.verification_status = "Pending"
    item.rejection_reason = ""
    item.verified_by = None
    item.verified_at = None
    db.commit()
    db.refresh(item)
    return student_document_payload(item)


@app.delete("/student/documents/{document_id}")
def delete_student_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(StudentDocument).filter(StudentDocument.id == document_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")
    if user.role != "student" or item.student_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own documents")
    db.delete(item)
    db.commit()
    return {"message": "Document removed"}


@app.get("/academician/document-verification")
def academician_document_verification(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in {"academician", "admin"}:
        raise HTTPException(status_code=403, detail="Only academicians or admins can review documents")
    rows = (
        db.query(StudentDocument)
        .filter(StudentDocument.verification_status == "Pending")
        .order_by(StudentDocument.created_at.asc())
        .all()
    )
    return [student_document_payload(row) for row in rows]


@app.patch("/academician/documents/{document_id}/verify")
def verify_student_document(
    document_id: int,
    payload: StudentDocumentVerificationIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in {"academician", "admin"}:
        raise HTTPException(status_code=403, detail="Only academicians or admins can verify documents")
    if payload.status not in {"Verified", "Rejected", "Pending"}:
        raise HTTPException(status_code=400, detail="Invalid verification status")
    item = db.query(StudentDocument).filter(StudentDocument.id == document_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")
    item.verification_status = payload.status
    item.rejection_reason = payload.reason.strip() if payload.status == "Rejected" else ""
    item.verified_by = user.id if payload.status != "Pending" else None
    item.verified_at = datetime.utcnow() if payload.status != "Pending" else None
    db.commit()
    db.refresh(item)
    return student_document_payload(item)


@app.get("/student/documents/{document_id}")
def get_student_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(StudentDocument).filter(StudentDocument.id == document_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")
    if user.role == "student" and item.student_id == user.id:
        return student_document_payload(item)
    if user.role in {"academician", "admin"}:
        return student_document_payload(item)
    if item.visibility == "Industry" and user.role == "company" and item.verification_status == "Verified":
        return student_document_payload(item)
    raise HTTPException(status_code=403, detail="You do not have access to this document")


# ============================================================
# PORTFOLIO
# ============================================================

@app.get("/portfolio")
def portfolio(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    skills = [
        {
            "skill": item.skill.name,
            "proficiency": evidence_proficiency(db, item),
            "verified": has_academic_verification(db, item),
        }
        for item in profile.skills
    ]

    projects = [
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "url": item.url,
            "type": "Project",
        }
        for item in profile.projects
    ]

    certificates = [
        {
            "id": item.id,
            "title": item.title,
            "issuer": item.issuer,
            "url": item.url,
            "type": "Certificate",
        }
        for item in profile.certificates
    ]

    courses = [
        {
            "id": item.id,
            "title": item.title,
            "provider": item.provider,
            "url": item.url,
            "type": "Course",
        }
        for item in profile.courses
    ]

    internships = [
        internship_payload(item)
        for item in db.query(InternshipRecord)
        .filter(InternshipRecord.student_id == user.id)
        .order_by(InternshipRecord.created_at.desc())
        .all()
    ]

    return {
        "profile": {
            "name": profile.name,
            "education": profile.education,
            "year_degree": profile.year_degree,
            "target_role": (
                profile.target_role.name
                if profile.target_role
                else None
            ),
        },
        "skills": skills,
        "projects": projects,
        "certificates": certificates,
        "courses": courses,
        "internships": internships,
    }


# ============================================================
# PROJECTS
# ============================================================

@app.post("/student/projects")
def add_project(
    data: ItemIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    project = Project(
        profile_id=profile.id,
        title=data.title,
        description=data.description,
        url=data.url,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "url": project.url,
    }


@app.get("/student/projects")
def get_projects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    return [
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "url": item.url,
        }
        for item in profile.projects
    ]


# ============================================================
# CERTIFICATES
# ============================================================

@app.post("/student/certificates")
def add_certificate(
    data: ItemIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    certificate = Certificate(
        profile_id=profile.id,
        title=data.title,
        issuer=data.issuer,
        url=data.url,
    )

    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    return {
        "id": certificate.id,
        "title": certificate.title,
        "issuer": certificate.issuer,
        "url": certificate.url,
    }


@app.get("/student/certificates")
def get_certificates(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    return [
        {
            "id": item.id,
            "title": item.title,
            "issuer": item.issuer,
            "url": item.url,
        }
        for item in profile.certificates
    ]


# ============================================================
# COURSES
# ============================================================

@app.post("/student/courses")
def add_course(
    data: ItemIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    course = Course(
        profile_id=profile.id,
        title=data.title,
        provider=data.provider,
        url=data.url,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return {
        "id": course.id,
        "title": course.title,
        "provider": course.provider,
        "url": course.url,
    }


@app.get("/student/courses")
def get_courses(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    return [
        {
            "id": item.id,
            "title": item.title,
            "provider": item.provider,
            "url": item.url,
        }
        for item in profile.courses
    ]


# ============================================================
# COMPANY VERIFICATION
# ============================================================

@app.get("/company/verification")
def get_company_verification(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "company":
        raise HTTPException(status_code=403, detail="Only company users can access company verification")

    row = db.execute(
        company_verification_requests.select().where(
            company_verification_requests.c.user_id == user.id
        )
    ).mappings().first()

    if not row:
        return {
            "status": "Not Submitted",
            "submitted_at": None,
            "reviewed_at": None,
            "notes": "Complete your company profile and submit it for verification.",
        }

    return {
        "status": row["status"],
        "submitted_at": row["submitted_at"],
        "reviewed_at": row["reviewed_at"],
        "notes": row["notes"] or "",
    }


@app.post("/company/verification")
def submit_company_verification(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "company":
        raise HTTPException(status_code=403, detail="Only company users can submit company verification")

    profile = profile_for(db, user)
    missing = []
    if not (profile.name or "").strip():
        missing.append("organisation name")
    if not (profile.education or "").strip():
        missing.append("industry / field")
    if not (profile.career_interests or "").strip():
        missing.append("AYUSH focus")
    if not (profile.research_experience or "").strip():
        missing.append("hiring / collaboration focus")

    if missing:
        raise HTTPException(
            status_code=400,
            detail="Complete these company profile fields first: " + ", ".join(missing),
        )

    existing = db.execute(
        company_verification_requests.select().where(
            company_verification_requests.c.user_id == user.id
        )
    ).mappings().first()

    now = datetime.utcnow()
    if existing:
        if existing["status"] == "Verified":
            return {"message": "Company is already verified.", "status": "Verified"}
        db.execute(
            company_verification_requests.update()
            .where(company_verification_requests.c.user_id == user.id)
            .values(status="Pending Review", submitted_at=now, reviewed_at=None, reviewer_id=None)
        )
    else:
        db.execute(
            company_verification_requests.insert().values(
                user_id=user.id,
                status="Pending Review",
                submitted_at=now,
                notes="",
            )
        )
    db.commit()
    return {"message": "Company verification submitted for review.", "status": "Pending Review"}


@app.get("/admin/company-verification")
def admin_company_verification_queue(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can review company verification")

    rows = db.execute(
        company_verification_requests.select().order_by(company_verification_requests.c.id.desc())
    ).mappings().all()

    result = []
    for row in rows:
        company = db.query(User).filter(User.id == row["user_id"]).first()
        profile = profile_for(db, company) if company else None
        result.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "email": company.email if company else "",
            "organisation_name": profile.name if profile else "",
            "industry": profile.education if profile else "",
            "ayush_focus": profile.career_interests if profile else "",
            "status": row["status"],
            "submitted_at": row["submitted_at"],
            "notes": row["notes"] or "",
        })
    return result


@app.patch("/admin/company-verification/{user_id}")
def review_company_verification(
    user_id: int,
    data: ApplicationStatusIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can review company verification")
    if data.status not in {"Verified", "Rejected", "Needs More Information"}:
        raise HTTPException(status_code=400, detail="Invalid company verification status")

    company = db.query(User).filter(User.id == user_id, User.role == "company").first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    row = db.execute(
        company_verification_requests.select().where(
            company_verification_requests.c.user_id == user_id
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Verification request not found")

    db.execute(
        company_verification_requests.update()
        .where(company_verification_requests.c.user_id == user_id)
        .values(status=data.status, reviewed_at=datetime.utcnow(), reviewer_id=user.id)
    )
    db.commit()
    return {"message": f"Company verification marked {data.status}.", "status": data.status}


# ============================================================
# INDUSTRY LEARNING PROGRAMS
# ============================================================

def learning_program_payload(
    program: LearningProgram,
    enrollment: Optional[LearningProgramEnrollment] = None,
):
    return {
        "id": program.id,
        "owner_id": program.owner_id,
        "owner_name": (
            program.owner.profile.name
            if program.owner
            and program.owner.profile
            and program.owner.profile.name
            else (program.owner.email if program.owner else "")
        ),
        "title": program.title,
        "description": program.description,
        "program_type": program.program_type,
        "ayush_focus": program.ayush_focus,
        "duration": program.duration,
        "delivery_mode": program.delivery_mode,
        "eligibility": program.eligibility,
        "registration_deadline": program.registration_deadline,
        "certificate_available": program.certificate_available,
        "registration_url": program.registration_url,
        "status": program.status,
        "created_at": program.created_at,
        "skills": [
            {
                "skill_id": item.skill_id,
                "skill": item.skill.name if item.skill else "",
                "category": item.skill.category if item.skill else "",
            }
            for item in program.skills
        ],
        "enrollment": (
            {
                "id": enrollment.id,
                "learning_program_id": enrollment.learning_program_id,
                "student_id": enrollment.student_id,
                "status": enrollment.status,
                "enrolled_at": enrollment.enrolled_at,
                "completed_at": enrollment.completed_at,
                "certificate_url": enrollment.certificate_url,
            }
            if enrollment
            else None
        ),
    }


@app.post("/industry/learning-programs")
def create_learning_program(
    data: LearningProgramIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in {"company", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only industry partners or admins can create learning programs",
        )

    program = LearningProgram(
        owner_id=user.id,
        title=data.title,
        description=data.description,
        program_type=data.program_type,
        ayush_focus=data.ayush_focus,
        duration=data.duration,
        delivery_mode=data.delivery_mode,
        eligibility=data.eligibility,
        registration_deadline=data.registration_deadline,
        certificate_available=data.certificate_available,
        registration_url=data.registration_url,
        status="Published",
    )

    db.add(program)
    db.commit()
    db.refresh(program)

    for item in data.skills:
        skill = (
            db.query(Skill)
            .filter(Skill.id == item.skill_id)
            .first()
        )
        if not skill:
            continue

        db.add(
            LearningProgramSkill(
                learning_program_id=program.id,
                skill_id=skill.id,
            )
        )

    db.commit()
    db.refresh(program)

    return learning_program_payload(program)


@app.get("/learning-programs")
def get_learning_programs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(LearningProgram)
        .filter(LearningProgram.status == "Published")
        .order_by(LearningProgram.created_at.desc())
    )

    programs = query.all()

    if user.role == "student":
        enrollments = {
            item.learning_program_id: item
            for item in (
                db.query(LearningProgramEnrollment)
                .filter(LearningProgramEnrollment.student_id == user.id)
                .all()
            )
        }
        return [
            learning_program_payload(
                program,
                enrollments.get(program.id),
            )
            for program in programs
        ]

    return [
        learning_program_payload(program)
        for program in programs
    ]


@app.get("/industry/learning-programs/mine")
def get_my_learning_programs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in {"company", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only industry partners or admins can view managed learning programs",
        )

    query = db.query(LearningProgram)

    if user.role == "company":
        query = query.filter(LearningProgram.owner_id == user.id)

    programs = (
        query
        .order_by(LearningProgram.created_at.desc())
        .all()
    )

    return [
        learning_program_payload(program)
        for program in programs
    ]


@app.get("/student/learning-programs")
def get_student_learning_programs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access learning program participation",
        )

    enrollments = (
        db.query(LearningProgramEnrollment)
        .filter(LearningProgramEnrollment.student_id == user.id)
        .order_by(LearningProgramEnrollment.enrolled_at.desc())
        .all()
    )

    return [
        learning_program_payload(
            enrollment.learning_program,
            enrollment,
        )
        for enrollment in enrollments
    ]


@app.post("/learning-programs/{program_id}/enroll")
def enroll_in_learning_program(
    program_id: int,
    data: LearningProgramEnrollmentIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can enroll in learning programs",
        )

    if data.learning_program_id != program_id:
        raise HTTPException(
            status_code=400,
            detail="Learning program ID does not match request",
        )

    program = (
        db.query(LearningProgram)
        .filter(
            LearningProgram.id == program_id,
            LearningProgram.status == "Published",
        )
        .first()
    )

    if not program:
        raise HTTPException(
            status_code=404,
            detail="Learning program not found",
        )

    existing = (
        db.query(LearningProgramEnrollment)
        .filter(
            LearningProgramEnrollment.learning_program_id == program_id,
            LearningProgramEnrollment.student_id == user.id,
        )
        .first()
    )

    if existing:
        return learning_program_payload(program, existing)

    enrollment = LearningProgramEnrollment(
        learning_program_id=program_id,
        student_id=user.id,
        status="Enrolled",
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return learning_program_payload(program, enrollment)


@app.patch("/learning-programs/enrollments/{enrollment_id}")
def update_learning_program_enrollment(
    enrollment_id: int,
    data: LearningProgramEnrollmentStatusIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enrollment = (
        db.query(LearningProgramEnrollment)
        .filter(LearningProgramEnrollment.id == enrollment_id)
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="Learning program enrollment not found",
        )

    program = enrollment.learning_program

    is_student = user.role == "student" and enrollment.student_id == user.id
    is_owner = user.role == "company" and program.owner_id == user.id
    is_admin = user.role == "admin"

    if not (is_student or is_owner or is_admin):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this enrollment",
        )

    allowed_statuses = {
        "Enrolled",
        "In Progress",
        "Completed",
        "Cancelled",
    }

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid enrollment status",
        )

    enrollment.status = data.status

    if data.status == "Completed":
        enrollment.completed_at = datetime.utcnow()
    elif data.status in {"Enrolled", "In Progress", "Cancelled"}:
        enrollment.completed_at = None

    db.commit()
    db.refresh(enrollment)

    return learning_program_payload(program, enrollment)




# ============================================================
# ACADEMIA–INDUSTRY FACULTY OPPORTUNITIES
# ============================================================

FACULTY_OPPORTUNITY_TYPES = {
    "Faculty Internship",
    "Industrial Training for Faculty",
    "Faculty Development Programme (FDP)",
    "Consultancy",
    "Collaborative Research",
    "Guest Lecture",
    "Innovation Challenge",
    "Live Industry Project",
}

def faculty_opportunity_payload(item: FacultyOpportunity, application=None):
    return {
        "id": item.id,
        "owner_id": item.owner_id,
        "owner_role": item.owner.role if item.owner else None,
        "owner_name": (
            item.owner.profile.name
            if item.owner and item.owner.profile and item.owner.profile.name
            else (item.owner.email if item.owner else "")
        ),
        "title": item.title,
        "description": item.description,
        "opportunity_type": item.opportunity_type,
        "ayush_focus": item.ayush_focus,
        "location": item.location,
        "delivery_mode": item.delivery_mode,
        "duration": item.duration,
        "eligibility": item.eligibility,
        "registration_url": item.registration_url,
        "status": item.status,
        "created_at": item.created_at,
        "skills": [
            {"skill_id": row.skill_id, "skill": row.skill.name if row.skill else "", "category": row.skill.category if row.skill else ""}
            for row in item.skills
        ],
        "application": (
            {
                "id": application.id,
                "academician_id": application.academician_id,
                "status": application.status,
                "message": application.message,
                "created_at": application.created_at,
            } if application else None
        ),
    }


@app.post("/faculty-opportunities")
def create_faculty_opportunity(
    data: FacultyOpportunityIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in {"company", "academician", "admin"}:
        raise HTTPException(status_code=403, detail="Only companies, academicians or admins can create faculty opportunities")
    if data.opportunity_type not in FACULTY_OPPORTUNITY_TYPES:
        raise HTTPException(status_code=400, detail="Invalid faculty opportunity type")

    item = FacultyOpportunity(
        owner_id=user.id, title=data.title, description=data.description,
        opportunity_type=data.opportunity_type, ayush_focus=data.ayush_focus,
        location=data.location, delivery_mode=data.delivery_mode, duration=data.duration,
        eligibility=data.eligibility, registration_url=data.registration_url, status="Published",
    )
    db.add(item)
    db.flush()
    for skill_id in data.skills:
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if skill:
            db.add(FacultyOpportunitySkill(opportunity_id=item.id, skill_id=skill.id))
    db.commit()
    db.refresh(item)
    return faculty_opportunity_payload(item)


@app.get("/faculty-opportunities")
def get_faculty_opportunities(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(FacultyOpportunity).filter(FacultyOpportunity.status == "Published").order_by(FacultyOpportunity.created_at.desc()).all()
    applications = {}
    if user.role == "academician":
        applications = {
            x.opportunity_id: x
            for x in db.query(FacultyOpportunityApplication).filter(FacultyOpportunityApplication.academician_id == user.id).all()
        }
    return [faculty_opportunity_payload(x, applications.get(x.id)) for x in rows]


@app.get("/faculty-opportunities/mine")
def get_my_faculty_opportunities(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in {"company", "academician", "admin"}:
        raise HTTPException(status_code=403, detail="Not authorized")
    rows = db.query(FacultyOpportunity).filter(FacultyOpportunity.owner_id == user.id).order_by(FacultyOpportunity.created_at.desc()).all()
    return [faculty_opportunity_payload(x) for x in rows]


@app.post("/faculty-opportunities/{opportunity_id}/apply")
def apply_faculty_opportunity(
    opportunity_id: int,
    data: FacultyOpportunityApplicationIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "academician":
        raise HTTPException(status_code=403, detail="Only academicians can apply to faculty opportunities")
    item = db.query(FacultyOpportunity).filter(FacultyOpportunity.id == opportunity_id, FacultyOpportunity.status == "Published").first()
    if not item:
        raise HTTPException(status_code=404, detail="Faculty opportunity not found")
    if item.owner_id == user.id:
        raise HTTPException(status_code=400, detail="You cannot apply to your own opportunity")
    existing = db.query(FacultyOpportunityApplication).filter(FacultyOpportunityApplication.opportunity_id == opportunity_id, FacultyOpportunityApplication.academician_id == user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already applied to this faculty opportunity")
    application = FacultyOpportunityApplication(opportunity_id=opportunity_id, academician_id=user.id, message=data.message.strip())
    db.add(application)
    db.commit()
    db.refresh(application)
    return faculty_opportunity_payload(item, application)


@app.get("/academician/faculty-opportunities/applications")
def get_my_faculty_opportunity_applications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "academician":
        raise HTTPException(status_code=403, detail="Only academicians can view these applications")
    rows = db.query(FacultyOpportunityApplication).filter(FacultyOpportunityApplication.academician_id == user.id).order_by(FacultyOpportunityApplication.created_at.desc()).all()
    return [
        {
            "id": x.id, "opportunity_id": x.opportunity_id, "title": x.opportunity.title,
            "opportunity_type": x.opportunity.opportunity_type, "owner_name": x.opportunity.owner.profile.name if x.opportunity.owner and x.opportunity.owner.profile and x.opportunity.owner.profile.name else (x.opportunity.owner.email if x.opportunity.owner else ""),
            "status": x.status, "message": x.message, "created_at": x.created_at,
        } for x in rows
    ]


@app.get("/faculty-opportunities/{opportunity_id}/applications")
def get_faculty_opportunity_applications(
    opportunity_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(FacultyOpportunity).filter(FacultyOpportunity.id == opportunity_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Faculty opportunity not found")
    if user.role != "admin" and item.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    rows = db.query(FacultyOpportunityApplication).filter(FacultyOpportunityApplication.opportunity_id == opportunity_id).order_by(FacultyOpportunityApplication.created_at.desc()).all()
    return [
        {
            "id": x.id, "academician_id": x.academician_id,
            "academician_name": x.academician.profile.name if x.academician and x.academician.profile and x.academician.profile.name else (x.academician.email if x.academician else ""),
            "academician_email": x.academician.email if x.academician else "",
            "status": x.status, "message": x.message, "created_at": x.created_at,
        } for x in rows
    ]


@app.patch("/faculty-opportunity-applications/{application_id}")
def update_faculty_opportunity_application(
    application_id: int,
    data: FacultyOpportunityApplicationStatusIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = db.query(FacultyOpportunityApplication).filter(FacultyOpportunityApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Faculty opportunity application not found")
    if user.role != "admin" and application.opportunity.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    allowed = {"Applied", "Under Review", "Accepted", "Rejected", "Completed"}
    if data.status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid application status")
    application.status = data.status
    db.commit()
    db.refresh(application)
    return {"id": application.id, "status": application.status}



# ============================================================
# ACADEMIA-INDUSTRY COLLABORATIONS
# ============================================================

COLLABORATION_TYPES = {
    "Collaborative Research", "Consultancy", "Guest Lecture",
    "Innovation Challenge", "Live Industry Project", "Faculty Internship",
    "Industrial Training", "Faculty Development Programme",
}


def _collaboration_person(user):
    if not user:
        return {"id": None, "name": "", "email": ""}
    name = user.profile.name if user.profile and user.profile.name else user.email
    return {"id": user.id, "name": name, "email": user.email}


def collaboration_payload(item: Collaboration):
    return {
        "id": item.id,
        "opportunity_id": item.opportunity_id,
        "application_id": item.application_id,
        "owner": _collaboration_person(item.owner),
        "academician": _collaboration_person(item.academician),
        "title": item.title,
        "collaboration_type": item.collaboration_type,
        "ayush_focus": item.ayush_focus,
        "objective": item.objective,
        "status": item.status,
        "start_date": item.start_date,
        "expected_end_date": item.expected_end_date,
        "actual_end_date": item.actual_end_date,
        "completion_summary": item.completion_summary,
        "created_at": item.created_at,
        "milestones": [
            {"id": x.id, "title": x.title, "description": x.description, "due_date": x.due_date, "status": x.status, "completed_at": x.completed_at}
            for x in sorted(item.milestones, key=lambda y: y.id)
        ],
        "feedback": [
            {"id": x.id, "author": _collaboration_person(x.author), "feedback_type": x.feedback_type, "comments": x.comments, "created_at": x.created_at}
            for x in sorted(item.feedback, key=lambda y: y.created_at or datetime.min, reverse=True)
        ],
        "outputs": [
            {"id": x.id, "title": x.title, "output_type": x.output_type, "description": x.description, "url": x.url, "verified": x.verified, "created_at": x.created_at}
            for x in sorted(item.outputs, key=lambda y: y.created_at or datetime.min, reverse=True)
        ],
    }


def _can_access_collaboration(item: Collaboration, user: User):
    return user.role == "admin" or item.owner_id == user.id or item.academician_id == user.id


@app.post("/faculty-opportunity-applications/{application_id}/start-collaboration")
def start_collaboration(
    application_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in {"company", "academician", "admin"}:
        raise HTTPException(status_code=403, detail="Not authorized")
    application = db.query(FacultyOpportunityApplication).filter(FacultyOpportunityApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Faculty opportunity application not found")
    if user.role != "admin" and application.opportunity.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the opportunity owner can start the collaboration")
    if application.status != "Accepted":
        raise HTTPException(status_code=400, detail="Accept the faculty application before starting a collaboration")
    existing = db.query(Collaboration).filter(Collaboration.application_id == application.id).first()
    if existing:
        return collaboration_payload(existing)
    opportunity = application.opportunity
    collaboration = Collaboration(
        opportunity_id=opportunity.id, application_id=application.id, owner_id=opportunity.owner_id,
        academician_id=application.academician_id, title=opportunity.title,
        collaboration_type=opportunity.opportunity_type, ayush_focus=opportunity.ayush_focus,
        objective=opportunity.description, status="Planned",
    )
    db.add(collaboration)
    db.commit()
    db.refresh(collaboration)
    return collaboration_payload(collaboration)


@app.get("/collaborations")
def get_collaborations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in {"company", "academician", "admin"}:
        raise HTTPException(status_code=403, detail="Not authorized")
    q = db.query(Collaboration)
    if user.role != "admin":
        q = q.filter((Collaboration.owner_id == user.id) | (Collaboration.academician_id == user.id))
    return [collaboration_payload(x) for x in q.order_by(Collaboration.updated_at.desc()).all()]


@app.get("/collaborations/{collaboration_id}")
def get_collaboration(
    collaboration_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(Collaboration).filter(Collaboration.id == collaboration_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    if not _can_access_collaboration(item, user):
        raise HTTPException(status_code=403, detail="Not authorized")
    return collaboration_payload(item)


@app.patch("/collaborations/{collaboration_id}")
def update_collaboration(
    collaboration_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(Collaboration).filter(Collaboration.id == collaboration_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    if not _can_access_collaboration(item, user):
        raise HTTPException(status_code=403, detail="Not authorized")
    allowed_status = {"Planned", "Active", "On Hold", "Completed", "Cancelled"}
    if "status" in data:
        if data["status"] not in allowed_status:
            raise HTTPException(status_code=400, detail="Invalid collaboration status")
        item.status = data["status"]
        if item.status == "Completed":
            item.actual_end_date = datetime.utcnow()
    for field in ("title", "objective", "ayush_focus", "collaboration_type", "completion_summary"):
        if field in data:
            setattr(item, field, str(data[field] or ""))
    for field in ("start_date", "expected_end_date"):
        if field in data and data[field]:
            try:
                setattr(item, field, datetime.fromisoformat(str(data[field]).replace("Z", "+00:00")).replace(tzinfo=None))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid {field}")
    db.commit()
    db.refresh(item)
    return collaboration_payload(item)


@app.post("/collaborations/{collaboration_id}/milestones")
def add_collaboration_milestone(
    collaboration_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(Collaboration).filter(Collaboration.id == collaboration_id).first()
    if not item or not _can_access_collaboration(item, user):
        raise HTTPException(status_code=404, detail="Collaboration not found")
    title = str(data.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=422, detail="Milestone title is required")
    due_date = None
    if data.get("due_date"):
        try:
            due_date = datetime.fromisoformat(str(data["due_date"]).replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid due date")
    milestone = CollaborationMilestone(collaboration_id=item.id, title=title, description=str(data.get("description") or ""), due_date=due_date)
    db.add(milestone)
    db.commit()
    db.refresh(item)
    return collaboration_payload(item)


@app.patch("/collaboration-milestones/{milestone_id}")
def update_collaboration_milestone(
    milestone_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    milestone = db.query(CollaborationMilestone).filter(CollaborationMilestone.id == milestone_id).first()
    if not milestone or not _can_access_collaboration(milestone.collaboration, user):
        raise HTTPException(status_code=404, detail="Milestone not found")
    if "status" in data:
        if data["status"] not in {"Planned", "In Progress", "Completed", "Blocked"}:
            raise HTTPException(status_code=400, detail="Invalid milestone status")
        milestone.status = data["status"]
        milestone.completed_at = datetime.utcnow() if milestone.status == "Completed" else None
    if "title" in data:
        milestone.title = str(data["title"] or "")
    if "description" in data:
        milestone.description = str(data["description"] or "")
    db.commit()
    db.refresh(milestone.collaboration)
    return collaboration_payload(milestone.collaboration)


@app.post("/collaborations/{collaboration_id}/feedback")
def add_collaboration_feedback(
    collaboration_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(Collaboration).filter(Collaboration.id == collaboration_id).first()
    if not item or not _can_access_collaboration(item, user):
        raise HTTPException(status_code=404, detail="Collaboration not found")
    comments = str(data.get("comments") or "").strip()
    if not comments:
        raise HTTPException(status_code=422, detail="Feedback comments are required")
    feedback = CollaborationFeedback(collaboration_id=item.id, author_id=user.id, feedback_type=str(data.get("feedback_type") or "Progress"), comments=comments)
    db.add(feedback)
    db.commit()
    db.refresh(item)
    return collaboration_payload(item)


@app.post("/collaborations/{collaboration_id}/outputs")
def add_collaboration_output(
    collaboration_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(Collaboration).filter(Collaboration.id == collaboration_id).first()
    if not item or not _can_access_collaboration(item, user):
        raise HTTPException(status_code=404, detail="Collaboration not found")
    title = str(data.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=422, detail="Output title is required")
    output = CollaborationOutput(collaboration_id=item.id, title=title, output_type=str(data.get("output_type") or "Report"), description=str(data.get("description") or ""), url=str(data.get("url") or ""), verified=False)
    db.add(output)
    db.commit()
    db.refresh(item)
    return collaboration_payload(item)


@app.patch("/collaboration-outputs/{output_id}/verify")
def verify_collaboration_output(
    output_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    output = db.query(CollaborationOutput).filter(CollaborationOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    if user.role != "admin" and output.collaboration.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the collaboration owner or admin can verify outputs")
    output.verified = True
    db.commit()
    db.refresh(output.collaboration)
    return collaboration_payload(output.collaboration)


@app.get("/student/academic-record")
def get_student_academic_record(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access academic records")
    record = db.query(StudentAcademicRecord).filter(StudentAcademicRecord.user_id == user.id).first()
    return {"cgpa": record.cgpa if record else None}


@app.put("/student/academic-record")
def update_student_academic_record(
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can update academic records")
    raw = data.get("cgpa")
    cgpa = None if raw in (None, "") else float(raw)
    if cgpa is not None and not 0 <= cgpa <= 10:
        raise HTTPException(status_code=422, detail="CGPA must be between 0 and 10")
    record = db.query(StudentAcademicRecord).filter(StudentAcademicRecord.user_id == user.id).first()
    if not record:
        record = StudentAcademicRecord(user_id=user.id, cgpa=cgpa)
        db.add(record)
    else:
        record.cgpa = cgpa
    db.commit()
    return {"cgpa": record.cgpa}


@app.patch("/opportunities/{opportunity_id}/eligibility")
def update_opportunity_eligibility(
    opportunity_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if user.role != "admin" and opportunity.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    required_education = str(data.get("required_education") or "").strip()
    minimum_year = data.get("minimum_year")
    minimum_cgpa = data.get("minimum_cgpa")
    if minimum_year not in (None, ""):
        minimum_year = int(minimum_year)
        if minimum_year < 1 or minimum_year > 4:
            raise HTTPException(status_code=422, detail="Minimum year must be between 1 and 4")
    else:
        minimum_year = None
    if minimum_cgpa not in (None, ""):
        minimum_cgpa = float(minimum_cgpa)
        if minimum_cgpa < 0 or minimum_cgpa > 10:
            raise HTTPException(status_code=422, detail="Minimum CGPA must be between 0 and 10")
    else:
        minimum_cgpa = None

    record = db.query(OpportunityEligibility).filter(OpportunityEligibility.opportunity_id == opportunity.id).first()
    if not record:
        record = OpportunityEligibility(opportunity_id=opportunity.id)
        db.add(record)
    record.required_education = required_education
    record.minimum_year = minimum_year
    record.minimum_cgpa = minimum_cgpa
    record.eligibility_notes = str(data.get("eligibility_notes") or "").strip()
    db.commit()
    return {"opportunity_id": opportunity.id, **opportunity_eligibility_payload(db, opportunity)}


# ============================================================
# OPPORTUNITIES
# ============================================================

@app.post("/opportunities")
def create_opportunity(
    data: OpportunityIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in {
        "company",
        "admin",
        "academician",
    }:
        raise HTTPException(
            status_code=403,
            detail="Only organizations, academicians or admins can create opportunities",
        )

    opportunity = Opportunity(
        owner_id=user.id,
        title=data.title,
        description=data.description,
        opportunity_type=data.opportunity_type,
        location=data.location,
    )

    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)

    for requirement in data.requirements:

        skill = (
            db.query(Skill)
            .filter(
                Skill.id == requirement.skill_id
            )
            .first()
        )

        if not skill:
            continue

        db.add(
            OpportunitySkillRequirement(
                opportunity_id=opportunity.id,
                skill_id=skill.id,
                required_level=requirement.required_level,
            )
        )

    db.commit()

    return {
        "id": opportunity.id,
        "title": opportunity.title,
        "description": opportunity.description,
        "opportunity_type": opportunity.opportunity_type,
        "location": opportunity.location,
    }


@app.get("/opportunities")
def get_opportunities(
    db: Session = Depends(get_db),
):
    opportunities = (
        db.query(Opportunity)
        .filter(
            Opportunity.status == "Published"
        )
        .order_by(
            Opportunity.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": opportunity.id,
            "owner_id": opportunity.owner_id,
            "owner_role": opportunity.owner.role if opportunity.owner else None,
            "owner_name": (
                opportunity.owner.profile.name
                if opportunity.owner and opportunity.owner.profile and opportunity.owner.profile.name
                else (opportunity.owner.email if opportunity.owner else "")
            ),
            "title": opportunity.title,
            "description": opportunity.description,
            "opportunity_type": opportunity.opportunity_type,
            "location": opportunity.location,
            "status": opportunity.status,
            "created_at": opportunity.created_at,
            "eligibility": opportunity_eligibility_payload(db, opportunity),
            "requirements": [
                {
                    "skill_id": req.skill_id,
                    "skill": req.skill.name,
                    "required_level": req.required_level,
                }
                for req in opportunity.requirements
            ],
        }
        for opportunity in opportunities
    ]


# ============================================================
# COMPANY / ACADEMIC TALENT MATCHING
# ============================================================

@app.get("/opportunities/{opportunity_id}/matches")
def opportunity_matches(
    opportunity_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opportunity = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id)
        .first()
    )

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    if user.role not in {"admin", "company", "academician"} or (
        user.role != "admin" and opportunity.owner_id != user.id
    ):
        raise HTTPException(status_code=403, detail="Not authorized to view these matches")

    students = db.query(User).filter(User.role == "student").all()
    results = []

    for student in students:
        profile = profile_for(db, student)
        eligibility = evaluate_opportunity_eligibility(db, profile, opportunity)

        if opportunity.requirements:
            total_ratio = 0.0
            for comparison in eligibility["skill_comparisons"]:
                required = comparison["required"]
                current = comparison["current"]
                total_ratio += min(current / required, 1.0) if required else 1.0
            score = round(total_ratio / len(opportunity.requirements) * 100)
        else:
            score = 100

        results.append({
            "student_id": student.id,
            "name": profile.name or student.email,
            "email": student.email,
            "score": score,
            "match_percentage": score,
            "eligible": eligibility["eligible"],
            "eligibility_reasons": eligibility["reasons"],
            "readiness": calculate_readiness(db, profile),
            "matched_skills": eligibility["matched_skills"],
            "missing_skills": eligibility["missing_skills"],
            "skill_comparisons": eligibility["skill_comparisons"],
            "verified_skills": eligibility["verified_skill_count"],
        })

    results.sort(
        key=lambda x: (x["eligible"], x["score"], x["readiness"]),
        reverse=True,
    )
    return results


@app.get("/student/opportunities/{opportunity_id}/eligibility")
def student_opportunity_eligibility(
    opportunity_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can check eligibility")

    opportunity = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id)
        .first()
    )
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    profile = profile_for(db, user)
    result = evaluate_opportunity_eligibility(db, profile, opportunity)
    result.update({
        "opportunity_id": opportunity.id,
        "opportunity_title": opportunity.title,
        "opportunity_type": opportunity.opportunity_type,
    })
    return result


# ============================================================
# COMPANY / ACADEMIC APPLICATIONS
# ============================================================

@app.get("/applications")
def get_applications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Application).join(Opportunity)

    if user.role in {"company", "academician"}:
        query = query.filter(Opportunity.owner_id == user.id)
    elif user.role == "student":
        query = query.filter(Application.student_id == user.id)
    elif user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    applications = query.order_by(Application.created_at.desc()).all()

    return [
        {
            "id": application.id,
            "opportunity_id": application.opportunity_id,
            "opportunity_title": application.opportunity.title,
            "student_id": application.student_id,
            "student_email": application.student.email,
            "student_name": (
                application.student.profile.name
                if application.student.profile and application.student.profile.name
                else application.student.email
            ),
            "status": application.status,
            "created_at": application.created_at,
        }
        for application in applications
    ]


# ============================================================
# MATCHED OPPORTUNITIES
#
# Match is based on verified student skills.
# ============================================================

@app.get("/student/opportunities/matches")
def matched_opportunities(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view matched opportunities")

    profile = profile_for(db, user)
    opportunities = (
        db.query(Opportunity)
        .filter(Opportunity.status == "Published")
        .order_by(Opportunity.created_at.desc())
        .all()
    )

    matches = []

    for opportunity in opportunities:
        eligibility = evaluate_opportunity_eligibility(db, profile, opportunity)
        requirements = opportunity.requirements

        if requirements:
            total_ratio = sum(
                (
                    min(item["current"] / item["required"], 1.0)
                    if item["required"] else 1.0
                )
                for item in eligibility["skill_comparisons"]
            )
            match_percentage = round(total_ratio / len(requirements) * 100)
        else:
            match_percentage = 100

        matches.append({
            "id": opportunity.id,
            "title": opportunity.title,
            "description": opportunity.description,
            "opportunity_type": opportunity.opportunity_type,
            "location": opportunity.location,
            "match_percentage": match_percentage,
            "eligible": eligibility["eligible"],
            "eligibility_reasons": eligibility["reasons"],
            "academic_eligibility": eligibility["academic_eligibility"],
            "matched_skills": eligibility["matched_skills"],
            "missing_skills": eligibility["missing_skills"],
            "requirements": [
                {
                    **item,
                    "student_level": item.get("current", 0),
                    "required_level": item.get("required", 0),
                }
                for item in eligibility["skill_comparisons"]
            ],
        })

    matches.sort(
        key=lambda x: (x["eligible"], x["match_percentage"]),
        reverse=True,
    )
    return matches


# ============================================================
# APPLICATIONS
# ============================================================

@app.post("/opportunities/{opportunity_id}/apply")
def apply_opportunity(
    opportunity_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can apply")

    opportunity = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id)
        .first()
    )
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    eligibility = evaluate_opportunity_eligibility(
        db,
        profile_for(db, user),
        opportunity,
    )
    if not eligibility["eligible"]:
        missing = ", ".join(
            item["skill"] for item in eligibility["missing_skills"]
        )
        raise HTTPException(
            status_code=403,
            detail=f"Not currently eligible. Missing verified requirements: {missing}",
        )

    existing = (
        db.query(Application)
        .filter(
            Application.opportunity_id == opportunity_id,
            Application.student_id == user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already applied")

    application = Application(
        opportunity_id=opportunity_id,
        student_id=user.id,
        status="Applied",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "id": application.id,
        "status": application.status,
        "eligible": True,
    }


@app.get("/student/applications")
def get_student_applications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    applications = (
        db.query(Application)
        .filter(
            Application.student_id == user.id
        )
        .order_by(
            Application.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": application.id,
            "opportunity_id": application.opportunity_id,
            "title": application.opportunity.title,
            "company": (
                application.opportunity.owner.profile.name
                if application.opportunity.owner
                and application.opportunity.owner.profile
                else application.opportunity.owner.email
            ),
            "status": application.status,
            "created_at": application.created_at,
        }
        for application in applications
    ]


@app.patch("/applications/{application_id}")
def update_application_status(
    application_id: int,
    data: ApplicationStatusIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    opportunity = application.opportunity

    if (
        user.role != "admin"
        and opportunity.owner_id != user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized",
        )

    application.status = data.status

    db.commit()

    if application.status == "Selected":
        existing = db.query(InternshipRecord).filter(InternshipRecord.application_id == application.id).first()
        if not existing and (opportunity.opportunity_type or "").lower() in {"internship", "apprenticeship", "industrial training"}:
            existing = InternshipRecord(
                application_id=application.id,
                opportunity_id=application.opportunity_id,
                student_id=application.student_id,
                company_id=opportunity.owner_id,
                status="Not Started",
            )
            db.add(existing)
            db.commit()

    return {
        "id": application.id,
        "status": application.status,
        "internship_id": existing.id if 'existing' in locals() and existing else None,
    }


# ============================================================
# INSTITUTION / ADMIN ANALYTICS
# ============================================================

@app.get("/admin/users")
def admin_users(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return live user directory data for the institution admin portal."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view users")

    users = db.query(User).order_by(User.created_at.desc(), User.id.desc()).all()
    return [
        {
            "id": item.id,
            "email": item.email,
            "role": item.role,
            "name": (item.profile.name if item.profile and item.profile.name else ""),
            "created_at": item.created_at,
        }
        for item in users
    ]



@app.get("/admin/outcome-analytics")
def admin_outcome_analytics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return live outcome analytics across the AYUSH ecosystem."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view outcome analytics")

    internship_rows = db.query(InternshipRecord).all()
    internship_status = {}
    for row in internship_rows:
        status = row.status or "Not Started"
        internship_status[status] = internship_status.get(status, 0) + 1
    internship_avg_progress = (
        round(sum(max(0, min(100, row.progress_percent or 0)) for row in internship_rows) / len(internship_rows))
        if internship_rows else 0
    )
    internship_feedback_count = db.query(InternshipFeedback).count()
    internship_milestones = db.query(InternshipMilestone).all()
    completed_internship_milestones = sum(
        1 for row in internship_milestones if row.status == "Completed"
    )

    learning_programs = db.query(LearningProgram).all()
    learning_enrollments = db.query(LearningProgramEnrollment).all()
    learning_status = {}
    for row in learning_enrollments:
        status = row.status or "Enrolled"
        learning_status[status] = learning_status.get(status, 0) + 1

    collaborations = db.query(Collaboration).all()
    collaboration_status = {}
    for row in collaborations:
        status = row.status or "Planned"
        collaboration_status[status] = collaboration_status.get(status, 0) + 1
    collaboration_outputs = db.query(CollaborationOutput).all()
    collaboration_milestones = db.query(CollaborationMilestone).all()

    faculty_opportunities = db.query(FacultyOpportunity).all()
    faculty_applications = db.query(FacultyOpportunityApplication).all()
    faculty_application_status = {}
    for row in faculty_applications:
        status = row.status or "Applied"
        faculty_application_status[status] = faculty_application_status.get(status, 0) + 1

    documents = db.query(StudentDocument).all()
    document_status = {}
    for row in documents:
        status = row.verification_status or "Pending"
        document_status[status] = document_status.get(status, 0) + 1

    applications = db.query(Application).all()
    application_status = {}
    for row in applications:
        status = row.status or "Applied"
        application_status[status] = application_status.get(status, 0) + 1

    opportunity_type_counts = {}
    for row in db.query(Opportunity).all():
        key = row.opportunity_type or "Other"
        opportunity_type_counts[key] = opportunity_type_counts.get(key, 0) + 1

    learning_program_type_counts = {}
    for row in learning_programs:
        key = row.program_type or "Other"
        learning_program_type_counts[key] = learning_program_type_counts.get(key, 0) + 1

    faculty_type_counts = {}
    for row in faculty_opportunities:
        key = row.opportunity_type or "Other"
        faculty_type_counts[key] = faculty_type_counts.get(key, 0) + 1

    return {
        "internships": {
            "total": len(internship_rows),
            "not_started": internship_status.get("Not Started", 0),
            "ongoing": internship_status.get("Ongoing", 0),
            "completed": internship_status.get("Completed", 0),
            "cancelled": internship_status.get("Cancelled", 0),
            "average_progress": internship_avg_progress,
            "mentor_feedback": internship_feedback_count,
            "milestones": len(internship_milestones),
            "completed_milestones": completed_internship_milestones,
        },
        "learning_programs": {
            "programs": len(learning_programs),
            "enrollments": len(learning_enrollments),
            "enrolled": learning_status.get("Enrolled", 0),
            "in_progress": learning_status.get("In Progress", 0),
            "completed": learning_status.get("Completed", 0),
            "cancelled": learning_status.get("Cancelled", 0),
            "certificate_programs": sum(1 for row in learning_programs if row.certificate_available),
            "types": [
                {"type": key, "count": value}
                for key, value in sorted(
                    learning_program_type_counts.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ],
        },
        "collaborations": {
            "total": len(collaborations),
            "planned": collaboration_status.get("Planned", 0),
            "active": collaboration_status.get("Active", 0),
            "on_hold": collaboration_status.get("On Hold", 0),
            "completed": collaboration_status.get("Completed", 0),
            "cancelled": collaboration_status.get("Cancelled", 0),
            "milestones": len(collaboration_milestones),
            "completed_milestones": sum(
                1 for row in collaboration_milestones if row.status == "Completed"
            ),
            "outputs": len(collaboration_outputs),
            "verified_outputs": sum(1 for row in collaboration_outputs if row.verified),
        },
        "faculty_opportunities": {
            "total": len(faculty_opportunities),
            "applications": len(faculty_applications),
            "accepted": faculty_application_status.get("Accepted", 0),
            "under_review": faculty_application_status.get("Under Review", 0),
            "rejected": faculty_application_status.get("Rejected", 0),
            "types": [
                {"type": key, "count": value}
                for key, value in sorted(
                    faculty_type_counts.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ],
        },
        "documents": {
            "total": len(documents),
            "pending": document_status.get("Pending", 0),
            "verified": document_status.get("Verified", 0),
            "rejected": document_status.get("Rejected", 0),
        },
        "applications": {
            "total": len(applications),
            "applied": application_status.get("Applied", 0) + application_status.get("Submitted", 0),
            "under_review": application_status.get("Under Review", 0),
            "shortlisted": application_status.get("Shortlisted", 0),
            "selected": application_status.get("Selected", 0),
            "ongoing": application_status.get("Ongoing", 0),
            "done": application_status.get("Done", 0),
        },
        "opportunity_types": [
            {"type": key, "count": value}
            for key, value in sorted(
                opportunity_type_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    }


@app.get("/admin/analytics")
def admin_analytics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return live institution-level AYUSH analytics from the database."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view institution analytics")

    students = db.query(User).filter(User.role == "student").all()
    academicians = db.query(User).filter(User.role == "academician").count()
    companies = db.query(User).filter(User.role == "company").count()

    submitted_attempts = (
        db.query(AssessmentAttempt)
        .filter(AssessmentAttempt.status == "SUBMITTED")
        .all()
    )
    assessed_student_ids = {a.student_id for a in submitted_attempts}
    avg_assessment_score = (
        round(sum((a.score or 0) for a in submitted_attempts) / sum((a.total_questions or 0) for a in submitted_attempts) * 100)
        if submitted_attempts and sum((a.total_questions or 0) for a in submitted_attempts) > 0
        else 0
    )

    readiness_values = []
    for student in students:
        profile = profile_for(db, student)
        readiness_values.append(calculate_readiness(db, profile))
    avg_readiness = round(sum(readiness_values) / len(readiness_values)) if readiness_values else 0

    student_skills = db.query(StudentSkill).all()
    evidence_rows = db.query(Evidence).all()
    verified_skill_ids = set()
    pending_evidence = 0
    rejected_evidence = 0
    for ss in student_skills:
        entries = db.query(Evidence).filter(Evidence.student_skill_id == ss.id).all()
        kinds = {(e.kind or '').lower() for e in entries}
        if 'academic_verification' in kinds:
            verified_skill_ids.add(ss.id)
        if any(k == 'needs_more_evidence' for k in kinds):
            pending_evidence += 1
        elif any(k == 'academic_rejected' for k in kinds) and 'academic_verification' not in kinds:
            rejected_evidence += 1

    submitted_evidence = sum(
        1 for e in evidence_rows
        if (e.kind or '').lower() not in {'academic_verification', 'academic_rejected', 'needs_more_evidence'}
    )
    pending_verification = 0
    for ss in student_skills:
        entries = db.query(Evidence).filter(Evidence.student_skill_id == ss.id).all()
        submitted = any((e.kind or '').lower() not in {'academic_verification', 'academic_rejected', 'needs_more_evidence'} for e in entries)
        if submitted and ss.id not in verified_skill_ids and not any((e.kind or '').lower() == 'academic_rejected' for e in entries):
            pending_verification += 1

    opportunities = db.query(Opportunity).all()
    applications = db.query(Application).all()
    internship_opportunities = [o for o in opportunities if 'intern' in (o.opportunity_type or '').lower()]
    research_opportunities = [o for o in opportunities if 'research' in (o.opportunity_type or '').lower()]

    status_counts = {}
    for app_row in applications:
        status = app_row.status or 'Applied'
        status_counts[status] = status_counts.get(status, 0) + 1

    # Industry demand is derived from actual opportunity requirements.
    demand = {}
    for opportunity in opportunities:
        for req in opportunity.requirements:
            name = req.skill.name if req.skill else str(req.skill_id)
            demand[name] = demand.get(name, 0) + 1
    top_demand = [
        {'skill': name, 'requests': count}
        for name, count in sorted(demand.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]

    # Institutional core gaps are derived from each student's target-role requirements.
    gap_totals = {}
    gap_students = {}
    for student in students:
        profile = profile_for(db, student)
        if not profile.target_role:
            continue
        for req in profile.target_role.requirements:
            if req.category != 'Core':
                continue
            ss = get_student_skill(db, profile.id, req.skill_id)
            current = evidence_proficiency(db, ss) if ss else 0
            gap = max(req.required_level - current, 0)
            if gap > 0:
                name = req.skill.name
                gap_totals[name] = gap_totals.get(name, 0) + gap
                gap_students[name] = gap_students.get(name, 0) + 1
    top_gaps = [
        {'skill': name, 'average_gap': round(gap_totals[name] / gap_students[name]), 'students': gap_students[name]}
        for name in sorted(gap_totals, key=lambda n: (-gap_students[n], -gap_totals[n], n))[:10]
    ]

    return {
        'students': {
            'total': len(students),
            'assessed': len(assessed_student_ids),
            'unassessed': max(len(students) - len(assessed_student_ids), 0),
        },
        'faculty': academicians,
        'industry_partners': companies,
        'readiness': avg_readiness,
        'assessment': {
            'attempts': len(submitted_attempts),
            'average_score': avg_assessment_score,
        },
        'skills': {
            'total_assessed': len(student_skills),
            'verified': len(verified_skill_ids),
        },
        'evidence': {
            'submitted': submitted_evidence,
            'verified': len(verified_skill_ids),
            'pending': pending_verification,
            'rejected': rejected_evidence,
        },
        'opportunities': {
            'total': len(opportunities),
            'internships': len(internship_opportunities),
            'research': len(research_opportunities),
        },
        'applications': {
            'total': len(applications),
            'applied': status_counts.get('Applied', 0) + status_counts.get('Submitted', 0),
            'under_review': status_counts.get('Under Review', 0),
            'shortlisted': status_counts.get('Shortlisted', 0),
            'selected': status_counts.get('Selected', 0),
            'ongoing': status_counts.get('Ongoing', 0),
            'done': status_counts.get('Done', 0),
        },
        'industry_demand': top_demand,
        'skill_gaps': top_gaps,
    }


# ============================================================
# ACADEMICIAN - STUDENT DISCOVERY & VERIFICATION
# ============================================================

@app.get("/academician/students")
def academician_students(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return dynamic student profiles for academicians/admins."""

    if user.role not in {"academician", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only academicians or admins can view students",
        )

    students = (
        db.query(User)
        .filter(User.role == "student")
        .all()
    )

    results = []

    for student in students:
        profile = profile_for(db, student)

        verified_skill_items = []
        for item in profile.skills:
            proficiency = evidence_proficiency(db, item)
            if has_academic_verification(db, item):
                verified_skill_items.append({
                    "id": item.skill_id,
                    "skill": item.skill.name,
                    "proficiency": proficiency,
                    "category": item.skill.category,
                })

        core_gaps = []
        if profile.target_role:
            for req in profile.target_role.requirements:
                if req.category != "Core":
                    continue

                student_skill = get_student_skill(
                    db,
                    profile.id,
                    req.skill_id,
                )
                current = (
                    evidence_proficiency(db, student_skill)
                    if student_skill
                    else 0
                )
                gap = max(req.required_level - current, 0)

                if gap > 0:
                    core_gaps.append({
                        "skill_id": req.skill_id,
                        "skill": req.skill.name,
                        "current": current,
                        "required": req.required_level,
                        "gap": gap,
                    })

        core_gaps.sort(key=lambda item: item["gap"], reverse=True)

        results.append({
            "student_id": student.id,
            "name": profile.name or student.email,
            "email": student.email,
            "education": profile.education,
            "year_degree": profile.year_degree,
            "target_role": (
                profile.target_role.name
                if profile.target_role
                else None
            ),
            "career_interests": profile.career_interests,
            "research_experience": profile.research_experience,
            "achievements": profile.achievements,
            "readiness": calculate_readiness(db, profile),
            "verified_skills": verified_skill_items,
            "verified_skill_count": len(verified_skill_items),
            "core_gaps": core_gaps,
            "project_count": len(profile.projects),
            "certificate_count": len(profile.certificates),
            "course_count": len(profile.courses),
        })

    results.sort(
        key=lambda item: (
            item["readiness"],
            item["verified_skill_count"],
        ),
        reverse=True,
    )

    return results


@app.get("/academician/verification-queue")
def academician_verification_queue(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return student skills that have evidence awaiting academic review."""
    if user.role not in {"academician", "admin"}:
        raise HTTPException(status_code=403, detail="Only academicians or admins can view the verification queue")

    results = []
    students = db.query(User).filter(User.role == "student").all()
    for student in students:
        profile = profile_for(db, student)
        for student_skill in profile.skills:
            evidence = db.query(Evidence).filter(Evidence.student_skill_id == student_skill.id).all()
            submitted = [e for e in evidence if (e.kind or '').lower() not in {
                'academic_verification', 'academic_rejected', 'needs_more_evidence'
            }]
            if not submitted or has_academic_verification(db, student_skill):
                continue
            review_status = academic_review_status(db, student_skill)
            if review_status == "Rejected":
                continue
            results.append({
                "student_id": student.id,
                "student_name": profile.name or student.email,
                "student_email": student.email,
                "skill_id": student_skill.skill_id,
                "skill": student_skill.skill.name,
                "category": student_skill.skill.category,
                "proficiency": evidence_proficiency(db, student_skill),
                "status": review_status,
                "evidence": [
                    {"id": e.id, "kind": e.kind, "title": e.title, "url": e.url}
                    for e in submitted
                ],
            })
    return results


@app.get("/academician/students/{student_id}/portfolio")
def academician_student_portfolio(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a student's full portfolio for academic review."""

    if user.role not in {"academician", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only academicians or admins can view student portfolios",
        )

    student = (
        db.query(User)
        .filter(
            User.id == student_id,
            User.role == "student",
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    profile = profile_for(db, student)

    skills = []
    for item in profile.skills:
        evidence = (
            db.query(Evidence)
            .filter(Evidence.student_skill_id == item.id)
            .all()
        )

        academic_verified = any(
            (entry.kind or "").lower() == "academic_verification"
            for entry in evidence
        )

        skills.append({
            "id": item.id,
            "skill_id": item.skill_id,
            "skill": item.skill.name,
            "category": item.skill.category,
            "proficiency": evidence_proficiency(db, item),
            "verified": academic_verified,
            "academic_verified": academic_verified,
            "review_status": academic_review_status(db, item),
            "evidence": [
                {
                    "id": entry.id,
                    "kind": entry.kind,
                    "title": entry.title,
                    "url": entry.url,
                }
                for entry in evidence
            ],
        })

    return {
        "student": {
            "id": student.id,
            "email": student.email,
            "name": profile.name or student.email,
            "education": profile.education,
            "year_degree": profile.year_degree,
            "target_role": (
                profile.target_role.name
                if profile.target_role
                else None
            ),
            "career_interests": profile.career_interests,
            "research_experience": profile.research_experience,
            "achievements": profile.achievements,
            "readiness": calculate_readiness(db, profile),
        },
        "skills": skills,
        "projects": [
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "url": item.url,
            }
            for item in profile.projects
        ],
        "certificates": [
            {
                "id": item.id,
                "title": item.title,
                "issuer": item.issuer,
                "url": item.url,
            }
            for item in profile.certificates
        ],
        "courses": [
            {
                "id": item.id,
                "title": item.title,
                "provider": item.provider,
                "url": item.url,
            }
            for item in profile.courses
        ],
    }


@app.post("/academician/students/{student_id}/skills/{skill_id}/review")
def review_student_skill(
    student_id: int,
    skill_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record an academic review action without changing assessment proficiency."""
    if user.role not in {"academician", "admin"}:
        raise HTTPException(status_code=403, detail="Only academicians or admins can review student skills")

    action = str(data.get("action", "")).strip().lower()
    allowed = {"approve", "reject", "request_more_evidence"}
    if action not in allowed:
        raise HTTPException(status_code=400, detail="Action must be approve, reject, or request_more_evidence")

    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    profile = profile_for(db, student)
    student_skill = get_student_skill(db, profile.id, skill_id)
    if not student_skill:
        raise HTTPException(status_code=404, detail="Student does not have this skill")

    verifier_profile = profile_for(db, user)
    verifier_name = verifier_profile.name or user.email

    if action == "approve":
        submitted = db.query(Evidence).filter(
            Evidence.student_skill_id == student_skill.id,
            Evidence.kind.notin_(["academic_verification", "academic_rejected", "needs_more_evidence"]),
        ).all()
        if not any((entry.url or "").strip() for entry in submitted):
            raise HTTPException(status_code=400, detail="Approval requires submitted evidence with a link")

        existing = db.query(Evidence).filter(
            Evidence.student_skill_id == student_skill.id,
            Evidence.kind == "academic_verification",
        ).first()
        if not existing:
            db.add(Evidence(
                student_skill_id=student_skill.id,
                kind="academic_verification",
                title=f"Verified by {verifier_name}",
                url="",
            ))
        message = "Skill approved and academically verified."
    elif action == "reject":
        db.add(Evidence(
            student_skill_id=student_skill.id,
            kind="academic_rejected",
            title=f"Rejected by {verifier_name}",
            url="",
        ))
        message = "Skill evidence marked as rejected."
    else:
        db.add(Evidence(
            student_skill_id=student_skill.id,
            kind="needs_more_evidence",
            title=f"More evidence requested by {verifier_name}",
            url="",
        ))
        message = "More evidence requested from the student."

    db.commit()
    return {
        "message": message,
        "skill_id": skill_id,
        "proficiency": evidence_proficiency(db, student_skill),
        "status": academic_review_status(db, student_skill),
        "verified": has_academic_verification(db, student_skill),
        "academic_verified": has_academic_verification(db, student_skill),
    }


@app.post("/academician/students/{student_id}/skills/{skill_id}/verify")
def verify_student_skill_by_academician(
    student_id: int,
    skill_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Academician/admin verification of an existing student skill.

    Verification is stored as a distinct evidence record so it becomes part
    of the same evidence-based proficiency calculation used everywhere else.
    """

    if user.role not in {"academician", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only academicians or admins can verify student skills",
        )

    student = (
        db.query(User)
        .filter(
            User.id == student_id,
            User.role == "student",
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    profile = profile_for(db, student)
    student_skill = get_student_skill(
        db,
        profile.id,
        skill_id,
    )

    if not student_skill:
        raise HTTPException(
            status_code=404,
            detail="Student does not have this skill",
        )

    existing = (
        db.query(Evidence)
        .filter(
            Evidence.student_skill_id == student_skill.id,
            Evidence.kind == "academic_verification",
        )
        .first()
    )

    if existing:
        return {
            "message": "Skill already verified by an academician",
            "skill_id": skill_id,
            "proficiency": evidence_proficiency(db, student_skill),
            "verified": True,
            "academic_verified": True,
        }

    verifier_profile = profile_for(db, user)
    verifier_name = verifier_profile.name or user.email

    verification = Evidence(
        student_skill_id=student_skill.id,
        kind="academic_verification",
        title=f"Verified by {verifier_name}",
        url="",
    )

    db.add(verification)
    db.commit()
    db.refresh(verification)

    return {
        "message": "Skill verified by academician",
        "id": verification.id,
        "skill_id": skill_id,
        "skill": student_skill.skill.name,
        "proficiency": evidence_proficiency(db, student_skill),
        "verified": True,
        "academic_verified": True,
        "verified_by": verifier_name,
    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/student/dashboard")
def student_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = profile_for(db, user)

    verified_skills = sum(
        1
        for skill in profile.skills
        if has_academic_verification(db, skill)
    )

    projects = len(profile.projects)
    certificates = len(profile.certificates)
    courses = len(profile.courses)

    gap = skill_gap(
        user=user,
        db=db,
    )

    return {
        "target_role": gap["target_role"],
        "readiness": gap["readiness"],
        "active_gaps": gap["active_gaps"],
        "verified_skills": verified_skills,
        "projects": projects,
        "certificates": certificates,
        "courses": courses,
    }