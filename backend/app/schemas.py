from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional

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

class ProfileIn(BaseModel):
    name: str = ""
    education: str = ""
    year_degree: str = ""
    target_role_id: Optional[int] = None
    career_interests: str = ""
    research_experience: str = ""
    achievements: str = ""

class SkillIn(BaseModel):
    skill_id: int
    # Students do not self-rate skills. The backend derives proficiency
    # from evidence, so this field defaults to 0 and is ignored on create.
    proficiency: int = Field(default=0, ge=0, le=100)

class EvidenceIn(BaseModel):
    kind: str
    title: str
    url: str = ""

class ItemIn(BaseModel):
    title: str
    description: str = ""
    issuer: str = ""
    provider: str = ""
    url: str = ""

class RequirementIn(BaseModel):
    skill_id: int
    required_level: int = Field(ge=0, le=100)

class OpportunityIn(BaseModel):
    title: str
    description: str = ""
    opportunity_type: str = "Internship"
    location: str = "Remote"
    requirements: list[RequirementIn] = []

class ApplicationStatusIn(BaseModel):
    status: str
