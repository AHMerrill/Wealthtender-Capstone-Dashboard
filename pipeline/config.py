"""Pipeline configuration — paths, constants, and dimension queries.

See NOTICE for full team attribution.
"""
import os

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
INTERMEDIATE_DIR = os.path.join(PROJECT_ROOT, "data", "intermediate")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")

# Input
RAW_CSV = os.path.join(RAW_DIR, "wealthtender_reviews.csv")

# Output artifact paths
MACRO_DIR = os.path.join(ARTIFACTS_DIR, "macro_insights")
SCORING_DIR = os.path.join(ARTIFACTS_DIR, "scoring")
QUALITY_DIR = os.path.join(MACRO_DIR, "quality")
LEXICAL_DIR = os.path.join(MACRO_DIR, "lexical")

# Intermediate files (large, gitignored)
EMBEDDINGS_CSV = os.path.join(INTERMEDIATE_DIR, "df_embeddings_MVP.csv")
ADVISOR_EMBEDDINGS_PARQUET = os.path.join(INTERMEDIATE_DIR, "advisor_embeddings_MVP.parquet")
ADVISOR_WEIGHTED_PARQUET = os.path.join(INTERMEDIATE_DIR, "df_advisors_weighted_time.parquet")

# ── Test / demo advisor exclusion list ────────────────────────────────────────
# Explicit advisor IDs for known test accounts on the Wealthtender platform.
# These are filtered out during cleaning so they don't pollute embeddings,
# scores, or the dashboard.
#
# Remove this set (and the filter in clean.py) when the raw export includes
# an is_test or status field — filter on that flag instead of hardcoded IDs.
TEST_ADVISOR_IDS = {
    "Press Advisor Test",                                                  # bare ID, no URL
    "https://wealthtender.com/financial-advisors/press-advisor-test/",     # Press Advisor Test
    "https://wealthtender.com/financial-advisors/demo/",                   # Jane Demo / Demo Jane
    "https://wealthtender.com/financial-advisors/john-geffert-test/",      # TEST John Geffert
    "https://wealthtender.com/financial-advisors/test-advisor-august-2022/",  # TEST ADVISOR August 2022
}

# ── Model ────────────────────────────────────────────────────────────────────
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64

# ── Cleaning thresholds (from NLP_I.ipynb) ───────────────────────────────────
MIN_TOTAL_TOKENS = 150
INFORMATIVE_TOKENS = 75
MIN_REVIEWS = 5

# ── Dimension queries (from notebooks/Embeddings+Scoring.ipynb) ──────────────
DIMENSION_QUERIES = {
    "trust_integrity": "I feel secure because my advisor always puts my best interests first and has unwavering honesty and the highest ethical integrity. They are fully transparent about their fees and act as a fiduciary.",
    "listening_personalization": "They take the time to listen to my needs and concerns and understand my personal goals. Instead of a standard, generic approach, they fit a customized and personalized roadmap that aligns with my unique situation and values.",
    "communication_clarity": "They are a strong communicator who explains complex concepts clearly without using confusing technical jargon. I always understand the logic, thought process, and rationale behind their recommendations because they keep me fully educated and informed.",
    "responsiveness_availability": "The level of customer service is exceptional; they are incredibly responsive, always accessible, and promptly return my calls and emails. Whenever I have an urgent question, they provide the fast, immediate support I need.",
    "life_event_support": "They have been compassionate and shown empathy, patience, and emotional support through major life transitions like divorce, sending a kid to college, or a death in the family. They truly care about my well-being and provide amazing support during stressful times.",
    "investment_expertise": "I have total confidence in their market knowledge, technical expertise, and skilled investment strategy. They are a professional who expertly navigates complex asset allocation and risk to produce positive returns.",
    "outcomes_results": "They delivered tangible results and ensured I successfully achieved my milestones and life goals. Thanks to their commitment, I have earned the financial goals I came to them for.",
}

# ── Stopwords (from NLP_I.ipynb) ─────────────────────────────────────────────
DOMAIN_STOPWORDS = {
    "advisor",
    "advisors",
    "financial",
    "finance",
    "wealth",
    "firm",
    "company",
    "client", "clients",
    "also",
    "would",
    "make",
    "always",
    "looking",
    "years",
    "know",
    "with", "with.",
    "anyone",
    "scale",
    "recommend",
    "berkshire",
    "lorem", "ipsum",
}

# ── Prompt patterns to strip (from NLP_I.ipynb) ─────────────────────────────
PROMPT_PATTERNS = [
    r"things\s+you\s+value\s+in\s+your\s+advisor[:\s]*",
    r"top\sthings\s+you\s+value\s+in\s+your\s+advisor[:\s]*",
    r"things\s+value\s+advisor[:\s]*",
    r"how\s+well\s+do\s+you\s+feel.*?\?",
    r"how\s+would\s+you\s+describe.*?\?",
    r"how\s+likely.*?\?",
    r"if\s+you\s+have\s+any\s+other\s+feedback\s+for\s+us[:\s]*",
    r"\bwe\s*'?\s*d\s+love\s+to\s+hear\s+from\s+you\b[^\w]*",
    r"on\s+a\s+scale\s+of\s+\d+\s*[-–]\s*\d+[:\s]*",
    r"scale\s+from\s+\d+\s*[-–]\s*\d+",
    r"please\s+rate[:\s]*",
    r"&amp\d+",
    r"client first capital",
]

# ── Boilerplate patterns to strip (from WT_Capstone_ReviewPipeline.ipynb) ────
BOILERPLATE_PATTERNS = [
    r"this reviewer received no compensation.*",
    r"there are no material conflicts of interest.*",
]
