# -*- coding: utf-8 -*-
"""Soulbound v0.38.0 - Party Combo, Party Ultimate, Crypt Summary, revive follow."""

PARTY_COMBO_WINDOW_V0380 = 8.0
PARTY_ULTIMATE_MAX_V0380 = 100

# Ordered execution is not required: the pair of classes is enough, but the
# second skill must be used by a different local party member on the same mob.
PARTY_COMBO_RULES_V0380 = {
    frozenset(("Mag", "Wojownik")): {
        "name": "Eksplozja Żywiołu", "bonus": 0.40, "effect": "burst",
    },
    frozenset(("Kapłan", "Nekromanta")): {
        "name": "Zaćmienie Duszy", "bonus": 0.32, "effect": "heal",
    },
    frozenset(("Łotrzyk", "Mec")): {
        "name": "Precyzyjny Przełom", "bonus": 0.38, "effect": "precision",
    },
    frozenset(("Mec", "Inżynier")): {
        "name": "Magitekowy Overdrive", "bonus": 0.34, "effect": "mana",
    },
    frozenset(("Nekromanta", "Mag")): {
        "name": "Płomień Grobu", "bonus": 0.35, "effect": "burst",
    },
    frozenset(("Druid", "Łowca")): {
        "name": "Dziki Łańcuch", "bonus": 0.30, "effect": "precision",
    },
    frozenset(("Psionik", "Czarownik")): {
        "name": "Rezonans Umysłu", "bonus": 0.33, "effect": "mana",
    },
    frozenset(("Berserker", "Mnich")): {
        "name": "Łamiący Rytm", "bonus": 0.36, "effect": "burst",
    },
    frozenset(("Strażnik", "Kapłan")): {
        "name": "Święty Bastion", "bonus": 0.26, "effect": "guard",
    },
    frozenset(("Łotrzyk", "Łowca")): {
        "name": "Krzyżowy Ostrzał", "bonus": 0.30, "effect": "precision",
    },
}


def _v0380_party_key(session):
    if not session or not getattr(session, "server", None) or session.account_id is None:
        return None
    return session.server.party_key_for_account(session.account_id)


def _v0380_local_party(session, living_only=True):
    if not session or not session.character:
        return []
    members = session.server.party_sessions(session.account_id, same_room=session.character.room_id)
    if living_only:
        members = [s for s in members if s.character and not s.closed and s.current_hp > 0]
    return members


def _v0380_ultimate_store(server):
    store = getattr(server, "party_ultimate_v0380", None)
    if not isinstance(store, dict):
        store = {}
        server.party_ultimate_v0380 = store
    return store


def _v0380_ultimate_state(session, create=True):
    key = _v0380_party_key(session)
    if key is None:
        return None
    store = _v0380_ultimate_store(session.server)
    if create:
        store.setdefault(key, {"value": 0, "threshold": 0})
    return store.get(key)


async def _v0380_add_ultimate(session, amount, reason="walka"):
    key = _v0380_party_key(session)
    if key is None:
        return 0
    local = _v0380_local_party(session, living_only=True)
    if len(local) < 2:
        return int((_v0380_ultimate_state(session, create=True) or {}).get("value", 0))
    state = _v0380_ultimate_state(session, create=True)
    old = int(state.get("value", 0) or 0)
    new = min(PARTY_ULTIMATE_MAX_V0380, old + max(0, int(amount or 0)))
    state["value"] = new
    old_step = old // 25
    new_step = new // 25
    if new >= 100 and old < 100:
        state["threshold"] = 100
        for member in local:
            await member.send(
                "ULTIMATE DRUŻYNY GOTOWY: 100/100. Lider może użyć: drużyna ultimate.",
                history_category="combat",
            )
    elif new_step > old_step and new in range(1, 100):
        threshold = min(75, new_step * 25)
        if threshold > int(state.get("threshold", 0) or 0):
            state["threshold"] = threshold
            for member in local:
                await member.send(
                    f"Ultimate drużyny: {new}/100 ({reason}).",
                    history_category="combat",
                )
    return new


def _v0380_shared_target(session):
    if not session or not session.character:
        return None
    room_id = session.character.room_id
    keys = []
    if getattr(session, "combat_mob_key", None):
        keys.append(session.combat_mob_key)
    for member in _v0380_local_party(session, living_only=True):
        if getattr(member, "combat_mob_key", None):
            keys.append(member.combat_mob_key)
    for key in keys:
        mob = session.server.world.mobs.get(key)
        if mob and mob.alive and mob.room_id == room_id:
            return mob
    return None


def _v0380_party_classes(session):
    names = []
    for member in _v0380_local_party(session, living_only=True):
        try:
            names.extend(member.active_class_names())
        except Exception:
            if member.character:
                names.append(member.character.class_name)
    return names


async def party_ultimate_v0380(self):
    key = _v0380_party_key(self)
    if key is None:
        await self.send("Nie należysz do drużyny.")
        return False
    if key != self.account_id:
        await self.send("Tylko lider może uruchomić Ultimate drużyny.")
        return False
    local = _v0380_local_party(self, living_only=True)
    if len(local) < 2:
        await self.send("Ultimate wymaga co najmniej 2 żywych członków drużyny w tej samej lokacji.")
        return False
    state = _v0380_ultimate_state(self, create=True)
    value = int(state.get("value", 0) or 0)
    if value < 100:
        await self.send(f"Ultimate drużyny: {value}/100. Walczcie razem, aby go naładować.")
        return False
    mob = _v0380_shared_target(self)
    if not mob:
        await self.send("Ultimate jest gotowy, ale drużyna nie ma wspólnego żywego celu w tej lokacji.")
        return False

    classes = _v0380_party_classes(self)
    class_set = set(classes)
    physical = sum(1 for name in classes if class_type_for_name(name) == "physical")
    magic = sum(1 for name in classes if class_type_for_name(name) == "magic")
    template = MOB_TEMPLATES[mob.template_id]

    if {"Mec", "Inżynier"}.issubset(class_set):
        name, pct, heal_pct, mana_pct, guard_pct = "Magitekowy Przeciąż", 0.12, 0.00, 0.18, 0.00
    elif {"Kapłan", "Nekromanta"}.issubset(class_set):
        name, pct, heal_pct, mana_pct, guard_pct = "Przymierze Życia i Śmierci", 0.09, 0.25, 0.15, 0.00
    elif physical >= magic + 2:
        name, pct, heal_pct, mana_pct, guard_pct = "Szarża Przysięgi", 0.11, 0.08, 0.00, 0.12
    elif magic >= physical + 2:
        name, pct, heal_pct, mana_pct, guard_pct = "Konwergencja Arkanów", 0.10, 0.00, 0.25, 0.00
    else:
        name, pct, heal_pct, mana_pct, guard_pct = "Konwergencja Soulbound", 0.09, 0.15, 0.15, 0.06

    # Reset first so a kill starts charging the next ultimate instead of leaving 100/100.
    state["value"] = 0
    state["threshold"] = 0
    damage = max(1, int(round(int(template.get("max_hp", max(1, mob.hp))) * pct)))
    mob.hp -= damage

    for member in local:
        if heal_pct > 0:
            member.current_hp = min(member.max_hp(), member.current_hp + max(1, int(member.max_hp() * heal_pct)))
        if mana_pct > 0:
            member.current_mana = min(member.max_mana(), member.current_mana + max(1, int(member.max_mana() * mana_pct)))
        if guard_pct > 0:
            member.skill_guard = max(int(getattr(member, "skill_guard", 0) or 0), max(1, int(member.max_hp() * guard_pct)))
        await member.send(
            f"ULTIMATE DRUŻYNY: {name}. {template['name']} otrzymuje {damage} obrażeń. "
            f"Pasek Ultimate wraca do 0/100.",
            history_category="combat",
        )

    if mob.hp <= 0 and mob.alive:
        await self.mob_defeated(mob)
    return True


# --- Party Combo -----------------------------------------------------------
_use_class_skill_before_v0380 = Session.use_class_skill

async def _use_class_skill_v0380(self, raw):
    skill = None
    target_text = ""
    mob = None
    before_hp = None
    try:
        skill, target_text = self.find_skill_from_input(raw)
        if skill and skill.get("kind") in ("damage", "drain", "execute", "aoe_damage"):
            if getattr(self, "combat_mob_key", None):
                candidate = self.server.world.mobs.get(self.combat_mob_key)
                if candidate and candidate.alive and candidate.room_id == self.character.room_id:
                    mob = candidate
            if mob is None and str(target_text or "").strip():
                mob = self.server.world.find_mob(self.character.room_id, target_text)
            if mob and mob.alive:
                before_hp = int(mob.hp)
    except Exception:
        skill = None
        mob = None
        before_hp = None

    _serial_before = int(getattr(self, "_v0380_skill_action_serial", 0) or 0)
    result = await _use_class_skill_before_v0380(self, raw)
    if skill and skill.get("kind") in ("damage", "drain", "execute", "aoe_damage"):
        self._v0380_skill_action_serial = _serial_before + 1

    if not skill or not mob or before_hp is None:
        return result
    damage = max(0, before_hp - int(getattr(mob, "hp", before_hp)))
    if damage <= 0:
        return result

    max_hp = max(1, int(MOB_TEMPLATES[mob.template_id].get("max_hp", before_hp)))
    await _v0380_add_ultimate(self, max(2, min(8, 2 + int((damage / max_hp) * 45))), reason="skill")

    if not mob.alive or mob.hp <= 0:
        return result
    party_key = _v0380_party_key(self)
    class_name = self.skill_class_name(skill)
    now = time.time()
    previous = getattr(mob, "party_combo_marker_v0380", None)
    combo = None
    if isinstance(previous, dict):
        age = now - float(previous.get("at", 0.0) or 0.0)
        pair = frozenset((str(previous.get("class_name", "")), str(class_name)))
        if (
            0 <= age <= PARTY_COMBO_WINDOW_V0380
            and party_key is not None
            and int(previous.get("account_id", -1)) != int(self.account_id)
            and previous.get("party_key") == party_key
        ):
            combo = PARTY_COMBO_RULES_V0380.get(pair)

    if combo:
        extra = max(1, int(round(damage * float(combo["bonus"]))))
        mob.hp -= extra
        local = _v0380_local_party(self, living_only=True)
        effect = combo.get("effect")
        if effect == "heal":
            for member in local:
                member.current_hp = min(member.max_hp(), member.current_hp + max(1, int(member.max_hp() * 0.05)))
        elif effect == "mana":
            for member in local:
                member.current_mana = min(member.max_mana(), member.current_mana + max(1, int(member.max_mana() * 0.07)))
        elif effect == "guard":
            for member in local:
                member.skill_guard = max(int(getattr(member, "skill_guard", 0) or 0), max(1, int(member.max_hp() * 0.04)))
        for member in local:
            await member.send(
                f"PARTY COMBO: {combo['name']}! {previous.get('class_name')} + {class_name}. "
                f"Dodatkowe obrażenia: {extra}. Cel: {MOB_TEMPLATES[mob.template_id]['name']}.",
                history_category="combat",
            )
        await _v0380_add_ultimate(self, 12, reason="combo")
        # consume marker; the current skill becomes the beginning of a new chain below
        previous = None
        if mob.hp <= 0 and mob.alive:
            await self.mob_defeated(mob)

    if mob.alive and mob.hp > 0 and party_key is not None and len(_v0380_local_party(self, living_only=True)) >= 2:
        mob.party_combo_marker_v0380 = {
            "account_id": int(self.account_id),
            "class_name": str(class_name),
            "skill_id": str(skill.get("id", "")),
            "skill_name": str(skill.get("name", "")),
            "party_key": party_key,
            "at": now,
        }
    return result

_use_class_skill_v0380._party_combo_v0380 = True
Session.use_class_skill = _use_class_skill_v0380


# Normal Soul Weapon attacks also charge the shared ultimate.
_realtime_player_action_before_v0380 = Session.realtime_player_action

async def _realtime_player_action_v0380(self, mob):
    before = int(mob.hp) if mob and mob.alive else None
    serial_before = int(getattr(self, "_v0380_skill_action_serial", 0) or 0)
    result = await _realtime_player_action_before_v0380(self, mob)
    skill_used = int(getattr(self, "_v0380_skill_action_serial", 0) or 0) != serial_before
    if before is not None and mob and not skill_used:
        damage = max(0, before - int(getattr(mob, "hp", before)))
        if damage > 0:
            max_hp = max(1, int(MOB_TEMPLATES[mob.template_id].get("max_hp", before)))
            await _v0380_add_ultimate(self, max(1, min(5, 1 + int((damage / max_hp) * 30))), reason="atak")
    return result

_realtime_player_action_v0380._party_ultimate_v0380 = True
Session.realtime_player_action = _realtime_player_action_v0380


# --- Crypt run summary -----------------------------------------------------
def _v0380_crypt_identity(room_id):
    floor = crypt_floor_number(str(room_id or ""))
    if floor is not None:
        return "Krypta", int(floor)
    floor = mythic_crypt_floor_number(str(room_id or ""))
    if floor is not None:
        return "Mityczna Krypta", int(floor)
    return None, None


def _v0380_run(session, room_id=None, create=False):
    room_id = room_id or (session.character.room_id if session.character else "")
    kind, floor = _v0380_crypt_identity(room_id)
    current = getattr(session, "crypt_run_summary_v0380", None)
    if kind is None:
        return None
    if not isinstance(current, dict) or current.get("kind") != kind:
        if not create:
            return None
        current = {
            "kind": kind,
            "started": time.time(),
            "kills": 0,
            "bosses": 0,
            "class_xp": 0,
            "soul_xp": 0,
            "character_xp": 0,
            "currency": 0,
            "best_drop_id": None,
            "best_drop_value": -1,
            "max_floor": int(floor or 1),
        }
        session.crypt_run_summary_v0380 = current
    current["max_floor"] = max(int(current.get("max_floor", 0) or 0), int(floor or 0))
    return current


async def _v0380_finish_run(session, reason="wyjście"):
    run = getattr(session, "crypt_run_summary_v0380", None)
    if not isinstance(run, dict):
        return False
    session.crypt_run_summary_v0380 = None
    seconds = max(0, int(time.time() - float(run.get("started", time.time()))))
    minutes, sec = divmod(seconds, 60)
    total_xp = int(run.get("class_xp", 0)) + int(run.get("soul_xp", 0)) + int(run.get("character_xp", 0))
    best_id = run.get("best_drop_id")
    best_name = player_item_display_name_v0335(best_id) if best_id and best_id in ITEMS else "brak"
    currency = max(0, int(run.get("currency", 0)))
    await session.send(
        f"DUNGEON SUMMARY — {run.get('kind')}. Czas {minutes} min {sec} s. "
        f"Zabite moby {int(run.get('kills',0))}; bossowie {int(run.get('bosses',0))}; "
        f"najgłębsze piętro {int(run.get('max_floor',0))}. "
        f"EXP łącznie {total_xp}: Class {int(run.get('class_xp',0))}, Soul {int(run.get('soul_xp',0))}, "
        f"postać {int(run.get('character_xp',0))}. Waluta {currency_reading_text(currency,0,0)}. "
        f"Najcenniejszy drop: {best_name}. Powód zakończenia: {reason}."
    )
    return True


# XP wrappers count all XP granted while a crypt run is active.
_grant_class_xp_before_v0380 = Session.grant_class_xp
async def _grant_class_xp_v0380(self, total_xp):
    run = _v0380_run(self, create=False)
    if run is not None:
        run["class_xp"] += max(0, int(total_xp or 0))
    return await _grant_class_xp_before_v0380(self, total_xp)
Session.grant_class_xp = _grant_class_xp_v0380

_grant_soul_xp_before_v0380 = Session.grant_soul_xp
async def _grant_soul_xp_v0380(self, amount):
    run = _v0380_run(self, create=False)
    if run is not None:
        run["soul_xp"] += max(0, int(amount or 0))
    return await _grant_soul_xp_before_v0380(self, amount)
Session.grant_soul_xp = _grant_soul_xp_v0380

_add_character_xp_before_v0380 = Session.add_character_xp_with_event
def _add_character_xp_v0380(self, amount):
    run = _v0380_run(self, create=False)
    if run is not None:
        run["character_xp"] += max(0, int(amount or 0))
    return _add_character_xp_before_v0380(self, amount)
Session.add_character_xp_with_event = _add_character_xp_v0380

_record_item_collection_before_v0380 = Session.record_item_collection
async def _record_item_collection_v0380(self, item_id, *args, **kwargs):
    result = await _record_item_collection_before_v0380(self, item_id, *args, **kwargs)
    run = _v0380_run(self, create=False)
    item = ITEMS.get(item_id)
    if run is not None and item:
        value = 0
        try:
            parts = self.generic_item_sale_value(item_id, item)
            value = legacy_currency_to_coins(parts.get("silver",0), parts.get("gold",0), parts.get("mithril",0))
        except Exception:
            price = max(0, int(item.get("price", 0) or 0))
            currency = str(item.get("currency", "silver"))
            if currency == "gold": value = price * SILVER_PER_GOLD
            elif currency == "mithril": value = price * SILVER_PER_MITHRIL
            else: value = price
        if value > int(run.get("best_drop_value", -1) or -1):
            run["best_drop_value"] = int(value)
            run["best_drop_id"] = item_id
    return result
Session.record_item_collection = _record_item_collection_v0380


_mob_defeated_before_v0380 = Session.mob_defeated
async def _mob_defeated_v0380(self, mob):
    template = MOB_TEMPLATES[mob.template_id]
    recipients = self.server.party_sessions(self.account_id, same_room=self.character.room_id) or [self]
    snapshots = {}
    for member in recipients:
        run = _v0380_run(member, room_id=mob.room_id, create=True)
        if run is not None:
            snapshots[member] = legacy_currency_to_coins(member.character.silver, member.character.gold, member.character.mithril)
    result = await _mob_defeated_before_v0380(self, mob)
    is_boss = bool(v0866_is_boss_template(template)) if "v0866_is_boss_template" in globals() else any(
        template.get(flag) for flag in ("world_boss","crypt_boss","mythic_crypt_boss","astral_boss","boss_mechanic")
    )
    for member, before_wallet in snapshots.items():
        run = getattr(member, "crypt_run_summary_v0380", None)
        if not isinstance(run, dict):
            continue
        run["kills"] += 1
        if is_boss:
            run["bosses"] += 1
        _kind, floor = _v0380_crypt_identity(mob.room_id)
        if floor is not None:
            run["max_floor"] = max(int(run.get("max_floor",0)), int(floor))
        after_wallet = legacy_currency_to_coins(member.character.silver, member.character.gold, member.character.mithril)
        run["currency"] += max(0, int(after_wallet - before_wallet))
    await _v0380_add_ultimate(self, 12 if is_boss else 5, reason="boss" if is_boss else "zabójstwo")
    return result
Session.mob_defeated = _mob_defeated_v0380


_move_before_v0380 = Session.move
async def _move_v0380(self, direction):
    old_room = self.character.room_id if self.character else None
    old_kind, _ = _v0380_crypt_identity(old_room)
    result = await _move_before_v0380(self, direction)
    new_room = self.character.room_id if self.character else None
    new_kind, _ = _v0380_crypt_identity(new_room)
    if new_kind:
        _v0380_run(self, room_id=new_room, create=True)
    if old_kind and not new_kind and new_room != old_room:
        await _v0380_finish_run(self, reason="wyjście z Krypty")
    return result
Session.move = _move_v0380


_dungeon_exit_before_v0380 = Session.dungeon_exit
async def _dungeon_exit_v0380(self):
    snapshots = {s: (s.character.room_id if s.character else None) for s in list(self.server.sessions) if not s.closed and s.character}
    result = await _dungeon_exit_before_v0380(self)
    for session, old_room in snapshots.items():
        old_kind, _ = _v0380_crypt_identity(old_room)
        new_room = session.character.room_id if session.character else None
        new_kind, _ = _v0380_crypt_identity(new_room)
        if old_kind and not new_kind and new_room != old_room:
            await _v0380_finish_run(session, reason="wycofanie z Krypty")
    return result
Session.dungeon_exit = _dungeon_exit_v0380


# Revive keeps the player in the same room and in the same party. Since Soulbound
# party-follow automatically picks all local members whenever the leader moves,
# the revived member remains eligible immediately; announce it explicitly.
_revive_before_v0380 = Session.revive_party_member_v0371
async def _revive_v0380(self, name):
    target_name = self.clean_party_player_argument(name)
    target = self.server.find_character_session(target_name) if target_name else None
    ok = await _revive_before_v0380(self, name)
    if ok and target and target.character and self.server.same_party(self.account_id, target.account_id):
        key = self.server.party_key_for_account(target.account_id)
        leader = self.server.session_by_account(key) if key is not None else None
        if leader and leader is not target:
            target.party_follow_resume_v0380 = int(leader.account_id)
            await target.send(
                f"Auto-follow po wskrzeszeniu pozostaje aktywny. Gdy lider {leader.character.name} ruszy z tej lokacji, podążysz za nim."
            )
    return ok
Session.revive_party_member_v0371 = _revive_v0380


# Party status also shows the shared Ultimate gauge.
_show_party_before_v0380 = Session.show_party
async def _show_party_v0380(self):
    result = await _show_party_before_v0380(self)
    if _v0380_party_key(self) is not None:
        state = _v0380_ultimate_state(self, create=True)
        await self.send(f"Ultimate drużyny: {int((state or {}).get('value',0))}/100.")
    return result
Session.show_party = _show_party_v0380


# Party handler: ultimate/status without adding another top-level parser branch.
_handle_party_before_v0380 = Session.handle_party
async def _handle_party_v0380(self, args):
    parts = str(args or "").strip().split(maxsplit=1)
    action = self.normalize_description_query(parts[0]) if parts else ""
    value = parts[1] if len(parts) > 1 else ""
    if action in ("ultimate", "ult", "super", "finisher"):
        if self.normalize_description_query(value) in ("status", "stan", "pasek"):
            state = _v0380_ultimate_state(self, create=True)
            await self.send(f"Ultimate drużyny: {int((state or {}).get('value',0))}/100.")
            return
        await party_ultimate_v0380(self)
        return
    return await _handle_party_before_v0380(self, args)
Session.handle_party = _handle_party_v0380
Session.party_ultimate_v0380 = party_ultimate_v0380


# Reset/migrate ultimate when parties are created/disbanded/transferred.
_create_party_before_v0380 = Session.create_party
async def _create_party_v0380(self):
    result = await _create_party_before_v0380(self)
    if result:
        _v0380_ultimate_store(self.server)[self.account_id] = {"value":0,"threshold":0}
    return result
Session.create_party = _create_party_v0380

_leave_party_before_v0380 = Session.leave_party
async def _leave_party_v0380(self, announce=True):
    key = _v0380_party_key(self)
    was_leader = key == self.account_id if key is not None else False
    result = await _leave_party_before_v0380(self, announce=announce)
    if was_leader and key is not None:
        _v0380_ultimate_store(self.server).pop(key, None)
    return result
Session.leave_party = _leave_party_v0380

_disband_party_before_v0380 = Session.disband_party
async def _disband_party_v0380(self):
    key = _v0380_party_key(self)
    result = await _disband_party_before_v0380(self)
    if key is not None:
        _v0380_ultimate_store(self.server).pop(key, None)
    return result
Session.disband_party = _disband_party_v0380


# Help / aliases.
HELP_TOPICS["partycombo_v0380"] = [
    "Party Combo: dwaj różni członkowie tej samej drużyny używają kompatybilnych skilli na tym samym przeciwniku w ciągu 8 sekund. Combo dodaje obrażenia i ładuje Ultimate.",
    "Przykłady: Mag + Wojownik = Eksplozja Żywiołu; Kapłan + Nekromanta = Zaćmienie Duszy; Łotrzyk + Mec = Precyzyjny Przełom; Mec + Inżynier = Magitekowy Overdrive.",
]
HELP_TOPIC_ALIASES.update({"combo":"partycombo_v0380","party combo":"partycombo_v0380","druzyna combo":"partycombo_v0380"})
HELP_TOPICS["partyultimate_v0380"] = [
    "Ultimate drużyny ma wspólny pasek 0-100 ładowany lokalną walką, skillami, combo i zabójstwami. Status: druzyna ultimate status. Użycie: druzyna ultimate.",
    "Ultimate może uruchomić tylko lider i wymaga co najmniej dwóch żywych członków w tej samej lokacji oraz wspólnego celu. Efekt zależy od składu klas party.",
]
HELP_TOPIC_ALIASES.update({"ultimate":"partyultimate_v0380","party ultimate":"partyultimate_v0380"})
HELP_TOPICS["dungeonsummary_v0380"] = [
    "Dungeon Summary dla zwykłej i Mitycznej Krypty: po wyjściu pokazuje czas runu, zabite moby i bossów, EXP, walutę, najcenniejszy drop i najgłębsze piętro.",
]
HELP_TOPIC_ALIASES.update({"dungeon summary":"dungeonsummary_v0380","podsumowanie krypty":"dungeonsummary_v0380"})
HELP_TOPICS.setdefault("druzyna", []).append(
    "v0.38.0: Party Combo, wspólny pasek Ultimate (druzyna ultimate/status) i auto-follow zachowany po wskrzeszeniu."
)
HELP_TOPICS.setdefault("krypta", []).append(
    "v0.38.0: po opuszczeniu zwykłej lub Mitycznej Krypty otrzymujesz Dungeon Summary całego runu."
)


def party_systems_audit_v0380():
    errors = []
    if len(PARTY_COMBO_RULES_V0380) < 8:
        errors.append("too few party combo rules")
    required_pairs = [
        frozenset(("Mag","Wojownik")), frozenset(("Kapłan","Nekromanta")),
        frozenset(("Łotrzyk","Mec")), frozenset(("Mec","Inżynier")),
    ]
    for pair in required_pairs:
        if pair not in PARTY_COMBO_RULES_V0380:
            errors.append(f"missing combo pair {sorted(pair)}")
    if not getattr(Session.use_class_skill, "_party_combo_v0380", False):
        errors.append("skill combo wrapper missing")
    if not getattr(Session.realtime_player_action, "_party_ultimate_v0380", False):
        errors.append("normal attack ultimate wrapper missing")
    if not hasattr(Session, "party_ultimate_v0380"):
        errors.append("party ultimate method missing")
    if Session.revive_party_member_v0371 is _revive_before_v0380:
        errors.append("revive auto-follow wrapper missing")
    if Session.dungeon_exit is _dungeon_exit_before_v0380:
        errors.append("dungeon summary exit wrapper missing")
    return {
        "version":"0.38.0", "combo_rules":len(PARTY_COMBO_RULES_V0380),
        "error_count":len(errors), "errors":errors,
    }

PARTY_SYSTEMS_AUDIT_V0380 = party_systems_audit_v0380()
if PARTY_SYSTEMS_AUDIT_V0380["error_count"]:
    raise RuntimeError("Party Systems Audit v0.38.0 failed: " + "; ".join(PARTY_SYSTEMS_AUDIT_V0380["errors"]))
