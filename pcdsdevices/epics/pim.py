#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .iocdevice import IocDevice
from .component import Component
from .state import statesrecord_class

PIMStates = statesrecord_class("PIMStates", ":OUT", ":YAG", ":DIODE")


class PIM(IocDevice):
    """
    Standard position monitor. Consists of one stage that can either block the
    beam with a YAG crystal or put a diode in. Has a camera that looks at the
    YAG crystal to determine beam position.
    """
    states = Component(PIMStates, "")

    @property
    def blocking(self):
        if self.states.value in ("OUT", "DIODE"):
            return False
        return True

    def move_in(self):
        """
        Move the PIM to the YAG position.
        """
        self.states.value = "YAG"

    def move_out(self):
        """
        Move the PIM to the OUT position.
        """
        self.states.value = "OUT"

    def move_diode(self):
        """
        Move the PIM to the DIODE position.
        """
        self.states.value = "DIODE"
