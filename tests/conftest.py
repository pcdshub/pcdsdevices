#!/usr/bin/env python
# -*- coding: utf-8 -*-
import inspect

def get_classes_in_module(module, subcls=None):
    classes = []
    all_classes = inspect.getmembers(module)
    for _, cls in all_classes:
        try:
            if cls.__module__ == module.__name__:
                if subcls is not None:
                    try:
                        if not issubclass(cls, subcls):
                            continue
                    except TypeError:
                        continue
                classes.append(cls)
        except AttributeError:
            pass    
    return classes
