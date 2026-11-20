# -*- coding: utf-8 -*-
"""Independent Jammer Stop target selection, retaining UOSS Support expansion.

The Support Soul Weapon + the ordinary AoE toggle enable room-wide Stop.
Jammer itself needs no Logic Bomb or prior Paralyze. Bosses may be
stopped, but only in the caster's current combat room; story/UOSS access,
engagements and already-active Stop remain guarded.
"""


def select_jammer_targets(room_mobs, templates, *, support_weapon=False,
                          aoe_enabled=True, preferred_key=None, allowed=None,
                          room_id=None, target_text=''):
    eligible = []
    immune = 0
    already = 0
    seen = set()
    for mob in room_mobs:
        if not mob or not getattr(mob, 'alive', False):
            continue
        # The room index is the first boundary, but an explicit check also
        # rejects stale/foreign-room instances returned by a faulty cache.
        if room_id is not None and getattr(mob, 'room_id', None) != room_id:
            continue
        key = getattr(mob, 'key', None)
        if key in seen:
            continue
        seen.add(key)
        template = templates.get(mob.template_id)
        if template is None or (allowed is not None and not allowed(mob, template)):
            continue
        if max(0, int(getattr(mob, 'v11196_jammer_stop_rounds', 0) or 0)):
            already += 1
            continue
        eligible.append(mob)
    if support_weapon and aoe_enabled:
        return eligible, immune, already
    if not eligible:
        return [], immune, already
    # UOSS permits an explicit single target. Never silently substitute a
    # different monster if the player's name was not found or is protected.
    # The permanent Soul makes wide Jammer possible, but 'aoe off' still
    # selects a single target. No Logic Bomb/Paralyze prerequisite is involved.
    wanted = str(target_text or '').strip()
    if wanted.casefold().startswith('at '):
        wanted = wanted[3:].strip()
    if wanted:
        from network.protocol_gameplay_utils import normalize_lookup_text
        lookup = normalize_lookup_text(wanted)
        choice = next((mob for mob in eligible
                       if lookup == normalize_lookup_text(str(mob.key)) or
                       lookup in normalize_lookup_text(str(templates[mob.template_id].get('name', '')))),
                      None)
        return ([choice] if choice is not None else []), immune, already
    choice = next((mob for mob in eligible if mob.key == preferred_key), eligible[0])
    return [choice], immune, already


async def cast_jammer(session, skill, target_text=''):
    """Cast standalone Mec Jammer while preserving the protected native method.

    Only the explicit Jammer skill is routed here by magitek.runtime.install().
    UOSS Support/AoE determine width; no Logic Bomb/paralysis is required.
    """
    import random
    import time
    from core.progression_600 import SKILL_MAX_LEVEL
    from data.mobs import MOB_TEMPLATES
    from world.uoss_superboss_runtime import superboss_attack_gate_v11137

    if (getattr(session, 'current_hp', 0) <= 0
            or getattr(session, 'is_downed_v0371', lambda: False)()):
        await session.send('Martwa lub powalona postać nie może używać umiejętności.')
        return
    skill_class = session.skill_class_name(skill)
    mastery = session.class_mastery_level(skill_class)
    if mastery < int(skill['unlock']):
        await session.send(
            f"{skill['name']} wymaga Biegłości klasy {skill['unlock']}. "
            f"Aktualna Biegłość {skill_class}: {mastery}."
        )
        return
    if not session.server.db.knows_skill(session.account_id, skill['id']):
        await session.send(f"Nie znasz jeszcze umiejętności {skill['name']}. Naucz się jej u nauczyciela klasy.")
        return
    progress = session.server.db.skill_progress(session.account_id, skill['id'])
    skill_level = int(progress['level'])
    mechanic_lock = bool(skill.get('mechanic_cooldown'))
    effective_cooldown = session.effective_skill_cooldown(skill, skill_level) if mechanic_lock else 0
    now = time.time()
    await session.mec_refresh_vmax_v0319()
    ready_at = session.skill_cooldown_ready_at_v0364(skill) if mechanic_lock else 0.0
    if ready_at > now:
        await session.send(f"{skill['name']} jest na cooldownie jeszcze {int(ready_at-now+0.999)} sekund.")
        return
    # Soulbound's Mec Soul is permanent; there is no equip/unequip Support
    # weapon action. In Soulbound the existing AoE switch selects the 20 MP
    # single-target mode or the 40 MP Support-wide mode (when Soul is active).
    support_effect = bool(session.mec_support_effect_v11149())
    aoe_enabled = bool(session.offensive_aoe_enabled_v11120())
    wide_jammer = support_effect and aoe_enabled
    mana_cost = session.combat_skill_mana_cost_v11191(skill, skill_class)
    if not wide_jammer and skill.get('uoss_mp_cost') is not None:
        mana_cost = max(0, int(skill['uoss_mp_cost']))
    if mana_cost > 0:
        mana_cost = int(round(mana_cost * session.equipment_mp_cost_multiplier_v11176()))
    if mana_cost > session.current_mana:
        await session.send(f"Za mało Many. {skill['name']} wymaga {mana_cost}, a masz {session.current_mana}.")
        return

    cast_room_id = session.character.room_id
    session.server.world.refresh()
    room_mobs = list(session.server.world.room_mobs(cast_room_id))
    def attackable(mob, template):
        if (session.character.room_id != cast_room_id
                or getattr(mob, 'room_id', None) != cast_room_id):
            return False
        okay, _ = superboss_attack_gate_v11137(session, template)
        return bool(okay and session.server.engagement_allowed(session, mob))
    targets, immune_count, stopped_count = select_jammer_targets(
        room_mobs, MOB_TEMPLATES, support_weapon=support_effect,
        aoe_enabled=aoe_enabled, preferred_key=session.combat_mob_key,
        allowed=attackable, room_id=cast_room_id, target_text=target_text,
    )
    if not targets:
        if target_text and not wide_jammer:
            await session.send('Jammer: nie ma takiego dostępnego przeciwnika w tym pokoju. Mana bez zmian.')
        else:
            await session.send(
                f"Jammer: brak dostępnych przeciwników do zatrzymania. "
                f"Już zatrzymanych: {stopped_count}. "
                "Mana bez zmian."
            )
        return

    # Resolve the entire eligible set before paying mana. Refuse to turn a
    # protected/foreign engagement into a new target after any side effects.
    for target in targets:
        if (not target.alive or target.room_id != cast_room_id
                or session.character.room_id != cast_room_id
                or not attackable(target, MOB_TEMPLATES[target.template_id])):
            await session.send('Jammer: zmienił się stan przeciwników. Mana bez zmian.')
            return
    if session.auto_fishing or session.auto_fishing_task:
        await session.stop_auto_fishing(announce=False)
        await session.send('Auto-łowienie wyłączone z powodu walki.')
    if session.auto_mining or session.auto_mining_task:
        await session.stop_auto_mining(announce=False)
        await session.send('Auto-kopanie wyłączone z powodu walki.')
    if session.auto_woodcutting or session.auto_woodcutting_task:
        await session.stop_auto_woodcutting(announce=False)
        await session.send('Auto-Drwalstwo wyłączone z powodu walki.')
    # Auto-activity shutdown awaits can move the character or let a target
    # leave; verify the full set again before any mana/engagement side effect.
    for target in targets:
        if (not target.alive or session.character.room_id != cast_room_id
                or target.room_id != cast_room_id
                or not attackable(target, MOB_TEMPLATES[target.template_id])):
            await session.send('Jammer: cel opuścił aktualną lokację. Mana bez zmian.')
            return
    for target in targets:
        session.server.sanitize_mob_engagement(target)
        session.apply_adaptive_mob_scale_v11330(target)

    session.current_mana -= mana_cost
    if effective_cooldown > 0:
        session.start_skill_cooldown_v0364(skill, effective_cooldown, now)
    jammer_level = max(1, min(SKILL_MAX_LEVEL, skill_level))
    p = (jammer_level-1) / float(max(1, SKILL_MAX_LEVEL-1))
    will = max(1, int(session.effective_willpower()))
    will_ratio = max(0.01, will/175.0)
    accuracy = (
        float(skill.get('soulbound_base_accuracy', 0.50) or 0.50)
        + p * float(skill.get('soulbound_skill_accuracy_bonus_max', 0.25) or 0.25)
        + min(float(skill.get('soulbound_will_accuracy_bonus_max', 0.15) or 0.15),
              0.075*(will_ratio**0.50))
    )
    start = max(1, int(skill.get('soulbound_duration_rounds_level1', 8) or 8))
    end = max(start, int(skill.get('soulbound_duration_rounds_level600', 16) or 16))
    rounds = max(1, int(round(start+(end-start)*(p**0.82))))
    rounds += min(int(skill.get('soulbound_will_duration_bonus_max', 4) or 4),
                  max(0, int(round((will_ratio**0.50)-1.0))))
    hits = misses = 0
    for target in targets:
        # An async message/assist from a preceding target may have changed
        # rooms; never apply Stop to mobs from another location.
        if (session.character.room_id != cast_room_id
                or not target.alive or target.room_id != cast_room_id):
            continue
        template = MOB_TEMPLATES[target.template_id]
        machine = bool(template.get('machine') or
                       str(template.get('creature_type','')).casefold() == 'machine')
        chance = accuracy + (float(skill.get('soulbound_machine_accuracy_bonus',0.15) or 0.15)
                             if machine else 0.0)
        chance = max(0.05, min(float(skill.get('soulbound_accuracy_cap',0.98) or 0.98), chance))
        if random.random() < chance:
            target.v11196_jammer_stop_rounds = rounds
            target.v11196_jammer_stop_cleanseable = True
            hits += 1
            await session.send(f"Jammer: {template['name']} zostaje jednorazowo wyłączony "
                               f"na {rounds} akcji. Celność {int(round(chance*100))} procent."
                               + (' Bonus Machine.' if machine else ''))
        else:
            misses += 1
            await session.send(f"Jammer: {template['name']} opiera się Stop. "
                               f"Celność {int(round(chance*100))} procent."
                               + (' Bonus Machine.' if machine else ''))
        if target.engaged_at <= 0:
            target.engaged_at = time.monotonic()
        if not target.engaged_by:
            target.engaged_by = session.character.name
        await session.server.auto_assist_party_combat(session, target)
    await session.send(
        f"Jammer: {hits} celów zatrzymanych, {misses} oparło się."
        + (' Dusza Meca: Jammer obejmuje wszystkich przeciwników.' if support_effect and aoe_enabled
           else (' AoE wyłączone: Jammer działa na jeden cel.'
                 if support_effect and not aoe_enabled else ''))
    )
    # One compact, essential party notification per cast. The server helper
    # excludes the caster, online non-party players and remote party members.
    # Never repeat the detailed per-target caster messages for each teammate.
    await session.server.party_combat_broadcast(
        session,
        f"{session.character.name} używa Jammera: "
        f"{hits} zatrzymanych, {misses} oparło się.",
        detail='essential',
    )
    await session.grant_skill_use_xp(skill)
    # A move during a per-target message or party broadcast must not leave
    # the next-room session targeting a monster from the previous room.
    if session.character.room_id != cast_room_id:
        return
    preferred = next((target for target in targets if target.key == session.combat_mob_key), targets[0])
    if not preferred.alive or preferred.room_id != cast_room_id:
        return
    session.combat_mob_key = preferred.key
    await session.ensure_realtime_combat()
