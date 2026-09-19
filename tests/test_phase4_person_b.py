"""Unit and integration tests for Person B (Product Layer) Phase 4:

- Progress Report generation service (generate_progress_report)
- Progress metrics, competency matrix, and weekly velocity aggregation
- AI narrative generation integration via provider switch
- Activity, struggle records, and adaptive replan tracking
- FastAPI HTML report view (GET /report/{learner_id})
- FastAPI JSON REST API endpoint (GET /api/learners/{learner_id}/report)
- 404 and edge-case handling (learner with no plan)
"""

import os
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.repository import init_db, save_learner, get_learner
from app.services import (
    seed_demo_learner,
    generate_progress_report,
    process_progress_update,
    complete_item,
)
from shared.schemas.models import (
    LearnerState,
    SkillProfile,
    Skill,
    SkillLevel,
    GapList,
    Gap,
    GapStatus,
    Rating,
)

client = TestClient(app)
TEST_DB = "test_phase4.db"


@pytest.fixture(autouse=True)
def cleanup_test_db():
    """Ensure clean test database for each test run."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_generate_progress_report_service():
    """Verify progress report data structure and calculations for a newly seeded learner."""
    demo_id = seed_demo_learner(db_path=TEST_DB)
    report = generate_progress_report(demo_id, db_path=TEST_DB)

    assert report["learner_id"] == demo_id
    assert report["target_role"] == "Machine Learning Engineer"
    assert "generated_at" in report

    stats = report["stats"]
    assert stats["items_done"] == 0
    assert stats["total_items"] == 3  # 2 in week 1, 1 in week 2
    assert stats["remaining_items"] == 3
    assert stats["completion_pct"] == 0.0
    assert stats["hours_spent"] == 0.0
    assert stats["plan_version"] == 1
    assert stats["struggle_count"] == 0

    # Narrative from provider/mock
    assert isinstance(report["ai_narrative"], str)
    assert len(report["ai_narrative"]) > 0

    # Skills categories
    assert len(report["skills"]["missing"]) == 2  # PyTorch & Model Deployment
    assert len(report["skills"]["prior"]) == 2    # Python & SQL

    # Weeks breakdown
    assert "1" in report["weeks"]
    assert "2" in report["weeks"]
    assert report["weeks"]["1"]["total"] == 2
    assert report["weeks"]["1"]["done"] == 0

    # Next recommended module
    assert report["next_recommended"] is not None
    assert report["next_recommended"]["week"] == 1
    assert report["next_recommended"]["id"] == "demo-item-1"


def test_generate_progress_report_after_activity_and_struggle():
    """Verify report reflects completed items, study hours, and struggle history."""
    demo_id = seed_demo_learner(db_path=TEST_DB)

    # 1. Complete item 1 normally
    complete_item(demo_id, "demo-item-1", minutes_spent=45, self_rating=Rating.EASY, db_path=TEST_DB)

    # 2. Complete item 2 with a low quiz score to trigger struggle
    process_progress_update(
        learner_id=demo_id,
        item_id="demo-item-2",
        minutes_spent=90,
        self_rating=Rating.STRUGGLED,
        quiz_score=40.0,
        db_path=TEST_DB,
    )

    report = generate_progress_report(demo_id, db_path=TEST_DB)
    stats = report["stats"]

    assert stats["items_done"] == 2
    assert stats["remaining_items"] == 1
    assert stats["completion_pct"] == 66.7
    assert stats["hours_spent"] == 2.25  # (45 + 90) / 60
    assert stats["total_minutes"] == 135
    assert stats["struggle_count"] >= 1
    assert stats["plan_version"] >= 2  # Replan triggered by struggle

    # Verify struggle list entry
    assert len(report["struggles"]) >= 1
    assert any("PyTorch" in s["skill"] for s in report["struggles"])

    # Verify week 1 velocity reflects completed items
    assert report["weeks"]["1"]["done"] == 2
    assert report["weeks"]["1"]["pct"] == 100.0

    # Verify next recommended advanced to week 2
    assert report["next_recommended"] is not None
    assert report["next_recommended"]["week"] == 2


def test_fastapi_report_html_endpoint():
    """Verify GET /report/{learner_id} serves valid HTML with all visual report sections."""
    demo_id = seed_demo_learner(db_path="edupath.db")

    response = client.get(f"/report/{demo_id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    html = response.text
    assert "Progress &amp; Competency Report" in html or "Progress & Competency Report" in html
    assert "Executive Learning Narrative" in html
    assert "Core Performance Metrics" in html
    assert "Curriculum Velocity by Week" in html
    assert "Acquired Skills" in html
    assert "Machine Learning Engineer" in html
    assert "Print / Save PDF" in html
    assert "window.print()" in html


def test_fastapi_report_json_api_endpoint():
    """Verify GET /api/learners/{learner_id}/report returns structured JSON data."""
    demo_id = seed_demo_learner(db_path="edupath.db")

    response = client.get(f"/api/learners/{demo_id}/report")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "report" in data

    rep = data["report"]
    assert rep["learner_id"] == demo_id
    assert "stats" in rep
    assert "completion_pct" in rep["stats"]
    assert "ai_narrative" in rep
    assert "skills" in rep
    assert "weeks" in rep


def test_report_endpoints_404_for_nonexistent_learner():
    """Verify 404 response for unknown learner ID on both HTML and API endpoints."""
    bad_id = "nonexistent-learner-9999"

    html_res = client.get(f"/report/{bad_id}")
    assert html_res.status_code == 404

    api_res = client.get(f"/api/learners/{bad_id}/report")
    assert api_res.status_code == 404
    assert "not found" in api_res.json()["detail"].lower()


def test_generate_progress_report_learner_without_plan():
    """Verify report handles edge-case where learner is onboarded but plan not yet generated."""
    empty_id = "empty-plan-learner"
    empty_learner = LearnerState(
        id=empty_id,
        profile=SkillProfile(skills=[Skill(name="Python", level=SkillLevel.BEGINNER)]),
        gaps=GapList(target_role="Data Analyst", gaps=[]),
        hours_per_week=5.0,
        weeks_available=4,
    )
    save_learner(empty_learner, db_path=TEST_DB)

    report = generate_progress_report(empty_id, db_path=TEST_DB)
    assert report["stats"]["items_done"] == 0
    assert report["stats"]["total_items"] == 0
    assert report["stats"]["completion_pct"] == 0.0
    assert report["next_recommended"] is None
    assert len(report["weeks"]) == 0

    # Also check HTML view doesn't crash
    save_learner(empty_learner, db_path="edupath.db")
    res = client.get(f"/report/{empty_id}")
    assert res.status_code == 200
    assert "Data Analyst" in res.text
