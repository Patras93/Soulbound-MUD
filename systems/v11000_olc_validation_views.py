# -*- coding: utf-8 -*-
"""V110: read-only catalogue views for OLC validation.

Avoid rebuilding six-figure item dictionaries for resource-only edits.  The
original registries are NOT changed.  All normal validation still runs.
"""


def combined_catalog(original, additions):
    """Return the existing registry unless a staged overlay actually exists.

    Only callers which *read* this mapping may use this helper. A real overlay
    is a fresh dictionary and never mutates the shared registry.
    """
    return {**original, **additions} if additions else original


def quest_dependency_view(original, additions, changes):
    """Keep full cycle validation without copying all quests on unrelated edits."""
    if not additions and not changes:
        return original
    merged = {key: dict(value) for key, value in original.items()}
    merged.update({key: dict(value) for key, value in additions.items()})
    for key, patch in changes.items():
        merged[key] = dict(merged.get(key, {}), **patch)
    return merged
