

.. raw:: html

   <h1 align="center">PCDS Devices</h1>



.. raw:: html

   <div align="center">
     <strong>Collection of Ophyd Device subclasses for IOCs unique to PCDS</strong>
   </div>



.. raw:: html

   <p align="center">
     <a href="#motivation">Motivation</a> •
     <a href="#installation">Installation</a>
   </p>



Motivation
----------

Ophyd presents a uniform set of abstractions for EPICS devices. While many
devices can be represented as generic ``EpicsMotor`` and ``AreaDetector``
objects, quite a few devices are specific to LCLS. This repository holds all of
these unique devices as well as additional tools to help aid the creation of
custom devices for specific applications.

Installation
------------

Install the most recent tagged build:

.. code-block::

     conda install pcdsdevices -c pcds-tag -c lightsource2-tag -c conda-forge

Install the most recent development build:

.. code-block::

     conda install pcdsdevices -c pcds-dev -c lightsource2-tag -c conda-forge
