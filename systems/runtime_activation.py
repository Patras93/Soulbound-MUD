# -*- coding: utf-8 -*-
"""Stable runtime authorization API for Soulbound releases.

All runtime features use the same module, regardless of release number.
Legacy installers or activators are never imported by the new game.
"""
from systems.universal_activation import (
    ROOT, VERSION, MARKER, REQUIRED, activation_manifest,
    authorized_mode, enabled, production_approved, sha, verify,
)

__all__ = (
    'ROOT', 'VERSION', 'MARKER', 'REQUIRED', 'activation_manifest',
    'authorized_mode', 'enabled', 'production_approved', 'sha', 'verify',
)
