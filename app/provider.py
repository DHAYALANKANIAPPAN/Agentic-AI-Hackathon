"""
Provider switch for AI functions.
Member A edits this on `develop` to switch from mock to real functions.
"""

# Import real AI functions safely
try:
    from ai import core as real_ai
except Exception:
    real_ai = None
# Import mock AI functions
from mocks import mock_ai

# --- Provider Switch ---
# True uses the real AI from `ai/core.py`
# False uses the mock AI from `mocks/mock_ai.py`

USE_REAL_EXTRACT_TEXT = True
USE_REAL_ANALYZE_PROFILE = True
USE_REAL_FIND_GAPS = True
USE_REAL_RECOMMEND_RESOURCES = True
USE_REAL_GENERATE_PLAN = True
USE_REAL_REPLAN = True
USE_REAL_ANSWER_QUESTION = True
USE_REAL_WRITE_REPORT = False

# --- Exported Functions ---

def extract_text_from_file(*args, **kwargs):
    return (real_ai if USE_REAL_EXTRACT_TEXT else mock_ai).extract_text_from_file(*args, **kwargs)

def analyze_profile(*args, **kwargs):
    return (real_ai if USE_REAL_ANALYZE_PROFILE else mock_ai).analyze_profile(*args, **kwargs)

def find_gaps(*args, **kwargs):
    return (real_ai if USE_REAL_FIND_GAPS else mock_ai).find_gaps(*args, **kwargs)

def recommend_resources(*args, **kwargs):
    return (real_ai if USE_REAL_RECOMMEND_RESOURCES else mock_ai).recommend_resources(*args, **kwargs)

def generate_plan(*args, **kwargs):
    return (real_ai if USE_REAL_GENERATE_PLAN else mock_ai).generate_plan(*args, **kwargs)

def replan(*args, **kwargs):
    return (real_ai if USE_REAL_REPLAN else mock_ai).replan(*args, **kwargs)

def answer_question(*args, **kwargs):
    return (real_ai if USE_REAL_ANSWER_QUESTION else mock_ai).answer_question(*args, **kwargs)

def write_report_narrative(*args, **kwargs):
    return (real_ai if USE_REAL_WRITE_REPORT else mock_ai).write_report_narrative(*args, **kwargs)
