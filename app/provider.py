"""
Provider switch for AI functions.
Member A edits this on `develop` to switch from mock to real functions.
"""

# Import real AI functions safely

AI_ERROR = None
try:
    from ai import core as real_ai
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f'Failed to import ai.core: {e}')
    real_ai = None
    AI_ERROR = str(e)

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
USE_REAL_WRITE_REPORT = True

# --- Exported Functions ---

def extract_text_from_file(*args, **kwargs):
    return (real_ai if (USE_REAL_EXTRACT_TEXT and real_ai is not None) else mock_ai).extract_text_from_file(*args, **kwargs)

def analyze_profile(*args, **kwargs):
    return (real_ai if (USE_REAL_ANALYZE_PROFILE and real_ai is not None) else mock_ai).analyze_profile(*args, **kwargs)

def find_gaps(*args, **kwargs):
    return (real_ai if (USE_REAL_FIND_GAPS and real_ai is not None) else mock_ai).find_gaps(*args, **kwargs)

def recommend_resources(*args, **kwargs):
    return (real_ai if (USE_REAL_RECOMMEND_RESOURCES and real_ai is not None) else mock_ai).recommend_resources(*args, **kwargs)

def generate_plan(*args, **kwargs):
    return (real_ai if (USE_REAL_GENERATE_PLAN and real_ai is not None) else mock_ai).generate_plan(*args, **kwargs)

def replan(*args, **kwargs):
    return (real_ai if (USE_REAL_REPLAN and real_ai is not None) else mock_ai).replan(*args, **kwargs)

def answer_question(*args, **kwargs):
    return (real_ai if (USE_REAL_ANSWER_QUESTION and real_ai is not None) else mock_ai).answer_question(*args, **kwargs)

def write_report_narrative(*args, **kwargs):
    return (real_ai if (USE_REAL_WRITE_REPORT and real_ai is not None) else mock_ai).write_report_narrative(*args, **kwargs)
