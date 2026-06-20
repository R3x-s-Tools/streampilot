import pytest


def test_main_window_imports_when_qt_available():
    pytest.importorskip("PySide6")

    try:
        from ui.main_window import MainWindow
    except ImportError as exc:
        if "libEGL.so.1" in str(exc):
            pytest.skip("Qt GUI libraries are not available in this CI runner.")
        raise

    assert MainWindow is not None