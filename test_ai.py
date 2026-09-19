import json
from ai.doc_reader import extract_text_from_file
from ai.core import analyze_profile, find_gaps
from shared.schemas.models import SkillProfile, GapList

def test_phase1():
    print("1. Extracting text from sample_resume.txt...")
    doc_text = extract_text_from_file("demo_data/sample_resume.txt")
    print(f"Extracted {len(doc_text)} characters.\n")
    
    print("2. Calling analyze_profile (This calls the Gemini LLM)...")
    form_text = "I want to become a Data Scientist."
    profile = analyze_profile(form_text, [doc_text])
    print("\n--- SKILL PROFILE OUTPUT ---")
    print(profile.model_dump_json(indent=2))
    
    print("\n3. Calling find_gaps (This calls the Gemini LLM)...")
    gaps = find_gaps(profile, "Data Scientist")
    print("\n--- GAP LIST OUTPUT ---")
    print(gaps.model_dump_json(indent=2))
    
    print("\nTest Complete!")

def test_phase2():
    print("1. Calling recommend_resources...")
    from ai.core import recommend_resources, generate_plan
    from shared.schemas.models import SkillLevel, GapList, Gap, GapStatus, Objective
    
    resources = recommend_resources("Learn fundamental Python syntax and data types", SkillLevel.BEGINNER)
    print("\n--- RESOURCES OUTPUT ---")
    for r in resources:
        print(f"- [{r.type.value}] {r.title} ({r.time_estimate_minutes} min)")
    
    print("\n2. Calling generate_plan...")
    # Mocking a small GapList for testing
    gaps = GapList(
        target_role="Data Scientist",
        gaps=[
            Gap(
                required_skill="Python", 
                status=GapStatus.MISSING, 
                priority=1, 
                objectives=[Objective(description="Learn Python basics", hours_estimated=5.0)]
            )
        ]
    )
    plan = generate_plan(gaps, hours_per_week=5.0, weeks_available=2)
    print("\n--- STUDY PLAN OUTPUT ---")
    print(plan.model_dump_json(indent=2))
    print("\nPhase 2 Test Complete!")

if __name__ == "__main__":
    # test_phase1()
    test_phase2()
