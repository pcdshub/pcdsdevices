import inspect

import pytest
import schema

import ophyd
from pcdsdevices.variety import get_metadata, set_metadata, validate_metadata

# A sentinel indicating the validated metadata should match the provided
# metadata exactly
SAME = object()


def test_empty_md():
    validate_metadata({})


def test_no_variety():
    with pytest.raises(ValueError):
        validate_metadata({'test': 'a'})


@pytest.mark.parametrize(
    'md, expected',
    [
        # ** command **
        pytest.param(
            dict(variety='command'),
            dict(variety='command', value=1),  # <-- picks up default
            id='command-default-value',
        ),

        pytest.param(
            dict(variety='command', value=0, enum_strings=['a', 'b', 'c']),
            SAME,
            id='command-with-enum-strs',
        ),

        pytest.param(
            dict(variety='command', value='a', enum_strings=['a', 'b', 'c']),
            SAME,
            id='command-str-with-enum-strs',
        ),

        pytest.param(
            dict(variety='command-proc'),
            dict(variety='command-proc', value=1),  # <-- picks up default
            id='command-proc',
        ),

        pytest.param(
            dict(variety='command-enum', value=0),
            dict(variety='command-enum', value=0),
            id='command-enum',
        ),

        pytest.param(
            dict(variety='command-setpoint-tracks-readback', value=0),
            dict(variety='command-setpoint-tracks-readback', value=0),
            id='command-setpoint-tracks-readback',
        ),

        # ** tweakable **
        pytest.param(
            dict(variety='tweakable'),
            schema.SchemaMissingKeyError,
            id='tweakable-no-value',
        ),

        pytest.param(
            dict(variety='tweakable', value=3),
            SAME,
            id='tweakable-value',
        ),

        pytest.param(
            dict(variety='tweakable', value=3, value_range=[-1, 10]),
            SAME,
            id='tweakable-good-range',
        ),

        pytest.param(
            dict(variety='tweakable', value=3, value_range=-1),
            schema.SchemaError,
            id='tweakable-bad-range',
        ),

        pytest.param(
            dict(variety='tweakable', value=3, value_range=[-1, 'q']),
            schema.SchemaError,
            id='tweakable-bad-range-type',
        ),

        # ** arrays / waveforms **
        pytest.param(
            dict(variety='array-timeseries'),
            SAME,
            id='array-timeseries'
        ),

        pytest.param(
            dict(variety='array-histogram'),
            SAME,
            id='array-histogram'
        ),

        pytest.param(
            dict(variety='array-image'),
            SAME,
            id='array-image'
        ),

        pytest.param(
            dict(variety='array-nd'),
            SAME,
            id='array-nd'
        ),

        pytest.param(
            dict(variety='array-nd', dimension=2, shape=(512, 512)),
            SAME,
            id='array-2d'
        ),

        pytest.param(
            dict(variety='array-nd', dimension=3, shape=(512, 512, 512)),
            SAME,
            id='array-3d'
        ),

        pytest.param(
            dict(variety='array-nd', shape=()),
            schema.SchemaError,
            id='array-bad-shape'
        ),

        # ** scalar - numeric **
        pytest.param(
            dict(variety='scalar',),
            SAME,
            id='scalar'
        ),

        pytest.param(
            dict(variety='scalar-range',),
            SAME,
            id='scalar-range'
        ),

        pytest.param(
            dict(variety='scalar-range', range_source='use_limits'),
            SAME,
            id='scalar-use_limits'
        ),

        pytest.param(
            dict(variety='scalar-range', range_source='custom'),
            SAME,
            id='scalar-custom'
        ),

        pytest.param(
            dict(variety='scalar-range', range_source='custom', range=[0, 5]),
            SAME,
            id='scalar-custom-range'
        ),

        pytest.param(
            dict(variety='scalar-range', range_source='custom', range=[0]),
            schema.SchemaError,
            id='scalar-bad-range'
        ),

        # ** text **
        pytest.param(
            dict(variety='text', enum_strings=['a', 'b', 'c']),
            SAME,
            id='text-enum_strings'
        ),

        pytest.param(
            dict(variety='text-enum', enum_strings=['a', 'b', 'c']),
            SAME,
            id='text-enum'
        ),

        pytest.param(
            dict(variety='text-multiline', enum_strings=['a', 'b', 'c']),
            SAME,
            id='text-multiline'
        ),

        pytest.param(
            dict(variety='text', range_source='custom', range=[0]),
            schema.SchemaError,
            id='text-bad-keys'
        ),

        # ** general enum **
        pytest.param(
            dict(variety='enum', enum_strings=['a', 'b', 'c']),
            SAME,
            id='enum-basic',
        ),

        pytest.param(
            dict(variety='enum', enum_strings='a'),
            schema.SchemaError,
            id='enum-not-a-list',
        ),

    ]
)
def test_schemas(md, expected):
    if expected is SAME:
        expected = dict(md)

    if inspect.isclass(expected):
        with pytest.raises(expected):
            validate_metadata(md)
    else:
        assert validate_metadata(md) == expected


def test_component():
    md = dict(variety='command', value=5)

    class MyDevice(ophyd.Device):
        cpt = ophyd.Component(ophyd.Signal)
        set_metadata(cpt, md)

    assert get_metadata(MyDevice.cpt) == md
    assert get_metadata(MyDevice(name='dev').cpt) == md


def test_component_empty_md():
    class MyDevice(ophyd.Device):
        cpt = ophyd.Component(ophyd.Signal)
        set_metadata(cpt, None)
        unset_cpt = ophyd.Component(ophyd.Signal)

    assert get_metadata(MyDevice.cpt) == {}
    assert get_metadata(MyDevice.unset_cpt) == {}
