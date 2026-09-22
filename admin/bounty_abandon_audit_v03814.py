# -*- coding: utf-8 -*-
"""Soulbound v0.38.14 - bounty abandon command audit."""

def bounty_abandon_audit_v03814():
    errors = []
    method = getattr(globals().get("SessionWorldProgressionMixin"), "handle_bounty", None)
    consts = repr(getattr(getattr(method, "__code__", None), "co_consts", ()))
    for token in ("porzuc", "Porzucono kontrakt", "Oferty na Tablicy Zleceń pozostały bez zmian"):
        if token not in consts:
            errors.append("handle_bounty missing: " + token)
    help_rows = HELP_TOPICS.get("bounty_contracts", [])
    if not any("bounty porzuć" in str(row) and "bounty porzuc" in str(row) for row in help_rows):
        errors.append("HELP missing bounty porzuć/porzuc aliases")
    return {
        "version": "0.38.14",
        "error_count": len(errors),
        "errors": errors,
    }

BOUNTY_ABANDON_AUDIT_V03814 = bounty_abandon_audit_v03814()
if BOUNTY_ABANDON_AUDIT_V03814["error_count"]:
    raise RuntimeError("Bounty Abandon Audit v0.38.14 failed: " + "; ".join(BOUNTY_ABANDON_AUDIT_V03814["errors"][:50]))
