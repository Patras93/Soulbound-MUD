# -*- coding: utf-8 -*-
"""Current Soulbound activation API, independent of historical release gates.

Gameplay imports this stable API instead of routing authorization through
v107-v111 activators. Only the current release verifies its own signed-off
file manifest or the explicitly isolated current staging database contract.
No historical release flag, installer, archive or approval file is consulted.
"""
from systems.v11200_activation import (
    ROOT, VERSION, MARKER, REQUIRED, activation_manifest, authorized_mode,
    enabled, production_approved, sha, verify,
)

__all__ = (
    'ROOT', 'VERSION', 'MARKER', 'REQUIRED', 'activation_manifest',
    'authorized_mode', 'enabled', 'production_approved', 'sha', 'verify',
)
