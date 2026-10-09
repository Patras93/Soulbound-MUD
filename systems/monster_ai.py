# -*- coding: utf-8 -*-
"""Soulbound 1.16.0: finite, combat-local AI for ordinary monsters and elites.

One decision per mob's own round. No new permanent mob templates or DB schema.
Existing authored bosses, quest NPCs and UOSS encounters keep their scripts.
"""
import time

from data.mobs import MOB_TEMPLATES

SUPPORT_COOLDOWN = 14.0
SUPPORT_DURATION = 10.0
SUMMON_LIFETIME = 120.0

PROTECTED_FLAGS = (
    "training_dummy", "uoss_superboss", "uoss_unique_superboss_key",
    "boss_mechanic", "world_boss", "mini_boss", "crypt_boss",
    "astral_boss", "mythic_crypt_boss", "mythic_astral_boss",
    "v018_legendary_event_boss", "v020_mythic_world_boss",
    "guild_boss", "profession_dungeon_boss", "source_xp_exact",
)


def monster_ai_necromancer_v1160(template):
    # Cursed elites are the existing necromantic variant in the real catalog.
    # Named necromancers/liches are also supported when future zones add them.
    if str(template.get("elite_affix") or "") == "cursed":
        return True
    name = (str(template.get("name") or "") + " " + str(template.get("creature_type") or "")).casefold()
    return any(token in name for token in ("nekroman", "necroman", "lich", "nekrom", "necrom"))


def monster_ai_eligible_v1160(mob, template):
    if not mob or not getattr(mob, "alive", False) or not getattr(mob, "engaged_by", None):
        return False
    if any(template.get(flag) for flag in PROTECTED_FLAGS):
        return False
    if getattr(mob, "monster_ai_summoned_v1160", False):
        return False
    return bool(template.get("elite_affix") or template.get("damage_type") == "magic" or monster_ai_necromancer_v1160(template))


def _max_hp(mob, template):
    return max(1, int(getattr(mob, "adaptive_max_hp_v11330", 0) or template.get("max_hp", 1) or 1))


def monster_ai_attack_multiplier_v1160(mob, now=None):
    now = time.monotonic() if now is None else float(now)
    if now >= float(getattr(mob, "monster_ai_empowered_until_v1160", 0) or 0):
        return 1.0
    # v1.23: each ordinary boss phase has a distinct offensive escalation;
    # the player's own damage never receives an artificial cap.
    return max(1.18, float(getattr(mob, "v1230_phase_attack_multiplier", 1.0) or 1.0))


def monster_ai_guard_damage_v1160(mob, damage, now=None):
    """One source of guarded damage handling for basic attacks and most skills."""
    now = time.monotonic() if now is None else float(now)
    damage = max(0, int(damage))
    if damage and now < float(getattr(mob, "monster_ai_guard_until_v1160", 0) or 0):
        return max(1, int(round(damage * 0.80)))
    return damage


def monster_ai_plan_v1160(mob, template, live_allies, dead_allies=(), now=None):
    """Purely select the action; the caller executes it once, before party targeting."""
    now = time.monotonic() if now is None else float(now)
    if not monster_ai_eligible_v1160(mob, template):
        return None
    turn = max(0, int(getattr(mob, "combat_turn", 0) or 0))
    if turn < 3 or turn % 3 or now < float(getattr(mob, "monster_ai_next_action_v1160", 0) or 0):
        return None
    engaged = [a for a in live_allies if a.alive and a.room_id == mob.room_id and a.engaged_by == mob.engaged_by]
    heal_targets = [mob] + [a for a in engaged if a.key != mob.key]
    injured = []
    for ally in heal_targets:
        if getattr(ally, "monster_ai_summoned_v1160", False):
            continue
        cap = _max_hp(ally, template if ally.key == mob.key else MOB_TEMPLATES.get(ally.template_id, template))
        if ally.hp * 100 < cap * 58:
            injured.append((ally.hp / cap, ally))
    caster = template.get("damage_type") == "magic" or monster_ai_necromancer_v1160(template)
    affix = str(template.get("elite_affix") or "")
    if injured and (caster or affix == "regenerating"):
        return {"kind": "heal", "target": min(injured, key=lambda pair: pair[0])[1]}
    if monster_ai_necromancer_v1160(template) and not getattr(mob, "monster_ai_resurrect_used_v1160", False):
        dead = [m for m in dead_allies if not m.alive and m.room_id == mob.room_id
                and not getattr(m, "v016_ephemeral", False)
                and not getattr(m, "monster_ai_raised_once_v1160", False)
                and m.template_id != mob.template_id]
        if dead:
            return {"kind": "resurrect", "target": dead[0]}
    if caster and turn >= 6 and not getattr(mob, "monster_ai_summon_used_v1160", False):
        return {"kind": "summon", "target": mob}
    guards = [a for a in engaged if a.key != mob.key and not getattr(a, "monster_ai_summoned_v1160", False)
              and now >= float(getattr(a, "monster_ai_guard_until_v1160", 0) or 0)]
    if guards and (affix in ("armored", "regenerating") or caster or
                   any(a.hp * 100 < _max_hp(a, MOB_TEMPLATES.get(a.template_id, {})) * 75 for a in guards)):
        return {"kind": "guard", "target": guards[0]}
    if now >= float(getattr(mob, "monster_ai_empowered_until_v1160", 0) or 0):
        return {"kind": "buff", "target": mob}
    return None


def monster_ai_execute_v1160(world, mob, template, plan, now=None):
    """Execute finite support action. Summons are encounter-local, unrewarded."""
    if not plan or not mob.alive:
        return ""
    now = time.monotonic() if now is None else float(now)
    kind, target = plan["kind"], plan["target"]
    name = str(template.get("name") or mob.template_id)
    target_template = world.mob_templates_for_ai_v1160(target)
    target_name = str(target_template.get("name") or target.template_id)
    text = ""
    if kind == "heal" and target.alive:
        cap = _max_hp(target, target_template)
        amount = min(max(0, cap - target.hp), max(1, (cap * 18) // 100))
        if amount:
            target.hp += amount
            text = f"{name} rzuca Uzdrowienie: {target_name} odzyskuje {amount} HP."
    elif kind == "guard" and target.alive:
        target.monster_ai_guard_until_v1160 = now + SUPPORT_DURATION
        text = f"{name} osłania {target_name} na {int(SUPPORT_DURATION)} sekund (20% mniej obrażeń)."
    elif kind == "buff":
        mob.monster_ai_empowered_until_v1160 = now + SUPPORT_DURATION
        text = f"{name} używa Wzmocnienia: +18% obrażeń przez {int(SUPPORT_DURATION)} sekund."
    elif kind in ("summon", "resurrect"):
        summoned = world.spawn_monster_ai_add_v1160(mob, target.template_id, now=now)
        if summoned:
            if kind == "resurrect":
                target.monster_ai_raised_once_v1160 = True
                mob.monster_ai_resurrect_used_v1160 = True
                mob.monster_ai_summon_used_v1160 = True
                text = f"{name} wskrzesza cień {target_name}; przyzwanie znika po walce i nie daje ponownych nagród."
            else:
                mob.monster_ai_summon_used_v1160 = True
                text = f"{name} przywołuje pomocnika do walki (maksymalnie jeden na starcie)."
    if text:
        mob.monster_ai_next_action_v1160 = now + (24.0 if kind in ("summon", "resurrect") else SUPPORT_COOLDOWN)
    return text


def monster_ai_lifesteal_v1160(mob, template, damage, now=None):
    """Only real landed damage feeds vampiric heal; once per mob round."""
    if str(template.get("elite_affix") or "") != "vampiric" or not mob.alive or damage <= 0:
        return 0
    turn = int(getattr(mob, "combat_turn", 0) or 0)
    if int(getattr(mob, "monster_ai_lifesteal_turn_v1160", -1)) == turn:
        return 0
    cap = _max_hp(mob, template)
    amount = min(max(0, cap - mob.hp), max(1, int(damage * .25)), max(1, (cap * 4) // 100))
    mob.monster_ai_lifesteal_turn_v1160 = turn
    mob.hp += amount
    return amount


def monster_ai_audit_v1160():
    from types import SimpleNamespace
    errors, checks = [], 0
    def check(cond, message):
        nonlocal checks
        checks += 1
        if not cond:
            errors.append(message)
    def mob(key, hp=100, turn=3, alive=True):
        return SimpleNamespace(key=key, template_id=key, room_id="arena", engaged_by="gracz",
                               hp=hp, alive=alive, combat_turn=turn)
    mage = {"name": "Nekromanta", "max_hp": 100, "damage_type": "magic"}
    skeleton = {"name": "Szkielet", "max_hp": 100, "damage_type": "physical"}
    m = mob("necro", 40)
    check(monster_ai_plan_v1160(m, mage, [m], [], now=100)["kind"] == "heal", "heal priority")
    m.hp = 100
    dead = mob("skeleton", alive=False)
    check(monster_ai_plan_v1160(m, mage, [m], [dead], now=100)["kind"] == "resurrect", "necro revive")
    m.monster_ai_resurrect_used_v1160 = True
    m.combat_turn = 6
    check(monster_ai_plan_v1160(m, mage, [m], [], now=100)["kind"] == "summon", "mage summon")
    m.monster_ai_summon_used_v1160 = True
    check(monster_ai_plan_v1160(m, mage, [m], [], now=100)["kind"] == "buff", "mage buff")
    m.monster_ai_next_action_v1160 = 114
    check(monster_ai_plan_v1160(m, mage, [m], [], now=101) is None, "cooldown")
    check(monster_ai_plan_v1160(m, mage, [m], [], now=115) is not None, "cooldown expires")
    m.monster_ai_guard_until_v1160 = 110
    check(monster_ai_guard_damage_v1160(m, 100, now=105) == 80, "guard reduces")
    check(monster_ai_guard_damage_v1160(m, 100, now=111) == 100, "guard expires")
    m.monster_ai_empowered_until_v1160 = 110
    check(monster_ai_attack_multiplier_v1160(m, 109) > 1 and monster_ai_attack_multiplier_v1160(m, 111) == 1, "buff expires")
    check(monster_ai_eligible_v1160(m, {"uoss_superboss": True, **mage}) is False, "authored boss protected")
    check(monster_ai_eligible_v1160(m, skeleton) is False, "ordinary mob uses basic AI")
    check(monster_ai_necromancer_v1160({"elite_affix": "cursed"}), "cursed elites may resurrect")
    vampire = mob("vamp", hp=50)
    vamp_template = {"name": "Wampir", "max_hp": 100, "elite_affix": "vampiric"}
    check(monster_ai_lifesteal_v1160(vampire, vamp_template, 20) == 4, "vampire heals landed damage")
    check(monster_ai_lifesteal_v1160(vampire, vamp_template, 20) == 0, "vampire once per round")
    vampire.combat_turn += 1
    check(monster_ai_lifesteal_v1160(vampire, vamp_template, 0) == 0, "vampire misses")
    summoned = mob("add")
    summoned.monster_ai_summoned_v1160 = True
    check(not monster_ai_eligible_v1160(summoned, mage), "summoned add cannot cascade")
    return {"checks": checks, "errors": errors, "error_count": len(errors)}
