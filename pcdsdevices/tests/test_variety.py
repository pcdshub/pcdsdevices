import inspect

import ophyd
import pytest
import schema

from .. import tags
from ..variety import (expand_dotted_dict, get_metadata, set_metadata,
                       validate_metadata)

# A sentinel indicating the validated metadata should match the provided
# metadata exactly
SAME = object()


def test_empty_md():
    validate_metadata({})


def test_no_variety():
    with pytest.raises(ValueError):
        validate_metadata({'test': 'a'})


text_defaults = dict(delimiter='\n', encoding='utf-8', format='plain')


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
            {'variety': 'scalar-tweakable',
             'display_format': 'default',
             'delta': {'value': 3,
                       'adds_to': 'setpoint',
                       'source': 'value',
                       }},
            SAME,
            id='tweakable-delta',
        ),

        pytest.param(
            {'variety': 'scalar-tweakable',
             'display_format': 'default',
             'delta': {'value': 3,
                       'adds_to': 'setpoint',
                       'source': 'value',
                       'range': [-1, 10]}},
            SAME,
            id='tweakable-good-range',
        ),

        pytest.param(
            {'variety': 'scalar-tweakable',
             'delta': {'value': 3,
                       'range': -1}},
            schema.SchemaError,
            id='tweakable-bad-range',
        ),

        pytest.param(
            dict(variety='scalar-tweakable', delta={'value': 3,
                                                    'range': [-1, 'q']}),
            schema.SchemaError,
            id='tweakable-bad-range-type',
        ),

        # ** arrays / waveforms **
        pytest.param(
            dict(variety='array-tabular'),
            SAME,
            id='array-tabular'
        ),

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
            dict(variety='scalar'),
            dict(variety='scalar', display_format='default'),
            id='scalar'
        ),

        pytest.param(
            dict(variety='scalar-range', display_format='default'),
            SAME,
            id='scalar-range'
        ),

        pytest.param(
            {'variety': 'scalar-range',
             'display_format': 'exponential',
             'range': {'source': 'use_limits'},
             },
            SAME,
            id='scalar-use_limits'
        ),

        pytest.param(
            {'variety': 'scalar-range',
             'range': dict(source='value'),
             'display_format': 'default'
             },
            SAME,
            id='scalar-custom'
        ),

        pytest.param(
            {'variety': 'scalar-range',
             'range': dict(source='value',
                           value=[0, 5]),
             'display_format': 'default',
             },
            SAME,
            id='scalar-custom-range'
        ),

        pytest.param(
            {'variety': 'scalar-range',
             'range': dict(source='value', value=[0]),
             },
            schema.SchemaError,
            id='scalar-bad-range'
        ),

        # ** text **
        pytest.param(
            dict(variety='text', enum_strings=['a', 'b', 'c'],
                 **text_defaults),
            SAME,
            id='text-enum_strings'
        ),

        pytest.param(
            dict(variety='text-enum', enum_strings=['a', 'b', 'c'],
                 **text_defaults),
            SAME,
            id='text-enum'
        ),

        pytest.param(
            dict(variety='text-multiline', enum_strings=['a', 'b', 'c'],
                 **text_defaults),
            SAME,
            id='text-multiline'
        ),

        pytest.param(
            dict(variety='text', range_source='custom', range=[0]),
            schema.SchemaError,
            id='text-bad-keys'
        ),

        # ** bitmask **
        pytest.param(
            dict(variety='bitmask'),
            dict(variety='bitmask', bits=8, orientation='horizontal',
                 first_bit='most-significant',
                 meaning=None,
                 style=dict(on_color='green', off_color='gray',
                            shape='rectangle')
                 ),
            id='bitmask-defaults',
        ),

        pytest.param(
            dict(variety='bitmask', bits=32, first_bit='least-significant'),
            dict(variety='bitmask', bits=32,
                 orientation='horizontal', first_bit='least-significant',
                 meaning=None,
                 style=dict(shape='rectangle', on_color='green',
                            off_color='gray'),
                 ),
            id='bitmask-custom',
        ),

        # ** general enum **
        pytest.param(
            dict(variety='enum', enum_strings=['a', 'b', 'c']),
            SAME,
            id='enum-basic',
        ),

        pytest.param(
            dict(variety='enum', enum_strings=['a', 'b', 'c'],
                 tags={'protected'}),
            SAME,
            id='enum-basic-with-tags',
        ),

        pytest.param(
            dict(variety='enum', enum_strings='a'),
            schema.SchemaError,
            id='enum-not-a-list',
        ),

        pytest.param(
            dict(variety='enum', enum_strings=['a', 'b', 'c'],
                 tags={'this-is-an-unknown-tag'}),
            schema.SchemaError,
            id='enum-basic-with-bad-tag',
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


def test_tag_explain():
    for tag in tags.get_valid_tags():
        print(tag, tags.explain_tag(tag))

    with pytest.raises(KeyError):
        tags.explain_tag('this-is-a-bad-tag')


@pytest.mark.parametrize(
    'value, expected',
    [pytest.param(
        {},
        {}
     ),

     pytest.param(
         {'a..': {}},
         ValueError,
         id='empty_dot',
     ),

     pytest.param(
         {'a': {'b': 3}, 'a.b': {}},
         ValueError,
         id='overwrite_dict',
     ),

     pytest.param(
         {'a': {'b': {}}, 'a.b.c': 3},
         {'a': {'b': {'c': 3}}},
         id='nested_3',
     ),

     pytest.param(
         {'a.b': {}},
         {'a': {'b': {}}},
         id='nested_ab',
     ),

     pytest.param(
         {'a': {}, 'a.b': 4},
         dict(a=dict(b=4))
     ),

     pytest.param(
         {'a.b.c': 1, 'a.b': {'d': 4}},
         dict(a=dict(b=dict(c=1, d=4)))
     ),

     pytest.param(
         {'a.b.c': {}, 'a.b': {'d': 4}},
         dict(a=dict(b=dict(c={}, d=4)))
     ),

     pytest.param(
         {'a': {}, 'a.b': '3', 'a.c': '4'},
         {'a': {'b': '3', 'c': '4'}},
     ),

     pytest.param(
         {'a': {'b': '2'}, 'a.b': '3', 'a.c': '4'},
         {'a': {'b': '3', 'c': '4'}},
         id='update_value',
     ),

     pytest.param(
        {'variety': 'scalar-tweakable',
         'delta.value': 0.5,
         'delta.range': [-1, 1],
         'range.source': 'custom',
         'range.value': [-1, 1],
         },
        {'variety': 'scalar-tweakable',
         'delta': {'value': 0.5,
                   'range': [-1, 1],
                   },
         'range': {'source': 'custom',
                   'value': [-1, 1],
                   },
         },
        id='real_world',
     ),

     pytest.param(
        {'variety': 'scalar-tweakable',
         'delta.value': 0.5,
         'delta.range': [-1, 1],
         'range': [-1, 1],  # <-- range specified as a value, not a dict
         'range.source': 'custom',  # <-- range.source update fails
         },
        ValueError,
        id='real_world_oops',
     ),
     ]
)
def test_dotted_dict(value, expected):
    if isinstance(expected, dict):
        assert expand_dotted_dict(value) == expected
    else:
        with pytest.raises(expected):
            expand_dotted_dict(value)
