"""FastAPI Application for EduPath (Member B - Phase 1).

Serves:
- GET /onboard: HTML form for resume text and target role intake.
- POST /onboard: processes intake and redirects to skill gap view.
- GET /gaps/{learner_id}: renders identified skill gaps and profile diagnostics.
- API endpoints: /api/onboard and /api/gaps/{learner_id}.
"""

from contextlib import asynccontextmanager
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
