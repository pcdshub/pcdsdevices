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


class AeroBase(EpicsMotor):
    """
    Base Aerotech motor class.
    """
    pass


class RotationAero(AeroBase):
    """
    Class for the aerotech rotation stage.
    """
    pass


class LinearAero(AeroBase):
    """
    Class for the aerotech linear stage.
    """
    pass
