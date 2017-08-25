#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diodes
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############

##########
# Module #
##########
from .device import device

logger = logging.getLogger(__name__)


class DiodeBase(Device):
    """
    Base class for the diode.
    """
    pass


class HamamatsuDiode(DiodeBase):
    """
    Class for the Hamamatsu diode.
    """
    pass
