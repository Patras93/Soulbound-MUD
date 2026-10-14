# -*- coding: utf-8 -*-
"""One-to-one method code binding without changing inheritance or MRO.

The historical session methods resolve explicit module imports at call time.
When moving code between files we must preserve the ORIGINAL host module's
namespace (same principle as the top-level functions extracted in v4.10.0).
"""
from types import FunctionType


def bind_legacy_method_v4200(source, namespace, owner_name):
    if source.__closure__ or source.__code__.co_freevars:
        raise ValueError(f"Unsupported closure in {source.__name__}")
    method = FunctionType(source.__code__, namespace, source.__name__, source.__defaults__)
    method.__kwdefaults__ = source.__kwdefaults__
    method.__annotations__ = dict(source.__annotations__)
    method.__dict__.update(source.__dict__)
    method.__qualname__ = owner_name + '.' + source.__name__
    method.__module__ = namespace['__name__']
    return method
