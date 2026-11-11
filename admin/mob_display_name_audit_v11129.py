# -*- coding: utf-8 -*-
"""Predeploy audit: every runtime mob must expose one clear display name."""

def audit_mob_display_names_v11129(server_module):
    mobs = getattr(server_module, "MOB_TEMPLATES", {})
    errors = []
    checked = 0
    for mob_id, template in mobs.items():
        if not isinstance(template, dict):
            continue
        checked += 1
        name = str(template.get("name") or "").strip()
        if not name:
            errors.append(f"{mob_id}: empty mob name")
            continue
        # NEMESIS is the only deliberate rank marker using an em dash.
        if " — " in name and "NEMESIS" not in name:
            errors.append(f"{mob_id}: compound mob name: {name}")
    return {"checked": checked, "errors": errors, "error_count": len(errors)}
