#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..component import Component

import ophyd


class FormattedComponent(Component, ophyd.FormattedComponent):
    """
    Subclass of ophyd.FormattedComponent to extend the formatting to the ioc
    argument. This lets us handle the IocAdmin class where the basename isn't
    necessarily related to the main pv basename.
    """
    def __init__(self, cls, suffix=None, *, lazy=True, trigger_value=None,
                 add_prefix=None, doc=None, **kwargs):
        if add_prefix is None:
            add_prefix = ('suffix', 'write_pv', 'ioc')
        super().__init__(cls, suffix=suffix, lazy=lazy,
                         trigger_value=trigger_value, add_prefix=add_prefix,
                         doc=doc, **kwargs)
