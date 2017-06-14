#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
import time

###############
# Third Party #
###############
import numpy as np

##########
# Module #
##########
from .signal import Signal
from .component import (FormattedComponent, Component, DynamicDeviceComponent)
from ..epics import mirror


class OMMotor(mirror.OMMotor):
    # TODO: Write a proper docstring
    """
    Offset Mirror Motor object used in the offset mirror systems. Mostly taken
    from ophyd.epics_motor.
    """
    # position
    user_readback = Component(Signal, value=0)
    user_setpoint = Component(Signal, value=0)

    # configuration
    velocity = Component(Signal)

    # motor status
    motor_is_moving = Component(Signal, value=0)
    motor_done_move = Component(Signal, value=1)
    high_limit_switch = Component(Signal, value=10000)
    low_limit_switch = Component(Signal, value=-10000)

    # status
    interlock = Component(Signal)
    enabled = Component(Signal)

    motor_stop = Component(Signal)

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None, velocity=0, noise=0, fake_sleep=0, 
                 refresh=0, settle_time=0, **kwargs):
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs, name=name, 
                         parent=parent, settle_time=settle_time, **kwargs)
        self.velocity.put(velocity)
        self.noise = noise
        self.fake_sleep = fake_sleep
        self.refresh = refresh

    def move(self, position, **kwargs):
        """
        Move to a specified position, optionally waiting for motion to
        complete.

        Parameters
        ----------
        position
            Position to move to

        Returns
        -------
        status : MoveStatus
        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`
        ValueError
            On invalid positions
        RuntimeError
            If motion fails other than timing out
        """
        self.user_setpoint.put(position)

        # Switch to moving state
        self.motor_is_moving.put(1)
        self.motor_done_move.put(0)

        # # Add uniform noise
        # pos = position + np.random.uniform(-1, 1)*self.noise

        # Make sure refresh is set to something sensible if using velo or sleep
        refresh = self.refresh or self.fake_sleep/10 or 0.1

        # If velo is set, incrementally set the readback according to the refresh
        if self.velocity.value:
            next_pos = self.user_readback.value
            while next_pos < position:
                self.user_readback.put(next_pos) 
                time.sleep(refresh)
                next_pos += self.velocity.value*refresh

        # If fake sleep is set, incrementatlly sleep while setting the readback
        elif self.fake_sleep:
            wait = 0
            while wait < self.fake_sleep:
                time.sleep(refresh)
                wait += refresh
                self.user_readback.put(wait/self.fake_sleep * position)
        status = self.user_readback.set(position)

        # Switch to finished state and wait for status to update
        self.motor_is_moving.put(0)
        self.motor_done_move.put(1)
        time.sleep(0.1)
        return status

    @property
    def position(self):
        self.user_readback.put(
            self.user_setpoint.value + np.random.uniform(-1,1)*self.noise)
        return self.user_readback.value

    def read(self, **kwargs):
        self.user_readback.put(
            self.user_setpoint.value + np.random.uniform(-1,1)*self.noise)
        return super().read(**kwargs)


class OffsetMirror(mirror.OffsetMirror):
    # TODO: Add all parameters to doc string
    """
    Simulation of a simple flat mirror with assorted motors.
    
    Parameters
    ----------
    name : string
        Name of motor

    x : float
        Initial position of x-motor

    z : float
        Initial position of z-motor

    alpha : float
        Initial position of alpha-motor

    noise_x : float, optional
        Multiplicative noise factor added to x-motor readback

    noise_z : float, optional
        Multiplicative noise factor added to z-motor readback

    noise_alpha : float, optional
        Multiplicative noise factor added to alpha-motor readback
    
    fake_sleep_x : float, optional
        Amount of time to wait after moving x-motor

    fake_sleep_z : float, optional
        Amount of time to wait after moving z-motor

    fake_sleep_alpha : float, optional
        Amount of time to wait after moving alpha-motor
    """
    # Gantry Motors
    gan_x_p = FormattedComponent(OMMotor, "STEP:{self._mirror}:X:P")
    gan_x_s = FormattedComponent(OMMotor, "STEP:{self._mirror}:X:S")
    gan_y_p = FormattedComponent(OMMotor, "STEP:{self._mirror}:Y:P")
    gan_y_s = FormattedComponent(OMMotor, "STEP:{self._mirror}:Y:S")
    
    # Pitch Motor
    pitch = FormattedComponent(OMMotor, "{self._prefix}")

    # Placeholder signals for non-implemented components
    piezo = Component(Signal)
    coupling = Component(Signal)
    motor_stop = Component(Signal)

    def __init__(self, prefix, *, name=None, read_attrs=None, parent=None, 
                 configuration_attrs=None, section="", x=0, y=0, z=0, alpha=0, 
                 velo_x=0, velo_y=0, velo_alpha=0, refresh_x=0, refresh_y=0, 
                 refresh_alpha=0, noise_x=0, noise_y=0, noise_z=0, noise_alpha=0, 
                 fake_sleep_x=0, fake_sleep_y=0, fake_sleep_alpha=0, **kwargs):
        if len(prefix.split(":")) < 3:
            prefix = "MIRR:TST:{0}".format(prefix)
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)

        # Simulation Attributes
        # Fake noise to readback and moves
        self.gan_x_p.noise = self.gan_x_s.noise = noise_x
        self.gan_y_p.noise = self.gan_y_s.noise = noise_y
        self.pitch.noise = noise_alpha
        
        # Fake sleep for every move
        self.gan_x_p.fake_sleep = self.gan_x_s.fake_sleep = fake_sleep_x
        self.gan_y_p.fake_sleep = self.gan_y_s.fake_sleep = fake_sleep_y
        self.pitch.fake_sleep = fake_sleep_alpha

        # Velocity for every move
        self.gan_x_p.velocity.value = self.gan_x_s.velocity.value = velo_x
        self.gan_y_p.velocity.value = self.gan_y_s.velocity.value = velo_y
        self.pitch.velocity.value = velo_alpha

        # Refresh rate for moves
        self.gan_x_p.refresh = self.gan_x_s.refresh = refresh_x
        self.gan_y_p.refresh = self.gan_y_s.refresh = refresh_y
        self.pitch.refresh = refresh_alpha
        
        # Set initial position values
        self.gan_x_p.user_setpoint.put(x)
        self.gan_x_p.user_readback.put(x)
        self.gan_x_s.user_setpoint.put(x)
        self.gan_x_s.user_readback.put(x)
        self.gan_y_p.user_setpoint.put(y)
        self.gan_y_p.user_readback.put(y)
        self.gan_y_s.user_setpoint.put(y)
        self.gan_y_s.user_readback.put(y)
        self.pitch.user_setpoint.put(alpha)
        self.pitch.user_readback.put(alpha)
        self.i_z = z
        self.noise_z = noise_z

    # Coupling motor isnt implemented as an example so override its properties
    @property
    def decoupled(self):
        return False

    @property
    def fault(self):
        return False

    @property
    def gdif(self):
        return 0.0

    @property
    def _x(self):
        return self.gan_x_p.position

    @property
    def _y(self):
        return self.gan_y_p.position

    @property
    def _z(self):
        return self.i_z + np.random.uniform(-1,1)*self.noise_z

    @_z.setter
    def _z(self, val):
        self.i_z = val

    @property
    def _alpha(self):
        return self.pitch.position

