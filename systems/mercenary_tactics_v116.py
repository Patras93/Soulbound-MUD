# -*- coding: utf-8 -*-
"""v116: tactical focus/area coordination for hired mercenaries.

Room-local transient intent only. No SQL writes, no world-wide aggro, no
new skills or damage multipliers. Fresh manual casts take precedence over
older intent; idle combat defaults to focused attacks.
"""
import time
import logging

LOG = logging.getLogger(__name__)

INTENT_SECONDS = 12.0


def remember_player_intent(session, area, target=None, now=None):
    character = getattr(session, 'character', None)
    if character is None:
        return
    when = time.monotonic() if now is None else float(now)
    session._mercenary_intent_v116 = {
        'room': character.room_id,
        'when': when,
        'mode': 'area' if area else 'focus',
        'target': str(getattr(target, 'key', '') or ''),
    }


def combat_intent(session, now=None):
    """Most recent valid local party intention; default is single target.

    Ignore old orders and parties in other rooms.  Only real player casts
    record intent, so companions never create enemies or make new pulls.
    """
    character = getattr(session, 'character', None)
    if character is None:
        return 'focus'
    when = time.monotonic() if now is None else float(now)
    server = getattr(session, 'server', None)
    members = (server.party_sessions(session.account_id, same_room=character.room_id)
               if server is not None else None) or [session]
    latest = None
    for member in members:
        if (getattr(member, 'closed', False) or
                getattr(getattr(member, 'character', None), 'room_id', None) != character.room_id):
            continue
        note = getattr(member, '_mercenary_intent_v116', None)
        if not isinstance(note, dict) or note.get('room') != character.room_id:
            continue
        stamp = note.get('when')
        if type(stamp) not in (int, float) or not 0 <= when - stamp <= INTENT_SECONDS:
            continue
        if note.get('mode') not in ('focus', 'area'):
            continue
        if latest is None or stamp > latest[0]:
            latest = stamp, note['mode']
    return latest[1] if latest else 'focus'


def select_ally_v116(living, *, action, threshold, healing_blocked=None):
    """Select the most injured *eligible* local companion, without side effects.

    A dying ally with an active anti-heal must not prevent helping another
    injured player; an existing barrier must not make the other unshielded
    ally invisible. Caller supplies only living members of the local party.
    This does not heal, grant guard, consume an attack or touch player saves.
    """
    if action not in ('heal', 'guard'):
        raise ValueError('Unknown mercenary support action')
    eligible = []
    for ally in living:
        if (getattr(ally, 'closed', False) or not getattr(ally, 'character', None)):
            continue
        hp_max = max(1, int(ally.max_hp()))
        hp_now = int(getattr(ally, 'current_hp', 0) or 0)
        if hp_now <= 0 or hp_now >= hp_max * threshold:
            continue
        if action == 'heal':
            if healing_blocked is not None and healing_blocked(ally):
                continue
        elif int(getattr(ally, 'skill_guard', 0) or 0) > 0:
            continue
        eligible.append((hp_now / hp_max, ally))
    return min(eligible, key=lambda pair: pair[0])[1] if eligible else None


def mercenary_race_damage_v116(role):
    """Read an NPC's *own* native race passive, never the owner's race.

    Eliza is the only contracted Vampire. No new race table or saved field.
    """
    if role != 'wampir':
        return 1.0
    from systems.v115.vampire_mercenary import MERCENARIES
    from systems.new_heroes_v900 import NEW_RACES
    race = MERCENARIES[role].get('race')
    for row in NEW_RACES:
        if row[0] == race and row[-2] == 'all_damage':
            return 1.0 + float(row[-1])
    return 1.0


def conserve_finishing_burst_v116(mob, expected_damage, boss=False):
    """Do not trigger Mec's rare V-MAX cooldown against a dying ordinary mob.

    Mercenaries have no separate MP pool; conserve cooldowns, not phantom MP.
    The native boss classification always wins over this approximation.
    """
    if boss or mob is None or not getattr(mob, 'alive', False):
        return False
    hp = int(getattr(mob, 'hp', 0) or 0)
    return 0 < hp <= max(1, int(expected_damage))


def install_skill_intent_hook_v116(mixin):
    """Add a small observation layer after the full native cast and OLC wrappers.

    Track only verified action side effects, never attempted/blocked casts.
    Catch errors only in observation; exceptions from the actual cast propagate.
    """
    from functools import wraps
    native_cast = mixin.use_class_skill

    @wraps(native_cast)
    async def observed_cast(self, raw):
        skill = None
        snapshot = ()
        old_mana = None
        room = None
        try:
            character = getattr(self, 'character', None)
            if character is not None:
                room = character.room_id
                skill, _ = self.find_skill_from_input(raw)
                special = str(skill.get('mec_special', '') or '') if skill else ''
                if skill and (skill.get('kind') in ('damage', 'aoe_damage', 'execute', 'drain')
                              or special == 'jammer'):
                    old_mana = int(getattr(self, 'current_mana', 0) or 0)
                    room_mobs = getattr(getattr(self.server, 'world', None), 'room_mobs', None)
                    if callable(room_mobs):
                        snapshot = tuple((enemy,
                                          getattr(enemy, 'hp', None),
                                          getattr(enemy, 'engaged_by', None),
                                          getattr(enemy, 'aoe_engaged_by', None),
                                          getattr(enemy, 'v11196_jammer_stop_rounds', None))
                                         for enemy in room_mobs(room))
                else:
                    skill = None
        except (AttributeError, KeyError, TypeError, ValueError):
            skill = None

        result = await native_cast(self, raw)
        if skill and snapshot and getattr(getattr(self, 'character', None), 'room_id', None) == room:
            try:
                changed = any((enemy.hp != hp or
                               enemy.engaged_by != engaged or
                               getattr(enemy, 'aoe_engaged_by', None) != area_owner or
                               getattr(enemy, 'v11196_jammer_stop_rounds', None) != stopped)
                              for enemy, hp, engaged, area_owner, stopped in snapshot)
                changed = changed or int(getattr(self, 'current_mana', 0) or 0) < old_mana
                if changed:
                    special = str(skill.get('mec_special', '') or '')
                    area_kind = (skill.get('kind') == 'aoe_damage' or special in (
                        'starlight_shower', 'shoot_all', 'laser_spin',
                        'area_bomb', 'maelstrom', 'shock', 'cosmic_rave'))
                    if special == 'jammer':
                        area_kind = bool(self.mec_support_effect_v11149())
                    area_enabled = bool(self.offensive_aoe_enabled_v11120()) if area_kind else False
                    # Verify multiple engaged targets after the real cast. No
                    # mercenary command can open a new enemy encounter.
                    party = self.server.party_sessions(self.account_id, same_room=room) or [self]
                    names = {member.character.name for member in party if getattr(member, 'character', None)}
                    live = [enemy for enemy, *_ in snapshot if
                            getattr(enemy, 'alive', False) and getattr(enemy, 'hp', 0) > 0 and
                            getattr(enemy, 'room_id', None) == room and
                            (getattr(enemy, 'engaged_by', None) in names or
                             getattr(enemy, 'aoe_engaged_by', None) in names)]
                    target = next((enemy for enemy, *_ in snapshot
                                   if getattr(enemy, 'key', None) == getattr(self, 'combat_mob_key', None)), None)
                    remember_player_intent(self, area_kind and area_enabled and len(live) > 1,
                                           target=target)
            except (AttributeError, KeyError, TypeError, ValueError):
                # Server-only diagnostic: a successful cast must remain successful.
                LOG.warning('Mercenary skill intent observation failed', exc_info=True)
        return result

    mixin.use_class_skill = observed_cast


def install_attack_intent_hook_v116(mixin):
    """Track successful single-target attacks without modifying protected AST."""
    from functools import wraps
    native_attack = mixin.attack

    @wraps(native_attack)
    async def observed_attack(self, query):
        result = await native_attack(self, query)
        try:
            character = getattr(self, 'character', None)
            world = getattr(getattr(self, 'server', None), 'world', None)
            if character is not None and world is not None:
                mob = world.mobs.get(getattr(self, 'combat_mob_key', None))
                wanted = str(query or '').strip()
                if mob is not None and mob.alive and mob.room_id == character.room_id:
                    # Never treat an invalid/blocked attack as a new order.
                    valid = not wanted or world.find_mob(character.room_id, wanted) is mob
                    if valid:
                        remember_player_intent(self, area=False, target=mob)
        except (AttributeError, TypeError, ValueError, KeyError):
            # Record unexpected telemetry failures without undoing the native hit.
            LOG.warning('Mercenary attack intent observation failed', exc_info=True)
        return result

    mixin.attack = observed_attack
