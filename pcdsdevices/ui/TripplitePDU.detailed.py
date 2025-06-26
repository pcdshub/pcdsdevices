import pydm
import re

from pydm import Display

from qtpy import QtCore, QtWidgets
from typhos import utils
from epics import camonitor

class PDUDetailedWidget(Display, utils.TyphosBase):
    """
    Custom widget for managing the pdu detailed screen
    """

    def __init__(self, parent=None, ui_filename='TripplitePDU.detailed.ui', **kwargs):
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
        self.post_typhos_init()

    def post_typhos_init(self):
        """
        Once typhos has relinked the device and parent widget, we need to clean
        up some of the signals and maybe add new widgets to the display.
        Add any other init-esque shenanigans you need here.
        """
        self.fix_pvs()
        self.add_channels()


    def fix_pvs(self):
        """
        Reconnect PyDM widgets to the actual PVs from the device object.
        This is necessary because the macros aren't expanded during UI parsing.
        """

        # Get high-level overview widgets
        name_widget = self.ui.findChild(pydm.widgets.line_edit.PyDMLineEdit, "Channel_Name")
        name_widget.setReadOnly(False)
        status_widget = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Status_Label")
        location_widget = self.ui.findChild(pydm.widgets.line_edit.PyDMLineEdit, "Location_Label")
        location_widget.setReadOnly(False)

        # Get PDU details
        num_inputs = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Num_Input")
        num_outputs = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Num_Output")
        num_outlets = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Num_Outlet")
        num_groups = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Num_Group")
        num_phases = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Num_Phase")
        num_circuits = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Num_Circuit")
        num_breakers = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Num_Breaker")
        num_heatsinks = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Num_Heatsink")

        # Get input details
        input_f = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Input_F")
        input_v = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Input_V")
        input_v_min = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Input_V_Min")
        input_v_max = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Input_V_Max")

        # Get output details
        output_f = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Output_F")
        output_v = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Output_V")
        output_p = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Output_P")
        output_c = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Output_C")
        output_c_min = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Output_C_Min")
        output_c_max = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Output_C_Max")

        # Get control buttons
        on_btn = self.ui.findChild(pydm.widgets.pushbutton.PyDMPushButton, 'All_On_Button')
        off_btn = self.ui.findChild(pydm.widgets.pushbutton.PyDMPushButton, 'All_Off_Button')
        reboot_btn = self.ui.findChild(pydm.widgets.pushbutton.PyDMPushButton, 'Reboot_All_Button')

        # Set control button
        if on_btn:
            on_btn.channel = f"ca://{self.device.channels_on.pvname}"
            on_btn.pressValue = 1
        if off_btn:
            off_btn.channel = f"ca://{self.device.channels_off.pvname}"
            off_btn.pressValue = 1
        if reboot_btn:
            reboot_btn.channel = f"ca://{self.device.channels_reboot.pvname}"
            reboot_btn.pressValue = 1


        # Set PDU data
        if name_widget:
            name_widget.channel = f"ca://{self.device.pdu_name.pvname}"
        if status_widget:
            status_widget.channel = f"ca://{self.device.pdu_status.pvname}"
        if location_widget:
            location_widget.channel = f"ca://{self.device.pdu_location.pvname}"
        if num_inputs:
            num_inputs.channel = f"ca://{self.device.pdu_num_inputs.pvname}"
        if num_outputs:
            num_outputs.channel = f"ca://{self.device.pdu_num_outputs.pvname}"
        if num_outlets:
            num_outlets.channel = f"ca://{self.device.pdu_num_outlets.pvname}"
        if num_groups:
            num_groups.channel = f"ca://{self.device.pdu_num_groups.pvname}"
        if num_phases:
            num_phases.channel = f"ca://{self.device.pdu_num_phases.pvname}"
        if num_circuits:
            num_circuits.channel = f"ca://{self.device.pdu_num_circuits.pvname}"
        if num_breakers:
            num_breakers.channel = f"ca://{self.device.pdu_num_breakers.pvname}"
        if num_heatsinks:
            num_heatsinks.channel = f"ca://{self.device.pdu_num_heatsinks.pvname}"

        # PVs that need scalling
        if input_f:
            self.monitor_pv_to_label(input_f, self.device.pdu_input_f.pvname, scale=0.1)
        if input_v:
            self.monitor_pv_to_label(input_v, self.device.pdu_input_v.pvname, scale=0.1)
        if input_v_min:
            self.monitor_pv_to_label(input_v_min, self.device.pdu_input_v_min.pvname, scale=0.1)
        if input_v_max:
            self.monitor_pv_to_label(input_v_max, self.device.pdu_input_v_max.pvname, scale=0.1)
        if output_f:
            self.monitor_pv_to_label(output_f, self.device.pdu_output_f.pvname, scale=0.1)
        if output_v:
            self.monitor_pv_to_label(output_v, self.device.pdu_output_v.pvname, scale=0.1)
        if output_p:
            self.monitor_pv_to_label(output_p, self.device.pdu_output_p.pvname, scale=1.0)
        if output_c:
            self.monitor_pv_to_label(output_c, self.device.pdu_output_c.pvname, scale=0.1)
        if output_c_min:
            self.monitor_pv_to_label(output_c_min, self.device.pdu_output_c_min.pvname, scale=0.1)
        if output_c_max:
            self.monitor_pv_to_label(output_c_max, self.device.pdu_output_c_max.pvname, scale=0.1)


    def add_channels(self):
        """
        Find all attributes of the PDU that start with the name 'channel'
        Append them and their signals to a dictionary, then call the
        function responsible for adding them to the layout
        """
        self.channel_signal_dict = {}

        for attr in dir(self.device):
            if attr.startswith("channel"):
                ch_obj = getattr(self.device, attr, None)
                if ch_obj is None or not all(hasattr(ch_obj, k) for k in ('ch_index', 'ch_name', 'ch_status', 'ch_ctrl_state', 'ch_ctrl_command')):
                    continue

                self.channel_signal_dict[attr] = {
                    'ch_index': ch_obj.ch_index.pvname,
                    'ch_name': ch_obj.ch_name.pvname,
                    'ch_status': ch_obj.ch_status.pvname,
                    'ch_ctrl_state': ch_obj.ch_ctrl_state.pvname,
                    'ch_ctrl_command': ch_obj.ch_ctrl_command.pvname,
                }
        """
        If we have a PDU with more than 8 channels, the rows will sort lexigraphically
        by channel (i.e 10 comes before 1). Force it to conform with some shenanigans
        """
        self.channel_signal_dict_sorted = dict(sorted(self.channel_signal_dict.items(), key=lambda item: self.extract_outlet_number(item[1]['ch_index'])))
        self.generate_rows()


    def generate_rows(self):
        """
        Format each ophyd pdu channel component into a row and append to the layout.
        Split channels into two collumns to keep the screen from growing length-wise
        """
        def add_channel_row(layout, ch_info):
            row_layout = QtWidgets.QHBoxLayout()

            # Index label
            idx_label = pydm.widgets.label.PyDMLabel()
            idx_label.channel = f"ca://{ch_info['ch_index']}"
            idx_label.setAlignment(QtCore.Qt.AlignCenter)
            row_layout.addWidget(idx_label, 1)

            # Name
            name_edit = pydm.widgets.line_edit.PyDMLineEdit()
            name_edit.channel = f"ca://{ch_info['ch_name']}"
            name_edit.setReadOnly(False)
            name_edit.setAlignment(QtCore.Qt.AlignCenter)
            row_layout.addWidget(name_edit, 8)

            # Status
            status = pydm.widgets.label.PyDMLabel()
            status.channel = f"ca://{ch_info['ch_status']}"
            status.setAlignment(QtCore.Qt.AlignCenter)
            row_layout.addWidget(status, 2)

            # Ctrl atate
            ctrl_state = pydm.widgets.label.PyDMLabel()
            ctrl_state.channel = f"ca://{ch_info['ch_ctrl_state']}"
            ctrl_state.setAlignment(QtCore.Qt.AlignCenter)
            row_layout.addWidget(ctrl_state, 2)

            # Command enum
            cmd = pydm.widgets.enum_combo_box.PyDMEnumComboBox()
            cmd.channel = f"ca://{ch_info['ch_ctrl_command']}"
            row_layout.addWidget(cmd, 2)

            row_widget = QtWidgets.QWidget()
            row_widget.setLayout(row_layout)
            layout.addWidget(row_widget)

        left_layout = self.ui.Left_Channels
        right_layout = self.ui.Right_Channels

        # Clear layouts
        for layout in (left_layout, right_layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        # Split channels
        ch_list = list(self.channel_signal_dict.values())
        midpoint = len(ch_list) // 2
        left_half = ch_list[:midpoint]
        right_half = ch_list[midpoint:]

        for ch in left_half:
            add_channel_row(left_layout, ch)
        for ch in right_half:
            add_channel_row(right_layout, ch)


    def monitor_pv_to_label(self, label, pvname, scale=1.0, precision=1):
        """
        Subscribe the PV, as saved in the ophyd component, to an EPICS
        monitor that executes a function to scale its value and assign
        it to the cooresponding widget's text. This works around using
        the channel property in these widgets, which to the best of
        my knowledge does not support scalling.
        """
        def on_change(pvname=None, value=None, **kwargs):
            if value is not None:
                label.setText(f"{value * scale:.{precision}f}")
            else:
                label.setText("--")

        # Register the monitor
        camonitor(pvname, callback=on_change)

    def extract_outlet_number(self, pvname):
        """
        Helper function for sorting the channel dictionaries
        """
        match = re.search(r':Outlet:(\d+):', pvname)
        return int(match.group(1)) if match else float('inf')
