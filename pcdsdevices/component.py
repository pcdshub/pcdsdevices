#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ophyd


class Component(ophyd.Component):
    """
    Subclass of ophyd.Component to set lazy=True
    """
    def __init__(self, cls, suffix=None, *, lazy=True, trigger_value=None,
                 add_prefix=None, doc=None, **kwargs):
        super().__init__(cls, suffix=suffix, lazy=lazy,
                         trigger_value=trigger_value, add_prefix=add_prefix,
                         doc=doc, **kwargs)
