# -*- coding: utf-8 -*-
"""Soulbound v0.38.7 - canonical Bounty Board mob targets.

Prevents technical dungeon-density variants (for example a display name built as
"Grobowy Upiór — Kościany Rycerz") from becoming a public bounty target.
Existing saved kill contracts are normalized to their underlying species without
resetting progress.
"""

V0387_BOUNTY_TARGET_VERSION = "0.38.7"


def bounty_target_audit_v0387():
    errors = []
    dense_ids = []
    for tid, template in (MOB_TEMPLATES or {}).items():
        if not template.get("dense_dungeon_variant"):
            continue
        dense_ids.append(str(tid))
        base = str(template.get("dense_dungeon_base_template") or "")
        if not base:
            errors.append(f"dense variant without canonical base: {tid}")
            continue
        if base not in MOB_TEMPLATES:
            errors.append(f"dense variant base missing: {tid}->{base}")
            continue
        if canonical_bestiary_template_id(tid) != base:
            errors.append(f"dense variant not canonicalized: {tid}->{canonical_bestiary_template_id(tid)} expected {base}")
        if tid in BESTIARY_CATALOG:
            errors.append(f"dense variant leaked into Bestiary catalog: {tid}")

    probe = Session.__new__(Session)
    candidates = probe.bounty_kill_candidates()
    candidate_ids = {str(tid) for tid, _name in candidates}
    leaked = sorted(candidate_ids.intersection(dense_ids))
    if leaked:
        errors.append("dense variants leaked into bounty candidates: " + ", ".join(leaked[:10]))
    for tid, name in candidates:
        if "\ufffd" in str(name):
            errors.append(f"replacement character in bounty target name: {tid}:{name}")

    migration_checked = False
    if dense_ids:
        dense_id = dense_ids[0]
        dense = MOB_TEMPLATES[dense_id]
        base = canonical_bestiary_template_id(dense_id)
        needed = 15
        old = {
            "kind": "kill", "target": dense_id,
            "label": str(dense.get("name") or dense_id),
            "needed": needed, "progress": 7,
            "reward_soul_xp": 123, "reward_gold": 4,
        }
        clean, changed = probe.normalize_bounty_kill_entry_v0387(old)
        migration_checked = True
        expected_name = str(MOB_TEMPLATES[base].get("name") or base)
        expected_label = f"Pokonaj {needed} razy: {expected_name}"
        if not changed:
            errors.append("saved dense bounty migration did not report change")
        if str(clean.get("target")) != str(base):
            errors.append(f"saved dense bounty target not migrated: {clean.get('target')} expected {base}")
        if str(clean.get("label")) != expected_label:
            errors.append(f"saved dense bounty label not rebuilt: {clean.get('label')!r} expected {expected_label!r}")
        if int(clean.get("progress", -1)) != 7:
            errors.append("saved dense bounty migration reset progress")
        if "\ufffd" in str(clean.get("label")):
            errors.append("replacement character remains after bounty migration")

    return {
        "version": V0387_BOUNTY_TARGET_VERSION,
        "dense_variants": len(dense_ids),
        "bounty_candidates": len(candidates),
        "migration_checked": migration_checked,
        "error_count": len(errors),
        "errors": errors,
    }


BOUNTY_CANONICAL_TARGET_AUDIT_V0387 = bounty_target_audit_v0387()
if BOUNTY_CANONICAL_TARGET_AUDIT_V0387["error_count"]:
    raise RuntimeError(
        "Bounty Canonical Target Audit v0.38.7 failed: "
        + "; ".join(BOUNTY_CANONICAL_TARGET_AUDIT_V0387["errors"][:100])
    )

HELP_TOPICS.setdefault("bounty", []).append(
    "v0.38.7: kontrakty zabójstw losują tylko kanoniczne gatunki mobów; techniczne warianty lochowe z podwójnymi nazwami nie są osobnymi celami."
)
HELP_TOPICS.setdefault("zlecenia", HELP_TOPICS.get("bounty", []))
