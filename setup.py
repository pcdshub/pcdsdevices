from setuptools import find_packages, setup

import versioneer

setup(
    name='pcdsdevices',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    license='BSD',
    author='SLAC National Accelerator Laboratory',
    packages=find_packages(),
    description='IOC definitions for LCLS Beamline Devices',
    entry_points={
        'happi.containers': ['pcdsdevices = pcdsdevices.happi.containers'],
    }
)
