import versioneer
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().split()

setup(name='pcdsdevices',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      license='BSD',
      author='SLAC National Accelerator Laboratory',
      packages=find_packages(),
      install_requires=requirements,
      description='IOC definitions for LCLS Beamline Devices',
      )
