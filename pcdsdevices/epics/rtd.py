#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RTDs
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
from .device import Device

logger = logging.getLogger(__name__)


class RTDBase(Device):
    """
    Base class for the RTD.
    """
    pass


class OmegaRTD(RTDBase):
    """
    Class for the Omega RTD.
    """
    pass
