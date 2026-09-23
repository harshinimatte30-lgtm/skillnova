"""
SkillNova Student Assessment System

MCQ-only, role-specific assessment engine.

Features:
- Technical, Soft Skills and Aptitude MCQs
- Role-specific assessment
- One attempt per student per role/year/test-type/difficulty configuration
- Correct answers are never exposed before submission
- Server-side grading
- Skill-level results
- Student-facing categorical statuses:
    Strong
    Developing
    Needs Improvement
    Not Assessed
- Numeric scores are retained internally for calculations.
"""

from datetime import datetime
from typing import Any, Optional
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import (
    User,
    Profile,
    Skill,
    StudentSkill,
    Assessment,
    AssessmentQuestion,
    AssessmentAttempt,
    AssessmentResponse,
    SkillAssessmentResult,
)
from ..security import decode_token

def _normalise_skill_name(name: str) -> str:
    """Return a consistent form of a skill name for comparisons."""
    return " ".join(name.strip().lower().split())


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/student/assessment",
    tags=["Student Assessment"],
)


# ============================================================
# STUDENT-FACING STATUS VALUES
# ============================================================

STRONG = "Strong"
DEVELOPING = "Developing"
NEEDS_IMPROVEMENT = "Needs Improvement"
NOT_ASSESSED = "Not Assessed"


# ============================================================
# INTERNAL ASSESSMENT STATUS VALUES
# ============================================================

ATTEMPT_IN_PROGRESS = "IN_PROGRESS"
ATTEMPT_SUBMITTED = "SUBMITTED"


# ============================================================
# ASSESSMENT CATEGORIES
# ============================================================

TECHNICAL = "Technical"
SOFT_SKILLS = "Soft Skills"
APTITUDE = "Aptitude"

VALID_CATEGORIES = {
    TECHNICAL,
    SOFT_SKILLS,
    APTITUDE,
}


# ============================================================
# SCORE / STATUS HELPERS
# ============================================================

def calculate_percentage(
    score: int,
    total_questions: int,
) -> int:
    """
    Calculate an internal percentage.

    Numeric percentage is used internally for calculations.
    Student-facing UI should prefer the categorical status.
    """

    if total_questions <= 0:
        return 0

    score = max(0, min(score, total_questions))

    return round(
        (score / total_questions) * 100
    )


def calculate_skill_status(
    score: int,
    total_questions: int,
) -> str:
    """
    Convert an assessment score into a student-facing status.

    Internal demo rules:

        >= 80%  -> Strong
        >= 50%  -> Developing
        > 0%    -> Needs Improvement
        no test -> Not Assessed
    """

    if total_questions <= 0:
        return NOT_ASSESSED

    percentage = calculate_percentage(
        score,
        total_questions,
    )

    if percentage >= 80:
        return STRONG

    if percentage >= 50:
        return DEVELOPING

    return NEEDS_IMPROVEMENT


def validate_option(option: str) -> bool:
    """Return True when an MCQ option is A, B, C or D."""

    if not option:
        return False

    return option.strip().upper() in {
        "A",
        "B",
        "C",
        "D",
    }


def normalize_option(option: str) -> str:
    """Normalize an MCQ option."""

    if not option:
        return ""

    return option.strip().upper()


def grade_answer(
    selected_option: str,
    correct_option: str,
) -> bool:
    """Grade one MCQ answer."""

    return (
        normalize_option(selected_option)
        == normalize_option(correct_option)
    )


# ============================================================
# AUTHENTICATION
# ============================================================

def get_user_from_token(
    token: str,
    db: Session,
) -> Optional[User]:
    """Decode the existing SkillNova JWT."""

    try:
        payload = decode_token(token)

        user_id = payload.get("sub")

        if not user_id:
            return None

        return (
            db.query(User)
            .filter(
                User.id == int(user_id)
            )
            .first()
        )

    except Exception:
        return None


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Require an authenticated user."""

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

    token = authorization.split(
        " ",
        1,
    )[1]

    user = get_user_from_token(
        token,
        db,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    return user


def require_student(
    user: User = Depends(get_current_user),
):
    """Allow only student accounts."""

    if user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can take assessments",
        )

    return user


# ============================================================
# PROFILE HELPERS
# ============================================================

def get_student_profile(
    db: Session,
    user: User,
) -> Profile:
    """Return the student's profile."""

    profile = (
        db.query(Profile)
        .filter(
            Profile.user_id == user.id
        )
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


# ============================================================
# ASSESSMENT LOOKUP HELPERS
# ============================================================


# ============================================================
# DEMO QUESTION BANK / AUTO-SEEDING
# ============================================================
# These are demo MCQs for the MVP. They are not an official AYUSH
# competency standard or an SIH-prescribed question bank.
#
# Technical questions are tied to the selected role's existing
# RoleSkillRequirement records. Soft Skills and Aptitude are included
# in every role assessment.

# ============================================================
# AYUSH DEMO QUESTION BANK / AUTO-SEEDING
# ============================================================
# These are demo MCQs for the MVP.
# They are NOT an official AYUSH competency standard or
# an SIH-prescribed question bank.
#
# Technical questions are selected from the skills attached
# to the student's selected AYUSH role.
#
# Soft Skills and Aptitude are included in every assessment.

# ============================================================
# ADAPTIVE AYUSH QUESTION BANK / AUTO-SEEDING
# ============================================================
# These are SkillNova demo questions. They are NOT an official AYUSH
# competency standard and are not an SIH-prescribed question bank.
#
# Design goals:
# - questions are tied to the student's target-role skill requirements
# - difficulty increases with academic year / degree stage
# - distractors are plausible rather than obviously wrong
# - technical questions are domain-specific; there is NO generic
#   "responsible <skill>" fallback
#
# Academic stages:
#   foundation -> 1st year / early undergraduate
#   applied     -> 2nd year undergraduate
#   advanced    -> 3rd/4th year and postgraduate
#
# Each question tuple is:
# (question, A, B, C, D, correct, explanation)

FOUNDATION = "foundation"
APPLIED = "applied"
ADVANCED = "advanced"


def _q(question, a, b, c, d, correct, explanation):
    return (question, a, b, c, d, correct, explanation)


# Three-level technical questions for the most important AYUSH/research
# competency areas. Aliases below allow the same bank to serve many roles.
TECHNICAL_BANK = {
    "ayush systems overview": {
        FOUNDATION: _q(
            "Which set correctly represents the major systems covered under AYUSH?",
            "Ayurveda, Yoga & Naturopathy, Unani, Siddha, Sowa-Rigpa and Homoeopathy",
            "Ayurveda, Allopathy, Dentistry and Nursing only",
            "Yoga, Physiotherapy and Radiology only",
            "Siddha, Surgery and Emergency Medicine only",
            "A",
            "AYUSH encompasses Ayurveda, Yoga & Naturopathy, Unani, Siddha, Sowa-Rigpa and Homoeopathy.",
        ),
        APPLIED: _q(
            "An AYUSH research team is comparing interventions from two different traditional systems. Which step is most important before comparing outcomes?",
            "Define the interventions and outcome measures clearly enough to make the comparison meaningful",
            "Assume terminology has identical meanings across systems",
            "Combine all outcomes into one measure without justification",
            "Exclude studies using different traditional terminology",
            "A",
            "Cross-system research requires clear definitions of interventions and outcomes before comparison.",
        ),
        ADVANCED: _q(
            "A review combines AYUSH studies that use different intervention descriptions and outcome instruments. What is the strongest first methodological response?",
            "Assess conceptual and methodological comparability before deciding whether quantitative synthesis is appropriate",
            "Standardize every outcome by simply converting it to a percentage",
            "Pool all studies because they address the same broad condition",
            "Exclude every study that uses a different instrument",
            "A",
            "Meaningful synthesis depends on assessing comparability of interventions, populations and outcome measures.",
        ),
    },
    "biochemistry": {
        FOUNDATION: _q(
            "Which molecule is the primary energy currency used by cells?",
            "ATP",
            "DNA",
            "Collagen",
            "Bilirubin",
            "A",
            "ATP directly supplies usable chemical energy for many cellular processes.",
        ),
        APPLIED: _q(
            "An enzyme-catalyzed reaction reaches a higher rate when substrate concentration is increased, but eventually approaches a plateau. What does the plateau most directly indicate?",
            "The enzyme is approaching saturation under the tested conditions",
            "The enzyme has been completely degraded",
            "The substrate has become a competitive inhibitor at every concentration",
            "The reaction has become independent of enzyme concentration",
            "A",
            "A reaction plateau is characteristic of enzyme saturation when active sites become limiting.",
        ),
        ADVANCED: _q(
            "Two enzyme preparations show the same Vmax, but preparation B reaches half-maximal velocity at a lower substrate concentration. Which interpretation is most appropriate?",
            "Preparation B has a lower apparent Km under the tested conditions",
            "Preparation B necessarily has a lower Vmax",
            "Preparation A necessarily contains more enzyme molecules",
            "The comparison proves the two enzymes have identical substrate affinity mechanisms",
            "A",
            "A lower Km in the same experimental framework indicates that half-maximal velocity is reached at a lower substrate concentration.",
        ),
    },
    "fundamental research": {
        FOUNDATION: _q(
            "What is the main purpose of a research hypothesis?",
            "State a testable expectation that can be examined using evidence",
            "Guarantee the expected result",
            "Replace the need for data collection",
            "Prevent alternative explanations from being considered",
            "A",
            "A hypothesis provides a testable expectation; it does not guarantee the outcome.",
        ),
        APPLIED: _q(
            "A study compares an AYUSH intervention with a control group. Which design choice most directly reduces the risk that baseline differences explain the outcome?",
            "Use an appropriate allocation strategy and compare baseline characteristics before interpreting outcomes",
            "Select participants for the intervention group after seeing their outcomes",
            "Change the primary outcome after the analysis",
            "Report only participants who completed the intervention",
            "A",
            "Sound allocation and baseline assessment help distinguish intervention effects from pre-existing differences.",
        ),
        ADVANCED: _q(
            "A proposed AYUSH study has a statistically significant primary outcome but substantial baseline imbalance between groups. Which issue should be addressed first in interpreting the result?",
            "Whether the imbalance could plausibly confound the estimated intervention effect",
            "Whether statistical significance automatically proves causality",
            "Whether the p-value can replace reporting effect size",
            "Whether all secondary outcomes should be discarded",
            "A",
            "Baseline imbalance can introduce confounding, so causal interpretation requires careful assessment of its impact.",
        ),
    },
    "research methodology": {
        FOUNDATION: _q(
            "Why should a research question be defined before collecting study data?",
            "It helps determine what evidence and study design are appropriate",
            "It guarantees a positive result",
            "It removes the need for a control group in every study",
            "It allows researchers to ignore unexpected observations",
            "A",
            "A clear question guides the choice of design, variables and evidence collection.",
        ),
        APPLIED: _q(
            "A researcher wants to estimate the association between an exposure and an outcome in a defined population. Which planning step is most important before selecting the statistical test?",
            "Define the variables, study design and assumptions that determine which analysis is appropriate",
            "Choose the most complex statistical test available",
            "Select the test solely from the sample size",
            "Run several tests and report whichever gives the smallest p-value",
            "A",
            "Statistical analysis should follow from the research design, variables and assumptions rather than from the desired result.",
        ),
        ADVANCED: _q(
            "A study protocol specifies a primary outcome, but the investigators later find a different outcome produces a stronger effect. What is the most defensible reporting approach?",
            "Report the prespecified primary outcome and transparently identify any additional exploratory analysis",
            "Replace the primary outcome without disclosure",
            "Report only the outcome with the strongest effect",
            "Remove all outcomes that are not statistically significant",
            "A",
            "Separating prespecified from exploratory analyses reduces selective reporting and preserves interpretability.",
        ),
    },
    "clinical research": {
        FOUNDATION: _q(
            "What is the purpose of a clinical research protocol?",
            "To define how participants, interventions, outcomes and procedures will be handled",
            "To guarantee the intervention works",
            "To replace informed consent",
            "To allow procedures to change without documentation",
            "A",
            "A protocol provides a predefined framework for conducting the study consistently.",
        ),
        APPLIED: _q(
            "During an AYUSH clinical study, a participant misses a scheduled assessment. What should the research team do first?",
            "Document the deviation and follow the protocol's predefined handling procedure",
            "Delete the participant's earlier observations",
            "Estimate the missing result from the investigator's expectation",
            "Change the study endpoint to avoid the missing assessment",
            "A",
            "Protocol deviations should be documented and handled according to predefined procedures.",
        ),
        ADVANCED: _q(
            "A trial has a prespecified primary endpoint and several exploratory endpoints. The primary endpoint is inconclusive, while one exploratory endpoint is significant. How should the result be characterized?",
            "As evidence from an exploratory analysis that should not be presented as confirmation of the primary hypothesis",
            "As proof that the primary endpoint was successful",
            "As sufficient reason to omit the primary endpoint from the report",
            "As automatically equivalent to a prespecified confirmatory result",
            "A",
            "Exploratory findings can be informative but should be distinguished from prespecified confirmatory outcomes.",
        ),
    },
    "clinical data management": {
        FOUNDATION: _q(
            "Why are validation checks used in a clinical dataset?",
            "To detect inconsistent, missing or implausible entries",
            "To guarantee every patient received the same treatment",
            "To replace source documentation",
            "To make all values identical",
            "A",
            "Validation checks identify data-quality problems for review.",
        ),
        APPLIED: _q(
            "A clinical dataset contains an impossible negative age value. What is the best first action?",
            "Flag the record and verify it against the source before correcting it",
            "Replace it with the sample mean immediately",
            "Delete the participant from the dataset",
            "Assume it is a valid coded value without checking the data dictionary",
            "A",
            "An implausible value should be verified against source data and documented before correction.",
        ),
        ADVANCED: _q(
            "Two fields in a clinical database conflict: the treatment date precedes the recorded enrollment date. What should a data associate do?",
            "Raise a query and reconcile the discrepancy using source records and predefined data-management rules",
            "Change whichever date produces a logically consistent timeline",
            "Delete both fields and proceed with analysis",
            "Use the database import timestamp as the clinical date",
            "A",
            "Clinical data discrepancies require traceable reconciliation against source records rather than arbitrary correction.",
        ),
    },
    "data analysis": {
        FOUNDATION: _q(
            "A dataset contains several unusually large values. What should be checked before deciding how to handle them?",
            "Whether the values are valid observations, entry errors or measurement problems",
            "Whether deleting them increases the desired result",
            "Whether every large value should automatically be replaced",
            "Whether the mean becomes closer to the expected value after deletion",
            "A",
            "Outliers should first be investigated for validity and context.",
        ),
        APPLIED: _q(
            "A treatment group's outcome distribution is strongly right-skewed. Which summary is generally more robust for describing its center?",
            "Median with an appropriate measure of spread",
            "Mean alone with no distribution information",
            "Maximum value only",
            "The first observation in the dataset",
            "A",
            "The median is less sensitive to extreme values and is often useful for skewed distributions.",
        ),
        ADVANCED: _q(
            "An AYUSH clinical dataset has missing outcomes concentrated among participants who discontinued treatment. What is the strongest analytical concern?",
            "Missingness may be related to observed or unobserved factors, so the missing-data mechanism should be investigated before choosing a method",
            "All missing values can safely be treated as zero",
            "Missingness can be ignored if the remaining sample is large",
            "Mean imputation always preserves the original uncertainty structure",
            "A",
            "Systematic missingness can bias estimates; its mechanism should inform the handling strategy.",
        ),
    },
    "statistics": {
        FOUNDATION: _q(
            "What does a confidence interval primarily communicate?",
            "A range of values reflecting uncertainty around an estimated quantity",
            "The probability that the sample mean is exactly correct",
            "A guarantee that the true value lies inside the interval",
            "The percentage of observations that are valid",
            "A",
            "Confidence intervals communicate uncertainty around an estimate under the stated statistical framework.",
        ),
        APPLIED: _q(
            "Two studies report the same estimated treatment effect, but one has a much wider confidence interval. What is the most appropriate interpretation?",
            "The wider interval indicates greater uncertainty in that study's estimate",
            "The wider interval proves the treatment is less effective",
            "The wider interval proves the study is biased",
            "The point estimate should be ignored entirely",
            "A",
            "Interval width reflects precision; it does not by itself establish effectiveness or bias.",
        ),
        ADVANCED: _q(
            "A study reports p=0.03 for a secondary outcome after testing many secondary outcomes. Which interpretation is most cautious?",
            "The finding should be interpreted in light of multiplicity and whether the analysis was prespecified",
            "p=0.03 proves the secondary outcome is clinically important",
            "Multiplicity never matters when each test uses 0.05",
            "The result should automatically become the primary endpoint",
            "A",
            "Multiple testing and prespecification affect how confidently a secondary finding should be interpreted.",
        ),
    },
    "pharmacognosy": {
        FOUNDATION: _q(
            "What is a central concern of pharmacognosy?",
            "Identification and characterization of medicinal materials from natural sources",
            "Design of hospital electrical systems",
            "Scheduling outpatient appointments",
            "Writing software user interfaces",
            "A",
            "Pharmacognosy focuses on natural medicinal materials and their identification and characterization.",
        ),
        APPLIED: _q(
            "Two plant samples have the same common name but come from different sources. What should be established before combining their analytical results?",
            "Their identity and relevant provenance are sufficiently comparable",
            "That their common names are spelled identically",
            "That both samples produce the same expected result",
            "That source information is unnecessary after extraction",
            "A",
            "Correct identity and provenance are important when comparing or combining natural-material samples.",
        ),
        ADVANCED: _q(
            "An herbal extract shows a different chromatographic profile from previous batches. Which investigation is most informative first?",
            "Compare botanical identity, source, processing and analytical conditions before attributing the difference to biological variation",
            "Discard the batch because any profile difference proves contamination",
            "Average the chromatograms with previous batches without investigation",
            "Change the analytical method until the profile matches historical data",
            "A",
            "Batch-to-batch analytical differences can arise from identity, provenance, processing or method conditions and require systematic investigation.",
        ),
    },
    "medicinal plants": {
        FOUNDATION: _q(
            "Why is correct botanical identification important in medicinal-plant research?",
            "It establishes what biological material is actually being studied",
            "It guarantees therapeutic efficacy",
            "It removes the need for sample labeling",
            "It makes chemical analysis unnecessary",
            "A",
            "Correct identification is fundamental to traceability and interpretation of plant research.",
        ),
        APPLIED: _q(
            "A plant sample lacks collection-location information. Which research consequence is most immediate?",
            "Traceability and interpretation of variation across samples become weaker",
            "The sample automatically becomes therapeutically inactive",
            "The missing location can be inferred from the common name",
            "All laboratory measurements become invalid by definition",
            "A",
            "Collection provenance helps researchers interpret and reproduce findings.",
        ),
        ADVANCED: _q(
            "Two medicinal-plant batches have the same species identification but markedly different metabolite profiles. Which factor should be investigated alongside analytical method variation?",
            "Cultivation or collection conditions, plant part, processing and storage history",
            "Only the font used on the sample label",
            "Only the final statistical p-value",
            "Whether the expected profile can be obtained by removing inconvenient peaks",
            "A",
            "Biological and processing factors can substantially affect metabolite profiles even within the same species.",
        ),
    },
    "pharmacology": {
        FOUNDATION: _q(
            "What does pharmacology study?",
            "How substances interact with biological systems and produce effects",
            "Only medicine packaging",
            "Only plant taxonomy",
            "Only hospital accounting",
            "A",
            "Pharmacology examines drug/substance actions, mechanisms and effects in biological systems.",
        ),
        APPLIED: _q(
            "An experimental group shows a response while the control group also changes slightly. Why is the control important?",
            "It helps separate changes associated with the intervention from background changes",
            "It guarantees the intervention caused every observed change",
            "It eliminates the need for replication",
            "It proves the intervention is clinically effective",
            "A",
            "Controls provide a comparison for interpreting changes that may occur without the intervention.",
        ),
        ADVANCED: _q(
            "An intervention produces a dose-dependent response that plateaus at higher doses. Which explanation is most consistent with receptor-mediated pharmacology?",
            "The relevant biological system may be approaching a maximal response under the tested conditions",
            "Higher doses must always produce proportionally higher responses",
            "A plateau proves the compound is inactive",
            "The control group becomes irrelevant once a plateau appears",
            "A",
            "A maximal or near-maximal response can occur when the biological system's capacity becomes limiting.",
        ),
    },
    "pharmacological research": {
        FOUNDATION: _q(
            "Why are control groups used in pharmacological experiments?",
            "To provide a comparison for interpreting the intervention effect",
            "To ensure every result is positive",
            "To replace replication",
            "To avoid measuring outcomes",
            "A",
            "Controls help distinguish intervention-related effects from background changes.",
        ),
        APPLIED: _q(
            "A laboratory study changes the dose midway through an experiment. What is the most important consequence for interpretation?",
            "The change must be documented because dose is part of the experimental conditions",
            "The change is irrelevant if the final result is significant",
            "The original dose should be deleted from the record",
            "Only the highest dose should be reported",
            "A",
            "Experimental conditions must be traceable so that results can be interpreted correctly.",
        ),
        ADVANCED: _q(
            "A pharmacological experiment has a significant treatment-control difference, but the groups also differ in baseline body weight. What should be considered before attributing the entire effect to treatment?",
            "Whether baseline weight could confound the observed treatment difference",
            "Whether significance makes baseline variables irrelevant",
            "Whether the control group can be removed from the analysis",
            "Whether only the largest response should be reported",
            "A",
            "Baseline differences can confound treatment comparisons and should be assessed in interpretation or analysis.",
        ),
    },
    "drug development": {
        FOUNDATION: _q(
            "Which three broad properties are commonly considered when evaluating a medicinal product?",
            "Quality, safety and efficacy",
            "Color, advertising and packaging only",
            "Price, logo and website design only",
            "Taste, font and shipping speed only",
            "A",
            "Evidence-based product development considers quality, safety and efficacy through appropriate studies.",
        ),
        APPLIED: _q(
            "A promising formulation performs well in an initial laboratory experiment. What is the most appropriate next principle?",
            "Generate additional evidence using studies appropriate to the development stage",
            "Assume clinical effectiveness is established",
            "Skip safety evaluation because the initial result was positive",
            "Change the formulation without documenting the change",
            "A",
            "Evidence must accumulate through appropriate development stages; an early result does not establish overall safety or efficacy.",
        ),
        ADVANCED: _q(
            "A formulation meets an analytical specification but has inconsistent performance across development batches. Which conclusion is most defensible?",
            "Analytical compliance alone may not establish process consistency or product performance",
            "Meeting one specification proves the manufacturing process is controlled",
            "Batch variability can be ignored if the average result is acceptable",
            "The specification should be changed until all batches pass",
            "A",
            "Product development requires consideration of process consistency and relevant performance characteristics, not a single measurement alone.",
        ),
    },
    "quality control": {
        FOUNDATION: _q(
            "What is the primary purpose of quality control?",
            "Check materials or products against defined specifications",
            "Guarantee every batch without testing",
            "Replace documented procedures",
            "Approve products based only on appearance",
            "A",
            "Quality control uses defined tests and specifications to assess conformity.",
        ),
        APPLIED: _q(
            "A batch result falls outside a predefined specification. What is the appropriate immediate response?",
            "Document and investigate the result according to the quality procedure",
            "Delete the result and repeat until it passes",
            "Change the specification after seeing the result",
            "Release the batch because one result is inconvenient",
            "A",
            "Out-of-specification results require controlled investigation and documentation.",
        ),
        ADVANCED: _q(
            "Three batches meet the specification, but their analytical values show a consistent drift toward the upper limit. What should a quality professional consider?",
            "Whether the trend indicates process variation requiring investigation before a specification failure occurs",
            "Whether specification compliance means trends are irrelevant",
            "Whether the highest result should be deleted from the trend analysis",
            "Whether the specification should automatically be widened",
            "A",
            "Trend analysis can identify emerging process problems before individual batches fail specifications.",
        ),
    },
    "standardization": {
        FOUNDATION: _q(
            "Why is standardization useful for AYUSH products?",
            "It supports consistency in defined quality characteristics",
            "It guarantees clinical effectiveness",
            "It eliminates the need for testing",
            "It makes documentation unnecessary",
            "A",
            "Standardization helps establish reproducible and measurable quality characteristics.",
        ),
        APPLIED: _q(
            "Two batches meet a broad identity test but differ substantially in a defined marker. What does this suggest?",
            "The batches may not be equivalent with respect to the specified quality characteristic and need investigation",
            "The marker is irrelevant because identity matched",
            "The batch with the higher marker is automatically more clinically effective",
            "The marker should be removed from the specification",
            "A",
            "A defined marker can be part of standardization and requires investigation when batches differ.",
        ),
        ADVANCED: _q(
            "A standardization method has good repeatability but poor recovery when the analyte is spiked into the matrix. Which issue should be investigated?",
            "Method accuracy or matrix effects, because repeatability alone does not establish trueness",
            "Only analyst attendance records",
            "Whether the product label uses the correct font",
            "Whether repeatability makes recovery irrelevant",
            "A",
            "Repeatability describes consistency of repeated measurements; recovery provides evidence relevant to analytical accuracy and matrix effects.",
        ),
    },
    "gmp": {
        FOUNDATION: _q(
            "Which practice best supports Good Manufacturing Practice?",
            "Use controlled procedures and maintain accurate production records",
            "Allow undocumented process changes",
            "Backdate records when a step is missed",
            "Use uncontrolled procedure copies",
            "A",
            "Controlled procedures and traceable records are central to GMP-oriented operations.",
        ),
        APPLIED: _q(
            "An operator discovers that the current batch record does not reflect a documented process change. What is the best action?",
            "Follow the approved deviation/change-control procedure and update records through the controlled process",
            "Edit the historical record without documenting the change",
            "Ignore the discrepancy if the batch result is acceptable",
            "Create a new uncontrolled batch record",
            "A",
            "Changes and deviations need controlled documentation and traceability.",
        ),
        ADVANCED: _q(
            "Repeated minor deviations occur at the same manufacturing step across several batches. What is the strongest quality response?",
            "Perform trend/root-cause analysis and assess whether a corrective or preventive action is needed",
            "Treat each deviation as unrelated without reviewing the pattern",
            "Remove the deviations from the quality summary",
            "Increase the acceptance limits without investigating the process",
            "A",
            "Recurring deviations can indicate an underlying process problem and warrant systematic investigation.",
        ),
    },
    "regulatory compliance": {
        FOUNDATION: _q(
            "What is the purpose of regulatory compliance in an AYUSH product setting?",
            "To ensure applicable requirements are followed and documented",
            "To guarantee every product is effective",
            "To replace quality testing",
            "To allow undocumented process changes",
            "A",
            "Compliance concerns meeting applicable requirements; it does not itself guarantee clinical effectiveness.",
        ),
        APPLIED: _q(
            "A regulatory requirement relevant to a product changes during development. What should happen first?",
            "Assess the change against the product and update controlled processes or documentation as required",
            "Ignore it until an inspection",
            "Delete earlier compliance records",
            "Apply the change informally without traceability",
            "A",
            "Regulatory changes require controlled assessment and implementation.",
        ),
        ADVANCED: _q(
            "A product dossier contains evidence generated under an older analytical procedure after the procedure was formally revised. What should be assessed?",
            "The impact of the method change on comparability, validity and the regulatory acceptability of the evidence",
            "Only whether the newer method produces a larger value",
            "Whether the old data can be silently relabeled",
            "Whether all historical evidence should automatically be discarded",
            "A",
            "Method changes can affect comparability and the interpretation or acceptability of previously generated evidence.",
        ),
    },
    "pharmacovigilance": {
        FOUNDATION: _q(
            "What is the primary purpose of pharmacovigilance?",
            "Detect and evaluate safety information related to medicinal products",
            "Promote products regardless of safety findings",
            "Replace all clinical research",
            "Ignore reports without positive outcomes",
            "A",
            "Pharmacovigilance focuses on medicine-related safety monitoring and evaluation.",
        ),
        APPLIED: _q(
            "A patient reports a suspected adverse reaction after using an AYUSH product. What should a pharmacovigilance associate do first?",
            "Capture the relevant case information accurately and follow the applicable reporting procedure",
            "Assume the product caused the event with certainty",
            "Delete the report if causality is unclear",
            "Wait until several identical cases appear before recording it",
            "A",
            "Potential safety reports should be documented and processed according to the applicable workflow even when causality is uncertain.",
        ),
        ADVANCED: _q(
            "A safety database shows a sudden increase in reports involving the same product-event combination. What is the most appropriate interpretation?",
            "It may represent a safety signal that requires structured evaluation rather than immediate causal confirmation",
            "The increase proves the product caused every event",
            "The reports should be excluded because reporting frequency changed",
            "The signal can be dismissed until a randomized trial confirms it",
            "A",
            "Signal detection identifies patterns warranting further evaluation; it does not by itself establish causality.",
        ),
    },
    "microbiology": {
        FOUNDATION: _q(
            "Why is aseptic technique important in microbiology?",
            "It reduces unwanted contamination of samples and cultures",
            "It guarantees every organism is harmless",
            "It removes the need for controls",
            "It makes sample labeling unnecessary",
            "A",
            "Aseptic technique reduces contamination that could compromise microbiological work.",
        ),
        APPLIED: _q(
            "A negative control in a microbiological assay shows growth. What should be considered first?",
            "Possible contamination or a problem with the control procedure before interpreting test results",
            "That every test sample is automatically positive",
            "That the negative control can be ignored",
            "That the assay is more sensitive and needs no investigation",
            "A",
            "Growth in a negative control can indicate contamination or procedural failure and should be investigated.",
        ),
        ADVANCED: _q(
            "A microbial assay shows variable counts between replicate plates despite identical nominal conditions. Which investigation is most useful?",
            "Review sampling, dilution, plating technique, incubation conditions and measurement variability",
            "Select only the replicate with the expected count",
            "Average the plates before checking for procedural differences",
            "Change the acceptance criterion after observing the variability",
            "A",
            "Replicate variability can arise from multiple procedural and measurement sources that should be assessed systematically.",
        ),
    },
    "biotechnology": {
        FOUNDATION: _q(
            "Why are controls important in biotechnology experiments?",
            "They provide a comparison for interpreting the effect of the experimental condition",
            "They guarantee successful results",
            "They remove the need for replication",
            "They allow procedures to remain undocumented",
            "A",
            "Controls help identify whether an observed change is associated with the experimental condition.",
        ),
        APPLIED: _q(
            "An assay result changes after the incubation temperature is altered. What should be done before comparing it with the previous run?",
            "Document the changed condition and assess whether the runs remain comparable",
            "Combine the results without recording temperature",
            "Discard the earlier run automatically",
            "Assume temperature has no effect because the assay is the same",
            "A",
            "Experimental conditions affect comparability and must be documented.",
        ),
        ADVANCED: _q(
            "A biotechnology experiment has strong treatment effects but only one biological replicate. What is the key limitation?",
            "The evidence may not adequately characterize biological variability or support generalization",
            "A single replicate proves the effect if the p-value is small",
            "Technical precision makes biological replication unnecessary",
            "The result can automatically be generalized to other systems",
            "A",
            "Biological replication is important for assessing variability and the reproducibility of biological effects.",
        ),
    },
    "epidemiology": {
        FOUNDATION: _q(
            "What does epidemiology primarily study?",
            "The distribution and determinants of health-related events in populations",
            "Only laboratory equipment",
            "Only medicine packaging",
            "Only individual preferences",
            "A",
            "Epidemiology studies health events and their determinants at the population level.",
        ),
        APPLIED: _q(
            "An AYUSH community survey finds that exposure and outcome are both more common in an older subgroup. What should be considered before interpreting their association?",
            "Age may act as a confounding factor and should be assessed in the analysis",
            "The association must be causal because both variables are common",
            "Age can be ignored because it is not the exposure of interest",
            "Only the p-value determines whether confounding exists",
            "A",
            "A third variable associated with both exposure and outcome can confound an observed association.",
        ),
        ADVANCED: _q(
            "A cross-sectional study finds an association between an AYUSH practice and a health outcome. Which causal limitation is especially important?",
            "Temporality may be unclear because exposure and outcome are assessed at the same time",
            "Cross-sectional studies always eliminate confounding",
            "Association automatically establishes incidence",
            "A statistically significant association proves the exposure preceded the outcome",
            "A",
            "Cross-sectional designs may not establish whether exposure preceded outcome.",
        ),
    },
    "health informatics": {
        FOUNDATION: _q(
            "Which principle is important when handling digital health information?",
            "Protect confidentiality and restrict access appropriately",
            "Make all records public",
            "Share credentials among team members",
            "Delete audit information routinely",
            "A",
            "Health information requires appropriate confidentiality, integrity and access controls.",
        ),
        APPLIED: _q(
            "A clinical application allows a user to edit records but does not record who changed them. Which risk is most direct?",
            "Reduced traceability and accountability for data changes",
            "Improved auditability",
            "Guaranteed data accuracy",
            "Automatic prevention of unauthorized access",
            "A",
            "Audit trails help establish who changed data, when and, where applicable, what changed.",
        ),
        ADVANCED: _q(
            "Two health datasets use different coding schemes for the same clinical variable. Before integrating them, what should be established?",
            "A documented mapping and semantic equivalence between the coding systems",
            "That the codes have the same numeric values",
            "That the datasets have identical row counts",
            "That missing values can be mapped to zero",
            "A",
            "Data integration requires semantic and coding equivalence, not merely matching data types or row counts.",
        ),
    },
    "literature review": {
        FOUNDATION: _q(
            "What is a key purpose of a literature review?",
            "Identify and evaluate existing evidence relevant to a research question",
            "Select only papers that support one conclusion",
            "Replace primary research in every situation",
            "List papers without considering their methods",
            "A",
            "A literature review evaluates existing evidence in relation to a question.",
        ),
        APPLIED: _q(
            "Two papers reach different conclusions about an AYUSH intervention. What should a reviewer examine next?",
            "Differences in study design, population, intervention, outcomes and risk of bias",
            "Which paper has the more attractive title",
            "Which conclusion agrees with personal expectations",
            "Only the publication year",
            "A",
            "Apparent disagreement can arise from meaningful methodological differences.",
        ),
        ADVANCED: _q(
            "A systematic review includes studies with substantial heterogeneity in interventions and outcome measures. What should the reviewer avoid?",
            "Assuming that a pooled estimate is automatically meaningful without assessing clinical and methodological heterogeneity",
            "Reporting study-level characteristics",
            "Exploring sources of heterogeneity",
            "Separating qualitatively different evidence when appropriate",
            "A",
            "Heterogeneity affects whether quantitative pooling is scientifically justified and how results should be interpreted.",
        ),
    },
    "evidence synthesis": {
        FOUNDATION: _q(
            "What does evidence synthesis aim to do?",
            "Bring together and critically evaluate findings from relevant sources",
            "Use one preferred source only",
            "Remove conflicting findings",
            "Assume all studies have equal quality",
            "A",
            "Evidence synthesis considers findings across sources while accounting for their quality and differences.",
        ),
        APPLIED: _q(
            "Three studies report the same outcome using different methods. What should be checked before combining their results?",
            "Whether the outcome definitions and methods are sufficiently comparable",
            "Whether their sample sizes are identical",
            "Whether all reported p-values are below 0.05",
            "Whether the studies were conducted by the same institution",
            "A",
            "Comparability of outcomes and methods is necessary before quantitative combination.",
        ),
        ADVANCED: _q(
            "A synthesis finds that small studies show larger effects than large studies. Which interpretation requires particular caution?",
            "Small-study effects and publication bias may contribute to the observed pattern and should be investigated",
            "The small studies must therefore be more accurate",
            "The largest study should automatically be discarded",
            "The difference proves the intervention works better in small samples",
            "A",
            "Differences by study size can reflect bias or methodological factors rather than a true effect modification.",
        ),
    },
    "scientific writing": {
        FOUNDATION: _q(
            "Which statement best distinguishes a research result from an interpretation?",
            "A result reports what was observed; an interpretation explains what the finding may mean",
            "A result is always a causal explanation",
            "An interpretation can replace the reported data",
            "Results should be changed to fit the discussion",
            "A",
            "Clear scientific writing separates observations/results from their interpretation.",
        ),
        APPLIED: _q(
            "A study observes an association but cannot establish temporality. Which wording is most appropriate?",
            "The findings are associated with the outcome, while causal interpretation remains uncertain",
            "The intervention caused the outcome",
            "The association proves effectiveness",
            "The limitation can be omitted if the p-value is significant",
            "A",
            "Scientific claims should match the strength and limitations of the evidence.",
        ),
        ADVANCED: _q(
            "A manuscript's discussion claims clinical effectiveness although the study measured only a surrogate laboratory marker. What should the author do?",
            "Limit the claim to what the measured outcome supports and explain the distinction from clinical effectiveness",
            "Keep the claim because surrogate outcomes always equal clinical outcomes",
            "Remove the methods section to avoid confusion",
            "Replace the surrogate result with a clinical endpoint that was not measured",
            "A",
            "Claims should not exceed the construct actually measured by the study.",
        ),
    },
    "traditional knowledge": {
        FOUNDATION: _q(
            "Why should the source and context of traditional knowledge be recorded?",
            "They preserve provenance and help others interpret the knowledge responsibly",
            "They guarantee the claim is clinically effective",
            "They make ethical considerations unnecessary",
            "They allow unsupported claims to be treated as verified facts",
            "A",
            "Provenance and context are important for responsible documentation and interpretation.",
        ),
        APPLIED: _q(
            "A community provides knowledge for documentation that includes culturally sensitive information. What should be considered?",
            "Appropriate permissions, context and responsible handling of sensitive information",
            "Publishing every detail immediately",
            "Removing the community's attribution",
            "Treating the knowledge as ownerless because it is traditional",
            "A",
            "Responsible documentation considers permissions, provenance, context and sensitivity.",
        ),
        ADVANCED: _q(
            "A traditional-use claim is frequently cited online but has limited primary documentation. How should it be represented in scientific writing?",
            "Clearly distinguish the documented traditional claim from evidence that independently evaluates its effectiveness or mechanism",
            "Present the claim as clinically established because it is widely repeated",
            "Remove all discussion of its provenance",
            "Convert repeated citations into quantitative evidence automatically",
            "A",
            "Frequency of citation does not substitute for independent evidence; provenance and evidentiary status should remain distinct.",
        ),
    },
    "literary research": {
        FOUNDATION: _q(
            "What is an important activity in literary research on traditional medicine?",
            "Critically examine historical and textual sources in context",
            "Accept every historical statement as scientifically proven",
            "Remove source information from notes",
            "Use only modern summaries without checking primary texts",
            "A",
            "Literary research requires contextual and critical examination of sources.",
        ),
        APPLIED: _q(
            "Two historical texts describe the same preparation differently. What should a researcher examine?",
            "Differences in provenance, period, terminology and textual context",
            "Which version is shorter",
            "Which version matches modern expectations",
            "Whether one text can be discarded without review",
            "A",
            "Historical differences need contextual analysis rather than selection by convenience.",
        ),
        ADVANCED: _q(
            "A modern article attributes a technical statement to an old text, but the cited passage does not contain the statement. What is the strongest response?",
            "Check the primary source and report the discrepancy rather than repeating the secondary attribution",
            "Keep the modern attribution because it is already published",
            "Edit the primary passage to match the article",
            "Treat repeated secondary citations as equivalent to primary verification",
            "A",
            "Primary-source verification is essential when evaluating historical or textual claims.",
        ),
    },
    "yoga": {
        FOUNDATION: _q(
            "When studying a yoga-based intervention, what should be defined clearly?",
            "The intervention protocol and the outcomes being measured",
            "Only the instructor's preference",
            "Only participant opinions after the study",
            "No intervention details if the practice is familiar",
            "A",
            "Clear intervention and outcome definitions support reproducible research.",
        ),
        APPLIED: _q(
            "Two yoga studies report different effects. Which factor could materially affect comparability?",
            "Differences in intervention duration, intensity, participant population or outcome measurement",
            "Only the journal's website design",
            "Whether the titles contain the same number of words",
            "Whether both studies use the word yoga in the title",
            "A",
            "Intervention dose and population/outcome differences can affect comparability.",
        ),
        ADVANCED: _q(
            "A yoga intervention study reports improved outcomes but has no comparator and substantial loss to follow-up. What is the strongest limitation?",
            "The observed improvement cannot be confidently attributed to the intervention because of missing comparison and potential attrition bias",
            "The improvement proves effectiveness because the outcome changed",
            "Loss to follow-up is irrelevant if the remaining participants improved",
            "A comparator is unnecessary for causal interpretation",
            "A",
            "Without an appropriate comparison and with substantial attrition, causal attribution is limited.",
        ),
    },
    "naturopathy": {
        FOUNDATION: _q(
            "What supports systematic research into naturopathy interventions?",
            "Clearly defined interventions, outcomes and study procedures",
            "Changing the intervention without documentation",
            "Reporting only favourable observations",
            "Avoiding participant criteria",
            "A",
            "Defined interventions and outcomes are necessary for systematic evaluation.",
        ),
        APPLIED: _q(
            "A naturopathy study combines several lifestyle interventions at once. What makes interpretation difficult?",
            "The individual contribution of each component cannot be separated easily",
            "The sample size becomes automatically larger",
            "Combined interventions guarantee stronger evidence",
            "Outcome measurement becomes unnecessary",
            "A",
            "Multicomponent interventions can make attribution to individual components difficult.",
        ),
        ADVANCED: _q(
            "A multicomponent naturopathy program improves an outcome, but adherence varies greatly between participants. Which factor should be considered in interpretation?",
            "Whether variation in adherence affects the estimated effect and introduces differences between participants",
            "That adherence is irrelevant once the intervention is assigned",
            "That all participants received identical exposure regardless of adherence",
            "That only participants with high adherence should define the primary result without prespecification",
            "A",
            "Actual exposure/adherence can influence observed effects and should be analyzed transparently.",
        ),
    },
    "siddha": {
        FOUNDATION: _q(
            "What is important when documenting research involving Siddha practices?",
            "Record the practice, context, methodology and observations clearly",
            "Record only positive findings",
            "Remove the source and context",
            "Change the procedure without documentation",
            "A",
            "Clear contextual and methodological documentation supports responsible research.",
        ),
        APPLIED: _q(
            "A Siddha preparation is described using a traditional term with multiple modern interpretations. What should a researcher do?",
            "Define the term and preparation context explicitly before comparing it with other studies",
            "Choose the most convenient modern interpretation",
            "Assume all interpretations are equivalent",
            "Remove the traditional terminology from the record",
            "A",
            "Terminology can be ambiguous across sources; explicit definitions are needed for valid comparison.",
        ),
        ADVANCED: _q(
            "A Siddha formulation varies between historical sources in ingredients and preparation. Which research approach is strongest?",
            "Document the variants and investigate whether they represent distinct formulations before aggregating evidence",
            "Treat all variants as identical because the name is similar",
            "Select the variant with the strongest claimed effect",
            "Exclude historical variants without documenting the decision",
            "A",
            "Formulation differences may represent materially different interventions and should be characterized before synthesis.",
        ),
    },
    "unani": {
        FOUNDATION: _q(
            "Which practice supports responsible Unani research?",
            "Use documented methods and evaluate evidence systematically",
            "Rely only on undocumented claims",
            "Ignore preparation details",
            "Report only successful observations",
            "A",
            "Documented methods and evidence evaluation support responsible research.",
        ),
        APPLIED: _q(
            "A Unani intervention study reports a positive outcome but provides limited information about the preparation. What is the main research concern?",
            "Insufficient intervention detail can limit reproducibility and interpretation",
            "Missing preparation information guarantees the result is false",
            "Preparation details are irrelevant to intervention research",
            "The outcome can be accepted without evaluating the intervention definition",
            "A",
            "Intervention characterization is necessary to reproduce and interpret research findings.",
        ),
        ADVANCED: _q(
            "A Unani intervention is described differently across three studies. Before synthesizing their outcomes, what should be established?",
            "Whether the formulations and treatment procedures are sufficiently equivalent to represent the same intervention",
            "Whether all three studies use the same sample size",
            "Whether the authors use the same terminology in English",
            "Whether the positive study has the largest effect",
            "A",
            "Intervention equivalence is essential before combining evidence across studies.",
        ),
    },
    "homoeopathy": {
        FOUNDATION: _q(
            "Which approach is appropriate when designing research involving Homoeopathy?",
            "Use a defined protocol and systematically record outcomes",
            "Change the protocol after seeing results",
            "Report only favourable observations",
            "Avoid defining the study population",
            "A",
            "A defined protocol and systematic outcome recording support interpretable research.",
        ),
        APPLIED: _q(
            "A study's outcome definition changes after data collection has begun. Why is this important?",
            "Changing outcome definitions can affect interpretation and should be documented transparently",
            "Outcome definitions never affect analysis",
            "The change can be hidden if the final result is significant",
            "Only the sample size matters for interpretation",
            "A",
            "Outcome definitions influence analysis and should be prespecified or transparently changed.",
        ),
        ADVANCED: _q(
            "A study reports a large improvement after a Homoeopathy intervention but lacks an adequate comparator. What is the strongest conclusion?",
            "The observed change warrants further evaluation, but the design limits causal attribution to the intervention",
            "The intervention is proven effective because the outcome improved",
            "The absence of a comparator strengthens causal inference",
            "Patient improvement automatically rules out placebo or natural-history effects",
            "A",
            "Without an adequate comparator, alternative explanations for observed change remain difficult to exclude.",
        ),
    },
    "sowa-rigpa": {
        FOUNDATION: _q(
            "What is important when documenting Sowa-Rigpa research?",
            "Record the intervention, context and research methodology clearly",
            "Record only positive findings",
            "Remove contextual information",
            "Avoid documenting preparation details",
            "A",
            "Clear context and methodology are important for responsible documentation and research.",
        ),
        APPLIED: _q(
            "A Sowa-Rigpa intervention is described using terminology that differs between sources. What should be done before comparing studies?",
            "Clarify terminology and intervention characteristics in each source",
            "Assume the terms are interchangeable",
            "Choose one translation and discard the source wording",
            "Compare outcomes without defining the intervention",
            "A",
            "Terminology and intervention definitions must be clarified before comparison.",
        ),
        ADVANCED: _q(
            "A review combines Sowa-Rigpa studies with substantially different intervention protocols. Which approach is most defensible?",
            "Assess protocol-level heterogeneity and synthesize quantitatively only when the interventions and outcomes are sufficiently comparable",
            "Pool all studies because they share the same medical tradition",
            "Ignore protocol differences if the direction of effect is similar",
            "Select only the study with the largest effect",
            "A",
            "Shared tradition does not by itself establish intervention equivalence for evidence synthesis.",
        ),
    },
    "public health": {
        FOUNDATION: _q(
            "What is a key goal of public-health research?",
            "Generate evidence that can inform population-level health decisions",
            "Focus only on one individual's preferences",
            "Avoid population data",
            "Replace evidence with assumptions",
            "A",
            "Public-health research aims to generate evidence relevant to populations and health decisions.",
        ),
        APPLIED: _q(
            "A community AYUSH program has high participation but little information about who did not participate. Why does this matter?",
            "Selection effects may limit how broadly the observed outcomes can be interpreted",
            "Nonparticipants are irrelevant to program evaluation",
            "High participation guarantees effectiveness",
            "Participation rate replaces outcome measurement",
            "A",
            "Differences between participants and nonparticipants can affect generalizability and interpretation.",
        ),
        ADVANCED: _q(
            "An AYUSH community intervention is associated with improved outcomes, but implementation differs substantially between villages. What should evaluation consider?",
            "Whether implementation fidelity and contextual differences contribute to variation in observed effects",
            "That contextual variation can be ignored because the intervention name is the same",
            "That the strongest village result represents all villages",
            "That outcome differences prove different biological mechanisms",
            "A",
            "Implementation and context can affect population-level intervention effects and should be evaluated.",
        ),
    },
    "health informatics": {},
}

# Remove the accidental duplicate placeholder while retaining the richer entry.
TECHNICAL_BANK.pop("health informatics", None)
# The dictionary above contains the full health-informatics entry under the
# same key; restore it explicitly to keep the source easy to audit.
TECHNICAL_BANK["health informatics"] = {
    FOUNDATION: _q(
        "Which principle is important when handling digital health information?",
        "Protect confidentiality and restrict access appropriately",
        "Make all records public",
        "Share credentials among team members",
        "Delete audit information routinely",
        "A",
        "Health information requires appropriate confidentiality, integrity and access controls.",
    ),
    APPLIED: _q(
        "A clinical application allows a user to edit records but does not record who changed them. Which risk is most direct?",
        "Reduced traceability and accountability for data changes",
        "Improved auditability",
        "Guaranteed data accuracy",
        "Automatic prevention of unauthorized access",
        "A",
        "Audit trails help establish who changed data, when and, where applicable, what changed.",
    ),
    ADVANCED: _q(
        "Two health datasets use different coding schemes for the same clinical variable. Before integrating them, what should be established?",
        "A documented mapping and semantic equivalence between the coding systems",
        "That the codes have the same numeric values",
        "That the datasets have identical row counts",
        "That missing values can be mapped to zero",
        "A",
        "Data integration requires semantic and coding equivalence, not merely matching data types or row counts.",
    ),
}


# ============================================================
# ROLE-SPECIFIC DEEP QUESTION BANK
# ============================================================
# These questions are intentionally scenario-based and role-specific.
# They are demo content, not an official AYUSH competency standard.
# Each role family has six questions per academic stage so the assessment
# can measure several different role skills without repeating a question.

ROLE_DEEP_BANK = {
    "clinical data": {
        FOUNDATION: [
            _q("An AYUSH clinical study records participant age in three formats: 20, twenty and 20 years. What should a data associate do before analysis?", "Define and apply one documented data format during cleaning", "Treat all three as different participants", "Delete the records", "Convert every value to zero", "A", "Consistent, documented formatting is necessary before reliable analysis."),
            _q("A case report form asks for the date of an outcome. Which entry is most useful for later analysis?", "A complete date recorded using the study's defined format", "Only the month", "An approximate date without explanation", "The date from memory after the study closes", "A", "Standardized and traceable dates support accurate analysis and auditing."),
            _q("A clinical dataset contains two records with the same participant identifier. What should be checked first?", "Whether the duplicate represents a legitimate repeated record or a data-entry error", "Delete one record immediately", "Assume both are correct", "Change one identifier randomly", "A", "Duplicates must be investigated before deciding how they should be handled."),
            _q("A variable is documented as treatment group A/B in the protocol. Which practice is safest during data entry?", "Use the predefined coding scheme consistently", "Create new codes whenever convenient", "Mix text and numbers without documentation", "Infer codes from the participant name", "A", "Predefined coding improves consistency and reduces ambiguity."),
            _q("Why is a data dictionary useful in a clinical research project?", "It defines variables, allowed values and meanings consistently", "It replaces the study protocol", "It guarantees there are no missing values", "It makes statistical testing unnecessary", "A", "A data dictionary establishes shared meaning and valid representations of variables."),
            _q("A participant ID appears in an analysis file but the participant's name is not required. What is the better practice?", "Use the minimum identifier needed for the analysis and protect the linkage separately", "Add the full name for convenience", "Publish all identifiers", "Share the linkage file with everyone", "A", "Data minimization reduces unnecessary privacy exposure while retaining required linkage."),
        ],
        APPLIED: [
            _q("A clinical dataset has 240 records. Validation shows that 18 records contain an impossible age of 250 years. What is the best next step?", "Query the source data and document the resolution rather than silently replacing the values", "Replace all 250 values with the mean age", "Delete the 18 participants", "Ignore the values because there are few of them", "A", "Source verification and traceable correction preserve data integrity."),
            _q("Two sites use different labels for the same outcome category. Before pooling their data, what should be established?", "A documented mapping showing that the categories have equivalent meanings", "That the labels have the same number of characters", "That one site's labels are always better", "That the categories can be merged without review", "A", "Semantic equivalence must be established before harmonizing codes."),
            _q("A missing outcome is concentrated in participants who withdrew early. What should be investigated before choosing a missing-data method?", "The pattern and likely mechanism of missingness and its relationship to study variables", "Whether the missing value can simply be set to zero", "Whether the final sample can be made smaller without explanation", "Whether missingness always means treatment failure", "A", "The mechanism and pattern of missingness affect appropriate handling and interpretation."),
            _q("A data query changes a value from 72 to 27 after source verification. Which record is most important to preserve?", "The traceable history of the original value, correction and reason", "Only the final value", "Only the person's name", "No record of the change", "A", "Auditability requires traceable correction history."),
            _q("A dataset has a treatment variable coded 1/2 at one site and A/B at another. What should happen before analysis?", "Create and document a common coding scheme and validate the mapping", "Assume 1 means A without checking", "Drop one site", "Convert every code to zero", "A", "A documented mapping is required for valid integration."),
            _q("A validation check finds that the date of treatment is later than the recorded date of follow-up. What does this indicate?", "A logical consistency issue that should be investigated against source records", "Proof that the treatment was ineffective", "A value that should automatically be deleted", "A normal pattern that needs no review", "A", "Cross-field validation identifies contradictions that require investigation."),
        ],
        ADVANCED: [
            _q("An AYUSH trial dataset shows a statistically significant treatment difference, but 22% of primary-outcome values are missing and missingness differs by group. What should be addressed before interpreting the effect?", "Assess the missing-data mechanism and perform appropriate sensitivity analyses", "Assume missing observations have no effect", "Replace every missing value with zero", "Report only complete cases without qualification", "A", "Differential missingness can bias estimates and should be assessed explicitly."),
            _q("Two clinical sites have different distributions of a key baseline variable. What should a data analyst do before pooling the sites?", "Investigate site effects, data quality and protocol differences and account for relevant structure in analysis", "Pool immediately because both sites used the same protocol title", "Delete the site with the unusual distribution", "Normalize the variable without checking why it differs", "A", "Site differences may reflect data quality, population or implementation effects."),
            _q("A derived endpoint is calculated from several source variables. What provides the strongest reproducibility?", "A documented derivation rule, source-variable definitions and validation checks", "Only the final endpoint value", "A screenshot of the spreadsheet", "A verbal explanation after analysis", "A", "Derived variables need traceable definitions and validation to be reproducible."),
            _q("A database lock is planned, but a small number of unresolved queries remain for the primary endpoint. What is the strongest approach?", "Assess the impact, resolve material issues and document any justified residual uncertainty before lock", "Close the database regardless of the queries", "Change the endpoint to avoid the queries", "Delete unresolved records", "A", "Database lock should follow controlled resolution and documentation of material issues."),
            _q("A model predicting an AYUSH clinical outcome has high accuracy because the outcome is highly imbalanced. Which additional metric is most useful for evaluating performance?", "Sensitivity, specificity and class-balanced measures appropriate to the clinical objective", "Only raw accuracy", "Number of rows in the dataset", "The model's training time", "A", "Accuracy alone can be misleading under class imbalance; clinically relevant measures are needed."),
            _q("Two analysts independently produce different cleaned datasets from the same source. What should the team prioritize?", "Compare transformation rules, establish a shared data-cleaning specification and document the final version", "Choose the dataset with the higher treatment effect", "Average the two datasets", "Discard both without investigation", "A", "Reproducible cleaning requires explicit, shared transformation rules."),
        ],
    },
    "fundamental research": {
        FOUNDATION: [
            _q("A researcher wants to test whether an AYUSH intervention changes a measurable biological outcome. What should be defined first?", "A clear research question, measurable outcome and appropriate study design", "The expected result only", "The conclusion before collecting data", "A statistical test before defining the outcome", "A", "A testable question and design should precede data collection and analysis."),
            _q("Why is a control or comparison condition useful in experimental research?", "It helps distinguish the intervention effect from other changes", "It guarantees the hypothesis is correct", "It removes all experimental error", "It makes replication unnecessary", "A", "Comparison helps evaluate alternative explanations for observed changes."),
            _q("A laboratory experiment gives an unexpected result. What is the best scientific response?", "Check the method and evidence and consider plausible explanations rather than discarding the result", "Delete the result", "Change the result to match the hypothesis", "Report only the expected observations", "A", "Unexpected observations should be investigated rather than selectively removed."),
            _q("What makes a research variable operationally useful?", "It has a clear definition and a reproducible way of being measured", "It has a complicated name", "It is always qualitative", "It is selected after seeing the result", "A", "Operational definitions make measurements consistent and interpretable."),
            _q("A study repeats an experiment several times. Why is this useful?", "It helps assess whether the observed finding is reproducible under comparable conditions", "It guarantees the result is true", "It removes the need for controls", "It allows unfavorable trials to be ignored", "A", "Replication provides evidence about reproducibility and variability."),
            _q("A research notebook contains the date, method, sample identifiers and observations. Why is this important?", "It provides traceability for how the result was produced", "It makes peer review unnecessary", "It guarantees there were no errors", "It replaces the raw data", "A", "Traceable records allow others to understand and evaluate the work."),
        ],
        APPLIED: [
            _q("An AYUSH experiment shows different results between batches of the same plant extract. What should be investigated first?", "Batch characteristics, extraction conditions, source material and other controlled variables", "Average the results and ignore the difference", "Discard the lower result", "Change the hypothesis to fit one batch", "A", "Batch variability can arise from material and process differences and needs investigation."),
            _q("A study compares two interventions but the groups differ substantially at baseline. Why is this important?", "Baseline differences may confound interpretation of the observed outcome difference", "Baseline differences prove the intervention failed", "They can always be ignored if the p-value is small", "They make all data unusable", "A", "Pre-existing differences can provide alternative explanations for outcome differences."),
            _q("A researcher tests ten outcomes but highlights only the one with p < 0.05. What methodological concern arises?", "Selective emphasis can increase the risk of misleading interpretation from multiple testing", "The result becomes automatically causal", "The other outcomes become irrelevant", "The study no longer needs replication", "A", "Multiple comparisons and selective reporting can distort interpretation."),
            _q("Two candidate assays measure the same biological property with different precision. Which evidence is most useful when choosing one?", "Validation data showing accuracy, precision, robustness and suitability for the intended purpose", "Which assay has the longer name", "Which gives the largest numerical result", "Which is newest without checking validation", "A", "Analytical method selection should be based on demonstrated performance and intended use."),
            _q("A literature search finds several studies with conflicting findings. What should a researcher do before concluding that the evidence is inconsistent?", "Compare populations, methods, interventions, outcomes and study quality across the studies", "Choose the study with the largest effect", "Average the conclusions without examining methods", "Ignore studies with negative findings", "A", "Apparent conflict can arise from meaningful methodological or contextual differences."),
            _q("A researcher changes the primary outcome after seeing the initial data. What is the main concern?", "The change can introduce outcome-selection bias and should be transparently justified", "Changing outcomes always improves validity", "The original outcome becomes automatically false", "The analysis becomes blinded", "A", "Post-hoc outcome changes can bias interpretation and require transparency."),
        ],
        ADVANCED: [
            _q("An AYUSH intervention shows benefit in an observational cohort, but users of the intervention differ systematically from non-users in baseline health status. What is the central analytical issue?", "Confounding may explain part of the observed association", "Association automatically proves causation", "Sample size removes confounding", "Statistical significance eliminates baseline differences", "A", "Systematic baseline differences can confound observational associations."),
            _q("A factorial experiment finds that two interventions each have an effect, but their combination performs differently from what would be expected from their separate effects. What should be examined?", "A possible interaction between the interventions", "Only the larger main effect", "Whether the smaller effect should be deleted", "Whether interaction can be assumed absent", "A", "Departure from expected combined effects can indicate interaction."),
            _q("A biomarker changes significantly after treatment, but the change is small and its clinical meaning is uncertain. Which conclusion is most defensible?", "Report the statistical result together with effect size, uncertainty and clinical relevance", "Call the treatment clinically effective because p < 0.05", "Ignore the effect size", "Treat statistical significance as proof of biological importance", "A", "Statistical and clinical significance are distinct and should both be considered."),
            _q("A preclinical study has strong internal control but uses a highly artificial experimental system. What limitation should be considered when interpreting the findings?", "Limited external validity or generalizability to real-world biological settings", "The controlled design makes generalization automatic", "Artificial systems cannot produce useful evidence", "External validity is unrelated to study design", "A", "Highly controlled systems can support inference while still limiting generalizability."),
            _q("A proposed study has adequate sample size but the measurement method is poorly validated. Which problem remains?", "Measurement error can undermine the validity of the conclusions despite adequate sample size", "Sample size guarantees valid measurement", "Validation is unnecessary when n is large", "Measurement error only affects presentation", "A", "Large samples do not correct for systematic problems in measurement validity."),
            _q("Several studies report different effects of an AYUSH intervention. Before performing a meta-analysis, what should be assessed most carefully?", "Clinical and methodological heterogeneity in populations, interventions, comparators and outcomes", "Only whether all studies have the same sample size", "Only the largest reported effect", "Whether the studies use the same title terminology", "A", "Meaningful synthesis requires assessment of clinical and methodological comparability."),
        ],
    },
    "pharmacovigilance": {
        FOUNDATION: [
            _q("What is the main purpose of pharmacovigilance?", "Detect and evaluate medicine-related safety problems and protect patients", "Increase product sales", "Guarantee that every adverse event is caused by the medicine", "Replace clinical diagnosis", "A", "Pharmacovigilance focuses on detecting, evaluating and preventing medicine-related risks."),
            _q("A patient develops a symptom after using an AYUSH product. What is the safest initial documentation practice?", "Record the product, event, timing, relevant patient details and available clinical information", "Record only the symptom name", "Assume causality immediately", "Delete unrelated clinical information", "A", "Complete, structured information supports later safety assessment."),
            _q("Why is the timing between product exposure and an adverse event important?", "It helps evaluate whether the temporal relationship is compatible with a possible association", "It proves causality", "It replaces all other evidence", "It is relevant only for manufacturing", "A", "Temporality is one part of evaluating a possible product-event relationship."),
            _q("What is the difference between severity and seriousness of an adverse event?", "They describe different concepts: intensity versus outcomes or regulatory seriousness criteria", "They are always identical", "Seriousness means the symptom feels strong", "Severity means the event required hospitalization", "A", "Severity and seriousness are distinct concepts in safety assessment."),
            _q("A safety report contains an obvious missing date. What should be done?", "Seek clarification or source information and document the correction", "Invent the most likely date", "Delete the report", "Assume the date is irrelevant", "A", "Missing critical information should be clarified rather than fabricated."),
            _q("Why should adverse-event reports be handled using controlled procedures?", "Consistent procedures improve traceability, completeness and safety evaluation", "They make causality automatic", "They remove the need for medical review", "They prevent every possible adverse event", "A", "Controlled workflows support reliable safety information."),
        ],
        APPLIED: [
            _q("Several reports describe the same unusual event after exposure to an AYUSH product. What should a pharmacovigilance team consider?", "Whether the reports form a pattern that warrants signal evaluation", "Delete duplicates without checking their details", "Assume the product caused every event", "Ignore the pattern until a clinical trial repeats it", "A", "Repeated reports of a potentially important event can warrant signal assessment."),
            _q("A report includes a positive dechallenge but no rechallenge information. What does this mean?", "Improvement after withdrawal may support an association but does not by itself prove causality", "Causality is proven", "The product cannot be involved", "Rechallenge is always required", "A", "Dechallenge is informative but must be interpreted with other evidence."),
            _q("Two reports use different names for the same suspected product. What should be done before signal analysis?", "Normalize and verify product identity using appropriate reference information", "Treat them as unrelated products", "Merge them without verification", "Delete the less common name", "A", "Accurate product identification is essential for reliable signal detection."),
            _q("A serious event is reported with incomplete clinical information. What is the best next step?", "Prioritize obtaining relevant missing information while preserving the original report and traceability", "Close the report as invalid immediately", "Invent missing clinical details", "Wait until all information is complete before recording it", "A", "Safety processing should preserve the report while actively addressing critical information gaps."),
            _q("A safety database shows a sudden increase in reports from one site. What should be checked before calling it a true signal?", "Reporting patterns, exposure volume, data quality and possible changes in reporting behavior", "Only the largest individual case", "Whether the product packaging changed color", "Whether the site has the highest staff count", "A", "Changes in reporting or exposure can create apparent signals that require contextual evaluation."),
            _q("Why is coding consistency important when analyzing adverse events?", "Different terms for clinically similar events can otherwise fragment the signal", "Coding guarantees causality", "Coding eliminates the need for case review", "Coding should be changed for each report", "A", "Consistent terminology supports meaningful aggregation and analysis."),
        ],
        ADVANCED: [
            _q("A disproportionality analysis identifies a potential signal for an AYUSH product, but reporting volume is low and the event has several alternative causes. What is the best interpretation?", "Treat it as a signal for further clinical and epidemiological assessment, not proof of causality", "Declare the product unsafe immediately", "Ignore it because the reporting volume is low", "Assume every report is causal", "A", "Signal detection identifies patterns for evaluation; it does not establish causality by itself."),
            _q("A safety signal appears only after a major awareness campaign increases reporting. What should be investigated?", "Whether increased reporting reflects stimulated reporting rather than a corresponding increase in event incidence", "Assume incidence doubled", "Delete all reports after the campaign", "Treat the signal as disproven", "A", "Stimulated reporting can alter reporting frequency without proving a change in incidence."),
            _q("Two products contain similar ingredients and have overlapping adverse-event reports. What is critical before attributing a signal to one product?", "Assess product composition, exposure, timing, alternative causes and case-level evidence", "Use the product with more reports automatically", "Combine all reports and assign causality to both", "Ignore co-medications", "A", "Attribution requires case-level and exposure-specific assessment."),
            _q("A signal is clinically plausible but epidemiological evidence is inconclusive. What is the most defensible safety communication?", "Describe the evidence, uncertainty and actions for further monitoring without overstating causality", "State that causality is confirmed", "State that no risk exists", "Report only the strongest cases", "A", "Safety communication should match the strength and uncertainty of evidence."),
            _q("A cluster of serious events occurs in a population with a high background rate of the same condition. What is important for interpretation?", "Compare the observed pattern with appropriate background incidence and exposure information", "Assume all events are product-related", "Ignore the background rate", "Use only the most severe case", "A", "Background incidence is important when evaluating whether observed events exceed expectation."),
            _q("A pharmacovigilance database contains duplicate reports submitted through different channels. What is the main analytical risk?", "Double-counting can inflate apparent reporting frequency and distort signal detection", "Duplicates always improve sensitivity without downside", "Duplicates prove a stronger causal relationship", "Duplicates should be treated as independent exposures", "A", "Duplicate cases can bias quantitative safety analyses if not identified and reconciled."),
        ],
    },
}


def _role_family(role_name: str) -> Optional[str]:
    """Map an AYUSH target role to a domain-specific question family."""
    key = _normalise_skill_name(role_name)
    families = {
        "clinical data": ("clinical data", "health informatics", "data associate", "clinical documentation"),
        "fundamental research": ("fundamental research", "research assistant", "research associate", "research project", "evidence synthesis"),
        "pharmacovigilance": ("pharmacovigilance", "safety monitoring"),
        "medicinal plants": ("medicinal plant", "plant survey"),
        "pharmacognosy": ("pharmacognosy",),
        "drug development": ("drug development", "drug research", "product development"),
        "quality": ("quality control", "quality assurance", "standardization", "regulatory", "gmp"),
        "public health": ("public health", "epidemiology", "community health"),
    }
    for family, needles in families.items():
        if any(n in key for n in needles):
            return family
    return None


def _role_specific_question(role_name: str, skill_name: str, stage: str, index: int):
    family = _role_family(role_name)
    if not family:
        return None
    pool = ROLE_DEEP_BANK.get(family, {}).get(stage, [])
    if not pool:
        return None
    return pool[index % len(pool)]


TECHNICAL_ALIASES = {
    "research methodology": "research methodology",
    "methodology": "research methodology",
    "research methods": "research methodology",
    "research ethics": "research ethics",
    "ethics": "research ethics",
    "clinical research": "clinical research",
    "clinical documentation": "clinical documentation",
    "documentation": "clinical documentation",
    "clinical data": "clinical data management",
    "clinical data management": "clinical data management",
    "data analysis": "data analysis",
    "research data analysis": "data analysis",
    "data management": "data management",
    "data analytics": "data analysis",
    "statistics": "statistics",
    "biostatistics": "statistics",
    "ayush systems overview": "ayush systems overview",
    "ayush": "ayush systems overview",
    "fundamental research": "fundamental research",
    "basic research": "fundamental research",
    "biochemistry": "biochemistry",
    "pharmacognosy": "pharmacognosy",
    "pharmacognosy research": "pharmacognosy",
    "medicinal plants": "medicinal plants",
    "medicinal plant research": "medicinal plants",
    "pharmacology": "pharmacology",
    "pharmacological research": "pharmacological research",
    "drug development": "drug development",
    "drug research": "drug development",
    "quality control": "quality control",
    "quality assurance": "quality control",
    "standardization": "standardization",
    "gmp": "gmp",
    "regulatory": "regulatory compliance",
    "regulatory compliance": "regulatory compliance",
    "pharmacovigilance": "pharmacovigilance",
    "safety monitoring": "pharmacovigilance",
    "microbiology": "microbiology",
    "biotechnology": "biotechnology",
    "public health": "public health",
    "epidemiology": "epidemiology",
    "health informatics": "health informatics",
    "digital health": "health informatics",
    "literature review": "literature review",
    "evidence synthesis": "evidence synthesis",
    "scientific writing": "scientific writing",
    "traditional knowledge": "traditional knowledge",
    "literary research": "literary research",
    "yoga": "yoga",
    "naturopathy": "naturopathy",
    "siddha": "siddha",
    "unani": "unani",
    "homoeopathy": "homoeopathy",
    "homeopathy": "homoeopathy",
    "sowa-rigpa": "sowa-rigpa",
    "sowa rigpa": "sowa-rigpa",
}

# Additional high-frequency role skills.
TECHNICAL_BANK["data management"] = {
    FOUNDATION: _q(
        "What is the purpose of a data dictionary in a research project?",
        "Define variables, formats and permitted values consistently",
        "Store only the final statistical results",
        "Replace source records",
        "Allow each analyst to use different variable meanings",
        "A",
        "A data dictionary creates a shared definition for variables and their permitted representations.",
    ),
    APPLIED: _q(
        "A study team discovers that the same response is coded as 1 in one file and 'Yes' in another. What should happen before merging the files?",
        "Document and apply a consistent coding map after confirming that the values have the same meaning",
        "Merge the files without changes because the values are both valid",
        "Convert every value to zero and rebuild the variable",
        "Choose whichever coding produces fewer missing values",
        "A",
        "Consistent semantic coding is necessary for safe data integration.",
    ),
    ADVANCED: _q(
        "A research database contains an audit trail showing several changes to a primary outcome after data lock. What should a data manager investigate first?",
        "Who made the changes, why they occurred and whether they followed the approved change and unlock procedures",
        "Whether the revised values improve statistical significance",
        "Whether the audit trail can be deleted after review",
        "Whether the original values should be overwritten permanently",
        "A",
        "Post-lock changes require traceable investigation against the approved data-management process.",
    ),
}

TECHNICAL_BANK["research ethics"] = {
    FOUNDATION: _q(
        "Why is informed consent important in human-participant research?",
        "It supports voluntary participation after relevant information has been provided",
        "It guarantees the study will produce the expected result",
        "It removes the need for ethics oversight",
        "It permits unlimited use of participant information",
        "A",
        "Informed consent supports voluntary participation based on appropriate information and understanding.",
    ),
    APPLIED: _q(
        "A research dataset contains identifiable participant information that is not needed for the planned analysis. What is the best data-management principle?",
        "Avoid collecting or retaining unnecessary identifiable information and apply appropriate safeguards",
        "Publish the identifiers so the dataset is transparent",
        "Share identifiers with every project member by default",
        "Keep all identifiers indefinitely regardless of purpose",
        "A",
        "Data minimization and appropriate safeguards reduce unnecessary privacy risk.",
    ),
    ADVANCED: _q(
        "A research team proposes a secondary analysis using participant data collected for a different purpose. What should be assessed before analysis?",
        "Whether the planned use is covered by the applicable consent, ethics approval and data-governance requirements",
        "Whether the new analysis produces a statistically significant result",
        "Whether the original study had a large sample size",
        "Whether participant identifiers can simply be copied into the new dataset",
        "A",
        "Secondary use of participant data requires appropriate ethical, consent and governance assessment.",
    ),
}

TECHNICAL_BANK["clinical documentation"] = {
    FOUNDATION: _q(
        "Which feature makes clinical documentation most useful for later review?",
        "It is accurate, timely, objective and traceable",
        "It records only conclusions",
        "It uses undocumented abbreviations",
        "It is changed without noting corrections",
        "A",
        "Good clinical documentation supports accuracy, timeliness, objectivity and traceability.",
    ),
    APPLIED: _q(
        "A clinical record contains a correction to an earlier entry. What is most important?",
        "The correction follows the approved process and remains traceable to the original entry",
        "The original entry is permanently deleted without a trace",
        "The correction is made without recording who made it",
        "The record is rewritten from memory",
        "A",
        "Traceable corrections preserve data integrity and accountability.",
    ),
    ADVANCED: _q(
        "A research monitor finds that clinical documentation supports an outcome value but the timing of the entry is inconsistent with the source record. What should be done?",
        "Reconcile the discrepancy against source information and document the resolution through the approved process",
        "Change the date to make the record internally consistent",
        "Ignore timing because the outcome value itself is plausible",
        "Delete the source record after copying the value",
        "A",
        "Source reconciliation and controlled documentation preserve the integrity of clinical records.",
    ),
}



def _technical_question(skill_name: str, stage: str = ADVANCED):
    """Return a genuinely domain-specific question or None.

    Unknown skills are intentionally NOT given a generic fallback question.
    """
    key = _normalise_skill_name(skill_name)
    bank_key = TECHNICAL_ALIASES.get(key)

    if not bank_key:
        for alias, candidate in TECHNICAL_ALIASES.items():
            if alias in key:
                bank_key = candidate
                break

    if not bank_key or bank_key not in TECHNICAL_BANK:
        return None

    bank = TECHNICAL_BANK[bank_key]
    return bank.get(stage) or bank.get(ADVANCED) or bank.get(APPLIED) or bank.get(FOUNDATION)


# ============================================================
# YEAR-AWARE SOFT-SKILL MCQs
# ============================================================
SOFT_SKILL_BANK = {
    FOUNDATION: [
        _q(
            "A teammate disagrees with your approach. What is the best first response?",
            "Listen to the concern and compare the reasoning",
            "End the discussion immediately",
            "Ignore the concern",
            "Ask someone else to decide without discussion",
            "A",
            "Constructive teamwork starts with listening and evaluating the concern.",
        ),
        _q(
            "You receive feedback that your work needs improvement. What should you do first?",
            "Understand the specific feedback and identify what can be improved",
            "Reject it automatically",
            "Hide the work",
            "Blame another person",
            "A",
            "Specific feedback is useful when converted into actionable improvements.",
        ),
        _q(
            "You discover a problem shortly before a deadline. What is most professional?",
            "Communicate it early, explain the impact and propose a practical next step",
            "Hide it until after submission",
            "Delete the affected work",
            "Assume somebody else will notice",
            "A",
            "Early, transparent communication helps teams manage problems responsibly.",
        ),
    ],
    APPLIED: [
        _q(
            "You are preparing a shared research report and notice that a teammate's analysis uses a different definition of the outcome. What should you do?",
            "Discuss the definition, check the agreed protocol or data dictionary and align the analysis before finalizing the report",
            "Quietly replace the teammate's result",
            "Keep both definitions without explanation",
            "Choose the definition that gives the stronger result",
            "A",
            "Shared analytical definitions should be reconciled using the agreed study documentation.",
        ),
        _q(
            "A senior colleague asks you to omit a limitation from a research presentation because it may weaken the result. What is the strongest response?",
            "Explain why the limitation matters and suggest presenting it alongside the result and its implications",
            "Remove it without discussion",
            "Add an unrelated limitation instead",
            "Change the result so the limitation appears less important",
            "A",
            "Professional scientific communication requires transparent presentation of material limitations.",
        ),
        _q(
            "Two team members have different interpretations of a dataset close to a submission deadline. What should happen next?",
            "Review the underlying data and agreed definitions together, document the decision and proceed with the supported interpretation",
            "Use the interpretation of the more senior person without checking",
            "Average the two interpretations",
            "Choose whichever interpretation produces a clearer conclusion",
            "A",
            "Evidence and shared definitions should guide disagreement resolution.",
        ),
    ],
    ADVANCED: [
        _q(
            "You identify a reproducibility problem in a colleague's analysis one day before an important submission. What is the strongest professional response?",
            "Raise the issue with specific evidence, preserve the original work and collaborate on a traceable correction or documented limitation",
            "Silently rewrite the analysis and submit it",
            "Ignore the issue because the deadline is close",
            "Remove the affected analysis without recording why",
            "A",
            "Responsible collaboration balances urgency with traceability, evidence and reproducibility.",
        ),
        _q(
            "A multidisciplinary team uses the same term differently in clinical, laboratory and data contexts. What is the best way to prevent downstream errors?",
            "Agree on an explicit shared definition and record it in the project documentation",
            "Allow each discipline to continue using its own meaning",
            "Choose the definition used by the largest team",
            "Avoid using the term in all future communication",
            "A",
            "Explicit shared terminology reduces ambiguity in multidisciplinary work.",
        ),
        _q(
            "A project lead asks you to present an uncertain finding as definitive to improve stakeholder confidence. What should you do?",
            "Present the finding with its uncertainty and explain what additional evidence would strengthen the conclusion",
            "Present it as definitive because the lead requested it",
            "Remove uncertainty from the slides only",
            "Replace the finding with a stronger result from another analysis without disclosure",
            "A",
            "Scientific and professional integrity requires claims to match the strength of evidence.",
        ),
    ],
}


# ============================================================
# YEAR-AWARE APTITUDE / RESEARCH-REASONING MCQs
# ============================================================
APTITUDE_BANK = {
    FOUNDATION: [
        _q(
            "A research team has 80 samples and tests 25% of them. How many samples are tested?",
            "20",
            "15",
            "25",
            "30",
            "A",
            "25% of 80 is 20.",
        ),
        _q(
            "A dataset contains 6, 8, 10 and 16. What is the median?",
            "9",
            "10",
            "8",
            "11",
            "A",
            "The middle two values are 8 and 10, so the median is 9.",
        ),
        _q(
            "A project has 12 tasks. Three are completed each week at a constant rate. How many weeks are needed?",
            "4",
            "3",
            "5",
            "6",
            "A",
            "12 divided by 3 is 4 weeks.",
        ),
    ],
    APPLIED: [
        _q(
            "A clinical dataset has 240 records. After validation, 15% require a data query. Approximately how many records require queries?",
            "36",
            "24",
            "30",
            "42",
            "A",
            "15% of 240 is 36.",
        ),
        _q(
            "An intervention group has 120 participants and 18 experience an event. What is the event proportion?",
            "15%",
            "12%",
            "18%",
            "20%",
            "A",
            "18 divided by 120 equals 0.15, or 15%.",
        ),
        _q(
            "A study screens 500 participants and enrolls 125. What is the screening-to-enrollment ratio in simplest form?",
            "4:1",
            "5:1",
            "3:1",
            "2:1",
            "A",
            "500:125 simplifies to 4:1.",
        ),
    ],
    ADVANCED: [
        _q(
            "A diagnostic dataset contains 1,000 observations. A model correctly classifies 180 of 200 positive cases and 720 of 800 negative cases. What is its overall accuracy?",
            "90%",
            "80%",
            "85%",
            "95%",
            "A",
            "Correct classifications are 180 + 720 = 900 out of 1,000, giving 90% accuracy.",
        ),
        _q(
            "A study estimates an effect of 1.8 with a 95% confidence interval of 1.1 to 2.9. Which statement is most defensible?",
            "The interval excludes the null value of 1, but the estimate still has uncertainty reflected by the interval",
            "The true effect must be exactly 1.8",
            "There is no uncertainty because the interval excludes 1",
            "The effect is clinically important solely because the interval excludes 1",
            "A",
            "The interval communicates uncertainty and, for a ratio measure, excluding 1 is relevant to statistical evidence against the null.",
        ),
        _q(
            "Two independent studies report effects of 0.30 and 0.60 with similar precision. Before treating the difference as a real effect modification, what should be examined?",
            "Whether the populations, interventions, outcomes and study contexts differ in ways that could explain the estimates",
            "Which study reports the larger number",
            "Whether the smaller effect should be discarded",
            "Whether averaging the two estimates proves a common effect",
            "A",
            "Differences between studies require contextual and methodological assessment before concluding true effect modification.",
        ),
    ],
}


def _academic_stage(profile: Profile) -> str:
    """Infer assessment difficulty from the student's stored education/year."""
    text = str(getattr(profile, "year_degree", "") or "").strip().lower()
    degree = str(getattr(profile, "education", "") or "").strip().lower()
    combined = f"{degree} {text}"

    # Postgraduate students receive the advanced research level.
    if any(token in combined for token in ("msc", "m.sc", "m pharm", "m.pharm", "postgraduate", "pg", "master")):
        return ADVANCED

    if any(token in text for token in ("1st", "first", "year 1", "1 year", "1st year")):
        return FOUNDATION
    if any(token in text for token in ("2nd", "second", "year 2", "2 year", "2nd year")):
        return APPLIED
    if any(token in text for token in ("3rd", "third", "year 3", "3 year", "3rd year", "4th", "fourth", "year 4", "4 year", "final")):
        return ADVANCED

    # If the field is simply a number, interpret it as undergraduate year.
    import re
    match = re.search(r"\b([1-4])\b", text)
    if match:
        return {"1": FOUNDATION, "2": APPLIED, "3": ADVANCED, "4": ADVANCED}[match.group(1)]

    # Missing/ambiguous year: use applied rather than the easiest level.
    return APPLIED


def _select_questions(bank, stage: str, count: int):
    """Return up to count questions, preferring the requested stage."""
    pool = bank.get(stage) or bank.get(ADVANCED) or bank.get(APPLIED) or bank.get(FOUNDATION) or []
    return pool[:count]


def get_assessment_for_role_raw(
    db: Session,
    role_id: int,
) -> Optional[Assessment]:
    """Read an assessment without triggering the seed process."""
    return (
        db.query(Assessment)
        .filter(Assessment.role_id == role_id)
        .first()
    )


def _normalise_test_type(test_type: Optional[str]) -> str:
    """Normalize the student-facing assessment type."""
    value = str(test_type or "Role-specific").strip().lower()
    aliases = {
        "role-specific": "Role-specific",
        "role specific": "Role-specific",
        "technical": "Role-specific",
        "technical skills": "Role-specific",
        "aptitude": "Aptitude",
        "soft skills": "Soft Skills",
        "soft-skill": "Soft Skills",
        "soft-skill assessment": "Soft Skills",
    }
    return aliases.get(value, "Role-specific")


def _normalise_difficulty(difficulty: Optional[str]) -> str:
    """Normalize the student-facing difficulty value."""
    value = str(difficulty or "Medium").strip().lower()
    aliases = {
        "easy": "Easy",
        "beginner": "Easy",
        "medium": "Medium",
        "moderate": "Medium",
        "hard": "Hard",
        "advanced": "Hard",
    }
    return aliases.get(value, "Medium")


def _stage_from_year(year: Optional[str], profile: Optional[Profile] = None) -> str:
    """Convert the UI year selection into the matching academic stage."""
    text = str(year or "").strip().lower()
    if text:
        if any(token in text for token in ("1st", "first", "year 1", "1 year")):
            return FOUNDATION
        if any(token in text for token in ("2nd", "second", "year 2", "2 year")):
            return APPLIED
        if any(token in text for token in ("3rd", "third", "year 3", "3 year", "4th", "fourth", "year 4", "4 year", "final")):
            return ADVANCED

        import re
        match = re.search(r"\b([1-4])\b", text)
        if match:
            return {"1": FOUNDATION, "2": APPLIED, "3": ADVANCED, "4": ADVANCED}[match.group(1)]

    return _academic_stage(profile) if profile else APPLIED


def _resolve_assessment_stage(
    profile: Optional[Profile],
    year: Optional[str],
    difficulty: Optional[str],
) -> str:
    """
    Resolve the question-bank stage from the student's selected year and
    requested difficulty.

    Year establishes the academic context while difficulty controls the
    actual question-bank level selected for the quiz. This keeps the API
    deterministic and makes the frontend selectors meaningful.
    """
    year_stage = _stage_from_year(year, profile)
    difficulty_value = _normalise_difficulty(difficulty)

    rank = {FOUNDATION: 1, APPLIED: 2, ADVANCED: 3}
    stage_by_rank = {1: FOUNDATION, 2: APPLIED, 3: ADVANCED}

    # Difficulty acts as an adjustment around the academic year:
    # Easy = one level easier, Medium = the year level, Hard = one level harder.
    # The result is capped to the available foundation/advanced boundaries.
    adjustment = {
        "Easy": -1,
        "Medium": 0,
        "Hard": 1,
    }[difficulty_value]

    resolved_rank = max(1, min(3, rank[year_stage] + adjustment))
    return stage_by_rank[resolved_rank]



# ============================================================
# AYUSH TOPIC INTELLIGENCE
# ============================================================
# Topic clusters are intentionally AYUSH-only. They reuse the existing
# AYUSH technical question banks rather than introducing non-AYUSH questions.

AYUSH_TOPIC_GROUPS = {
    "AYUSH Foundations": [
        "ayush systems overview", "traditional knowledge", "fundamental research",
        "research methodology", "public health", "epidemiology", "literature review",
        "evidence synthesis", "scientific writing", "research ethics", "health informatics",
    ],
    "Research & Evidence": [
        "fundamental research", "research methodology", "clinical research",
        "clinical data management", "data analysis", "statistics", "literature review",
        "evidence synthesis", "scientific writing", "research ethics", "data management",
        "biochemistry",
    ],
    "Clinical & Healthcare": [
        "clinical research", "clinical data management", "pharmacology", "pharmacovigilance",
        "epidemiology", "public health", "health informatics", "biochemistry", "microbiology",
        "research methodology", "ayush systems overview",
    ],
    "Pharmaceutical & Product Development": [
        "pharmacognosy", "medicinal plants", "pharmacology", "pharmacological research",
        "drug development", "quality control", "standardization", "gmp", "regulatory compliance",
        "microbiology", "biotechnology", "biochemistry",
    ],
    "Quality, Standardization & GMP": [
        "quality control", "standardization", "gmp", "regulatory compliance", "pharmacognosy",
        "medicinal plants", "microbiology", "biotechnology", "drug development", "pharmacology",
        "pharmacological research",
    ],
    "Drug Safety & Regulatory": [
        "pharmacovigilance", "regulatory compliance", "clinical research", "clinical data management",
        "drug development", "quality control", "standardization", "gmp", "research ethics",
        "public health", "epidemiology",
    ],
    "Medicinal Plants & Natural Products": [
        "medicinal plants", "pharmacognosy", "pharmacology", "pharmacological research",
        "drug development", "quality control", "standardization", "biochemistry", "microbiology",
        "biotechnology", "traditional knowledge",
    ],
    "Digital Health & Data": [
        "health informatics", "data analysis", "data management", "statistics", "clinical data management",
        "epidemiology", "public health", "scientific writing", "research methodology", "clinical research",
        "evidence synthesis",
    ],
    "Traditional Systems & Knowledge": [
        "ayush systems overview", "ayurveda", "yoga", "naturopathy", "siddha", "unani",
        "homoeopathy", "sowa-rigpa", "traditional knowledge", "literary research", "public health",
        "research methodology",
    ],
    "Public Health & Community AYUSH": [
        "public health", "epidemiology", "health informatics", "clinical research", "clinical data management",
        "research methodology", "research ethics", "evidence synthesis", "scientific writing",
        "ayush systems overview", "traditional knowledge",
    ],
}

CAREER_DIRECTION_TO_TOPICS = {
    "ayush research & evidence": ["Research & Evidence"],
    "clinical / healthcare services": ["Clinical & Healthcare"],
    "ayush pharmaceutical & product development": ["Pharmaceutical & Product Development"],
    "quality control / quality assurance": ["Quality, Standardization & GMP"],
    "drug standardization": ["Quality, Standardization & GMP"],
    "pharmacovigilance / drug safety": ["Drug Safety & Regulatory"],
    "medicinal plants / herbal products": ["Medicinal Plants & Natural Products"],
    "ayush education / academia": ["Research & Evidence", "Traditional Systems & Knowledge"],
    "public health / community ayush": ["Public Health & Community AYUSH"],
    "regulatory / compliance": ["Drug Safety & Regulatory", "Quality, Standardization & GMP"],
    "ayush digital health / informatics": ["Digital Health & Data"],
    "industry / innovation": ["Pharmaceutical & Product Development", "Quality, Standardization & GMP"],
    "entrepreneurship": ["Pharmaceutical & Product Development", "Public Health & Community AYUSH"],
}


def _profile_ayush_preferences(profile: Optional[Profile]) -> dict[str, list[str]]:
    raw = str(getattr(profile, "career_interests", "") or "").strip()
    if not raw:
        return {"ayush_systems": [], "career_directions": [], "work_preferences": []}
    try:
        value = json.loads(raw)
        if isinstance(value, dict):
            return {
                "ayush_systems": [str(x).strip() for x in value.get("ayush_systems", []) if str(x).strip()],
                "career_directions": [str(x).strip() for x in value.get("career_directions", []) if str(x).strip()],
                "work_preferences": [str(x).strip() for x in value.get("work_preferences", []) if str(x).strip()],
            }
    except Exception:
        pass
    return {"ayush_systems": [], "career_directions": [], "work_preferences": []}


def _recommended_topics(profile: Optional[Profile], role_name: str, required_skills: list[str]) -> list[str]:
    prefs = _profile_ayush_preferences(profile)
    scores = {topic: 0 for topic in AYUSH_TOPIC_GROUPS}
    for direction in prefs["career_directions"]:
        for topic in CAREER_DIRECTION_TO_TOPICS.get(direction.strip().lower(), []):
            scores[topic] += 5
    role_text = _normalise_skill_name(role_name)
    for topic, banks in AYUSH_TOPIC_GROUPS.items():
        scores[topic] += sum(2 for skill in required_skills if _normalise_skill_name(skill) in set(banks))
        if any(token in role_text for token in _normalise_skill_name(topic).split() if len(token) > 4):
            scores[topic] += 1
    return sorted(scores, key=lambda name: (-scores[name], name))


def _resolve_assessment_topic(
    profile: Optional[Profile],
    role_name: str,
    required_skills: list[str],
    requested_topic: Optional[str],
) -> str:
    requested = str(requested_topic or "").strip()
    if requested:
        if requested not in AYUSH_TOPIC_GROUPS:
            raise HTTPException(status_code=400, detail="Invalid AYUSH assessment topic")
        return requested
    recommended = _recommended_topics(profile, role_name, required_skills)
    return recommended[0] if recommended else next(iter(AYUSH_TOPIC_GROUPS))


def _topic_question_pool(topic: str, stage: str, role_id: int) -> list[tuple[str, tuple]]:
    import hashlib
    pool = []
    seen = set()
    for bank_key in AYUSH_TOPIC_GROUPS.get(topic, []):
        bank = TECHNICAL_BANK.get(bank_key)
        if not bank:
            continue
        item = bank.get(stage)
        if not item:
            continue
        signature = item[0]
        if signature in seen:
            continue
        seen.add(signature)
        pool.append((bank_key, item))
    if pool:
        seed = int(hashlib.sha1(f"{role_id}|{topic}|{stage}".encode()).hexdigest()[:8], 16)
        offset = seed % len(pool)
        pool = pool[offset:] + pool[:offset]
    return pool


def _select_topic_questions(topic: str, stages: list[str], count: int, role_id: int) -> list[tuple[str, tuple]]:
    selected = []
    used = set()
    for index in range(count):
        stage = stages[index % len(stages)]
        for bank_key, item in _topic_question_pool(topic, stage, role_id):
            if item[0] not in used:
                selected.append((bank_key, item))
                used.add(item[0])
                break
    return selected


def _topic_from_category(category: Optional[str]) -> Optional[str]:
    value = str(category or "")
    marker = "|topic="
    if marker not in value:
        return None
    return value.split(marker, 1)[1].split("|", 1)[0].strip() or None

def _assessment_config_id(
    role_id: int,
    test_type: str,
    year: str,
    difficulty: str,
    topic: str = "",
) -> str:
    """Create a stable ID for one role/year/type/difficulty combination."""
    import hashlib

    raw = f"{role_id}|{test_type}|{year}|{difficulty}|{topic}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def _assessment_config_token(config_id: str) -> int:
    """Encode a config ID into a compact negative integer for in-progress attempts."""
    return -int(config_id[:6], 16)


def _assessment_marker(
    test_type: str,
    stage: str,
    difficulty: str,
    year: Optional[str],
    config_id: Optional[str] = None,
) -> str:
    """Return compact metadata stored in Assessment.description."""
    safe_year = str(year or "").strip() or "Profile"
    config = config_id or "legacy"
    return (
        f"[SkillNova-v5|type={test_type}|stage={stage}|"
        f"difficulty={difficulty}|year={safe_year}|cfg={config}]"
    )


def _question_config_id(question: AssessmentQuestion) -> Optional[str]:
    """Read the config marker from a stored question category."""
    category = str(getattr(question, "category", "") or "")
    marker = "|cfg="
    if marker not in category:
        return None
    value = category.split(marker, 1)[1].split("|", 1)[0].strip()
    return value or None


def _clean_question_category(category: Optional[str]) -> str:
    """Remove internal config metadata before sending a category to the UI."""
    value = str(category or "")
    return value.split("|cfg=", 1)[0] or value


def _extract_assessment_test_type(description: Optional[str]) -> str:
    """Recover the test type from an assessment description when possible."""
    text = str(description or "")
    marker = "|type="
    if marker in text:
        value = text.split(marker, 1)[1].split("|", 1)[0]
        return _normalise_test_type(value)
    return "Role-specific"


def _stage_sequence(
    year_stage: str,
    difficulty: str,
    count: int,
) -> list[str]:
    """
    Build a year + difficulty aware stage sequence.

    The academic year is the student's fixed context. Difficulty then changes
    the mix of foundation/applied/advanced questions. This intentionally avoids
    collapsing 3rd/4th-year Medium and Hard into the exact same question set.
    """
    rank = {FOUNDATION: 1, APPLIED: 2, ADVANCED: 3}
    stage_by_rank = {1: FOUNDATION, 2: APPLIED, 3: ADVANCED}
    base = rank.get(year_stage, 2)
    difficulty = _normalise_difficulty(difficulty)

    if difficulty == "Easy":
        # Easy emphasizes the level below the student's academic stage, but
        # keeps one question at the student's level when possible. At the
        # boundaries we mix in the nearest available stage so Easy is still
        # distinguishable from Medium.
        ranks = [max(1, base - 1), base, (2 if base == 1 else max(1, base - 1))]
    elif difficulty == "Hard":
        # Hard emphasizes the next level. For a 3rd/4th-year student, where
        # Advanced is already the ceiling, one applied question is retained
        # so Hard is not an identical copy of Medium.
        ranks = [min(3, base + 1), min(3, base + 1), max(1, base - 1)]
    else:
        ranks = [base, base, base]

    sequence = [stage_by_rank[r] for r in ranks]
    if count <= len(sequence):
        return sequence[:count]
    return [sequence[i % len(sequence)] for i in range(count)]


def _select_questions_for_bank(
    bank: dict,
    stages: list[str],
    count: int,
    role_id: int,
) -> list[tuple]:
    """Select questions deterministically using role + stage, without randomness."""
    import hashlib

    selected = []
    used = set()
    for index in range(count):
        stage = stages[index % len(stages)]
        pool = bank.get(stage) or []
        if not pool:
            continue

        seed = int(
            hashlib.sha1(f"{role_id}|{stage}|{index}".encode("utf-8")).hexdigest()[:8],
            16,
        )
        # The bank is intentionally small; rotation makes the selected role
        # influence which question appears without exposing any answer data.
        offset = seed % len(pool)
        item = pool[offset]
        if len(pool) > 1:
            for step in range(len(pool)):
                candidate = pool[(offset + step) % len(pool)]
                signature = candidate[0] if candidate else str(candidate)
                if signature not in used:
                    item = candidate
                    break

        signature = item[0] if item else str(item)
        used.add(signature)
        selected.append(item)

    return selected


def _questions_for_test_type(
    questions: list[AssessmentQuestion],
    test_type: str,
) -> list[AssessmentQuestion]:
    """Filter an assessment's stored questions to the selected quiz type."""
    normalized = _normalise_test_type(test_type)
    return [q for q in questions if _clean_question_category(q.category) == {
        "Aptitude": APTITUDE,
        "Soft Skills": SOFT_SKILLS,
        "Role-specific": TECHNICAL,
    }[normalized]]


def _questions_for_config(
    db: Session,
    assessment_id: int,
    config_id: str,
) -> list[AssessmentQuestion]:
    """Return only questions belonging to one assessment configuration."""
    questions = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.assessment_id == assessment_id)
        .order_by(AssessmentQuestion.order_index.asc(), AssessmentQuestion.id.asc())
        .all()
    )
    return [q for q in questions if _question_config_id(q) == config_id]


def _attempt_config_id(
    db: Session,
    attempt: AssessmentAttempt,
) -> Optional[str]:
    """
    Recover the stable configuration key for an attempt.

    New attempts store it directly in AssessmentAttempt.configuration_key.
    The response/question fallback keeps older attempts compatible.
    """
    stored = str(getattr(attempt, "configuration_key", "") or "").strip()
    if stored and stored != "legacy":
        return stored

    response = (
        db.query(AssessmentResponse)
        .filter(AssessmentResponse.attempt_id == attempt.id)
        .first()
    )
    if not response:
        return stored or None

    question = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.id == response.question_id)
        .first()
    )
    return _question_config_id(question) if question else (stored or None)


def _attempt_matches_config(
    db: Session,
    attempt: AssessmentAttempt,
    config_id: str,
) -> bool:
    """Return whether an attempt belongs to the requested configuration."""
    actual = _attempt_config_id(db, attempt)
    if not actual:
        return False
    # In-progress attempts store a short token, while submitted attempts have
    # the full question marker. Compare using the same prefix.
    return actual == config_id or actual == config_id[:6]


def ensure_assessment_for_role(
    db: Session,
    role_id: int,
    profile: Optional[Profile] = None,
    test_type: str = "Role-specific",
    year: Optional[str] = None,
    difficulty: str = "Medium",
    topic: Optional[str] = None,
) -> Optional[Assessment]:
    """Return/create the shared assessment container for one AYUSH configuration."""
    from ..models import Role, RoleSkillRequirement

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return None

    normalized_type = _normalise_test_type(test_type)
    normalized_difficulty = _normalise_difficulty(difficulty)
    profile_year = str(getattr(profile, "year_degree", "") or "").strip()
    if not profile_year:
        raise HTTPException(
            status_code=400,
            detail="Set your current year of study in My Profile before starting an assessment.",
        )

    requirements = (
        db.query(RoleSkillRequirement)
        .filter(RoleSkillRequirement.role_id == role.id)
        .order_by(RoleSkillRequirement.id.asc())
        .all()
    )
    technical_skills = []
    seen = set()
    for requirement in requirements:
        skill = db.query(Skill).filter(Skill.id == getattr(requirement, "skill_id", None)).first()
        if not skill:
            continue
        key = _normalise_skill_name(skill.name)
        if key and key not in seen:
            seen.add(key)
            technical_skills.append(skill)

    required_skill_names = [str(skill.name) for skill in technical_skills]
    selected_topic = (
        _resolve_assessment_topic(profile, role.name, required_skill_names, topic)
        if normalized_type == "Role-specific" else ""
    )

    year_stage = _stage_from_year(profile_year, profile)
    stages = _stage_sequence(year_stage, normalized_difficulty, 10)
    config_id = _assessment_config_id(
        role_id, normalized_type, profile_year, normalized_difficulty, selected_topic
    )

    assessment = db.query(Assessment).filter(Assessment.role_id == role_id).first()
    if assessment is None:
        assessment = Assessment(
            role_id=role.id,
            title=f"{role.name} Assessment",
            description="AYUSH assessment container with role, difficulty and competency-topic configurations.",
        )
        db.add(assessment)
        db.flush()

    if _questions_for_config(db, assessment.id, config_id):
        return assessment

    base_order = 100000 + int(config_id[:6], 16) * 10
    order_index = base_order
    added = 0

    if normalized_type == "Role-specific":
        topic_questions = _select_topic_questions(selected_topic, stages, 10, role_id)
        if len(topic_questions) < 10:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"The AYUSH topic '{selected_topic}' currently has only "
                    f"{len(topic_questions)} unique questions for this configuration. "
                    "Add more questions to that AYUSH topic before launching it."
                ),
            )
        for bank_key, item in topic_questions:
            question, a, b, c, d, correct, explanation = item
            skill = db.query(Skill).filter(Skill.name.ilike(bank_key)).first()
            db.add(AssessmentQuestion(
                assessment_id=assessment.id,
                skill_id=skill.id if skill else None,
                category=f"{TECHNICAL}|topic={selected_topic}|cfg={config_id}",
                question=question,
                option_a=a,
                option_b=b,
                option_c=c,
                option_d=d,
                correct_option=correct,
                explanation=explanation,
                order_index=order_index,
            ))
            order_index += 1
            added += 1
    elif normalized_type == "Soft Skills":
        for item in _select_questions_for_bank(SOFT_SKILL_BANK, stages[:3], 3, role_id):
            question, a, b, c, d, correct, explanation = item
            db.add(AssessmentQuestion(
                assessment_id=assessment.id, skill_id=None,
                category=f"{SOFT_SKILLS}|cfg={config_id}",
                question=question, option_a=a, option_b=b, option_c=c, option_d=d,
                correct_option=correct, explanation=explanation, order_index=order_index,
            ))
            order_index += 1
            added += 1
    else:
        for item in _select_questions_for_bank(APTITUDE_BANK, stages[:3], 3, role_id):
            question, a, b, c, d, correct, explanation = item
            db.add(AssessmentQuestion(
                assessment_id=assessment.id, skill_id=None,
                category=f"{APTITUDE}|cfg={config_id}",
                question=question, option_a=a, option_b=b, option_c=c, option_d=d,
                correct_option=correct, explanation=explanation, order_index=order_index,
            ))
            order_index += 1
            added += 1

    db.flush()
    if added == 0:
        raise HTTPException(status_code=404, detail=f"No {normalized_type.lower()} questions are available for this role yet.")
    db.commit()
    db.refresh(assessment)
    return assessment


def get_assessment_for_role(
    db: Session,
    role_id: int,
    profile: Optional[Profile] = None,
    test_type: str = "Role-specific",
    year: Optional[str] = None,
    difficulty: str = "Medium",
    topic: Optional[str] = None,
) -> Optional[Assessment]:
    """Return/create the role assessment using the requested quiz settings."""
    return ensure_assessment_for_role(
        db,
        role_id,
        profile=profile,
        test_type=test_type,
        year=year,
        difficulty=difficulty,
        topic=topic,
    )

def get_question_list(
    db: Session,
    assessment_id: int,
):
    """
    Return assessment questions in deterministic order.
    """

    return (
        db.query(AssessmentQuestion)
        .filter(
            AssessmentQuestion.assessment_id
            == assessment_id
        )
        .order_by(
            AssessmentQuestion.order_index.asc(),
            AssessmentQuestion.id.asc(),
        )
        .all()
    )


def get_existing_attempt(
    db: Session,
    student_id: int,
    assessment_id: int,
    configuration_key: Optional[str] = None,
) -> Optional[AssessmentAttempt]:
    """Find the student's existing attempt for an optional configuration."""

    query = (
        db.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.student_id == student_id,
            AssessmentAttempt.assessment_id == assessment_id,
        )
    )

    if configuration_key:
        query = query.filter(
            AssessmentAttempt.configuration_key == configuration_key
        )

    return query.order_by(AssessmentAttempt.id.desc()).first()


# ============================================================
# QUESTION SERIALIZATION
# ============================================================

def question_for_student(
    question: AssessmentQuestion,
) -> dict[str, Any]:
    """
    Serialize a question WITHOUT revealing the correct answer.

    This is intentionally used before submission.
    """

    return {
        "id": question.id,
        "skill_id": question.skill_id,
        "category": _clean_question_category(question.category),
        "topic": _topic_from_category(question.category),
        "question": question.question,
        "options": {
            "A": question.option_a,
            "B": question.option_b,
            "C": question.option_c,
            "D": question.option_d,
        },
        "order": question.order_index,
    }


def question_result(
    question: AssessmentQuestion,
    response: AssessmentResponse,
) -> dict[str, Any]:
    """
    Serialize a submitted question result.

    Correct answer becomes visible only after submission.
    """

    selected = normalize_option(
        response.selected_option
    )

    correct = normalize_option(
        question.correct_option
    )

    return {
        "question_id": question.id,
        "skill_id": question.skill_id,
        "category": _clean_question_category(question.category),
        "topic": _topic_from_category(question.category),
        "question": question.question,
        "options": {
            "A": question.option_a,
            "B": question.option_b,
            "C": question.option_c,
            "D": question.option_d,
        },
        "selected_option": selected,
        "correct_option": correct,
        "is_correct": (
            selected == correct
        ),
        "explanation": (
            question.explanation or ""
        ),
        "order": question.order_index,
    }


# ============================================================
# SKILL RESULT HELPERS
# ============================================================

def build_skill_result(
    skill_id: int,
    skill_name: str,
    correct_count: int,
    total_questions: int,
) -> dict[str, Any]:
    """Build one skill assessment result."""

    percentage = calculate_percentage(
        correct_count,
        total_questions,
    )

    return {
        "skill_id": skill_id,
        "skill": skill_name,
        # Student-facing results intentionally expose only the
        # categorical status. Numeric assessment scores remain in
        # the database for internal readiness/matching calculations.
        "status": calculate_skill_status(
            correct_count,
            total_questions,
        ),
    }


def get_skill_results_for_attempt(
    db: Session,
    attempt_id: int,
) -> list[dict[str, Any]]:
    """Return all skill-level results for an attempt."""

    results = (
        db.query(SkillAssessmentResult)
        .filter(
            SkillAssessmentResult.attempt_id
            == attempt_id
        )
        .all()
    )

    output = []

    for result in results:
        skill = (
            db.query(Skill)
            .filter(
                Skill.id == result.skill_id
            )
            .first()
        )

        if not skill:
            continue

        output.append(
            build_skill_result(
                skill_id=skill.id,
                skill_name=skill.name,
                correct_count=result.correct_count,
                total_questions=result.total_questions,
            )
        )

    output.sort(
        key=lambda x: x["skill"]
    )

    return output


# ============================================================
# UPDATE STUDENT SKILL FROM ASSESSMENT
# ============================================================

def update_student_skill_from_result(
    db: Session,
    profile: Profile,
    skill_id: int,
    score: int,
    total_questions: int,
) -> StudentSkill:
    """
    Update the student's calculated skill level.

    IMPORTANT:
    This is assessment-derived.

    The student never enters this value manually.
    """

    student_skill = (
        db.query(StudentSkill)
        .filter(
            StudentSkill.profile_id
            == profile.id,
            StudentSkill.skill_id
            == skill_id,
        )
        .first()
    )

    if not student_skill:
        student_skill = StudentSkill(
            profile_id=profile.id,
            skill_id=skill_id,
            proficiency=0,
        )

        db.add(student_skill)
        db.flush()

    percentage = calculate_percentage(
        score,
        total_questions,
    )

    student_skill.proficiency = percentage

    return student_skill


# ============================================================
# AYUSH ASSESSMENT TOPICS
# ============================================================

@router.get("/{role_id}/topics")
def assessment_topics(
    role_id: int,
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    profile = get_student_profile(db, user)
    from ..models import Role, RoleSkillRequirement
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    required = (
        db.query(Skill)
        .join(RoleSkillRequirement, RoleSkillRequirement.skill_id == Skill.id)
        .filter(RoleSkillRequirement.role_id == role_id)
        .all()
    )
    names = [str(skill.name) for skill in required]
    recommended = _recommended_topics(profile, role.name, names)
    result = []
    for rank, topic_name in enumerate(recommended):
        # Count unique bank entries across the three academic stages.
        available = len({
            item[1][0]
            for stage in (FOUNDATION, APPLIED, ADVANCED)
            for item in _topic_question_pool(topic_name, stage, role_id)
        })
        result.append({
            "name": topic_name,
            "description": f"AYUSH competency assessment covering {topic_name.lower()}.",
            "recommended": rank < 3,
            "available_questions": available,
            "ready": available >= 10,
        })
    return {"role_id": role_id, "topics": result}


# ============================================================
# CREATE ATTEMPT
# ============================================================

@router.post(
    "/{role_id}/start"
)
def start_assessment(
    role_id: int,
    test_type: str = Query("Role-specific"),
    difficulty: str = Query("Medium"),
    topic: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Start one configuration-specific assessment.

    Year is intentionally ignored from the browser request. The student's
    Profile.year_degree is the only source of truth, so the year displayed on
    the Assessment page cannot be changed independently of My Profile.
    """
    profile = get_student_profile(db, user)

    if not profile.target_role_id:
        raise HTTPException(
            status_code=400,
            detail="Select a target role before starting an assessment",
        )

    if profile.target_role_id != role_id:
        raise HTTPException(
            status_code=400,
            detail="Assessment role must match your current target role",
        )

    profile_year = str(getattr(profile, "year_degree", "") or "").strip()
    if not profile_year:
        raise HTTPException(
            status_code=400,
            detail="Set your current year of study in My Profile before starting an assessment.",
        )

    normalized_type = _normalise_test_type(test_type)
    normalized_difficulty = _normalise_difficulty(difficulty)

    from ..models import Role, RoleSkillRequirement
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    required = (
        db.query(Skill)
        .join(RoleSkillRequirement, RoleSkillRequirement.skill_id == Skill.id)
        .filter(RoleSkillRequirement.role_id == role_id)
        .all()
    )
    resolved_topic = (
        _resolve_assessment_topic(profile, role.name, [str(x.name) for x in required], topic)
        if normalized_type == "Role-specific" else ""
    )
    config_id = _assessment_config_id(
        role_id, normalized_type, profile_year, normalized_difficulty, resolved_topic
    )

    assessment = get_assessment_for_role(
        db,
        role_id,
        profile=profile,
        test_type=normalized_type,
        year=profile_year,
        difficulty=normalized_difficulty,
        topic=resolved_topic,
    )

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="No assessment is available for this role yet",
        )

    questions = _questions_for_config(
        db,
        assessment.id,
        config_id,
    )
    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No questions are available for this assessment configuration yet",
        )

    # Each configuration gets its own attempt. This is enforced by the
    # database unique constraint on:
    # student_id + assessment_id + configuration_key.
    existing = (
        db.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.student_id == user.id,
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.configuration_key == config_id,
        )
        .order_by(AssessmentAttempt.id.desc())
        .first()
    )

    if existing:
        if existing.status == ATTEMPT_SUBMITTED:
            raise HTTPException(
                status_code=409,
                detail=(
                    "You have already completed this assessment configuration. "
                    "Change the test type or difficulty to take another assessment, "
                    "or open your previous result."
                ),
            )

        return {
            "status": "in_progress",
            "attempt_id": existing.id,
            "assessment_id": assessment.id,
            "role_id": role_id,
            "title": f"{assessment.title.split(' Assessment')[0]} {normalized_type} Assessment",
            "description": (
                f"{normalized_type} assessment for {assessment.title.split(' Assessment')[0]}. "
                f"Academic year: {profile_year}. Difficulty: {normalized_difficulty}."
            ),
            "test_type": normalized_type,
            "difficulty": normalized_difficulty,
            "topic": resolved_topic or None,
            "year": profile_year,
            "total_questions": len(questions),
            "questions": [question_for_student(q) for q in questions],
        }

    attempt = AssessmentAttempt(
        student_id=user.id,
        assessment_id=assessment.id,
        status=ATTEMPT_IN_PROGRESS,
        score=0,
        total_questions=len(questions),
        configuration_key=config_id,
        started_at=datetime.utcnow(),
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    role_name = assessment.title.split(" Assessment")[0]
    return {
        "status": "started",
        "attempt_id": attempt.id,
        "assessment_id": assessment.id,
        "role_id": role_id,
        "title": f"{role_name} {normalized_type} Assessment",
        "description": (
            f"{normalized_type} MCQ assessment for {role_name}. "
            f"Academic year: {profile_year}. Difficulty: {normalized_difficulty}. "
            "Correct answers are revealed only after submission."
        ),
        "test_type": normalized_type,
        "difficulty": normalized_difficulty,
        "topic": resolved_topic or None,
        "year": profile_year,
        "total_questions": len(questions),
        "questions": [question_for_student(q) for q in questions],
    }


# ============================================================
# SUBMIT ASSESSMENT
# ============================================================

@router.post(
    "/attempt/{attempt_id}/submit"
)
def submit_assessment(
    attempt_id: int,
    answers: dict[str, Any],
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Submit one assessment attempt.

    Expected body:

    {
        "answers": {
            "12": "A",
            "13": "C",
            "14": "B"
        }
    }

    Question IDs are keys.

    Correct answers are read ONLY from the database.
    """

    attempt = (
        db.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.id
            == attempt_id,
            AssessmentAttempt.student_id
            == user.id,
        )
        .first()
    )

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Assessment attempt not found",
        )

    if attempt.status == ATTEMPT_SUBMITTED:
        raise HTTPException(
            status_code=409,
            detail=(
                "This assessment has already "
                "been submitted. Retakes are not allowed."
            ),
        )

    if not isinstance(
        answers,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail="Answers must be an object keyed by question ID",
        )

    # Accept both {"answers": {...}} and a raw question-id map.
    if (
        set(answers.keys()) == {"answers"}
        and isinstance(answers.get("answers"), dict)
    ):
        answers = answers["answers"]

    # The legacy schema stores all configuration blocks under one Assessment
    # row. Therefore submission must grade ONLY the question IDs that were
    # actually delivered for this attempt, never every question for the role.
    submitted_ids = {str(key) for key in answers.keys()}

    if not submitted_ids:
        raise HTTPException(
            status_code=400,
            detail="Please answer all questions before submitting",
        )

    try:
        numeric_ids = [int(value) for value in submitted_ids]
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Invalid question ID in submitted answers",
        )

    questions = (
        db.query(AssessmentQuestion)
        .filter(
            AssessmentQuestion.assessment_id == attempt.assessment_id,
            AssessmentQuestion.id.in_(numeric_ids),
        )
        .order_by(AssessmentQuestion.order_index.asc(), AssessmentQuestion.id.asc())
        .all()
    )

    if not questions:
        raise HTTPException(
            status_code=400,
            detail="Assessment contains no valid questions for this attempt",
        )

    question_ids = {str(question.id) for question in questions}
    if question_ids != submitted_ids:
        raise HTTPException(
            status_code=400,
            detail="Invalid question ID in submitted answers",
        )

    # Every question in one submission must belong to the same configuration.
    config_ids = {_question_config_id(question) for question in questions}
    if None in config_ids or len(config_ids) != 1:
        raise HTTPException(
            status_code=400,
            detail="The submitted questions do not belong to one assessment configuration",
        )

    config_id = next(iter(config_ids))
    if not config_id:
        raise HTTPException(
            status_code=400,
            detail="This assessment uses an unsupported legacy question set. Please start a new configuration.",
        )

    attempt_config = _attempt_config_id(db, attempt)
    if attempt_config and attempt_config != config_id:
        raise HTTPException(
            status_code=400,
            detail="These answers belong to a different assessment configuration",
        )

    if len(questions) != int(attempt.total_questions or 0):
        raise HTTPException(
            status_code=400,
            detail="Please answer every question before submitting",
        )

    # --------------------------------------------------------
    # Grade every question.
    # --------------------------------------------------------

    total_score = 0

    skill_totals: dict[int, int] = {}
    skill_correct: dict[int, int] = {}

    result_items = []

    for question in questions:
        raw_answer = answers.get(
            str(question.id)
        )

        if not isinstance(
            raw_answer,
            str,
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid answer for question "
                    f"{question.id}"
                ),
            )

        selected = normalize_option(
            raw_answer
        )

        if not validate_option(selected):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid option for question "
                    f"{question.id}. Use A, B, C or D."
                ),
            )

        correct = grade_answer(
            selected,
            question.correct_option,
        )

        if correct:
            total_score += 1

        # ----------------------------------------------------
        # Store response.
        # ----------------------------------------------------

        existing_response = (
            db.query(AssessmentResponse)
            .filter(
                AssessmentResponse.attempt_id
                == attempt.id,
                AssessmentResponse.question_id
                == question.id,
            )
            .first()
        )

        if existing_response:
            existing_response.selected_option = selected
            existing_response.is_correct = correct
        else:
            db.add(
                AssessmentResponse(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    selected_option=selected,
                    is_correct=correct,
                )
            )

        # ----------------------------------------------------
        # Build skill-level totals.
        # ----------------------------------------------------

        if question.skill_id:
            skill_totals[
                question.skill_id
            ] = (
                skill_totals.get(
                    question.skill_id,
                    0,
                )
                + 1
            )

            if correct:
                skill_correct[
                    question.skill_id
                ] = (
                    skill_correct.get(
                        question.skill_id,
                        0,
                    )
                    + 1
                )

        result_items.append(
            {
                "question": question,
                "selected": selected,
                "correct": correct,
            }
        )

    # --------------------------------------------------------
    # Save overall attempt.
    # --------------------------------------------------------

    attempt.score = total_score
    attempt.total_questions = len(
        questions
    )
    attempt.status = ATTEMPT_SUBMITTED
    attempt.submitted_at = datetime.utcnow()

    # --------------------------------------------------------
    # Save skill-level results.
    # --------------------------------------------------------

    profile = get_student_profile(
        db,
        user,
    )

    skill_results = []

    for skill_id, total in skill_totals.items():

        correct_count = skill_correct.get(
            skill_id,
            0,
        )

        percentage = calculate_percentage(
            correct_count,
            total,
        )

        status = calculate_skill_status(
            correct_count,
            total,
        )

        existing_result = (
            db.query(SkillAssessmentResult)
            .filter(
                SkillAssessmentResult.attempt_id
                == attempt.id,
                SkillAssessmentResult.skill_id
                == skill_id,
            )
            .first()
        )

        if existing_result:
            existing_result.correct_count = (
                correct_count
            )
            existing_result.total_questions = (
                total
            )
            existing_result.score = (
                percentage
            )
            existing_result.status = status
        else:
            db.add(
                SkillAssessmentResult(
                    attempt_id=attempt.id,
                    skill_id=skill_id,
                    correct_count=correct_count,
                    total_questions=total,
                    score=percentage,
                    status=status,
                )
            )

        # ----------------------------------------------------
        # Feed assessment result into StudentSkill.
        # ----------------------------------------------------

        update_student_skill_from_result(
            db=db,
            profile=profile,
            skill_id=skill_id,
            score=correct_count,
            total_questions=total,
        )

    db.commit()

    # --------------------------------------------------------
    # Build student-facing result.
    # --------------------------------------------------------

    for item in result_items:

        result_items_question = item[
            "question"
        ]

        response = (
            db.query(AssessmentResponse)
            .filter(
                AssessmentResponse.attempt_id
                == attempt.id,
                AssessmentResponse.question_id
                == result_items_question.id,
            )
            .first()
        )

        if response:
            result_items[
                result_items.index(item)
            ] = question_result(
                result_items_question,
                response,
            )

    # Reload skill results after commit.
    skill_results = (
        get_skill_results_for_attempt(
            db,
            attempt.id,
        )
    )

    return {
        "status": "submitted",
        "attempt_id": attempt.id,
        "assessment_id": attempt.assessment_id,
        "total_questions": len(questions),
        "overall_status": calculate_skill_status(
            total_score,
            len(questions),
        ),
        "skill_results": skill_results,
        "questions": result_items,
        "message": (
            "Assessment submitted successfully. "
            "Your skill profile has been updated."
        ),
    }


# ============================================================
# GET ASSESSMENT STATUS / RESULT
# ============================================================

@router.get(
    "/{role_id}/status"
)
def assessment_status(
    role_id: int,
    test_type: str = Query("Role-specific"),
    difficulty: str = Query("Medium"),
    topic: Optional[str] = Query(None),
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Return the student's assessment state for a role.

    Does NOT expose correct answers for an unfinished attempt.
    """

    profile = get_student_profile(db, user)

    profile_year = str(getattr(profile, "year_degree", "") or "").strip()
    if not profile_year:
        raise HTTPException(
            status_code=400,
            detail="Set your current year of study in My Profile before checking assessment status.",
        )

    normalized_type = _normalise_test_type(test_type)
    normalized_difficulty = _normalise_difficulty(difficulty)
    from ..models import Role, RoleSkillRequirement
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    required = (
        db.query(Skill)
        .join(RoleSkillRequirement, RoleSkillRequirement.skill_id == Skill.id)
        .filter(RoleSkillRequirement.role_id == role_id)
        .all()
    )
    resolved_topic = (
        _resolve_assessment_topic(profile, role.name, [str(x.name) for x in required], topic)
        if normalized_type == "Role-specific" else ""
    )
    config_id = _assessment_config_id(
        role_id, normalized_type, profile_year, normalized_difficulty, resolved_topic
    )

    assessment = get_assessment_for_role(
        db,
        role_id,
        profile=profile,
        test_type=normalized_type,
        year=profile_year,
        difficulty=normalized_difficulty,
        topic=resolved_topic,
    )

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found for this role",
        )

    attempt = get_existing_attempt(
        db,
        user.id,
        assessment.id,
        configuration_key=config_id,
    )

    if not attempt:
        return {
            "status": "NOT_STARTED",
            "attempt_id": None,
            "assessment_id": assessment.id,
            "role_id": role_id,
            "title": assessment.title,
            "description": assessment.description,
        }

    if attempt.status == ATTEMPT_IN_PROGRESS:
        return {
            "status": "IN_PROGRESS",
            "attempt_id": attempt.id,
            "assessment_id": assessment.id,
            "role_id": role_id,
            "title": assessment.title,
            "description": assessment.description,
            "total_questions": attempt.total_questions,
        }

    return {
        "status": "SUBMITTED",
        "attempt_id": attempt.id,
        "assessment_id": assessment.id,
        "role_id": role_id,
        "title": assessment.title,
        "description": assessment.description,
        "total_questions": attempt.total_questions,
        "overall_status": calculate_skill_status(
            attempt.score,
            attempt.total_questions,
        ),
    }


# ============================================================
# GET FINAL RESULT
# ============================================================

@router.get(
    "/attempt/{attempt_id}/result"
)
def get_assessment_result(
    attempt_id: int,
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Return the complete submitted assessment result.

    This is the endpoint where:
    - selected answer
    - correct answer
    - correctness
    - explanations
    become visible.
    """

    attempt = (
        db.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.id
            == attempt_id,
            AssessmentAttempt.student_id
            == user.id,
        )
        .first()
    )

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Assessment attempt not found",
        )

    if attempt.status != ATTEMPT_SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail=(
                "Assessment has not been submitted yet"
            ),
        )

    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id
            == attempt.assessment_id
        )
        .first()
    )

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    questions = get_question_list(
        db,
        assessment.id,
    )

    output_questions = []

    for question in questions:

        response = (
            db.query(AssessmentResponse)
            .filter(
                AssessmentResponse.attempt_id
                == attempt.id,
                AssessmentResponse.question_id
                == question.id,
            )
            .first()
        )

        if not response:
            continue

        output_questions.append(
            question_result(
                question,
                response,
            )
        )

    skill_results = (
        get_skill_results_for_attempt(
            db,
            attempt.id,
        )
    )

    return {
        "status": "SUBMITTED",
        "attempt_id": attempt.id,
        "assessment_id": assessment.id,
        "title": assessment.title,
        "description": assessment.description,
        "total_questions": attempt.total_questions,
        "overall_status": calculate_skill_status(
            attempt.score,
            attempt.total_questions,
        ),
        "skill_results": skill_results,
        "questions": output_questions,
    }


# ============================================================
# COMPATIBILITY HELPERS
# ============================================================

def build_question_result(
    question: dict[str, Any],
    selected_option: str,
) -> dict[str, Any]:
    """
    Compatibility helper for existing SkillNova code.

    Correct answer is returned because this helper is intended
    for post-submission processing only.
    """

    selected = normalize_option(
        selected_option
    )

    correct = normalize_option(
        str(
            question[
                "correct_option"
            ]
        )
    )

    return {
        "question_id": question["id"],
        "question": question["question"],
        "selected_option": selected,
        "correct_option": correct,
        "is_correct": (
            selected == correct
        ),
        "explanation": question.get(
            "explanation",
            "",
        ),
    }


__all__ = [
    "router",
    "STRONG",
    "DEVELOPING",
    "NEEDS_IMPROVEMENT",
    "NOT_ASSESSED",
    "calculate_skill_status",
    "calculate_percentage",
    "validate_option",
    "normalize_option",
    "grade_answer",
    "build_question_result",
    "build_skill_result",
]