from typhos.utils import DISPLAY_PATHS

from ..ui import path


def test_ui_entry_point():
    assert path in DISPLAY_PATHS


def test_ui_files_in_distribution():
    assert len(list(path.glob('*.ui'))) > 0
