import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRANDBOOK = ROOT / "Brandbook" / "brandbook.slim.json"


def get_dataviz_palette() -> list[str]:
    try:
        data = json.loads(BRANDBOOK.read_text())
        palette = data.get("data_viz_palette", [])
        return palette if palette else _fallback_palette()
    except Exception:
        return _fallback_palette()


def _fallback_palette() -> list[str]:
    return [
        "#111827",
        "#1c417d",
        "#6b7280",
        "#e3f5fe",
        "#790000",
        "#5757dd",
        "#5a8fd0",
        "#1da1f2",
        "#000000",
    ]
