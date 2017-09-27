PCDS Devices
============
.. image:: https://travis-ci.org/slaclab/pcds-devices.svg?branch=master
  :target: https://travis-ci.org/slaclab/pcds-devices

.. image:: https://codecov.io/gh/slaclab/pcds-devices/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/slaclab/pcds-devices

Collection of Ophyd Device subclasses for IOCs unique to LCLS PCDS.


Ophyd presents a uniform set of abstractions for EPICS devices. While many
devices can be represented as generic ``EpicsMotor`` and ``AreaDetector``
objects, quite a few devices are specific to LCLS. This repository holds all of
these unique devices as well as additional tools to create simulations as well
as loading items with our metadata store `happi <http://pswww.slac.stanford.edu/swdoc/releases/skywalker/happi>`_

Conda
++++++

Install the most recent tagged build:

.. code::
  
  conda install pcds-devices -c skywalker-tag -c lightsource2-tag -c conda-forge

Install the most recent development build: 

.. code::

  conda install pcds-devices -c skywalker-dev -c lightsource2-tag -c conda-forge
