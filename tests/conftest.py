import os
import shutil
import warnings
from pathlib import Path

import pytest
from ophyd.sim import (FakeEpicsSignal, FakeEpicsSignalRO, fake_device_cache,
                       make_fake_device)
from pcdsdevices.attenuator import (MAX_FILTERS, Attenuator, _att3_classes,
                                    _att_classes)
from pcdsdevices.mv_interface import setup_preset_paths
from pcdsdevices.signal import PytmcSignal
from pytmc.pragmas import normalize_io

# Signal.put warning is a testing artifact.
# FakeEpicsSignal needs an update, but I don't have time today
# Needs to not pass tons of kwargs up to Signal.put
warnings.filterwarnings('ignore',
                        message='Signal.put no longer takes keyword arguments')


# Make sure an acceptable fake class is set for PytmcSignal
def FakePytmcSignal(prefix, *, io, **kwargs):
    norm = normalize_io(io)
    if norm == 'output':
        return FakeEpicsSignal(prefix, **kwargs)
    elif norm == 'input':
        return FakeEpicsSignalRO(prefix, **kwargs)
    else:
        # Give us the normal error message
        return PytmcSignal(prefix, io=io, **kwargs)


fake_device_cache[PytmcSignal] = FakePytmcSignal

for name, cls in _att_classes.items():
    _att_classes[name] = make_fake_device(cls)

for name, cls in _att3_classes.items():
    _att3_classes[name] = make_fake_device(cls)


# Used in multiple test files
@pytest.fixture(scope='function')
def fake_att():
    att = Attenuator('TST:ATT', MAX_FILTERS-1, name='test_att')
    att.readback.sim_put(1)
    att.done.sim_put(0)
    att.calcpend.sim_put(0)
    for i, filt in enumerate(att.filters):
        filt.state.put('OUT')
        filt.thickness.put(2*i)
    return att


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
