"""
Module for defining bell-and-whistles movement features
"""
from pathlib import Path
from types import SimpleNamespace

from bluesky.utils import ProgressBar
from ophyd.status import wait as status_wait


class MvInterface:
    """
    Interface layer to attach to a positioner for motion shortcuts.

    Defines common shortcuts that the beamline scientists like for moving
    things on the command line. There is no need for these in a scripting
    environnment, but this is a safe space for implementing move features that
    would otherwise be disruptive to running scans and writing higher-level
    applications.
    """
    def mv(self, position, timeout=None, wait=False):
        """
        Absolute move to a position.

        Parameters
        ----------
        position
            Desired end position

        timeout: ``float``, optional
            If provided, the mover will throw an error if motion takes longer
            than timeout to complete. If omitted, the mover's default timeout
            will be use.

        wait: ``bool``, optional
            If ``True``, wait for motion completion before returning.
            Defaults to ``False``.
        """
        self.move(position, timeout=timeout, wait=wait)

    def wm(self):
        """
        Get the mover's positon (where motor)

        Returns
        -------
        position
            Current position
        """
        return self.position

    def __call__(self, position=None, timeout=None, wait=False):
        """
        Calling the object will either move the object or get the current
        position, depending on if the position argument is given. See the
        docstrings for `mv` and `wm`.
        """
        if position is None:
            return self.wm()
        else:
            self.mv(position, timeout=timeout, wait=wait)


class FltMvInterface(MvInterface):
    """
    Extension of MvInterface for when the position is a float.

    This lets us do more with the interface, such as relative moves.
    """
    def mvr(self, delta, timeout=None, wait=False):
        """
        Relative move from this position.

        Parameters
        ----------
        delta: float
            Desired change in position

        timeout: number, optional
            If provided, the mover will throw an error if motion takes longer
            than timeout to complete. If omitted, the mover's default timeout
            will be use.

        wait: bool, optional
            If True, wait for motion completion before returning. Defaults to
            False.
        """
        self.mv(delta + self.wm(), timeout=timeout, wait=wait)

    def umv(self, position, timeout=None):
        """
        Move to a position, wait, and update with a progress bar.

        Parameters
        ----------
        position: float
            Desired end position

        timeout: number, optional
            If provided, the mover will throw an error if motion takes longer
            than timeout to complete. If omitted, the mover's default timeout
            will be use.
        """
        status = self.move(position, timeout=timeout, wait=False)
        ProgressBar([status])
        try:
            status_wait(status)
        except KeyboardInterrupt:
            self.stop()

    def umvr(self, delta, timeout=None):
        """
        Relative move from this position, wait, and update with a progress bar.

        Parameters
        ----------
        delta: float
            Desired change in position

        timeout: number, optional
            If provided, the mover will throw an error if motion takes longer
            than timeout to complete. If omitted, the mover's default timeout
            will be use.
        """
        self.umv(delta + self.wm(), timeout=timeout)


class Presets:
    """
    Manager for device preset positions. This provides methods for adding new
    presets, checking which presets are active, and related utilities.

    Parameters
    ----------
    device: ``Device``
        The device to manage saved preset positions for. It must implement the
        `FltMvInterface`.

    paths: ``dict{str: str}``
        A mapping from type of preset to destination path. These will be
        directories that contain the yaml files that define the preset
        positions.
    """
    _MAX_HISTORY_LENGTH = 5

    def __init__(self, device, paths):
        self._device = device
        self._paths = {}
        for k, v in paths.items():
            self._paths[k] = Path(v)
        self._methods = []
        self.positions = SimpleNamespace()
        self.sync()

    def sync(self):
        """
        Read from the database and create methods and objects appropriately.
        """
        pass

    def _save(self, path, name, position):
        pass

    def _save_here(self, path, name):
        pass

    def _load(self, path):
        pass

    def _clear_load(self, name):
        pass

    def _clear_load_all(self):
        pass

    def _delete(self, path, name, deactivate=True):
        """
        Remove an entry from the database.

        Parameters
        ----------
        path: ``Path``
            Directory to use

        name: ``str``
            Name of the device, which informs the file name to find

        deactivate: ``bool``, optional
            If ``True``, we'll simply mark the preset as inactive. If
            ``False``, we'll permenantly remove it.
        """
        pass


class PresetPosition:
    """
    Manager for a single preset position.

    Parameters
    ----------
    presets: `Presets`
        The main `Presets` object that manages this position.

    name: ``str``
        The name of this preset position.
    """
    def __init__(self, presets, name):
        self._presets = presets
        self._name = name

    def update(self, pos=None):
        """
        Change this preset position and save it.

        Parameters
        ----------
        pos: ``float``, optional
            The position to use for this preset. If omitted, we'll use the
            current position.
        """
        if pos is None:
            self._presets._add_here(self._name)
        else:
            self._presets._add(self._name, pos)

    def delete(self, deactivate=True):
        """
        Remove this preset from the device. By default, this will only
        deactivate the name, not permenantly delete it.

        Parameters
        ----------
        deactivate: ``bool``, optional
            This can be changed to ``False`` to permenantly delete a preset
            instead of just deactivating it.
        """
        self._presets.delete(self._name, deactivate=deactivate)
