import dash
from dash import html


dash.register_page(__name__, path="/")


MSBA = [
    "Alisha Surabhi",
    "Joseph Bailey",
    "Chris Breton",
    "Manny Escalante",
    "Zan Merrill",
    "Carolina Rios",
]

UNDERGRAD = [
    "Saif Ansari",
    "Isabelle Demengeon",
    "Abhinav Yarlagadda",
    "Julianna Tijerina",
    "Katelyn Semien",
]


def layout():
    return html.Div(
        children=[
            html.H2("UT Austin MSBA Wealthtender Capstone 2026"),
            html.Div("Choose a View from the Top Menu"),
            html.Div(
                className="section",
                children=[
                    html.A(
                        href="https://wealthtender.com",
                        target="_blank",
                        children=[
                            html.Img(
                                src="/assets/brand/logo-wordmark.svg",
                                className="brand-wordmark",
                                alt="Wealthtender",
                            )
                        ],
                    )
                ],
            ),
            html.Div(
                className="section",
                children=[
                    html.H3("MSBA"),
                    html.Ul([html.Li(name) for name in sorted(MSBA, key=_last_name)]),
                ],
            ),
            html.Div(
                className="section",
                children=[
                    html.H3("Undergrad"),
                    html.Ul([html.Li(name) for name in sorted(UNDERGRAD, key=_last_name)]),
                ],
            ),
        ]
    )


def _last_name(full_name: str) -> str:
    parts = full_name.split()
    return parts[-1] if parts else full_name
