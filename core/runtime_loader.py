# -*- coding: utf-8 -*-
"""Deprecated v0.40 compatibility import.

The active runtime since v0.41.0 is :mod:`core.native_runtime`.  This tiny
wrapper is retained only so external maintenance scripts importing the old
function name do not break.
"""
from core.native_runtime import load_native_runtime


def load_runtime(root, namespace):
    return load_native_runtime(root, namespace)
