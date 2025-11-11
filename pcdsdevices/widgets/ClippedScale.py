import numpy as np
from pydm.widgets.scale import PyDMScaleIndicator


class ClippedScale(PyDMScaleIndicator):

    def value_changed(self, new_value: float) -> None:
        if new_value is not None:
            super().value_changed(np.clip(new_value,
                                          self.scale_indicator._lower_limit,
                                          self.scale_indicator._upper_limit
                                          )
                                  )
