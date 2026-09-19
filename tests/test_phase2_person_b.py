"""Unit and integration tests for Person B (Product Layer) Phase 2:

- Plan validation (hour constraints, uniqueness, objective coverage)
- Complete item and activity logging
- Skill status transitions (missing -> partial -> has)
- Struggle flag & quiz score gating on skill acquisition
- Dashboard statistics computation
- Demo learner seeding
- FastAPI weekly plan & completion UI endpoints
"""

import os
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.repository import init_db, save_learner, get_learner, save_struggle_flag
from app.services import (
    validate_plan,
    complete_item,
    recompute_skill_status,
    compute_stats,
    seed_demo_learner,
    generate_learner_plan,
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
    StruggleFlag,
    Resource,
    ResourceType,
)

client = TestClient(app)
TEST_DB = "test_phase2.db"


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


def test_validate_plan():
    """Verify plan validation: hour limit, unique item IDs, and objective coverage."""
    gaps = GapList(
        target_role="AI Engineer",
        gaps=[
            Gap(
                required_skill="PyTorch",
                status=GapStatus.MISSING,
                priority=1,
                objectives=[Objective(description="Tensor math", hours_estimated=3.0)],
            )
        ],
    )

    valid_plan = WeeklyPlan(
        version=1,
        goal_sentences={1: "Understand tensors"},
        weeks={
            1: [
                PlanItem(
                    id="valid-item-1",
                    objective_ref="Tensor math",
                    skill_ref="PyTorch",
                    item_type=ItemType.LEARNING,
                    description="Tensor basics",
                    resources=[
                        Resource(
                            title="Docs",
                            url="http://example.com",
                            type=ResourceType.DOCS,
                            level=SkillLevel.BEGINNER,
                            time_estimate_minutes=120,
                        )
                    ],
                )
            ]
        },
    )

    is_valid, errors = validate_plan(valid_plan, hours_per_week=10.0, gaps=gaps)
    assert is_valid is True
    assert len(errors) == 0

    # 1. Test duplicate item ID detection
    dup_plan = WeeklyPlan(
        version=1,
        weeks={
            1: [
                PlanItem(id="item-x", item_type=ItemType.LEARNING, description="One"),
                PlanItem(id="item-x", item_type=ItemType.PRACTICE, description="Two"),
            ]
        },
    )
    is_valid, errors = validate_plan(dup_plan, hours_per_week=10.0)
    assert is_valid is False
    assert any("Duplicate item ID" in e for e in errors)

    # 2. Test week hour overflow (> 10% of hours_per_week)
    overflow_plan = WeeklyPlan(
        version=1,
        weeks={
            1: [
                PlanItem(
                    id="item-heavy",
                    item_type=ItemType.PROJECT,
                    description="Heavy project",
                    resources=[
                        Resource(
                            title="Long project",
                            url="http://example.com",
                            type=ResourceType.PRACTICE,
                            level=SkillLevel.ADVANCED,
                            time_estimate_minutes=720,  # 12 hours (> 10h * 1.10 = 11h)
                        )
                    ],
                )
            ]
        },
    )
    is_valid, errors = validate_plan(overflow_plan, hours_per_week=10.0)
    assert is_valid is False
    assert any("exceeds limit" in e for e in errors)

    # 3. Test missing objective detection
    is_valid, errors = validate_plan(dup_plan, hours_per_week=10.0, gaps=gaps)
    assert is_valid is False
    assert any("Objective 'Tensor math' not found" in e for e in errors)


def test_complete_item_and_activity_logging():
    """Verify marking an item complete records minutes, rating, quiz score, and ActivityLog."""
    learner = LearnerState(
        id="learner-test-complete",
        profile=SkillProfile(skills=[]),
        gaps=GapList(
            target_role="Data Scientist",
            gaps=[
                Gap(
                    required_skill="Pandas",
                    status=GapStatus.MISSING,
                    priority=1,
                    objectives=[Objective(description="Data wrangling", hours_estimated=2.0)],
                )
            ],
        ),
        plan=WeeklyPlan(
            version=1,
            weeks={
                1: [
                    PlanItem(
                        id="plan-item-101",
                        skill_ref="Pandas",
                        objective_ref="Data wrangling",
                        item_type=ItemType.LEARNING,
                        description="Pandas DataFrames",
                        status=ItemStatus.TODO,
                    )
                ]
            },
        ),
        hours_per_week=10.0,
        weeks_available=4,
    )
    save_learner(learner, db_path=TEST_DB)

    updated = complete_item(
        learner_id="learner-test-complete",
        item_id="plan-item-101",
        minutes_spent=50,
        self_rating=Rating.OK,
        quiz_score=92.0,
        db_path=TEST_DB,
    )

    assert updated is not None
    item = updated.plan.weeks[1][0]
    assert item.status == ItemStatus.DONE
    assert item.minutes_spent == 50
    assert item.rating == Rating.OK
    assert item.quiz_score == 92.0

    # Verify ActivityLog persistence
    persisted = get_learner("learner-test-complete", db_path=TEST_DB)
    assert len(persisted.activity_log) == 1
    assert persisted.activity_log[0].item_id == "plan-item-101"
    assert persisted.activity_log[0].minutes_spent == 50
    assert persisted.activity_log[0].quiz_score == 92.0


def test_recompute_skill_status_transitions():
    """Verify transitions: missing -> partial -> has, and gating on struggle flags and quizzes."""
    gap = Gap(
        required_skill="PyTorch",
        status=GapStatus.MISSING,
        priority=1,
        objectives=[Objective(description="Basics", hours_estimated=2.0)],
    )

    learner = LearnerState(
        id="learner-recompute",
        gaps=GapList(target_role="AI Engineer", gaps=[gap]),
        plan=WeeklyPlan(
            version=1,
            weeks={
                1: [
                    PlanItem(
                        id="item-a",
                        skill_ref="PyTorch",
                        item_type=ItemType.LEARNING,
                        description="Intro",
                        status=ItemStatus.TODO,
                    ),
                    PlanItem(
                        id="item-b",
                        skill_ref="PyTorch",
                        item_type=ItemType.PRACTICE,
                        description="Tensors",
                        status=ItemStatus.TODO,
                    ),
                ]
            },
        ),
        hours_per_week=10.0,
        weeks_available=4,
    )

    # 1. Not started -> missing
    learner = recompute_skill_status(learner)
    assert learner.gaps.gaps[0].status == GapStatus.MISSING

    # 2. Complete 1 of 2 items -> partial (in progress)
    learner.plan.weeks[1][0].status = ItemStatus.DONE
    learner.plan.weeks[1][0].quiz_score = 80.0
    learner = recompute_skill_status(learner)
    assert learner.gaps.gaps[0].status == GapStatus.PARTIAL

    # 3. Complete all items, passing quiz -> has (acquired)
    learner.plan.weeks[1][1].status = ItemStatus.DONE
    learner.plan.weeks[1][1].quiz_score = 85.0
    learner = recompute_skill_status(learner)
    assert learner.gaps.gaps[0].status == GapStatus.HAS

    # 4. Struggle flag blocks acquisition (demotes/holds at partial)
    learner.struggle_flags.append(
        StruggleFlag(skill_name="PyTorch", reason="Confused by autograd", severity="high")
    )
    learner = recompute_skill_status(learner)
    assert learner.gaps.gaps[0].status == GapStatus.PARTIAL

    # 5. Low quiz average blocks acquisition even without struggle flag
    learner.struggle_flags = []
    learner.plan.weeks[1][1].quiz_score = 40.0  # Average = (80 + 40) / 2 = 60 < 70
    learner = recompute_skill_status(learner)
    assert learner.gaps.gaps[0].status == GapStatus.PARTIAL


def test_compute_stats_and_seed_demo():
    """Verify statistics calculation and demo learner generation."""
    demo_id = seed_demo_learner(db_path=TEST_DB)
    assert demo_id is not None

    learner = get_learner(demo_id, db_path=TEST_DB)
    assert learner is not None
    assert learner.plan is not None

    stats = compute_stats(learner)
    assert stats.items_done == 0
    assert stats.hours_spent == 0.0
    assert "missing" in stats.skills_by_status

    # Complete one demo item
    complete_item(
        learner_id=demo_id,
        item_id="demo-item-1",
        minutes_spent=60,
        self_rating=Rating.EASY,
        db_path=TEST_DB,
    )

    updated_learner = get_learner(demo_id, db_path=TEST_DB)
    updated_stats = compute_stats(updated_learner)
    assert updated_stats.items_done == 1
    assert updated_stats.hours_spent == 1.0


def test_fastapi_plan_and_complete_endpoints():
    """Verify GET /plan/{id}, POST /plan/{id}/complete, GET /dashboard/{id}, and GET /demo/seed."""
    # 1. GET /demo/seed (seeds into default DB and redirects)
    seed_res = client.get("/demo/seed", follow_redirects=False)
    assert seed_res.status_code == 303
    assert seed_res.headers["location"].startswith("/plan/demo-")
    demo_id = seed_res.headers["location"].replace("/plan/", "")

    # 2. GET /plan/{demo_id}
    res = client.get(f"/plan/{demo_id}")
    assert res.status_code == 200
    assert "Personalized Roadmap" in res.text
    assert "Week 1" in res.text

    # 3. POST /plan/{demo_id}/complete
    post_res = client.post(
        f"/plan/{demo_id}/complete",
        data={
            "item_id": "demo-item-1",
            "minutes_spent": "45",
            "rating": "ok",
            "quiz_score": "88",
            "week": "1",
        },
        follow_redirects=True,
    )
    assert post_res.status_code == 200
    assert "Completed (45 min" in post_res.text

    # 4. GET /dashboard/{demo_id}
    dash_res = client.get(f"/dashboard/{demo_id}")
    assert dash_res.status_code == 200
    assert "Learner Progress Dashboard" in dash_res.text
    assert "demo-item-1" in dash_res.text

    # 5. REST API: POST /api/learners/{id}/activity
    api_res = client.post(
        f"/api/learners/{demo_id}/activity",
        data={
            "item_id": "demo-item-2",
            "minutes_spent": "30",
            "rating": "easy",
            "quiz_score": "95",
        },
    )
    assert api_res.status_code == 200
    assert api_res.json()["status"] == "success"
