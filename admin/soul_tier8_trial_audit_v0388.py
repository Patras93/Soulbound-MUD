# -*- coding: utf-8 -*-
"""Soulbound v0.38.8 - easier Soul Weapon Tier 8 trial guard."""

V0388_SOUL_TIER8_TRIAL_VERSION = "0.38.8"

def soul_tier8_trial_audit_v0388():
    errors=[]
    q=QUESTS.get("soul_tier_08_trial") or {}
    if q.get("target") != "cemetery_bell_wraith":
        errors.append(f"Tier 8 target={q.get('target')!r}, expected cemetery_bell_wraith")
    if int(q.get("needed",0) or 0) != 5:
        errors.append(f"Tier 8 needed={q.get('needed')!r}, expected 5")
    desc=str(q.get("description", ""))
    if "5 Upiorów Dzwonu" not in desc:
        errors.append("Tier 8 description does not name 5 Upiorów Dzwonu")
    tmpl=MOB_TEMPLATES.get("cemetery_bell_wraith") or {}
    if tmpl.get("boss") or tmpl.get("world_boss") or tmpl.get("boss_mechanic"):
        errors.append("Tier 8 target is still classified as a boss")
    spawns=[rid for rid,mid in MOB_SPAWNS if mid == "cemetery_bell_wraith"]
    if len(spawns) < 5:
        errors.append(f"Tier 8 has only {len(spawns)} simultaneous bell-wraith spawns, expected at least 5")
    return {
        "version": V0388_SOUL_TIER8_TRIAL_VERSION,
        "target": q.get("target"),
        "needed": int(q.get("needed",0) or 0),
        "spawn_count": len(spawns),
        "spawn_rooms": spawns,
        "error_count": len(errors),
        "errors": errors,
    }

SOUL_TIER8_TRIAL_AUDIT_V0388 = soul_tier8_trial_audit_v0388()
if SOUL_TIER8_TRIAL_AUDIT_V0388["error_count"]:
    raise RuntimeError(
        "Soul Tier 8 Trial Audit v0.38.8 failed: "
        + "; ".join(SOUL_TIER8_TRIAL_AUDIT_V0388["errors"][:50])
    )

HELP_TOPICS.setdefault("proba duszy", []).append(
    "Tier 8: pokonaj 5 Upiorów Dzwonu na Starym Cmentarzu. Pierwsza próba bossowa zaczyna się od Tieru 9."
)
HELP_TOPICS.setdefault("próba duszy", []).append(
    "Tier 8: pokonaj 5 Upiorów Dzwonu na Starym Cmentarzu. Pierwsza próba bossowa zaczyna się od Tieru 9."
)
