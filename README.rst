============
PCDS Devices
============
.. image:: https://travis-ci.org/pcdshub/pcdsdevices.svg?branch=master
   :target: https://travis-ci.org/pcdshub/pcdsdevices
   :alt: Build Status
.. image:: https://codecov.io/gh/pcdshub/pcdsdevices/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/pcdshub/pcdsdevices
   :alt: Code Coverage

``pcdsdevices`` is a collection of ophyd device subclasses for IOCs unique to PCDS.
The documentation is hosted at `<https://pcdshub.github.io/pcdsdevices>`_.

Motivation
##########

Ophyd presents a uniform set of abstractions for EPICS devices. While many
devices can be represented as generic ``EpicsMotor`` and ``AreaDetector``
objects, quite a few devices are specific to LCLS. This repository holds all of
these unique devices as well as additional tools to help aid the creation of
custom devices for specific applications.

Installation
############

Install the most recent tagged build:

.. code:: bash

  conda install pcdsdevices -c pcds-tag -c conda-forge

Install the most recent development build: 

.. code:: bash

  conda install pcdsdevices -c pcds-dev -c conda-forge
