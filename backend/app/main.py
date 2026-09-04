from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
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
    Application,
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
)
from .security import (
    hash_password,
    verify_password,
    create_token,
)


app = FastAPI(title="SkillNova API")


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
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

SEED_ROLES = {

    "Data Scientist": [
        # CORE
        ("Python", 90, "Core", None),
        ("Statistics", 90, "Core", None),
        ("Data Analysis", 90, "Core", None),
        ("Machine Learning", 85, "Core", None),
        ("SQL", 80, "Core", None),

        # RECOMMENDED
        ("Pandas", 80, "Recommended", None),
        ("NumPy", 80, "Recommended", None),
        ("Scikit-learn", 80, "Recommended", None),
        ("Data Visualization", 75, "Recommended", None),
        ("Git", 70, "Recommended", None),

        # ALTERNATIVES
        ("R", 75, "Alternative", "Python"),
        ("Julia", 65, "Alternative", "Python"),
        ("Spark", 70, "Alternative", "Pandas"),

        # ADVANCED
        ("Deep Learning", 75, "Advanced/Optional", None),
        ("TensorFlow", 70, "Advanced/Optional", None),
        ("PyTorch", 70, "Advanced/Optional", None),
        ("MLOps", 65, "Advanced/Optional", None),
        ("Cloud Computing", 65, "Advanced/Optional", None),
    ],

    "Data Analyst": [
        # CORE
        ("SQL", 85, "Core", None),
        ("Excel", 85, "Core", None),
        ("Data Analysis", 85, "Core", None),
        ("Statistics", 75, "Core", None),
        ("Data Visualization", 80, "Core", None),

        # RECOMMENDED
        ("Python", 70, "Recommended", None),
        ("Pandas", 70, "Recommended", None),
        ("Power BI", 75, "Recommended", None),
        ("Tableau", 75, "Recommended", None),
        ("Git", 60, "Recommended", None),

        # ALTERNATIVES
        ("R", 70, "Alternative", "Python"),
        ("Looker", 65, "Alternative", "Power BI"),
        ("Qlik Sense", 65, "Alternative", "Power BI"),

        # ADVANCED
        ("Machine Learning", 65, "Advanced/Optional", None),
        ("Cloud Computing", 60, "Advanced/Optional", None),
        ("dbt", 60, "Advanced/Optional", None),
    ],

    "Machine Learning Engineer": [
        # CORE
        ("Python", 90, "Core", None),
        ("Machine Learning", 90, "Core", None),
        ("Data Structures", 80, "Core", None),
        ("SQL", 75, "Core", None),
        ("Git", 80, "Core", None),

        # RECOMMENDED
        ("Scikit-learn", 85, "Recommended", None),
        ("NumPy", 80, "Recommended", None),
        ("Pandas", 80, "Recommended", None),
        ("Docker", 75, "Recommended", None),
        ("REST APIs", 70, "Recommended", None),

        # ALTERNATIVES
        ("TensorFlow", 80, "Alternative", "PyTorch"),
        ("PyTorch", 80, "Alternative", "TensorFlow"),
        ("XGBoost", 75, "Alternative", "Scikit-learn"),

        # ADVANCED
        ("Deep Learning", 85, "Advanced/Optional", None),
        ("MLOps", 80, "Advanced/Optional", None),
        ("Kubernetes", 70, "Advanced/Optional", None),
        ("Cloud Computing", 75, "Advanced/Optional", None),
    ],

    "AI/ML Engineer": [
        # CORE
        ("Python", 90, "Core", None),
        ("Machine Learning", 90, "Core", None),
        ("Deep Learning", 85, "Core", None),
        ("Data Structures", 80, "Core", None),
        ("Git", 80, "Core", None),

        # RECOMMENDED
        ("PyTorch", 80, "Recommended", None),
        ("TensorFlow", 80, "Recommended", None),
        ("NumPy", 80, "Recommended", None),
        ("Pandas", 75, "Recommended", None),
        ("Scikit-learn", 80, "Recommended", None),

        # ALTERNATIVES
        ("Keras", 70, "Alternative", "TensorFlow"),
        ("JAX", 65, "Alternative", "PyTorch"),
        ("XGBoost", 70, "Alternative", "Scikit-learn"),

        # ADVANCED
        ("MLOps", 80, "Advanced/Optional", None),
        ("NLP", 75, "Advanced/Optional", None),
        ("Computer Vision", 75, "Advanced/Optional", None),
        ("Generative AI", 80, "Advanced/Optional", None),
        ("Cloud Computing", 70, "Advanced/Optional", None),
    ],

    "Software Engineer": [
        # CORE
        ("Programming", 90, "Core", None),
        ("Data Structures", 85, "Core", None),
        ("Algorithms", 85, "Core", None),
        ("Git", 80, "Core", None),
        ("Software Engineering", 85, "Core", None),

        # RECOMMENDED
        ("Python", 75, "Recommended", None),
        ("Java", 75, "Recommended", None),
        ("JavaScript", 75, "Recommended", None),
        ("SQL", 70, "Recommended", None),
        ("REST APIs", 70, "Recommended", None),

        # ALTERNATIVES
        ("C++", 75, "Alternative", "Java"),
        ("C#", 70, "Alternative", "Java"),
        ("Go", 70, "Alternative", "Java"),

        # ADVANCED
        ("System Design", 80, "Advanced/Optional", None),
        ("Docker", 70, "Advanced/Optional", None),
        ("Cloud Computing", 70, "Advanced/Optional", None),
        ("Kubernetes", 65, "Advanced/Optional", None),
    ],

    "Full Stack Developer": [
        # CORE
        ("HTML/CSS", 85, "Core", None),
        ("JavaScript", 90, "Core", None),
        ("React", 85, "Core", None),
        ("Node.js", 80, "Core", None),
        ("SQL", 75, "Core", None),
        ("Git", 80, "Core", None),

        # RECOMMENDED
        ("TypeScript", 80, "Recommended", None),
        ("REST APIs", 80, "Recommended", None),
        ("Express.js", 75, "Recommended", None),
        ("PostgreSQL", 70, "Recommended", None),
        ("MongoDB", 70, "Recommended", None),

        # ALTERNATIVES
        ("Angular", 75, "Alternative", "React"),
        ("Vue.js", 75, "Alternative", "React"),
        ("Django", 70, "Alternative", "Node.js"),
        ("Spring Boot", 70, "Alternative", "Node.js"),

        # ADVANCED
        ("Next.js", 75, "Advanced/Optional", None),
        ("Docker", 70, "Advanced/Optional", None),
        ("Cloud Computing", 70, "Advanced/Optional", None),
        ("Redis", 65, "Advanced/Optional", None),
        ("GraphQL", 65, "Advanced/Optional", None),
    ],

    "Frontend Developer": [
        # CORE
        ("HTML", 90, "Core", None),
        ("CSS", 90, "Core", None),
        ("JavaScript", 90, "Core", None),
        ("TypeScript", 80, "Core", None),
        ("React", 85, "Core", None),
        ("Git", 75, "Core", None),

        # RECOMMENDED
        ("Responsive Design", 80, "Recommended", None),
        ("REST APIs", 75, "Recommended", None),
        ("Accessibility", 70, "Recommended", None),
        ("Testing", 70, "Recommended", None),
        ("npm", 70, "Recommended", None),

        # ALTERNATIVES
        ("Angular", 80, "Alternative", "React"),
        ("Vue.js", 80, "Alternative", "React"),
        ("Svelte", 70, "Alternative", "React"),

        # ADVANCED
        ("Next.js", 80, "Advanced/Optional", None),
        ("Redux", 70, "Advanced/Optional", None),
        ("Tailwind CSS", 70, "Advanced/Optional", None),
        ("Webpack", 65, "Advanced/Optional", None),
        ("Vite", 70, "Advanced/Optional", None),
        ("Jest", 65, "Advanced/Optional", None),
        ("Cypress", 65, "Advanced/Optional", None),
    ],

    "Backend Developer": [
        # CORE
        ("Python", 85, "Core", None),
        ("SQL", 85, "Core", None),
        ("REST APIs", 85, "Core", None),
        ("Git", 80, "Core", None),
        ("Data Structures", 75, "Core", None),

        # RECOMMENDED
        ("FastAPI", 75, "Recommended", None),
        ("Django", 75, "Recommended", None),
        ("PostgreSQL", 80, "Recommended", None),
        ("Docker", 70, "Recommended", None),
        ("Authentication", 75, "Recommended", None),

        # ALTERNATIVES
        ("Node.js", 80, "Alternative", "Python"),
        ("Java", 75, "Alternative", "Python"),
        ("Spring Boot", 70, "Alternative", "Django"),

        # ADVANCED
        ("Redis", 65, "Advanced/Optional", None),
        ("Kafka", 65, "Advanced/Optional", None),
        ("Kubernetes", 65, "Advanced/Optional", None),
        ("Cloud Computing", 70, "Advanced/Optional", None),
        ("System Design", 75, "Advanced/Optional", None),
    ],

    "Cloud / DevOps Engineer": [
        # CORE
        ("Linux", 85, "Core", None),
        ("Networking", 80, "Core", None),
        ("Docker", 85, "Core", None),
        ("Cloud Computing", 85, "Core", None),
        ("Git", 80, "Core", None),

        # RECOMMENDED
        ("Kubernetes", 80, "Recommended", None),
        ("CI/CD", 80, "Recommended", None),
        ("Terraform", 75, "Recommended", None),
        ("Python", 70, "Recommended", None),
        ("Bash", 75, "Recommended", None),

        # ALTERNATIVES
        ("AWS", 80, "Alternative", "Cloud Computing"),
        ("Azure", 80, "Alternative", "Cloud Computing"),
        ("Google Cloud", 80, "Alternative", "Cloud Computing"),

        # ADVANCED
        ("Ansible", 65, "Advanced/Optional", None),
        ("Prometheus", 65, "Advanced/Optional", None),
        ("Grafana", 65, "Advanced/Optional", None),
        ("Service Mesh", 60, "Advanced/Optional", None),
    ],

    "Cybersecurity Analyst": [
        # CORE
        ("Networking", 85, "Core", None),
        ("Linux", 80, "Core", None),
        ("Cybersecurity", 90, "Core", None),
        ("Security Fundamentals", 85, "Core", None),
        ("Python", 70, "Core", None),

        # RECOMMENDED
        ("Wireshark", 75, "Recommended", None),
        ("SIEM", 75, "Recommended", None),
        ("Incident Response", 75, "Recommended", None),
        ("Firewalls", 70, "Recommended", None),
        ("Git", 60, "Recommended", None),

        # ALTERNATIVES
        ("Splunk", 75, "Alternative", "SIEM"),
        ("ELK Stack", 70, "Alternative", "SIEM"),
        ("Microsoft Sentinel", 70, "Alternative", "SIEM"),

        # ADVANCED
        ("Ethical Hacking", 75, "Advanced/Optional", None),
        ("Penetration Testing", 75, "Advanced/Optional", None),
        ("Cloud Security", 70, "Advanced/Optional", None),
        ("Digital Forensics", 65, "Advanced/Optional", None),
    ],

    "Product Analyst": [
        # CORE
        ("SQL", 85, "Core", None),
        ("Data Analysis", 85, "Core", None),
        ("Statistics", 75, "Core", None),
        ("Excel", 80, "Core", None),
        ("Data Visualization", 75, "Core", None),

        # RECOMMENDED
        ("Python", 65, "Recommended", None),
        ("Product Analytics", 80, "Recommended", None),
        ("A/B Testing", 75, "Recommended", None),
        ("Power BI", 70, "Recommended", None),
        ("Tableau", 70, "Recommended", None),

        # ALTERNATIVES
        ("R", 65, "Alternative", "Python"),
        ("Looker", 65, "Alternative", "Power BI"),

        # ADVANCED
        ("Machine Learning", 60, "Advanced/Optional", None),
        ("Mixpanel", 65, "Advanced/Optional", None),
        ("Amplitude", 65, "Advanced/Optional", None),
    ],

    "Bioinformatics Analyst": [
        # CORE
        ("Python", 85, "Core", None),
        ("Statistics", 75, "Core", None),
        ("Data Analysis", 85, "Core", None),
        ("Bioinformatics", 90, "Core", None),
        ("Biology", 80, "Core", None),

        # RECOMMENDED
        ("Pandas", 75, "Recommended", None),
        ("NumPy", 70, "Recommended", None),
        ("R", 75, "Recommended", None),
        ("SQL", 65, "Recommended", None),
        ("Linux", 65, "Recommended", None),

        # ALTERNATIVES
        ("Bioconductor", 75, "Alternative", "R"),
        ("Biopython", 75, "Alternative", "Python"),

        # ADVANCED
        ("Machine Learning", 70, "Advanced/Optional", None),
        ("Genomics", 75, "Advanced/Optional", None),
        ("Data Visualization", 70, "Advanced/Optional", None),
    ],

    "Research Assistant": [
        # CORE
        ("Research Methods", 85, "Core", None),
        ("Data Analysis", 75, "Core", None),
        ("Statistics", 75, "Core", None),
        ("Scientific Writing", 80, "Core", None),
        ("Literature Review", 80, "Core", None),

        # RECOMMENDED
        ("Python", 70, "Recommended", None),
        ("Excel", 70, "Recommended", None),
        ("Data Visualization", 65, "Recommended", None),
        ("Git", 55, "Recommended", None),

        # ALTERNATIVES
        ("R", 70, "Alternative", "Python"),
        ("MATLAB", 70, "Alternative", "Python"),

        # ADVANCED
        ("Machine Learning", 60, "Advanced/Optional", None),
        ("LaTeX", 65, "Advanced/Optional", None),
        ("Academic Publishing", 70, "Advanced/Optional", None),
    ],

    "Computational Chemistry Researcher": [
        # CORE
        ("Chemistry", 90, "Core", None),
        ("Python", 75, "Core", None),
        ("Data Analysis", 70, "Core", None),
        ("Research Methods", 80, "Core", None),
        ("Scientific Computing", 75, "Core", None),

        # RECOMMENDED
        ("Machine Learning", 70, "Recommended", None),
        ("Statistics", 65, "Recommended", None),
        ("Linux", 65, "Recommended", None),
        ("NumPy", 65, "Recommended", None),
        ("Pandas", 65, "Recommended", None),

        # ALTERNATIVES
        ("MATLAB", 70, "Alternative", "Python"),
        ("R", 60, "Alternative", "Python"),

        # ADVANCED
        ("Molecular Modeling", 80, "Advanced/Optional", None),
        ("Deep Learning", 65, "Advanced/Optional", None),
        ("Quantum Chemistry", 80, "Advanced/Optional", None),
        ("High Performance Computing", 65, "Advanced/Optional", None),
    ],

    "AI Research Intern": [
        # CORE
        ("Python", 85, "Core", None),
        ("Machine Learning", 85, "Core", None),
        ("Data Analysis", 75, "Core", None),
        ("Statistics", 75, "Core", None),
        ("Research Methods", 80, "Core", None),

        # RECOMMENDED
        ("Deep Learning", 80, "Recommended", None),
        ("PyTorch", 80, "Recommended", None),
        ("NumPy", 75, "Recommended", None),
        ("Git", 70, "Recommended", None),
        ("Scientific Writing", 70, "Recommended", None),

        # ALTERNATIVES
        ("TensorFlow", 75, "Alternative", "PyTorch"),
        ("JAX", 65, "Alternative", "PyTorch"),

        # ADVANCED
        ("NLP", 75, "Advanced/Optional", None),
        ("Computer Vision", 75, "Advanced/Optional", None),
        ("Generative AI", 80, "Advanced/Optional", None),
        ("Reinforcement Learning", 70, "Advanced/Optional", None),
    ],
}


# ============================================================
# BASIC SKILL SEED LIST
# ============================================================

SEED_SKILLS = [
    ("Python", "Programming"),
    ("Java", "Programming"),
    ("JavaScript", "Programming"),
    ("TypeScript", "Programming"),
    ("C++", "Programming"),
    ("C#", "Programming"),
    ("Go", "Programming"),
    ("R", "Programming"),
    ("Julia", "Programming"),
    ("HTML", "Frontend"),
    ("CSS", "Frontend"),
    ("HTML/CSS", "Frontend"),
    ("React", "Frontend"),
    ("Angular", "Frontend"),
    ("Vue.js", "Frontend"),
    ("Svelte", "Frontend"),
    ("Next.js", "Frontend"),
    ("Redux", "Frontend"),
    ("Tailwind CSS", "Frontend"),
    ("Responsive Design", "Frontend"),
    ("Accessibility", "Frontend"),
    ("Testing", "Frontend"),
    ("Jest", "Frontend"),
    ("Cypress", "Frontend"),
    ("Webpack", "Frontend"),
    ("Vite", "Frontend"),
    ("npm", "Frontend"),
    ("Node.js", "Backend"),
    ("Express.js", "Backend"),
    ("Django", "Backend"),
    ("FastAPI", "Backend"),
    ("Spring Boot", "Backend"),
    ("REST APIs", "Backend"),
    ("GraphQL", "Backend"),
    ("Authentication", "Backend"),
    ("SQL", "Data"),
    ("PostgreSQL", "Data"),
    ("MongoDB", "Data"),
    ("Redis", "Data"),
    ("Excel", "Data"),
    ("Pandas", "Data"),
    ("NumPy", "Data"),
    ("Data Analysis", "Data"),
    ("Data Visualization", "Data"),
    ("Statistics", "Data"),
    ("Power BI", "Data"),
    ("Tableau", "Data"),
    ("Looker", "Data"),
    ("Qlik Sense", "Data"),
    ("Product Analytics", "Data"),
    ("A/B Testing", "Data"),
    ("Machine Learning", "AI/ML"),
    ("Deep Learning", "AI/ML"),
    ("Scikit-learn", "AI/ML"),
    ("TensorFlow", "AI/ML"),
    ("PyTorch", "AI/ML"),
    ("Keras", "AI/ML"),
    ("JAX", "AI/ML"),
    ("XGBoost", "AI/ML"),
    ("NLP", "AI/ML"),
    ("Computer Vision", "AI/ML"),
    ("Generative AI", "AI/ML"),
    ("Reinforcement Learning", "AI/ML"),
    ("MLOps", "AI/ML"),
    ("Git", "Tools"),
    ("Docker", "Cloud"),
    ("Kubernetes", "Cloud"),
    ("Cloud Computing", "Cloud"),
    ("AWS", "Cloud"),
    ("Azure", "Cloud"),
    ("Google Cloud", "Cloud"),
    ("Linux", "Cloud"),
    ("Bash", "Cloud"),
    ("Terraform", "Cloud"),
    ("CI/CD", "Cloud"),
    ("Ansible", "Cloud"),
    ("Prometheus", "Cloud"),
    ("Grafana", "Cloud"),
    ("Networking", "Cybersecurity"),
    ("Cybersecurity", "Cybersecurity"),
    ("Security Fundamentals", "Cybersecurity"),
    ("Wireshark", "Cybersecurity"),
    ("SIEM", "Cybersecurity"),
    ("Splunk", "Cybersecurity"),
    ("ELK Stack", "Cybersecurity"),
    ("Microsoft Sentinel", "Cybersecurity"),
    ("Firewalls", "Cybersecurity"),
    ("Incident Response", "Cybersecurity"),
    ("Ethical Hacking", "Cybersecurity"),
    ("Penetration Testing", "Cybersecurity"),
    ("Cloud Security", "Cybersecurity"),
    ("Digital Forensics", "Cybersecurity"),
    ("Programming", "Programming"),
    ("Data Structures", "Computer Science"),
    ("Algorithms", "Computer Science"),
    ("Software Engineering", "Software Engineering"),
    ("System Design", "Software Engineering"),
    ("Research Methods", "Research"),
    ("Scientific Writing", "Research"),
    ("Literature Review", "Research"),
    ("Academic Publishing", "Research"),
    ("Scientific Computing", "Research"),
    ("Chemistry", "Science"),
    ("Biology", "Science"),
    ("Bioinformatics", "Science"),
    ("Bioconductor", "Science"),
    ("Biopython", "Science"),
    ("Genomics", "Science"),
    ("Molecular Modeling", "Science"),
    ("Quantum Chemistry", "Science"),
    ("High Performance Computing", "Science"),
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


def evidence_proficiency(
    db: Session,
    student_skill: StudentSkill,
):
    """
    Evidence-based proficiency.

    The student does NOT enter a proficiency percentage.

    For MVP:
        at least one evidence item -> verified skill

    A future version can use stronger verification signals,
    but the student is never asked to self-rate.
    """

    count = (
        db.query(Evidence)
        .filter(
            Evidence.student_skill_id == student_skill.id
        )
        .count()
    )

    if count > 0:
        return 100

    return 0


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

        proficiency = evidence_proficiency(
            db,
            student_skill,
        )

        result.append(
            {
                "id": student_skill.id,
                "skill_id": student_skill.skill_id,
                "skill": student_skill.skill.name,
                "category": student_skill.skill.category,
                "proficiency": proficiency,
                "verified": proficiency > 0,
                "evidence_count": (
                    db.query(Evidence)
                    .filter(
                        Evidence.student_skill_id
                        == student_skill.id
                    )
                    .count()
                ),
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
        "message": "Skill added. Add evidence to verify it.",
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

    # Evidence verifies the skill.
    student_skill.proficiency = 100

    db.commit()
    db.refresh(evidence)

    return {
        "message": "Evidence added and skill verified",
        "id": evidence.id,
        "proficiency": 100,
        "verified": True,
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
            "verified": current > 0,
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
            "proficiency": evidence_proficiency(
                db,
                item,
            ),
            "verified": evidence_proficiency(
                db,
                item,
            ) > 0,
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

    if user.role != "admin" and opportunity.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these matches")

    students = db.query(User).filter(User.role == "student").all()
    results = []

    for student in students:
        profile = profile_for(db, student)
        verified = {
            item.skill_id: evidence_proficiency(db, item)
            for item in profile.skills
        }

        matched_skills = []
        missing_skills = []
        total_ratio = 0.0

        requirements = opportunity.requirements
        if not requirements:
            score = 100
        else:
            for req in requirements:
                current = verified.get(req.skill_id, 0)
                required = req.required_level
                ratio = 1.0 if required == 0 and current >= 0 else min(current / required, 1.0) if required else 1.0
                total_ratio += ratio
                if current >= required:
                    matched_skills.append(req.skill.name)
                else:
                    missing_skills.append({
                        "skill": req.skill.name,
                        "current": current,
                        "required": required,
                        "gap": max(required - current, 0),
                    })
            score = round(total_ratio / len(requirements) * 100)

        results.append({
            "student_id": student.id,
            "name": profile.name or student.email,
            "email": student.email,
            "score": score,
            "readiness": calculate_readiness(db, profile),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "verified_skills": len([x for x in profile.skills if evidence_proficiency(db, x) > 0]),
        })

    results.sort(key=lambda x: (x["score"], x["readiness"]), reverse=True)
    return results


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
    profile = profile_for(db, user)

    student_skills = {
        item.skill_id: evidence_proficiency(
            db,
            item,
        )
        for item in profile.skills
    }

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

    matches = []

    for opportunity in opportunities:

        requirements = opportunity.requirements

        if not requirements:
            match_percentage = 100
        else:
            matched = 0

            for req in requirements:
                current = student_skills.get(
                    req.skill_id,
                    0,
                )

                if current >= req.required_level:
                    matched += 1

            match_percentage = round(
                matched
                / len(requirements)
                * 100
            )

        matches.append(
            {
                "id": opportunity.id,
                "title": opportunity.title,
                "description": opportunity.description,
                "opportunity_type": opportunity.opportunity_type,
                "location": opportunity.location,
                "match_percentage": match_percentage,
                "requirements": [
                    {
                        "skill": req.skill.name,
                        "required_level": req.required_level,
                        "student_level": student_skills.get(
                            req.skill_id,
                            0,
                        ),
                    }
                    for req in requirements
                ],
            }
        )

    matches.sort(
        key=lambda x: x["match_percentage"],
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
        raise HTTPException(
            status_code=403,
            detail="Only students can apply",
        )

    opportunity = (
        db.query(Opportunity)
        .filter(
            Opportunity.id == opportunity_id
        )
        .first()
    )

    if not opportunity:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found",
        )

    existing = (
        db.query(Application)
        .filter(
            Application.opportunity_id
            == opportunity_id,
            Application.student_id
            == user.id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Already applied",
        )

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

    return {
        "id": application.id,
        "status": application.status,
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
            if proficiency > 0:
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
            "verified": evidence_proficiency(db, item) > 0,
            "academic_verified": academic_verified,
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

    # Academic verification is an evidence signal, so it contributes
    # to the same 100% verified proficiency used by the MVP.
    student_skill.proficiency = 100

    db.commit()
    db.refresh(verification)

    return {
        "message": "Skill verified by academician",
        "id": verification.id,
        "skill_id": skill_id,
        "skill": student_skill.skill.name,
        "proficiency": 100,
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
        if evidence_proficiency(
            db,
            skill,
        ) > 0
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