#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for ophyd and pcdsdevices plugins to be used in simulated detectors.
"""
###############
# Third Party #
###############
import numpy as np

##########
# Module #
##########
from .base import ad_group
from ..signal import FakeSignal
from ..component import (Component, DynamicDeviceComponent)
from ...epics.areadetector import plugins

class PluginBase(plugins.PluginBase):
    """
    PluginBase but with components initialized to be empty signals.
    """
    array_counter = Component(FakeSignal, value=0)
    array_rate = Component(FakeSignal, value=0)
    asyn_io = Component(FakeSignal, value=0)
    nd_attributes_file = Component(FakeSignal, value=0)
    pool_alloc_buffers = Component(FakeSignal, value=0)
    pool_free_buffers = Component(FakeSignal, value=0)
    pool_max_buffers = Component(FakeSignal, value=0)
    pool_max_mem = Component(FakeSignal, value=0)
    pool_used_buffers = Component(FakeSignal, value=0)
    pool_used_mem = Component(FakeSignal, value=0)
    port_name = Component(FakeSignal, value=0)
    width = Component(FakeSignal, value=0)
    height = Component(FakeSignal, value=0)
    depth = Component(FakeSignal, value=0)
    array_size = DynamicDeviceComponent(ad_group(
        FakeSignal, (('height'), ('width'), ('depth')), value=0), 
                                        doc='The array size')
    bayer_pattern = Component(FakeSignal, value=0)
    blocking_callbacks = Component(FakeSignal, value=0)
    color_mode = Component(FakeSignal, value=0)
    data_type = Component(FakeSignal, value=0)
    dim0_sa = Component(FakeSignal, value=0)
    dim1_sa = Component(FakeSignal, value=0)
    dim2_sa = Component(FakeSignal, value=0)
    dim_sa = DynamicDeviceComponent(ad_group(
        FakeSignal, (('dim0'), ('dim1'), ('dim2')), value=0),
                                    doc='Dimension sub-arrays')
    dimensions = Component(FakeSignal, value=0)
    dropped_arrays = Component(FakeSignal, value=0)
    enable = Component(FakeSignal, value=0)
    min_callback_time = Component(FakeSignal, value=0)
    nd_array_address = Component(FakeSignal, value=0)
    nd_array_port = Component(FakeSignal, value=0)
    ndimensions = Component(FakeSignal, value=0)
    plugin_type = Component(FakeSignal, value=0)
    queue_free = Component(FakeSignal, value=0)
    queue_free_low = Component(FakeSignal, value=0)
    queue_size = Component(FakeSignal, value=0)
    queue_use = Component(FakeSignal, value=0)
    queue_use_high = Component(FakeSignal, value=0)
    queue_use_hihi = Component(FakeSignal, value=0)
    time_stamp = Component(FakeSignal, value=0)
    unique_id = Component(FakeSignal, value=0)


class StatsPlugin(plugins.StatsPlugin, PluginBase):
    """
    StatsPlugin but with components instantiated to be empty signals.
    """
    plugin_type = Component(FakeSignal, value='NDPluginStats')
    bgd_width = Component(FakeSignal, value=0)
    centroid_threshold = Component(FakeSignal, value=0)
    centroid = DynamicDeviceComponent(ad_group(FakeSignal, (('x'), ('y')), value=0),
                                      doc='The centroid XY')
    compute_centroid = Component(FakeSignal, value=0)
    compute_histogram = Component(FakeSignal, value=0)
    compute_profiles = Component(FakeSignal, value=0)
    compute_statistics = Component(FakeSignal, value=0)
    cursor = DynamicDeviceComponent(ad_group(FakeSignal, (('x'), ('y')), value=0),
                                    doc='The cursor XY')
    hist_entropy = Component(FakeSignal, value=0)
    hist_max = Component(FakeSignal, value=0)
    hist_min = Component(FakeSignal, value=0)
    hist_size = Component(FakeSignal, value=0)
    histogram = Component(FakeSignal, value=0)
    max_size = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='The maximum size in XY')
    max_value = Component(FakeSignal, value=0)
    max_xy = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Maximum in XY')
    mean_value = Component(FakeSignal, value=0)
    min_value = Component(FakeSignal, value=0)
    min_xy = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Minimum in XY')
    net = Component(FakeSignal, value=0)
    profile_average = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Profile average in XY')
    profile_centroid = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Profile centroid in XY')
    profile_cursor = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Profile cursor in XY')
    profile_size = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Profile size in XY')
    profile_threshold = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Profile threshold in XY')
    set_xhopr = Component(FakeSignal, value=0)
    set_yhopr = Component(FakeSignal, value=0)
    sigma_xy = Component(FakeSignal, value=0)
    sigma_x = Component(FakeSignal, value=0)
    sigma_y = Component(FakeSignal, value=0)
    sigma = Component(FakeSignal, value=0)
    ts_acquiring = Component(FakeSignal, value=0)
    ts_centroid = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Time series centroid in XY')
    ts_control = Component(FakeSignal, value=0)
    ts_current_point = Component(FakeSignal, value=0)
    ts_max_value = Component(FakeSignal, value=0)
    ts_max = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Time series maximum in XY')
    ts_mean_value = Component(FakeSignal, value=0)
    ts_min_value = Component(FakeSignal, value=0)
    ts_min = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Time series minimum in XY')
    ts_net = Component(FakeSignal, value=0)
    ts_num_points = Component(FakeSignal, value=0)
    ts_read = Component(FakeSignal, value=0)
    ts_sigma = Component(FakeSignal, value=0)
    ts_sigma_x = Component(FakeSignal, value=0)
    ts_sigma_xy = Component(FakeSignal, value=0)
    ts_sigma_y = Component(FakeSignal, value=0)
    ts_total = Component(FakeSignal, value=0)
    total = Component(FakeSignal, value=0)

    def __init__(self, prefix, *, noise_x=0, noise_y=0, noise_func=None, 
                 noise_type="uni", noise_args=(), noise_kwargs={}, **kwargs):
        self.noise_x = noise_x
        self.noise_y = noise_y
        self.noise_type = noise_type
        self.noise_func = noise_func or self._int_noise_func
        self.noise_args = noise_args
        self.noise_kwargs = noise_kwargs
        super().__init__(prefix, **kwargs)

    def _int_noise_func(self):
        if self.noise_type == "uni":
            if not self.noise_args:
                self.noise_args = (-1,1)
            if not self.noise_kwargs:
                self.noise_kwargs = {}
            return int(np.round(np.random.uniform(*self.noise_args,
                                                  **self.noise_kwargs)))
        elif self.noise_type == "norm":
            if not self.noise_args:
                self.noise_args = (0,0.25)
            if not self.noise_kwargs:
                self.noise_kwargs = {}
            return int(np.round(np.random.normal(*self.noise_args,
                                                 **self.noise_kwargs)))
        else:
            raise ValueError("Invalid noise type. Must be 'uni' or 'norm'") 
                                            
    @property
    def noise_x(self):
        return self.centroid.x.noise

    @noise_x.setter
    def noise_x(self, val):
        self.centroid.x.noise = val

    @property
    def noise_y(self):
        return self.centroid.y.noise

    @noise_y.setter
    def noise_y(self, val):
        self.centroid.y.noise = val


        
    # def read(self, **kwargs):
    #     # Run custom centroid function
    #     cent_x = self._cent_x()
    #     cent_y = self._cent_y()
    #     # Set the base pixel value 
    #     self.centroid.x.put(int(np.round(cent_x)))
    #     self.centroid.y.put(int(np.round(cent_y)))
    #     # Add noise and make sure it is an int
    #     cent_x = int(np.round(cent_x + np.random.uniform(-1,1) * self.noise_x))
    #     cent_y = int(np.round(cent_y + np.random.uniform(-1,1) * self.noise_y))
    #     # Check we arent out of bounds
    #     if self.zero_outside_yag and self._centroid_out_of_bounds():
    #         cent_x = 0
    #         cent_y = 0
    #     read = super().read(**kwargs)
    #     # Update the read with a noisy centroid or 0 if using oob
    #     read['{0}_centroid_x'.format(self.name)]['value'] = cent_x
    #     read['{0}_centroid_y'.format(self.name)]['value'] = cent_y
    #     return read
        
    # def _cent_x(self, **kwargs):
    #     """
    #     Place holder method that is can be overriden to calculate and return the
    #     centroid
    #     """
    #     return self.centroid.x.value
    
    # def _cent_y(self, **kwargs):
    #     """
    #     Place holder method that is can be overriden to calculate and return the 
    #     centroid.
    #     """
    #     return self.centroid.y.value

    # def _centroid_out_of_bounds(self):
    #     """
    #     Placeholder to be overridden by a function that checks the yag size.
    #     """
    #     return False
