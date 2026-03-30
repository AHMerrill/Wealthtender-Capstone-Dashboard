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
    "trust_integrity": "Clients feel confident their advisor acts honestly and in their best interest.",
    "listening_personalization": "Advisors empathize with client needs and tailor plans to individual goals.",
    "communication_clarity": "Complex financial concepts are explained in plain, understandable language.",
    "responsiveness_availability": "Advisors are accessible and respond promptly to client needs.",
    "life_event_support": "Guidance through major transitions \u2014 retirement, inheritance, career changes.",
    "investment_expertise": "Demonstrated knowledge of markets, portfolios, and financial strategy.",
    "outcomes_results": "Tangible results and measurable progress toward real-world financial goals.",
}

# Full canonical query texts — the "ideal review" each review is compared
# against via sentence-embedding cosine similarity.
DIM_QUERY_TEXTS = {
    "trust_integrity": "I feel a deep sense of security and peace of mind because my advisor acts as a true fiduciary, always putting my best interest before their own commissions or conflicts of interest. They have earned my trust through years of unwavering integrity, honesty, and transparency regarding fees and performance, proving they are an ethical, principled, and reliable professional with a stand-up character who protects my family\u2019s future and life savings.",
    "listening_personalization": "My advisor genuinely empathizes with my situation, takes the time to understand my unique goals and risk tolerance, and makes me feel truly heard. They have built a highly personalized, custom-tailored financial plan and investment strategy that fits my specific circumstances, aspirations, and values, making me feel like a valued partner rather than just another account number or a sales target.",
    "communication_clarity": "Complex financial concepts are made simple and digestible because my advisor is a master communicator who explains things clearly in plain English without using confusing technical jargon. They provide timely updates, regular check-ins, and transparent breakdowns of my portfolio, ensuring I am well-educated, fully informed, and confident in the logic and rationale behind every recommendation or financial decision.",
    "responsiveness_availability": "The level of service is exceptional; they are always accessible, easy to reach, and promptly return calls or emails within hours, not days. Whether I have a quick question or an urgent concern during market volatility or a personal crisis, they are responsive, attentive, and reliable, providing the immediate support and availability I need to feel taken care of and less anxious about my liquidity and financial health.",
    "life_event_support": "Beyond being a numbers person, they have been a compassionate counselor and supportive partner through major life transitions, including retirement, career changes, marriages, inheritance, or the loss of a loved one. They provide empathy, patience, and guidance during emotional times, offering perspective and hand-holding that goes far beyond a spreadsheet to address the human element and life context of my wealth management.",
    "investment_expertise": "I have total confidence in their technical proficiency, investment pedigree, and deep market knowledge. They are a savvy, highly skilled professional with the credentials and expertise to navigate complex asset allocations, tax strategies, and market cycles. Their competence and strategic insight ensure my portfolio is well-positioned for long-term growth, wealth preservation, and solid returns that meet or exceed my financial expectations.",
    "outcomes_results": "My advisor has delivered tangible results and measurable progress toward my real-world goals, ensuring I have achieved milestones like becoming debt-free, funding a college education, or reaching retirement readiness. They have successfully implemented my tax strategies, finalized estate documents, and consolidated my accounts, demonstrating the follow-through and execution needed to advance my financial plan, avoid costly mistakes, and effectively course-correct when the market or my life changed.",
}
