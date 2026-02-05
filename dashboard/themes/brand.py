BRAND_CSS = """
<!DOCTYPE html>
<html>
  <head>
    {%metas%}
    <title>Wealthtender Dashboard</title>
    {%favicon%}
    {%css%}
    <style>
      :root {
        --wt-blue: #1c417d;
        --wt-ink: #111827;
        --wt-soft-blue: #e3f5fe;
        --wt-soft-lavender: #ebebff;
        --wt-red: #790000;
        --wt-bg: #f8fbff;
      }
      body {
        margin: 0;
        font-family: "Open Sans", Arial, sans-serif;
        background: linear-gradient(180deg, var(--wt-soft-blue), var(--wt-bg));
        color: var(--wt-ink);
      }
      .app-shell { min-height: 100vh; }
      .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 24px;
        background: white;
        border-bottom: 1px solid #e5e7eb;
      }
      .brand-title {
        font-weight: 700;
        color: var(--wt-blue);
        font-size: 18px;
      }
      .top-nav-links a {
        margin-left: 16px;
        color: var(--wt-ink);
        text-decoration: none;
        font-weight: 600;
      }
      .content-shell {
        display: grid;
        grid-template-columns: 240px 1fr;
        gap: 16px;
        padding: 16px 24px 32px 24px;
      }
      .sidebar {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px;
        height: fit-content;
      }
      .sidebar-title { font-weight: 700; margin-bottom: 8px; }
      .sidebar-note { color: #6b7280; font-size: 13px; }
      .page-container {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 24px;
        min-height: 70vh;
      }
      .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(120px, 1fr));
        gap: 12px;
      }
      .kpi-card {
        background: var(--wt-soft-lavender);
        border-radius: 10px;
        padding: 12px;
      }
      .kpi-label { font-size: 12px; color: #374151; }
      .kpi-value { font-size: 20px; font-weight: 700; color: var(--wt-blue); }
    </style>
  </head>
  <body>
    {%app_entry%}
    <footer>
      {%config%}
      {%scripts%}
      {%renderer%}
    </footer>
  </body>
</html>
"""
