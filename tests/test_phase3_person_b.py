"""Unit and integration tests for Person B (Product Layer) Phase 3:

- Struggle detection with 4 deterministic rules and deduplication
- Adaptive feedback loop (process_progress_update)
  - No replan on easy / ok
  - Replan on new struggle flag, version increment, change reasons, completed items preservation
  - No repeated replan for existing flags
- Chat persistence (save_chat_message, get_chat_history)
- Conversational agent service (chat_with_agent)
- FastAPI chat UI and JSON endpoints (GET/POST /chat/{id}, GET/POST /api/chat/{id})
- FastAPI plan completion triggering adaptive redirect and UI rendering
- FastAPI dashboard rendering active struggle alerts
"""

import os
from datetime import datetime, timedelta
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.repository import (
    init_db,
    save_learner,
    get_learner,
    save_chat_message,
    get_chat_history,
)
from app.services import (
    detect_struggles,
    process_progress_update,
    chat_with_agent,
    seed_demo_learner,
)
from shared.schemas.models import (
    LearnerState,
    SkillProfile,
    Skill,
    SkillLevel,
    GapList,
    Gap,
    GapStatus,
    Objective,
    WeeklyPlan,
    PlanItem,
    ItemType,
    ItemStatus,
    Rating,
    ActivityLog,
    StruggleFlag,
)

client = TestClient(app)
TEST_DB = "test_phase3.db"


@pytest.fixture(autouse=True)
def setup_teardown_test_db():
    """Ensure clean test database for each test run."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass


def test_detect_struggles_all_rules():
    """Verify all 4 struggle detection rules and deduplication."""
    now = datetime.utcnow()

    # Rule 1: Same skill rated 'struggled' 2+ times
    # Rule 2: Quiz score below 60%
    # Rule 3: Aged friction older than 7 days
    # Rule 4: Items skipped or retried 2+ times
    learner = LearnerState(
        id="learner-struggle-test",
        gaps=GapList(
            target_role="ML Engineer",
            gaps=[
                Gap(required_skill="PyTorch", status=GapStatus.MISSING, priority=1, objectives=[]),
                Gap(required_skill="Docker", status=GapStatus.MISSING, priority=2, objectives=[]),
            ],
        ),
        plan=WeeklyPlan(
            version=1,
            weeks={
                1: [
                    PlanItem(id="item-pt-1", skill_ref="PyTorch", item_type=ItemType.LEARNING, description="Tensors"),
                    PlanItem(id="item-pt-2", skill_ref="PyTorch", item_type=ItemType.PRACTICE, description="Autograd"),
                    PlanItem(id="item-dk-1", skill_ref="Docker", item_type=ItemType.LEARNING, description="Containers", status=ItemStatus.SKIPPED),
                ]
            },
        ),
        activity_log=[
            # PyTorch rated struggled twice (Rule 1)
            ActivityLog(item_id="item-pt-1", minutes_spent=40, rating=Rating.STRUGGLED, quiz_score=80.0, timestamp=now),
            ActivityLog(item_id="item-pt-2", minutes_spent=50, rating=Rating.STRUGGLED, quiz_score=55.0, timestamp=now),  # Also Rule 2 (quiz < 60)
            # Docker aged friction older than 8 days (Rule 3)
            ActivityLog(item_id="item-dk-1", minutes_spent=30, rating=Rating.STRUGGLED, timestamp=now - timedelta(days=9)),
            # Item dk-1 attempted twice in log + marked skipped in plan -> attempts >= 2 (Rule 4)
            ActivityLog(item_id="item-dk-1", minutes_spent=25, rating=Rating.OK, timestamp=now),
        ],
        hours_per_week=10.0,
        weeks_available=4,
    )

    flags = detect_struggles(learner)
    assert len(flags) >= 3

    flag_skills = {f.skill_name for f in flags}
    assert "PyTorch" in flag_skills
    assert "Docker" in flag_skills

    # Verify rule 1 detected
    assert any("Rated 'struggled' 2+ times" in f.reason for f in flags if f.skill_name == "PyTorch")

    # Verify rule 2 detected
    assert any("Low quiz score of 55.0%" in f.reason for f in flags if f.skill_name == "PyTorch")

    # Verify rule 3 detected
    assert any("Study friction unresolved for over 7 days" in f.reason for f in flags if f.skill_name == "Docker")

    # Verify rule 4 detected
    assert any("Items skipped or retried 2+ times" in f.reason for f in flags if f.skill_name == "Docker")


def test_adaptive_feedback_loop_no_replan_on_easy_or_ok():
    """Verify that completing an item with 'ok' or 'easy' does NOT trigger replan."""
    learner = LearnerState(
        id="learner-smooth",
        gaps=GapList(
            target_role="Data Analyst",
            gaps=[Gap(required_skill="SQL", status=GapStatus.MISSING, priority=1, objectives=[])],
        ),
        plan=WeeklyPlan(
            version=1,
            weeks={
                1: [
                    PlanItem(id="item-sql-1", skill_ref="SQL", item_type=ItemType.LEARNING, description="Joins"),
                    PlanItem(id="item-sql-2", skill_ref="SQL", item_type=ItemType.PRACTICE, description="Subqueries"),
                ]
            },
        ),
        hours_per_week=10.0,
        weeks_available=4,
    )
    save_learner(learner, db_path=TEST_DB)

    # Complete with OK rating
    updated, replanned = process_progress_update(
        learner_id="learner-smooth",
        item_id="item-sql-1",
        minutes_spent=45,
        self_rating=Rating.OK,
        quiz_score=85.0,
        db_path=TEST_DB,
    )

    assert replanned is False
    assert updated.plan.version == 1
    assert len(updated.struggle_flags) == 0
    assert updated.plan.weeks[1][0].status == ItemStatus.DONE


def test_adaptive_feedback_loop_triggers_replan_on_new_struggle():
    """Verify that a newly detected struggle triggers replan, version increment, and completed items preservation."""
    learner = LearnerState(
        id="learner-struggling",
        gaps=GapList(
            target_role="AI Engineer",
            gaps=[Gap(required_skill="PyTorch", status=GapStatus.MISSING, priority=1, objectives=[])],
        ),
        plan=WeeklyPlan(
            version=1,
            weeks={
                1: [
                    PlanItem(id="item-p1", skill_ref="PyTorch", item_type=ItemType.LEARNING, description="Tensors"),
                    PlanItem(id="item-p2", skill_ref="PyTorch", item_type=ItemType.PRACTICE, description="Autograd"),
                ],
                2: [
                    PlanItem(id="item-p3", skill_ref="PyTorch", item_type=ItemType.PROJECT, description="Classifier"),
                ],
            },
        ),
        hours_per_week=10.0,
        weeks_available=4,
    )
    save_learner(learner, db_path=TEST_DB)

    # First struggle: 1st time struggling with PyTorch (no flag yet because rule 1 needs 2+)
    updated_1, replanned_1 = process_progress_update(
        learner_id="learner-struggling",
        item_id="item-p1",
        minutes_spent=60,
        self_rating=Rating.STRUGGLED,
        quiz_score=75.0,
        db_path=TEST_DB,
    )
    assert replanned_1 is False
    assert updated_1.plan.version == 1

    # Second struggle on same skill: hits Rule 1 (2+ times struggled) -> triggers REPLAN!
    updated_2, replanned_2 = process_progress_update(
        learner_id="learner-struggling",
        item_id="item-p2",
        minutes_spent=70,
        self_rating=Rating.STRUGGLED,
        quiz_score=72.0,
        db_path=TEST_DB,
    )

    assert replanned_2 is True
    assert updated_2.plan.version == 2
    assert len(updated_2.struggle_flags) > 0
    assert updated_2.struggle_flags[0].skill_name == "PyTorch"
    assert any("Adaptive replan: detected struggle" in r for r in updated_2.plan.change_reasons)

    # Crucial: verify completed items were preserved!
    assert updated_2.plan.weeks[1][0].status == ItemStatus.DONE
    assert updated_2.plan.weeks[1][0].minutes_spent == 60
    assert updated_2.plan.weeks[1][1].status == ItemStatus.DONE
    assert updated_2.plan.weeks[1][1].minutes_spent == 70

    # Repeating with the same struggle flag does NOT trigger a second replan
    # Add a 3rd item to plan week 2 and complete with struggled
    updated_3, replanned_3 = process_progress_update(
        learner_id="learner-struggling",
        item_id="item-p3",
        minutes_spent=40,
        self_rating=Rating.STRUGGLED,
        quiz_score=80.0,
        db_path=TEST_DB,
    )
    assert replanned_3 is False
    assert updated_3.plan.version == 2


def test_chat_repository_and_service():
    """Verify chat message persistence and chat_with_agent integration."""
    demo_id = seed_demo_learner(db_path=TEST_DB)

    # 1. Test repository directly
    save_chat_message(demo_id, "user", "What is autograd?", db_path=TEST_DB)
    save_chat_message(demo_id, "assistant", "Autograd is PyTorch's automatic differentiation engine.", db_path=TEST_DB)

    history = get_chat_history(demo_id, db_path=TEST_DB)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "What is autograd?"
    assert history[1]["role"] == "assistant"
    assert "differentiation" in history[1]["content"]

    # 2. Test chat_with_agent service
    response = chat_with_agent(
        learner_id=demo_id,
        question="Can you explain tensor operations?",
        db_path=TEST_DB,
    )
    assert isinstance(response, str)
    assert len(response) > 0

    updated_history = get_chat_history(demo_id, db_path=TEST_DB)
    assert len(updated_history) == 4
    assert updated_history[2]["role"] == "user"
    assert updated_history[2]["content"] == "Can you explain tensor operations?"
    assert updated_history[3]["role"] == "assistant"
    assert updated_history[3]["content"] == response


def test_fastapi_chat_endpoints():
    """Verify GET /chat/{id}, POST /chat/{id}, GET /api/chat/{id}, and POST /api/chat/{id}."""
    demo_id = seed_demo_learner()

    # 1. GET /chat/{demo_id}
    chat_res = client.get(f"/chat/{demo_id}")
    assert chat_res.status_code == 200
    assert "AI Coach Chat" in chat_res.text
    assert "Learner Context" in chat_res.text
    assert "Machine Learning Engineer" in chat_res.text

    # 2. GET /chat/{nonexistent} -> 404
    not_found_res = client.get("/chat/nonexistent-user-999")
    assert not_found_res.status_code == 404

    # 3. POST /chat/{demo_id}
    post_res = client.post(
        f"/chat/{demo_id}",
        data={"question": "What is the best way to study tensors this week?"},
        follow_redirects=True,
    )
    assert post_res.status_code == 200
    assert "What is the best way to study tensors this week?" in post_res.text

    # 4. GET /api/chat/{demo_id}
    api_get_res = client.get(f"/api/chat/{demo_id}")
    assert api_get_res.status_code == 200
    json_data = api_get_res.json()
    assert json_data["status"] == "success"
    assert len(json_data["history"]) > 0

    # 5. POST /api/chat/{demo_id} (JSON body)
    api_post_res = client.post(
        f"/api/chat/{demo_id}",
        json={"question": "Can you summarize week 1 goals?"},
    )
    assert api_post_res.status_code == 200
    assert api_post_res.json()["status"] == "success"
    assert "answer" in api_post_res.json()
    assert len(api_post_res.json()["answer"]) > 0


def test_fastapi_plan_completion_adaptive_redirect_and_ui():
    """Verify completing item with low quiz triggers adaptive redirect and renders replan banner."""
    demo_id = seed_demo_learner()

    # Trigger struggle via quiz score < 60% (Rule 2)
    post_res = client.post(
        f"/plan/{demo_id}/complete",
        data={
            "item_id": "demo-item-1",
            "minutes_spent": "50",
            "rating": "ok",
            "quiz_score": "45",  # Failing quiz score < 60% -> triggers Rule 2 & Replan!
            "week": "1",
        },
        follow_redirects=False,
    )
    assert post_res.status_code == 303
    assert "replanned=1" in post_res.headers["location"]

    # Fetch redirected page
    plan_page_res = client.get(post_res.headers["location"])
    assert plan_page_res.status_code == 200
    assert "Adaptive Loop Triggered" in plan_page_res.text
    assert "Plan Version 2" in plan_page_res.text
    assert "Adaptive Replan Changelog" in plan_page_res.text
    assert "Active Study Friction Identified" in plan_page_res.text
    assert "Remediate with AI Tutor" in plan_page_res.text


def test_fastapi_dashboard_struggle_alerts():
    """Verify dashboard renders struggle alerts after friction is detected."""
    demo_id = seed_demo_learner()

    # Log friction via REST API
    api_res = client.post(
        f"/api/learners/{demo_id}/activity",
        data={
            "item_id": "demo-item-1",
            "minutes_spent": "60",
            "rating": "struggled",
            "quiz_score": "50",  # Low quiz score
        },
    )
    assert api_res.status_code == 200
    assert api_res.json()["status"] == "success"
    assert api_res.json()["replanned"] is True

    # View Dashboard
    dash_res = client.get(f"/dashboard/{demo_id}")
    assert dash_res.status_code == 200
    assert "Active Struggle Flags" in dash_res.text
    assert "PyTorch" in dash_res.text
    assert "AI Remediation" in dash_res.text
