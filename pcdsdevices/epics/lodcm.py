#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ..interface import BranchingInterface
from .device import Device
from .state import statesrecord_class, InOutStates
from .component import Component


YagLomStates = statesrecord_class("YagLomStates", ":OUT", ":YAG", ":SLIT1",
                                  ":SLIT2", ":SLIT3")
LodcmStates = statesrecord_class("LodcmStates", ":OUT", ":C", ":Si")
DectrisStates = statesrecord_class("DectrisStates", ":OUT", ":DECTRIS",
                                   ":SLIT1", ":SLIT2", ":SLIT3", ":OUTLOW")
FoilStates = statesrecord_class("FoilStates", ":OUT", ":Mo", ":Zr", ":Zn",
                                ":Cu", ":Ni", ":Fe", "Ti")


class LODCM(Device, metaclass=BranchingInterface):
    h1n_state = Component(LodcmStates, ":H1N")
    h2n_state = Component(LodcmStates, ":H2N")
    yag_state = Component(YagLomStates, ":DV")
    dectris_state = Component(DectrisStates, ":DH")
    diode_state = Component(InOutStates, ":DIODE")
    foil_state = Component(FoilStates, ":FOIL")

    def __init__(self, prefix, *, name, main_name='MAIN', mono_name='MONO',
                 **kwargs):
        self.main_name = main_name
        self.mono_name = mono_name
        super().__init__(prefix, name=name, **kwargs)

    @property
    def destination(self):
        """
        Return where the light is going at the current LODCM
        state.

        Returns
        -------
        destination: list of str
            self.main_name if the light continues on the main line.
            self.mono_name if the light continues on the mono line.
        """
        # H2N:     OUT      C       Si
        table = [["MAIN", "MAIN", "MAIN"],  # H1N at OUT
                 ["MAIN", "BOTH", "MAIN"],  # H1N at C
                 ["BLOCKED", "BLOCKED", "MONO"]]  # H1N at Si
        n1 = ("OUT", "C", "Si").index(self.h1n_state.value)
        n2 = ("OUT", "C", "Si").index(self.h2n_state.value)
        state = table[n1][n2]
        if state == "MAIN":
            return [self.main_name]
        elif state == "BLOCKED":
            return []
        else:
            if state == "MONO" and self.diag_clear:
                return [self.mono_name]
            if state == "BOTH":
                if self.diag_clear:
                    return [self.main_name, self.mono_name]
                else:
                    return [self.main_name]
        return []

    @property
    def branches(self):
        return [self.main_name, self.mono_name]

    @property
    def diag_clear(self):
        yag_clear = self.yag_state.value == 'OUT'
        dectris_clear = self.dectris_state.value in ('OUT', 'OUTLOW')
        diode_clear = self.diode_state.value in ('IN', 'OUT')
        foil_clear = self.foil_state.value == 'OUT'
        return all(yag_clear, dectris_clear, diode_clear, foil_clear)

    @property
    def inserted(self):
        return not (self.destination and self.diag_clear)

    @property
    def removed(self):
        return self.diag_clear or self.destination == self.main

    def remove(self, wait=False, timeout=None, finished_cb=None, **kwargs):
        yag_status = self.yag_state.move('OUT')
        dectris_status = self.dectris_state.move('OUT')
        diode_status = self.diode_state.move('OUT')
        foil_status = self.foil_state.move('OUT')
