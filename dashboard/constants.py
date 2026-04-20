"""Shared constants for Advisor DNA dimensions.

Single source of truth for all dashboard pages:
advisor_dna.py, all_reviews.py, benchmarks.py, leaderboard.py, and comparisons.py.

IMPORTANT: Other page modules must import dimension data from HERE, never
cross-import from another page module.  Cross-page imports cause Dash to
register the same page twice under different module names, which corrupts
the callback graph and blanks the entire dashboard.
"""

from dashboard.branding import DATA_VIZ_PALETTE

DIMENSIONS = [
    "trust_integrity",
    "listening_personalization",
    "communication_clarity",
    "responsiveness_availability",
    "life_event_support",
    "investment_expertise",
    "outcomes_results",
]

DIM_LABELS = {
    "trust_integrity": "Trust & Integrity",
    "listening_personalization": "Customer Empathy & Personalization",
    "communication_clarity": "Communication Clarity",
    "responsiveness_availability": "Responsiveness",
    "life_event_support": "Life Event Support",
    "investment_expertise": "Investment Expertise",
    "outcomes_results": "Outcomes & Results",
}

DIM_SHORT = {
    "trust_integrity": "Trust",
    "listening_personalization": "Empathy",
    "communication_clarity": "Clarity",
    "responsiveness_availability": "Responsive",
    "life_event_support": "Life Events",
    "investment_expertise": "Expertise",
    "outcomes_results": "Outcomes",
}

# Indices intentionally skip palette[4] (deep navy, too close to palette[0]).
DIM_COLORS = {
    "trust_integrity": DATA_VIZ_PALETTE[0],
    "listening_personalization": DATA_VIZ_PALETTE[1],
    "communication_clarity": DATA_VIZ_PALETTE[2],
    "responsiveness_availability": DATA_VIZ_PALETTE[3],
    "life_event_support": DATA_VIZ_PALETTE[5],
    "investment_expertise": DATA_VIZ_PALETTE[6],
    "outcomes_results": DATA_VIZ_PALETTE[7],
}

# Short one-liner descriptions for dimension card grids.
DIM_DESCRIPTIONS = {
    "trust_integrity": "Advisors act as fiduciaries with honesty, integrity, and full fee transparency.",
    "listening_personalization": "Advisors listen, understand personal goals, and tailor a customized roadmap.",
    "communication_clarity": "Complex concepts explained clearly, without jargon, with full rationale.",
    "responsiveness_availability": "Accessible, responsive, and prompt with calls, emails, and urgent questions.",
    "life_event_support": "Compassionate support through divorce, college, loss, and other major transitions.",
    "investment_expertise": "Skilled market knowledge, asset allocation, and risk-managed returns.",
    "outcomes_results": "Tangible results and delivery on the milestones and life goals clients hired them for.",
}

# Full canonical query texts — the "ideal review" each review is compared
# against via sentence-embedding cosine similarity. These MUST match
# pipeline/config.py DIMENSION_QUERIES byte-for-byte.
DIM_QUERY_TEXTS = {
    "trust_integrity": "I feel secure because my advisor always puts my best interests first and has unwavering honesty and the highest ethical integrity. They are fully transparent about their fees and act as a fiduciary.",
    "listening_personalization": "They take the time to listen to my needs and concerns and understand my personal goals. Instead of a standard, generic approach, they fit a customized and personalized roadmap that aligns with my unique situation and values.",
    "communication_clarity": "They are a strong communicator who explains complex concepts clearly without using confusing technical jargon. I always understand the logic, thought process, and rationale behind their recommendations because they keep me fully educated and informed.",
    "responsiveness_availability": "The level of customer service is exceptional; they are incredibly responsive, always accessible, and promptly return my calls and emails. Whenever I have an urgent question, they provide the fast, immediate support I need.",
    "life_event_support": "They have been compassionate and shown empathy, patience, and emotional support through major life transitions like divorce, sending a kid to college, or a death in the family. They truly care about my well-being and provide amazing support during stressful times.",
    "investment_expertise": "I have total confidence in their market knowledge, technical expertise, and skilled investment strategy. They are a professional who expertly navigates complex asset allocation and risk to produce positive returns.",
    "outcomes_results": "They delivered tangible results and ensured I successfully achieved my milestones and life goals. Thanks to their commitment, I have earned the financial goals I came to them for.",
}
