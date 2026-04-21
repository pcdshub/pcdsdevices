from ..utils import convert_unit


def test_standard_units():
    assert convert_unit(1, 'm', 'mm') == 1000
    assert convert_unit(10, 'kilograms', 'gram') == 10000


def test_custom_units():
    assert convert_unit(1, 'J', 'joule') == 1
    assert convert_unit(0.5, 'J', 'mJ') == 500
    assert convert_unit(2, 'joule', 'uJ') == 2000000
    assert convert_unit(1, 'millijoule', 'J') == 0.001
    assert convert_unit(0.1, 'mJ', 'microjoule') == 100
    assert convert_unit(1000, 'uJ', 'J') == 0.001
    assert convert_unit(10, 'microjoule', 'millijoule') == 0.01
