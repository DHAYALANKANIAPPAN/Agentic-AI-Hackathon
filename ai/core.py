from typing import List, Dict, Any
from shared.schemas.models import (
    SkillProfile, GapList, Resource, WeeklyPlan, LearnerState, ProgressStats, SkillLevel, GapStatus, Gap, Objective, Skill
)
from ai import llm
from ai.doc_reader import extract_text_from_file

def analyze_profile(form_text: str, document_texts: List[str]) -> SkillProfile:
    """Produces a SkillProfile from the form text and document texts."""
    combined_text = f"Form Information:\n{form_text}\n\n"
    for idx, doc_text in enumerate(document_texts):
        combined_text += f"Document {idx + 1}:\n{doc_text}\n\n"
        
    prompt = f"""
    Analyze the following user profile and documents. Extract up to 25 skills that the user possesses.
    For each skill, determine its level (beginner, intermediate, advanced) and provide a short snippet of evidence from the text.
    
    User Information:
    {combined_text}
    """
    
    return llm.generate_json(prompt, SkillProfile)


def find_gaps(profile: SkillProfile, target_role: str) -> GapList:
    """Produces a GapList from a profile and a target role."""
    
    # Fallback lists in case LLM fails
    fallbacks = {
        "Data Scientist": GapList(
            target_role="Data Scientist",
            gaps=[
                Gap(required_skill="Python", status=GapStatus.MISSING, priority=1, objectives=[Objective(description="Learn Python basics", hours_estimated=10.0)]),
                Gap(required_skill="Machine Learning", status=GapStatus.MISSING, priority=2, objectives=[Objective(description="Understand ML algorithms", hours_estimated=20.0)])
            ]
        ),
        "Software Engineer": GapList(
            target_role="Software Engineer",
            gaps=[
                Gap(required_skill="Data Structures", status=GapStatus.MISSING, priority=1, objectives=[Objective(description="Learn core data structures", hours_estimated=15.0)])
            ]
        )
    }
    
    skills_context = "\n".join([f"- {s.name} ({s.level.value})" for s in profile.skills])
    
    prompt = f"""
    The user wants to become a "{target_role}".
    Here are their current skills:
    {skills_context if skills_context else "(No skills listed)"}
    
    1. Generate the key required skills for a {target_role}.
    2. Compare them against the user's current skills.
    3. Label each required skill as 'has', 'partial', or 'missing'.
    4. Assign a priority (1 is highest priority/foundational, higher numbers are lower priority/advanced).
    5. For each 'partial' or 'missing' skill, generate 2 to 4 learning objectives with hour estimates.
    
    Output this exactly matching the GapList schema.
    """
    
    try:
        gap_list = llm.generate_json(prompt, GapList)
        return gap_list
    except Exception as e:
        # Fallback
        for role_key, fallback_list in fallbacks.items():
            if role_key.lower() in target_role.lower():
                return fallback_list
                
        # Generic fallback
        return GapList(
            target_role=target_role,
            gaps=[Gap(required_skill="Core Concepts", status=GapStatus.MISSING, priority=1, objectives=[Objective(description="Learn fundamentals", hours_estimated=10.0)])]
        )

def recommend_resources(objective_desc: str, level: SkillLevel) -> List[Resource]:
    pass

def generate_plan(gaps: GapList, hours_per_week: float, weeks_available: int) -> WeeklyPlan:
    pass

def replan(state: LearnerState) -> WeeklyPlan:
    pass

def answer_question(state: LearnerState, chat_history: List[Dict[str, str]], question: str) -> str:
    pass

def write_report_narrative(stats: ProgressStats, state: LearnerState) -> str:
    pass
