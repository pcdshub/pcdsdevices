from ..utils import convert_unit


def test_convert_unit():
    assert convert_unit(0.5, 'J', 'mJ') == 500
    assert convert_unit(2, 'J', 'uJ') == 2000000
    assert convert_unit(1, 'mJ', 'J') == 0.001
    assert convert_unit(0.1, 'mJ', 'uJ') == 100
    assert convert_unit(1000, 'uJ', 'J') == 0.001
    assert convert_unit(10, 'uJ', 'mJ') == 0.01
