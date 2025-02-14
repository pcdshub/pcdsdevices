from __future__ import annotations

import logging
import re

import pydm
from pydm import Display
from qtpy import QtCore, QtWidgets
from typhos import utils

logger = logging.getLogger(__name__)


class _SmarActDetailedUI(QtWidgets.QWidget):
    """Annotations helper for SmarAct.detailed.ui. Do not instantiate."""
    # Status bar
    calibrated_bool: pydm.widgets.byte.PyDMByteIndicator
    has_encoder_bool: pydm.widgets.byte.PyDMByteIndicator
    referenced_bool: pydm.widgets.byte.PyDMByteIndicator
    # Open-loop tab
    jog_fwd_button: pydm.widgets.pushbutton.PyDMPushButton
    jog_rev_button: pydm.widgets.pushbutton.PyDMPushButton
    step_clear_cmd_button: pydm.widgets.pushbutton.PyDMPushButton
    total_step_count_rbv: pydm.widgets.label.PyDMLabel
    step_size_rbv: pydm.widgets.label.PyDMLabel
    step_size_set: pydm.widgets.line_edit.PyDMLineEdit
    step_volt_rbv: pydm.widgets.label.PyDMLabel
    step_volt_set: pydm.widgets.line_edit.PyDMLineEdit
    step_freq_rbv: pydm.widgets.label.PyDMLabel
    step_freq_set: pydm.widgets.line_edit.PyDMLineEdit
    scan_move_rbv: pydm.widgets.label.PyDMLabel
    scan_move_set: pydm.widgets.line_edit.PyDMLineEdit
    # Closed-loop tab
    home_forward_button: pydm.widgets.pushbutton.PyDMPushButton
    home_reverse_button: pydm.widgets.pushbutton.PyDMPushButton
    curr_pos_rbv: pydm.widgets.label.PyDMLabel
    curr_pos_set: pydm.widgets.line_edit.PyDMLineEdit
    home_velocity_rbv: pydm.widgets.label.PyDMLabel
    home_velocity_set: pydm.widgets.line_edit.PyDMLineEdit
    velocity_rbv: pydm.widgets.label.PyDMLabel
    velocity_set: pydm.widgets.line_edit.PyDMLineEdit
    velocity_base_rbv: pydm.widgets.label.PyDMLabel
    velocity_base_set: pydm.widgets.line_edit.PyDMLineEdit
    velocity_max_rbv: pydm.widgets.label.PyDMLabel
    velocity_max_set: pydm.widgets.line_edit.PyDMLineEdit
    acceleration_rbv: pydm.widgets.label.PyDMLabel
    acceleration_set: pydm.widgets.line_edit.PyDMLineEdit
    closed_loop_freq_max_rbv: pydm.widgets.label.PyDMLabel
    closed_loop_freq_max_set: pydm.widgets.line_edit.PyDMLineEdit
    # Diagnostics tab
    channel_temp_rbv: pydm.widgets.label.PyDMLabel
    module_temp_rbv: pydm.widgets.label.PyDMLabel
    motor_load_rbv: pydm.widgets.label.PyDMLabel
    chan_error_rbv: pydm.widgets.label.PyDMLabel
    diag_closed_loop_freq_max_rbv: pydm.widgets.label.PyDMLabel
    diag_closed_loop_freq_avg_rbv: pydm.widgets.label.PyDMLabel
    diag_closed_loop_freq_timebase_rbv: pydm.widgets.label.PyDMLabel
    channel_states: pydm.widgets.byte.PyDMByteIndicator
    # Config tab
    desc_rbv: pydm.widgets.label.PyDMLabel
    desc_set: pydm.widgets.line_edit.PyDMLineEdit
    egu_rbv: pydm.widgets.label.PyDMLabel
    egu_set: pydm.widgets.line_edit.PyDMLineEdit
    pos_type_rbv: pydm.widgets.label.PyDMLabel
    pos_type_set: pydm.widgets.line_edit.PyDMLineEdit
    needs_calib_led: pydm.widgets.byte.PyDMByteIndicator
    do_calib_button: pydm.widgets.pushbutton.PyDMPushButton
    low_limit_rbv: pydm.widgets.label.PyDMLabel
    low_limit_set: pydm.widgets.line_edit.PyDMLineEdit
    high_limit_rbv: pydm.widgets.label.PyDMLabel
    high_limit_set: pydm.widgets.line_edit.PyDMLineEdit
    ttzv_rbv: pydm.widgets.label.PyDMLabel
    ttzv_set: pydm.widgets.enum_combo_box.PyDMEnumComboBox
    ttzv_threshold_rbv: pydm.widgets.label.PyDMLabel
    ttzv_treshold_set: pydm.widgets.line_edit.PyDMLineEdit
    log_scale_offset_rbv: pydm.widgets.label.PyDMLabel
    log_scale_offset_set: pydm.widgets.line_edit.PyDMLineEdit
    log_scale_inversion_rbv: pydm.widgets.label.PyDMLabel
    log_scale_inversion_set: pydm.widgets.enum_combo_box.PyDMEnumComboBox
    def_range_min_rbv: pydm.widgets.label.PyDMLabel
    def_range_min_set: pydm.widgets.line_edit.PyDMLineEdit
    def_range_max_rbv: pydm.widgets.label.PyDMLabel
    def_range_max_set: pydm.widgets.line_edit.PyDMLineEdit
    dist_code_inversion_rbv: pydm.widgets.label.PyDMLabel
    dist_code_inversion_set: pydm.widgets.enum_combo_box.PyDMEnumComboBox
    # Misc
    controls_tabs: QtWidgets.QTabWidget
    pico_adjustment_prog_bar: QtWidgets.QProgressBar


class SmarActDetailedWidget(Display, utils.TyphosBase):
    """
    Custom widget for managing the SmarAct detailed screen
    """
    ui: _SmarActDetailedUI

    def __init__(self, parent=None, ui_filename='SmarAct.detailed.ui', **kwargs):
        super().__init__(parent=parent, ui_filename=ui_filename)

    @property
    def device(self):
        """The associated device."""
        try:
            return self.devices[0]
        except Exception:
            ...

    def add_device(self, device):
        """Typhos hook for adding a new device."""
        super().add_device(device)
        # Gotta make sure to destroy this screen if you were handed an empty device
        if device is None:
            self.ui.device_name_label.setText("(no device)")
            return

        self.post_typhos_init()

    def post_typhos_init(self):
        """
        Once typhos has relinked the device and parent widget, we need to clean
        Up some of the signals and maybe add new widgets to the display.
        Add any other init-esque shenanigans you need here.
        """
        self.fix_pvs()
        self.maybe_add_pico()
        self.add_tool_tips()

    def fix_pvs(self):
        """
        Fix all the channel access and signal linking to various pydm objects in the screen,
        since the macros aren't expanded when the UI is initialized.
        """
        object_names = self.find_pydm_names()
        for obj in object_names:
            _widget = getattr(self, obj)
            _channel = getattr(_widget, 'channel')
            if not _channel:
                _channel = ''
            if re.search(r'\{prefix\}', _channel):
                _widget.set_channel(_channel.replace('${prefix}', self.device.prefix))

        # Now let's manually add the funky egu and description signals here to avoid terminal spam
        self.desc_set.set_channel(f'sig://{self.device.name}_description')
        self.egu_set.set_channel(f'sig://{self.device.name}_motor_egu')

    def add_tool_tips(self):
        """
        Add hutch_python tooltips to label widgets, if they exist.
        """
        _signals = list(self.device.component_names)
        # Let's deal with the subdevice signals afterwards
        _signals.remove('open_loop')
        _open_loop_signals = list(self.device.open_loop.component_names)

        def _get_tooltip(device: any, signal: str) -> str:
            """
            Get the tooltip from the Ophyd.Device signal, if it exists.
            """
            _dotted_name = getattr(device, signal).dotted_name
            try:
                _tooltip = getattr(type(device), signal).doc
            except AttributeError:
                _tooltip = ''
            _tooltip = (_dotted_name + '<br>'
                        + round(1.75*len(_dotted_name))*'-' + '<br>'
                        + _tooltip)
            return _tooltip

        for sig in (_signals + _open_loop_signals):
            # Assume the QLabel's object name is standard form
            _label_name = sig + '_label'
            _device = self.device
            # open_loop is a component device, nests differently
            if sig in _open_loop_signals:
                _device = self.device.open_loop
            # Now let's add the tooltip for widgets that exist
            if hasattr(self, _label_name):
                _tooltip = _get_tooltip(_device, sig)
                getattr(self, _label_name).setToolTip(_tooltip)

    def find_pydm_names(self) -> list[str]:
        """
        Find the object names for all PyDM objects using findChildren

        Returns
        ------------
        result : list[str]
            1D list of object names
        """
        _button = pydm.widgets.pushbutton.PyDMPushButton
        _byte = pydm.widgets.byte.PyDMByteIndicator
        _label = pydm.widgets.label.PyDMLabel
        _line_edit = pydm.widgets.line_edit.PyDMLineEdit
        _combo_box = pydm.widgets.enum_combo_box.PyDMEnumComboBox

        result = []

        for obj_type in [_button, _byte, _label, _line_edit, _combo_box]:
            result += [obj.objectName() for obj in self.findChildren(obj_type)]

        # get rid of the objects from the embedded TyphosPositioner widget
        _omit = ['low_limit_switch', 'moving_indicator', 'high_limit_switch',
                 'low_limit', 'user_readback', 'error_label',
                 'high_limit', 'user_setpoint']

        return [obj for obj in result if obj not in _omit]

    def maybe_add_pico(self):
        """
        Maybe add the picoscale tab and signals _if_ they exist.
        Sadly involves a lot of manual signal management that would normally be
        handled in TyphosSignalPanel.
        """
        if hasattr(self.device, 'pico_exists'):
            if hasattr(self, 'picoscale'):
                # Don't add infite tabs please :]
                return
            # Only start this timer if PicoScale exists
            self.adj_prog_timer = QtCore.QTimer(parent=self)
            self.adj_prog_timer.timeout.connect(self.update_adj_prog)
            self.adj_prog_timer.setInterval(1000)
            self.adj_prog_timer.start()
            self._last_adj_prog = 0
            # Grab all the pico related signals
            _pico_signals = [sig for sig in self.device.component_names if 'pico' in sig]
            self.pico_signal_dict = {}
            # Grab any usable info from the HAPPI device and rebuild the JSON
            for sig in _pico_signals:
                _d = {}
                _sig = getattr(self.device, sig)
                _d['name'] = sig
                if hasattr(_sig, 'pvname'):
                    _d['read_pv'] = _sig.pvname
                if hasattr(_sig, 'setpoint_pvname'):
                    _d['write_pv'] = _sig.setpoint_pvname
                if hasattr(_sig, 'long_name'):
                    _d['label'] = _sig.long_name
                self.pico_signal_dict[sig] = _d

            # Now let's add some metadata for customizing the display
            _byte_sigs = ['pico_present', 'pico_exists', 'pico_valid', 'pico_enable', 'pico_stable', 'pico_adj_done']
            _enum_sigs = ['pico_adj_state']
            for sig in _byte_sigs:
                self.pico_signal_dict[sig]['meta'] = 'byte'
            for sig in _enum_sigs:
                self.pico_signal_dict[sig]['meta'] = 'enum'
            # Some exceptions that prove the rule
            self.pico_signal_dict['pico_curr_adj_prog']['meta'] = 'progressbar'

            # Last but not least, let me manually dictate the signal order
            _rows = ['pico_name', 'pico_present', 'pico_exists', 'pico_valid', 'pico_enable',
                     'pico_stable', 'pico_adj_done', 'pico_wmin', 'pico_wmax', 'pico_sig_qual',
                     'pico_adj_state', 'pico_curr_adj_prog']
            for pos, item in enumerate(_rows):
                self.pico_signal_dict[item]['row'] = pos

            # Generate the tab
            self.generate_pico_tab()

    def generate_pico_tab(self):
        """
        Gather all the pico related signals from the device and format the signal panel.
        A lot of this is recycled from TyphosSignalPanel with some alterations.
        """

        def add_signal_row(grid: QtWidgets.QGridLayout, signal_dict: dict):
            """
            Similar to the typhos method but allows for some manual overhauling.
            Bundles an EpicsSignal into a row of (Label, RBV widget, Setpoint widget)
            and adds it to a grid layout.

            Parameters
            ------------
                grid: QtWidgets.QGridLayout
                    The layout to add the signals to
                signal_dict: dict
                    A JSON-like dictionary of device signals, names, and metadata

            Returns
            ------------
            None
            """
            # Make the row label first
            row_label = QtWidgets.QLabel()
            row_label.setText(signal_dict['label'])
            # Set the object name as an attr for later shenanigans
            setattr(self, signal_dict['name'] + '_label', row_label)

            # Then set the RBV widget
            rbv_widget = pydm.widgets.label.PyDMLabel()
            rbv_widget.setAlignment(QtCore.Qt.AlignCenter)
            # Unless they're special
            if 'meta' in signal_dict:
                if signal_dict['meta'] == 'byte':
                    rbv_widget = pydm.widgets.byte.PyDMByteIndicator()
                    rbv_widget.circles = 1
                    rbv_widget.showLabels = 0
                if signal_dict['meta'] == 'progressbar':
                    rbv_widget = QtWidgets.QProgressBar()
                    rbv_widget.setRange(0, 100)
                    rbv_widget.hide()
                    row_label.hide()

            # Add the widget as an attr for later shenanigans
            setattr(self, signal_dict['name'] + '_rbv', rbv_widget)

            if hasattr(rbv_widget, 'set_channel'):
                rbv_widget.set_channel(signal_dict['read_pv'])

            # Create setpoint widgets if they exist
            if 'write_pv' in signal_dict:
                # handle tricky enums
                if 'meta' in signal_dict and signal_dict['meta'] == 'enum':
                    setpoint_widget = pydm.widgets.enum_combo_box.PyDMEnumComboBox()
                    setpoint_widget.set_channel(signal_dict['write_pv'])
                    # lean on HAPPI if possible
                    _signal_metadata = getattr(self.device, signal_dict['name']).metadata
                    if 'enum_strs' in _signal_metadata:
                        for item in _signal_metadata['enum_strs']:
                            setpoint_widget.addItem(item)
                    # Otherwise just give it some defaults
                    else:
                        for item in ['Disable', 'Enable']:
                            setpoint_widget.addItem(item)
                # Default line edits
                else:
                    setpoint_widget = pydm.widgets.line_edit.PyDMLineEdit()
                    setpoint_widget.set_channel(signal_dict['write_pv'])

                # Add the widget as an attr for later shenanigans
                setattr(self, signal_dict['name'] + '_set', setpoint_widget)

            # Now finally add these signals
            grid.addWidget(row_label, signal_dict['row'], 0)
            grid.addWidget(
                getattr(self, signal_dict['name'] + '_rbv'), signal_dict['row'], 1)
            if 'write_pv' in signal_dict:
                grid.addWidget(setpoint_widget, signal_dict['row'], 2)

        # Make the tab
        self.picoscale = QtWidgets.QWidget()
        # Format the scroll area
        pico_scroll_area = QtWidgets.QScrollArea()
        pico_scroll_area.setFrameStyle(QtWidgets.QFrame.NoFrame)
        pico_scroll_area.setWidget(self.picoscale)
        # Format the tab layout
        self.picoscale.layout = QtWidgets.QVBoxLayout()
        # Add signals
        self.picoscale.panel = QtWidgets.QGridLayout()
        for _d in self.pico_signal_dict:
            add_signal_row(self.picoscale.panel, self.pico_signal_dict[_d])
        # Set the layout and add to the tab widget
        self.picoscale.setLayout(self.picoscale.panel)
        self.controls_tabs.addTab(self.picoscale, 'Picoscale')

    def update_adj_prog(self):
        """
        Function for displaying and updating the QProgressBar when the PicoScale
        Auto-adjustment is taking place.
        """
        # Check to see if the system can even enter adjustment and display the bar
        if self.device.pico_adj_state.get():
            self.adj_prog_timer.start()
            if not self._last_adj_prog:
                self.pico_curr_adj_prog_rbv.show()
                self.pico_curr_adj_prog_label.show()
        # Then check to see if the progress has updated
        if self._last_adj_prog < self.device.pico_curr_adj_prog.get():
            self.pico_curr_adj_prog_rbv.setValue(self.device.pico_curr_adj_prog.get())
        # Now finally check to see if it is complete. Since the threaded behavior in the IOC
        # toggles the adjustment PV for ALL stages on a PicoScale when adjustment completes,
        # check for that state change too.
        if self.device.pico_adj_done.get() or not self.device.pico_adj_state.get():
            self.pico_curr_adj_prog_rbv.hide()
            self.pico_curr_adj_prog_rbv.reset()
            self.pico_curr_adj_prog_label.hide()
            # reset the timer too in case you need re-adjust later on
            self.adj_prog_timer.start()
