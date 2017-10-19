#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum

from ..interface import BranchingInterface
from .device import Device
from .state import statesrecord_class
from .state import statesrecord_class, InOutStates
from .component import Component


YagLomStates = statesrecord_class("YagLomStates", ":OUT", ":YAG", ":SLIT1",
                                  ":SLIT2", ":SLIT3")
LodcmStates = statesrecord_class("LodcmStates", ":OUT", ":C", ":Si")
DectrisStates = statesrecord_class("DectrisStates", ":OUT", ":DECTRIS",
                                   ":SLIT1", ":SLIT2", ":SLIT3", ":OUTLOW")
FoilStates = statesrecord_class("FoilStates", ":OUT", ":Mo", ":Zr", ":Zn",
                                ":Cu", ":Ni", ":Fe", "Ti")


class LODCM(Device metaclass=BranchingInterface):
    h1n_state = Component(LodcmStates, ":H1N")
    h2n_state = Component(LodcmStates, ":H2N")
    yag_state = Component(YagLomStates, ":DV")
    dectris_state = Component(DectrisStates, ":DH")
    diode_state = Component(InOutStates, ":DIODE")
    foil_state = Component(FoilStates, ":FOIL")

    light_states = Enum("LightStates", "BLOCKED MAIN MONO BOTH UNKNOWN",
                        start=0)

    def __init__(self, prefix, *, name, main_name='MAIN', mono_name='MONO',
                 **kwargs):
        self.main_name = main_name
        self.mono_name = mono_name
        super().__init__(prefix, name=name, **kwargs)

    def destination(self, line=None):
        """
        Return where the light is going for a given line at the current LODCM
        state.

        Parameters
        ----------
        line: str or int, optional
            The starting line for the beam. If this is 1 or "MAIN", light is
            coming in on H1N from the main line. If this is 2 or "MONO", light
            is coming in on H2N to the mono line (e.g. XCS periscope)

        Returns
        -------
        destination: str
            "BLOCKED" if the light (probably) does not go through.
            "MAIN" if the light continues on the main line.
            "MONO" if the light continues on the mono line.
            "BOTH" if the light continues on both lines.
            "UNKNOWN" if the state is strange.
        """
        if line is None:
            line = self.light_states.MAIN
        else:
            try:
                line = self.light_states[line]
            except:
                line = self.light_states(line)
        if line == self.light_states.MAIN:
            # H2N:     OUT      C       Si
            table = [["MAIN", "MAIN", "MAIN"],  # H1N at OUT
                     ["MAIN", "BOTH", "MAIN"],  # H1N at C
                     ["BLOCKED", "BLOCKED", "MONO"]]  # H1N at Si
            try:
                n1 = ("OUT", "C", "Si").index(self.h1n_state.value)
                n2 = ("OUT", "C", "Si").index(self.h2n_state.value)
            except ValueError:
                return "UNKNOWN"
            return table[n1][n2]
        elif line == self.light_states.MONO:
            table = ["MONO", "BLOCKED", "BLOCKED"]
            try:
                n2 = ("OUT", "C", "Si").index(self.h2n_state.value)
            except ValueError:
                return "UNKNOWN"
            return table[n2]
