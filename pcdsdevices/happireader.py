#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read the beamline database and construct objects
"""
import logging

import happi

import pcdsdevices

logger = logging.getLogger(__name__)
_client = None


def read_happi(client=None):
    """
    Connect to the happi database and return a list of all devices.

    Parameters
    ----------
    client : happi.Client, optional
        Instance of Client to use for the read. Included as a parameter to be
        substituted with the mock client for testing. If not provided, we'll
        use the default client.

    Returns
    -------
    devices : list of happi.Device
    """
    if client is None:
        global _client
        if _client is None:
            logger.info("Instantiating happi client")
            _client = happi.Client()
        client = _client
    logger.info("Requesting all devices from happi client of class %s",
                type(client))
    return client.all_devices


def construct_device(happi_object, device_class=None):
    """
    Create a functional device from the information stored in a happi device.

    Parameters
    ----------
    happi_object : happi.Device

    device_class : class, optional
        Class to instantiate with given happi information. If no class is given
        one will be selected using the :func:`.pick_class` function

    Returns
    -------
    device : ophyd.Device
    """
    info = {}
    #Gather information from device
    for entry in happi_object.info_names:
        try:
            info[entry] = getattr(happi_object, entry)
        except AttributeError:
            pass
    logger.debug("Extracted info dictionary from happi: %s", info)
    #Class selection
    if not device_class:
        device_type = happi_object.__class__.__name__
        device_class = pick_class(device_type, info)
    #Instantiate device with information
    return device_class(db_info=info, **info)


def pick_class(base, info):
    """
    Given information from happi, determine which device subclass to use. add
    kwargs to info if necessary.

    Parameters
    ----------
    base : str
        A string representation of the device class name from happi. These
        should always match an available class in module.
    info : dict
        A dictionary mapping of happi entry info to stored value. Eventually
        this will be passed as kwargs to instantiate the device object. This
        may be mutated in this function to pass additional args.
    """
    clsname = base
    if base == "PulsePicker":
        if info["beamline"] in ("XCS", "XPP"):
            clsname += "Pink"
    # TODO find ioc pvs as needed and add to info
    # probably scrape iocmanager and iocdata
    return getattr(pcdsdevices, clsname)
