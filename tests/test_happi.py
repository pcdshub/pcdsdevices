#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
try:
    import happi
    from happi.tests import MockClient
    from devices import happireader
    has_happi = True
except ImportError:
    has_happi = False

requires_happi = pytest.mark.skipif(not has_happi,
                                    reason="Missing happi or mongomock")


@pytest.fixture(scope="function")
def mockclient():
    client = MockClient()
    pp = client.create_device("PulsePicker", name="xpp_pp",
                              prefix="XPP:SB2:MMS:29", states="XPP:SB2:PP:Y",
                              beamline="XPP", z=785.574, stand="SB2")
    valve = client.create_device("GateValve", name="xpp_sb2_valve",
                                 prefix="XPP:SB2:VGC:01", mps="placeholder",
                                 beamline="XPP", z=784.132, stand="SB2")
    pp.save()
    valve.save()
    return client


@requires_happi
def test_read_happi_basic():
    with pytest.raises(happi.errors.DatabaseError):
        happireader.read_happi()


@requires_happi
def test_read_happi(mockclient):
    all_devices = happireader.read_happi(mockclient)
    assert(isinstance(all_devices, list))
    for dev in all_devices:
        assert(isinstance(dev, happi.Device))


@requires_happi
def test_construct_device(mockclient):
    all_devices = happireader.read_happi(mockclient)
    for dev in all_devices:
        happireader.construct_device(dev)
