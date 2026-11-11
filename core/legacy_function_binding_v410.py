# -*- coding: utf-8 -*-
"""Preserve late-bound original module globals for factored historical functions.

The game runtime resolves many historical names after module import. Moving the
function body into an ordinary helper module would redirect those references
and can silently change the game. This adapter uses the original Python code
object, unmodified, with its original module's live global namespace.
"""
from types import FunctionType


def bind_legacy_function_v410(source, namespace):
    if source.__closure__:
        raise ValueError(f"Historical closure requires explicit refactor: {source.__name__}")
    fn = FunctionType(source.__code__, namespace, source.__name__, source.__defaults__)
    fn.__kwdefaults__ = source.__kwdefaults__
    fn.__annotations__ = dict(source.__annotations__)
    fn.__dict__.update(source.__dict__)
    fn.__qualname__ = source.__qualname__
    fn.__module__ = namespace['__name__']
    return fn
