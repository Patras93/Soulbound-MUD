# -*- coding: utf-8 -*-
"""Soulbound v1.11.97 - final public HELP truth pass.

admin/audits.py still contains historical HELP writers.  This module is loaded
immediately afterwards so player-visible help ends in the current 1-600 truth.
It intentionally defines no new helper functions; it reuses the audited refresh
functions authored in admin/help_refresh.py through the legacy compatibility
runtime namespace.
"""

refresh_help_truth_v11197()
refresh_public_help_surface_v11197()

HELP_TRUTH_AUDIT_V11197 = help_truth_audit_v11197()
HELP_SURFACE_AUDIT_V11197 = help_surface_audit_v11197()

_help_errors_v11197 = []
_help_errors_v11197.extend(HELP_TRUTH_AUDIT_V11197.get("errors", ()))
_help_errors_v11197.extend(HELP_SURFACE_AUDIT_V11197.get("errors", ()))
if _help_errors_v11197:
    raise RuntimeError(
        "Final HELP Truth Audit v1.11.97 failed: "
        + "; ".join(str(error) for error in _help_errors_v11197[:100])
    )
