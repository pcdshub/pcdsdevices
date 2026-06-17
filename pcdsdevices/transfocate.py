from ophyd import Component as Cpt
from ophyd import Device

from .interface import BaseInterface
from .signal import PytmcSignal


class TFIErrors(BaseInterface, Device):
    energy_error = Cpt(PytmcSignal, ':ENRG:IN:Error', io='i',
                       kind='normal', doc='')
    effective_radius_error = Cpt(PytmcSignal, ':EFF:RADIUS:Error', io='i',
                                 kind='normal', doc='')
    current_mode_error = Cpt(PytmcSignal, ':CURR:MODE:Error', io='i',
                             kind='normal', doc='')
    diss_allowed_region_error = Cpt(PytmcSignal, ':DISSALL:Error', io='i',
                                    kind='normal', doc='')
    lens_mover_error = Cpt(PytmcSignal, ':LENS:MOV:Error', io='i',
                           kind='normal', doc='')
    twod_lens1_error = Cpt(PytmcSignal, ':2D1:Error', io='i',
                           kind='normal', doc='')
    twod_lens2_error = Cpt(PytmcSignal, ':2D2:Error', io='i',
                           kind='normal', doc='')
    twod_lens3_error = Cpt(PytmcSignal, ':2D3:Error', io='i',
                           kind='normal', doc='')
    twod_lens4_error = Cpt(PytmcSignal, ':2D4:Error', io='i',
                           kind='normal', doc='')
    twod_lens5_error = Cpt(PytmcSignal, ':2D5:Error', io='i',
                           kind='normal', doc='')
    twod_lens6_error = Cpt(PytmcSignal, ':2D6:Error', io='i',
                           kind='normal', doc='')
    twod_lens7_error = Cpt(PytmcSignal, ':2D7:Error', io='i',
                           kind='normal', doc='')
    twod_lens8_error = Cpt(PytmcSignal, ':2D8:Error', io='i',
                           kind='normal', doc='')

    oned_horz_error = Cpt(PytmcSignal, ':1DH:Error', io='i',
                          kind='normal', doc='')
    oned_vert_error = Cpt(PytmcSignal, ':1DV:Error', io='i',
                          kind='normal', doc='')


class XPPTFI(BaseInterface, Device):
    """
        Transssssfooocatttteee
    """
    bypass_mode = Cpt(PytmcSignal, ':BYP:SW', io='i',
                      kind='normal', doc='')
    test_mode = Cpt(PytmcSignal, ':TST:SW', io='i',
                    kind='normal', doc='')
    error_type = Cpt(PytmcSignal, ':SYS:ERROR:TYPE', io='i',
                     kind='normal', doc='')
    error_msg = Cpt(PytmcSignal, ':SYS:ERROR:MSG', io='i',
                    kind='normal', doc='', string=True)
    error_summary = Cpt(PytmcSignal, ':ERROR:SUMMARY', io='i',
                        kind='normal', doc='true means theres an error somehwere in the system')
    master_reset = Cpt(PytmcSignal, ':MASTER:RESET', io='o',
                       kind='normal', doc='')
    mono_bb_temp = Cpt(PytmcSignal, ':MONO:BB:EPS:ILOCK:TC_TEMP', io='i',
                       kind='normal', doc='')
    reset_mono_latch = Cpt(PytmcSignal, ':MONO:RST:LATCH', io='io',
                           kind='normal', doc='')
    safe_to_retract_mono_bb = Cpt(PytmcSignal, ':MONO:BB:EPS:SAFE:TO:RETRACT', io='i',
                                  kind='normal', doc='')
    curr_mode = Cpt(PytmcSignal, ':CURR:MODE', io='i',
                    kind='normal', doc='')
    mono_bb_state = Cpt(PytmcSignal, ':MONO:BB:State', io='i',
                        kind='normal', doc='')
    st1l0_state = Cpt(PytmcSignal, ':ST1L0:STATE', io='i',
                      kind='normal', doc='state is either IN or Unknown')
    st1l2_state = Cpt(PytmcSignal, ':ST1L2:STATE', io='i',
                      kind='normal', doc='state is either IN or Unknown')

    protected = Cpt(PytmcSignal, ':PROTECTED', io='i',
                    kind='normal', doc='')
    in_disallowed_region = Cpt(PytmcSignal, ':DISSALL:IN:REGION', io='i',
                               kind='normal', doc='')
    disallowed_low = Cpt(PytmcSignal, ':DISSALL:RAD:LOW', io='i',
                         kind='normal', doc='')
    disallowed_high = Cpt(PytmcSignal, ':DISSALL:RAD:HIGH', io='i',
                          kind='normal', doc='')
    effective_rad_vert = Cpt(PytmcSignal, ':EFF:VERT:RADIUS', io='i',
                             kind='normal', doc='')
    effective_rad_horz = Cpt(PytmcSignal, ':EFF:HORZ:RADIUS', io='i',
                             kind='normal', doc='')
    pmps_photon_energy = Cpt(PytmcSignal, ':ENRG:IN:PMPS:PHOTON:ENERGY', io='i',
                             kind='normal', doc='')
    epics_photon_energy = Cpt(PytmcSignal, ':ENRG:IN:EPICS:PHOTON:ENERGY', io='i',
                              kind='normal', doc='')

    one_horz_state = Cpt(PytmcSignal, ':1DH:State', io='i',
                         kind='normal', doc='')
    one_vert_state = Cpt(PytmcSignal, ':1DV:State', io='i',
                         kind='normal', doc='')
    twod_lens1_state = Cpt(PytmcSignal, ':2D1:State', io='i',
                           kind='normal', doc='')
    twod_lens2_state = Cpt(PytmcSignal, ':2D2:State', io='i',
                           kind='normal', doc='')
    twod_lens3_state = Cpt(PytmcSignal, ':2D3:State', io='i',
                           kind='normal', doc='')
    twod_lens4_state = Cpt(PytmcSignal, ':2D4:State', io='i',
                           kind='normal', doc='')
    twod_lens5_state = Cpt(PytmcSignal, ':2D5:State', io='i',
                           kind='normal', doc='')
    twod_lens6_state = Cpt(PytmcSignal, ':2D6:State', io='i',
                           kind='normal', doc='')
    twod_lens7_state = Cpt(PytmcSignal, ':2D7:State', io='i',
                           kind='normal', doc='')
    twod_lens8_state = Cpt(PytmcSignal, ':2D8:State', io='i',
                           kind='normal', doc='')

    two_insert_lens1 = Cpt(PytmcSignal, ':2D:INSERT:LENS:1:INSERT', io='io',
                           kind='normal', doc='')
    two_insert_lens2 = Cpt(PytmcSignal, ':2D:INSERT:LENS:2:INSERT', io='io',
                           kind='normal', doc='')
    two_insert_Lens3 = Cpt(PytmcSignal, ':2D:INSERT:LENS:3:INSERT', io='io',
                           kind='normal', doc='')
    two_Insert_Lens4 = Cpt(PytmcSignal, ':2D:INSERT:LENS:4:INSERT', io='io',
                           kind='normal', doc='')
    two_Insert_Lens5 = Cpt(PytmcSignal, ':2D:INSERT:LENS:5:INSERT', io='io',
                           kind='normal', doc='')
    two_Insert_Lens6 = Cpt(PytmcSignal, ':2D:INSERT:LENS:6:INSERT', io='io',
                           kind='normal', doc='')
    two_Insert_Lens7 = Cpt(PytmcSignal, ':2D:INSERT:LENS:7:INSERT', io='io',
                           kind='normal', doc='')
    two_Insert_Lens8 = Cpt(PytmcSignal, ':2D:INSERT:LENS:8:INSERT', io='io',
                           kind='normal', doc='')

    two_remove_Lens1 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:1:REMOVE', io='io',
                           kind='normal', doc='')
    two_Remove_Lens2 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:2:REMOVE', io='io',
                           kind='normal', doc='')
    two_Remove_Lens3 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:3:REMOVE', io='io',
                           kind='normal', doc='')
    two_Remove_Lens4 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:4:REMOVE', io='io',
                           kind='normal', doc='')
    two_Remove_Lens5 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:5:REMOVE', io='io',
                           kind='normal', doc='')
    two_Remove_Lens6 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:6:REMOVE', io='io',
                           kind='normal', doc='')
    two_Remove_Lens7 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:7:REMOVE', io='io',
                           kind='normal', doc='')
    two_Remove_Lens8 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:8:REMOVE', io='io',
                           kind='normal', doc='')

    one_Horz_Lens1 = Cpt(PytmcSignal, ':1D:HORZ:MOVE:LENS:1:INSERT', io='io',
                         kind='normal', doc='')
    one_Horz_Lens2 = Cpt(PytmcSignal, ':1D:HORZ:MOVE:LENS:2:INSERT', io='io',
                         kind='normal', doc='')
    one_Horz_Lens3 = Cpt(PytmcSignal, ':1D:HORZ:MOVE:LENS:3:INSERT', io='io',
                         kind='normal', doc='')
    one_Horz_Lens4 = Cpt(PytmcSignal, ':1D:HORZ:MOVE:LENS:4:INSERT', io='io',
                         kind='normal', doc='')
    one_Horz_Out = Cpt(PytmcSignal, ':1D:HORZ:MOVE:OUT', io='io',
                       kind='normal', doc='')

    one_VertLens1 = Cpt(PytmcSignal, ':1D:VERT:MOVE:LENS:1:INSERT', io='io',
                        kind='normal', doc='')
    one_VertLens2 = Cpt(PytmcSignal, ':1D:VERT:MOVE:LENS:2:INSERT', io='io',
                        kind='normal', doc='')
    one_VertLens3 = Cpt(PytmcSignal, ':1D:VERT:MOVE:LENS:3:INSERT', io='io',
                        kind='normal', doc='')
    one_VertLens4 = Cpt(PytmcSignal, ':1D:VERT:MOVE:LENS:4:INSERT', io='io',
                        kind='normal', doc='')
    one_VertOut = Cpt(PytmcSignal, ':1D:VERT:MOVE:OUT', io='io',
                      kind='normal', doc='')
