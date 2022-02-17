# Hacky ophyd and pyepics hotfixes
import epics.ca
from ophyd.device import Device

from ._version import get_versions
from .registry import device_registry  # NOQA


def __contains__(self, value):
    return value in self._OphydAttrList__internal_list()


Device.OphydAttrList.__contains__ = __contains__
del Device
del __contains__


# Fix handling of often corrupt IMS PN fields
def make_new_bts(old_bts):
    def new_bts(st1):
        try:
            return old_bts(st1)
        except UnicodeDecodeError:
            return st1.decode("utf-8", "ignore")
    return new_bts


try:
    epics.ca.BYTES2STR = make_new_bts(epics.ca.BYTES2STR)
    epics.ca.bytes2str = make_new_bts(epics.ca.bytes2str)
except AttributeError:
    pass

del epics
del make_new_bts

__version__ = get_versions()['version']
del get_versions
