#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read the beamline database and construct objects
"""
from importlib import import_module
import happi


def read_happi():
    """
    Connect to the happi database and return a list of all devices.

    Returns
    -------
    devices : list of happi.Device
    """
    client = happi.Client()
    return client.all_devices


def construct_device(happi_object):
    """
    Create a functional device from the information stored in a happi device.

    Parameters
    ----------
    happi_object : happi.Device

    Returns
    -------
    device : ophyd.Device
    """
    device_type = happi_object.__class__.__name__
    module_name = device_type.lower()
    module = import_module(".." + module_name, __name__)
    info = {}
    for entry in happi_object.info_names:
        try:
            info[entry] = getattr(happi_object, entry)
        except AttributeError:
            pass
    cls = pick_class(device_type, module, info)
    return cls(**info)


def pick_class(base, module, info):
    """
    Given information from happi, determine which device subclass to use. add
    kwargs to info if necessary.

    Parameters
    ----------
    base : str
        A string representation of the device class name from happi. These
        should always match an available class in module.
    module : module
        A valid submodule in this package. This must contain a class with the
        same name as base, and may optionally contain subclasses that are all
        prefixed with base.
    info : dict
        A dictionary mapping of happi entry info to stored value. Eventually
        this will be passed as kwargs to instantiate the device object. This
        may be mutated in this function to pass additional args.
    """
    # TODO pick subclass based on context for pulsepicker
    # TODO find ioc pvs as needed and add to info
    return getattr(module, base)
