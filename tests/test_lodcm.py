#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest.mock import Mock
import pytest

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.epics.lodcm import LODCM


@pytest.fixture(scope='function')
@using_fake_epics_pv
def lodcm():
    lom = LODCM('FAKE:LOM', name='fake_lom', main_line='MAIN')
    lom.h1n.state._read_pv.put('OUT')
    lom.h1n.state._read_pv.enum_strs = ['OUT', 'C', 'Si']
    lom.h2n.state._read_pv.put('C')
    lom.h2n.state._read_pv.enum_strs = ['C', 'Si']
    lom.yag.state._read_pv.put('OUT')
    lom.yag.state._read_pv.enum_strs = ['OUT', 'YAG', 'SLIT1', 'SLIT2',
                                        'SLIT3']
    lom.dectris.state._read_pv.put('OUT')
    lom.dectris.state._read_pv.enum_strs = ['OUT', 'DECTRIS', 'SLIT1',
                                            'SLIT2', 'SLIT3', 'OUTLOW']
    lom.diode.state._read_pv.put('OUT')
    lom.diode.state._read_pv.enum_strs = ['OUT', 'IN']
    lom.foil.state._read_pv.put('OUT')
    lom.foil.state._read_pv.enum_strs = ['OUT']
    return lom


# Call all light interface items and hope for the best
@using_fake_epics_pv
def test_destination(lodcm):
    dest = lodcm.destination
    assert isinstance(dest, list)
    for d in dest:
        assert isinstance(d, str)


@using_fake_epics_pv
def test_branches(lodcm):
    branches = lodcm.branches
    assert isinstance(branches, list)
    for b in branches:
        assert isinstance(b, str)


@using_fake_epics_pv
def test_inserted(lodcm):
    inserted = lodcm.inserted
    assert isinstance(inserted, bool)


@using_fake_epics_pv
def test_removed(lodcm):
    removed = lodcm.removed
    assert isinstance(removed, bool)


@using_fake_epics_pv
def test_remove(lodcm):
    lodcm.remove()


@using_fake_epics_pv
def test_subscribe(lodcm):
    cb = Mock()
    lodcm.subscribe(cb, run=False)
    assert not cb.called
    # Change destination from main to mono
    lodcm.h1n.state._read_pv.put('C')
    assert cb.called
