#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ophyd.Component overrides
"""
from copy import copy

import ophyd


class Component(ophyd.Component):
    """
    Subclass of ophyd.Component to set lazy=True and to add a __copy__
    method.
    """
    def __init__(self, cls, suffix=None, *, lazy=True, trigger_value=None,
                 add_prefix=None, doc=None, **kwargs):
        super().__init__(cls, suffix=suffix, lazy=lazy,
                         trigger_value=trigger_value, add_prefix=add_prefix,
                         doc=doc, **kwargs)

    def __copy__(self):
        """
        Allows use of the copy module to duplicate a Component object for
        tweaks in a subclass.
        """
        add_prefix = copy(self.add_prefix)
        kwargs = copy(self.kwargs)
        return self.__class__(self.cls, suffix=self.suffix, lazy=self.lazy,
                              trigger_value=self.trigger_value,
                              add_prefix=add_prefix, doc=self.doc,
                              **kwargs)
