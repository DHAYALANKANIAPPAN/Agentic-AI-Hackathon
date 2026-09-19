import uuid
from typing import List, Dict, Any
from shared.schemas.models import (
    SkillProfile, Skill, SkillLevel, GapList, Gap, GapStatus, Objective,
    Resource, ResourceType, WeeklyPlan, PlanItem, ItemType, LearnerState, ProgressStats
)

def extract_text_from_file(file_path: str) -> str:
    return "This is mock extracted text from a file. It contains Python and Data Science skills."

def analyze_profile(form_text: str, document_texts: List[str]) -> SkillProfile:
    return SkillProfile(
        skills=[
            Skill(name="Python", level=SkillLevel.INTERMEDIATE, evidence="Mock evidence"),
            Skill(name="Data Analysis", level=SkillLevel.BEGINNER, evidence="Mock evidence")
        ]
    )

def find_gaps(profile: SkillProfile, target_role: str) -> GapList:
    return GapList(
        target_role=target_role,
        gaps=[
            Gap(
                required_skill="Machine Learning",
                status=GapStatus.MISSING,
                priority=1,
                objectives=[Objective(description="Learn ML basics", hours_estimated=5.0)]
            )
        ]
    )

def recommend_resources(objective_desc: str, level: SkillLevel) -> List[Resource]:
    return [
        Resource(
            title="Mock Resource 1",
            url="http://mock.url",
            type=ResourceType.VIDEO,
            level=level,
            time_estimate_minutes=60
        )
    ]

def generate_plan(gaps: GapList, hours_per_week: float, weeks_available: int) -> WeeklyPlan:
    return WeeklyPlan(
        version=1,
        goal_sentences={1: "Mock goal week 1"},
        weeks={
            1: [
                PlanItem(
                    id=str(uuid.uuid4()),
                    item_type=ItemType.LEARNING,
                    description="Mock learning item",
                    resources=[]
                )
            ]
        }
    )

def replan(state: LearnerState) -> WeeklyPlan:
    if state.plan:
        new_plan = state.plan.model_copy(deep=True)
        new_plan.version += 1
        new_plan.change_reasons.append("Mock replan reason: user struggled")
        return new_plan
    return generate_plan(state.gaps, state.hours_per_week, state.weeks_available)

def answer_question(state: LearnerState, chat_history: List[Dict[str, str]], question: str) -> str:
    return "This is a mock answer based on your state."

def write_report_narrative(stats: ProgressStats, state: LearnerState) -> str:
    return "You are doing great! This is a mock report narrative."
