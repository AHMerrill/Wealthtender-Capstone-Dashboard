from dashboard.branding import DATA_VIZ_PALETTE


def get_dataviz_palette() -> list[str]:
    """Return a copy so callers can't corrupt the global palette."""
    return list(DATA_VIZ_PALETTE)
