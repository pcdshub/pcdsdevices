from ophyd import Component as Cpt
from ophyd import Device

from .interface import BaseInterface
from .signal import PytmcSignal


class TFIErrors(BaseInterface, Device):
    energy_error = Cpt(PytmcSignal, ':ENRG:IN:Error', io='i',
                       kind='normal', doc='Energy input error signal')
    effective_radius_error = Cpt(PytmcSignal, ':EFF:RADIUS:Error', io='i',
                                 kind='normal', doc='Effective radius error signal')
    current_mode_error = Cpt(PytmcSignal, ':CURR:MODE:Error', io='i',
                             kind='normal', doc='Current mode error signal')
    diss_allowed_region_error = Cpt(PytmcSignal, ':DISSALL:Error', io='i',
                                    kind='normal', doc='Disallowed region error signal')
    lens_mover_error = Cpt(PytmcSignal, ':LENS:MOV:Error', io='i',
                           kind='normal', doc='Lens mover error signal')
    twod_lens1_error = Cpt(PytmcSignal, ':2D1:Error', io='i',
                           kind='normal', doc='2D lens 1 error signal')
    twod_lens2_error = Cpt(PytmcSignal, ':2D2:Error', io='i',
                           kind='normal', doc='2D lens 2 error signal')
    twod_lens3_error = Cpt(PytmcSignal, ':2D3:Error', io='i',
                           kind='normal', doc='2D lens 3 error signal')
    twod_lens4_error = Cpt(PytmcSignal, ':2D4:Error', io='i',
                           kind='normal', doc='2D lens 4 error signal')
    twod_lens5_error = Cpt(PytmcSignal, ':2D5:Error', io='i',
                           kind='normal', doc='2D lens 5 error signal')
    twod_lens6_error = Cpt(PytmcSignal, ':2D6:Error', io='i',
                           kind='normal', doc='2D lens 6 error signal')
    twod_lens7_error = Cpt(PytmcSignal, ':2D7:Error', io='i',
                           kind='normal', doc='2D lens 7 error signal')
    twod_lens8_error = Cpt(PytmcSignal, ':2D8:Error', io='i',
                           kind='normal', doc='2D lens 8 error signal')

    oned_horz_error = Cpt(PytmcSignal, ':1DH:Error', io='i',
                          kind='normal', doc='1D horizontal lens error signal')
    oned_vert_error = Cpt(PytmcSignal, ':1DV:Error', io='i',
                          kind='normal', doc='1D vertical lens error signal')


class XPPTFI(BaseInterface, Device):
    """
        Transssssfooocatttteee
    """
    bypass_mode = Cpt(PytmcSignal, ':BYP:SW', io='i',
                      kind='normal', doc='Bypass mode switch')
    test_mode = Cpt(PytmcSignal, ':TST:SW', io='i',
                    kind='normal', doc='Test mode switch')
    error_type = Cpt(PytmcSignal, ':SYS:ERROR:TYPE', io='i',
                     kind='normal', doc='System error type indicator')
    error_msg = Cpt(PytmcSignal, ':SYS:ERROR:MSG', io='i',
                    kind='normal', doc='System error message', string=True)
    error_summary = Cpt(PytmcSignal, ':ERROR:SUMMARY', io='i',
                        kind='normal', doc='true means theres an error somehwere in the system')
    master_reset = Cpt(PytmcSignal, ':MASTER:RESET', io='o',
                       kind='normal', doc='Master reset command')
    mono_bb_temp = Cpt(PytmcSignal, ':MONO:BB:EPS:ILOCK:TC_TEMP', io='i',
                       kind='normal', doc='Monochromator backplane temperature')
    reset_mono_latch = Cpt(PytmcSignal, ':MONO:RST:LATCH', io='io',
                           kind='normal', doc='Reset monochromator latch')
    safe_to_retract_mono_bb = Cpt(PytmcSignal, ':MONO:BB:EPS:SAFE:TO:RETRACT', io='i',
                                  kind='normal', doc='Safe to retract monochromator backplane')
    curr_mode = Cpt(PytmcSignal, ':CURR:MODE', io='i',
                    kind='normal', doc='Current mode')
    mono_bb_state = Cpt(PytmcSignal, ':MONO:BB:State', io='i',
                        kind='normal', doc='Monochromator backplane state')
    st1l0_state = Cpt(PytmcSignal, ':ST1L0:STATE', io='i',
                      kind='normal', doc='state is either IN or Unknown')
    st1l2_state = Cpt(PytmcSignal, ':ST1L2:STATE', io='i',
                      kind='normal', doc='state is either IN or Unknown')

    protected = Cpt(PytmcSignal, ':PROTECTED', io='i',
                    kind='normal', doc='Protected status')
    in_disallowed_region = Cpt(PytmcSignal, ':DISSALL:IN:REGION', io='i',
                               kind='normal', doc='Indicator if in disallowed region')
    disallowed_low = Cpt(PytmcSignal, ':DISSALL:RAD:LOW', io='i',
                         kind='normal', doc='Low radius of disallowed region')
    disallowed_high = Cpt(PytmcSignal, ':DISSALL:RAD:HIGH', io='i',
                          kind='normal', doc='High radius of disallowed region')
    effective_rad_vert = Cpt(PytmcSignal, ':EFF:VERT:RADIUS', io='i',
                             kind='normal', doc='Vertical effective radius')
    effective_rad_horz = Cpt(PytmcSignal, ':EFF:HORZ:RADIUS', io='i',
                             kind='normal', doc='Horizontal effective radius')
    pmps_photon_energy = Cpt(PytmcSignal, ':ENRG:IN:PMPS:PHOTON:ENERGY', io='i',
                             kind='normal', doc='Photon energy from PMPS')
    epics_photon_energy = Cpt(PytmcSignal, ':ENRG:IN:EPICS:PHOTON:ENERGY', io='i',
                              kind='normal', doc='Photon energy from EPICS')

    one_horz_state = Cpt(PytmcSignal, ':1DH:State', io='i',
                         kind='normal', doc='1D horizontal lens state')
    one_vert_state = Cpt(PytmcSignal, ':1DV:State', io='i',
                         kind='normal', doc='1D vertical lens state')
    twod_lens1_state = Cpt(PytmcSignal, ':2D1:State', io='i',
                           kind='normal', doc='2D lens 1 state')
    twod_lens2_state = Cpt(PytmcSignal, ':2D2:State', io='i',
                           kind='normal', doc='2D lens 2 state')
    twod_lens3_state = Cpt(PytmcSignal, ':2D3:State', io='i',
                           kind='normal', doc='2D lens 3 state')
    twod_lens4_state = Cpt(PytmcSignal, ':2D4:State', io='i',
                           kind='normal', doc='2D lens 4 state')
    twod_lens5_state = Cpt(PytmcSignal, ':2D5:State', io='i',
                           kind='normal', doc='2D lens 5 state')
    twod_lens6_state = Cpt(PytmcSignal, ':2D6:State', io='i',
                           kind='normal', doc='2D lens 6 state')
    twod_lens7_state = Cpt(PytmcSignal, ':2D7:State', io='i',
                           kind='normal', doc='2D lens 7 state')
    twod_lens8_state = Cpt(PytmcSignal, ':2D8:State', io='i',
                           kind='normal', doc='2D lens 8 state')

    two_insert_lens1 = Cpt(PytmcSignal, ':2D:INSERT:LENS:1:INSERT', io='io',
                           kind='normal', doc='Command to insert 2D lens 1')
    two_insert_lens2 = Cpt(PytmcSignal, ':2D:INSERT:LENS:2:INSERT', io='io',
                           kind='normal', doc='Command to insert 2D lens 2')
    two_insert_Lens3 = Cpt(PytmcSignal, ':2D:INSERT:LENS:3:INSERT', io='io',
                           kind='normal', doc='Command to insert 2D lens 3')
    two_Insert_Lens4 = Cpt(PytmcSignal, ':2D:INSERT:LENS:4:INSERT', io='io',
                           kind='normal', doc='Command to insert 2D lens 4')
    two_Insert_Lens5 = Cpt(PytmcSignal, ':2D:INSERT:LENS:5:INSERT', io='io',
                           kind='normal', doc='Command to insert 2D lens 5')
    two_Insert_Lens6 = Cpt(PytmcSignal, ':2D:INSERT:LENS:6:INSERT', io='io',
                           kind='normal', doc='Command to insert 2D lens 6')
    two_Insert_Lens7 = Cpt(PytmcSignal, ':2D:INSERT:LENS:7:INSERT', io='io',
                           kind='normal', doc='Command to insert 2D lens 7')
    two_Insert_Lens8 = Cpt(PytmcSignal, ':2D:INSERT:LENS:8:INSERT', io='io',
                           kind='normal', doc='Command to insert 2D lens 8')

    two_remove_Lens1 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:1:REMOVE', io='io',
                           kind='normal', doc='Command to remove 2D lens 1')
    two_Remove_Lens2 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:2:REMOVE', io='io',
                           kind='normal', doc='Command to remove 2D lens 2')
    two_Remove_Lens3 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:3:REMOVE', io='io',
                           kind='normal', doc='Command to remove 2D lens 3')
    two_Remove_Lens4 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:4:REMOVE', io='io',
                           kind='normal', doc='Command to remove 2D lens 4')
    two_Remove_Lens5 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:5:REMOVE', io='io',
                           kind='normal', doc='Command to remove 2D lens 5')
    two_Remove_Lens6 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:6:REMOVE', io='io',
                           kind='normal', doc='Command to remove 2D lens 6')
    two_Remove_Lens7 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:7:REMOVE', io='io',
                           kind='normal', doc='Command to remove 2D lens 7')
    two_Remove_Lens8 = Cpt(PytmcSignal, ':2D:REMOVE:LENS:8:REMOVE', io='io',
                           kind='normal', doc='Command to remove 2D lens 8')

    one_Horz_Lens1 = Cpt(PytmcSignal, ':1D:HORZ:MOVE:LENS:1:INSERT', io='io',
                         kind='normal', doc='Command to insert 1D horizontal lens 1')
    one_Horz_Lens2 = Cpt(PytmcSignal, ':1D:HORZ:MOVE:LENS:2:INSERT', io='io',
                         kind='normal', doc='Command to insert 1D horizontal lens 2')
    one_Horz_Lens3 = Cpt(PytmcSignal, ':1D:HORZ:MOVE:LENS:3:INSERT', io='io',
                         kind='normal', doc='Command to insert 1D horizontal lens 3')
    one_Horz_Lens4 = Cpt(PytmcSignal, ':1D:HORZ:MOVE:LENS:4:INSERT', io='io',
                         kind='normal', doc='Command to insert 1D horizontal lens 4')
    one_Horz_Out = Cpt(PytmcSignal, ':1D:HORZ:MOVE:OUT', io='io',
                       kind='normal', doc='Command to move 1D horizontal lens out')

    one_VertLens1 = Cpt(PytmcSignal, ':1D:VERT:MOVE:LENS:1:INSERT', io='io',
                        kind='normal', doc='Command to insert 1D vertical lens 1')
    one_VertLens2 = Cpt(PytmcSignal, ':1D:VERT:MOVE:LENS:2:INSERT', io='io',
                        kind='normal', doc='Command to insert 1D vertical lens 2')
    one_VertLens3 = Cpt(PytmcSignal, ':1D:VERT:MOVE:LENS:3:INSERT', io='io',
                        kind='normal', doc='Command to insert 1D vertical lens 3')
    one_VertLens4 = Cpt(PytmcSignal, ':1D:VERT:MOVE:LENS:4:INSERT', io='io',
                        kind='normal', doc='Command to insert 1D vertical lens 4')
    one_VertOut = Cpt(PytmcSignal, ':1D:VERT:MOVE:OUT', io='io',
                      kind='normal', doc='Command to move 1D vertical lens out')
