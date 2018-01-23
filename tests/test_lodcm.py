#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest.mock import Mock
import pytest

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.lodcm import LODCM

from .conftest import attr_wait_true


def fake_lodcm():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    lom = LODCM('FAKE:LOM', name='fake_lom', main_line='MAIN')
    lom.h1n.state._read_pv.put('OUT')
    lom.h1n.state._read_pv.enum_strs = ['OUT', 'C', 'Si']
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
    lom.wait_for_connection()
    return lom


# Call all light interface items and hope for the best
@using_fake_epics_pv
def test_destination():
    lodcm = fake_lodcm()
    dest = lodcm.destination
    assert isinstance(dest, list)
    for d in dest:
        assert isinstance(d, str)


@using_fake_epics_pv
def test_branches():
    lodcm = fake_lodcm()
    branches = lodcm.branches
    assert isinstance(branches, list)
    for b in branches:
        assert isinstance(b, str)


@using_fake_epics_pv
def test_inserted():
    lodcm = fake_lodcm()
    inserted = lodcm.inserted
    assert isinstance(inserted, bool)


@using_fake_epics_pv
def test_removed():
    lodcm = fake_lodcm()
    removed = lodcm.removed
    assert isinstance(removed, bool)


@using_fake_epics_pv
def test_remove():
    lodcm = fake_lodcm()
    lodcm.remove()


@using_fake_epics_pv
def test_subscribe():
    lodcm = fake_lodcm()
    cb = Mock()
    lodcm.subscribe(cb, event_type=lodcm.SUB_STATE, run=False)
    assert not cb.called
    # Change destination from main to mono and main
    lodcm.h1n.state._read_pv.put('C')
    attr_wait_true(cb, 'called')
    assert cb.called
