"""Additional component metadata, classifying each into a "variety"."""

import schema
from schema import Optional

import ophyd

from . import tags, utils

_schema_registry = {}
varieties_by_category = {
    'command': {
        'command',
        'command-proc',
        'command-enum',
        'command-setpoint-tracks-readback',
    },
    'array': {
        'array-tabular',
        'array-timeseries',
        'array-histogram',
        'array-image',
        'array-nd',
    },
    'scalar': {
        'scalar',
        'scalar-range',
        'scalar-tweakable',
    },
    'bitmask': {
        'bitmask',
    },
    'text': {
        'text',
        'text-multiline',
        'text-enum',
    },
    'enum': {
        'enum',
    },
}


def _length_validate(min_count, max_count, type_):
    """
    Wrapper to validate a value, based on the given length.
    """

    def validate(value):
        try:
            assert min_count <= len(value) <= max_count
        except Exception:
            ...
        else:
            for item in value:
                assert isinstance(item, type_)
            return True

        if min_count == max_count:
            raise ValueError(
                f'Expecting a sequence of {min_count} values ({type_})'
            )

        raise ValueError(
            f'Expecting a sequence betweeen {min_count} and {max_count} values'
            f' ({type_})'
        )

    return validate


common_schema = {
    Optional('tags'): {schema.Or(*tags.get_valid_tags())},
}


_default_bitmask_style = dict(shape='rectangle', on_color='green',
                              off_color='gray')

schema_by_category = {
    'command': schema.Schema({
        'variety': schema.Or(*varieties_by_category['command']),
        Optional('value', default=1): schema.Or(float, int, str),
        Optional('enum_strings'): [str],
        Optional('enum_dict'): dict,
        **common_schema
    }),

    'array': schema.Schema({
        'variety': schema.Or(*varieties_by_category['array']),
        Optional('shape'): _length_validate(1, 10, int),
        Optional('shape_signal'): str,
        Optional('dimension'): int,
        Optional('embed'): bool,
        Optional('colormap'): str,
        **common_schema
    }),

    'bitmask': schema.Schema({
        'variety': schema.Or(*varieties_by_category['bitmask']),
        Optional('orientation', default='horizontal'): schema.Or(
            'horizontal', 'vertical'),
        Optional('bits', default=8): int,
        Optional('first_bit', default='most-significant'): schema.Or(
            'most-significant', 'least-significant'),
        Optional('meaning', default=None): [str],

        Optional('style', default=_default_bitmask_style): schema.Schema({
            Optional('shape', default='rectangle'): schema.Or(
                'circle', 'rectangle'),

            Optional('on_color', default='green'): str,
            Optional('off_color', default='gray'): str,
        }),
        **common_schema
    }),

    'scalar': schema.Schema({
        'variety': schema.Or(*varieties_by_category['scalar']),
        Optional('display_format', default='default'): schema.Or(
            'default', 'string', 'decimal', 'exponential', 'hex', 'binary'),

        Optional('range'): schema.Schema({
            Optional('value'): _length_validate(2, 2, (float, int)),
            Optional('source', default='use_limits'): schema.Or(
                'use_limits', 'value'),
        }),

        Optional('delta'): schema.Schema({
            Optional('value'): schema.Or(float, int),
            Optional('range'): _length_validate(2, 2, (float, int)),
            Optional('source', default='value'): schema.Or(
                'signal', 'value'),
            Optional('signal'): schema.Or(str, ophyd.Component),

            Optional('add_signal'): str,
            Optional('adds_to', default='setpoint'): schema.Or(
                'setpoint', 'readback', 'custom-signal'),
        }),
        **common_schema
    }),

    'text': schema.Schema({
        'variety': schema.Or(*varieties_by_category['text']),
        Optional('enum_strings'): [str],
        Optional('delimiter', default='\n'): str,
        Optional('encoding', default='utf-8'): schema.Or('utf-8', 'latin-1',
                                                         'ascii'),
        Optional('format', default='plain'): schema.Or('plain', 'markdown',
                                                       'html'),
        **common_schema
    }),

    'enum': schema.Schema({
        'variety': schema.Or(*varieties_by_category['enum']),
        Optional('enum_strings'): [str],
        **common_schema
    }),
}


def expand_dotted_dict(root):
    """
    Expand dotted dictionary keys.

    Parameters
    ----------
    root : dict
        The dictionary to expand.

    Returns
    -------
    dct : dict
        The expanded dictionary.
    """
    if not root:
        return {}

    if not isinstance(root, dict):
        raise ValueError('A dictionary is required')

    res = {}

    def expand_key(dct, key, value):
        if isinstance(value, dict):
            # specifies a sub-dict; use full dotted name
            parts = key.split('.')
        else:
            # specifies a value; last part refers to a value
            parts = key.split('.')[:-1]

        for part in parts:
            if not part:
                raise ValueError('Dotted key cannot contain empty part '
                                 f'({key})')

            if part not in dct:
                dct[part] = {}
            elif not isinstance(dct[part], dict):
                raise ValueError('Dotted key does not refer to a dictionary '
                                 f'({part} of {key})')

            dct = dct[part]

        return dct

    def set_values(dct, value):
        dotted_keys = set(key for key in value if '.' in key)
        non_dotted = set(value) - dotted_keys

        for key in non_dotted:
            if key in dct:
                raise KeyError(f'Key specified multiple times: {key}')
            dct[key] = value[key]

        for key in dotted_keys:
            sub_value = value[key]
            sub_dict = expand_key(dct, key, sub_value)
            if isinstance(sub_value, dict):
                set_values(sub_dict, sub_value)
            else:
                last_part = key.split('.')[-1]
                sub_dict[last_part] = sub_value

        return dct

    return set_values(res, root)


def validate_metadata(md):
    """
    Validate a given metadata dictionary.  Expands dotted dictionary keys.

    Parameters
    ----------
    md : dict
        The metadata dictionary.

    Returns
    -------
    md : dict
        The validated metadata dictionary, with default values filled in if
        necessary.
    """
    if not md:
        return {}

    try:
        variety = md['variety']
    except KeyError:
        raise ValueError(
            'Unexpected metadata keys without variety specified: ' +
            ', '.join(md)
        ) from None

    md = expand_dotted_dict(md)

    try:
        schema = _schema_registry[variety]
    except KeyError:
        raise ValueError(
            f'Unexpected variety: {variety!r}.  Valid options: ' +
            ', '.join(_schema_registry)
        ) from None

    return schema.validate(md)


def _initialize_varieties():
    """Add all available varieties + schemas to the module-global registry."""
    for category, varieties in varieties_by_category.items():
        schema = schema_by_category[category]
        for variety in varieties:
            _schema_registry[variety] = schema


def get_metadata(cpt):
    """
    Get "variety" metadata from a component or signal.

    Parameters
    ----------
    cpt : ophyd.Component or ophyd.OphydItem
        The component / ophyd item to get the metadata for.

    Returns
    -------
    metadata : dict
        The metadata, if set. Otherwise an empty dictionary.  This metadata is
        guaranteed to be valid according to the known schemas.
    """
    if not isinstance(cpt, ophyd.Component):
        cpt = utils.get_component(cpt)

    return getattr(cpt, '_variety_metadata', {})


def set_metadata(cpt, metadata):
    """
    Set "variety" metadata on a given component.

    Expands dotted keys into sub-dictionaries.

    Validates the metadata against the known schema.

    Parameters
    ----------
    cpt : ophyd.Component
        The component for which to set the metadata.

    metadata
        The metadata to add.

    Raises
    ------
    ValueError
        If an invalid variety or no variety is specified, or ``cpt`` is not an
        :class:`ophyd.Component`.

    schema.SchemaError
        If the metadata does not adhere to the variety schema as required.
    """
    if not isinstance(cpt, ophyd.Component):
        raise ValueError(f'A component is required. Got: {type(cpt).__name__}')

    cpt._variety_metadata = validate_metadata(metadata)


_initialize_varieties()
