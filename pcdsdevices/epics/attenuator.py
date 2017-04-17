#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define operation of the lcls attenuator IOCs
"""
from enum import Enum
from threading import Event, RLock

from .device import Device
from .iocdevice import IocDevice
from .component import Component
from .signal import EpicsSignal, EpicsSignalRO

MAX_FILTERS = 12


class Filter(Device):
    """
    A single attenuation blade.
    """
    state_sig = Component(EpicsSignal, ":STATE", write_pv=":GO")
    thickness_sig = Component(EpicsSignal, ":THICK")
    material_sig = Component(EpicsSignal, ":MATERIAL")
    stuck_sig = Component(EpicsSignal, ":IS_STUCK")

    FilterStates = Enum("FilterStates", "UNKNOWN IN OUT")
    StuckEnum = Enum("StuckEnum", "NOT_STUCK STUCK_IN STUCK_OUT")

    def __init__(self, prefix, *, name=None, read_attrs=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['state_sig']
        super().__init__(prefix, name=name, read_attrs=read_attrs, **kwargs)

    @property
    def value(self):
        """
        The blade's current position.

        Returns
        -------
        value: str
            "IN" if the blade is in, "OUT" if the blade is out, and "UNKNOWN"
            if the blade is between the two segments.
        """
        return self.FilterStates(self.state_sig.get()).name

    def move_in(self):
        """
        Moves the blade to the "IN" position.
        """
        self.state_sig.put(self.FilterStates.IN.value)

    def move_out(self):
        """
        Moves the blade to the "OUT" position.
        """
        self.state_sig.put(self.FilterStates.OUT.value)

    @property
    def stuck(self):
        """
        Whether or not the blade is currently stuck. The attenuator IOC will
        handle stuck blades and try to reach the desired transmission given the
        constraints.

        Returns
        -------
        stuck: str
            "NOT_STUCK" if the blade is not stuck. "STUCK_IN" if the blade is
            stuck in the "IN" position. "STUCK_OUT" if the blade is stuck in
            the "OUT" position.
        """
        return self.StuckEnum(self.stuck_sig.get()).name

    def mark_stuck_in(self):
        """
        Mark this blade as "STUCK_IN"
        """
        self.stuck_sig.put(self.StuckEnum.STUCK_IN.value)

    def mark_stuck_out(self):
        """
        Mark this blade as "STUCK_OUT"
        """
        self.stuck_sig.put(self.StuckEnum.STUCK_OUT.value)

    def mark_not_stuck(self):
        """
        Mark this blade as "NOT_STUCK"
        """
        self.stuck_sig.put(self.StuckEnum.NOT_STUCK.value)

    @property
    def thickness(self):
        return self.thickness_sig.get()


class AttenuatorBase(IocDevice):
    """
    Interface to the attenuator IOC, which handles all the calculations. This
    base class does not include any filters. You may pass n_filters to the
    Attenuator class to connect to the correct number of filters.
    """
    user_energy = Component(EpicsSignal, ":EDES")
    energy = Component(EpicsSignalRO, ":T_CALC.VALE")
    desired_transmission = Component(EpicsSignal, ":RDES")
    transmission = Component(EpicsSignalRO, ":R_CUR")
    transmission_ceiling = Component(EpicsSignalRO, ":R_CEIL")
    transmission_floor = Component(EpicsSignalRO, ":R_FLOOR")

    user_energy_3rd = Component(EpicsSignal, ":E3DES")
    energy_3rd = Component(EpicsSignalRO, ":T_CALC.VALH")
    desired_transmission_3rd = Component(EpicsSignal, ":R3DES")
    transmission_3rd = Component(EpicsSignalRO, ":R3_CUR")
    transmission_ceiling_3rd = Component(EpicsSignalRO, ":R3_CEIL")
    transmission_floor_3rd = Component(EpicsSignalRO, ":R3_FLOOR")

    num_att = Component(EpicsSignalRO, ":NATT")
    status = Component(EpicsSignalRO, ":STATUS")
    calcpend = Component(EpicsSignalRO, ":CALCP")

    eget_cmd = Component(EpicsSignal, ":EACT.SCAN")
    mode_cmd = Component(EpicsSignal, ":MODE")
    go_cmd = Component(EpicsSignal, ":GO")

    def __init__(self, prefix, *, name=None, read_attrs=None, ioc="",
                 **kwargs):
        self._calc_event = Event()
        self._set_lock = RLock()
        if read_attrs is None:
            read_attrs = ["transmission", "transmission_3rd"]
        super().__init__(prefix, name=name, read_attrs=read_attrs,
                         ioc=ioc, **kwargs)

    def __call__(self, transmission=None, **kwargs):
        """
        Delegate object calls to getting or setting the transmission.

        Parameters
        ----------
        transmission: number, optional
            If provided, the attenuator will set the transmission to this
            value. If this is omitted, we will just return the current
            transmission.
        **kwargs: optional
            See set_energy and set_transmission for valid kwargs.

        Returns
        -------
        transmission: float
            Returns the current attenuator transmission, after the filters are
            done moving if applicable.
        """
        if transmission is None:
            return self.get_transmission(**kwargs)
        else:
            return self.set_transmission(transmission, **kwargs)

    def all_in(self):
        """
        Move all filters to the "IN" position.
        """
        self.go_cmd.put(1)

    def all_out(self):
        """
        Move all filters to the "OUT" position.
        """
        self.go_cmd.put(0)

    def thickest_filter_in(self):
        """
        Move just the thickest filter in to block the beam.
        """
        filt = self._thickest_filter()
        filt.move_in()

    def thickest_filter_out(self):
        """
        Move just the thickest filter out to stop blocking the beam.
        """
        filt = self._thickest_filter()
        filt.move_out()

    def _thickest_filter(self):
        """
        Figure out which filter is the thickest and return the Filter object,
        or pick the answer from the cache.

        Returns
        -------
        filter: filter
        """
        try:
            return self._thickest_filter_cache
        except AttributeError:
            best = None
            best_num = 0
            for i in range(1, MAX_FILTERS + 1):
                try:
                    filt = getattr(self, "filter{}".format(i))
                except AttributeError:
                    break
                if filt.thickness > best_num:
                    best_num = filt.thickness
                    best = filt
            self._thickest_filter_cache = best
            return best

    def set_energy(self, energy=None, use3rd=False):
        """
        Sets the energy to use for transmission calculations.

        Parameters
        ----------
        energy: number, optional
            If provided, this is the energy we'll use for the transmission
            calcluations. If omitted, we'll clear any set energy and use the
            current beam energy instead.
        use3rd: bool, optional
            If True, set the 3rd harmonic energy instead of the fundamental
            energy. This defaults to False.
        """
        if energy is None:
            self.eget_cmd.put(6)
        else:
            self.eget_cmd.put(0)
            self.eget_cmd.wait_for_value(0, timeout=1)
            if use3rd:
                self.user_energy_3rd.put(energy)
            else:
                self.user_energy.put(energy)

    def get_transmission(self, use3rd=False):
        """
        Get the current value for the transmission.

        Parameters
        ----------
        use3rd: bool, optional
            If True, get the 3rd harmonic transmission instead of the
            fundamental transmission.
        """
        if use3rd:
            return self.transmission_3rd.get()
        else:
            return self.transmission.get()

    def set_transmission(self, transmission, E=None, use3rd=False, wait=False):
        """
        Moves the filters to most closely match the desired transmission.

        Parameters
        ----------
        transmission: number
            Desired transmission ratio
        E: number, optional
            Desired energy to use for the calculation. If not provided, use the
            current set energy.
        use3rd: bool, optional
            If True, use the 3rd harmonic energy and transmission instead of
            the fundamental. Defaults to False.
        wait: bool, optional
            If True, waits for the filters to stop moving. Return the actual
            transmission if we waited.

        Returns
        -------
        transmission: number or None
            If we waited, return the actual transmission. Otherwise, return
            None.
        """
        if wait:
            raise NotImplementedError()
        with self._set_lock:
            floor, ceiling = self.calc_transmission(transmission, E=E,
                                                    use3rd=use3rd)
            if abs(floor - transmission) >= abs(ceiling - transmission):
                self.go_cmd.put(3)
            else:
                self.go_cmd.put(2)

    def calc_transmission(self, transmission, E=None, use3rd=False):
        """
        Calculate the closest transmissions we can get to the desired
        transmission given our attenuator blades.

        Do not run this if a user in another session is trying to set the
        transmission. This can cause problems such as having the attenuation
        set to the outputs of this calculation.

        Parameters
        ----------
        transmission: number
            Transmission ratio to use for the calculations
        E: number, optional
            Desired energy to use for the calculation. If not provided, use the
            current set energy.
        use3rd: bool, optional
            If True, use the 3rd harmonic energy and transmission instead of
            the fundamental. Defaults to False.

        Returns
        -------
        transmissions: length 2 tuple of floats
            The possible transmissions that are closest to the desired
            transmissions. The first will be the floor and the second will be
            the ceiling.
        """
        with self._set_lock:
            if E is not None:
                self.set_energy(E, use3rd=use3rd)
            if use3rd:
                with self.calcpend.wait_for_value_context(0, old_value=1,
                                                          timeout=1):
                    self.desired_transmission_3rd.put(transmission)
                floor = self.transmission_floor.get()
                ceiling = self.transmission_ceiling.get()
            else:
                with self.calcpend.wait_for_value_context(0, old_value=1,
                                                          timeout=1):
                    self.desired_transmission.put(transmission)
                floor = self.transmission_floor_3rd.get()
                ceiling = self.transmission_ceiling_3rd.get()
            return (floor, ceiling)


def make_att_classes(max_filters):
    att_classes = {}
    for i in range(1, max_filters + 1):
        att_filters = {}
        for n in range(1, i):
            att_filters["filter{}".format(n)] = Component(Filter,
                                                          ":{:02}".format(n))
        att_classes[i] = type("Attenuator{}".format(i), (AttenuatorBase,),
                              att_filters)
    return att_classes


att_classes = make_att_classes(MAX_FILTERS)


def Attenuator(prefix, n_filters, *, name=None, read_attrs=None, ioc="",
               **kwargs):
    """
    Factory function for instantiating an attenuator with the correct filter
    components given the number required.
    """
    return att_classes[n_filters](prefix, name=name, read_atts=read_attrs,
                                  ioc=ioc, **kwargs)
