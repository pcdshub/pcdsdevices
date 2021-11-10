import logging

import pytest
from ophyd.sim import make_fake_device

from ..sample_delivery import (HPLC, PCM, CoolerShaker, FlowIntegrator,
                               GasManifold, Selector)

logger = logging.getLogger(__name__)


@pytest.mark.timeout(5)
def test_sds_init():
    logger.debug('test_sds_init')
    FakeFlowIntegrator = make_fake_device(FlowIntegrator)
    FakeFlowIntegrator(name='test_fi', integrator_source_prefix='test1',
                       flow_source_prefix='test2', names_prefix='test3',
                       flow1_start_prefix='test4', flow1_used_prefix='test5',
                       flow1_time_prefix='test6', flow2_start_prefix='test7',
                       flow2_used_prefix='test8', flow2_time_prefix='test9',
                       flow3_start_prefix='test10', flow3_used_prefix='test11',
                       flow3_time_prefix='test12', flow4_start_prefix='test13',
                       flow4_used_prefix='test14', flow4_time_prefix='test15',
                       flow5_start_prefix='test16', flow5_used_prefix='test17',
                       flow5_time_prefix='test18', flow6_start_prefix='test19',
                       flow6_used_prefix='test20', flow6_time_prefix='test21',
                       flow7_start_prefix='test22', flow7_used_prefix='test23',
                       flow7_time_prefix='test24', flow8_start_prefix='test25',
                       flow8_used_prefix='test26', flow8_time_prefix='test27',
                       flow9_start_prefix='test28', flow9_used_prefix='test29',
                       flow9_time_prefix='test30',
                       flow10_start_prefix='test31',
                       flow10_used_prefix='test32',
                       flow10_time_prefix='test33', flow1_prefix='test34',
                       flow2_prefix='test35', flow3_prefix='test36',
                       flow4_prefix='test37', flow5_prefix='test38',
                       flow6_prefix='test39', flow7_prefix='test40',
                       flow8_prefix='test41', flow9_prefix='test42',
                       flow10_prefix='test62')
    FakePCM = make_fake_device(PCM)
    FakePCM('FAKE:PCM', name='test_pcm')
    FakeHPLC = make_fake_device(HPLC)
    FakeHPLC('FAKE:HPLC', name='test_hplc', status_prefix='test43',
             run_prefix='test44', flowrate_prefix='test45',
             set_flowrate_prefix='test46', flowrate_SP_prefix='test47',
             pressure_prefix='test48', pressure_units_prefix='test49',
             set_max_pressure_prefix='test50', max_pressure_prefix='test51',
             clear_error_prefix='test52')
    FakeCoolerShaker = make_fake_device(CoolerShaker)
    FakeCoolerShaker('FAKE:CS', name='test_cs', temperature1_prefix='test53',
                     SP1_prefix='test54', set_SP1_prefix='test55',
                     current1_prefix='test56', temperature2_prefix='test57',
                     SP2_prefix='test58', set_SP2_prefix='test59',
                     current2_prefix='test60', reboot_prefix='test61')
    FakeSelector = make_fake_device(Selector)
    FakeSelector('FAKE:SEL', name='test_sel')
    FakeGasManifold = make_fake_device(GasManifold)
    FakeGasManifold('FAKE:MAN', name='test_man')


@pytest.mark.timeout(5)
def test_sds_disconnected():
    logger.debug('test_sds_disconnected')
    FlowIntegrator(name='test_fi', integrator_source_prefix='test1',
                   flow_source_prefix='test2', names_prefix='test3',
                   flow1_start_prefix='test4', flow1_used_prefix='test5',
                   flow1_time_prefix='test6', flow2_start_prefix='test7',
                   flow2_used_prefix='test8', flow2_time_prefix='test9',
                   flow3_start_prefix='test10', flow3_used_prefix='test11',
                   flow3_time_prefix='test12', flow4_start_prefix='test13',
                   flow4_used_prefix='test14', flow4_time_prefix='test15',
                   flow5_start_prefix='test16', flow5_used_prefix='test17',
                   flow5_time_prefix='test18', flow6_start_prefix='test19',
                   flow6_used_prefix='test20', flow6_time_prefix='test21',
                   flow7_start_prefix='test22', flow7_used_prefix='test23',
                   flow7_time_prefix='test24', flow8_start_prefix='test25',
                   flow8_used_prefix='test26', flow8_time_prefix='test27',
                   flow9_start_prefix='test28', flow9_used_prefix='test29',
                   flow9_time_prefix='test30', flow10_start_prefix='test31',
                   flow10_used_prefix='test32', flow10_time_prefix='test33',
                   flow1_prefix='test34', flow2_prefix='test35',
                   flow3_prefix='test36', flow4_prefix='test37',
                   flow5_prefix='test38', flow6_prefix='test39',
                   flow7_prefix='test40', flow8_prefix='test41',
                   flow9_prefix='test42', flow10_prefix='test62')
    PCM('FAKE:PCM', name='test_pcm')
    HPLC('FAKE:HPLC', name='test_hplc', status_prefix='test43',
         run_prefix='test44', flowrate_prefix='test45',
         set_flowrate_prefix='test46', flowrate_SP_prefix='test47',
         pressure_prefix='test48', pressure_units_prefix='test49',
         set_max_pressure_prefix='test50', max_pressure_prefix='test51',
         clear_error_prefix='test52')
    CoolerShaker('FAKE:CS', name='test_cs', temperature1_prefix='test53',
                 SP1_prefix='test54', set_SP1_prefix='test55',
                 current1_prefix='test56', temperature2_prefix='test57',
                 SP2_prefix='test58', set_SP2_prefix='test59',
                 current2_prefix='test60', reboot_prefix='test61')
    Selector('FAKE:SEL', name='test_sel')
    GasManifold('FAKE:MAN', name='test_man')
