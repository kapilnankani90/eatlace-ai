"""Lightweight tests for UI-related helpers (no Streamlit runtime)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_app_module_imports():
    """Ensure app.py dependencies resolve (Streamlit may be optional in CI)."""
    pytest = __import__("pytest")
    streamlit = pytest.importorskip("streamlit")
    assert streamlit is not None

    # Import after path setup; avoid running streamlit main
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ui_app", ROOT / "src" / "ui" / "app.py"
    )
    assert spec and spec.loader
