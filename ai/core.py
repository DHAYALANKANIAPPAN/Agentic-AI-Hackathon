from typing import List, Dict, Any
from shared.schemas.models import (
    SkillProfile, GapList, Resource, WeeklyPlan, PlanItem, ResourceType, LearnerState, ProgressStats, SkillLevel, GapStatus, Gap, Objective, Skill
)

_cache_analyze = {}
_cache_gaps = {}
_cache_plan = {}
_cache_report = {}

from ai import llm
from ai.doc_reader import extract_text_from_file

def analyze_profile(form_text: str, document_texts: List[str]) -> SkillProfile:
    """Produces a SkillProfile from the form text and document texts."""
    combined_text = f"Form Information:\n{form_text}\n\n"
    for idx, doc_text in enumerate(document_texts):
        combined_text += f"Document {idx + 1}:\n{doc_text}\n\n"
        
    prompt = f"""
    Analyze the following user profile and documents. Extract up to 5 skills that the user possesses.
    For each skill, determine its level (beginner, intermediate, advanced) and provide a short snippet of evidence from the text.
    
    User Information:
    {combined_text}
    """
    
    return llm.generate_json(prompt, SkillProfile)


def find_gaps(profile_text: str, target_role: str) -> GapList:
    """Produces a GapList from a profile and a target role."""
    cache_key = str(profile_text)[:100] + target_role
    if cache_key in _cache_gaps: return _cache_gaps[cache_key]
    
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
    
    
    
    prompt = f"""
    The user wants to become a "{target_role}".
    Here is their resume/background text:
    {profile_text}
    
    1. Generate the key required skills for a {target_role}.
    2. Compare them against the user's background.
    3. Label each required skill as 'has', 'partial', or 'missing'.
    4. Assign a priority (1 is highest priority/foundational, higher numbers are lower priority/advanced).
    5. For each 'partial' or 'missing' skill, generate 2 to 3 structured learning objectives with hour estimates.
    
    Output this exactly matching the GapList schema.
    """
    
    try:
        gap_list = llm.generate_json(prompt, GapList)
        _cache_gaps[cache_key] = gap_list
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
    cache_key = gaps.model_dump_json() + str(hours_per_week) + str(weeks_available)
    if cache_key in _cache_plan: return _cache_plan[cache_key]
    import uuid
    prompt = f"""
    Create a highly structured {weeks_available}-week study plan for someone transitioning to a "{gaps.target_role}" role.
    They can commit {hours_per_week} hours per week.
    
    Here are their skill gaps and objectives:
    {gaps.model_dump_json(indent=2)}
    

    Allocate the objectives across the {weeks_available} weeks.
    For each week (week_number 1 to {weeks_available}), provide a 'goal_sentence' and a list of 'items'.
    CRITICAL REQUIREMENTS:
    1. LIMIT to exactly 2 items total per week to be concise. DO NOT generate week 2, week 3, or anything beyond week 1. Stop immediately after week 1.
    2. Every week MUST include at least one practice task or project (set item_type strictly to "practice" or "project").
    2. For URLs, NEVER invent links. Only provide safe search links. Example: https://www.youtube.com/results?search_query=Topic
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
                    
        _cache_plan[cache_key] = plan
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
    """Adjusts the WeeklyPlan based on the learner's struggles and progress."""
    import uuid
    prompt = f"""
    The learner has been studying for the role of "{state.gaps.target_role if state.gaps else 'Unknown'}".
    Here are the struggles they reported recently:
    {[s.model_dump_json() for s in state.struggle_flags]}
    
    Here is their current plan:
    {state.plan.model_dump_json() if state.plan else "No plan"}
    
    Generate an updated {state.weeks_available}-week plan that addresses their struggles by allocating more time or adding practice items for the concepts they found difficult.
    Provide a 'goal_sentence' for each week and a list of 'items'.
    Assign a UUID for each item's id field.
    """
    
    try:
        wrapper = llm.generate_json(prompt, WeeklyPlanWrapper)
        plan = WeeklyPlan(version=(state.plan.version + 1 if state.plan else 1), change_reasons=["Adjusted based on recent struggles"], goal_sentences={}, weeks={})
        for w in wrapper.weeks:
            plan.goal_sentences[w.week_number] = w.goal_sentence
            plan.weeks[w.week_number] = w.items
            for item in w.items:
                if not item.id or len(str(item.id)) < 5:
                    item.id = str(uuid.uuid4())
        return plan
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to replan: {e}")
        return state.plan if state.plan else WeeklyPlan()

def answer_question(state: LearnerState, chat_history: List[Dict[str, str]], question: str) -> str:
    """Answers a user's question directly, aware of their current learning state."""
    history_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in chat_history])
    
    prompt = f"""
    You are an AI learning assistant helping a student transition to "{state.gaps.target_role if state.gaps else 'Unknown'}".
    
    Recent Chat History:
    {history_text}
    
    Student's New Question:
    {question}
    
    Please provide a concise, encouraging, and accurate answer to the student's question. 
    Keep it under 3 paragraphs.
    """
    
    try:
        return llm.generate_text(prompt)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to answer question: {e}")
        return "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please try asking again later!"

def write_report_narrative(stats: ProgressStats, state: LearnerState) -> str:
    """Writes an encouraging progress report narrative."""
    cache_key = str(stats.items_done) + str(stats.hours_spent) + (state.gaps.target_role if state.gaps else '')
    if cache_key in _cache_report: return _cache_report[cache_key]
    
    skills_acq = stats.skills_by_status.get('has', 0)
    
    struggles_str = ", ".join([s.topic_id for s in state.struggle_flags]) if state.struggle_flags else "None"
    
    prompt = f"""
    Write a short, encouraging progress report for a student aiming to be a "{state.gaps.target_role if state.gaps else 'Unknown'}".
    - Hours studied: {stats.hours_spent}
    - Items completed: {stats.items_done}
    - Skills acquired: {skills_acq}
    - Struggling areas: {struggles_str}
    
    The report MUST cover:
    1. Skills acquired and skills in progress.
    2. Remaining gaps and struggling areas.
    3. End with exactly 3 to 5 concrete next steps tied to their learning plan.
    """
    
    try:
        report = llm.generate_text(prompt)
        _cache_report[cache_key] = report
        return report
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to write report: {e}")
        return f"Great job! You have completed {stats.items_done} items and studied for {stats.hours_spent} hours."
