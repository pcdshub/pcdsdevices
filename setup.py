from setuptools import find_packages, setup

import versioneer

with open("requirements.txt", "rt") as fp:
    install_requires = [
        line for line in fp.read().splitlines()
        if line and not line.startswith("#")
    ]

setup(
    name="pcdsdevices",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    license="BSD",
    author="SLAC National Accelerator Laboratory",
    packages=find_packages(),
    include_package_data=True,
    description="Ophyd Device definitions for LCLS Beamline components",
    entry_points={
        "happi.containers": ["pcdsdevices = pcdsdevices.happi.containers"],
        "typhos.ui": ["pcdsdevices = pcdsdevices.ui:path"],
    },
    install_requires=install_requires,
    python_requires=">=3.9",
)
