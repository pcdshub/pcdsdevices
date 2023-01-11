"""
Tool that generates the source for ``source/api.rst``.

Uses tools from the pcdsdevices test suite to enumerate classes and callables.
"""
import sys

import ophyd

import pcdsdevices.interface
from pcdsdevices.tests import conftest

classes = conftest.find_all_classes(
    (
        ophyd.Device,
        ophyd.ophydobj.OphydObject,
        pcdsdevices.interface.BaseInterface,
        pcdsdevices.interface._TabCompletionHelper,
    )
)

callables = conftest.find_all_callables()

modules = {
    obj.__module__
    for obj in list(classes) + list(callables)
    if obj.__module__.startswith("pcdsdevices.")
}


def create_api_list() -> list[str]:
    """Create the API list with all classes and functions."""
    output = [
        "API",
        "###",
        "",
    ]

    for module_name in sorted(modules):
        underline = "-" * len(module_name)
        output.append(module_name)
        output.append(underline)
        output.append("")
        module = sys.modules[module_name]
        objects = [
            obj
            for obj in list(classes) + list(callables)
            if obj.__module__ == module_name and hasattr(module, obj.__name__)
        ]

        if objects:
            output.append(".. autosummary::")
            output.append("    :toctree: generated")
            output.append("")

            for obj in sorted(objects, key=lambda obj: obj.__name__):
                output.append(f"    {obj.__module__}.{obj.__name__}")

            output.append("")

    while output[-1] == "":
        output.pop(-1)
    return output


if __name__ == "__main__":
    output = create_api_list()
    print("\n".join(output))
