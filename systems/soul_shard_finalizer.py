# -*- coding: utf-8 -*-
"""Final Soul Shard guarantee for Crypt content.

Loaded at the very end of the gameplay runtime, after Generator Core and all
Crypt difficulty/reward layers.  Older milestone fixes ran too early and their
1.0 authored chances could later be numerically rebalanced down again.
"""

from data.mobs import MOB_TEMPLATES

SOUL_SHARD_FINALIZER_VERSION = "0.71.1"


def _is_crypt_soul_shard_template_v0711(template_id, template):
    if not isinstance(template, dict):
        return False
    try:
        crypt_floor = int(template.get("crypt_floor", 0) or 0)
    except Exception:
        crypt_floor = 0
    try:
        mythic_floor = int(template.get("mythic_crypt_floor", 0) or 0)
    except Exception:
        mythic_floor = 0
    if crypt_floor > 0 or mythic_floor > 0:
        return True
    if template.get("crypt_boss") or template.get("mythic_crypt_boss"):
        return True
    if str(template_id) in {"skeleton", "crypt_wraith"}:
        return True
    for key in ("elite_base_template", "rare_base_template", "base_template", "template_id"):
        base_id = str(template.get(key) or "")
        if base_id in {"skeleton", "crypt_wraith"}:
            return True
        base = MOB_TEMPLATES.get(base_id)
        if isinstance(base, dict):
            try:
                if int(base.get("crypt_floor", 0) or 0) > 0 or int(base.get("mythic_crypt_floor", 0) or 0) > 0:
                    return True
            except Exception:
                pass
    return False


def _force_crypt_soul_shard_v0711(template_id, template):
    if not _is_crypt_soul_shard_template_v0711(template_id, template):
        return False
    drops = template.setdefault("drops", {})
    if not isinstance(drops, dict):
        template["drops"] = drops = {}
    drops["soul_shard"] = 1.0
    return True


def finalize_crypt_soul_shards_v0711():
    touched = 0
    regular = 0
    mythic = 0
    bosses = 0
    variants = 0
    classic = 0
    errors = []
    for template_id, template in list(MOB_TEMPLATES.items()):
        if not _force_crypt_soul_shard_v0711(template_id, template):
            continue
        touched += 1
        if template_id in {"skeleton", "crypt_wraith"}:
            classic += 1
        if template.get("crypt_boss") or template.get("mythic_crypt_boss"):
            bosses += 1
        if template.get("elite_mob") or template.get("rare_mob") or template.get("elite_base_template") or template.get("rare_base_template"):
            variants += 1
        if int(template.get("mythic_crypt_floor", 0) or 0) > 0:
            mythic += 1
        elif int(template.get("crypt_floor", 0) or 0) > 0:
            regular += 1

    # Audit the exact final runtime values, not the authored pre-generator data.
    for template_id, template in MOB_TEMPLATES.items():
        if not _is_crypt_soul_shard_template_v0711(template_id, template):
            continue
        drops = template.get("drops") or {}
        try:
            chance = float(drops.get("soul_shard", 0) or 0)
        except Exception:
            chance = 0.0
        if chance < 1.0:
            errors.append(f"{template_id}: soul_shard={chance}, expected 1.0")

    return {
        "version": SOUL_SHARD_FINALIZER_VERSION,
        "templates_guaranteed": touched,
        "regular_crypt": regular,
        "mythic_crypt": mythic,
        "bosses": bosses,
        "elite_rare_variants": variants,
        "classic_entry_templates": classic,
        "error_count": len(errors),
        "errors": errors,
    }


# Final boot-time pass after every earlier generator/rebalance layer.
SOUL_SHARD_CRYPT_FINAL_AUDIT_V0711 = finalize_crypt_soul_shards_v0711()
if SOUL_SHARD_CRYPT_FINAL_AUDIT_V0711["error_count"]:
    raise RuntimeError(
        "Soul Shard Crypt Finalizer v0.71.1 failed: "
        + "; ".join(SOUL_SHARD_CRYPT_FINAL_AUDIT_V0711["errors"][:100])
    )
