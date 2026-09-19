import pytest
from mocks import mock_ai
from shared.schemas.models import (
    SkillProfile, GapList, Resource, WeeklyPlan, LearnerState
)

def test_extract_text_mock():
    text = mock_ai.extract_text_from_file("dummy.pdf")
    assert isinstance(text, str)

def test_analyze_profile_mock():
    profile = mock_ai.analyze_profile("form text", ["doc text"])
    assert isinstance(profile, SkillProfile)

def test_find_gaps_mock():
    profile = SkillProfile()
    gaps = mock_ai.find_gaps(profile, "Data Scientist")
    assert isinstance(gaps, GapList)

def test_recommend_resources_mock():
    resources = mock_ai.recommend_resources("Learn ML", "beginner")
    assert isinstance(resources, list)
    if resources:
        assert isinstance(resources[0], Resource)

def test_generate_plan_mock():
    gaps = GapList(target_role="Data Scientist")
    plan = mock_ai.generate_plan(gaps, 10.0, 12)
    assert isinstance(plan, WeeklyPlan)

def test_replan_mock():
    state = LearnerState(id="1", hours_per_week=10.0, weeks_available=12)
    state.plan = mock_ai.generate_plan(GapList(target_role="DS"), 10.0, 12)
    new_plan = mock_ai.replan(state)
    assert isinstance(new_plan, WeeklyPlan)
    assert new_plan.version > state.plan.version

def test_answer_question_mock():
    state = LearnerState(id="1", hours_per_week=10.0, weeks_available=12)
    ans = mock_ai.answer_question(state, [], "What next?")
    assert isinstance(ans, str)

def test_write_report_narrative_mock():
    from shared.schemas.models import ProgressStats
    state = LearnerState(id="1", hours_per_week=10.0, weeks_available=12)
    stats = ProgressStats()
    report = mock_ai.write_report_narrative(stats, state)
    assert isinstance(report, str)
