# -*- coding: utf-8 -*-
"""Runtime-safe release proof contract; no imports from offline validation.

When mandatory universal gates are added/removed, change this count together
with the test suite. Linux rejects stale prior-release receipts (e.g. 24/24).
"""
UNIVERSAL_REQUIRED_GATES = 30
