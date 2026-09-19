"""Backend services for EduPath (Member B).

Orchestrates onboarding by calling AI functions through app.provider
and saving results to SQLite repository.
"""

import uuid
from typing import Optional
from app.provider import analyze_profile, find_gaps
from app.repository import save_learner, get_learner
from shared.schemas.models import LearnerState


def onboard_learner(
    resume_text: str,
    target_role: str,
    db_path: str = "edupath.db",
) -> str:
    """Execute learner intake:

    1. Call AI analyze_profile to extract skills.
    2. Call AI find_gaps to benchmark against target role.
    3. Construct and save LearnerState to the database.
    4. Return unique learner_id.
    """
    # 1. Analyze profile from resume text
    profile = analyze_profile(form_text=resume_text, document_texts=[resume_text])

    # 2. Find skill gaps against target role
    gaps = find_gaps(profile=profile, target_role=target_role)

    # 3. Create unique learner state
    learner_id = f"learner-{uuid.uuid4().hex[:8]}"
    learner = LearnerState(
        id=learner_id,
        profile=profile,
        gaps=gaps,
        plan=None,
        activity_log=[],
        struggle_flags=[],
        hours_per_week=10.0,
        weeks_available=4,
    )

    # 4. Save to database
    save_learner(learner, db_path=db_path)

    return learner_id


def get_learner_state(
    learner_id: str,
    db_path: str = "edupath.db",
) -> Optional[LearnerState]:
    """Retrieve full LearnerState from the database."""
    return get_learner(learner_id, db_path=db_path)
