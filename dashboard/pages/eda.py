import dash
from dash import html

dash.register_page(__name__, path="/eda", name="EDA", title="EDA")


def layout():
    # EDA content lives in the static app layout (eda-shell in app.py).
    # This empty page just registers the /eda route for the pages system.
    return html.Div()
