#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility functions and/or classes that fall within the Python standard library.
"""

def isnumber(obj):
    """
    Checks if the input is a number.

    Parameters
    ----------
    obj : object
        Object to test if it is an number.

    Returns
    -------
    bool : bool
        True if the obj is a number, False if not.    
    """
    if isinstance(obj, str):
        try:
            float(obj)
            return True
        except ValueError:
            return False
    elif isinstance(obj, float) or isinstance(obj, int):
        return True
    else:
        return False
