import dash
from dash import html, dcc, callback, Input, Output, State, ALL, no_update

from dashboard.branding import COLORS

dash.register_page(__name__, path="/methodology", title="Methodology")

# ---------------------------------------------------------------------------
# Section content — each entry is a dict with "id", "title", "content"
# Content is a list of Dash HTML components.
# ---------------------------------------------------------------------------

SECTIONS = [
    {
        "id": "overview",
        "title": "Project Overview",
        "content": [
            html.P(
                "This dashboard provides an interactive analytics platform for evaluating "
                "financial advisor quality based on client reviews collected by Wealthtender. "
                "It combines natural language processing (NLP), embedding-based semantic "
                "similarity scoring, and interactive data visualization to surface insights "
                "across six dimensions of advisor quality."
            ),
            html.P(
                "The system is built as two independent services: a FastAPI backend that "
                "processes and serves pre-computed analytical artifacts, and a Plotly Dash "
                "frontend that renders interactive visualizations and drill-down interfaces. "
                "Both services are containerized and deployed on Render, communicating over "
                "authenticated REST endpoints."
            ),
            html.P(
                "The analytical pipeline operates in two phases. First, an offline scoring "
                "notebook generates dimension scores for every review and entity using "
                "sentence-transformer embeddings. Second, the dashboard consumes those "
                "pre-built artifacts at runtime, computing percentiles, tier labels, and "
                "aggregate statistics on the fly without re-running the NLP models."
            ),
        ],
    },
    {
        "id": "data-source",
        "title": "Data Source & Corpus",
        "content": [
            html.P(
                "The review corpus consists of client-submitted reviews hosted on Wealthtender's "
                "platform. Each review includes the raw text, a star rating, the reviewer's name, "
                "the review date, and the associated advisor or firm. Reviews span multiple years "
                "and cover both individual financial advisors and advisory firms."
            ),
            html.P(
                "The current dataset contains 4,579 reviews across 334 entities (288 individual "
                "advisors and 46 firms). Review counts per entity range from 1 to 135, with a "
                "median of 9 and a mean of approximately 13.7. This skewed distribution is a key "
                "consideration for statistical confidence, motivating the confidence tier system "
                "described later."
            ),
            html.H4("Data Cleaning", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Raw reviews undergo a cleaning pipeline that normalizes whitespace, strips HTML "
                "entities, and standardizes encoding. A cleaned token count is computed for each "
                "review using a simple tokenizer that lowercases text, removes non-alphanumeric "
                "characters (preserving apostrophes), collapses whitespace, and drops single-character "
                "tokens. These cleaned token counts power the EDA word count distributions and filters."
            ),
        ],
    },
    {
        "id": "eda",
        "title": "Exploratory Data Analysis (EDA)",
        "content": [
            html.P(
                "The EDA module provides a comprehensive statistical overview of the review corpus. "
                "All charts are computed dynamically from the cleaned review data, supporting "
                "real-time filtering by entity, date range, rating, word count, and review volume."
            ),
            html.H4("Review Volume Over Time", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Reviews are aggregated into time buckets at three granularities: monthly, quarterly, "
                "and yearly. The time series uses pandas resampling with period-start alignment "
                "(MS, QS, YS codes). Users toggle granularity to smooth out noise in early periods "
                "when review volume was sparse."
            ),
            html.H4("Rating Distribution", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Star ratings are tabulated using value_counts and rendered as a bar chart. "
                "Missing ratings are included in the distribution as a separate category to "
                "surface data completeness issues."
            ),
            html.H4("Word Count Analysis", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Word counts are derived from cleaned token counts (not raw character length). "
                "The distribution is rendered as a histogram, and summary statistics (quartiles, "
                "mean, percentage under 20 and 50 words) are reported. A scatter plot of rating "
                "vs. word count helps identify whether review length correlates with sentiment."
            ),
            html.H4("Lexical Analysis (N-Grams)", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Top unigrams and bigrams are extracted by tokenizing each cleaned review, "
                "generating n-gram sequences, and counting frequencies across the corpus. "
                "Stopword filtering uses a vendored copy of the NLTK 3.8.1 English stopword "
                "list (174 words) and is applied only to the n-gram chart — not to word counts "
                "or other metrics. Users can also supply custom stopwords for domain-specific "
                "filtering."
            ),
            html.H4("Coverage Metrics", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Coverage analysis reports the percentage of advisors with fewer than 3, 5, and "
                "10 reviews, the median reviews per advisor, and the 90th percentile. These "
                "metrics inform decisions about minimum thresholds for statistical reliability "
                "and feed directly into the confidence tier design."
            ),
        ],
    },
    {
        "id": "embeddings",
        "title": "Sentence Embeddings",
        "content": [
            html.P(
                "The core NLP approach uses sentence-transformer models to encode both review "
                "texts and dimension query strings into dense vector representations (embeddings). "
                "These embeddings capture semantic meaning, allowing us to measure how closely "
                "a review's language aligns with each quality dimension — even when the review "
                "doesn't use the exact words from the dimension description."
            ),
            html.H4("Embedding Model", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Review texts and query strings are encoded using the "
                "all-MiniLM-L6-v2 model from the sentence-transformers library. "
                "This model maps variable-length text inputs to 384-dimensional dense vectors "
                "in a shared semantic space. This encoding is performed offline in a Jupyter notebook "
                "and the resulting embeddings are stored as Parquet files for efficient reuse."
            ),
            html.H4("Review Embeddings", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Each review in the corpus is encoded once into a single embedding vector. These "
                "vectors are pre-computed and stored, eliminating the need to run the transformer "
                "model at dashboard runtime. The embedding captures the full semantic content "
                "of the review text."
            ),
            html.H4("Dimension Query Strings", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Six carefully crafted query strings define the quality dimensions. Each query is "
                "a detailed paragraph (approximately 60-80 words) that describes the ideal client "
                "experience for that dimension. These queries were developed through a combination "
                "of subject matter expertise, analysis of real client reviews, and iterative "
                "refinement with large language models (LLMs). They are designed to capture nuanced "
                "aspects of advisor quality that go beyond simple keyword matching."
            ),
            html.P(
                "The six dimensions are: Trust & Integrity, Customer Empathy & Personalization, "
                "Communication Clarity, Responsiveness, Life Event Support, and Investment Expertise. "
                "Each query string is encoded into the same embedding space as the reviews, enabling "
                "direct cosine similarity comparison."
            ),
        ],
    },
    {
        "id": "similarity-scoring",
        "title": "Cosine Similarity Scoring",
        "content": [
            html.P(
                "Cosine similarity measures the angular distance between two vectors in embedding "
                "space. A score of 1.0 indicates identical direction (perfect semantic alignment), "
                "while 0.0 indicates orthogonality (no semantic relationship). In practice, review "
                "similarity scores for advisor quality dimensions typically range from 0.05 to 0.65."
            ),
            html.H4("Review-Level Scores", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "For each review, cosine similarity is computed against all six dimension query "
                "embeddings, producing a 6-dimensional score vector per review. This is stored in "
                "review_dimension_scores.csv with columns sim_trust_integrity, sim_listening_personalization, "
                "etc. These per-review scores are the atomic unit of the scoring system."
            ),
            html.H4("Score Interpretation", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Higher cosine similarity means the review's language more closely mirrors the "
                "dimension's ideal description. For example, a review mentioning 'honesty,' "
                "'fiduciary duty,' and 'transparency' will score higher on Trust & Integrity "
                "than on Investment Expertise. Importantly, a single review can score well on "
                "multiple dimensions simultaneously — the dimensions are not mutually exclusive."
            ),
        ],
    },
    {
        "id": "aggregation",
        "title": "Entity-Level Aggregation",
        "content": [
            html.P(
                "Review-level similarity scores are aggregated to the entity level (advisor or firm) "
                "using three methods, each designed to surface different aspects of performance."
            ),
            html.H4("Mean Scoring", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The simple arithmetic mean of all review-level cosine similarity scores for an "
                "entity within each dimension. This gives equal weight to every review regardless "
                "of when it was written or how consistent it is with other reviews. It represents "
                "the overall central tendency of client sentiment."
            ),
            html.H4("Penalized Scoring", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The mean score adjusted by a consistency penalty. Entities with high variance in "
                "their review scores (indicating inconsistent client experiences) receive a lower "
                "penalized score than entities with consistent scores. The penalty is proportional "
                "to the standard deviation of review-level scores within each dimension. This method "
                "rewards advisors whose clients consistently report similar experiences."
            ),
            html.H4("Weighted Scoring", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "A time-weighted mean that gives more recent reviews higher influence. Older reviews "
                "contribute less to the aggregate score, reflecting the idea that recent client "
                "experiences are more indicative of current advisor quality. The weighting function "
                "applies exponential decay based on review age."
            ),
            html.H4("Entity Types", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Aggregation is performed separately for individual advisors and firms. Firm-level "
                "scores are computed from all reviews associated with that firm entity. The current "
                "dataset contains 288 advisors and 46 firms. Tier labels and percentile ranks are "
                "computed within each entity type to ensure fair peer-group comparisons."
            ),
        ],
    },
    {
        "id": "percentiles",
        "title": "Percentile Ranking",
        "content": [
            html.P(
                "Raw cosine similarity scores are difficult to interpret in isolation — a score of "
                "0.42 on Trust & Integrity has no intuitive meaning. Percentile ranking transforms "
                "these scores into a 0-100 scale that answers the question: 'How does this entity "
                "compare to peers?'"
            ),
            html.H4("Calculation Method", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Percentile ranks are computed using pandas rank(pct=True) within each entity type "
                "(advisor or firm) and scoring method (mean, penalized, weighted). The rank is "
                "multiplied by 100 and rounded to one decimal place. A percentile of 82.5 means "
                "the entity scores higher than 82.5% of peers on that dimension."
            ),
            html.H4("Peer Group Composition", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "By default, the peer group includes all entities of the same type (all 288 advisors "
                "or all 46 firms). The premier pool option restricts the peer group to entities with "
                "20 or more reviews, creating a higher-bar comparison against well-reviewed peers. "
                "The target entity is always included in its own percentile calculation regardless "
                "of review count."
            ),
            html.H4("Method-Specific Breakpoints", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Tier breakpoints (P25, P50, P75) are computed separately for each scoring method "
                "and entity type. This means the threshold for 'Very Strong' under weighted scoring "
                "may differ from the threshold under mean scoring. The breakpoints are requested "
                "from the API at render time and used consistently across all visualizations."
            ),
        ],
    },
    {
        "id": "tiers",
        "title": "Performance Tiers",
        "content": [
            html.P(
                "Four performance tiers translate percentile ranks into plain-language labels that "
                "advisors and firms can immediately understand."
            ),
            html.Div(
                style={"margin": "16px 0", "display": "flex", "flexDirection": "column", "gap": "8px"},
                children=[
                    _tier_card("Very Strong", "75th percentile and above",
                               "Top-quartile performance. This entity excels in this dimension relative to peers."),
                    _tier_card("Strong", "50th to 75th percentile",
                               "Above-median performance. Consistently positive client sentiment in this area."),
                    _tier_card("Moderate", "25th to 50th percentile",
                               "Below-median but not critically low. Room for targeted improvement."),
                    _tier_card("Foundational", "Below 25th percentile",
                               "Lowest quartile. This dimension may benefit from focused attention and strategy."),
                ],
            ) if False else html.Div(),  # placeholder to avoid forward ref — built inline below
            html.Table(
                style={"width": "100%", "borderCollapse": "collapse", "marginTop": "16px", "fontSize": "14px"},
                children=[
                    html.Thead(html.Tr([
                        html.Th("Tier", style={"textAlign": "left", "padding": "8px 12px",
                                                "borderBottom": f"2px solid {COLORS['border']}",
                                                "color": COLORS["navy"]}),
                        html.Th("Percentile Range", style={"textAlign": "left", "padding": "8px 12px",
                                                            "borderBottom": f"2px solid {COLORS['border']}",
                                                            "color": COLORS["navy"]}),
                        html.Th("Interpretation", style={"textAlign": "left", "padding": "8px 12px",
                                                          "borderBottom": f"2px solid {COLORS['border']}",
                                                          "color": COLORS["navy"]}),
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td("Very Strong", style={"padding": "8px 12px", "fontWeight": "600",
                                                           "borderBottom": f"1px solid {COLORS['border']}"}),
                            html.Td("\u2265 75th percentile", style={"padding": "8px 12px",
                                                                      "borderBottom": f"1px solid {COLORS['border']}"}),
                            html.Td("Top-quartile performance; this entity excels relative to peers.",
                                     style={"padding": "8px 12px",
                                            "borderBottom": f"1px solid {COLORS['border']}"}),
                        ]),
                        html.Tr([
                            html.Td("Strong", style={"padding": "8px 12px", "fontWeight": "600",
                                                      "borderBottom": f"1px solid {COLORS['border']}"}),
                            html.Td("50th \u2013 75th percentile", style={"padding": "8px 12px",
                                                                           "borderBottom": f"1px solid {COLORS['border']}"}),
                            html.Td("Above-median performance; consistently positive client sentiment.",
                                     style={"padding": "8px 12px",
                                            "borderBottom": f"1px solid {COLORS['border']}"}),
                        ]),
                        html.Tr([
                            html.Td("Moderate", style={"padding": "8px 12px", "fontWeight": "600",
                                                        "borderBottom": f"1px solid {COLORS['border']}"}),
                            html.Td("25th \u2013 50th percentile", style={"padding": "8px 12px",
                                                                           "borderBottom": f"1px solid {COLORS['border']}"}),
                            html.Td("Below median; room for targeted improvement in this area.",
                                     style={"padding": "8px 12px",
                                            "borderBottom": f"1px solid {COLORS['border']}"}),
                        ]),
                        html.Tr([
                            html.Td("Foundational", style={"padding": "8px 12px", "fontWeight": "600"}),
                            html.Td("Below 25th percentile", style={"padding": "8px 12px"}),
                            html.Td("Lowest quartile; this dimension may benefit from focused attention.",
                                     style={"padding": "8px 12px"}),
                        ]),
                    ]),
                ],
            ),
            html.P(
                "Tier assignments use raw similarity breakpoints when in raw mode and "
                "percentile thresholds (25/50/75) when in percentile mode. Breakpoints are "
                "computed per scoring method and entity type, so tier boundaries adapt to "
                "the distribution of each population.",
                style={"marginTop": "16px"},
            ),
        ],
    },
    {
        "id": "confidence",
        "title": "Confidence Tiers & Premier Pool",
        "content": [
            html.P(
                "Not all entities have enough reviews to produce statistically reliable dimension "
                "scores. A single glowing review can inflate scores just as a single negative review "
                "can deflate them. The confidence tier system communicates data reliability to users "
                "and gates access to the premier benchmarking pool."
            ),
            html.H4("Confidence Zones", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Entities are assigned to one of three confidence zones based on their total "
                "review count:"
            ),
            html.Table(
                style={"width": "100%", "borderCollapse": "collapse", "marginTop": "8px", "fontSize": "14px"},
                children=[
                    html.Thead(html.Tr([
                        html.Th("Review Count", style={"textAlign": "left", "padding": "8px 12px",
                                                        "borderBottom": f"2px solid {COLORS['border']}",
                                                        "color": COLORS["navy"]}),
                        html.Th("Confidence Level", style={"textAlign": "left", "padding": "8px 12px",
                                                            "borderBottom": f"2px solid {COLORS['border']}",
                                                            "color": COLORS["navy"]}),
                        html.Th("User Experience", style={"textAlign": "left", "padding": "8px 12px",
                                                           "borderBottom": f"2px solid {COLORS['border']}",
                                                           "color": COLORS["navy"]}),
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td("< 10 reviews", style={"padding": "8px 12px", "fontWeight": "600",
                                                             "borderBottom": f"1px solid {COLORS['border']}"}),
                            html.Td("Directional", style={"padding": "8px 12px",
                                                           "borderBottom": f"1px solid {COLORS['border']}"}),
                            html.Td("Amber warning banner. Scores are visible but flagged as preliminary.",
                                     style={"padding": "8px 12px",
                                            "borderBottom": f"1px solid {COLORS['border']}"}),
                        ]),
                        html.Tr([
                            html.Td("10 \u2013 19 reviews", style={"padding": "8px 12px", "fontWeight": "600",
                                                                     "borderBottom": f"1px solid {COLORS['border']}"}),
                            html.Td("Standard", style={"padding": "8px 12px",
                                                        "borderBottom": f"1px solid {COLORS['border']}"}),
                            html.Td("Normal access with no additional indicators.",
                                     style={"padding": "8px 12px",
                                            "borderBottom": f"1px solid {COLORS['border']}"}),
                        ]),
                        html.Tr([
                            html.Td("\u2265 20 reviews", style={"padding": "8px 12px", "fontWeight": "600"}),
                            html.Td("Robust", style={"padding": "8px 12px"}),
                            html.Td("Green 'Robust Data' badge. Included in the premier benchmarking pool.",
                                     style={"padding": "8px 12px"}),
                        ]),
                    ]),
                ],
            ),
            html.H4("Premier Benchmarking Pool", style={"marginTop": "20px", "color": COLORS["navy"]}),
            html.P(
                "The premier pool restricts the comparison population to entities with 20 or more "
                "reviews. When enabled, percentile ranks are recomputed against only this subset, "
                "providing a higher-bar benchmark. The current premier pool contains 74 entities "
                "(out of 334 total). This serves a dual purpose: it ensures benchmarks are based "
                "on statistically meaningful data, and it creates a commercial incentive for advisors "
                "to collect more reviews."
            ),
        ],
    },
    {
        "id": "evidence",
        "title": "Evidence Cards",
        "content": [
            html.P(
                "When a user drills into a specific dimension on the entity view, the system surfaces "
                "the top three reviews that most strongly drive that dimension's score. These 'evidence "
                "cards' answer the natural question: 'Why did this entity score this way on this dimension?'"
            ),
            html.H4("Ranking Mechanism", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Reviews are sorted by their cosine similarity score for the selected dimension "
                "in descending order. The top three are displayed as cards, each showing a rank "
                "badge (gold, silver, bronze), the reviewer's name, date, the review's tier and "
                "similarity score for that dimension, and a 200-character text snippet."
            ),
            html.H4("Design Rationale", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Evidence cards bridge the gap between abstract similarity scores and tangible "
                "client feedback. Rather than asking advisors to trust a number, the system shows "
                "them the actual words their clients used. This transparency builds confidence in "
                "the scoring methodology and provides actionable insight: advisors can read what "
                "clients specifically valued."
            ),
        ],
    },
    {
        "id": "visualizations",
        "title": "Visualization Methods",
        "content": [
            html.P(
                "The dashboard uses Plotly for all interactive charts, chosen for its hover tooltips, "
                "click events, and responsive rendering. Chart types were selected based on the "
                "analytical task each view supports."
            ),
            html.H4("Horizontal Bar Charts", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Used for both macro-level dimension totals and entity-level dimension profiles. "
                "Bars are sorted by score (highest at top), color-coded per dimension, and annotated "
                "with rank labels (#1, #2, etc.) or tier labels (Very Strong, Strong, etc.). "
                "Horizontal orientation accommodates long dimension labels without truncation."
            ),
            html.H4("Spider / Radar Charts", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Available as a toggle on both macro and entity views. Radar charts use Plotly's "
                "Scatterpolar trace with a filled polygon showing the dimension profile. Each "
                "vertex is a dimension, with distance from center representing the score. "
                "Individual dimension dots are color-coded and show rank in the legend. "
                "Scroll-zoom is disabled to prevent accidental interaction."
            ),
            html.H4("Review-Level Spider", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "When drilling into a single review, a spider chart displays that review's "
                "six-dimensional similarity profile. The legend is placed externally to avoid "
                "label overlap on the radar grid. This allows direct comparison of how strongly "
                "a single review aligns with each quality dimension."
            ),
            html.H4("EDA Charts", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The EDA module renders time series (line charts), rating distributions (bar charts), "
                "word count histograms, rating vs. word count scatter plots, and n-gram frequency "
                "bar charts. All charts support dynamic filtering and respond to sidebar controls "
                "in real time via Dash callbacks."
            ),
        ],
    },
    {
        "id": "architecture",
        "title": "System Architecture",
        "content": [
            html.P(
                "The dashboard is a two-service system designed for clean separation of concerns. "
                "The API service owns the data and computation; the dashboard service owns the "
                "presentation and user interaction."
            ),
            html.H4("FastAPI Backend", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The API service (api/) is built on FastAPI and serves pre-computed analytical "
                "artifacts over REST endpoints. On startup, it loads all artifact files (CSVs, "
                "JSONs) into an in-memory ArtifactStore singleton. Endpoints are stateless — "
                "each request queries the in-memory data, computes any needed aggregation "
                "(percentiles, breakpoints, filtering), and returns JSON. The API handles "
                "entity listing, review retrieval, dimension scoring, percentile computation, "
                "and EDA payload generation."
            ),
            html.H4("Plotly Dash Frontend", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The dashboard (dashboard/) is a multi-page Plotly Dash application. Each page "
                "is registered via Dash's page registry and rendered within a shared layout shell "
                "that includes a top navigation bar, a contextual sidebar, and a main content area. "
                "The dashboard communicates with the API via an HTTP client (dashboard/services/api.py) "
                "and renders all data through Plotly chart objects and Dash HTML components."
            ),
            html.H4("Callback Architecture", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Dash callbacks provide reactive interactivity. The Advisor DNA page uses a "
                "15-output main callback that responds to view changes, entity selection, scoring "
                "method, display mode, and pool toggles. Separate callbacks handle dimension "
                "click-through (8 outputs), review selection, chart type toggling, and panel "
                "management. Callbacks use allow_duplicate=True where multiple callbacks need "
                "to write to the same output (e.g., hiding/showing panels from different user actions)."
            ),
            html.H4("Artifact Pipeline", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Scoring artifacts are generated offline by a Jupyter notebook that: (1) loads "
                "pre-computed review embeddings from Parquet files, (2) encodes the six dimension "
                "query strings using sentence-transformers, (3) computes cosine similarity between "
                "each review and each query, (4) aggregates to entity level using mean, penalized, "
                "and weighted methods, and (5) exports two CSV files. A metadata.json manifest "
                "tells the API where to find each artifact file."
            ),
        ],
    },
    {
        "id": "auth",
        "title": "Authentication & Access Control",
        "content": [
            html.P(
                "The system implements role-based access control with two user roles and two "
                "authentication layers."
            ),
            html.H4("Roles", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The Admin role (Wealthtender Admin) has full access to all pages and all entities, "
                "including the EDA module, Advisor DNA, Benchmarks, and Methodology. The Firm role "
                "(Firm Portal) has access to Advisor DNA and Benchmarks, scoped to their own firm. "
                "Role definitions are maintained in a single configuration file (roles.py) that "
                "maps each role to its allowed page paths, display labels, and firm-picker visibility."
            ),
            html.H4("Service-to-Service Auth", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The API requires an X-API-Key header on all requests except the health check "
                "endpoint. The dashboard's HTTP client attaches this key automatically. Both services "
                "read the shared secret from the API_KEY environment variable. In local development, "
                "the key is empty and auth is bypassed."
            ),
            html.H4("User-Facing Auth", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The admin portal requires a password entered on the splash page. The check is "
                "performed server-side and cannot be bypassed from the browser. The firm portal "
                "selects from a dropdown. In a production deployment, these would be replaced "
                "with SSO/OAuth integration, with role and firm ID injected from the identity token."
            ),
        ],
    },
    {
        "id": "branding",
        "title": "Branding & Design System",
        "content": [
            html.P(
                "All visual styling is driven by a centralized branding module (branding.py) that "
                "defines colors, fonts, and a data visualization palette. The design system uses "
                "Wealthtender's brand colors as the backbone and extends them with complementary "
                "tones for data visualization."
            ),
            html.H4("Color Palette", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The primary palette is anchored by Wealthtender's brand navy (#004C8C) and sky blue "
                "(#529BD9). The data visualization palette extends to 10 colors: brand blues, "
                "raspberry, deep violet, dark goldenrod, burgundy, soft lavender-purple, mid blue, "
                "and muted gold. Oranges, yellows, and bright reds were excluded to maintain "
                "brand coherence."
            ),
            html.H4("Typography", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Open Sans is used throughout at weights 400, 600, and 700. It is loaded from "
                "Google Fonts and applied globally via CSS custom properties. Chart labels, "
                "tooltips, and legends all inherit from the same font family for visual consistency."
            ),
            html.H4("Component Styling", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "CSS is generated programmatically from the branding module and written to an "
                "assets/theme.css file on startup. This ensures the stylesheet always matches "
                "the Python-defined brand constants. The layout uses CSS Grid for the main "
                "shell (sidebar + content) and Flexbox for navigation and card grids."
            ),
        ],
    },
    {
        "id": "deployment",
        "title": "Deployment & Infrastructure",
        "content": [
            html.P(
                "Both services are containerized using Docker and deployed on Render as separate "
                "web services. A render.yaml blueprint defines the deployment configuration."
            ),
            html.H4("Docker Containers", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "Each service has its own Dockerfile. The API uses Uvicorn as its ASGI server; "
                "the dashboard uses Gunicorn as its WSGI server. Multi-stage builds keep images "
                "lean by separating dependency installation from runtime. Artifacts are baked "
                "into the container image, so the API loads data from the filesystem at startup "
                "with no external database dependency."
            ),
            html.H4("Environment Configuration", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The dashboard discovers the API via the API_BASE environment variable. Both "
                "services share the same API_KEY for authenticated communication. ADMIN_PASSWORD "
                "configures the user-facing login. All variables have sensible defaults for local "
                "development — running locally requires zero configuration."
            ),
            html.H4("Local Development", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "A launcher script (run.sh / run.ps1) auto-detects the best Python version, "
                "creates a virtual environment, installs dependencies, and starts both services "
                "in a single terminal session. Docker Compose is available as an alternative for "
                "developers who prefer containerized local environments."
            ),
            html.H4("WordPress Integration", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The two-service architecture is designed to integrate with existing web platforms "
                "like WordPress. The simplest approach is an iframe embed — the dashboard runs on "
                "its own domain and renders inside a WordPress page with no code changes. "
                "Alternatively, the Dash frontend can be bypassed entirely: WordPress templates or "
                "any other frontend can consume the FastAPI backend directly as a JSON API, giving "
                "full control over presentation. A reverse proxy on a subdomain "
                "(e.g., analytics.wealthtender.com) provides the most seamless experience."
            ),
            html.H4("Future: Live Data Pipeline", style={"marginTop": "16px", "color": COLORS["navy"]}),
            html.P(
                "The current system is snapshot-based — scoring artifacts are static files baked "
                "into the API Docker image at build time. To update the data, the scoring notebook "
                "is rerun, the CSVs are replaced, and the container is rebuilt."
            ),
            html.P(
                "For a production system with continuously incoming reviews, the flat-file storage "
                "can be swapped for a database (e.g., PostgreSQL). The only file that changes is "
                "artifacts.py — CSV reads become database queries. The API endpoints, request "
                "parameters, and JSON response shapes all stay identical, so the dashboard (or any "
                "other frontend consuming the API) requires zero changes. The API is designed to be "
                "storage-agnostic, making this a backend-only migration."
            ),
        ],
    },
]


def _tier_card(label, range_text, description):
    """Helper — not used in final layout, kept for reference."""
    return html.Div()


# ---------------------------------------------------------------------------
# Section index for next/prev navigation
# ---------------------------------------------------------------------------

SECTION_IDS = [s["id"] for s in SECTIONS]
SECTION_TITLES = {s["id"]: s["title"] for s in SECTIONS}


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout():
    # Build TOC items
    toc_items = []
    for i, section in enumerate(SECTIONS):
        toc_items.append(
            html.Div(
                id={"type": "meth-toc-item", "index": section["id"]},
                children=section["title"],
                n_clicks=0,
                style={
                    "padding": "10px 14px",
                    "cursor": "pointer",
                    "borderRadius": "8px",
                    "fontSize": "13px",
                    "fontWeight": "600" if i == 0 else "400",
                    "color": COLORS["blue"] if i == 0 else COLORS["ink"],
                    "background": COLORS["soft_blue"] if i == 0 else "transparent",
                    "transition": "all 0.15s",
                    "borderLeft": f"3px solid {COLORS['blue']}" if i == 0 else "3px solid transparent",
                },
            )
        )

    # Build content sections (all hidden except first)
    content_sections = []
    for i, section in enumerate(SECTIONS):
        content_sections.append(
            html.Div(
                id={"type": "meth-content", "index": section["id"]},
                style={"display": "block" if i == 0 else "none"},
                children=[
                    html.H2(
                        section["title"],
                        style={"color": COLORS["navy"], "marginBottom": "20px",
                               "fontSize": "22px", "fontWeight": "700"},
                    ),
                    html.Div(
                        children=section["content"],
                        style={"lineHeight": "1.7", "fontSize": "14px",
                               "color": COLORS["ink"]},
                    ),
                ],
            )
        )

    return html.Div(
        style={"display": "grid", "gridTemplateColumns": "260px 1fr", "gap": "16px",
               "alignItems": "start"},
        children=[
            # --- Left: Table of Contents ---
            html.Div(
                style={
                    "background": "white",
                    "border": f"1px solid {COLORS['border']}",
                    "borderRadius": "12px",
                    "padding": "16px 8px",
                    "position": "sticky",
                    "top": "16px",
                    "maxHeight": "calc(100vh - 120px)",
                    "overflowY": "auto",
                },
                children=[
                    html.Div(
                        "Methodology",
                        style={
                            "fontWeight": "700", "fontSize": "16px",
                            "color": COLORS["blue"], "padding": "0 14px 12px",
                            "borderBottom": f"1px solid {COLORS['border']}",
                            "marginBottom": "8px",
                        },
                    ),
                    html.Div(id="meth-toc-container", children=toc_items),
                ],
            ),
            # --- Right: Content Panel ---
            html.Div(
                style={
                    "background": "white",
                    "border": f"1px solid {COLORS['border']}",
                    "borderRadius": "12px",
                    "padding": "32px 36px",
                    "minHeight": "70vh",
                },
                children=[
                    # Section content container
                    html.Div(id="meth-content-container", children=content_sections),
                    # Navigation bar
                    html.Div(
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "marginTop": "40px",
                            "paddingTop": "20px",
                            "borderTop": f"1px solid {COLORS['border']}",
                        },
                        children=[
                            html.Button(
                                "\u2190  Previous",
                                id="meth-prev-btn",
                                n_clicks=0,
                                style={
                                    "background": COLORS["soft_blue"],
                                    "border": f"1px solid {COLORS['border']}",
                                    "borderRadius": "8px",
                                    "padding": "8px 20px",
                                    "cursor": "pointer",
                                    "fontWeight": "600",
                                    "fontSize": "13px",
                                    "color": COLORS["ink"],
                                    "visibility": "hidden",
                                },
                            ),
                            html.Span(
                                id="meth-page-indicator",
                                children="1 / {}".format(len(SECTIONS)),
                                style={"fontSize": "13px", "color": COLORS["gray"]},
                            ),
                            html.Button(
                                "Next  \u2192",
                                id="meth-next-btn",
                                n_clicks=0,
                                style={
                                    "background": COLORS["blue"],
                                    "border": "none",
                                    "borderRadius": "8px",
                                    "padding": "8px 20px",
                                    "cursor": "pointer",
                                    "fontWeight": "600",
                                    "fontSize": "13px",
                                    "color": "white",
                                },
                            ),
                        ],
                    ),
                ],
            ),
            # Hidden store for current section index
            dcc.Store(id="meth-current-section", data=0),
        ],
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("meth-current-section", "data", allow_duplicate=True),
    Input({"type": "meth-toc-item", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toc_click(clicks):
    """When user clicks a TOC item, update the current section index."""
    from dash import ctx
    if not ctx.triggered_id or not any(c for c in clicks if c):
        return no_update
    clicked_id = ctx.triggered_id["index"]
    if clicked_id in SECTION_IDS:
        return SECTION_IDS.index(clicked_id)
    return no_update


@callback(
    Output("meth-current-section", "data", allow_duplicate=True),
    Input("meth-prev-btn", "n_clicks"),
    State("meth-current-section", "data"),
    prevent_initial_call=True,
)
def prev_click(n, current):
    if current is None or current <= 0:
        return no_update
    return current - 1


@callback(
    Output("meth-current-section", "data"),
    Input("meth-next-btn", "n_clicks"),
    State("meth-current-section", "data"),
    prevent_initial_call=True,
)
def next_click(n, current):
    if current is None or current >= len(SECTIONS) - 1:
        return no_update
    return current + 1


@callback(
    Output({"type": "meth-content", "index": ALL}, "style"),
    Output({"type": "meth-toc-item", "index": ALL}, "style"),
    Output("meth-prev-btn", "style"),
    Output("meth-next-btn", "style"),
    Output("meth-page-indicator", "children"),
    Input("meth-current-section", "data"),
)
def update_visible_section(current_idx):
    """Show the selected section, highlight its TOC item, update nav buttons."""
    if current_idx is None:
        current_idx = 0

    total = len(SECTIONS)

    # Content visibility
    content_styles = []
    for i in range(total):
        content_styles.append(
            {"display": "block"} if i == current_idx else {"display": "none"}
        )

    # TOC highlighting
    toc_styles = []
    for i in range(total):
        if i == current_idx:
            toc_styles.append({
                "padding": "10px 14px",
                "cursor": "pointer",
                "borderRadius": "8px",
                "fontSize": "13px",
                "fontWeight": "600",
                "color": COLORS["blue"],
                "background": COLORS["soft_blue"],
                "transition": "all 0.15s",
                "borderLeft": f"3px solid {COLORS['blue']}",
            })
        else:
            toc_styles.append({
                "padding": "10px 14px",
                "cursor": "pointer",
                "borderRadius": "8px",
                "fontSize": "13px",
                "fontWeight": "400",
                "color": COLORS["ink"],
                "background": "transparent",
                "transition": "all 0.15s",
                "borderLeft": "3px solid transparent",
            })

    # Prev button
    prev_base = {
        "background": COLORS["soft_blue"],
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "8px",
        "padding": "8px 20px",
        "cursor": "pointer",
        "fontWeight": "600",
        "fontSize": "13px",
        "color": COLORS["ink"],
    }
    if current_idx == 0:
        prev_base["visibility"] = "hidden"
    else:
        prev_base["visibility"] = "visible"

    # Next button
    next_base = {
        "background": COLORS["blue"],
        "border": "none",
        "borderRadius": "8px",
        "padding": "8px 20px",
        "cursor": "pointer",
        "fontWeight": "600",
        "fontSize": "13px",
        "color": "white",
    }
    if current_idx >= total - 1:
        next_base["visibility"] = "hidden"
    else:
        next_base["visibility"] = "visible"

    page_text = f"{current_idx + 1} / {total}"

    return content_styles, toc_styles, prev_base, next_base, page_text
