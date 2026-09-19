from typing import List, Dict, Any
from shared.schemas.models import (
    SkillProfile, GapList, Resource, WeeklyPlan, PlanItem, ResourceType, LearnerState, ProgressStats, SkillLevel, GapStatus, Gap, Objective, Skill
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

from pydantic import BaseModel

class ResourceListWrapper(BaseModel):
    resources: List[Resource]

def recommend_resources(objective_desc: str, level: SkillLevel) -> List[Resource]:
    """Generates a list of recommended resources for a specific learning objective."""
    prompt = f"""
    Suggest 3 high-quality learning resources to help a student achieve the following objective:
    "{objective_desc}"
    
    The student's current level for this topic is: {level.value}.
    Ensure the resources are of type VIDEO, DOCS, COURSE, ARTICLE, or PRACTICE.
    Return a list of resources.
    """
    
    # We use a local wrapper to parse the list using generate_json
    try:
        wrapper = llm.generate_json(prompt, ResourceListWrapper)
        return wrapper.resources
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to generate resources: {e}")
        return [
            Resource(
                title=f"Basics of {objective_desc}",
                url="https://google.com/search?q=" + objective_desc.replace(' ', '+'),
                type=ResourceType.ARTICLE,
                level=level,
                time_estimate_minutes=60
            )
        ]

class WeekItemWrapper(BaseModel):
    week_number: int
    goal_sentence: str
    items: List[PlanItem]

class WeeklyPlanWrapper(BaseModel):
    weeks: List[WeekItemWrapper]

def generate_plan(gaps: GapList, hours_per_week: float, weeks_available: int) -> WeeklyPlan:
    """Generates a study plan based on identified skill gaps and time constraints."""
    import uuid
    prompt = f"""
    Create a highly structured {weeks_available}-week study plan for someone transitioning to a "{gaps.target_role}" role.
    They can commit {hours_per_week} hours per week.
    
    Here are their skill gaps and objectives:
    {gaps.model_dump_json(indent=2)}
    
    Allocate the objectives across the {weeks_available} weeks.
    For each week (week_number 1 to {weeks_available}), provide a 'goal_sentence' and a list of 'items'.
    Assign a UUID for each item's id field.
    """
    
    try:
        wrapper = llm.generate_json(prompt, WeeklyPlanWrapper)
        
        # Convert wrapper to the real WeeklyPlan
        plan = WeeklyPlan(version=1, goal_sentences={}, weeks={})
        for w in wrapper.weeks:
            plan.goal_sentences[w.week_number] = w.goal_sentence
            plan.weeks[w.week_number] = w.items
            
            # Ensure UUIDs are generated if the LLM forgot
            for item in w.items:
                if not item.id or len(str(item.id)) < 5:
                    item.id = str(uuid.uuid4())
                    
        return plan
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to generate plan: {e}")
        # Fallback empty plan
        return WeeklyPlan(
            version=1,
            goal_sentences={1: "Begin working on your primary gaps."},
            weeks={1: []}
        )

def replan(state: LearnerState) -> WeeklyPlan:
    pass

def answer_question(state: LearnerState, chat_history: List[Dict[str, str]], question: str) -> str:
    pass

def write_report_narrative(stats: ProgressStats, state: LearnerState) -> str:
    pass
