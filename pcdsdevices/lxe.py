"""
'lxe' position / pulse energy pseudopositioner support.

Notes
-----
OPA::

    An optical parametric amplifier, abbreviated OPA, is a laser light source
    that emits light of variable wavelengths by an optical parametric
    amplification process. It is essentially the same as an optical parametric
    oscillator, but without the optical cavity, that is, the light beams pass
    through the apparatus just once or twice, rather than many many times.

las_comp_wp::

    Laser compressor waveplate

las_pol_wp::

    Laser polarizer waveplate

LXE::

    Laser energy motor, I assume
"""

import numpy as np

from ophyd import Component as Cpt
from ophyd.positioner import EpicsMotor, SoftPositioner  # noqa

from .pseudopos import LookupTablePositioner, PseudoSingleInterface


def load_calibration_file(filename: str) -> np.ndarray:
    """
    Load a calibration file.

    Data will be sorted by position and need not be pre-sorted.

    Two columns of data in a space-delimited text file.  No header:
        Column 1: waveplate position [mm?]
        Column 2: pulse energy [uJ]

    Parameters
    ----------
    filename : str
        The calibration data filename.

    Returns
    -------
    np.ndarray
        Of shape (num_data_rows, 2)
    """
    data = np.loadtxt(filename)
    sort_indices = data[:, 0].argsort()
    return np.column_stack([data[sort_indices, 0],
                            data[sort_indices, 1]
                            ])


def plot_calibration(table: np.ndarray, *, show: bool = True):
    """
    Plot calibration data.
    """
    # Importing forces backend selection, so do inside method
    import matplotlib.pyplot as plt  # noqa
    plt.plot(table[:, 0], table[:, 1], "k-o")
    plt.xlabel("las_opa_wp")
    plt.ylabel(r"Pulse energy / $\mu$J")
    if show:
        plt.show()


class LaserEnergyPositioner(LookupTablePositioner):
    energy = Cpt(PseudoSingleInterface, egu='uJ')
    motor = Cpt(EpicsMotor, '')

    def __init__(self, *args, calibration_file, column_names=None, **kwargs):
        table = load_calibration_file(calibration_file)
        column_names = column_names or ['motor', 'energy']
        super().__init__(*args, table=table, column_names=column_names,
                         **kwargs)


# TODO: add optional plotting support for each move?
#   pl.axvline(Evalue)
#   pl.axhline(WPdes)

if __name__ == '__main__':
    motor = LaserEnergyPositioner(
        'sim:mtr1',
        calibration_file='xcslt8717_wpcalib_opa',
        name='motor')
