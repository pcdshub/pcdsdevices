from __future__ import annotations

import logging

from pydm import Display
from typhos import utils

from pcdsdevices.widgets.qmini import QminiBase

logger = logging.getLogger(__name__)


class QminiSpectrometerDetailedUI(QminiBase, Display, utils.TyphosBase):
    """
    Custom widget for managing the SmarAct detailed screen

    NOTE: inherit QminiBase FIRST so that the mro resolves it LAST
    """

    def __init__(self, parent=None, ui_filename='QminiSpectrometer.detailed.ui', **kwargs):
        super().__init__(parent=parent, ui_filename=ui_filename)
