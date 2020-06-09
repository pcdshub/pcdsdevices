"""
Additional component metadata, classifying each into a "variety".

TODO, something like the following:

    def get_component_metadata(cpt):
       if not isinstance(cpt, Component):
           return get_component_metadata(get_component_from_signal(cpt))
        return cpt.additional_metadata
"""
import schema

COMMAND_VARIETIES = (
    'command',
    'command-proc',
    'command-enum',
    'command-setpoint-tracks-readback',
)

TWEAKABLE_VARIETIES = [
    'tweakable',
]

ARRAY_VARIETIES = [
    'array-timeseries',
    'array-histogram',
    'array-image',
    'array-nd',
]

SCALAR_VARIETIES = [
    'scalar',
    'scalar-range',
]

TEXT_VARIETIES = [
    'text',
    'text-multiline',
    'text-enum',
]

ENUM_VARIETIES = [
    'enum',
]

OTHER_VARIETIES = [
    'unknown',
]

_schemas = {}


def add_variety_schema(variety, schema):
    _schemas[variety] = schema


def validate_metadata(md):
    """
    Validate a given metadata dictionary.

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
        return md

    try:
        variety = md['variety']
    except KeyError:
        raise ValueError(
            'Unexpected metadata keys without variety specified: ' +
            ', '.join(md)
        ) from None

    try:
        schema = _schemas[variety]
    except KeyError:
        raise ValueError(
            f'Unexpected variety: {variety!r}.  Valid options: ' +
            ', '.join(_schemas)
        ) from None

    return schema.validate(md)


COMMAND_SCHEMA = schema.Schema(
    {
        'variety': schema.Or(*COMMAND_VARIETIES),
        schema.Optional('value', default=1): schema.Or(float, int, str),
        schema.Optional('enum_strings'): [str],
        # schema.Optional('enum_dict'): dict,
    },
    description="Schema for the 'command' variety"
)


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


TWEAKABLE_SCHEMA = schema.Schema(
    {
        'variety': schema.Or(*TWEAKABLE_VARIETIES),
        'value': schema.Or(float, int),
        schema.Optional('value_range'): _length_validate(2, 2, (float, int)),
        schema.Optional('source_signal'): str,
        schema.Optional('source'): schema.Or('setpoint', 'readback',
                                             'other-signal'),
    },
    description="Schema for the 'tweakable' variety"
)

ARRAY_SCHEMA = schema.Schema(
    {
        'variety': schema.Or(*ARRAY_VARIETIES),
        schema.Optional('shape'): _length_validate(1, 10, int),
        schema.Optional('dimension'): int,
    },
    description="Schema for the 'array' variety"
)

SCALAR_SCHEMA = schema.Schema(
    {
        'variety': schema.Or(*SCALAR_VARIETIES),
        schema.Optional('range'): _length_validate(2, 2, (float, int)),
        schema.Optional('range_source'): schema.Or('use_limits', 'custom'),
    },
    description="Schema for the 'scalar' variety"
)

TEXT_SCHEMA = schema.Schema(
    {
        'variety': schema.Or(*TEXT_VARIETIES),
        schema.Optional('enum_strings'): [str],
    },
    description="Schema for the 'text' variety"
)

ENUM_SCHEMA = schema.Schema(
    {
        'variety': schema.Or(*ENUM_VARIETIES),
        schema.Optional('enum_strings'): [str],
    },
    description="Schema for the 'enum' variety"
)

for variety in COMMAND_VARIETIES:
    add_variety_schema(variety, COMMAND_SCHEMA)

for variety in TWEAKABLE_VARIETIES:
    add_variety_schema(variety, TWEAKABLE_SCHEMA)

for variety in ARRAY_VARIETIES:
    add_variety_schema(variety, ARRAY_SCHEMA)

for variety in SCALAR_VARIETIES:
    add_variety_schema(variety, SCALAR_SCHEMA)

for variety in TEXT_VARIETIES:
    add_variety_schema(variety, TEXT_SCHEMA)

for variety in ENUM_VARIETIES:
    add_variety_schema(variety, ENUM_SCHEMA)
