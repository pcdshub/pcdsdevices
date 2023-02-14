<h1 align="center">PCDS Devices</h1>

<div align="center">
  <strong>Collection of Ophyd Device subclasses for IOCs unique to PCDS</strong>
</div>

<p align="center">
  <a href="#motivation">Motivation</a> •
  <a href="#installation">Installation</a>
</p>

## Motivation

Ophyd presents a uniform set of abstractions for EPICS devices. Many devices at
the LCLS are covered by ophyd-provided classes such as ``EpicsMotor`` and
``AreaDetector``, but there are also many more custom and unique devices.

This repository:

* Defines unique device classes required by the LCLS, referenced by happi
  and our [device_config](https://github.com/pcdshub/device_config/) database.
* Offers LCLS-tailored solutions for functionality not provided by ophyd
* Provides essential tools to aid in the creation of new devices for specific
  applications
* Acts as a proving ground for features that may eventually be destined for
  ophyd
* ... and more!

Much of the core re-used functionality can be found in
``pcdsdevices.device``, ``pcdsdevices.interface``, ``pcdsdevices.pseudopos``,
and ``pcdsdevices.signal``.

## Installation

Install the most recent tagged build:

```bash
$ conda install -c conda-forge pcdsdevices
```

Install the most recent development build:

```bash
$ conda install pcdsdevices -c pcds-dev -c lightsource2-tag -c conda-forge
```

Or alternatively:

```bash
# Install the tagged version for the dependencies
$ conda install -c conda-forge pcdsdevices

# Clone the master branch:
$ git clone https://github.com/pcdshub/pcdsdevices
$ cd pcdsdevices

# And perform a development install:
$ python -m pip install -e .
```

## Testing

### Testing from psbuild-rhel7

Use the pcds conda environment:

```bash
$ source /cds/group/pcds/pyps/conda/pcds_conda
```

### Testing without PCDS servers

Ensure you have all of the development requirements available:

```bash
$ pip install -r dev-requirements.txt
```

### General testing steps

```bash
$ git clone https://github.com/pcdshub/pcdsdevices
$ cd pcdsdevices

# Switch to a branch that reflects what you're working on:
$ git checkout -b my_feature_branch_name

# Make your changes to files
# Install pre-commit to allow for style checks before committing
$ pre-commit install

# Run the test suite
$ python run_tests.py -v
```

If all is well, commit and push your changes.

If pre-commit complains about an issue, you will need to resolve it and try
again.

```bash
$ git commit -a -m "ENH: my new feature"
$ git remote add my_remote git@github.com:my_username/pcdsdevices
$ git push -u my_remote my_feature_branch_name
```
