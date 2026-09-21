# -*- coding: utf-8 -*-
"""Soulbound v0.38.9 - canonical kill quest credit guard."""

V0389_QUEST_KILL_CREDIT_VERSION = "0.38.9"


def quest_kill_credit_audit_v0389():
    errors = []
    checked_variants = 0

    helper = globals().get("quest_kill_targets_v0389")
    if not callable(helper):
        errors.append("quest_kill_targets_v0389 missing")
        return {
            "version": V0389_QUEST_KILL_CREDIT_VERSION,
            "checked_variants": 0,
            "bell_wraith_variants": 0,
            "error_count": len(errors),
            "errors": errors,
        }

    q = QUESTS.get("soul_tier_08_trial") or {}
    if q.get("kind") != "kill" or q.get("target") != "cemetery_bell_wraith":
        errors.append(
            f"Tier 8 quest target invalid: kind={q.get('kind')!r}, target={q.get('target')!r}"
        )

    bell_variants = []
    for mob_id, template in MOB_TEMPLATES.items():
        canonical = canonical_bestiary_template_id(mob_id)
        if canonical != mob_id:
            checked_variants += 1
            targets = set(helper(mob_id, template))
            if canonical not in targets:
                errors.append(f"{mob_id}: canonical target {canonical} not credited")
        if canonical == "cemetery_bell_wraith":
            bell_variants.append(mob_id)
            targets = set(helper(mob_id, template))
            if "cemetery_bell_wraith" not in targets:
                errors.append(f"{mob_id}: does not credit cemetery_bell_wraith")

    if len(bell_variants) < 3:
        errors.append(f"too few Bell Wraith variants checked: {len(bell_variants)}")

    # Base aliases authored on the canonical species must also survive generated variants.
    base_aliases = set((MOB_TEMPLATES.get("cemetery_bell_wraith") or {}).get("quest_targets") or ())
    for mob_id in bell_variants:
        targets = set(helper(mob_id, MOB_TEMPLATES.get(mob_id) or {}))
        missing = base_aliases - targets
        if missing:
            errors.append(f"{mob_id}: missing base quest aliases {sorted(missing)}")

    return {
        "version": V0389_QUEST_KILL_CREDIT_VERSION,
        "checked_variants": checked_variants,
        "bell_wraith_variants": len(bell_variants),
        "error_count": len(errors),
        "errors": errors,
    }


QUEST_KILL_CANONICALIZATION_AUDIT_V0389 = quest_kill_credit_audit_v0389()
if QUEST_KILL_CANONICALIZATION_AUDIT_V0389["error_count"]:
    raise RuntimeError(
        "Canonical Kill Quest Credit Audit v0.38.9 failed: "
        + "; ".join(QUEST_KILL_CANONICALIZATION_AUDIT_V0389["errors"][:100])
    )

HELP_TOPICS.setdefault("questy", []).append(
    "v0.38.9: kill questy zaliczają zwykłe, Elite, Rare i proceduralne warianty tego samego gatunku przez kanoniczny cel bazowy."
)
