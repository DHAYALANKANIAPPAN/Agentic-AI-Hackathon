"""FastAPI Application for EduPath (Member B - Phase 1).

Serves:
- GET /onboard: HTML form for resume text and target role intake.
- POST /onboard: processes intake and redirects to skill gap view.
- GET /gaps/{learner_id}: renders identified skill gaps and profile diagnostics.
- API endpoints: /api/onboard and /api/gaps/{learner_id}.
"""

from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import Response, FastAPI, Form, File, UploadFile, HTTPException, Request, status
import tempfile
import os
from ai.doc_reader import extract_text_from_file
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.repository import init_db, get_learner
from app.services import onboard_learner, generate_learner_plan
from app.repository import save_learner


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="EduPath - AI Learning Agent",
    description="EduPath Agentic AI Application",
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.responses import HTMLResponse
import traceback

app.mount('/static', StaticFiles(directory='static'), name='static')

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    html_content = f'''
    <html>
    <body>
        <h2>Internal Server Error</h2>
        <pre>{error_trace}</pre>
    </body>
    </html>
    '''
    return HTMLResponse(content=html_content, status_code=500)



@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the landing page."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-slate-950 text-slate-100">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EduPath | Agentic AI Learning Coach</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
        <style>
            .glass-card { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
            .gradient-text { background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        </style>
    </head>
    <body class="min-h-full flex flex-col font-sans antialiased bg-slate-950 text-slate-100">
        <!-- Navigation -->
        <header class="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-20">
            <div class="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                    <img src="/static/logo.png" class="w-10 h-10 rounded-xl object-cover shadow-lg">
                    <span class="font-heading font-bold text-xl tracking-tight text-white">EduPath</span>
                </div>
            </div>
        </header>

        <main class="flex-1 flex items-center justify-center p-6 text-center">
            <div class="max-w-2xl space-y-8">
                <h1 class="text-5xl font-extrabold font-heading text-white">
                    Your Personalized <span class="gradient-text">AI Learning Coach</span>
                </h1>
                <p class="text-lg text-slate-400">
                    EduPath is an autonomous agentic platform that analyzes your current skills, identifies the gaps to your dream career, and generates a dynamic weekly curriculum that adapts to your progress.
                </p>
                <div class="flex flex-col sm:flex-row justify-center gap-4 pt-4">
                    <a href="/login" class="px-8 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-purple-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 shadow-lg shadow-purple-600/30 transition-all text-lg">
                        Get Started
                    </a>
                    <a href="/demo/seed" class="px-8 py-3 rounded-xl font-bold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all text-lg">
                        View Live Demo
                    </a>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-12 text-left">
                    <div class="glass-card p-6 rounded-2xl">
                        <div class="text-cyan-400 mb-2">🎯 1. Gap Analysis</div>
                        <p class="text-sm text-slate-400">Upload your resume to instantly benchmark your skills against industry requirements.</p>
                    </div>
                    <div class="glass-card p-6 rounded-2xl">
                        <div class="text-purple-400 mb-2">📅 2. Dynamic Plan</div>
                        <p class="text-sm text-slate-400">Get a custom weekly roadmap that automatically adapts if you struggle with concepts.</p>
                    </div>
                    <div class="glass-card p-6 rounded-2xl">
                        <div class="text-indigo-400 mb-2">🤖 3. AI Tutor</div>
                        <p class="text-sm text-slate-400">Chat with a context-aware AI tutor who understands exactly where you are in your journey.</p>
                    </div>
                </div>
            </div>
        </main>
    
<script>
    document.addEventListener('DOMContentLoaded', () => {{
        const overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'fixed inset-0 z-[9999] hidden bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center';
        overlay.innerHTML = `
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500 mb-4"></div>
            <h2 class="text-2xl font-bold text-white mb-2">Loading...</h2>
            <p class="text-slate-400">Please wait, taking only minimum time!</p>
        `;
        document.body.appendChild(overlay);

        function showLoading() {{
            document.getElementById('globalLoadingOverlay').classList.remove('hidden');
        }}

        document.querySelectorAll('a').forEach(link => {{
            link.addEventListener('click', (e) => {{
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && link.getAttribute('target') !== '_blank') {{
                    showLoading();
                }}
            }});
        }});

        document.querySelectorAll('form').forEach(form => {{
            form.addEventListener('submit', () => {{
                showLoading();
            }});
        }});
    }});
</script>
</body>

    </html>
    """
    return HTMLResponse(content=html_content)


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
                <a href="/login" class="flex items-center gap-2.5">
                    <img src="/static/logo.png" class="w-10 h-10 rounded-xl object-cover shadow-lg">
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
                    Profile & Skill-Gap Analysis
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

                <form action="/onboard" method="POST" enctype="multipart/form-data" onsubmit="showLoading()" class="space-y-6">
                    <!-- Target Role -->
                    <div>
                        <label for="target_role" class="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                            Target Career Role <span class="text-purple-400">*</span>
                        </label>
                        <input list="role-options" id="target_role" name="target_role" required
                            placeholder="Select from list or type your own (e.g., Data Scientist)"
                            class="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500">
                        <datalist id="role-options">
                            <option value="Data Scientist">
                            <option value="Machine Learning Engineer">
                            <option value="Frontend Developer">
                            <option value="Backend Engineer">
                            <option value="Full Stack Developer">
                            <option value="DevOps Engineer">
                            <option value="Product Manager">
                            <option value="UX/UI Designer">
                            <option value="Cybersecurity Analyst">
                            <option value="Cloud Architect">
                        </datalist>
                    </div>

                    <!-- Resume / Profile Text -->
                    <div>
                        <label for="resume_text" class="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                            Resume or Background Profile <span class="text-purple-400">*</span>
                        </label>
                        <textarea id="resume_text" name="resume_text" rows="4"
                            placeholder="Paste your resume text, work experiences, technical skills, or education here..."
                            class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono"></textarea>
                    </div>

                    
                    <!-- OR File Uploads -->
                    <div class="text-center text-sm font-bold text-slate-500 my-2">OR</div>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                                1. Upload Resume (PDF, DOCX, TXT)
                            </label>
                            <input type="file" name="resume_file" accept=".pdf,.docx,.txt"
                                class="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-300 focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-purple-500/20 file:text-purple-300 hover:file:bg-purple-500/30">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                                2. Upload Certificate (Optional)
                            </label>
                            <input type="file" name="cert_file" accept=".pdf,.docx,.txt"
                                class="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-300 focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-cyan-500/20 file:text-cyan-300 hover:file:bg-cyan-500/30">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                                3. Upload Portfolio (Optional)
                            </label>
                            <input type="file" name="portfolio_file" accept=".pdf,.docx,.txt"
                                class="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-300 focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-pink-500/20 file:text-pink-300 hover:file:bg-pink-500/30">
                        </div>
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
                const overlay = document.createElement('div');
                overlay.className = 'fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center';
                overlay.innerHTML = `
                    <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500 mb-4"></div>
                    <h2 class="text-2xl font-bold gradient-text mb-2 text-white">Analyzing your Profile...</h2>
                    <p class="text-slate-400">Please wait, taking only minimum time!</p>
                `;
                document.body.appendChild(overlay);
            }
        </script>
    
<script>
    document.addEventListener('DOMContentLoaded', () => {{
        const overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'fixed inset-0 z-[9999] hidden bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center';
        overlay.innerHTML = `
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500 mb-4"></div>
            <h2 class="text-2xl font-bold text-white mb-2">Loading...</h2>
            <p class="text-slate-400">Please wait, taking only minimum time!</p>
        `;
        document.body.appendChild(overlay);

        function showLoading() {{
            document.getElementById('globalLoadingOverlay').classList.remove('hidden');
        }}

        document.querySelectorAll('a').forEach(link => {{
            link.addEventListener('click', (e) => {{
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && link.getAttribute('target') !== '_blank') {{
                    showLoading();
                }}
            }});
        }});

        document.querySelectorAll('form').forEach(form => {{
            form.addEventListener('submit', () => {{
                showLoading();
            }});
        }});
    }});
</script>
</body>

    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/onboard")
async def handle_onboard_form(
    request: Request,
    target_role: str = Form(...),
    resume_text: str = Form(""),
    resume_file: UploadFile = File(None),
    cert_file: UploadFile = File(None),
    portfolio_file: UploadFile = File(None)
):
    """Process onboarding form submission and redirect to gap diagnostics."""
    extracted_texts = []
    if resume_text.strip():
        extracted_texts.append(resume_text.strip())

    for label, f_obj in [("Resume", resume_file), ("Certificate", cert_file), ("Portfolio", portfolio_file)]:
        if f_obj and f_obj.filename:
            fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(f_obj.filename)[1])
            with open(temp_path, "wb") as f:
                f.write(await f_obj.read())
            os.close(fd)
            
            ext_text = extract_text_from_file(temp_path)
            if ext_text:
                extracted_texts.append(f"--- {label}: {f_obj.filename} ---\n" + ext_text)
                
            os.remove(temp_path)
            
    final_text = "\n\n".join(extracted_texts)
        
    if not final_text.strip():
        # Re-render with error (simplified for demo, we'll just redirect to onboard)
        return RedirectResponse(url="/onboard", status_code=status.HTTP_303_SEE_OTHER)

    username = request.cookies.get("username")
    learner_id = onboard_learner(resume_text=final_text, target_role=target_role)
    if username:
        from app.auth import add_user_role
        add_user_role(username, target_role, learner_id)
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
                <a href="/login" class="flex items-center gap-2.5">
                    <img src="/static/logo.png" class="w-10 h-10 rounded-xl object-cover shadow-lg">
                    <span class="font-heading font-bold text-xl tracking-tight text-white">
                        EduPath <span class="text-xs uppercase font-semibold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">AI Agent</span>
                    </span>
                </a>
                <div class="flex items-center gap-3">
                    <a href="/dashboard/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Dashboard
                    </a>
                    <a href="/plan/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Weekly Plan
                    </a>
                    <a href="/report/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Progress Report
                    </a>
                    <a href="/chat/{learner_id}" class="px-3.5 py-1.5 text-xs font-bold rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-md transition-all flex items-center gap-1.5">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
                        <span>AI Tutor</span>
                    </a>
                    <a href="/profile" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-purple-900/40 hover:bg-purple-900/60 text-purple-300 border border-purple-800/50 transition-all">+ Add Roles</a>
<a href="/logout" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-rose-900/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/50 transition-all">Logout</a>
                </div>
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
    
<script>
    document.addEventListener('DOMContentLoaded', () => {{
        const overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'fixed inset-0 z-[9999] hidden bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center';
        overlay.innerHTML = `
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500 mb-4"></div>
            <h2 class="text-2xl font-bold text-white mb-2">Loading...</h2>
            <p class="text-slate-400">Please wait, taking only minimum time!</p>
        `;
        document.body.appendChild(overlay);

        function showLoading() {{
            document.getElementById('globalLoadingOverlay').classList.remove('hidden');
        }}

        document.querySelectorAll('a').forEach(link => {{
            link.addEventListener('click', (e) => {{
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && link.getAttribute('target') !== '_blank') {{
                    showLoading();
                }}
            }});
        }});

        document.querySelectorAll('form').forEach(form => {{
            form.addEventListener('submit', () => {{
                showLoading();
            }});
        }});
    }});
</script>
</body>

    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/plan/{learner_id}", response_class=HTMLResponse)
async def view_weekly_plan(learner_id: str, week: int = 1, replanned: Optional[int] = None):
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

    # Adaptive replan notifications
    replan_banner_html = ""
    if replanned == 1 or (plan and plan.version > 1 and plan.change_reasons):
        reasons_li = "".join(
            f"<li class='flex items-start gap-2 text-xs text-purple-200'><span class='text-cyan-400 font-bold'>&bull;</span> <span>{r}</span></li>"
            for r in plan.change_reasons
        )
        replan_banner_html = f"""
        <div class="p-5 rounded-2xl bg-gradient-to-r from-purple-950/70 via-slate-900/90 to-cyan-950/70 border border-cyan-500/40 shadow-xl space-y-3">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div class="flex items-start gap-3">
                    <div class="w-8 h-8 rounded-xl bg-cyan-500/20 text-cyan-300 flex items-center justify-center font-bold text-base flex-shrink-0 mt-0.5">
                        ⚡
                    </div>
                    <div>
                        <h3 class="font-heading font-bold text-sm text-white flex items-center gap-2">
                            Adaptive Loop Triggered
                            <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">Plan Version {plan.version}</span>
                        </h3>
                        <p class="text-xs text-slate-300 mt-1">
                            Your roadmap has dynamically adapted based on recent study activity feedback. Completed items have been strictly preserved while future focus is adjusted.
                        </p>
                    </div>
                </div>
                <a href="/chat/{learner_id}" class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 transition-all flex items-center gap-1.5 self-start sm:self-center whitespace-nowrap">
                    <span>Ask AI Coach</span>
                    &rarr;
                </a>
            </div>
            {f'<div class="pt-2.5 border-t border-slate-800/80"><p class="text-[10px] uppercase font-bold text-slate-400 mb-1">Adaptive Replan Changelog:</p><ul class="space-y-1">{reasons_li}</ul></div>' if reasons_li else ''}
        </div>
        """

    # Active struggle flags banner
    struggle_banner_html = ""
    if learner.struggle_flags:
        badges = "".join(
            f"<span class='px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30'><strong>{f.skill_name}:</strong> {f.reason}</span>"
            for f in learner.struggle_flags
        )
        struggle_banner_html = f"""
        <div class="p-4 rounded-xl bg-rose-950/30 border border-rose-800/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
            <div class="space-y-1.5">
                <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-rose-400 animate-pulse"></span>
                    <h4 class="text-xs font-bold text-rose-200 uppercase tracking-wider">Active Study Friction Identified ({len(learner.struggle_flags)})</h4>
                </div>
                <div class="flex flex-wrap gap-2">
                    {badges}
                </div>
            </div>
            <a href="/chat/{learner_id}" class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow transition-all whitespace-nowrap flex items-center gap-1.5 self-start sm:self-center">
                <span>Remediate with AI Tutor</span>
                &rarr;
            </a>
        </div>
        """

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
            <form action="/plan/{learner_id}/complete" method="POST" enctype="multipart/form-data" class="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80 space-y-3 mt-3">
                <input type="hidden" name="item_id" value="{item.id}">
                <input type="hidden" name="week" value="{week}">
                <div class="flex flex-wrap items-center gap-4 text-xs">
                    <div>
                        <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Minutes Spent</label>
                        <input type="number" name="minutes_spent" value="45" min="5" max="600" required
                               class="w-24 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs">
                    </div>
                    <div>
                        <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Upload Evidence (Optional)</label>
                        <input type="file" name="evidence_file" class="w-48 text-[10px] text-slate-400 file:mr-2 file:py-1 file:px-2 file:rounded-lg file:border-0 file:font-semibold file:bg-purple-900/40 file:text-purple-300 hover:file:bg-purple-900/60 transition-all">
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
                <a href="/login" class="flex items-center gap-2.5">
                    <img src="/static/logo.png" class="w-10 h-10 rounded-xl object-cover shadow-lg">
                    <span class="font-heading font-bold text-xl tracking-tight text-white">
                        EduPath <span class="text-xs uppercase font-semibold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">AI Agent</span>
                    </span>
                </a>
                <div class="flex items-center gap-3">
                    <a href="/dashboard/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Dashboard
                    </a>
                    <a href="/gaps/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Skill Gaps
                    </a>
                    <a href="/report/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Progress Report
                    </a>
                    <a href="/chat/{learner_id}" class="px-3.5 py-1.5 text-xs font-bold rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-md transition-all flex items-center gap-1.5">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
                        <span>AI Tutor Chat</span>
                    </a>
                    <a href="/profile" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-purple-900/40 hover:bg-purple-900/60 text-purple-300 border border-purple-800/50 transition-all">+ Add Roles</a>
<a href="/logout" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-rose-900/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/50 transition-all">Logout</a>
                </div>
            </div>
        </header>

        <main class="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 space-y-6">
            {replan_banner_html}
            {struggle_banner_html}

            <!-- Progress Banner -->
            <div class="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                                Adaptive Learning Plan (v{plan.version if plan else 1})
                            </span>
                            
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
    
<script>
    document.addEventListener('DOMContentLoaded', () => {{
        const overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'fixed inset-0 z-[9999] hidden bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center';
        overlay.innerHTML = `
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500 mb-4"></div>
            <h2 class="text-2xl font-bold text-white mb-2">Loading...</h2>
            <p class="text-slate-400">Please wait, taking only minimum time!</p>
        `;
        document.body.appendChild(overlay);

        function showLoading() {{
            document.getElementById('globalLoadingOverlay').classList.remove('hidden');
        }}

        document.querySelectorAll('a').forEach(link => {{
            link.addEventListener('click', (e) => {{
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && link.getAttribute('target') !== '_blank') {{
                    showLoading();
                }}
            }});
        }});

        document.querySelectorAll('form').forEach(form => {{
            form.addEventListener('submit', () => {{
                showLoading();
            }});
        }});
    }});
</script>
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
    from app.services import process_progress_update
    from shared.schemas.models import Rating

    try:
        r_enum = Rating(rating.lower())
    except Exception:
        r_enum = Rating.OK

    _, is_replanned = process_progress_update(
        learner_id=learner_id,
        item_id=item_id,
        minutes_spent=minutes_spent,
        self_rating=r_enum,
        quiz_score=quiz_score,
    )
    redirect_query = f"?week={week}&replanned=1" if is_replanned else f"?week={week}"
    return RedirectResponse(url=f"/plan/{learner_id}{redirect_query}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/dashboard/{learner_id}", response_class=HTMLResponse)
async def view_dashboard(learner_id: str):
    """Serve basic learner dashboard with summary statistics, struggle flags, and activity timeline."""
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

    # Struggle Flags Table HTML
    if learner.struggle_flags:
        flag_rows = ""
        for flag in learner.struggle_flags:
            sev_badge = "bg-rose-500/20 text-rose-300 border-rose-500/30" if flag.severity.lower() == "high" else "bg-amber-500/20 text-amber-300 border-amber-500/30"
            flag_rows += f"""
            <tr class="border-b border-slate-800/80 text-xs">
                <td class="py-3 px-4 font-bold text-white">{flag.skill_name}</td>
                <td class="py-3 px-4 text-slate-300">{flag.reason}</td>
                <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-[10px] uppercase font-bold border {sev_badge}">{flag.severity}</span></td>
                <td class="py-3 px-4">
                    <a href="/chat/{learner_id}" class="inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300">
                        Ask AI Tutor &rarr;
                    </a>
                </td>
            </tr>
            """
        struggle_section_html = f"""
        <div class="p-6 rounded-2xl bg-slate-900/80 border border-rose-900/40 space-y-4 shadow-xl">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
                    <h3 class="font-bold text-base text-white">Active Struggle Flags ({len(learner.struggle_flags)})</h3>
                </div>
                <a href="/chat/{learner_id}" class="px-3 py-1 rounded-lg text-xs font-semibold bg-rose-600/30 hover:bg-rose-600/50 text-rose-200 border border-rose-500/40 transition-all flex items-center gap-1">
                    <span>AI Remediation</span> &rarr;
                </a>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-[11px] uppercase font-semibold text-slate-400">
                            <th class="py-2 px-4">Skill</th>
                            <th class="py-2 px-4">Struggle Reason</th>
                            <th class="py-2 px-4">Severity</th>
                            <th class="py-2 px-4">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {flag_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """
    else:
        struggle_section_html = f"""
        <div class="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-800/40 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs">✓</div>
                <div>
                    <h4 class="text-xs font-bold text-emerald-200 uppercase tracking-wider">No Active Friction</h4>
                    <p class="text-xs text-slate-400">Learning pace is steady with no struggle flags active.</p>
                </div>
            </div>
            <a href="/chat/{learner_id}" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700">
                Ask AI Tutor
            </a>
        </div>
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
                <a href="/login" class="flex items-center gap-2.5">
                    <img src="/static/logo.png" class="w-10 h-10 rounded-xl object-cover shadow-lg">
                    <span class="font-bold text-xl text-white">EduPath <span class="text-xs uppercase px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300">Dashboard</span></span>
                </a>
                <div class="flex items-center gap-3">
                    <a href="/plan/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700">Weekly Plan</a>
                    <a href="/gaps/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700">Skill Gaps</a>
                    <a href="/report/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-purple-900/40 hover:bg-purple-900/60 text-purple-300 border border-purple-800/50 transition-all flex items-center gap-1">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                        <span>Progress Report</span>
                    </a>
                    <a href="/chat/{learner_id}" class="px-3.5 py-1.5 text-xs font-bold rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-md transition-all flex items-center gap-1.5">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
                        <span>AI Tutor Chat</span>
                    </a>
                </div>
            </div>
        </header>

        <main class="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 class="text-2xl sm:text-3xl font-extrabold text-white">Learner Progress Dashboard</h1>
                    
                </div>
                <div class="flex items-center gap-2">
                    <a href="/report/{learner_id}" class="px-4 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 text-white shadow-lg transition-all flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                        <span>View Full Progress Report</span>
                    </a>
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

            <!-- Struggle Flags Section -->
            {struggle_section_html}

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
    
<script>
    document.addEventListener('DOMContentLoaded', () => {{
        const overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'fixed inset-0 z-[9999] hidden bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center';
        overlay.innerHTML = `
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500 mb-4"></div>
            <h2 class="text-2xl font-bold text-white mb-2">Loading...</h2>
            <p class="text-slate-400">Please wait, taking only minimum time!</p>
        `;
        document.body.appendChild(overlay);

        function showLoading() {{
            document.getElementById('globalLoadingOverlay').classList.remove('hidden');
        }}

        document.querySelectorAll('a').forEach(link => {{
            link.addEventListener('click', (e) => {{
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && link.getAttribute('target') !== '_blank') {{
                    showLoading();
                }}
            }});
        }});

        document.querySelectorAll('form').forEach(form => {{
            form.addEventListener('submit', () => {{
                showLoading();
            }});
        }});
    }});
</script>
</body>

    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/chat/{learner_id}", response_class=HTMLResponse)
async def view_chat(learner_id: str):
    """Serve interactive AI Coach Chat interface with learner context and message history."""
    learner = get_learner(learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail=f"Learner ID '{learner_id}' not found.")

    from app.repository import get_chat_history
    from app.services import compute_stats
    chat_history = get_chat_history(learner_id)
    stats = compute_stats(learner)

    target_role = learner.gaps.target_role if learner.gaps else "Target Career"
    plan_version = learner.plan.version if learner.plan else 1

    # Render struggle alerts for sidebar
    struggle_sidebar_html = ""
    if learner.struggle_flags:
        badges = ""
        for f in learner.struggle_flags:
            badges += f"""
            <div class="p-2.5 rounded-xl bg-rose-950/40 border border-rose-800/50 space-y-1">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-xs text-white">{f.skill_name}</span>
                    <span class="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-rose-900 text-rose-200">{f.severity}</span>
                </div>
                <p class="text-[11px] text-rose-200/80">{f.reason}</p>
                <button type="button" onclick="insertPrompt('Can you explain how to overcome my struggle with {f.skill_name}? {f.reason}')"
                        class="text-[11px] font-semibold text-cyan-400 hover:text-cyan-300 underline pt-1 block">
                    Ask Coach about this &rarr;
                </button>
            </div>
            """
        struggle_sidebar_html = f"""
        <div class="space-y-2 pt-2 border-t border-slate-800">
            <span class="text-[10px] uppercase font-bold text-rose-400 flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse"></span>
                Active Learning Friction
            </span>
            <div class="space-y-2">
                {badges}
            </div>
        </div>
        """

    # Render message history
    messages_html = ""
    if not chat_history:
        messages_html = f"""
        <div class="flex items-start gap-3 p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-md">
            <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-purple-600 to-cyan-400 flex items-center justify-center font-extrabold text-white text-xs flex-shrink-0">
                AI
            </div>
            <div class="space-y-1 text-xs text-slate-200">
                <p class="font-bold text-white">EduPath AI Coach</p>
                <p>
                    Hello! I have full context of your profile, your target role of <strong class="text-cyan-300">{target_role}</strong>, and your current learning roadmap (Plan v{plan_version}).
                </p>
                <p class="text-slate-400">
                    Ask me anything about your roadmap, questions on challenging concepts, or why your curriculum was adapted!
                </p>
            </div>
        </div>
        """
    else:
        for msg in chat_history:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                messages_html += f"""
                <div class="flex justify-end">
                    <div class="max-w-xl p-4 rounded-2xl rounded-tr-sm bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg space-y-1">
                        <div class="flex items-center justify-between gap-4 text-[10px] text-purple-200 font-bold uppercase">
                            <span>You</span>
                        </div>
                        <p class="text-xs whitespace-pre-wrap leading-relaxed">{content}</p>
                    </div>
                </div>
                """
            else:
                messages_html += f"""
                <div class="flex items-start gap-3">
                    <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-cyan-400 flex items-center justify-center font-extrabold text-white text-xs flex-shrink-0 mt-0.5 shadow-md">
                        AI
                    </div>
                    <div class="max-w-xl p-4 rounded-2xl rounded-tl-sm bg-slate-900/90 border border-slate-800 text-slate-100 shadow-lg space-y-1">
                        <div class="flex items-center justify-between gap-4 text-[10px] text-cyan-300 font-bold uppercase">
                            <span>EduPath AI Coach</span>
                        </div>
                        <p class="text-xs whitespace-pre-wrap leading-relaxed">{content}</p>
                    </div>
                </div>
                """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-slate-950 text-slate-100">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Coach Chat | EduPath</title>
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
                <a href="/login" class="flex items-center gap-2.5">
                    <img src="/static/logo.png" class="w-10 h-10 rounded-xl object-cover shadow-lg">
                    <span class="font-heading font-bold text-xl tracking-tight text-white">
                        EduPath <span class="text-xs uppercase font-semibold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">AI Coach</span>
                    </span>
                </a>
                <div class="flex items-center gap-3">
                    <a href="/dashboard/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Dashboard
                    </a>
                    <a href="/plan/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Weekly Plan
                    </a>
                    <a href="/report/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Progress Report
                    </a>
                    <a href="/gaps/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Skill Gaps
                    </a>
                </div>
            </div>
        </header>

        <main class="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 flex flex-col md:flex-row gap-6">
            <!-- Sidebar: Context & Quick Prompts -->
            <aside class="w-full md:w-80 space-y-4 flex-shrink-0">
                <div class="glass-card rounded-2xl p-5 border border-slate-800 space-y-3 shadow-xl">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        <h3 class="font-heading font-bold text-sm text-white">Learner Context</h3>
                    </div>
                    <div class="space-y-2 text-xs">
                        <div class="flex justify-between py-1 border-b border-slate-800/80">
                            <span class="text-slate-400">Target Role</span>
                            <span class="font-semibold text-white">{target_role}</span>
                        </div>
                        <div class="flex justify-between py-1 border-b border-slate-800/80">
                            <span class="text-slate-400">Plan Version</span>
                            <span class="font-semibold text-cyan-400">v{plan_version}</span>
                        </div>
                        <div class="flex justify-between py-1 border-b border-slate-800/80">
                            <span class="text-slate-400">Pace / Hours</span>
                            <span class="font-semibold text-purple-300">{stats.hours_spent}h logged</span>
                        </div>
                        <div class="flex justify-between py-1">
                            <span class="text-slate-400">Items Completed</span>
                            <span class="font-semibold text-emerald-400">{stats.items_done} done</span>
                        </div>
                    </div>
                    {struggle_sidebar_html}
                </div>

                <!-- Suggested Quick Prompts -->
                <div class="glass-card rounded-2xl p-5 border border-slate-800 space-y-3 shadow-xl">
                    <h4 class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Suggested Questions</h4>
                    <div class="space-y-2">
                        <button type="button" onclick="insertPrompt('Why was my learning plan adapted?')"
                                class="w-full text-left p-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 text-xs text-slate-300 hover:text-white transition-all">
                            💡 Why was my learning plan adapted?
                        </button>
                        <button type="button" onclick="insertPrompt('What should I focus on this week?')"
                                class="w-full text-left p-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 text-xs text-slate-300 hover:text-white transition-all">
                            🎯 What should I focus on this week?
                        </button>
                        <button type="button" onclick="insertPrompt('Can you quiz me on core concepts?')"
                                class="w-full text-left p-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 text-xs text-slate-300 hover:text-white transition-all">
                            📝 Can you quiz me on core concepts?
                        </button>
                        <button type="button" onclick="insertPrompt('How can I better understand autograd mechanics?')"
                                class="w-full text-left p-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 text-xs text-slate-300 hover:text-white transition-all">
                            🧠 How can I understand autograd mechanics?
                        </button>
                    </div>
                </div>
            </aside>

            <!-- Main Chat Area -->
            <section class="flex-1 flex flex-col glass-card rounded-2xl border border-slate-800 overflow-hidden shadow-2xl min-h-[550px]">
                <!-- Chat Header -->
                <div class="px-6 py-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-cyan-400 flex items-center justify-center font-bold text-white text-sm">
                            AI
                        </div>
                        <div>
                            <h2 class="font-heading font-bold text-sm text-white">EduPath Interactive Coach</h2>
                            <p class="text-[11px] text-slate-400">Contextual Tutor &bull; Powered by AI Provider</p>
                        </div>
                    </div>
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        Active
                    </span>
                </div>

                <!-- Chat Transcript Window -->
                <div id="chat-window" class="flex-1 p-6 overflow-y-auto space-y-4 max-h-[480px]">
                    {messages_html}
                </div>

                <!-- Chat Input Form -->
                <div class="p-4 border-t border-slate-800 bg-slate-900/80">
                    <form id="chat-form" action="/chat/{learner_id}" method="POST" onsubmit="handleSend()" class="flex items-center gap-3">
                        <input type="text" id="question-input" name="question" required autocomplete="off"
                               placeholder="Ask the AI Coach a question..."
                               class="flex-1 px-4 py-3 bg-slate-950 border border-slate-700 rounded-xl text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500">
                        <button type="submit" id="send-btn"
                                class="px-5 py-3 rounded-xl font-heading font-bold text-xs sm:text-sm text-white bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 shadow-lg shadow-purple-600/30 transition-all flex items-center gap-2">
                            <span id="send-text">Send</span>
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                        </button>
                    </form>
                </div>
            </section>
        </main>

        <script>
            function insertPrompt(text) {{
                const input = document.getElementById('question-input');
                input.value = text;
                input.focus();
            }}

            function handleSend() {{
                const btn = document.getElementById('send-btn');
                const text = document.getElementById('send-text');
                btn.disabled = true;
                btn.classList.add('opacity-80', 'cursor-not-allowed');
                text.innerText = "Thinking...";
            }}

            window.addEventListener('DOMContentLoaded', () => {{
                const win = document.getElementById('chat-window');
                if (win) {{
                    win.scrollTop = win.scrollHeight;
                }}
            }});
        </script>
    
<script>
    document.addEventListener('DOMContentLoaded', () => {{
        const overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'fixed inset-0 z-[9999] hidden bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center';
        overlay.innerHTML = `
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500 mb-4"></div>
            <h2 class="text-2xl font-bold text-white mb-2">Loading...</h2>
            <p class="text-slate-400">Please wait, taking only minimum time!</p>
        `;
        document.body.appendChild(overlay);

        function showLoading() {{
            document.getElementById('globalLoadingOverlay').classList.remove('hidden');
        }}

        document.querySelectorAll('a').forEach(link => {{
            link.addEventListener('click', (e) => {{
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && link.getAttribute('target') !== '_blank') {{
                    showLoading();
                }}
            }});
        }});

        document.querySelectorAll('form').forEach(form => {{
            form.addEventListener('submit', () => {{
                showLoading();
            }});
        }});
    }});
</script>
</body>

    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/chat/{learner_id}")
async def handle_chat_message(
    learner_id: str,
    question: str = Form(...),
):
    """Process chat question and redirect back to chat UI."""
    from app.services import chat_with_agent
    chat_with_agent(learner_id=learner_id, question=question)
    return RedirectResponse(url=f"/chat/{learner_id}", status_code=status.HTTP_303_SEE_OTHER)


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


@app.get("/api/chat/{learner_id}")
async def api_get_chat_history(learner_id: str):
    """JSON API for retrieving chat history."""
    from app.repository import get_chat_history
    learner = get_learner(learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    history = get_chat_history(learner_id)
    return {"status": "success", "learner_id": learner_id, "history": history}


@app.post("/api/chat/{learner_id}")
async def api_send_chat_message(learner_id: str, request: Request):
    """JSON API for sending a question and getting the AI answer."""
    from app.services import chat_with_agent
    content_type = request.headers.get("content-type", "")
    question = None
    if "application/json" in content_type:
        try:
            body = await request.json()
            question = body.get("question")
        except Exception:
            question = None
    else:
        form = await request.form()
        question = form.get("question")

    if not question or not str(question).strip():
        raise HTTPException(status_code=400, detail="Question parameter is required")

    answer = chat_with_agent(learner_id=learner_id, question=str(question))
    return {
        "status": "success",
        "learner_id": learner_id,
        "question": question,
        "answer": answer,
    }


@app.post("/api/learners/{learner_id}/activity")
async def api_log_activity(
    learner_id: str,
    item_id: str = Form(...),
    minutes_spent: int = Form(...),
    rating: str = Form(...),
    quiz_score: Optional[float] = Form(None),
):
    """REST API endpoint for completing a plan item and logging activity."""
    from app.services import process_progress_update
    from shared.schemas.models import Rating

    try:
        r_enum = Rating(rating.lower())
    except Exception:
        r_enum = Rating.OK

    updated_state, replanned = process_progress_update(
        learner_id=learner_id,
        item_id=item_id,
        minutes_spent=minutes_spent,
        self_rating=r_enum,
        quiz_score=quiz_score,
    )
    if not updated_state:
        raise HTTPException(status_code=404, detail="Learner or item not found")
    return {"status": "success", "learner_id": learner_id, "item_id": item_id, "replanned": replanned}


@app.get("/report/{learner_id}", response_class=HTMLResponse)
async def view_progress_report(learner_id: str):
    """Serve comprehensive visual progress report with metrics, skill status, and AI narrative."""
    from app.services import generate_progress_report

    try:
        report = generate_progress_report(learner_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Learner not found")

    stats = report["stats"]
    skills = report["skills"]
    weeks = report["weeks"]
    struggles = report["struggles"]
    replan_history = report["replan_history"]
    next_rec = report["next_recommended"]
    target_role = report["target_role"]
    narrative = report["ai_narrative"]
    generated_at = report["generated_at"][:16].replace("T", " ")

    # Format narrative paragraphs
    narrative_paragraphs = narrative.strip().split("\n\n")
    narrative_html = "".join(
        f"<p class='text-sm sm:text-base text-slate-200 leading-relaxed'>{p.strip()}</p>"
        for p in narrative_paragraphs
        if p.strip()
    )

    # Acquired skills HTML
    if skills["acquired"]:
        acquired_html = ""
        for s in skills["acquired"]:
            objs = "".join(
                f"<li class='flex items-center gap-1.5 text-xs text-slate-300'><span class='text-emerald-400 font-bold'>✓</span> {o}</li>"
                for o in s["objectives"]
            )
            objs_list = f"<ul class='mt-2 space-y-1 pl-1 border-t border-slate-800 pt-2'>{objs}</ul>" if objs else ""
            acquired_html += f"""
            <div class="p-4 rounded-xl bg-slate-900/80 border border-emerald-500/30 shadow-md">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-sm text-white">{s['skill']}</span>
                    <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Acquired</span>
                </div>
                {objs_list}
            </div>
            """
    else:
        acquired_html = "<div class='p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400 italic'>No skills marked as fully acquired yet. Keep completing plan items!</div>"

    # In-progress skills HTML
    if skills["in_progress"]:
        in_progress_html = ""
        for s in skills["in_progress"]:
            objs = "".join(
                f"<li class='flex items-center gap-1.5 text-xs text-slate-300'><span class='text-cyan-400 font-bold'>•</span> {o}</li>"
                for o in s["objectives"]
            )
            objs_list = f"<ul class='mt-2 space-y-1 pl-1 border-t border-slate-800 pt-2'>{objs}</ul>" if objs else ""
            in_progress_html += f"""
            <div class="p-4 rounded-xl bg-slate-900/80 border border-cyan-500/30 shadow-md">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-sm text-white">{s['skill']}</span>
                    <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">In Progress</span>
                </div>
                {objs_list}
            </div>
            """
    else:
        in_progress_html = "<div class='p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400 italic'>No skills currently in partial progress.</div>"

    # Missing gaps HTML
    if skills["missing"]:
        missing_html = ""
        for s in skills["missing"]:
            objs = "".join(
                f"<li class='flex items-center gap-1.5 text-xs text-slate-300'><span class='text-purple-400 font-bold'>○</span> {o}</li>"
                for o in s["objectives"]
            )
            objs_list = f"<ul class='mt-2 space-y-1 pl-1 border-t border-slate-800 pt-2'>{objs}</ul>" if objs else ""
            missing_html += f"""
            <div class="p-4 rounded-xl bg-slate-900/80 border border-purple-500/20 shadow-md">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-sm text-white">{s['skill']}</span>
                    <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">Target Gap (P{s['priority']})</span>
                </div>
                {objs_list}
            </div>
            """
    else:
        missing_html = "<div class='p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400 italic'>All identified target skills have been addressed!</div>"

    # Prior profile skills HTML
    if skills["prior"]:
        prior_html = ""
        for p in skills["prior"]:
            ev = f"<p class='text-[11px] text-slate-400 mt-1 italic'>{p['evidence']}</p>" if p.get("evidence") else ""
            prior_html += f"""
            <div class="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-xs text-white">{p['name']}</span>
                    <span class="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">{p['level']}</span>
                </div>
                {ev}
            </div>
            """
    else:
        prior_html = "<p class='text-xs text-slate-500 italic'>No prior skills on file.</p>"

    # Week velocity HTML
    weeks_html = ""
    if weeks:
        for w_key, w_data in weeks.items():
            pct = w_data["pct"]
            weeks_html += f"""
            <div class="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div class="space-y-1">
                    <div class="flex items-center gap-2">
                        <span class="font-bold text-sm text-white">Week {w_data['week_number']}</span>
                        <span class="text-[11px] px-2 py-0.5 rounded font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                            {w_data['done']}/{w_data['total']} items completed
                        </span>
                    </div>
                    <p class="text-xs text-slate-400">{w_data['goal']}</p>
                </div>
                <div class="flex items-center gap-3">
                    <div class="w-32 bg-slate-800 h-2.5 rounded-full overflow-hidden border border-slate-700">
                        <div class="bg-gradient-to-r from-purple-500 to-cyan-400 h-full rounded-full" style="width: {pct}%"></div>
                    </div>
                    <span class="text-xs font-bold text-cyan-300 w-12 text-right">{pct}%</span>
                </div>
            </div>
            """
    else:
        weeks_html = "<p class='text-xs text-slate-400 italic'>No weekly plan items found.</p>"

    # Struggles & Adaptive Replan Journey HTML
    struggle_items_html = ""
    if struggles:
        for st in struggles:
            struggle_items_html += f"""
            <div class="p-3.5 rounded-xl bg-rose-950/20 border border-rose-800/40 flex items-start justify-between gap-2">
                <div class="space-y-0.5">
                    <div class="flex items-center gap-2">
                        <span class="font-bold text-xs text-white">{st['skill']}</span>
                        <span class="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-rose-900/60 text-rose-200 border border-rose-700/50">{st['severity']}</span>
                    </div>
                    <p class="text-xs text-rose-200/90">{st['reason']}</p>
                </div>
                <span class="text-[10px] text-slate-400 font-mono">{st['timestamp'][:10]}</span>
            </div>
            """
    else:
        struggle_items_html = """
        <div class="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 flex items-center gap-3">
            <div class="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs">✓</div>
            <div>
                <p class="text-xs font-bold text-emerald-200">Optimal Learning Velocity</p>
                <p class="text-[11px] text-slate-400">No friction alerts logged. Course progression has been fluid.</p>
            </div>
        </div>
        """

    # Replan reasons
    replan_html = ""
    if replan_history:
        for r in replan_history:
            replan_html += f"""
            <li class="text-xs text-cyan-300/90 flex items-start gap-1.5">
                <span class="text-cyan-400 font-bold">•</span>
                <span>{r}</span>
            </li>
            """
    else:
        replan_html = "<li class='text-xs text-slate-400 italic'>Initial baseline plan active (version 1).</li>"

    # Next recommendation card HTML
    if next_rec:
        next_rec_html = f"""
        <div class="p-5 rounded-2xl bg-gradient-to-r from-purple-950/50 to-indigo-950/50 border border-purple-500/30 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div class="space-y-1">
                <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    Week {next_rec['week']} Next Target
                </span>
                <h4 class="font-bold text-sm sm:text-base text-white">{next_rec['description']}</h4>
                <p class="text-xs text-slate-300">Target Skill: <strong class="text-purple-300">{next_rec['skill']}</strong> &bull; Resource: {next_rec['resource']}</p>
            </div>
            <a href="{next_rec['url']}" target="_blank" rel="noopener noreferrer"
               class="px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-purple-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 text-white shadow transition-all whitespace-nowrap self-start sm:self-center">
                Launch Module &rarr;
            </a>
        </div>
        """
    else:
        next_rec_html = """
        <div class="p-5 rounded-2xl bg-emerald-950/30 border border-emerald-800/40 text-center space-y-1">
            <h4 class="font-bold text-sm text-emerald-200">Curriculum Completed! 🎉</h4>
            <p class="text-xs text-slate-400">All planned items have been finished. Ready for new challenges or project evaluations.</p>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-slate-950 text-slate-100">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Progress Report | EduPath AI</title>
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
            @media print {{
                header, .no-print {{ display: none !important; }}
                body {{ background: #0f172a !important; color: #f8fafc !important; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
                .glass-card {{ background: #1e293b !important; border: 1px solid #334155 !important; box-shadow: none !important; }}
            }}
        </style>
    </head>
    <body class="min-h-full flex flex-col font-sans antialiased bg-slate-950 text-slate-100">
        <!-- Navigation -->
        <header class="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-20 no-print">
            <div class="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
                <a href="/login" class="flex items-center gap-2.5">
                    <img src="/static/logo.png" class="w-10 h-10 rounded-xl object-cover shadow-lg">
                    <span class="font-heading font-bold text-xl tracking-tight text-white">
                        EduPath <span class="text-xs uppercase font-semibold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">Report</span>
                    </span>
                </a>
                <div class="flex items-center gap-3">
                    <a href="/dashboard/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Dashboard
                    </a>
                    <a href="/plan/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Weekly Plan
                    </a>
                    <a href="/chat/{learner_id}" class="px-3.5 py-1.5 text-xs font-bold rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-md transition-all flex items-center gap-1.5">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
                        <span>AI Tutor Chat</span>
                    </a>
                    <a href="/gaps/{learner_id}" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                        Skill Gaps
                    </a>
                </div>
            </div>
        </header>

        <main class="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
            <!-- Hero Header -->
            <div class="glass-card rounded-2xl p-6 sm:p-8 shadow-xl border border-slate-800 relative overflow-hidden">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                    <div>
                        <div class="flex items-center gap-2 mb-2">
                            <span class="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase bg-gradient-to-r from-purple-500/20 to-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                                Official Progress Evaluation
                            </span>
                            <span class="text-xs text-slate-400 font-mono">Plan v{stats['plan_version']}</span>
                        </div>
                        <h1 class="text-2xl sm:text-4xl font-extrabold text-white font-heading tracking-tight">
                            Progress & Competency Report
                        </h1>
                        <p class="text-xs sm:text-sm text-slate-300 mt-1">
                            Target Career Role: <span class="gradient-text font-bold">{target_role}</span> &bull; Generated: {generated_at}
                        </p>
                    </div>

                    <div class="flex items-center gap-3 no-print">
                        <button onclick="window.print()" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center gap-2 shadow">
                            <svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/></svg>
                            <span>Print / Save PDF</span>
                        </button>
                        <a href="/dashboard/{learner_id}" class="px-4 py-2 text-xs font-bold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg transition-all flex items-center gap-1.5">
                            <span>Back to Dashboard</span>
                            &rarr;
                        </a>
                    </div>
                </div>
            </div>

            <!-- Executive AI Coach Narrative -->
            <div class="glass-card rounded-2xl p-6 sm:p-8 border border-purple-500/30 shadow-2xl relative overflow-hidden">
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-cyan-400 flex items-center justify-center font-extrabold text-white text-sm shadow-lg">
                        AI
                    </div>
                    <div>
                        <h2 class="text-base sm:text-lg font-bold text-white font-heading">
                            Executive Learning Narrative
                        </h2>
                        <span class="text-[11px] text-purple-300/80 font-medium">Generated by EduPath AI Agent</span>
                    </div>
                </div>
                <div class="space-y-3 bg-slate-900/60 p-5 rounded-xl border border-slate-800/80">
                    {narrative_html}
                </div>
            </div>

            <!-- Next Immediate Priority -->
            <div>
                <h3 class="text-xs uppercase font-bold text-slate-400 tracking-wider mb-3">Recommended Next Step</h3>
                {next_rec_html}
            </div>

            <!-- High Level KPI Grid -->
            <div>
                <h3 class="text-xs uppercase font-bold text-slate-400 tracking-wider mb-3">Core Performance Metrics</h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
                        <div class="flex items-center justify-between">
                            <span class="text-xs uppercase font-semibold text-slate-400">Curriculum Completion</span>
                            <span class="text-xs font-bold text-cyan-400">{stats['completion_pct']}%</span>
                        </div>
                        <div class="text-2xl sm:text-3xl font-extrabold text-white mt-2 font-heading">
                            {stats['items_done']} <span class="text-sm font-normal text-slate-500">/ {stats['total_items']} items</span>
                        </div>
                        <div class="w-full bg-slate-800 h-2 rounded-full mt-3 overflow-hidden border border-slate-700">
                            <div class="bg-gradient-to-r from-purple-500 to-cyan-400 h-full rounded-full" style="width: {stats['completion_pct']}%"></div>
                        </div>
                    </div>

                    <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
                        <span class="text-xs uppercase font-semibold text-slate-400">Time Invested</span>
                        <div class="text-2xl sm:text-3xl font-extrabold text-cyan-400 mt-2 font-heading">
                            {stats['hours_spent']}h
                        </div>
                        <p class="text-xs text-slate-400 mt-3">{stats['total_minutes']} study minutes logged</p>
                    </div>

                    <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
                        <span class="text-xs uppercase font-semibold text-slate-400">Mastered Competencies</span>
                        <div class="text-2xl sm:text-3xl font-extrabold text-emerald-400 mt-2 font-heading">
                            {stats['skills_acquired_count']} <span class="text-sm font-normal text-slate-500">skills</span>
                        </div>
                        <p class="text-xs text-slate-400 mt-3">{stats['skills_in_progress_count']} skills in active practice</p>
                    </div>

                    <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
                        <span class="text-xs uppercase font-semibold text-slate-400">Adaptive Iterations</span>
                        <div class="text-2xl sm:text-3xl font-extrabold text-purple-400 mt-2 font-heading">
                            v{stats['plan_version']}
                        </div>
                        <p class="text-xs text-slate-400 mt-3">{stats['struggle_count']} struggle alerts handled</p>
                    </div>
                </div>
            </div>

            <!-- Competency Breakdown -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Acquired Skills -->
                <div class="glass-card rounded-2xl p-5 border border-slate-800 space-y-4">
                    <div class="flex items-center justify-between">
                        <h3 class="text-sm font-bold text-white font-heading flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                            Acquired Skills ({len(skills['acquired'])})
                        </h3>
                    </div>
                    <div class="space-y-3">
                        {acquired_html}
                    </div>
                </div>

                <!-- In Progress Skills -->
                <div class="glass-card rounded-2xl p-5 border border-slate-800 space-y-4">
                    <div class="flex items-center justify-between">
                        <h3 class="text-sm font-bold text-white font-heading flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                            In Progress ({len(skills['in_progress'])})
                        </h3>
                    </div>
                    <div class="space-y-3">
                        {in_progress_html}
                    </div>
                </div>

                <!-- Pending Target Gaps -->
                <div class="glass-card rounded-2xl p-5 border border-slate-800 space-y-4">
                    <div class="flex items-center justify-between">
                        <h3 class="text-sm font-bold text-white font-heading flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-purple-400"></span>
                            Upcoming Gaps ({len(skills['missing'])})
                        </h3>
                    </div>
                    <div class="space-y-3">
                        {missing_html}
                    </div>
                </div>
            </div>

            <!-- Baseline Skills From Resume -->
            <div class="glass-card rounded-2xl p-5 border border-slate-800 space-y-3">
                <h3 class="text-xs uppercase font-bold text-slate-400 tracking-wider">Baseline Background Skills (From Resume)</h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                    {prior_html}
                </div>
            </div>

            <!-- Weekly Progress Breakdown -->
            <div class="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
                <div class="flex items-center justify-between">
                    <h3 class="text-base font-bold text-white font-heading">
                        Curriculum Velocity by Week
                    </h3>
                    <span class="text-xs text-slate-400">{len(weeks)} Weeks Total</span>
                </div>
                <div class="space-y-3">
                    {weeks_html}
                </div>
            </div>

            <!-- Adaptive Journey & Struggle Resolution -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Struggle Logs -->
                <div class="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
                    <h3 class="text-sm font-bold text-white font-heading flex items-center gap-2">
                        <svg class="w-4 h-4 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                        Friction & Struggle Records ({len(struggles)})
                    </h3>
                    <div class="space-y-2.5">
                        {struggle_items_html}
                    </div>
                </div>

                <!-- Replan Events -->
                <div class="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
                    <h3 class="text-sm font-bold text-white font-heading flex items-center gap-2">
                        <svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                        Agentic Adaptation History
                    </h3>
                    <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                        <ul class="space-y-2">
                            {replan_html}
                        </ul>
                    </div>
                </div>
            </div>
        </main>

        <!-- Footer -->
        <footer class="mt-auto border-t border-slate-900 py-6 text-center text-xs text-slate-500 no-print">
            <p>EduPath Agentic AI Hackathon &bull; Progress Report &bull; Powered by FastAPI & Agentic AI</p>
        </footer>
    
<script>
    document.addEventListener('DOMContentLoaded', () => {{
        const overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'fixed inset-0 z-[9999] hidden bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center';
        overlay.innerHTML = `
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500 mb-4"></div>
            <h2 class="text-2xl font-bold text-white mb-2">Loading...</h2>
            <p class="text-slate-400">Please wait, taking only minimum time!</p>
        `;
        document.body.appendChild(overlay);

        function showLoading() {{
            document.getElementById('globalLoadingOverlay').classList.remove('hidden');
        }}

        document.querySelectorAll('a').forEach(link => {{
            link.addEventListener('click', (e) => {{
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && link.getAttribute('target') !== '_blank') {{
                    showLoading();
                }}
            }});
        }});

        document.querySelectorAll('form').forEach(form => {{
            form.addEventListener('submit', () => {{
                showLoading();
            }});
        }});
    }});
</script>
</body>

    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/learners/{learner_id}/report")
async def api_get_learner_report(learner_id: str):
    """JSON API endpoint returning the full progress report data for external consumers."""
    from app.services import generate_progress_report

    try:
        report_data = generate_progress_report(learner_id)
        return {"status": "success", "report": report_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@app.post("/dashboard/upload/{learner_id}")
async def upload_certificate_replan(learner_id: str, cert_file: UploadFile = File(...)):
    """Handles new certificate uploads to dynamically replan the curriculum."""
    learner = get_learner(learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
        
    if cert_file and cert_file.filename:
        fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(cert_file.filename)[1])
        with open(temp_path, "wb") as f:
            f.write(await cert_file.read())
        os.close(fd)
        
        ext_text = extract_text_from_file(temp_path)
        os.remove(temp_path)
        
        if ext_text:
            # Tell the AI to analyze this new certificate and adjust the gaps!
            from ai.core import find_gaps, _cache_gaps
            
            combined_context = f"Learner's previous profile summary: They had gaps in {learner.gaps.target_role}.\nNEW CERTIFICATE EARNED:\n{ext_text}\n\nPlease remove any gaps they have now mastered."
            _cache_gaps.clear()
            
            new_gaps = find_gaps(profile_text=combined_context, target_role=learner.gaps.target_role)
            learner.gaps = new_gaps
            save_learner(learner)
            
            # Now replan the curriculum based on the reduced gaps
            generate_learner_plan(learner_id)
            
    return RedirectResponse(url=f"/dashboard/{learner_id}", status_code=status.HTTP_303_SEE_OTHER)

from fastapi.responses import HTMLResponse, RedirectResponse

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    html_content = '''
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-slate-950 text-slate-100">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login | EduPath</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
        <style>
            .glass-card { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
            .gradient-text { background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        </style>
    </head>
    <body class="min-h-full flex items-center justify-center font-sans antialiased bg-slate-950 p-4">
        <div class="glass-card rounded-2xl border border-slate-800 p-8 w-full max-w-md shadow-2xl relative overflow-hidden">
            <div class="absolute -top-32 -right-32 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl"></div>
            
            <div class="text-center mb-8 relative z-10">
                <img src="/static/logo.png" class="w-12 h-12 rounded-xl object-cover shadow-lg mx-auto mb-4">
                <h1 class="text-2xl font-bold text-white font-heading">Welcome to EduPath</h1>
                <p class="text-slate-400 mt-2 text-sm">Sign in or create an account to continue your learning journey.</p>
            </div>
            
            <form action="/api/auth" method="POST" class="space-y-5 relative z-10">
                <div>
                    <label class="block text-sm font-medium text-slate-300 mb-1">Username</label>
                    <input type="text" name="username" required class="w-full bg-slate-900/80 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-colors">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-300 mb-1">Password</label>
                    <input type="password" name="password" required class="w-full bg-slate-900/80 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-colors">
                </div>
                
                <div class="flex flex-col gap-3 pt-2">
                    <button type="submit" name="action" value="login" class="w-full py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold rounded-lg shadow-lg hover:shadow-indigo-500/25 transition-all">
                        Login
                    </button>
                    <button type="submit" name="action" value="signup" class="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-lg border border-slate-700 transition-colors">
                        Create Account
                    </button>
                </div>
            </form>
        </div>
    
<script>
    document.addEventListener('DOMContentLoaded', () => {{
        const overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'fixed inset-0 z-[9999] hidden bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center';
        overlay.innerHTML = `
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500 mb-4"></div>
            <h2 class="text-2xl font-bold text-white mb-2">Loading...</h2>
            <p class="text-slate-400">Please wait, taking only minimum time!</p>
        `;
        document.body.appendChild(overlay);

        function showLoading() {{
            document.getElementById('globalLoadingOverlay').classList.remove('hidden');
        }}

        document.querySelectorAll('a').forEach(link => {{
            link.addEventListener('click', (e) => {{
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && link.getAttribute('target') !== '_blank') {{
                    showLoading();
                }}
            }});
        }});

        document.querySelectorAll('form').forEach(form => {{
            form.addEventListener('submit', () => {{
                showLoading();
            }});
        }});
    }});
</script>
</body>

    </html>
    '''
    return HTMLResponse(content=html_content)

@app.post("/api/auth")
async def handle_auth(
    action: str = Form(...),
    username: str = Form(...),
    password: str = Form(...)
):
    from app.auth import authenticate_user, register_user
    if action == "signup":
        success = register_user(username, password)
        if not success:
            return HTMLResponse("Username already exists. <a href='/login'>Go back</a>", status_code=400)
        redirect_resp = RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)
        redirect_resp.set_cookie(key="username", value=username)
        return redirect_resp
        
    elif action == "login":
        success = authenticate_user(username, password)
        if not success:
            return HTMLResponse("Invalid credentials. <a href='/login'>Go back</a>", status_code=400)
            
        redirect_resp = RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)
        redirect_resp.set_cookie(key="username", value=username)
        return redirect_resp

@app.get("/logout")
async def logout():
    redirect_resp = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    redirect_resp.delete_cookie("username")
    return redirect_resp

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/login")
    
    from app.auth import get_user_roles
    roles = get_user_roles(username)
    
    roles_html = ""
    for role in roles:
        roles_html += f'''
        <a href="/dashboard/{role['learner_id']}" class="block p-4 rounded-xl border border-slate-700 bg-slate-800/50 hover:bg-slate-800 transition-colors">
            <h3 class="text-lg font-bold text-white">{role['target_role']}</h3>
            <p class="text-sm text-slate-400">View progress dashboard →</p>
        </a>
        '''
        
    if not roles:
        roles_html = "<p class='text-slate-400'>You haven't added any roles yet.</p>"
        
    html_content = f'''
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-slate-950 text-slate-100">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>My Profile | EduPath</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
    </head>
    <body class="min-h-full flex items-center justify-center font-sans antialiased bg-slate-950 p-4">
        <div class="rounded-2xl border border-slate-800 p-8 w-full max-w-lg shadow-2xl relative overflow-hidden bg-slate-900/80 backdrop-blur-lg">
            <div class="flex items-center justify-between mb-8">
                <div class="flex items-center gap-3">
                    <img src="/static/logo.png" class="w-12 h-12 rounded-xl object-cover shadow-lg">
                    <h1 class="text-2xl font-bold text-white font-heading">My Roles</h1>
                </div>
                <a href="/logout" class="px-4 py-2 text-sm text-rose-400 bg-rose-400/10 hover:bg-rose-400/20 rounded-lg transition-colors">Logout</a>
            </div>
            
            <div class="space-y-4 mb-8">
                {roles_html}
            </div>
            
            <a href="/onboard" class="w-full block text-center py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold rounded-lg shadow-lg transition-all">
                + Add New Role
            </a>
        </div>
    
<script>
    document.addEventListener('DOMContentLoaded', () => {{
        const overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'fixed inset-0 z-[9999] hidden bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center';
        overlay.innerHTML = `
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500 mb-4"></div>
            <h2 class="text-2xl font-bold text-white mb-2">Loading...</h2>
            <p class="text-slate-400">Please wait, taking only minimum time!</p>
        `;
        document.body.appendChild(overlay);

        function showLoading() {{
            document.getElementById('globalLoadingOverlay').classList.remove('hidden');
        }}

        document.querySelectorAll('a').forEach(link => {{
            link.addEventListener('click', (e) => {{
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && link.getAttribute('target') !== '_blank') {{
                    showLoading();
                }}
            }});
        }});

        document.querySelectorAll('form').forEach(form => {{
            form.addEventListener('submit', () => {{
                showLoading();
            }});
        }});
    }});
</script>
</body>

    </html>
    '''
    return HTMLResponse(content=html_content)


