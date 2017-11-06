#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PCDS Ophyd Device overrides.
"""
from collections import OrderedDict

import ophyd
from .interface import LightInterface

from .component import Component
VALID_OPHYD_KWARGS = ("name", "parent", "prefix", "read_attrs",
                      "configuration_attrs")

LIGHTPATH_KWARGS = ('beamline', 'z')

class Device(ophyd.Device, metaclass=LightInterface):
    """
    Subclass of ophyd.Device that soaks up and stores information from the
    happi device database.
    """
    transmission = 0.0
    def __init__(self, prefix, **kwargs):
        db_info = kwargs.pop("db_info", None)
        #Create mandatory lightpath attributes from Happi Information
        #Placing None as default
        for key in LIGHTPATH_KWARGS:
            setattr(self, key, kwargs.pop(key, None))
        #Store happi information if provided 
        if db_info:
            self.db = HappiData(db_info)
            for key in list(kwargs.keys()):
                # Remove keys in kwargs if they were from the happi import but
                # they cannot be passed to ophyd.Device
                if key in db_info and key not in VALID_OPHYD_KWARGS:
                    kwargs.pop(key)
        super().__init__(prefix, **kwargs)

    @property
    def removed(self):
        """
        Report if the device is currently removed from the beam
        """
        raise NotImplementedError

    @property
    def inserted(self):
        """
        Report if the device is currently inserted into the beam
        """
        raise NotImplementedError


class HappiData:
    """
    Class to hold arbitrary happi data

    The information is stored as attribute with the name corresponding to the
    key given in the input dictionary. Dictionary-like access is still possible
    by using :attr:`.db_info`
    """
    def __init__(self, db_info):
        """
        Parameters
        ----------
        db_info: dict
            Mapping from happi keyword to value
        """
        self.info = db_info
        for entry, value in db_info.items():
            setattr(self, entry, value)

class DynamicDeviceComponent(ophyd.DynamicDeviceComponent):
    """
    Overrides for DynamicDeviceComponent so it uses pcds Device and Component.
    """

    def create_attr(self, attr_name):
        cls, suffix, kwargs = self.defn[attr_name]
        inst = Component(cls, suffix, **kwargs)
        inst.attr = attr_name
        return inst

    def create_component(self, instance):
        """Create a component for the instance"""
        clsname = self.clsname
        if clsname is None:
            # make up a class name based on the instance's class name
            clsname = ''.join((instance.__class__.__name__,
                               self.attr.capitalize()))

            # TODO: and if the attribute has any underscores, convert that to
            #       camelcase

        docstring = self.doc
        if docstring is None:
            docstring = '{} sub-device'.format(clsname)

        clsdict = OrderedDict(__doc__=docstring)

        for attr in self.defn.keys():
            clsdict[attr] = self.create_attr(attr)

        attrs = set(self.defn.keys())
        inst_read = set(instance.read_attrs)
        if self.attr in inst_read:
            # if the sub-device is in the read list, then add all attrs
            read_attrs = attrs
        else:
            # otherwise, only add the attributes that exist in the sub-device
            # to the read_attrs list
            read_attrs = inst_read.intersection(attrs)

        cls = type(clsname, (Device, ), clsdict)
        return cls(instance.prefix, read_attrs=list(read_attrs),
                   name='{}_{}'.format(instance.name, self.attr),
                   parent=instance)
