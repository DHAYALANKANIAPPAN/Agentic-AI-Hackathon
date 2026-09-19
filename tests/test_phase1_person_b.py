"""Unit and integration tests for Person B (Product Layer) Phase 1."""

import os
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.repository import init_db, save_learner, get_learner, log_activity, save_struggle_flag
from app.services import onboard_learner, get_learner_state
from shared.schemas.models import (
    LearnerState, SkillProfile, Skill, SkillLevel, GapList, Gap, GapStatus,
    ActivityLog, Rating, StruggleFlag
)

client = TestClient(app)
TEST_DB = "test_phase1.db"


@pytest.fixture(autouse=True)
def cleanup_test_db():
    """Ensure clean test database for each test run."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_repository_save_and_get_learner():
    """Verify save_learner and get_learner round-trip in SQLite."""
    learner = LearnerState(
        id="learner-test-1",
        profile=SkillProfile(
            skills=[Skill(name="Python", level=SkillLevel.ADVANCED, evidence="5 years experience")]
        ),
        gaps=GapList(
            target_role="AI Engineer",
            gaps=[Gap(required_skill="PyTorch", status=GapStatus.MISSING, priority=1, objectives=[])]
        ),
        hours_per_week=12.0,
        weeks_available=6,
    )
    save_learner(learner, db_path=TEST_DB)

    retrieved = get_learner("learner-test-1", db_path=TEST_DB)
    assert retrieved is not None
    assert retrieved.id == "learner-test-1"
    assert retrieved.hours_per_week == 12.0
    assert retrieved.weeks_available == 6
    assert retrieved.profile is not None
    assert len(retrieved.profile.skills) == 1
    assert retrieved.profile.skills[0].name == "Python"
    assert retrieved.gaps is not None
    assert retrieved.gaps.target_role == "AI Engineer"


def test_repository_activity_and_struggles():
    """Verify activity logging and struggle flag persistence."""
    learner = LearnerState(id="learner-act-1", hours_per_week=10.0, weeks_available=4)
    save_learner(learner, db_path=TEST_DB)

    act = ActivityLog(item_id="item-101", minutes_spent=45, rating=Rating.OK, quiz_score=85.0)
    log_activity("learner-act-1", act, db_path=TEST_DB)

    flag = StruggleFlag(skill_name="Docker", reason="Networking issues", severity="medium")
    save_struggle_flag("learner-act-1", flag, db_path=TEST_DB)

    retrieved = get_learner("learner-act-1", db_path=TEST_DB)
    assert len(retrieved.activity_log) == 1
    assert retrieved.activity_log[0].item_id == "item-101"
    assert retrieved.activity_log[0].minutes_spent == 45
    assert len(retrieved.struggle_flags) == 1
    assert retrieved.struggle_flags[0].skill_name == "Docker"


def test_services_onboard_learner():
    """Verify onboard_learner calls mock AI and saves to database."""
    resume = "Alex Mercer, Python developer with experience in SQL, Docker, and REST APIs."
    target_role = "Data Scientist"

    learner_id = onboard_learner(resume_text=resume, target_role=target_role, db_path=TEST_DB)
    assert learner_id is not None
    assert learner_id.startswith("learner-")

    state = get_learner_state(learner_id, db_path=TEST_DB)
    assert state is not None
    assert state.id == learner_id
    assert state.profile is not None
    assert len(state.profile.skills) > 0
    assert state.gaps is not None
    assert state.gaps.target_role == "Data Scientist"


def test_fastapi_onboard_and_gaps_ui():
    """Verify FastAPI UI endpoints: GET /onboard, POST /onboard, and GET /gaps/{id}."""
    # 1. GET /onboard
    get_res = client.get("/onboard")
    assert get_res.status_code == 200
    assert "Discover Your" in get_res.text
    assert 'name="target_role"' in get_res.text
    assert 'name="resume_text"' in get_res.text

    # 2. POST /onboard
    post_res = client.post(
        "/onboard",
        data={
            "target_role": "Data Scientist",
            "resume_text": "Experienced Python and SQL developer transitioning to Data Science.",
        },
        follow_redirects=False,
    )
    assert post_res.status_code == 303
    redirect_url = post_res.headers["location"]
    assert redirect_url.startswith("/gaps/learner-")
    learner_id = redirect_url.replace("/gaps/", "")

    # 3. GET /gaps/{learner_id}
    gaps_res = client.get(f"/gaps/{learner_id}")
    assert gaps_res.status_code == 200
    assert "Skill Gap Analysis" in gaps_res.text
    assert "Data Scientist" in gaps_res.text
    assert "Missing Gaps" in gaps_res.text
    assert "Extracted Profile Credentials" in gaps_res.text


def test_fastapi_gaps_404_not_found():
    """Verify 404 is returned for nonexistent learner."""
    res = client.get("/gaps/nonexistent-id-999")
    assert res.status_code == 404
