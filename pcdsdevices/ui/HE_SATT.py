from typing import Optional

from ophyd import Device
from pydm import Display
from qtpy.QtCore import QTimer
from typhos import utils

from pcdsdevices.attenuator import HE_SATT_Commands


class HeSattGUI(Display, utils.TyphosBase):
    def __init__(self, parent=None, ui_filename="HE_SATT.ui", macros=None, **kwargs):
        super().__init__(parent=parent, ui_filename=ui_filename, macros=macros, **kwargs)

        self.reset_and_request_timer = QTimer()
        self.ui.req_trans_edit_pydm.returnPressed.connect(self.reset_and_request_return_callback)
        self.ui.predicted_error_label_pydm.textChanged.connect(self.turn_big_error_red)
        self.ui.state_label_pydm.currentTextChanged.connect(self.turn_state_error_red)

    @property
    def device(self) -> Optional[Device]:
        """The associated device."""
        try:
            return self.devices[0]
        except Exception:
            ...

    def add_device(self, device):
        """Typhos hook for adding a new device."""
        super().add_device(device)
        self.add_channels()

    def add_channels(self):
        for cpt in self.device.walk_components():
            if cpt.item.cls is HE_SATT_Commands and len(cpt.ancestors) == 1:
                self.commands = getattr(self.device, cpt.dotted_name)

    def reset_and_request_return_callback(self):
        self.commands.reset.put(1)
        self.reset_and_request_timer.singleShot(1000, self.reset_and_request_timer_callback)

    def reset_and_request_timer_callback(self):
        self.commands.request_trans.put(1)

    def turn_big_error_red(self, text):
        if abs(float(text)) > 30:
            self.ui.predicted_error_label_pydm.setStyleSheet("background-color: red; color: white;")
        else:
            self.ui.predicted_error_label_pydm.setStyleSheet("background-color: rgb(11, 58, 232); color: white;")

    def turn_state_error_red(self, text):
        if text == "ERROR":
            self.ui.state_label_pydm.setStyleSheet("background-color: red; color: white;")
        else:
            self.ui.state_label_pydm.setStyleSheet("background-color: rgb(11, 58, 232); color: white;")
