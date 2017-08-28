#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Attocube devices
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
from .epicsmotor import EpicsMotor

logger = logging.getLogger(__name__)


class MicronixBase(EpicsMotor):
    """
    Base Micronix motor class.
    """

    
class VT50(MicronixBase):
    """
    VT50 Micronix Motor
    """
    pass
