from pathlib import Path
from pcdsdevices.interface import setup_preset_paths

import os
import pytest
import shutil
import warnings


# Signal.put warning is a testing artifact.
# FakeEpicsSignal needs an update, but I don't have time today
# Needs to not pass tons of kwargs up to Signal.put
warnings.filterwarnings('ignore',
                        message='Signal.put no longer takes keyword arguments')


@pytest.fixture(scope='function')
def presets():
    folder_obj = Path(__file__).parent / 'test_presets'
    folder = str(folder_obj)
    if folder_obj.exists():
        shutil.rmtree(folder)
    hutch = folder + '/hutch'
    user = folder + '/user'
    os.makedirs(hutch)
    os.makedirs(user)
    setup_preset_paths(hutch=hutch, user=user)
    yield
    setup_preset_paths()
    shutil.rmtree(folder)
