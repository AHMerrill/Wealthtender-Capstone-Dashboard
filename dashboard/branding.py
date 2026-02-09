from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FONT_FAMILY = '"Open Sans", Arial, sans-serif'

COLORS = {
    "blue": "#1c417d",
    "ink": "#111827",
    "gray": "#6b7280",
    "soft_blue": "#e3f5fe",
    "soft_lavender": "#ebebff",
    "red": "#790000",
    "bg": "#f8fbff",
}

DATA_VIZ_PALETTE = [
    "#111827",
    "#1c417d",
    "#6b7280",
    "#ffffff",
    "#e3f5fe",
    "#790000",
    "#5757dd",
    "#5a8fd0",
    "#1da1f2",
    "#000000",
]

THEME_CSS = f"""@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');

:root {{
  --wt-blue: {COLORS["blue"]};
  --wt-ink: {COLORS["ink"]};
  --wt-gray: {COLORS["gray"]};
  --wt-soft-blue: {COLORS["soft_blue"]};
  --wt-soft-lavender: {COLORS["soft_lavender"]};
  --wt-red: {COLORS["red"]};
  --wt-bg: {COLORS["bg"]};

  /* Data-viz palette */
  --wt-dv-1: {DATA_VIZ_PALETTE[0]};
  --wt-dv-2: {DATA_VIZ_PALETTE[1]};
  --wt-dv-3: {DATA_VIZ_PALETTE[2]};
  --wt-dv-4: {DATA_VIZ_PALETTE[3]};
  --wt-dv-5: {DATA_VIZ_PALETTE[4]};
  --wt-dv-6: {DATA_VIZ_PALETTE[5]};
  --wt-dv-7: {DATA_VIZ_PALETTE[6]};
  --wt-dv-8: {DATA_VIZ_PALETTE[7]};
  --wt-dv-9: {DATA_VIZ_PALETTE[8]};
  --wt-dv-10: {DATA_VIZ_PALETTE[9]};
}}

* {{ box-sizing: border-box; }}

body {{
  margin: 0;
  font-family: {FONT_FAMILY};
  font-size: 16px;
  background: linear-gradient(180deg, var(--wt-soft-blue), var(--wt-bg));
  color: var(--wt-ink);
}}

h1, h2, h3 {{
  font-weight: 700;
  color: var(--wt-ink);
  margin: 0 0 12px 0;
}}

h2 {{ font-size: 24px; }}

a {{ color: var(--wt-blue); text-decoration: none; }}

.app-shell {{ min-height: 100vh; }}

.top-nav {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 28px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}}

.brand-block {{
  display: flex;
  align-items: center;
  gap: 10px;
}}

.brand-mark {{
  height: 32px;
  width: auto;
}}

.brand-wordmark {{
  height: 24px;
  width: auto;
}}

.top-nav-links a {{
  margin: 0;
  color: var(--wt-ink);
  font-weight: 600;
}}

.top-nav-links {{
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
}}

.content-shell {{
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 16px;
  padding: 16px 24px 32px 24px;
  position: relative;
}}

.sidebar {{
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  height: fit-content;
  transition: all 0.2s ease;
  overflow: visible;
}}

.sidebar-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}}

.sidebar-toggle {{
  background: var(--wt-soft-blue);
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 4px 8px;
  font-weight: 600;
  cursor: pointer;
}}

.sidebar-section {{
  display: flex;
  flex-direction: column;
  gap: 16px;
}}

.sidebar-section .filter-label {{
  margin-top: 14px;
}}

.sidebar-section .filter-label:first-child {{
  margin-top: 0;
}}

.filter-group {{
  display: flex;
  flex-direction: column;
  gap: 6px;
}}

.filter-group {{
  display: flex;
  flex-direction: column;
  gap: 6px;
}}

.filter-group {{
  display: flex;
  flex-direction: column;
  gap: 6px;
}}

.filter-group {{
  display: flex;
  flex-direction: column;
  gap: 6px;
}}

.sidebar-section > *:not(:first-child) {{
  margin-top: 8px;
}}

.DateInput_input {{
  font-size: 10px;
  padding: 4px 6px;
  width: 100%;
  min-width: 0;
}}

.DateRangePickerInput {{
  gap: 4px;
  width: 100%;
  max-width: 100%;
  display: flex;
  box-sizing: border-box;
  flex-wrap: wrap;
}}

.DateInput {{
  width: 100%;
  flex: 1 1 0;
  min-width: 0;
}}

.DateRangePicker {{
  width: 100%;
  max-width: 100%;
}}

.DateRangePicker_picker {{
  z-index: 20;
}}

.sidebar-title {{
  font-weight: 700;
  font-size: 16px;
  margin-bottom: 10px;
  color: var(--wt-blue);
}}

.sidebar-note {{ color: var(--wt-gray); font-size: 13px; }}

.page-container {{
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  min-height: 70vh;
}}

.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(4, minmax(120px, 1fr));
  gap: 12px;
}}

.kpi-card {{
  background: var(--wt-soft-lavender);
  border-radius: 10px;
  padding: 12px;
}}

.kpi-label {{ font-size: 12px; color: #374151; }}
.kpi-value {{ font-size: 20px; font-weight: 700; color: var(--wt-blue); }}

.section {{ margin-top: 24px; }}

.section-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}}

.section-actions button {{
  background: var(--wt-soft-blue);
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 6px 12px;
  font-weight: 600;
  color: var(--wt-ink);
  cursor: pointer;
}}

.filters-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 12px;
}}

.filter-label {{
  font-size: 13px;
  font-weight: 600;
  color: var(--wt-gray);
  margin-bottom: 4px;
}}

.sidebar-section .filter-label {{
  margin-top: 12px;
}}

.sidebar-section .filter-label:first-child {{
  margin-top: 0;
}}

.sidebar-section .Select,
.sidebar-section .DateRangePicker,
.sidebar-section .rc-slider {{
  margin-bottom: 12px;
}}

.rc-slider-mark-text {{
  font-size: 11px;
  color: var(--wt-gray);
}}

.review-detail-card {{
  margin-top: 12px;
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
}}

.review-detail-title {{
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--wt-ink);
}}

.review-detail-meta {{
  font-size: 12px;
  color: var(--wt-gray);
  margin-bottom: 8px;
}}

.review-detail-text {{
  font-size: 14px;
  color: var(--wt-ink);
  margin-bottom: 8px;
}}

.review-detail-link {{
  font-size: 12px;
  font-weight: 600;
}}

.review-detail-empty {{
  font-size: 13px;
  color: var(--wt-gray);
}}


.DateRangePickerInput__withBorder {{
  width: 100%;
  max-width: 100%;
}}

.DateRangePickerInput_arrow {{
  padding: 0 4px;
}}

.Select-control,
.Select-placeholder,
.Select-input,
.Select-value-label {{
  font-size: 13px;
}}

.chart-card {{
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 8px;
}}

.chart-title {{
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--wt-blue);
}}
"""


def ensure_theme_css() -> None:
    assets_css = ROOT / "assets" / "theme.css"
    if not assets_css.exists() or assets_css.read_text() != THEME_CSS:
        assets_css.write_text(THEME_CSS)
