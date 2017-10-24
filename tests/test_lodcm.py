#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.epics.lodcm import LODCM


@pytest.fixture(scope='function')
def lodcm():
    lom = LODCM('FAKE:LOM', name='fake_lom', main_line='MAIN')
    lom.h1n_state.value = 'OUT'
    lom.h2n_state.value = 'OUT'
    lom.yag_state.value = 'OUT'
    lom.dectris_state.value = 'OUT'
    lom.diode_state.value = 'OUT'
    lom.foil_state.value = 'OUT'


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
