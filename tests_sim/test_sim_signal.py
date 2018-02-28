import time

import numpy as np

from pcdsdevices.sim.signal import FakeSignal

def test_FakeSignal_instantiates():
    assert(FakeSignal(name='Fake'))

def test_FakeSignal_runs_ophyd_functions():
    sig = FakeSignal(name='Fake')
    assert(isinstance(sig.read(), dict))
    assert(isinstance(sig.describe(), dict))
    assert(isinstance(sig.describe_configuration(), dict))
    assert(isinstance(sig.read_configuration(), dict))

def test_FakeSignal_uni_noise_readback():
    sig = FakeSignal(name="TEST", noise=True, noise_type="uni", 
                     noise_args=(-1,1), noise_kwargs={'scale':5})
    for i in range(10):
        test_val = np.random.uniform(-1,1) * 5
        assert(sig.value == test_val or np.isclose(sig.value, 0, atol=5))
        assert(sig.get() == test_val or np.isclose(sig.value, 0, atol=5))
        assert(sig.read()["TEST"]['value'] == test_val or np.isclose(
            sig.read()["TEST"]['value'], 0, atol=5))

def test_FakeSignal_norm_noise_readback():
    sig = FakeSignal(name="TEST", noise=True, noise_type="norm", 
                     noise_args=(0,0.25))
    for i in range(10):
        test_val = np.random.normal(0, 0.25)
        assert(sig.value == test_val or np.isclose(sig.value, 0, atol=5))
        assert(sig.get() == test_val or np.isclose(sig.get(), 0, atol=5))
        assert(sig.read()["TEST"]['value'] == test_val or np.isclose(
            sig.read()["TEST"]['value'], 0, atol=5))
    
def test_FakeSignal_noise_changes_every_read():
    sig = FakeSignal(name="TEST", noise=True, noise_kwargs={'scale':5})
    val = [sig.value for i in range(10)]
    get = [sig.get() for i in range(10)]
    read = [sig.read()["TEST"]['value'] for i in range(10)]
    assert(len(val) == len(set(val)))
    assert(len(get) == len(set(get)))
    assert(len(read) == len(set(read)))
    
def test_FakeSignal_get_and_put_sleep_time():
    sig = FakeSignal(name="TEST", put_sleep=.1, get_sleep=1.5)
    t0 = time.time()
    sig.put(5)
    t1 = time.time() - t0
    assert(np.isclose(t1, sig.put_sleep, rtol=0.1))
    t2 = time.time()
    val = sig.get()
    t3 = time.time() - t2
    assert(np.isclose(t3, sig.get_sleep, rtol=0.1))

def test_FakeSignal_velocity_sleep_time():
    sig = FakeSignal(name="TEST", velocity=1)
    t0 = time.time()
    sig.put(1.5)
    t1 = time.time() - t0
    assert(np.isclose(t1, 1.5, rtol=0.1))
    
    
