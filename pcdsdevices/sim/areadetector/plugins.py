#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for ophyd and pcdsdevices plugins to be used in simulated detectors.
"""
##########
# Module #
##########
from .base import ad_group
from ..signal import Signal
from ..component import (Component, DynamicDeviceComponent)
from ...epics.areadetector import plugins

class PluginBase(plugins.PluginBase):
    """
    PluginBase but with components initialized to be empty signals.
    """
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
    width = Component(Signal, value=0)
    height = Component(Signal, value=0)
    depth = Component(Signal, value=0)
    array_size = DynamicDeviceComponent(ad_group(
        Signal, (('height'), ('width'), ('depth')), value=0), 
                                        doc='The array size')
    bayer_pattern = Component(Signal, value=0)
    blocking_callbacks = Component(Signal, value=0)
    color_mode = Component(Signal, value=0)
    data_type = Component(Signal, value=0)
    dim0_sa = Component(Signal, value=0)
    dim1_sa = Component(Signal, value=0)
    dim2_sa = Component(Signal, value=0)
    dim_sa = DynamicDeviceComponent(ad_group(
        Signal, (('dim0'), ('dim1'), ('dim2')), value=0),
                                    doc='Dimension sub-arrays')
    dimensions = Component(Signal, value=0)
    dropped_arrays = Component(Signal, value=0)
    enable = Component(Signal, value=0)
    min_callback_time = Component(Signal, value=0)
    nd_array_address = Component(Signal, value=0)
    nd_array_port = Component(Signal, value=0)
    ndimensions = Component(Signal, value=0)
    plugin_type = Component(Signal, value=0)
    queue_free = Component(Signal, value=0)
    queue_free_low = Component(Signal, value=0)
    queue_size = Component(Signal, value=0)
    queue_use = Component(Signal, value=0)
    queue_use_high = Component(Signal, value=0)
    queue_use_hihi = Component(Signal, value=0)
    time_stamp = Component(Signal, value=0)
    unique_id = Component(Signal, value=0)


class StatsPlugin(plugins.StatsPlugin, PluginBase):
    """
    StatsPlugin but with components instantiated to be empty signals.
    """
    plugin_type = Component(Signal, value='NDPluginStats')
    bgd_width = Component(Signal, value=0)
    centroid_threshold = Component(Signal, value=0)
    centroid = DynamicDeviceComponent(ad_group(Signal, (('x'), ('y')), value=0),
                                      doc='The centroid XY')
    compute_centroid = Component(Signal, value=0)
    compute_histogram = Component(Signal, value=0)
    compute_profiles = Component(Signal, value=0)
    compute_statistics = Component(Signal, value=0)
    cursor = DynamicDeviceComponent(ad_group(Signal, (('x'), ('y')), value=0),
                                    doc='The cursor XY')
    hist_entropy = Component(Signal, value=0)
    hist_max = Component(Signal, value=0)
    hist_min = Component(Signal, value=0)
    hist_size = Component(Signal, value=0)
    histogram = Component(Signal, value=0)
    max_size = DynamicDeviceComponent(ad_group(Signal, (('x'), ('y')), value=0),
                                      doc='The maximum size in XY')
    max_value = Component(Signal, value=0)
    max_xy = DynamicDeviceComponent(ad_group(Signal, (('x'), ('y')), value=0),
                                    doc='Maximum in XY')
    mean_value = Component(Signal, value=0)
    min_value = Component(Signal, value=0)
    min_xy = DynamicDeviceComponent(ad_group(Signal, (('x'), ('y')), value=0), 
                                    doc='Minimum in XY')
    net = Component(Signal, value=0)
    profile_average = DynamicDeviceComponent(ad_group(
        Signal, (('x'), ('y')), value=0), doc='Profile average in XY')
    profile_centroid = DynamicDeviceComponent(ad_group(
        Signal, (('x'), ('y')), value=0), doc='Profile centroid in XY')
    profile_cursor = DynamicDeviceComponent(ad_group(
        Signal, (('x'), ('y')), value=0), doc='Profile cursor in XY')
    profile_size = DynamicDeviceComponent(ad_group(
        Signal, (('x'), ('y')), value=0), doc='Profile size in XY')
    profile_threshold = DynamicDeviceComponent(ad_group(
        Signal, (('x'), ('y')), value=0), doc='Profile threshold in XY')
    set_xhopr = Component(Signal, value=0)
    set_yhopr = Component(Signal, value=0)
    sigma_xy = Component(Signal, value=0)
    sigma_x = Component(Signal, value=0)
    sigma_y = Component(Signal, value=0)
    sigma = Component(Signal, value=0)
    ts_acquiring = Component(Signal, value=0)
    ts_centroid = DynamicDeviceComponent(ad_group(
        Signal, (('x'), ('y')), value=0), doc='Time series centroid in XY')
    ts_control = Component(Signal, value=0)
    ts_current_point = Component(Signal, value=0)
    ts_max_value = Component(Signal, value=0)
    ts_max = DynamicDeviceComponent(ad_group(Signal, (('x'), ('y')), value=0), 
                                    doc='Time series maximum in XY')
    ts_mean_value = Component(Signal, value=0)
    ts_min_value = Component(Signal, value=0)
    ts_min = DynamicDeviceComponent(ad_group(Signal, (('x'), ('y')), value=0), 
                                    doc='Time series minimum in XY')
    ts_net = Component(Signal, value=0)
    ts_num_points = Component(Signal, value=0)
    ts_read = Component(Signal, value=0)
    ts_sigma = Component(Signal, value=0)
    ts_sigma_x = Component(Signal, value=0)
    ts_sigma_xy = Component(Signal, value=0)
    ts_sigma_y = Component(Signal, value=0)
    ts_total = Component(Signal, value=0)
    total = Component(Signal, value=0)
