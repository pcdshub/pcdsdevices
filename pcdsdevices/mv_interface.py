"""
Module for defining bell-and-whistles movement features
"""
import time
import fcntl
import logging
import numbers
import signal
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace, MethodType

import yaml

from bluesky.utils import ProgressBar
from ophyd.status import wait as status_wait

logger = logging.getLogger(__name__)


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
        Dispatches to `mv` or `wm` based on the arguments.

        Calling the object will either move the object or get the current
        position, depending on if the position argument is given. See the
        docstrings for `mv` and `wm`.
        """
        if position is None:
            return self.wm()
        else:
            self.mv(position, timeout=timeout, wait=wait)

    def camonitor(self):
        """
        Updates current position of the motor.
        """
        try:
            while True:
                print("\r {0:4f}".format(self.position), end=" ")
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass


class FltMvInterface(MvInterface):
    """
    Extension of `MvInterface` for when the position is a ``float``.

    This lets us do more with the interface, such as relative moves.

    Attributes
    ----------
    presets: `Presets`
        Manager for preset positions.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.presets = Presets(self)

    def mvr(self, delta, timeout=None, wait=False):
        """
        Relative move from this position.

        Parameters
        ----------
        delta: ``float``
            Desired change in position

        timeout: ``float``, optional
            If provided, the mover will throw an error if motion takes longer
            than timeout to complete. If omitted, the mover's default timeout
            will be use.

        wait: ``bool``, optional
            If ``True``, wait for motion completion before returning. Defaults
            to ``False``.
        """
        self.mv(delta + self.wm(), timeout=timeout, wait=wait)

    def umv(self, position, timeout=None):
        """
        Move to a position, wait, and update with a progress bar.

        Parameters
        ----------
        position: ``float``
            Desired end position

        timeout: ``float``, optional
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
        delta: ``float``
            Desired change in position

        timeout: ``float``, optional
            If provided, the mover will throw an error if motion takes longer
            than timeout to complete. If omitted, the mover's default timeout
            will be use.
        """
        self.umv(delta + self.wm(), timeout=timeout)


def setup_preset_paths(**paths):
    """
    Prepare the `Presets` class.

    Sets the paths for saving and loading presets.

    Parameters
    ----------
    **paths: ``str`` keyword args
        A mapping from type of preset to destination path. These will be
        directories that contain the yaml files that define the preset
        positions.
    """
    Presets._paths = {}
    for k, v in paths.items():
        Presets._paths[k] = Path(v)
    for preset in Presets._registry.values():
        preset.sync()


class Presets:
    """
    Manager for device preset positions.

    This provides methods for adding new presets, checking which presets are
    active, and related utilities.

    It will install the ``mv_presetname`` and ``wm_presetname`` methods onto
    the associated device, and the ``add_preset`` and ``add_preset_here``
    methods onto itself.

    Parameters
    ----------
    device: ``Device``
        The device to manage saved preset positions for. It must implement the
        `FltMvInterface`.

    Attributes
    ----------
    positions: ``SimpleNamespace``
        A namespace that contains all of the active presets as `PresetPosition`
        objects.
    """
    _registry = {}
    _paths = {}

    def __init__(self, device):
        self._device = device
        self._methods = []
        self._fd = None
        self._registry[device.name] = self
        self.name = device.name + '_presets'
        self.sync()

    def _path(self, preset_type):
        """
        Utility function to get the preset file ``Path``.
        """
        path = self._paths[preset_type] / (self._device.name + '.yml')
        logger.debug('select presets path %s', path)
        return path

    def _read(self, preset_type):
        """
        Utility function to get a particular preset's datum dictionary.
        """
        logger.debug('read presets for %s', self._device.name)
        with self._file_open_rlock(preset_type) as f:
            f.seek(0)
            return yaml.load(f) or {}

    def _write(self, preset_type, data):
        """
        Utility function to overwrite a particular preset's datum dictionary.
        """
        logger.debug('write presets for %s', self._device.name)
        with self._file_open_rlock(preset_type) as f:
            f.seek(0)
            yaml.dump(data, f, default_flow_style=False)
            f.truncate()

    @contextmanager
    def _file_open_rlock(self, preset_type, timeout=1.0):
        """
        File locking context manager for this object.

        Works like threading.Rlock in that you can acquire it multiple times
        safely.

        Parameters
        ----------
        fd: ``file``
            The file descriptor to lock on.

        Raises
        ------
        BlockingIOError:
            If we cannot acquire the file lock.
        """
        if self._fd is None:
            path = self._path(preset_type)
            with open(path, 'r+') as fd:
                # Set up file lock timeout with a raising handler
                # We will need this handler due to PEP 475
                def interrupt(signum, frame):
                    raise InterruptedError()

                old_handler = signal.signal(signal.SIGALRM, interrupt)
                try:
                    signal.setitimer(signal.ITIMER_REAL, timeout)
                    fcntl.flock(fd, fcntl.LOCK_EX)
                except InterruptedError:
                    # Ignore interrupted and proceed to cleanup
                    pass
                finally:
                    # Clean up file lock timeout
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    signal.signal(signal.SIGALRM, old_handler)
                # Error now if we still can't get the lock.
                # Getting lock twice is safe.
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.debug('acquired lock for %s', path)
                self._fd = fd
                yield fd
                fcntl.flock(fd, fcntl.LOCK_UN)
                logger.debug('released lock for %s', path)
            self._fd = None
        else:
            logger.debug('using already open file descriptor')
            yield self._fd

    def _update(self, preset_type, name, value=None, comment=None,
                active=True):
        """
        Utility function to update a preset position.

        Reads the existing preset's datum, updates the value the comment, and
        the active state, and then writes the datum back to the file, updating
        the history accordingly.
        """
        logger.debug(('call %s presets._update(%s, %s, value=%s, comment=%s, '
                      'active=%s)'), self._device.name, preset_type, name,
                     value, comment, active)
        if not isinstance(name, str):
            raise TypeError(('name must be of type <str>, not type'
                             '{}'.format(type(name))))
        if value is not None and not isinstance(value, numbers.Real):
            raise TypeError(('value must be a real numeric type, not type'
                             '{}'.format(type(value))))
        try:
            path = self._path(preset_type)
            if not path.exists():
                path.touch()
                path.chmod(0o666)
            with self._file_open_rlock(preset_type):
                data = self._read(preset_type)
                if value is None and comment is not None:
                    value = data[name]['value']
                if value is not None:
                    if name not in data:
                        data[name] = {}
                    ts = time.strftime('%d %b %Y %H:%M:%S')
                    data[name]['value'] = value
                    history = data[name].get('history', {})
                    if comment:
                        comment = ' ' + comment
                    else:
                        comment = ''
                    history[ts] = '{:10.4f}{}'.format(value, comment)
                    data[name]['history'] = history
                if active:
                    data[name]['active'] = True
                else:
                    data[name]['active'] = False
                self._write(preset_type, data)
        except BlockingIOError:
            self._log_flock_error()

    def sync(self):
        """
        Synchronize the presets with the database.
        """
        logger.debug('call %s presets.sync()', self._device.name)
        self._remove_methods()
        self._cache = {}
        logger.debug('filling %s cache', self.name)
        for preset_type in self._paths.keys():
            path = self._path(preset_type)
            if path.exists():
                try:
                    self._cache[preset_type] = self._read(preset_type)
                except BlockingIOError:
                    self._log_flock_error()
            else:
                logger.debug('No %s preset file for %s',
                             preset_type, self._device.name)
        self._create_methods()

    def _log_flock_error(self):
        logger.error(('Unable to acquire file lock for %s. '
                      'File may be being edited by another user.'), self.name)
        logger.debug('', exc_info=True)

    def _create_methods(self):
        """
        Create the dynamic methods based on the configured paths.

        Add methods to this object for adding presets of each type, add
        methods to the associated device to move and check each preset, and
        add `PresetPosition` instances to ``self.positions`` for each preset
        name.
        """
        logger.debug('call %s presets._create_methods()', self._device.name)
        for preset_type in self._paths.keys():
            add, add_here = self._make_add(preset_type)
            self._register_method(self, 'add_' + preset_type, add)
            self._register_method(self, 'add_here_' + preset_type, add_here)
        for preset_type, data in self._cache.items():
            for name, info in data.items():
                if info['active']:
                    mv, umv = self._make_mv_pre(preset_type, name)
                    wm = self._make_wm_pre(preset_type, name)
                    self._register_method(self._device, 'mv_' + name, mv)
                    self._register_method(self._device, 'umv_' + name, umv)
                    self._register_method(self._device, 'wm_' + name, wm)
                    setattr(self.positions, name,
                            PresetPosition(self, preset_type, name))

    def _register_method(self, obj, method_name, method):
        """
        Utility function for managing dynamic methods.

        Adds a method to the ``_methods`` list and binds the method to an
        object.
        """
        logger.debug('register method %s to %s', method_name, obj.name)
        self._methods.append((obj, method_name))
        setattr(obj, method_name, MethodType(method, obj))

    def _make_add(self, preset_type):
        """
        Create the functions that add preset positions.

        Creates suitable versions of ``add`` and ``add_here`` for a particular
        preset type, e.g. ``add_preset_type`` and ``add_here_preset_type``.
        """
        def add(self, name, value, comment=None):
            """
            Add a preset position of type "{}".

            Parameters
            ----------
            name: ``str``
                The name of the new preset position.

            value: ``float``
                The value of the new preset_position.

            comment: ``str``, optional
                A comment to associate with the preset position.
            """
            self._update(preset_type, name, value=value,
                         comment=comment)
            self.sync()

        def add_here(self, name, comment=None):
            """
            Add a preset of the current position of type "{}".

            Parameters
            ----------
            name: ``str``
                The name of the new preset position.

            comment: ``str``, optional
                A comment to associate with the preset position.
            """
            add(self, name, self._device.wm(), comment=comment)

        add.__doc__ = add.__doc__.format(preset_type)
        add_here.__doc__ = add_here.__doc__.format(preset_type)
        return add, add_here

    def _make_mv_pre(self, preset_type, name):
        """
        Create the functions that move to preset positions.

        Creates a suitable versions of ``mv`` and ``umv`` for a particular
        preset type and name e.g. ``mv_sample``.
        """
        def mv_pre(self, timeout=None, wait=False):
            """
            Move to the {} preset position.

            Parameters
            ----------
            timeout: ``float``, optional
                If provided, the mover will throw an error if motion takes
                longer than timeout to complete. If omitted, the mover's
                default timeout will be use.

            wait: ``bool``, optional
                If ``True``, wait for motion completion before returning.
                Defaults to ``False``.
            """
            pos = self.presets._cache[preset_type][name]['value']
            self.mv(pos, timeout=timeout, wait=wait)

        def umv_pre(self, timeout=None):
            """
            Update move to the {} preset position.

            Parameters
            ----------
            timeout: ``float``, optional
                If provided, the mover will throw an error if motion takes
                longer than timeout to complete. If omitted, the mover's
                default timeout will be use.
            """
            pos = self.presets._cache[preset_type][name]['value']
            self.umv(pos, timeout=timeout)

        mv_pre.__doc__ = mv_pre.__doc__.format(name)
        umv_pre.__doc__ = umv_pre.__doc__.format(name)
        return mv_pre, umv_pre

    def _make_wm_pre(self, preset_type, name):
        """
        Create a method to get the offset from a preset position.

        Creates a suitable version of ``wm`` for a particular preset type and
        name e.g. ``wm_sample``.
        """
        def wm_pre(self):
            """
            Check the offset from the {} preset position.

            Returns
            -------
            offset: ``float``
                How far we are from the preset position. If this is near zero,
                we are at the position. If this positive, the preset position
                is in the positive direction from us.
            """
            pos = self.presets._cache[preset_type][name]['value']
            return pos - self.wm()

        wm_pre.__doc__ = wm_pre.__doc__.format(name)
        return wm_pre

    def _remove_methods(self):
        """
        Remove all methods created in the last call to _create_methods.
        """
        logger.debug('call %s presets._remove_methods()', self._device.name)
        for obj, method_name in self._methods:
            try:
                delattr(obj, method_name)
            except AttributeError:
                pass
        self._methods = []
        self.positions = SimpleNamespace()


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
    def __init__(self, presets, preset_type, name):
        self._presets = presets
        self._preset_type = preset_type
        self._name = name

    def update_pos(self, pos=None, comment=None):
        """
        Change this preset position and save it.

        Parameters
        ----------
        pos: ``float``, optional
            The position to use for this preset. If omitted, we'll use the
            current position.

        comment: ``str``, optional
            A comment to associate with the preset position.
        """
        if pos is None:
            pos = self._presets._device.wm()
        self._presets._update(self._preset_type, self._name, value=pos,
                              comment=comment)
        self._presets.sync()

    def update_comment(self, comment):
        """
        Revise the most recent comment in the preset history.

        Parameters
        ----------
        comment: ``str``
            A comment to associate with the preset position.
        """
        self._presets._update(self._preset_type, self._name, comment=comment)
        self._presets.sync()

    def deactivate(self):
        """
        Deactivate a preset from a device.

        This can always be undone unless you edit the underlying file.
        """
        self._presets._update(self._preset_type, self._name, active=False)
        self._presets.sync()

    @property
    def info(self):
        """
        All information associated with this preset.

        Returns
        -------
        info: ``dict``
        """
        return self._presets._cache[self._preset_type][self._name]

    @property
    def pos(self):
        """
        The set position of this preset.

        Returns
        -------
        pos: ``float``
        """
        return self.info['value']

    @property
    def history(self):
        """
        This position history associated with this preset.

        Returns
        -------
        history: ``dict``
        """
        return self.info['history']

    @property
    def path(self):
        """
        The filepath that defines this preset.

        Returns
        -------
        path: ``str``
        """
        return str(self._presets._path(self._preset_type))

    def __repr__(self):
        return str(self.pos)
