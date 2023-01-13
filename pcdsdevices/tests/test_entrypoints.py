from __future__ import annotations

import importlib.metadata
import pathlib

import pytest
import typhos

from .. import ui


@pytest.fixture(scope="session")
def entry_points() -> dict[str, importlib.metadata.EntryPoints]:
    return importlib.metadata.entry_points()


def test_typhos_entrypoint(entry_points):
    assert "typhos.ui" in entry_points, "No typhos entrypoints"
    values = {entry.value for entry in entry_points["typhos.ui"]}
    assert "pcdsdevices.ui:path" in values


def test_typhos_paths():
    ui_directory = pathlib.Path(ui.__file__).resolve().parent
    assert ui_directory in typhos.utils.DISPLAY_PATHS


def test_happi_entrypoint(entry_points):
    assert "happi.containers" in entry_points, "No happi entrypoints"
    values = {entry.value for entry in entry_points["happi.containers"]}
    assert "pcdsdevices.happi.containers" in values
