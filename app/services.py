import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict
from app.provider import (
    analyze_profile,
    find_gaps,
    generate_plan,
    replan,
    answer_question,
    write_report_narrative,
)
from app.repository import (
    save_learner,
    get_learner,
    log_activity,
    save_plan,
    save_struggle_flag,
    save_chat_message,
    get_chat_history,
    clear_learner_history,
)
from shared.schemas.models import (
    LearnerState,
    WeeklyPlan,
    PlanItem,
    ItemStatus,
    Rating,
    ActivityLog,
    GapStatus,
    GapList,
    ProgressStats,
    SkillProfile,
    Skill,
    SkillLevel,
    Gap,
    Objective,
    ItemType,
    Resource,
    ResourceType,
    StruggleFlag,
)


def onboard_learner(
    resume_text: str,
    target_role: str,
    db_path: str = "edupath.db",
) -> str:
    """Execute learner intake:

    1. Call AI analyze_profile to extract skills.
    2. Call AI find_gaps to benchmark against target role.
    3. Construct and save LearnerState to the database.
    4. Return unique learner_id.
    """
    # 1. Analyze profile from resume text
    profile = analyze_profile(form_text=resume_text, document_texts=[resume_text])

    # 2. Find skill gaps against target role
    gaps = find_gaps(profile=profile, target_role=target_role)

    # 3. Create unique learner state
    learner_id = f"learner-{uuid.uuid4().hex[:8]}"
    learner = LearnerState(
        id=learner_id,
        profile=profile,
        gaps=gaps,
        plan=None,
        activity_log=[],
        struggle_flags=[],
        hours_per_week=10.0,
        weeks_available=1,
    )

    # 4. Save to database
    save_learner(learner, db_path=db_path)

    return learner_id


def get_learner_state(
    learner_id: str,
    db_path: str = "edupath.db",
) -> Optional[LearnerState]:
    """Retrieve full LearnerState from the database."""
    return get_learner(learner_id, db_path=db_path)


def generate_learner_plan(
    learner_id: str,
    db_path: str = "edupath.db",
) -> Optional[WeeklyPlan]:
    """Generate and persist a weekly learning plan for the learner."""
    learner = get_learner(learner_id, db_path=db_path)
    if not learner or not learner.gaps:
        return None

    plan = generate_plan(
        gaps=learner.gaps,
        hours_per_week=learner.hours_per_week,
        weeks_available=learner.weeks_available,
    )

    # Ensure plan items have skill_ref and objective_ref assigned for tracking
    if learner.gaps.gaps:
        default_skill = learner.gaps.gaps[0].required_skill
        default_obj = learner.gaps.gaps[0].objectives[0].description if learner.gaps.gaps[0].objectives else "Foundational study"
        for week_num, items in plan.weeks.items():
            for item in items:
                if not item.skill_ref:
                    item.skill_ref = default_skill
                if not item.objective_ref:
                    item.objective_ref = default_obj

    learner.plan = plan
    save_plan(learner_id, plan, db_path=db_path)
    return plan


def validate_plan(
    plan: WeeklyPlan,
    hours_per_week: float,
    gaps: Optional[GapList] = None,
) -> Tuple[bool, List[str]]:
    """Validate plan constraints:

    1. No week exceeds hours_per_week by more than ~10%.
    2. Every objective in gaps appears in at least one plan item.
    3. All item IDs across the entire plan are unique.
    """
    errors: List[str] = []
    seen_ids = set()
    all_objective_refs = set()

    max_allowed_hours = hours_per_week * 1.10

    for week_num, items in plan.weeks.items():
        week_total_minutes = 0
        for item in items:
            # Check unique ID
            if item.id in seen_ids:
                errors.append(f"Duplicate item ID detected: {item.id}")
            seen_ids.add(item.id)

            if item.objective_ref:
                all_objective_refs.add(item.objective_ref)

            # Sum item minutes (from resources or default estimate)
            if item.resources:
                week_total_minutes += sum(r.time_estimate_minutes for r in item.resources)
            else:
                week_total_minutes += 60  # Default 1h if no resources specified

        week_total_hours = week_total_minutes / 60.0
        if week_total_hours > max_allowed_hours:
            errors.append(
                f"Week {week_num} total hours ({week_total_hours:.1f}h) exceeds limit "
                f"({max_allowed_hours:.1f}h = {hours_per_week}h + 10%)"
            )

    # Check objective coverage if gaps provided
    if gaps:
        for gap in gaps.gaps:
            for obj in gap.objectives:
                if obj.description not in all_objective_refs:
                    # Check substring or direct match
                    matched = any(obj.description in ref for ref in all_objective_refs)
                    if not matched:
                        errors.append(f"Objective '{obj.description}' not found in any plan item")

    return len(errors) == 0, errors


def complete_item(
    learner_id: str,
    item_id: str,
    minutes_spent: int,
    self_rating: Rating,
    quiz_score: Optional[float] = None,
    db_path: str = "edupath.db",
) -> Optional[LearnerState]:
    """Mark an item done, save ActivityLog, recompute skill statuses, and persist."""
    learner = get_learner(learner_id, db_path=db_path)
    if not learner or not learner.plan:
        return None

    item_found = False
    for week_num, items in learner.plan.weeks.items():
        for item in items:
            if item.id == item_id:
                item.status = ItemStatus.DONE
                item.minutes_spent = minutes_spent
                item.rating = self_rating
                item.quiz_score = quiz_score
                item_found = True
                break
        if item_found:
            break

    if not item_found:
        return None

    # Log activity
    act = ActivityLog(
        item_id=item_id,
        minutes_spent=minutes_spent,
        rating=self_rating,
        quiz_score=quiz_score,
        timestamp=datetime.utcnow(),
    )
    learner.activity_log.append(act)
    log_activity(learner_id, act, db_path=db_path)

    # Recompute skill status
    learner = recompute_skill_status(learner)

    # Save updated learner state
    save_learner(learner, db_path=db_path)
    return learner


def recompute_skill_status(learner: LearnerState) -> LearnerState:
    """Transition skill status:

    - missing -> partial (in_progress) once any item is done
    - partial -> has (acquired) ONLY when ALL items for the skill are done,
      no struggle flag exists for the skill, and quiz average >= 70% if quizzes exist.
    """
    if not learner.gaps or not learner.plan:
        return learner

    struggled_skills = {f.skill_name.strip().lower() for f in learner.struggle_flags}

    for gap in learner.gaps.gaps:
        skill_name_lower = gap.required_skill.strip().lower()
        objective_descs = {o.description.strip().lower() for o in gap.objectives}

        # Find all plan items associated with this skill
        related_items: List[PlanItem] = []
        for week_num, items in learner.plan.weeks.items():
            for item in items:
                matches_skill = item.skill_ref and item.skill_ref.strip().lower() == skill_name_lower
                matches_obj = item.objective_ref and item.objective_ref.strip().lower() in objective_descs
                if matches_skill or matches_obj:
                    related_items.append(item)

        if not related_items:
            continue

        done_items = [i for i in related_items if i.status == ItemStatus.DONE]
        all_done = len(done_items) == len(related_items) and len(related_items) > 0
        any_done = len(done_items) > 0

        # Check struggle flags
        has_struggle = skill_name_lower in struggled_skills

        # Check quiz scores
        quizzes = [i.quiz_score for i in done_items if i.quiz_score is not None]
        quiz_passes = True
        if quizzes:
            quiz_avg = sum(quizzes) / len(quizzes)
            quiz_passes = quiz_avg >= 70.0

        if all_done and not has_struggle and quiz_passes:
            gap.status = GapStatus.HAS
        elif any_done:
            gap.status = GapStatus.PARTIAL
        else:
            gap.status = GapStatus.MISSING

    return learner


def compute_stats(learner: LearnerState) -> ProgressStats:
    """Calculate progress statistics for basic dashboard."""
    items_done = 0
    if learner.plan and learner.plan.weeks:
        for week_items in learner.plan.weeks.values():
            for item in week_items:
                if item.status == ItemStatus.DONE:
                    items_done += 1

    total_minutes = sum(a.minutes_spent for a in learner.activity_log)
    hours_spent = round(total_minutes / 60.0, 2)

    skills_by_status = {"missing": 0, "partial": 0, "has": 0}
    if learner.gaps and learner.gaps.gaps:
        for gap in learner.gaps.gaps:
            val = gap.status.value if hasattr(gap.status, "value") else str(gap.status).lower()
            skills_by_status[val] = skills_by_status.get(val, 0) + 1

    return ProgressStats(
        items_done=items_done,
        hours_spent=hours_spent,
        skills_by_status=skills_by_status,
    )


def seed_demo_learner(db_path: str = "edupath.db") -> str:
    """Seed a rich demo learner with multi-week plan, resources, and objectives."""
    demo_id = "demo-alex-mercer"

    learner = LearnerState(
        id=demo_id,
        profile=SkillProfile(
            skills=[
                Skill(name="Python", level=SkillLevel.ADVANCED, evidence="4 years backend development"),
                Skill(name="SQL", level=SkillLevel.INTERMEDIATE, evidence="Database schema design"),
            ]
        ),
        gaps=GapList(
            target_role="Machine Learning Engineer",
            gaps=[
                Gap(
                    required_skill="PyTorch",
                    status=GapStatus.MISSING,
                    priority=1,
                    objectives=[Objective(description="Master tensors and autograd", hours_estimated=4.0)],
                ),
                Gap(
                    required_skill="Model Deployment",
                    status=GapStatus.MISSING,
                    priority=2,
                    objectives=[Objective(description="Deploy models with ONNX and FastAPI", hours_estimated=5.0)],
                ),
            ],
        ),
        plan=WeeklyPlan(
            version=1,
            goal_sentences={
                1: "Deep dive into PyTorch tensor fundamentals",
                2: "Build neural network classifiers and loss optimization",
            },
            weeks={
                1: [
                    PlanItem(
                        id="demo-item-1",
                        skill_ref="PyTorch",
                        objective_ref="Master tensors and autograd",
                        item_type=ItemType.LEARNING,
                        description="Complete PyTorch Tensors 60-Minute Blitz tutorial",
                        resources=[
                            Resource(
                                title="PyTorch Blitz: Deep Learning Essentials",
                                url="https://pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html",
                                type=ResourceType.DOCS,
                                level=SkillLevel.BEGINNER,
                                time_estimate_minutes=60,
                            )
                        ],
                        status=ItemStatus.TODO,
                        minutes_spent=0,
                    ),
                    PlanItem(
                        id="demo-item-2",
                        skill_ref="PyTorch",
                        objective_ref="Master tensors and autograd",
                        item_type=ItemType.PRACTICE,
                        description="Implement custom autograd function and verify gradients",
                        resources=[
                            Resource(
                                title="Autograd Mechanics Tutorial",
                                url="https://pytorch.org/tutorials/beginner/blitz/autograd_tutorial.html",
                                type=ResourceType.DOCS,
                                level=SkillLevel.BEGINNER,
                                time_estimate_minutes=45,
                            )
                        ],
                        status=ItemStatus.TODO,
                        minutes_spent=0,
                    ),
                ],
                2: [
                    PlanItem(
                        id="demo-item-3",
                        skill_ref="Model Deployment",
                        objective_ref="Deploy models with ONNX and FastAPI",
                        item_type=ItemType.PROJECT,
                        description="Export trained model to ONNX runtime and serve behind FastAPI",
                        resources=[
                            Resource(
                                title="ONNX Runtime Python API Guide",
                                url="https://onnxruntime.ai/docs/get-started/with-python.html",
                                type=ResourceType.DOCS,
                                level=SkillLevel.INTERMEDIATE,
                                time_estimate_minutes=90,
                            )
                        ],
                        status=ItemStatus.TODO,
                        minutes_spent=0,
                    )
                ],
            },
        ),
        activity_log=[],
        struggle_flags=[],
        hours_per_week=10.0,
        weeks_available=1,
    )

    clear_learner_history(demo_id, db_path=db_path)
    save_learner(learner, db_path=db_path)
    return demo_id


def detect_struggles(state: LearnerState) -> List[StruggleFlag]:
    """Detect study friction and learning struggles deterministically.

    Rules:
    1. Same skill rated 'struggled' 2+ times.
    2. Quiz score below 60% on any completed item.
    3. Item overdue by more than 7 days with struggle friction.
    4. Skill items skipped or retried 2+ times.
    """
    flags: List[StruggleFlag] = []

    # Map item_id to skill name
    item_to_skill: Dict[str, str] = {}
    if state.plan and state.plan.weeks:
        for week_items in state.plan.weeks.values():
            for item in week_items:
                if item.skill_ref:
                    item_to_skill[item.id] = item.skill_ref

    # 1. Same skill rated "struggled" 2+ times
    struggle_counts: Dict[str, int] = {}
    for act in state.activity_log:
        r_val = act.rating.value if hasattr(act.rating, "value") else str(act.rating).lower()
        if r_val == "struggled":
            skill = item_to_skill.get(act.item_id, "Core Skill")
            struggle_counts[skill] = struggle_counts.get(skill, 0) + 1

    for skill, count in struggle_counts.items():
        if count >= 2:
            flags.append(
                StruggleFlag(
                    skill_name=skill,
                    reason="Rated 'struggled' 2+ times across study items",
                    severity="high",
                )
            )

    # 2. Quiz score below 60%
    for act in state.activity_log:
        if act.quiz_score is not None and act.quiz_score < 60.0:
            skill = item_to_skill.get(act.item_id, "Core Skill")
            flags.append(
                StruggleFlag(
                    skill_name=skill,
                    reason=f"Low quiz score of {act.quiz_score:.1f}% on item {act.item_id} (passing threshold is 60%)",
                    severity="high",
                )
            )

    # 3. Friction older than 7 days
    now = datetime.utcnow()
    for act in state.activity_log:
        age_days = (now - act.timestamp).total_seconds() / 86400.0
        r_val = act.rating.value if hasattr(act.rating, "value") else str(act.rating).lower()
        if age_days > 7.0 and r_val == "struggled":
            skill = item_to_skill.get(act.item_id, "Core Skill")
            flags.append(
                StruggleFlag(
                    skill_name=skill,
                    reason=f"Study friction unresolved for over 7 days on item {act.item_id}",
                    severity="medium",
                )
            )

    # 4. Skipped or retried 2+ times
    item_attempts: Dict[str, int] = {}
    for act in state.activity_log:
        item_attempts[act.item_id] = item_attempts.get(act.item_id, 0) + 1

    skill_friction_counts: Dict[str, int] = {}
    for item_id, attempts in item_attempts.items():
        if attempts >= 2:
            skill = item_to_skill.get(item_id, "Core Skill")
            skill_friction_counts[skill] = skill_friction_counts.get(skill, 0) + (attempts - 1)

    if state.plan and state.plan.weeks:
        for week_items in state.plan.weeks.values():
            for item in week_items:
                s_val = item.status.value if hasattr(item.status, "value") else str(item.status).lower()
                if s_val == "skipped":
                    skill = item.skill_ref or "Core Skill"
                    skill_friction_counts[skill] = skill_friction_counts.get(skill, 0) + 1

    for skill, count in skill_friction_counts.items():
        if count >= 2:
            flags.append(
                StruggleFlag(
                    skill_name=skill,
                    reason="Items skipped or retried 2+ times without mastery",
                    severity="medium",
                )
            )

    # Deduplicate deterministically
    unique_flags: List[StruggleFlag] = []
    seen = set()
    for f in flags:
        key = (f.skill_name.strip().lower(), f.reason.strip())
        if key not in seen:
            seen.add(key)
            unique_flags.append(f)

    return unique_flags


def process_progress_update(
    learner_id: str,
    item_id: str,
    minutes_spent: int,
    self_rating: Rating,
    quiz_score: Optional[float] = None,
    db_path: str = "edupath.db",
) -> Tuple[LearnerState, bool]:
    """Execute adaptive feedback loop:

    1. Mark item done and log activity via complete_item.
    2. Detect struggles.
    3. ONLY if a NEW struggle flag appears:
       - Trigger AI replan.
       - Increment version and add plain-English change reasons.
       - Preserve all completed items.
       - Save updated plan and struggle flags.
    4. Never replan on 'easy' or 'ok' alone.
    """
    # 1. Complete item
    learner = complete_item(
        learner_id=learner_id,
        item_id=item_id,
        minutes_spent=minutes_spent,
        self_rating=self_rating,
        quiz_score=quiz_score,
        db_path=db_path,
    )
    if not learner:
        raise ValueError(f"Learner {learner_id} not found")

    # 2. Existing flags
    existing_flag_keys = {(f.skill_name.strip().lower(), f.reason.strip()) for f in learner.struggle_flags}

    # 3. Detect struggles
    detected_flags = detect_struggles(learner)
    new_flags = [f for f in detected_flags if (f.skill_name.strip().lower(), f.reason.strip()) not in existing_flag_keys]

    # 4. Adaptive loop: only replan if new struggle flag appeared
    if new_flags:
        for f in new_flags:
            save_struggle_flag(learner_id, f, db_path=db_path)
            learner.struggle_flags.append(f)

        # Call AI replan
        new_plan = replan(learner)
        current_version = learner.plan.version if learner.plan else 1
        new_plan.version = current_version + 1

        for f in new_flags:
            reason_msg = f"Adaptive replan: detected struggle ({f.reason}) in {f.skill_name}"
            if reason_msg not in new_plan.change_reasons:
                new_plan.change_reasons.append(reason_msg)

        # Preserve already completed items
        done_items = {}
        if learner.plan and learner.plan.weeks:
            for w_items in learner.plan.weeks.values():
                for itm in w_items:
                    if itm.status == ItemStatus.DONE:
                        done_items[itm.id] = itm

        if new_plan.weeks:
            for w_num, w_items in new_plan.weeks.items():
                for idx, itm in enumerate(w_items):
                    if itm.id in done_items:
                        w_items[idx] = done_items[itm.id]

        save_plan(learner_id, new_plan, db_path=db_path)
        learner.plan = new_plan
        learner = recompute_skill_status(learner)
        save_learner(learner, db_path=db_path)
        return learner, True

    return learner, False

    return learner, False


def chat_with_agent(
    learner_id: str,
    question: str,
    db_path: str = "edupath.db",
) -> str:
    """Orchestrate interactive conversational guidance with learner state context."""
    learner = get_learner(learner_id, db_path=db_path)
    if not learner:
        raise ValueError(f"Learner {learner_id} not found")

    chat_history = get_chat_history(learner_id, db_path=db_path)
    answer = answer_question(state=learner, chat_history=chat_history, question=question)

    save_chat_message(learner_id, "user", question, db_path=db_path)
    save_chat_message(learner_id, "assistant", answer, db_path=db_path)
    return answer


def generate_progress_report(
    learner_id: str,
    db_path: str = "edupath.db",
) -> dict:
    """Generate comprehensive progress report with metrics, skill status, struggle history, and AI narrative."""
    learner = get_learner(learner_id, db_path=db_path)
    if not learner:
        raise ValueError(f"Learner {learner_id} not found")

    stats = compute_stats(learner)

    total_items = 0
    completed_items = 0
    in_progress_items = 0
    todo_items = 0
    week_breakdown = {}

    if learner.plan and learner.plan.weeks:
        for w_num in sorted(learner.plan.weeks.keys()):
            items = learner.plan.weeks[w_num]
            w_done = sum(1 for itm in items if itm.status == ItemStatus.DONE)
            w_total = len(items)
            goal = (
                learner.plan.goal_sentences.get(w_num, f"Week {w_num} Focus")
                if learner.plan.goal_sentences
                else f"Week {w_num} Focus"
            )
            week_breakdown[str(w_num)] = {
                "week_number": w_num,
                "total": w_total,
                "done": w_done,
                "pct": round((w_done / w_total * 100), 1) if w_total > 0 else 0.0,
                "goal": goal,
            }
            total_items += w_total
            completed_items += w_done
            todo_items += sum(1 for itm in items if itm.status == ItemStatus.TODO)

    remaining_items = total_items - completed_items
    completion_pct = round((completed_items / total_items * 100), 1) if total_items > 0 else 0.0

    narrative = write_report_narrative(stats, learner)

    acquired_skills = []
    in_progress_skills = []
    missing_skills = []
    if learner.gaps and learner.gaps.gaps:
        for g in learner.gaps.gaps:
            status_val = g.status.value if hasattr(g.status, "value") else str(g.status).lower()
            item_info = {
                "skill": g.required_skill,
                "status": status_val,
                "priority": g.priority,
                "objectives": [obj.description for obj in g.objectives] if g.objectives else [],
            }
            if status_val == "has":
                acquired_skills.append(item_info)
            elif status_val == "partial":
                in_progress_skills.append(item_info)
            else:
                missing_skills.append(item_info)

    prior_skills = []
    if learner.profile and learner.profile.skills:
        for sk in learner.profile.skills:
            prior_skills.append({
                "name": sk.name,
                "level": sk.level.value if hasattr(sk.level, "value") else str(sk.level),
                "evidence": sk.evidence or "",
            })

    total_study_minutes = sum(a.minutes_spent for a in learner.activity_log)
    struggle_count = len(learner.struggle_flags)
    struggles_list = [
        {
            "skill": f.skill_name,
            "reason": f.reason,
            "severity": f.severity,
            "timestamp": str(getattr(f, "timestamp", "")) if getattr(f, "timestamp", None) else "",
        }
        for f in learner.struggle_flags
    ]

    replan_history = []
    if learner.plan and learner.plan.change_reasons:
        replan_history = list(learner.plan.change_reasons)

    next_recommended_item = None
    if learner.plan and learner.plan.weeks:
        for w_num in sorted(learner.plan.weeks.keys()):
            for itm in learner.plan.weeks[w_num]:
                if itm.status != ItemStatus.DONE:
                    next_recommended_item = {
                        "week": w_num,
                        "id": itm.id,
                        "description": itm.description,
                        "skill": itm.skill_ref,
                        "resource": itm.resources[0].title if itm.resources else "Recommended Module",
                        "url": itm.resources[0].url if itm.resources else "#",
                    }
                    break
            if next_recommended_item:
                break

    return {
        "learner_id": learner.id,
        "target_role": learner.gaps.target_role if learner.gaps else "Specialist",
        "generated_at": datetime.utcnow().isoformat(),
        "stats": {
            "items_done": stats.items_done,
            "total_items": total_items,
            "remaining_items": remaining_items,
            "completion_pct": completion_pct,
            "hours_spent": stats.hours_spent,
            "total_minutes": total_study_minutes,
            "skills_acquired_count": len(acquired_skills),
            "skills_in_progress_count": len(in_progress_skills),
            "skills_missing_count": len(missing_skills),
            "struggle_count": struggle_count,
            "plan_version": learner.plan.version if learner.plan else 1,
        },
        "ai_narrative": narrative,
        "skills": {
            "acquired": acquired_skills,
            "in_progress": in_progress_skills,
            "missing": missing_skills,
            "prior": prior_skills,
        },
        "weeks": week_breakdown,
        "struggles": struggles_list,
        "replan_history": replan_history,
        "next_recommended": next_recommended_item,
    }


