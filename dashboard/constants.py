"""Shared constants for Advisor DNA dimensions.

Single source of truth for all dashboard pages:
advisor_dna.py, benchmarks.py, leaderboard.py, and comparisons.py.
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

# Indices intentionally skip palette[4] (deep navy, too close to palette[0]).
DIM_COLORS = {
    "trust_integrity": DATA_VIZ_PALETTE[0],
    "listening_personalization": DATA_VIZ_PALETTE[1],
    "communication_clarity": DATA_VIZ_PALETTE[2],
    "responsiveness_availability": DATA_VIZ_PALETTE[3],
    "life_event_support": DATA_VIZ_PALETTE[5],
    "investment_expertise": DATA_VIZ_PALETTE[6],
}
