# -*- coding: utf-8 -*-
"""Soulbound v0.36.8 - Crypt Threat/EXP Rebalance + Party Dungeon Exit.

Final runtime layer. It deliberately runs after Generator Core and the UOSSMUD
Superboss layer so dedicated Crypt difficulty survives every runtime template
refresh and leader emergency withdrawal can move the whole local dungeon party.
"""

V0368_CRYPT_XP_MULTIPLIERS = {
    "crypt_regular": 2.0,
    "crypt_boss": 3.0,
    "mythic_regular": 3.0,
    "mythic_boss": 5.0,
}


def _v0368_crypt_kind(template):
    if not isinstance(template, dict):
        return None
    if template.get("mythic_crypt_floor") is not None:
        return "mythic_boss" if template.get("mythic_crypt_boss") else "mythic_regular"
    if template.get("crypt_floor") is not None:
        return "crypt_boss" if template.get("crypt_boss") else "crypt_regular"
    return None


def _v0368_apply_crypt_threat(template):
    """Apply FINAL Crypt combat numbers after canonical Generator Core refresh.

    Ordinary Crypt is intentionally tougher than same-stage open terrain.
    Mythic Crypt is another clear step above it. This function is idempotent
    because the canonical refresher is always called first at runtime.
    """
    kind = _v0368_crypt_kind(template)
    if kind is None:
        return template

    try:
        stage = max(1, min(CHARACTER_MAX_LEVEL, int(template.get("generator_level", template.get("v019_stage", 1)) or 1)))
    except Exception:
        stage = 1

    if kind.startswith("crypt_"):
        # ~2.14x HP at stage 10, ~3.43x at 100, cap 4.8x from ~200+.
        hp_mult = min(4.80, 2.00 + stage / 70.0)
        # Damage rises more gently but remains above equivalent open terrain.
        dmg_mult = min(2.00, 1.30 + stage / 400.0)
        if kind == "crypt_boss":
            # Boss canonical rank already has 8.5x HP; this makes the milestone
            # a real wall instead of a slightly larger regular mob.
            hp_mult *= 2.00
            dmg_mult *= 1.25
    else:
        # Mythic floors use a higher Generator stage already; amplify that stage
        # instead of replacing it with hand-authored flat numbers.
        hp_mult = min(6.00, 3.00 + stage / 100.0)
        dmg_mult = min(2.50, 1.60 + stage / 450.0)
        if kind == "mythic_boss":
            hp_mult *= 1.70
            dmg_mult *= 1.25
            # Concrete UOSSMUD Superboss identities keep their individual feel
            # after the generic Mythic multiplier.
            if template.get("uoss_superboss") and "uoss_superboss_profile_v0366" in globals():
                try:
                    profile = uoss_superboss_profile_v0366("mythic_crypt", int(template.get("mythic_crypt_floor") or 10))
                    hp_mult *= float(profile.get("hp", 1.0) or 1.0)
                    dmg_mult *= float(profile.get("damage", 1.0) or 1.0)
                except Exception:
                    pass

    template["max_hp"] = max(1, int(round(int(template.get("max_hp", 1) or 1) * hp_mult)))
    template["base_max_hp"] = int(template["max_hp"])
    template["damage"] = max(1, int(round(int(template.get("damage", 1) or 1) * dmg_mult)))
    template["crypt_threat_rebalance_v0368"] = True
    template["crypt_threat_hp_mult_v0368"] = round(float(hp_mult), 4)
    template["crypt_threat_damage_mult_v0368"] = round(float(dmg_mult), 4)
    return template


# Every World spawn/respawn restores canonical Generator numbers first. Wrap
# that single refresh point so the dedicated dungeon layer can never be lost.
_v0190_apply_combat_template_before_v0368 = v0190_apply_combat_template

def v0190_apply_combat_template(template):
    result = _v0190_apply_combat_template_before_v0368(template)
    return _v0368_apply_crypt_threat(result)


# EXP uses Generator Core dynamically at kill time, not the legacy hand-written
# reward fields. Give harder Crypt encounters an explicit final reward premium.
_v0190_combat_reward_before_v0368 = v0190_combat_reward

def v0190_combat_reward(template, kind):
    base = int(_v0190_combat_reward_before_v0368(template, kind))
    if str(kind) == "coins":
        return base
    crypt_kind = _v0368_crypt_kind(template)
    if crypt_kind is None:
        return base
    mult = float(V0368_CRYPT_XP_MULTIPLIERS[crypt_kind])
    return min(V019_SAFE_INT, max(0, int(round(base * mult))))


# Rebuild the already-created static templates through the same final runtime
# refresh path. Lazy 201+ floors are covered automatically by the wrapper above.
for _v0368_tid, _v0368_template in list(MOB_TEMPLATES.items()):
    if _v0368_crypt_kind(_v0368_template):
        v0190_apply_combat_template(_v0368_template)


# Lazy floor builders create templates after module import. Their internal calls
# do not always refresh after the final dict mutation, so patch every spawned
# template once more before returning the floor definition.
_create_infinite_crypt_floor_definition_before_v0368 = create_infinite_crypt_floor_definition

def create_infinite_crypt_floor_definition(floor, mythic=False):
    room_id, spawns = _create_infinite_crypt_floor_definition_before_v0368(floor, mythic=mythic)
    for _room_id, template_id in list(spawns or ()): 
        template = MOB_TEMPLATES.get(template_id)
        if isinstance(template, dict) and _v0368_crypt_kind(template):
            v0190_apply_combat_template(template)
    return room_id, spawns


# ----------------------- PARTY DUNGEON EXIT -----------------------
_dungeon_exit_before_v0368 = Session.dungeon_exit

async def _party_dungeon_exit_v0368(self):
    """Leader emergency exit moves only party members in the same room.

    The emergency withdrawal is allowed during combat. Only online party
    members whose room_id exactly matches the leader's current room are moved.
    Members on another floor/room of the same dungeon remain where they are.
    Combat tasks and mob aggro for moved members are cleared before teleport.
    """
    result = self.dungeon_exit_destination()
    key = self.party_key() if self.account_id is not None else None

    # Solo players and non-leaders preserve the original one-character path.
    # The special combat-capable group withdrawal belongs to the party leader.
    if key is None or key != self.account_id or not result:
        return await _dungeon_exit_before_v0368(self)

    target, dungeon_name = result
    leader_room = str(self.character.room_id)
    candidates = []
    for member in self.server.party_sessions(self.account_id, same_room=leader_room):
        if not member or member.closed or not member.character:
            continue
        member_result = member.dungeon_exit_destination()
        if not member_result:
            continue
        member_target, member_dungeon = member_result
        if str(member_target) == str(target) and str(member_dungeon) == str(dungeon_name):
            candidates.append(member)

    if self not in candidates:
        candidates.append(self)

    # Combat withdrawal is explicitly allowed. First stop every realtime loop
    # and clear target keys for the whole moved set, then release engagements.
    # Clearing all keys first prevents aggro from being reassigned to another
    # party member who is about to leave the same room.
    for member in candidates:
        await member.stop_realtime_combat()
        member.combat_mob_key = None
        member.combat_hp_warn_level = 0

    for member in candidates:
        member.server.release_all_engagements_for_session(member)
        member.skill_guard = 0
        member.skill_evade = False
        member.skill_evade_lockout_until = 0.0

    # If the active party protector is among the withdrawn players, disable
    # the protector assignment so it cannot remain attached to a remote room.
    protector = self.server.party_protector_session(self.account_id)
    if protector in candidates:
        self.server.party_protectors.pop(key, None)

    moved = []
    for member in candidates:
        old_room = str(member.character.room_id)
        if old_room == str(target):
            continue
        member.previous_room_id = old_room
        await member.server.broadcast_room(
            old_room,
            f"{member.character.name} wycofuje się z lochu razem z liderem drużyny.",
            exclude=member,
        )
        member.character.room_id = target
        member.server.db.save_character(member.character)
        await member.server.broadcast_room(
            target,
            f"{member.character.name} wraca z lochu wraz z drużyną.",
            exclude=member,
        )
        moved.append(member)

    for member in moved:
        await member.send(
            f"WYJŚCIE DRUŻYNOWE: lider {self.character.name} wycofuje osoby stojące z nim w tej samej lokacji z {dungeon_name}. "
            f"Wracasz do: {ROOMS[target]['name']}."
        )
        await member.look()

    await self.send(
        f"Drużynowe wycofanie zakończone. Z tej lokacji {dungeon_name} wycofano {len(moved)} członków drużyny."
    )
    return True

_party_dungeon_exit_v0368._party_dungeon_exit_v0368 = True
Session.dungeon_exit = _party_dungeon_exit_v0368


# ----------------------------- HELP -----------------------------
HELP_TOPICS.setdefault("krypta", []).extend([
    "v0.36.8: zwykła Krypta jest celowo trudniejsza od zwykłego terenu o podobnym etapie; wraz z piętrem rosną HP i obrażenia zwykłych mobów oraz bossów.",
    "Zwykłe moby Krypty dają x2 bazowego EXP Generator Core, bossowie x3. Mityczna Krypta daje x3 za zwykłe moby i x5 za bossów/Superbossów, przed dynamicznym EXP i Dungeon Party Bonus.",
    "Jeżeli lider drużyny użyje wyjścia awaryjnego z lochu, wycofywani są tylko członkowie stojący z liderem w dokładnie tej samej lokacji. Wycofanie działa także podczas walki i czyści walkę/aggro wycofywanych osób.",
])
HELP_TOPICS.setdefault("drużyna", []).append(
    "v0.36.8: wyjście awaryjne lidera wycofuje tylko członków drużyny stojących z nim w tej samej lokacji; działa także podczas walki."
)
HELP_TOPICS.setdefault("dusza", []).append(
    "v0.36.8: gdy gracz odblokuje nowy Tier Duszy, wszyscy inni gracze stojący w tej samej lokacji dostają krótki lokalny komunikat. Nie trzeba być w drużynie."
)
HELP_TOPICS.setdefault("soul", []).append(
    "v0.36.8: Soul Tier unlocks are announced to every other player in the same room; party membership is not required."
)


def crypt_party_rebalance_audit_v0368():
    errors = []
    # Static checkpoints must visibly exceed canonical same-stage terrain values.
    for floor in (10, 50, 100, 200):
        reg = MOB_TEMPLATES.get(f"crypt_floor_mob_{floor}")
        boss = MOB_TEMPLATES.get(f"crypt_boss_{floor}")
        if not reg or not boss:
            errors.append(f"missing ordinary crypt checkpoint {floor}")
            continue
        canonical_hp = generator_core_v027.mob_hp(min(CHARACTER_MAX_LEVEL, floor), "normal")
        if int(reg.get("max_hp", 0) or 0) <= canonical_hp * 2:
            errors.append(f"crypt regular floor {floor} still too weak: {reg.get('max_hp')} <= {canonical_hp*2}")
        if int(boss.get("max_hp", 0) or 0) <= int(reg.get("max_hp", 0) or 0) * 8:
            errors.append(f"crypt boss floor {floor} insufficient HP wall")
        if v0190_combat_reward(reg, "class") <= _v0190_combat_reward_before_v0368(reg, "class"):
            errors.append(f"crypt regular floor {floor} missing EXP premium")
        if v0190_combat_reward(boss, "class") <= v0190_combat_reward(reg, "class"):
            errors.append(f"crypt boss floor {floor} XP not above regular")

    for floor in (10, 100, 200):
        myth = MOB_TEMPLATES.get(f"mythic_crypt_mob_{floor}")
        ordinary = MOB_TEMPLATES.get(f"crypt_floor_mob_{floor}")
        mboss = MOB_TEMPLATES.get(f"mythic_crypt_boss_{floor}")
        if not myth or not ordinary or not mboss:
            errors.append(f"missing mythic crypt checkpoint {floor}")
            continue
        if int(myth.get("max_hp", 0) or 0) <= int(ordinary.get("max_hp", 0) or 0):
            errors.append(f"mythic regular floor {floor} not stronger than ordinary")
        if v0190_combat_reward(mboss, "class") <= v0190_combat_reward(myth, "class"):
            errors.append(f"mythic boss floor {floor} XP not above mythic regular")

    if not getattr(Session.dungeon_exit, "_party_dungeon_exit_v0368", False):
        errors.append("party leader dungeon exit wrapper missing")

    # Soul Tier unlock must remain a local-room broadcast for all players,
    # independent of party membership. Static source guard catches accidental
    # removal or replacement with a party-only notifier.
    try:
        import inspect as _inspect_v0368
        _unlock_src_v0368 = _inspect_v0368.getsource(Session.unlock)
        if "broadcast_room" not in _unlock_src_v0368 or "Tier Duszy" not in _unlock_src_v0368:
            errors.append("Soul Tier local-room announcement missing from Session.unlock")
        if "party_sessions" in _unlock_src_v0368:
            errors.append("Soul Tier announcement must not be limited to party members")
    except Exception as _exc_v0368:
        errors.append(f"Soul Tier announcement audit failed: {_exc_v0368}")

    return {
        "version": "0.36.8",
        "error_count": len(errors),
        "errors": errors,
        "xp_multipliers": dict(V0368_CRYPT_XP_MULTIPLIERS),
    }


CRYPT_PARTY_REBALANCE_AUDIT_V0368 = crypt_party_rebalance_audit_v0368()
if CRYPT_PARTY_REBALANCE_AUDIT_V0368["error_count"]:
    raise RuntimeError(
        "Crypt/Party Rebalance Audit v0.36.8 failed: "
        + "; ".join(CRYPT_PARTY_REBALANCE_AUDIT_V0368["errors"][:50])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.36.8: wzmocniono zwykłą i Mityczną Kryptę, zwiększono EXP lochowy oraz dodano drużynowe wycofanie z lochu przez lidera."
)
LATEST_CHANGES_TITLE = "Soulbound v0.36.8 - Crypt Threat/EXP + Same-Room Exit + Local Soul Tier"
LATEST_CHANGES = [
    "Zwykła Krypta jest teraz wyraźnie trudniejsza od zwykłego świata o podobnym etapie; wzmocniono zarówno zwykłe moby, jak i bossów.",
    "Mityczna Krypta dostała dodatkowy skok HP/obrażeń, a UOSSMUD Superbossy zachowują indywidualne profile po każdym runtime refreshu.",
    "EXP: zwykła Krypta x2 regular / x3 boss; Mityczna Krypta x3 regular / x5 boss, przed dynamicznym EXP i Dungeon Party Bonus.",
    "Wyjście awaryjne użyte przez lidera wycofuje tylko członków stojących z nim w tej samej lokacji. Działa także podczas walki; osoby w innych pokojach lub na innych piętrach pozostają na miejscu.",
    "Odblokowanie Tieru Duszy jest ogłaszane wszystkim innym graczom w tej samej lokacji, niezależnie od drużyny; osoby w innych pokojach nie dostają komunikatu.",
]
