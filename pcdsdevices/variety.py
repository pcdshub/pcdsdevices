"""Additional component metadata, classifying each into a "variety"."""

import schema

import ophyd

from . import utils

_schema_registry = {}
varieties_by_category = {
    'command': {
        'command',
        'command-proc',
        'command-enum',
        'command-setpoint-tracks-readback',
    },
    'tweakable': {
        'tweakable'
    },
    'array': {
        'array-timeseries',
        'array-histogram',
        'array-image',
        'array-nd',
    },
    'scalar': {
        'scalar',
        'scalar-range',
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


schema_by_category = {
    'command': schema.Schema({
        'variety': schema.Or(*varieties_by_category['command']),
        schema.Optional('value', default=1): schema.Or(float, int, str),
        schema.Optional('enum_strings'): [str],
        # schema.Optional('enum_dict'): dict,
    }),

    'tweakable': schema.Schema({
        'variety': schema.Or(*varieties_by_category['tweakable']),
        'delta': schema.Or(float, int),
        schema.Optional('delta_range'): _length_validate(2, 2, (float, int)),
        schema.Optional('source_signal'): str,
        schema.Optional('source'): schema.Or('setpoint', 'readback',
                                             'other-signal'),
    }),

    'array': schema.Schema({
        'variety': schema.Or(*varieties_by_category['array']),
        schema.Optional('shape'): _length_validate(1, 10, int),
        schema.Optional('dimension'): int,
        schema.Optional('embed'): bool,
        schema.Optional('colormap'): str,
    }),

    'scalar': schema.Schema({
        'variety': schema.Or(*varieties_by_category['scalar']),
        schema.Optional('range'): _length_validate(2, 2, (float, int)),
        schema.Optional('range_source'): schema.Or('use_limits', 'custom'),
    }),

    'text': schema.Schema({
        'variety': schema.Or(*varieties_by_category['text']),
        schema.Optional('enum_strings'): [str],
    }),

    'enum': schema.Schema({
        'variety': schema.Or(*varieties_by_category['enum']),
        schema.Optional('enum_strings'): [str],
    }),
}


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
        return {}

    try:
        variety = md['variety']
    except KeyError:
        raise ValueError(
            'Unexpected metadata keys without variety specified: ' +
            ', '.join(md)
        ) from None

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
