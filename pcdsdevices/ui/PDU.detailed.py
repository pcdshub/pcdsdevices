import re

import pydm
from epics import PV
from pydm import Display
from qtpy import QtCore, QtWidgets
from typhos import utils

from pcdsdevices.pdu import PDUChannel


class PDUDetailedWidget(Display, utils.TyphosBase):
    """
    Custom widget for managing the pdu detailed screen
    """

    def __init__(self, parent=None, ui_filename='PDU.detailed.ui', macros=None, **kwargs):
        super().__init__(parent=parent, ui_filename=ui_filename, macros=macros, **kwargs)

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

        # Alarm color callbacks
        status_widget = self.ui.Status_Label
        if status_widget:
            self.update_color(status_widget, self.device.status.pvname)

        self.add_channels()

    def add_channels(self):
        """
        Find all attributes of the PDU that start with the name 'channel'
        Append them and their signals to a dictionary, then call the
        function responsible for adding them to the layout
        """
        self.channel_signal_dict = {}

        for cpt in self.device.walk_components():
            # Get top level channel components
            if cpt.item.cls is PDUChannel and len(cpt.ancestors) == 1:
                # Get the actual device instance using the dotted name
                ch_obj = getattr(self.device, cpt.dotted_name)
                # add to the dictionary
                self.channel_signal_dict[cpt.dotted_name] = {
                    'ch_index': ch_obj.ch_index.pvname,
                    'ch_name': ch_obj.ch_name.pvname,
                    'ch_status': ch_obj.ch_status.pvname,
                    'ch_ctrl_state': ch_obj.ch_ctrl_state.pvname
                }
        # If we have a PDU with more than 8 channels, the rows will sort lexigraphically
        # by channel (ex: 10 comes before 1). Force it to conform with some shenanigans
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

            # Ctrl state
            ctrl_state = pydm.widgets.label.PyDMLabel()
            ctrl_state.channel = f"ca://{ch_info['ch_ctrl_state']}"
            ctrl_state.setAlignment(QtCore.Qt.AlignCenter)
            row_layout.addWidget(ctrl_state, 2)

            # Alarm color callback
            self.update_color(ctrl_state, ch_info['ch_status'])
            self.update_color(status, ch_info['ch_status'])

            # Command combo box
            # This would be a pydm enum combo box but the Epics record is not a mbbo. I need to
            # do more schenanigans to wrap this in one widget. I connect it to a helper function for
            # setting the appropriate command component on the pdu channel

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

        # I need to resize the window after the scroll widget is populated, or else the screen will cuttoff all the channels
        # I Encapsulate in a function so I can add a delay, Qt needs time to draw everything to screen before I resize
        def delayed_resize():
            current_width = self.width()
            top_window = self.window()
            top_window.resize(current_width, 700)

        QtCore.QTimer.singleShot(100, delayed_resize)

    def order_channels(self, pvname):
        """
        Helper function for sorting the channel dictionaries
        """
        match = re.search(r':Outlet:(\d+):', pvname)
        return int(match.group(1)) if match else float('inf')

    def update_color(self, label, pvname):
        """
        Monitor PV severity to update a widget whenever an alarm is active. I use PV instead of
        camonitor because I noticed issues where the color wouldn't update. I believe camonitor
        grabs from chached metadata despite updating the PV value, resulting in the incorrect color
        being applied. Using PV updates the metadata, not just the PV's value (from what I can tell)

        label: str
            The widget you want to have update its color
        pvname: str
            The alarm PV that should trigger a color change
        """
        def on_change(value=None, **kwargs):
            severity = kwargs.get("severity")
            if severity == 2:
                label.setStyleSheet("background-color: red; color: black")
            elif severity == 1:
                label.setStyleSheet("background-color: yellow; color: black")
            else:
                label.setStyleSheet("background-color: #0b3ae8; color: white")

        # Set the call back
        pv = PV(pvname)
        pv.add_callback(on_change)
