from typing import List, Dict, Any
from shared.schemas.models import (
    SkillProfile, GapList, Resource, WeeklyPlan, LearnerState, ProgressStats, SkillLevel
)

def extract_text_from_file(file_path: str) -> str:
    """Turns an uploaded file into plain text."""
    pass

def analyze_profile(form_text: str, document_texts: List[str]) -> SkillProfile:
    """Produces a SkillProfile from the form text and document texts."""
    pass

def find_gaps(profile: SkillProfile, target_role: str) -> GapList:
    """Produces a GapList from a profile and a target role."""
    pass

def recommend_resources(objective_desc: str, level: SkillLevel) -> List[Resource]:
    """Gives 2-3 resources for one objective at a given level."""
    pass

def generate_plan(gaps: GapList, hours_per_week: float, weeks_available: int) -> WeeklyPlan:
    """Produces a WeeklyPlan from gaps, hours per week, and weeks available."""
    pass

def replan(state: LearnerState) -> WeeklyPlan:
    """Takes a LearnerState and returns an updated WeeklyPlan with a version number and change reasons."""
    pass

def answer_question(state: LearnerState, chat_history: List[Dict[str, str]], question: str) -> str:
    """Answers a learner's question using a LearnerState and the chat history."""
    pass

def write_report_narrative(stats: ProgressStats, state: LearnerState) -> str:
    """Writes the report text from ProgressStats and LearnerState."""
    pass
