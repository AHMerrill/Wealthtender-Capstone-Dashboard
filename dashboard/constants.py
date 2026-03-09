"""Shared constants for Advisor DNA dimensions.

Used by advisor_dna.py, benchmarks.py, leaderboard.py, and comparisons.py.
"""

from dashboard.branding import DATA_VIZ_PALETTE

DIMENSIONS = [
    "trust_integrity",
    "listening_personalization",
    "communication_clarity",
    "responsiveness_availability",
    "life_event_support",
    "investment_expertise",
]

DIM_LABELS = {
    "trust_integrity": "Trust & Integrity",
    "listening_personalization": "Customer Empathy & Personalization",
    "communication_clarity": "Communication Clarity",
    "responsiveness_availability": "Responsiveness",
    "life_event_support": "Life Event Support",
    "investment_expertise": "Investment Expertise",
}

DIM_SHORT = {
    "trust_integrity": "Trust",
    "listening_personalization": "Empathy",
    "communication_clarity": "Clarity",
    "responsiveness_availability": "Responsive",
    "life_event_support": "Life Events",
    "investment_expertise": "Expertise",
}

DIM_COLORS = {dim: DATA_VIZ_PALETTE[i] for i, dim in enumerate(DIMENSIONS)}
