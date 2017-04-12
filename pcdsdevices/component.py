#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Modifications to ophyd.Component that I'm going to use repeatedly across lcls
devices.

lazy=True instead of False default
add __copy__ method

For formatted components, put "ioc" onto default add_prefix so it gets
formatted as well.
"""
from copy import copy
from ophyd import Component, FormattedComponent


class PcdsComponent(Component):
    def __init__(self, cls, suffix=None, *, lazy=True, trigger_value=None,
                 add_prefix=None, doc=None, **kwargs):
        super().__init__(cls, suffix=suffix, lazy=lazy,
                         trigger_value=trigger_value, add_prefix=add_prefix,
                         doc=doc, **kwargs)

    def __copy__(self):
        add_prefix = copy(self.add_prefix)
        kwargs = copy(self.kwargs)
        return self.__class__(self.cls, suffix=self.suffix, lazy=self.lazy,
                              trigger_value=self.trigger_value,
                              add_prefix=add_prefix, doc=self.doc,
                              **kwargs)


class PcdsFormattedComponent(PcdsComponent, FormattedComponent):
    def __init__(self, cls, suffix=None, *, lazy=True, trigger_value=None,
                 add_prefix=None, doc=None, **kwargs):
        if add_prefix is None:
            add_prefix = ('suffix', 'write_pv', 'ioc')
        super().__init__(cls, suffix=suffix, lazy=lazy,
                         trigger_value=trigger_value, add_prefix=add_prefix,
                         doc=doc, **kwargs)
