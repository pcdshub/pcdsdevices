import pydm
import re

from pydm import Display
from os import path

from pydm.widgets import PyDMEmbeddedDisplay
from qtpy import QtCore, QtWidgets
from typhos import utils

class PDUDetailedWidget(Display, utils.TyphosBase):
    """
    Custom widget for managing the pdu detailed screen
    """

    def __init__(self, parent=None, ui_filename='PDU.detailed.ui', **kwargs):
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
        Up some of the signals and maybe add new widgets to the display.
        Add any other init-esque shenanigans you need here.
        """
        self.fix_pvs()
        self.add_channels()


    def fix_pvs(self):
        """
        Reconnect PyDM widgets to the actual PVs from the device object.
        This is necessary because the macros aren't expanded during UI parsing.
        I'm doing this manually for now, as this screen expands with more signals,
        I will make use of find_pydm_names()
        """

        # High-level overview data
        name_widget = self.ui.findChild(pydm.widgets.line_edit.PyDMLineEdit, "Channel_Name")
        name_widget.setReadOnly(False)
        status_widget = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Status_Label")
        location_widget = self.ui.findChild(pydm.widgets.line_edit.PyDMLineEdit, "Location_Label")
        name_widget.setReadOnly(False)

        # Sensor data and threshholds
        sensor1_id = self.ui.findChild(pydm.widgets.label.PyDMLabel, "S1_ID")
        sensor1_name = self.ui.findChild(pydm.widgets.label.PyDMLabel, "S1_Status")
        sensor1_temp = self.ui.findChild(pydm.widgets.label.PyDMLabel, "S1_Temp")
        sensor1_humid = self.ui.findChild(pydm.widgets.label.PyDMLabel, "S1_Hum")
        sensor2_id = self.ui.findChild(pydm.widgets.label.PyDMLabel, "S2_ID")
        sensor2_name = self.ui.findChild(pydm.widgets.label.PyDMLabel, "S2_Status")
        sensor2_temp = self.ui.findChild(pydm.widgets.label.PyDMLabel, "S2_Temp")
        sensor2_humid = self.ui.findChild(pydm.widgets.label.PyDMLabel, "S2_Hum")

        temp_lo = self.ui.findChild(pydm.widgets.line_edit.PyDMLineEdit, "Temp_Lo")
        temp_hi = self.ui.findChild(pydm.widgets.line_edit.PyDMLineEdit, "Temp_Hi")
        humid_lo = self.ui.findChild(pydm.widgets.line_edit.PyDMLineEdit, "Hum_Lo")
        humid_hi = self.ui.findChild(pydm.widgets.line_edit.PyDMLineEdit, "Hum_Hi")

        # Input/output details:
        output_c = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Infeed_Load")
        output_c_max = self.ui.findChild(pydm.widgets.line_edit.PyDMLineEdit, "Infeed_Load_Threshhold")
        output_c_status = self.ui.findChild(pydm.widgets.label.PyDMLabel, "Infeed_Status")
        output_p = self.ui.findChild(pydm.widgets.label.PyDMLabel, "PDU_Power")

        if name_widget:
            name_widget.channel = f"ca://{self.device.pdu_name.pvname}"
        if status_widget:
            status_widget.channel = f"ca://{self.device.pdu_status.pvname}"
        if location_widget:
            location_widget.channel = f"ca://{self.device.pdu_location.pvname}"
        if sensor1_id:
            sensor1_id.channel = f"ca://{self.device.pdu_sensor1_id.pvname}"
        if sensor1_name:
            sensor1_name.channel = f"ca://{self.device.pdu_sensor1_status.pvname}"
        if sensor1_temp:
            sensor1_temp.channel = f"ca://{self.device.pdu_sensor1_temperature.pvname}"
        if sensor1_humid:
            sensor1_humid.channel = f"ca://{self.device.pdu_sensor1_humidity.pvname}"
        if sensor2_id:
            sensor2_id.channel = f"ca://{self.device.pdu_sensor2_id.pvname}"
        if sensor2_name:
            sensor2_name.channel = f"ca://{self.device.pdu_sensor2_status.pvname}"
        if sensor2_temp:
            sensor2_temp.channel = f"ca://{self.device.pdu_sensor2_temperature.pvname}"
        if sensor2_humid:
            sensor2_humid.channel = f"ca://{self.device.pdu_sensor2_humidity.pvname}"
        if temp_lo:
            temp_lo.channel = f"ca://{self.device.pdu_temperature_lo.pvname}"
        if temp_hi:
            temp_hi.channel = f"ca://{self.device.pdu_temperature_hi.pvname}"
        if humid_lo:
            humid_lo.channel = f"ca://{self.device.pdu_humidity_lo.pvname}"
        if humid_hi:
            humid_hi.channel = f"ca://{self.device.pdu_humidity_hi.pvname}"
        if output_c:
            output_c.channel = f"ca://{self.device.pdu_output_c.pvname}"
        if output_c_max:
            output_c_max.channel = f"ca://{self.device.pdu_output_c_max.pvname}"
        if output_c_status:
            output_c_status.channel = f"ca://{self.device.pdu_output_c_status.pvname}"
        if output_p:
            output_p.channel = f"ca://{self.device.pdu_output_p.pvname}"


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
                if ch_obj is None or not all(hasattr(ch_obj, k) for k in ('ch_index', 'ch_name', 'ch_status', 'ch_ctrl_state')):
                    continue
                self.channel_signal_dict[attr] = {
                    'ch_index': ch_obj.ch_index.pvname,
                    'ch_name': ch_obj.ch_name.pvname,
                    'ch_status': ch_obj.ch_status.pvname,
                    'ch_ctrl_state': ch_obj.ch_ctrl_state.pvname
                }
        """
        If we have a PDU with more than 8 channels, the rows will sort lexigraphically
        by channel (ex: 10 comes before 1). Force it to conform with some shenanigans
        """
        self.channel_signal_dict_sorted = dict(sorted(self.channel_signal_dict.items(), key=lambda item: self.order_channels(item[1]['ch_index'])))
        self.generate_rows()


    def generate_rows(self):
        """
        Format each ophyd pdu channel component into a row and append to the layout.
        Split channels into two collumns to keep the screen from growing length-wise
        """
        def add_channel_row(layout, ch_info, ch_obj):
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

            """
            Command combo box
            This would be a pydm enum combo box but the Epics record is not a mbbo. I need to
            do more schenanigans to wrap this in one widget. I connect it to a helper function for
            setting the appropriate command component on the pdu channel
            """
            cmd = QtWidgets.QComboBox()
            cmd.wheelEvent = lambda event: None  # This disables scrolling on the widget to stop people from accidentally turning channels off
            cmd.addItems(["Idle", "Turn On", "Turn Off", "Cycle"])

            def on_action_selected(index):
                if index == 1:
                    ch_obj.ch_ctrl_command_on.put(1)
                elif index == 2:
                    ch_obj.ch_ctrl_command_off.put(2)
                elif index == 3:
                    ch_obj.ch_ctrl_command_reboot.put(3)

            cmd.currentIndexChanged.connect(on_action_selected)
            row_layout.addWidget(cmd)

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
        ch_list = list(self.channel_signal_dict_sorted.items())
        midpoint = len(ch_list) // 2
        left_half = ch_list[:midpoint]
        right_half = ch_list[midpoint:]

        # Reminder that left and right half are dicitonaries with entries: (<string name of channel attribute>, <dict of channel attributes>)
        for ch, ch_info in left_half:
            ch_obj = getattr(self.device, ch)
            add_channel_row(left_layout, ch_info, ch_obj)
        for ch, ch_info in right_half:
            ch_obj = getattr(self.device, ch)
            add_channel_row(right_layout, ch_info, ch_obj)

    def order_channels(self, pvname):
        """
        Helper function for sorting the channel dictionaries
        """
        match = re.search(r':Outlet:(\d+):', pvname)
        return int(match.group(1)) if match else float('inf')
