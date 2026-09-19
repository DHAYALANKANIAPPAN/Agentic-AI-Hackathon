"""FastAPI Application for EduPath (Member B - Phase 1).

Serves:
- GET /onboard: HTML form for resume text and target role intake.
- POST /onboard: processes intake and redirects to skill gap view.
- GET /gaps/{learner_id}: renders identified skill gaps and profile diagnostics.
- API endpoints: /api/onboard and /api/gaps/{learner_id}.
"""

from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.repository import init_db, get_learner
from app.services import onboard_learner


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="EduPath - AI Learning Agent",
    description="Product Layer (Member B) - Phase 1: Intake, Database, and UI",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect home to onboarding page."""
    return RedirectResponse(url="/onboard")


@app.get("/onboard", response_class=HTMLResponse)
async def onboard_form():
    """Serve the learner intake HTML form."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-slate-950 text-slate-100">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EduPath | AI Learning Intake</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        fontFamily: {
                            sans: ['Inter', 'sans-serif'],
                            heading: ['Outfit', 'sans-serif'],
                        }
                    }
                }
            }
        </script>
        <style>
            .glass-card {
                background: rgba(15, 23, 42, 0.85);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .gradient-text {
                background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
        </style>
    </head>
    <body class="min-h-full flex flex-col font-sans antialiased bg-slate-950 text-slate-100">
        <!-- Navigation -->
        <header class="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-20">
            <div class="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
                <a href="/onboard" class="flex items-center gap-2.5">
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-cyan-400 flex items-center justify-center font-heading font-extrabold text-white text-lg shadow-lg">
                        E
                    </div>
                    <span class="font-heading font-bold text-xl tracking-tight text-white">
                        EduPath <span class="text-xs uppercase font-semibold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">AI Agent</span>
                    </span>
                </a>
                <a href="/demo/seed" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/40 transition-all flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
                    <span>Load Demo Learner</span>
                </a>
            </div>
        </header>

        <!-- Main Form -->
        <main class="flex-1 max-w-3xl w-full mx-auto px-4 sm:px-6 py-10">
            <div class="text-center mb-8">
                <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20 mb-3">
                    <span class="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></span>
                    Phase 1: Profile & Skill-Gap Analysis
                </span>
                <h1 class="text-3xl sm:text-4xl font-extrabold text-white font-heading">
                    Discover Your <span class="gradient-text">Skill Gaps</span>
                </h1>
                <p class="mt-2 text-sm text-slate-400">
                    Paste your background or resume, enter your target role, and let our agent benchmark your competencies.
                </p>
            </div>

            <div class="glass-card rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-600 via-indigo-500 to-cyan-400"></div>

                <form action="/onboard" method="POST" onsubmit="showLoading()" class="space-y-6">
                    <!-- Target Role -->
                    <div>
                        <label for="target_role" class="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                            Target Career Role <span class="text-purple-400">*</span>
                        </label>
                        <input type="text" id="target_role" name="target_role" required
                            placeholder="e.g., Data Scientist, AI Engineer, or Software Engineer"
                            class="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500">
                    </div>

                    <!-- Resume / Profile Text -->
                    <div>
                        <label for="resume_text" class="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                            Resume or Background Profile <span class="text-purple-400">*</span>
                        </label>
                        <textarea id="resume_text" name="resume_text" rows="8" required
                            placeholder="Paste your resume text, work experiences, technical skills, or education here..."
                            class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono"></textarea>
                    </div>

                    <!-- Quick Sample Text Button -->
                    <div class="flex items-center justify-between text-xs text-slate-400">
                        <span>Need a quick test?</span>
                        <button type="button" onclick="loadSampleData()" class="text-cyan-400 hover:text-cyan-300 font-medium underline">
                            Insert Sample Resume
                        </button>
                    </div>

                    <!-- Submit Button -->
                    <button type="submit" id="submit-btn"
                        class="w-full py-3.5 px-6 rounded-xl font-heading font-bold text-white bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 shadow-lg shadow-purple-600/30 transition-all flex items-center justify-center gap-2">
                        <span id="btn-text">Analyze Profile & Identify Gaps</span>
                        <svg id="btn-icon" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
                        </svg>
                    </button>
                </form>
            </div>
        </main>

        <script>
            function loadSampleData() {
                document.getElementById('target_role').value = "Data Scientist";
                document.getElementById('resume_text').value = "Alex Mercer\\nSoftware Engineer with 3 years experience in Python, SQL, REST APIs, and basic data analysis using pandas and matplotlib.\\nLooking to transition into Machine Learning and Data Science.";
            }

            function showLoading() {
                const btn = document.getElementById('submit-btn');
                const btnText = document.getElementById('btn-text');
                const btnIcon = document.getElementById('btn-icon');
                btn.disabled = true;
                btn.classList.add('opacity-80', 'cursor-not-allowed');
                btnText.innerText = "Analyzing with AI Agent...";
                btnIcon.classList.add('animate-spin');
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/onboard")
async def handle_onboard_form(
    resume_text: str = Form(...),
    target_role: str = Form(...),
):
    """Process onboarding form submission and redirect to gap diagnostics."""
    learner_id = onboard_learner(resume_text=resume_text, target_role=target_role)
    return RedirectResponse(url=f"/gaps/{learner_id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/gaps/{learner_id}", response_class=HTMLResponse)
async def view_gaps(learner_id: str):
    """Retrieve and display the identified skill gaps for a learner."""
    learner = get_learner(learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail=f"Learner ID '{learner_id}' not found.")

    target_role = learner.gaps.target_role if learner.gaps else "Target Role"

    # Separate gaps into has, partial, missing
    missing_gaps = []
    partial_gaps = []
    has_gaps = []

    if learner.gaps and learner.gaps.gaps:
        for g in learner.gaps.gaps:
            status_val = g.status.value if hasattr(g.status, "value") else str(g.status).lower()
            if status_val == "missing":
                missing_gaps.append(g)
            elif status_val == "partial":
                partial_gaps.append(g)
            else:
                has_gaps.append(g)

    # Render skills from profile
    skills_html = ""
    if learner.profile and learner.profile.skills:
        for s in learner.profile.skills:
            lvl = s.level.value if hasattr(s.level, "value") else str(s.level)
            ev = f"<p class='text-[11px] text-slate-400 mt-0.5 italic'>{s.evidence}</p>" if s.evidence else ""
            skills_html += f"""
            <div class="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-xs text-white">{s.name}</span>
                    <span class="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">{lvl}</span>
                </div>
                {ev}
            </div>
            """
    else:
        skills_html = "<p class='text-xs text-slate-500 italic'>No prior skills extracted.</p>"

    def render_gap_cards(gap_list, badge_bg, badge_text, border_color):
        cards = ""
        for gap in gap_list:
            objs = ""
            for o in gap.objectives:
                objs += f"<li class='flex items-start gap-1.5'><span class='text-purple-400'>&bull;</span> <span>{o.description} (~{o.hours_estimated}h)</span></li>"
            objs_block = f"<ul class='text-xs text-slate-300 space-y-1 mt-2.5 pt-2 border-t border-slate-800'>{objs}</ul>" if objs else ""
            cards += f"""
            <div class="p-4 rounded-xl bg-slate-900/70 border {border_color} shadow-lg space-y-2">
                <div class="flex items-center justify-between">
                    <h4 class="font-bold text-sm text-white">{gap.required_skill}</h4>
                    <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded {badge_bg} {badge_text}">Priority {gap.priority}</span>
                </div>
                {objs_block}
            </div>
            """
        return cards or "<p class='text-xs text-slate-500 italic p-3'>None in this category.</p>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-slate-950 text-slate-100">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Skill Gaps | {target_role}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        fontFamily: {{
                            sans: ['Inter', 'sans-serif'],
                            heading: ['Outfit', 'sans-serif'],
                        }}
                    }}
                }}
            }}
        </script>
        <style>
            .glass-card {{
                background: rgba(15, 23, 42, 0.85);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
            .gradient-text {{
                background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
        </style>
    </head>
    <body class="min-h-full flex flex-col font-sans antialiased bg-slate-950 text-slate-100">
        <!-- Navigation -->
        <header class="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-20">
            <div class="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
                <a href="/onboard" class="flex items-center gap-2.5">
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-cyan-400 flex items-center justify-center font-heading font-extrabold text-white text-lg shadow-lg">
                        E
                    </div>
                    <span class="font-heading font-bold text-xl tracking-tight text-white">
                        EduPath <span class="text-xs uppercase font-semibold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">AI Agent</span>
                    </span>
                </a>
                <a href="/onboard" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all">
                    &larr; New Intake
                </a>
            </div>
        </header>

        <main class="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
            <!-- Header Hero -->
            <div class="glass-card rounded-2xl p-6 sm:p-8 shadow-xl border border-slate-800 relative overflow-hidden">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <div class="flex items-center gap-2 mb-1.5">
                            <span class="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase bg-purple-500/20 text-purple-300 border border-purple-500/30">
                                Diagnostic Report
                            </span>
                            <span class="text-xs text-slate-400 font-mono">Learner ID: {learner_id}</span>
                        </div>
                        <h1 class="text-2xl sm:text-3xl font-extrabold text-white font-heading">
                            Skill Gap Analysis for <span class="gradient-text">{target_role}</span>
                        </h1>
                        <p class="text-xs sm:text-sm text-slate-300 mt-1">
                            Calculated competency benchmark comparing your extracted background to the industry baseline for {target_role}.
                        </p>
                    </div>
                    <div class="flex items-center gap-3">
                        <a href="/plan/{learner_id}" class="px-5 py-2.5 rounded-xl font-heading font-bold text-sm text-white bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 shadow-lg shadow-purple-600/30 transition-all flex items-center gap-2">
                            <span>View Learning Plan</span>
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                        </a>
                    </div>
                </div>
            </div>

            <!-- Extracted Skills Section -->
            <div class="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl">
                <h3 class="font-heading font-bold text-base text-white mb-3 flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                    Extracted Profile Credentials ({len(learner.profile.skills) if learner.profile else 0})
                </h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                    {skills_html}
                </div>
            </div>

            <!-- 3-Column Skill Gaps Section -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
                <!-- Column 1: Missing Gaps -->
                <div class="space-y-4">
                    <div class="flex items-center justify-between pb-2 border-b border-rose-500/30">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50"></span>
                            <h3 class="font-heading font-bold text-base text-white">Missing Gaps</h3>
                        </div>
                        <span class="text-xs font-bold px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">{len(missing_gaps)}</span>
                    </div>
                    <div class="space-y-3">
                        {render_gap_cards(missing_gaps, "bg-rose-500/20", "text-rose-300", "border-rose-900/40")}
                    </div>
                </div>

                <!-- Column 2: Partial Gaps -->
                <div class="space-y-4">
                    <div class="flex items-center justify-between pb-2 border-b border-amber-500/30">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-amber-400 shadow-sm shadow-amber-400/50"></span>
                            <h3 class="font-heading font-bold text-base text-white">Partial Competencies</h3>
                        </div>
                        <span class="text-xs font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">{len(partial_gaps)}</span>
                    </div>
                    <div class="space-y-3">
                        {render_gap_cards(partial_gaps, "bg-amber-500/20", "text-amber-300", "border-amber-900/40")}
                    </div>
                </div>

                <!-- Column 3: Has (Mastered) -->
                <div class="space-y-4">
                    <div class="flex items-center justify-between pb-2 border-b border-emerald-500/30">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50"></span>
                            <h3 class="font-heading font-bold text-base text-white">Verified Skills</h3>
                        </div>
                        <span class="text-xs font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">{len(has_gaps)}</span>
                    </div>
                    <div class="space-y-3">
                        {render_gap_cards(has_gaps, "bg-emerald-500/20", "text-emerald-300", "border-emerald-900/40")}
                    </div>
                </div>
            </div>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/plan/{learner_id}", response_class=HTMLResponse)
async def view_weekly_plan(learner_id: str, week: int = 1):
    """Serve the weekly learning plan and study tracking interface."""
    learner = get_learner(learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail=f"Learner ID '{learner_id}' not found.")

    # Auto-generate plan if not already created
    if not learner.plan:
        from app.services import generate_learner_plan
        plan = generate_learner_plan(learner_id)
        learner = get_learner(learner_id)

    from app.services import compute_stats
    stats = compute_stats(learner)

    plan = learner.plan
    total_items = sum(len(items) for items in plan.weeks.values()) if plan and plan.weeks else 0
    percent_done = int((stats.items_done / total_items * 100)) if total_items > 0 else 0

    weeks_available = sorted(plan.weeks.keys()) if plan and plan.weeks else [1]
    if week not in weeks_available and weeks_available:
        week = weeks_available[0]

    current_week_items = plan.weeks.get(week, []) if plan and plan.weeks else []
    goal_sentence = plan.goal_sentences.get(week, "Build core technical proficiency") if plan and plan.goal_sentences else "Weekly technical goal"

    # Week tabs HTML
    tabs_html = ""
    for w in weeks_available:
        is_active = (w == week)
        active_class = "bg-purple-600 text-white font-bold shadow-lg shadow-purple-600/30" if is_active else "bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white"
        tabs_html += f"""
        <a href="/plan/{learner_id}?week={w}" class="px-4 py-2 rounded-xl text-xs uppercase font-semibold transition-all {active_class}">
            Week {w}
        </a>
        """

    # Items checklist HTML
    items_html = ""
    for item in current_week_items:
        is_done = (item.status.value if hasattr(item.status, "value") else str(item.status).lower()) == "done"
        type_str = item.item_type.value if hasattr(item.item_type, "value") else str(item.item_type).upper()

        badge_color = "bg-cyan-500/20 text-cyan-300 border-cyan-500/30"
        if type_str.lower() == "practice":
            badge_color = "bg-indigo-500/20 text-indigo-300 border-indigo-500/30"
        elif type_str.lower() == "project":
            badge_color = "bg-amber-500/20 text-amber-300 border-amber-500/30"

        # Resources
        res_html = ""
        for r in item.resources:
            r_type = r.type.value if hasattr(r.type, "value") else str(r.type).upper()
            res_html += f"""
            <a href="{r.url}" target="_blank" rel="noopener noreferrer"
               class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs text-cyan-300 hover:text-cyan-200 transition-all">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                <span>{r.title} (~{r.time_estimate_minutes}m)</span>
                <span class="text-[9px] uppercase px-1 rounded bg-slate-900 text-slate-400">{r_type}</span>
            </a>
            """

        if is_done:
            status_block = f"""
            <div class="flex items-center gap-2 text-emerald-400 text-xs font-semibold bg-emerald-950/40 px-3 py-1.5 rounded-lg border border-emerald-800/50">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                <span>Completed ({item.minutes_spent} min &bull; Rating: {item.rating.value if hasattr(item.rating, 'value') else item.rating})</span>
                {f'<span class="px-1.5 py-0.5 rounded bg-emerald-900 text-[10px]">Quiz: {item.quiz_score}%</span>' if item.quiz_score is not None else ''}
            </div>
            """
        else:
            status_block = f"""
            <form action="/plan/{learner_id}/complete" method="POST" class="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80 space-y-3 mt-3">
                <input type="hidden" name="item_id" value="{item.id}">
                <input type="hidden" name="week" value="{week}">
                <div class="flex flex-wrap items-center gap-4 text-xs">
                    <div>
                        <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Minutes Spent</label>
                        <input type="number" name="minutes_spent" value="45" min="5" max="600" required
                               class="w-24 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs">
                    </div>
                    <div>
                        <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Self Rating</label>
                        <select name="rating" class="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs">
                            <option value="easy">Easy (Understood well)</option>
                            <option value="ok" selected>OK (Comfortable)</option>
                            <option value="struggled">Struggled (Need review)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Quiz Score % (Optional)</label>
                        <input type="number" name="quiz_score" placeholder="e.g. 85" min="0" max="100"
                               class="w-28 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs">
                    </div>
                    <div class="pt-4 sm:pt-3">
                        <button type="submit"
                                class="px-4 py-1.5 rounded-lg font-bold text-xs bg-gradient-to-r from-purple-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 text-white shadow-md transition-all flex items-center gap-1.5">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                            Mark Done
                        </button>
                    </div>
                </div>
            </form>
            """

        items_html += f"""
        <div class="glass-card rounded-xl p-5 border {'border-emerald-900/40 bg-emerald-950/10' if is_done else 'border-slate-800'} space-y-3">
            <div class="flex items-start justify-between gap-3">
                <div class="space-y-1">
                    <div class="flex items-center gap-2">
                        <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded border {badge_color}">
                            {type_str}
                        </span>
                        {f'<span class="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-800 text-purple-300">{item.skill_ref}</span>' if item.skill_ref else ''}
                    </div>
                    <h4 class="font-bold text-sm text-white">{item.description}</h4>
                    {f'<p class="text-xs text-slate-400">Objective: {item.objective_ref}</p>' if item.objective_ref else ''}
                </div>
            </div>

            {f'<div class="flex flex-wrap gap-2 pt-1">{res_html}</div>' if res_html else ''}

            {status_block}
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-slate-950 text-slate-100">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weekly Learning Plan | EduPath</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        fontFamily: {{
                            sans: ['Inter', 'sans-serif'],
                            heading: ['Outfit', 'sans-serif'],
                        }}
                    }}
                }}
            }}
        </script>
        <style>
            .glass-card {{
                background: rgba(15, 23, 42, 0.85);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
            .gradient-text {{
                background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
        </style>
    </head>
    <body class="min-h-full flex flex-col font-sans antialiased bg-slate-950 text-slate-100">
        <!-- Navigation -->
        <header class="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-20">
            <div class="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
                <a href="/onboard" class="flex items-center gap-2.5">
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-cyan-400 flex items-center justify-center font-heading font-extrabold text-white text-lg shadow-lg">
                        E
                    </div>
                    <span class="font-heading font-bold text-xl tracking-tight text-white">
                        EduPath <span class="text-xs uppercase font-semibold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">AI Agent</span>
                    </span>
                </a>
                <div class="flex items-center gap-3">
                    <a href="/gaps/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Skill Gaps
                    </a>
                    <a href="/dashboard/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Dashboard
                    </a>
                    <a href="/onboard" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-purple-900/40 hover:bg-purple-900/60 text-purple-300 border border-purple-800/50 transition-all">
                        + New Intake
                    </a>
                </div>
            </div>
        </header>

        <main class="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 space-y-6">
            <!-- Progress Banner -->
            <div class="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                                Adaptive Learning Plan (v{plan.version if plan else 1})
                            </span>
                            <span class="text-xs text-slate-400 font-mono">Learner: {learner_id}</span>
                        </div>
                        <h1 class="text-2xl sm:text-3xl font-extrabold text-white font-heading">
                            Personalized Roadmap: <span class="gradient-text">{learner.gaps.target_role if learner.gaps else 'Career Path'}</span>
                        </h1>
                    </div>
                    <div class="flex items-center gap-4 bg-slate-900/80 px-4 py-3 rounded-xl border border-slate-800">
                        <div class="text-center">
                            <div class="text-xl font-bold text-white font-heading">{stats.items_done} / {total_items}</div>
                            <div class="text-[10px] uppercase font-semibold text-slate-400">Items Done</div>
                        </div>
                        <div class="w-px h-8 bg-slate-800"></div>
                        <div class="text-center">
                            <div class="text-xl font-bold text-cyan-400 font-heading">{stats.hours_spent}h</div>
                            <div class="text-[10px] uppercase font-semibold text-slate-400">Hours Logged</div>
                        </div>
                        <div class="w-px h-8 bg-slate-800"></div>
                        <div class="text-center">
                            <div class="text-xl font-bold text-purple-400 font-heading">{percent_done}%</div>
                            <div class="text-[10px] uppercase font-semibold text-slate-400">Pace</div>
                        </div>
                    </div>
                </div>

                <!-- Progress Bar -->
                <div class="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
                    <div class="bg-gradient-to-r from-purple-500 to-cyan-400 h-2.5 rounded-full transition-all duration-500" style="width: {percent_done}%"></div>
                </div>
            </div>

            <!-- Week Selection & Goal -->
            <div class="space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        {tabs_html}
                    </div>
                </div>
                <div class="p-4 rounded-xl bg-purple-950/30 border border-purple-800/40 flex items-center gap-3">
                    <span class="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></span>
                    <p class="text-xs text-purple-200 font-medium">
                        <strong class="text-purple-100">Week {week} Objective:</strong> {goal_sentence}
                    </p>
                </div>
            </div>

            <!-- Items List -->
            <div class="space-y-4">
                {items_html or "<p class='text-xs text-slate-400 italic p-6 text-center'>No items scheduled for this week.</p>"}
            </div>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/plan/{learner_id}/complete")
async def handle_complete_item(
    learner_id: str,
    item_id: str = Form(...),
    minutes_spent: int = Form(...),
    rating: str = Form(...),
    quiz_score: Optional[float] = Form(None),
    week: int = Form(1),
):
    """Process item completion from UI form and redirect to current week."""
    from app.services import complete_item
    from shared.schemas.models import Rating

    try:
        r_enum = Rating(rating.lower())
    except Exception:
        r_enum = Rating.OK

    complete_item(
        learner_id=learner_id,
        item_id=item_id,
        minutes_spent=minutes_spent,
        self_rating=r_enum,
        quiz_score=quiz_score,
    )
    return RedirectResponse(url=f"/plan/{learner_id}?week={week}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/dashboard/{learner_id}", response_class=HTMLResponse)
async def view_dashboard(learner_id: str):
    """Serve basic learner dashboard with summary statistics and activity timeline."""
    learner = get_learner(learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail=f"Learner ID '{learner_id}' not found.")

    from app.services import compute_stats
    stats = compute_stats(learner)

    # Activity timeline HTML
    activity_rows = ""
    for act in reversed(learner.activity_log):
        r_val = act.rating.value if hasattr(act.rating, "value") else str(act.rating)
        quiz_str = f"&bull; Quiz: {act.quiz_score}%" if act.quiz_score is not None else ""
        activity_rows += f"""
        <tr class="border-b border-slate-800/80 text-xs">
            <td class="py-3 px-4 font-mono text-purple-300">{act.item_id}</td>
            <td class="py-3 px-4 text-white">{act.minutes_spent} min</td>
            <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-slate-800 text-slate-300">{r_val}</span></td>
            <td class="py-3 px-4 text-slate-400">{act.timestamp.strftime('%b %d, %H:%M') if hasattr(act.timestamp, 'strftime') else str(act.timestamp)[:16]} {quiz_str}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-slate-950 text-slate-100">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard | EduPath</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="min-h-full flex flex-col font-sans antialiased bg-slate-950 text-slate-100">
        <!-- Navigation -->
        <header class="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-20">
            <div class="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
                <a href="/onboard" class="flex items-center gap-2.5">
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-cyan-400 flex items-center justify-center font-bold text-white text-lg">E</div>
                    <span class="font-bold text-xl text-white">EduPath <span class="text-xs uppercase px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300">Dashboard</span></span>
                </a>
                <div class="flex items-center gap-3">
                    <a href="/plan/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700">Weekly Plan</a>
                    <a href="/gaps/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700">Skill Gaps</a>
                </div>
            </div>
        </header>

        <main class="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 class="text-2xl sm:text-3xl font-extrabold text-white">Learner Progress Dashboard</h1>
                    <p class="text-xs text-slate-400 mt-1">Learner ID: {learner_id} &bull; Target: {learner.gaps.target_role if learner.gaps else 'Role'}</p>
                </div>
            </div>

            <!-- Stats Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
                    <div class="text-xs uppercase font-semibold text-slate-400">Items Completed</div>
                    <div class="text-3xl font-extrabold text-white mt-1">{stats.items_done}</div>
                </div>
                <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
                    <div class="text-xs uppercase font-semibold text-slate-400">Total Hours Invested</div>
                    <div class="text-3xl font-extrabold text-cyan-400 mt-1">{stats.hours_spent}h</div>
                </div>
                <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
                    <div class="text-xs uppercase font-semibold text-slate-400">Skills Acquired</div>
                    <div class="text-3xl font-extrabold text-emerald-400 mt-1">{stats.skills_by_status.get('has', 0)}</div>
                </div>
                <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
                    <div class="text-xs uppercase font-semibold text-slate-400">In Progress / Missing</div>
                    <div class="text-3xl font-extrabold text-purple-400 mt-1">{stats.skills_by_status.get('partial', 0)} / {stats.skills_by_status.get('missing', 0)}</div>
                </div>
            </div>

            <!-- Activity Log Table -->
            <div class="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
                <h3 class="font-bold text-base text-white">Recent Study Activity Logs ({len(learner.activity_log)})</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-slate-800 text-[11px] uppercase font-semibold text-slate-400">
                                <th class="py-2 px-4">Item ID</th>
                                <th class="py-2 px-4">Minutes</th>
                                <th class="py-2 px-4">Self Rating</th>
                                <th class="py-2 px-4">Timestamp & Quiz</th>
                            </tr>
                        </thead>
                        <tbody>
                            {activity_rows or '<tr><td colspan="4" class="py-4 text-center text-xs text-slate-500 italic">No study activities logged yet.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/demo/seed")
@app.post("/demo/seed")
async def seed_demo():
    """Seed demo learner state and redirect to weekly plan."""
    from app.services import seed_demo_learner
    demo_id = seed_demo_learner()
    return RedirectResponse(url=f"/plan/{demo_id}", status_code=status.HTTP_303_SEE_OTHER)


# JSON API Routes
@app.post("/api/onboard", status_code=status.HTTP_201_CREATED)
async def api_onboard(
    resume_text: str = Form(...),
    target_role: str = Form(...),
):
    """JSON API for learner intake."""
    learner_id = onboard_learner(resume_text=resume_text, target_role=target_role)
    return {"status": "success", "learner_id": learner_id}


@app.get("/api/gaps/{learner_id}")
async def api_get_gaps(learner_id: str):
    """JSON API to retrieve learner state and gap list."""
    learner = get_learner(learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    return learner


@app.post("/api/learners/{learner_id}/activity")
async def api_log_activity(
    learner_id: str,
    item_id: str = Form(...),
    minutes_spent: int = Form(...),
    rating: str = Form(...),
    quiz_score: Optional[float] = Form(None),
):
    """REST API endpoint for completing a plan item and logging activity."""
    from app.services import complete_item
    from shared.schemas.models import Rating

    try:
        r_enum = Rating(rating.lower())
    except Exception:
        r_enum = Rating.OK

    updated_state = complete_item(
        learner_id=learner_id,
        item_id=item_id,
        minutes_spent=minutes_spent,
        self_rating=r_enum,
        quiz_score=quiz_score,
    )
    if not updated_state:
        raise HTTPException(status_code=404, detail="Learner or item not found")
    return {"status": "success", "learner_id": learner_id, "item_id": item_id}

