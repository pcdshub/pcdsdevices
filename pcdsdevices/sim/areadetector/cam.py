#!/usr/bin/env python
# -*- coding: utf-8 -*-
##########
# Module #
##########
from .base import ad_group
from ..signal import Signal
from ..component import (Component, DynamicDeviceComponent)
from ...epics.areadetector import cam


class CamBase(cam.CamBase):
    # Shared among all cams and plugins
    array_counter = Component(Signal, value=0)
    array_rate = Component(Signal, value=0)
    asyn_io = Component(Signal, value=0)

    nd_attributes_file = Component(Signal, value=0)
    pool_alloc_buffers = Component(Signal, value=0)
    pool_free_buffers = Component(Signal, value=0)
    pool_max_buffers = Component(Signal, value=0)
    pool_max_mem = Component(Signal, value=0)
    pool_used_buffers = Component(Signal, value=0)
    pool_used_mem = Component(Signal, value=0)
    port_name = Component(Signal, value=0)

    # Cam-specific
    acquire = Component(Signal, value=0)
    acquire_period = Component(Signal, value=0)
    acquire_time = Component(Signal, value=0)

    array_callbacks = Component(Signal, value=0)
    array_size = DynamicDeviceComponent(ad_group(Signal,
                              (('array_size_x'),
                               ('array_size_y'),
                               ('array_size_z')), value=0),
                     doc='Size of the array in the XYZ dimensions')

    array_size_bytes = Component(Signal, value=0)
    bin_x = Component(Signal, value=0)
    bin_y = Component(Signal, value=0)
    color_mode = Component(Signal, value=0)
    data_type = Component(Signal, value=0)
    detector_state = Component(Signal, value=0)
    frame_type = Component(Signal, value=0)
    gain = Component(Signal, value=0)

    image_mode = Component(Signal, value=0)
    manufacturer = Component(Signal, value=0)

    max_size = DynamicDeviceComponent(ad_group(Signal,
                            (('max_size_x'),
                             ('max_size_y')), value=0),
                   doc='Maximum sensor size in the XY directions')

    min_x = Component(Signal, value=0)
    min_y = Component(Signal, value=0)
    model = Component(Signal, value=0)

    num_exposures = Component(Signal, value=0)
    num_exposures_counter = Component(Signal, value=0)
    num_images = Component(Signal, value=0)
    num_images_counter = Component(Signal, value=0)

    read_status = Component(Signal, value=0)
    reverse = DynamicDeviceComponent(ad_group(Signal,
                           (('reverse_x'),
                            ('reverse_y')), value=0))

    shutter_close_delay = Component(Signal, value=0)
    shutter_close_epics = Component(Signal, value=0)
    shutter_control = Component(Signal, value=0)
    shutter_control_epics = Component(Signal, value=0)
    shutter_fanout = Component(Signal, value=0)
    shutter_mode = Component(Signal, value=0)
    shutter_open_delay = Component(Signal, value=0)
    shutter_open_epics = Component(Signal, value=0)
    shutter_status_epics = Component(Signal, value=0)
    shutter_status = Component(Signal, value=0)

    size = DynamicDeviceComponent(ad_group(Signal,
                        (('size_x'),
                         ('size_y')), value=0))

    status_message = Component(Signal, value=0)
    string_from_server = Component(Signal, value=0)
    string_to_server = Component(Signal, value=0)
    temperature = Component(Signal, value=0)
    temperature_actual = Component(Signal, value=0)
    time_remaining = Component(Signal, value=0)
    trigger_mode = Component(Signal, value=0)


class PulnixCam(cam.PulnixCam, CamBase):
    pass
