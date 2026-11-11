"""v1.17.3: deterministic, non-invasive class/party/superboss combat projections.

This audit is not a claim of complete live-game DPS balance. The runtime lane
executes the *actual* adaptive-scaling mixin with synthetic damage profiles and
real, fully materialized class equipment. No player account is created or edited.
"""
from __future__ import annotations

import math
from types import SimpleNamespace

from core.classes_skills import CLASSES, CLASS_SKILLS
from core.player_math import (
    basic_attack_hits_from_dexterity,
    character_offensive_build_multiplier,
)
from systems.adaptive_combat import (
    adaptive_combat_rank_v11330,
    adaptive_target_incoming_fraction_v11330,
    adaptive_target_max_hp_v11330,
)

STAGES = (100, 200, 400, 600)
OFFENSIVE = frozenset(("damage", "aoe_damage", "execute", "drain"))


def audit_combat_balance_fast_v1173():
    errors, checks, summaries = [], 0, {}
    for name, kind, *_ in CLASSES:
        catalog = CLASS_SKILLS.get(name, ())
        summary = {}
        for stage in STAGES:
            available = [s for s in catalog if int(s.get("unlock", 1) or 1) <= stage]
            attacks = [s for s in available if s.get("kind") in OFFENSIVE]
            checks += 2
            if not attacks:
                errors.append(f"{name}/{stage}: no unlocked damaging abilities")
                continue
            options = [s for s in attacks if s.get("kind") != "aoe_damage"]
            best = max(options or attacks, key=lambda s: float(s.get("mult", 1) or 1))
            summary[stage] = {
                "unlocked": len(available),
                "offensive": len(attacks),
                "best_single": str(best.get("name") or best.get("id")),
                "best_multiplier": float(best.get("mult", 1) or 1),
                "heals": sum(s.get("kind") in ("heal", "group_heal") for s in available),
                "aoe": sum(s.get("kind") == "aoe_damage" for s in available),
                "class_type": kind,
            }
            if not (0 < summary[stage]["best_multiplier"] < 100):
                errors.append(f"{name}/{stage}: out-of-range top ability multiplier")
        for earlier, later in zip(STAGES, STAGES[1:]):
            checks += 1
            if earlier in summary and later in summary:
                if summary[later]["offensive"] < summary[earlier]["offensive"]:
                    errors.append(f"{name}: damaging skills disappear after {earlier}")
        summaries[name] = summary
    for stage in STAGES:
        dex = stage * 2
        normal = basic_attack_hits_from_dexterity(dex)
        haste = basic_attack_hits_from_dexterity(dex, haste=True)
        checks += 2
        if haste < normal or haste > 2 * normal + 1:
            errors.append(f"stage {stage}: Haste hit sequence unexpected")
        if not math.isfinite(character_offensive_build_multiplier(dex)):
            errors.append(f"stage {stage}: nonfinite stat build multiplier")
    for rank in ("normal", "elite", "boss", "world_boss"):
        previous_hp = 0
        for size in (1, 2, 4):
            checks += 2
            hp = adaptive_target_max_hp_v11330(1000, 1600 * size, {"rank": rank})
            if hp < previous_hp:
                errors.append(f"{rank}: adding players reduced scaled HP")
            previous_hp = hp
            pressure = adaptive_target_incoming_fraction_v11330({"rank": rank}, size)
            if not (0 < pressure <= .22):
                errors.append(f"{rank}/{size}: invalid incoming pressure")
    return {"version": "1.17.3", "checks": checks, "classes": len(summaries),
            "per_class": summaries, "errors": errors, "error_count": len(errors)}


def audit_combat_balance_runtime_v1173(items, catalog):
    """Exercise actual SessionCombatDamageMixin via disposable representative combatants."""
    from data.mobs import MOB_TEMPLATES
    from player.session_mixins.combat_damage import SessionCombatDamageMixin
    errors, checks, result = [], 0, {}

    class Combatant(SessionCombatDamageMixin):
        def __init__(self, class_name, room, hit, hits):
            self.account_id = 1
            self.character = SimpleNamespace(class_name=class_name, room_id=room)
            self.closed = False
            self.current_hp = 100000
            self.current_mana = 100000
            self._hit, self._hits = float(hit), int(hits)
            self.combat_player_interval = 1.0
            self.server = SimpleNamespace(party_sessions=lambda _account, same_room=None: [])

        def consider_player_expected_hit(self):
            return self._hit

        def basic_attack_hit_count_v11196(self):
            return self._hits

        def player_action_interval_v11154(self):
            return self.combat_player_interval

        def max_hp(self):
            return 100000

        def consider_enemy_expected_hit(self, template):
            # A monotone post-defense estimate, independent of any subclass.
            return max(1.0, float(template.get("damage", 1)) * .6)

    # Each test uses its own fake template to ensure the actual production
    # method reads the expected rank and unmodified base HP.
    for class_name, class_type, *_ in CLASSES:
        report = {}
        for stage in STAGES:
            ids = catalog.get(class_name, {}).get(stage, ())
            hand = next((items[i] for i in ids if i in items and items[i].get("slot") == "hands"), None)
            checks += 1
            if hand is None:
                errors.append(f"{class_name}/{stage}: missing finalized hand equipment")
                continue
            bonuses = dict(hand.get("stats") or {})
            affix = str(hand.get("affix") or "")
            if affix in ("strength", "dexterity", "constitution", "intelligence", "willpower"):
                bonuses[affix] = int(bonuses.get(affix, 0) or 0) + int(hand.get("affix_amount", 0) or 0)
            primary = "intelligence" if class_type == "magic" else (
                "dexterity" if class_name in ("Łotrzyk", "Łowca", "Mnich", "Inżynier") else "strength"
            )
            # Equal trained base; use real generated class-EQ delta for identity.
            effective = stage * 2 + int(bonuses.get(primary, 0) or 0)
            expected_hit = (effective + stage * 3) * character_offensive_build_multiplier(effective)
            hits = basic_attack_hits_from_dexterity(stage + 100)
            checks += 2
            if expected_hit <= 0 or not math.isfinite(expected_hit):
                errors.append(f"{class_name}/{stage}: invalid projected attack power")
                continue
            solo = Combatant(class_name, "audit_room", expected_hit, hits)
            projected = {}
            for party_size in (1, 2, 4):
                members = [solo] + [Combatant(class_name, "audit_room", expected_hit, hits) for _ in range(party_size-1)]
                solo.server.party_sessions = lambda _account, same_room=None, m=members: m
                for rank in ("normal", "boss", "world_boss"):
                    mob_id = f"audit_balance_v1173_{class_name}_{stage}_{party_size}_{rank}"
                    template = {"rank": rank, "max_hp": 1000, "damage": 100}
                    MOB_TEMPLATES[mob_id] = template
                    try:
                        mob = SimpleNamespace(template_id=mob_id, room_id="audit_room", alive=True, hp=1000)
                        scaled = solo.apply_adaptive_mob_scale_v11330(mob)
                        checks += 3
                        total = solo.adaptive_member_dps_v11330(solo) * party_size
                        if not scaled or scaled["max_hp"] != mob.hp:
                            errors.append(f"{class_name}/{stage}/{party_size}/{rank}: scaled current HP inconsistent")
                        if scaled and scaled["party_size"] != party_size:
                            errors.append(f"{class_name}/{stage}/{party_size}/{rank}: party count drift")
                        if scaled and scaled["max_hp"] < int(total * 7):
                            errors.append(f"{class_name}/{stage}/{party_size}/{rank}: fight remains one-hit")
                        if scaled and rank == "world_boss":
                            projected[party_size] = round(scaled["max_hp"] / total, 2)
                    finally:
                        MOB_TEMPLATES.pop(mob_id, None)
            report[stage] = {"projected_hit": round(expected_hit), "hits": hits,
                             "world_boss_target_seconds": projected}
        result[class_name] = report
    return {"version": "1.17.3", "checks": checks, "classes": len(result),
            "per_class": result, "errors": errors, "error_count": len(errors)}


def audit_party_support_runtime_v1173():
    """Exercise a real mercenary turn, cooldown and v1.22 EXP persistence calls."""
    import asyncio
    import time
    from data.mobs import MOB_TEMPLATES
    from player.session_mixins.mercenary_taverns import SessionMercenaryTavernsMixin

    errors, checks, messages = [], 0, []

    class ProgressStore:
        """Small in-memory replacement for the two DB calls made by a mercenary turn.

        Keep this historical combat test independent of the live player database,
        while exercising the same read -> grant EXP -> read progression contract.
        """
        def __init__(self, contracts):
            self.contracts = contracts
            self.rows = {}

        def mercenary_contracts(self, _account, _now=None):
            return self.contracts

        def mercenary_progress_v1220(self, account, role):
            return dict(self.rows.get((account, role),
                                      {"xp": 0, "specialization": "", "actions": 0}))

        def mercenary_gain_xp_v1220(self, account, role, xp):
            key = (account, role)
            row = self.mercenary_progress_v1220(account, role)
            row["xp"] += max(1, int(xp))
            row["actions"] += 1
            self.rows[key] = row
            return dict(row)

    class TestSession(SessionMercenaryTavernsMixin):
        def __init__(self):
            self.account_id = 1
            self.character = SimpleNamespace(name="Test", room_id="audit_merc_room")
            self.current_hp = 50000
            self.skill_guard = 1  # A guard is already active: test offensive turn.
            self._mercenary_next_action_v1170 = 0.0
            self._mercenary_last_role_v1170 = None
            self.owner_messages = []
            contracts = [
                {"role": role, "expires_at": time.time() + 60}
                for role in ("mec", "mag", "druid")
            ]
            self.server = SimpleNamespace(
                db=ProgressStore(contracts),
                party_sessions=lambda _account, same_room=None: [self],
                party_combat_broadcast=self._broadcast,
            )

        async def send_combat(self, message, detail="essential"):
            self.owner_messages.append((message, detail))

        async def _broadcast(self, _session, message, detail="normal"):
            messages.append(message)

        def max_hp(self):
            return 50000

        def physical_power(self):
            return 10000

        def spell_power(self):
            return 12000

        async def apply_boss_defense(self, _mob, damage):
            return damage

        def mob_effective_max_hp_v11330(self, _mob):
            return 100000

    async def run():
        session = TestSession()
        mob = SimpleNamespace(
            template_id="combat_balance_synthetic_mercenary_v1173",
            room_id="audit_merc_room", alive=True, hp=100000,
        )
        # Synthetic template is temporary: never contaminate the real catalog.
        MOB_TEMPLATES[mob.template_id] = {
            "max_hp": 100000, "damage": 200, "rank": "world_boss"
        }
        try:
            before = mob.hp
            await session.mercenary_combat_turn_v1170(mob)
            first_hp = mob.hp
            first_msgs = len(messages)
            await session.mercenary_combat_turn_v1170(mob)
            progress = session.server.db.mercenary_progress_v1220(1, "mec")
            if len(session.owner_messages) != 3 or any(msg[1] != "essential" for msg in session.owner_messages):
                raise AssertionError("mercenary owner did not receive all three essential combat messages")
            return before, first_hp, first_msgs, mob.hp, len(messages), progress
        finally:
            MOB_TEMPLATES.pop(mob.template_id, None)

    try:
        before, first_hp, first_msgs, after, msg_count, progress = asyncio.run(run())
    except Exception as exc:
        errors.append(f"mercenary combat action failed: {type(exc).__name__}: {exc}")
        return {"checks": 1, "errors": errors, "error_count": len(errors)}
    checks += 1
    if not 3500 < before - first_hp <= before:
        errors.append("mercenary missing uncapped full owner power against boss")
    checks += 1
    if first_msgs != 3 or msg_count != 3 or after != first_hp:
        errors.append("each contract must act once, then respect its own cooldown")
    checks += 1
    if not messages or "Vex" not in messages[0]:
        errors.append("mercenary round-robin first action not activated")
    checks += 1
    if progress["actions"] != 0 or progress["xp"] != 0:
        errors.append("mercenary v1.22.8: combat must not grant separate mercenary EXP")
    return {"version": "1.17.3", "checks": checks,
            "errors": errors, "error_count": len(errors)}
