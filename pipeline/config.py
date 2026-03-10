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

# ── Dimension queries (from query_embeddings_vs_review_embeddings.ipynb) ─────
DIMENSION_QUERIES = {
    "trust_integrity": "I feel a deep sense of security and peace of mind because my advisor acts as a true fiduciary, always putting my best interest before their own commissions or conflicts of interest. They have earned my trust through years of unwavering integrity, honesty, and transparency regarding fees and performance, proving they are an ethical, principled, and reliable professional with a stand-up character who protects my family's future and life savings.",
    "listening_personalization": "My advisor takes the time to truly listen, hear my concerns, and understand my unique goals and risk tolerance. They have built a highly personalized, custom-tailored financial plan and investment strategy that fits my specific situation, aspirations, and values, making me feel like a valued partner rather than just another account number or a sales target.",
    "communication_clarity": "Complex financial concepts are made simple and digestible because my advisor is a master communicator who explains things clearly in plain English without using confusing technical jargon. They provide timely updates, regular check-ins, and transparent breakdowns of my portfolio, ensuring I am well-educated, fully informed, and confident in the logic and rationale behind every recommendation or financial decision.",
    "responsiveness_availability": "The level of service is exceptional; they are always accessible, easy to reach, and promptly return calls or emails within hours, not days. Whether I have a quick question or an urgent concern during market volatility or a personal crisis, they are responsive, attentive, and reliable, providing the immediate support and availability I need to feel taken care of and less anxious about my liquidity and financial health.",
    "life_event_support": "Beyond being a numbers person, they have been a compassionate counselor and supportive partner through major life transitions, including retirement, career changes, marriages, inheritance, or the loss of a loved one. They provide empathy, patience, and guidance during emotional times, offering perspective and hand-holding that goes far beyond a spreadsheet to address the human element and life context of my wealth management.",
    "investment_expertise": "I have total confidence in their technical proficiency, investment pedigree, and deep market knowledge. They are a savvy, highly skilled professional with the credentials and expertise to navigate complex asset allocations, tax strategies, and market cycles. Their competence and strategic insight ensure my portfolio is well-positioned for long-term growth, wealth preservation, and solid returns that meet or exceed my financial expectations.",
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
