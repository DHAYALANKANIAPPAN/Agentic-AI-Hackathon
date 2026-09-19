# EduPath - Agentic AI Learning Coach

EduPath is an autonomous, AI-driven learning platform that bridges the gap between a user's current skills and their dream career. By leveraging agentic AI, EduPath dynamically analyzes resumes, identifies skill gaps, and generates a fully personalized, adaptive weekly study plan.

## Problem Statement
Traditional online learning is static. Students are often handed a generic curriculum that doesn't account for what they already know, leading to boredom or frustration. EduPath solves this by creating a highly personalized learning roadmap that constantly adapts to the student's progress and struggles.

## Architecture
- **Backend:** FastAPI (Python) serving a RESTful JSON API and SSR HTML.
- **AI Core (Person A):** Integration with LLMs (NVIDIA NIM / Llama 3.2) for profile analysis, gap detection, plan generation, dynamic replanning, and an AI tutor chatbot.
- **Product Layer (Person B):** User Interface (HTML/Tailwind CSS), SQLite database persistence, progress tracking, and interactive dashboards.
- **State Management:** Pydantic models strictly enforce the contract between the AI Core and the Product Layer.

## Setup Steps
1. Clone the repository and navigate into the folder.
2. Create and activate a Python virtual environment (`python3 -m venv venv && source venv/bin/activate`).
3. Install dependencies: `pip install -r requirements.txt` (and `pip install openai python-dotenv` for the NVIDIA backend).
4. Create a `.env` file and add your NVIDIA API key: `NVIDIA_API_KEY=nvapi-your-key-here`.
5. Run the server: `PYTHONPATH=. uvicorn app.main:app`

## Demo Steps
1. Navigate to `http://127.0.0.1:8000/onboard`.
2. Enter your resume and target career role. Click "Analyzing with AI Agent" to watch the agent generate a 1-week adaptive plan.
3. Review your **Skill Gaps** and accept your **Weekly Plan**.
4. Check off items in the plan and mark some as a "struggle" (thumbs down).
5. Click **Replan** to watch the Agentic AI dynamically adjust your future curriculum based on your struggles.
6. Chat with the **AI Tutor** for contextual help.
7. Generate a final **Progress Report**!
