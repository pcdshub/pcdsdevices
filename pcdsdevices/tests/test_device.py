import pytest
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.device import Kind
from ophyd.positioner import SoftPositioner
from ophyd.signal import Signal

from ..device import GroupDevice
from ..device import InterfaceComponent as ICpt
from ..device import InterfaceDevice
from ..device import ObjectComponent as OCpt
from ..device import UnrelatedComponent as UCpt
from ..device import UpdateComponent as UpCpt
from ..device import to_interface


class Basic(Device):
    apple = UCpt(Device)
    sauce = UCpt(Device)
    empty = Cpt(Device, ':EMPTY')

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class Complex(Device):
    one = UCpt(Basic)
    two = UCpt(Basic)
    tomayto = Cpt(Device, ':TOMAHTO')

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


def test_basic_class_good():
    obj = Basic('GLASS', name='jar', apple_prefix='APPLE',
                sauce_prefix='SAUCE')
    assert obj.prefix == 'GLASS'
    assert obj.apple.prefix == 'APPLE'
    assert obj.sauce.prefix == 'SAUCE'
    assert obj.empty.prefix == 'GLASS:EMPTY'


def test_basic_class_bad():
    with pytest.raises(ValueError):
        Basic('GLASS', name='jar', apple_prefix='APPLE')


def test_complex_class():
    obj = Complex('APPT', name='apt',
                  one_prefix='UNO',
                  one_apple_prefix='APPLE:01',
                  one_sauce_prefix='SAUCE:01',
                  two_prefix='DOS',
                  two_apple_prefix='APPLE:02',
                  two_sauce_prefix='SAUCE:02')

    assert obj.prefix == 'APPT'
    assert obj.one.prefix == 'UNO'
    assert obj.one.apple.prefix == 'APPLE:01'
    assert obj.one.sauce.prefix == 'SAUCE:01'
    assert obj.one.empty.prefix == 'UNO:EMPTY'
    assert obj.two.prefix == 'DOS'
    assert obj.two.apple.prefix == 'APPLE:02'
    assert obj.two.sauce.prefix == 'SAUCE:02'
    assert obj.two.empty.prefix == 'DOS:EMPTY'
    assert obj.tomayto.prefix == 'APPT:TOMAHTO'


def test_ocpt():
    sig_one = Signal(name='one', kind=Kind.config)
    sig_two = Signal(name='two')

    class ObjectDevice(Device):
        one = OCpt(sig_one, kind=Kind.hinted)
        two = OCpt(sig_two)

    assert sig_one.kind == Kind.config
    obj = ObjectDevice('prefix', name='name')
    assert 'one' in obj.component_names
    assert obj.one.kind == Kind.hinted
    obj.one.put(5)
    assert sig_one.get() == 5
    obj.two.put(3)
    assert sig_two.get() == 3


class TwoSignal(InterfaceDevice):
    sig_one = ICpt(Signal, kind=Kind.hinted)
    sig_two = ICpt(Signal)


class SomeDevice(Device):
    some = Cpt(Signal)
    where = Cpt(Signal)


def test_interface_basic():
    one = Signal(name='one', kind=Kind.config)
    two = Signal(name='two')

    assert one.kind == Kind.config
    two_sig = TwoSignal('prefix', name='name', sig_one=one, sig_two=two)
    assert one.kind == Kind.hinted
    two_sig.sig_one.put(1)
    two_sig.sig_two.put(2)

    assert one.get() == 1
    assert two.get() == 2


def test_to_interface():
    SomeDeviceInterface = to_interface(SomeDevice)
    some = Signal(name='some')
    where = Signal(name='where')

    sdi = SomeDeviceInterface('', name='sdi', some=some, where=where)
    sd = SomeDevice('', name='sd')

    sdi.some.put(1)
    sdi.where.put(2)
    sd.some.put(3)
    sd.where.put(4)

    assert some.get() == 1
    assert where.get() == 2


def test_update_component():
    # Make some classes
    class PrefixSignal(Signal):
        def __init__(self, prefix, **kwargs):
            self.prefix = prefix
            super().__init__(**kwargs)

    class PrefixSignalAlt(PrefixSignal):
        ...

    class One(Device):
        cpt = Cpt(PrefixSignal, 'CPT', kind='normal')
        fcpt = FCpt(PrefixSignal, '{_fcpt}', kind='normal')

        def __init__(self, prefix, fcpt, **kwargs):
            self._fcpt = fcpt
            super().__init__(prefix, **kwargs)

    class Two(One):
        cpt = UpCpt(cls=PrefixSignalAlt, kind='hinted')

    class Three(Two):
        fcpt = UpCpt(suffix='fcpt{_fcpt}')

    # Check that the modifications were correct
    assert Two.cpt.cls is PrefixSignalAlt
    assert Two.cpt.kind == Kind.hinted
    assert Two.fcpt.suffix == '{_fcpt}'

    assert Three.cpt.cls is PrefixSignalAlt
    assert Three.cpt.kind == Kind.hinted
    assert Three.fcpt.suffix == 'fcpt{_fcpt}'

    # Let's make a device
    three = Three('DEVICE:', '42', name='three')

    # Check the names, kinds, and pvnames
    assert three.cpt.prefix == 'DEVICE:CPT'
    assert three.cpt.name == 'three_cpt'
    assert three.cpt.kind == Kind.hinted
    assert three.fcpt.prefix == 'fcpt42'
    assert three.fcpt.name == 'three_fcpt'
    assert three.fcpt.kind == Kind.normal


class BadStager(Device):
    dev = Cpt(Device, ':DEV')

    def stage(self):
        raise RuntimeError('This should not have been called!')


class BasicGroup(GroupDevice):
    one = Cpt(Device, ':BASIC')
    two = Cpt(Device, ':COMPLEX')
    bad = Cpt(BadStager, ':BAD')


def test_group_device_basic():
    """
    Make sure group device basic features work.
    """
    group = BasicGroup('GROUP', name='group')
    assert group.one.parent is None
    assert group.two.parent is None
    assert group.two.biological_parent is group
    assert group.bad.dev.parent is group.bad
    assert group.one not in group.stage()
    assert group.two not in group.unstage()


def test_group_device_partial():
    """
    We should call stage this time, but not on BadStager
    """
    class StageGroupPartial(BasicGroup):
        stage_group = [BasicGroup.one, BasicGroup.two]

    group = StageGroupPartial('PARTIAL', name='partial')
    assert group.one in group.stage()
    assert group.two in group.unstage()


def test_group_device_class_errors():
    """
    Various issues that should be caught when we define a class.
    """
    # If we're a positioner, we must define a stage_group
    with pytest.raises(TypeError):
        class PosGroup(SoftPositioner, GroupDevice):
            pass

    # stage_group must have only components in it
    with pytest.raises(TypeError):
        class MessyGroup(BasicGroup):
            stage_group = [BasicGroup.one, 'cats']

    # stage_group targets should not be overriden in subclass except by Cpt
    with pytest.raises(TypeError):
        class OverrideGroup(BasicGroup):
            one = None
            stage_group = [BasicGroup.one, BasicGroup.two]
