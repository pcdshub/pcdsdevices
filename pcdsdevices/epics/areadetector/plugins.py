#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for AreaDetector Plugins.
"""

import logging
from ophyd import plugins
from ophyd.device import GenerateDatumInterface
from .base import ADBase

logger = logging.getLogger(__name__)


class PluginBase(plugins.PluginBase, ADBase):
    pass


class ImagePlugin(plugins.ImagePlugin, PluginBase):
    pass


class StatsPlugin(plugins.StatsPlugin, PluginBase):
    pass


class ColorConvPlugin(plugins.ColorConvPlugin, PluginBase):
    pass


class ProcessPlugin(plugins.ProcessPlugin, PluginBase):
    pass


class Overlay(plugins.Overlay, ADBase):
    pass


class OverlayPlugin(plugins.OverlayPlugin, PluginBase):
    pass


class ROIPlugin(plugins.ROIPlugin, PluginBase):
    pass


class TransformPlugin(plugins.TransformPlugin, PluginBase):
    pass


class FilePlugin(plugins.FilePlugin, PluginBase, GenerateDatumInterface):
    pass


class NetCDFPlugin(plugins.NetCDFPlugin, FilePlugin):
    pass


class TIFFPlugin(plugins.TIFFPlugin, FilePlugin):
    pass


class JPEGPlugin(plugins.JPEGPlugin, FilePlugin):
    pass


class NexusPlugin(plugins.NexusPlugin, FilePlugin):
    pass


class HDF5Plugin(plugins.HDF5Plugin, FilePlugin):
    pass


class MagickPlugin(plugins.MagickPlugin, FilePlugin):
    pass


