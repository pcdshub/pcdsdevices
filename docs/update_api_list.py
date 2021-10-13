import pathlib
import sys

import ophyd

import pcdsdevices.interface
from pcdsdevices.tests import conftest

classes = conftest.find_all_classes(
    (
        ophyd.Device,
        pcdsdevices.interface.BaseInterface,
        pcdsdevices.interface._TabCompletionHelper,
    )
)

callables = conftest.find_all_callables()

modules = set(
    obj.__module__
    for obj in list(classes) + list(callables)
    if obj.__module__.startswith("pcdsdevices.")
)


automodules = "".join(
    f"""
.. automodule:: {module}
    :members:

"""
    for module in sorted(modules)
)


print(f"""
API
###

""".rstrip())


for module_name in sorted(modules):
    underline = "-" * len(module_name)
    print(module_name)
    print(underline)
    print()
    module = sys.modules[module_name]
    objects = [
        obj
        for obj in list(classes) + list(callables)
        if obj.__module__ == module_name and
        hasattr(module, obj.__name__)
    ]

    if objects:
        print(".. autosummary::")
        print("    :toctree: generated")
        print()

        for obj in sorted(objects, key=lambda obj: obj.__name__):
            print(f"    {obj.__module__}.{obj.__name__}")

        print()
