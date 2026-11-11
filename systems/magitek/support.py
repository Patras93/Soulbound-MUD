# -*- coding: utf-8 -*-
"""Soulbound v107 staging: executable support skills for UOSS Magitek.

The UOSS source contains no durations, damage coefficients, ward percentages
or teleport failure rules. Constants below are explicitly Soulbound test tuning.
No production database migration and no effect unless v107 staging is enabled.
"""
from __future__ import annotations

import random
import time

WARD_KEY = 'v107_magitek_ward'
RUNIC_KEY = 'v107_magitek_runicweapon'
WARD_DEFENSE_MULTIPLIER = 1.25  # Soulbound prototype; not an UOSS number


def active_ward(session, now=None):
    row = getattr(session, 'active_skill_buffs', {}).get(WARD_KEY)
    now = time.time() if now is None else float(now)
    if row and float(row.get('until', 0)) > now:
        mode = row.get('magitek_mode')
        if mode in ('tekshield', 'tekbarrier'):
            return mode
    return None


def runic_weapon_active(session, now=None):
    row = getattr(session, 'active_skill_buffs', {}).get(RUNIC_KEY)
    now = time.time() if now is None else float(now)
    return bool(row and float(row.get('until', 0)) > now)


def duration_seconds(slug, level, willpower):
    """Short statuses; their exact seconds are not defined by UOSS."""
    level = max(1, int(level))
    if slug in ('tekshield', 'tekbarrier'):
        return min(80, 15 + level // 12 + max(0, int(willpower)) // 200)
    if slug == 'runicweapon':
        return min(60, 12 + level // 10)
    raise ValueError(slug)


def _valid_party_target(actor, query):
    """Only self or a nearby, living, authenticated party member."""
    text = str(query or '').strip().casefold()
    if text.startswith('at '):
        text = text[3:].strip()
    if not text or text in ('me', 'self', 'siebie', 'ja'):
        return actor
    members = list(actor.server.party_sessions(actor.account_id, same_room=actor.character.room_id) or [])
    for member in members:
        if (not member.closed and member.character and member.current_hp > 0
                and member.character.room_id == actor.character.room_id
                and member.character.name.casefold() == text):
            return member
    return None


def _can_cast(actor, skill):
    if not getattr(actor, 'character', None) or getattr(actor, 'closed', False):
        return False, 'Brak aktywnej postaci.'
    if getattr(actor, 'current_hp', 0) <= 0 or actor.is_downed_v0371():
        return False, 'Martwa lub powalona postać nie może używać Magiteka.'
    if actor.class_mastery_level('Magitek') < int(skill['unlock']):
        return False, f'{skill["name"]} wymaga poziomu klasy {skill["unlock"]}.'
    if not actor.server.db.knows_skill(actor.account_id, skill['id']):
        return False, f'Najpierw naucz się {skill["name"]}.'
    return True, ''


# Only temporary, source-backed MONSTER buffs. Time values are monotonic
# clocks (systems.monster_ai); wall-clock buffs and permanent UOSS boss
# properties must never be guessed or removed by Magitek's Diffuser.
DISPELABLE_MOB_BUFFS = {
    'monster_ai_guard_until_v1160': 'osłona potwora',
    'monster_ai_empowered_until_v1160': 'wzmocnienie ataku',
}


def removable_enemy_buffs(mob, now_monotonic=None):
    """Return actual active temporary benefits; never claim intrinsic buffs."""
    if not mob or not getattr(mob, 'alive', False) or int(getattr(mob, 'hp', 0)) <= 0:
        return ()
    now = time.monotonic() if now_monotonic is None else float(now_monotonic)
    active = []
    for field, title in DISPELABLE_MOB_BUFFS.items():
        try:
            expiry = float(getattr(mob, field, 0) or 0)
        except (TypeError, ValueError, OverflowError):
            continue
        if expiry > now:
            active.append((field, title))
    return tuple(active)


def dispel_enemy_buffs(mob, now_monotonic=None):
    """Clear only these 2 original runtime AI status flags, not boss mechanics."""
    removed = removable_enemy_buffs(mob, now_monotonic)
    for field, title in removed:
        setattr(mob, field, 0.0)
    return tuple(title for _, title in removed)


async def use_support_skill(actor, skill, target_text):
    """Return handled=True. Commit effects and XP only after all validation."""
    slug = skill['v107_skill']
    valid, error = _can_cast(actor, skill)
    if not valid:
        await actor.send(error)
        return
    progress = actor.server.db.skill_progress(actor.account_id, skill['id'])
    level = max(1, int(progress['level'])) if progress is not None else 1
    now = time.time()
    if slug in ('tekshield', 'tekbarrier'):
        target = _valid_party_target(actor, target_text)
        if target is None or target.current_hp <= 0:
            await actor.send('Osłona: cel musi być żywym członkiem drużyny w tym samym pokoju.')
            return
        length = duration_seconds(slug, level, actor.effective_willpower())
        if not hasattr(target, 'active_skill_buffs') or target.active_skill_buffs is None:
            target.active_skill_buffs = {}
        # A single shared key enforces source-exclusive TekShield/TekBarrier.
        target.active_skill_buffs[WARD_KEY] = {
            'name': skill['name'], 'source': actor.character.name,
            'until': now + length, 'beneficial': True,
            'magitek_mode': slug, 'canonical_status': 'protect',
            'properties': ['dispelable', 'extendable'],
            'numeric_source_defined': False,
        }
        await actor.grant_skill_use_xp(skill)
        await actor.send(f'{skill["name"]}: {target.character.name}, {length} s. '
                         + ('Protect + Shell.' if slug == 'tekshield' else 'Protect + Reflect.'))
        if target is not actor:
            await target.send(f'{actor.character.name} używa {skill["name"]}: osłona {length} s.')
        return
    if slug == 'runicweapon':
        if target_text and target_text.strip().casefold() not in ('self', 'me', 'ja', 'siebie'):
            await actor.send('Runic Weapon działa wyłącznie na własną postać.')
            return
        seconds = duration_seconds(slug, level, actor.effective_willpower())
        if not hasattr(actor, 'active_skill_buffs') or actor.active_skill_buffs is None:
            actor.active_skill_buffs = {}
        actor.active_skill_buffs[RUNIC_KEY] = {
            'name': 'Runic Weapon', 'until': now + seconds,
            'source': actor.character.name, 'beneficial': True,
            'properties': ['dispelable'], 'numeric_source_defined': False,
        }
        await actor.grant_skill_use_xp(skill)
        await actor.send(f'Runic Weapon: gotowość do przechwytywania magii przez {seconds} s.')
        return
    if slug == 'diffuser':
        target = _valid_party_target(actor, target_text)
        if target is None:
            # The genuine combat target resolver checks enemy names, PVP/NPC
            # exclusions, engagement rights, party protection and boss openers.
            # We do not bypass any of those checks even though dispel deals 0 HP.
            query = str(target_text or '').strip()
            if query.casefold().startswith('at '):
                query = query[3:].strip()
            if not query:
                await actor.send('Diffuser: podaj wroga lub członka drużyny.')
                return
            mob = await actor.skill_combat_target(query)
            if not mob or not mob.alive or mob.room_id != actor.character.room_id:
                return
            effects = dispel_enemy_buffs(mob)
            if not effects:
                await actor.send('Diffuser: wróg nie ma czasowych wzmocnień, które można rozproszyć.')
                return
            await actor.grant_skill_use_xp(skill)
            from data.mobs import MOB_TEMPLATES
            name = MOB_TEMPLATES.get(mob.template_id, {}).get('name', mob.template_id)
            await actor.send(f'Diffuser: {name}. Usunięto: {", ".join(effects)}.')
            if getattr(actor, 'combat_mob_key', None) == mob.key:
                await actor.ensure_realtime_combat()
            return
        buffs = getattr(target, 'active_skill_buffs', None)
        if not isinstance(buffs, dict):
            await actor.send('Diffuser: cel nie ma aktywnych wzmocnień.')
            return
        # No hostile dispel against allies with active source-backed Permanence.
        if target is not actor and getattr(target, 'permanence_active_v11154', lambda: False)():
            await actor.send('Diffuser: Permanence chroni wzmocnienia sojusznika.')
            return
        keys = [key for key, row in buffs.items()
                if isinstance(row, dict) and row.get('beneficial') is True
                and float(row.get('until', 0) or 0) > now]
        if not keys:
            await actor.send('Diffuser: brak aktywnych pozytywnych efektów do rozproszenia.')
            return
        for key in keys:
            buffs.pop(key, None)
        await actor.grant_skill_use_xp(skill)
        await actor.send(f'Diffuser: rozproszono {len(keys)} pozytywnych efektów: {target.character.name}.')
        if target is not actor:
            await target.send(f'{actor.character.name} usuwa {len(keys)} pozytywnych efektów przez Diffuser.')
        return
    if slug == 'xfer':
        if target_text and str(target_text).strip().casefold() not in ('party','druzyna','drużyna','all'):
            await actor.send('X-Fer przenosi całą obecną drużynę. Wpisz mtek xfer.')
            return
        origin = actor.character.room_id
        # Never teleport remote party members (source all allies, adapted to local room).
        members = list(actor.server.party_sessions(actor.account_id, same_room=origin) or [actor])
        if actor not in members:
            members.append(actor)
        members = list({member.account_id: member for member in members}.values())
        members.sort(key=lambda member: member.character.name.casefold())
        for member in members:
            if (getattr(member, 'closed', False) or not member.character or
                member.character.room_id != origin or member.current_hp <= 0 or
                member.is_downed_v0371() or getattr(member, 'combat_mob_key', None)):
                await actor.send('X-Fer: członek drużyny jest nieobecny, walczy albo jest powalony. Teleport anulowany.')
                return
        from data.rooms import ROOMS
        if 'square' not in ROOMS:
            await actor.send('X-Fer: Plac Dusz nie jest dostępny.')
            return
        # Save every actor BEFORE announcing success. On persistence error,
        # revert previously moved characters; do not give skill XP.
        moved = []
        try:
            for member in members:
                previous = member.character.room_id
                member.character.room_id = 'square'
                try:
                    member.server.db.save_character(member.character)
                except Exception:
                    member.character.room_id = previous
                    raise
                member.previous_room_id = previous
                moved.append((member, previous))
        except Exception:
            for member, previous in reversed(moved):
                member.character.room_id = previous
                member.server.db.save_character(member.character)
            await actor.send('X-Fer: zapis teleportacji nie powiódł się; pozycje cofnięte.')
            return
        await actor.grant_skill_use_xp(skill)
        for member, previous in moved:
            if previous != 'square':
                await actor.server.broadcast_room(previous, f'{member.character.name} znika dzięki X-Fer.', exclude=member)
            await member.send(f'X-Fer: teleport na Plac Dusz, grupa {len(members)}.')
            await member.look()
        return
    raise ValueError(f'unsupported Magitek support skill {slug}')


def install_defense_adapter(equipment_mixin):
    """Protect/Shell work on the genuine defense calculations; no HP refunds."""
    from functools import wraps
    old_defense = equipment_mixin.defense
    old_magic_defense = equipment_mixin.magic_defense

    @wraps(old_defense)
    def physical(self):
        base = old_defense(self)
        return max(0, int(round(base * WARD_DEFENSE_MULTIPLIER))) if active_ward(self) else base

    @wraps(old_magic_defense)
    def magical(self):
        base = old_magic_defense(self)
        return max(0, int(round(base * WARD_DEFENSE_MULTIPLIER))) if active_ward(self) == 'tekshield' else base

    equipment_mixin.defense = physical
    equipment_mixin.magic_defense = magical


def install_runic_adapter(skill_learning_mixin):
    """Intercept only attacks known to be magical; no generic physical counter."""
    from functools import wraps
    from data.mobs import MOB_TEMPLATES
    from systems.magitek.rules import runic_interception
    old = skill_learning_mixin.mec_intercept_incoming_attack_v11196

    @wraps(old)
    async def intercept(self, mob):
        if not mob or not mob.alive:
            return False
        template = MOB_TEMPLATES.get(mob.template_id, {})
        if str(template.get('damage_type', 'physical')).lower() != 'magic':
            return await old(self, mob)
        ward = active_ward(self)
        if ward == 'tekbarrier':
            # Reflect incoming magical damage, limited by boss defense hooks.
            raw = max(1, int(template.get('damage', 1)) // 3)
            dealt = await self.apply_boss_defense(mob, raw)
            dealt = min(mob.hp, max(0, int(dealt)))
            mob.hp -= dealt
            await self.send(f'TekBarrier odbija magię: {dealt} obrażeń.')
            if mob.hp <= 0:
                await self.mob_defeated(mob)
            return True
        # A friendly Magitek may cast TekBarrier on another class.
        # Only the Runic counter itself requires the Magitek class.
        if getattr(getattr(self, 'character', None), 'class_name', None) != 'Magitek':
            return await old(self, mob)
        temporary = runic_weapon_active(self)
        selected = (self.server.db.job_ability_slot(self.account_id, 'counter')
                    == 'v107_magitek_runic' and
                    self.server.db.knows_skill(self.account_id, 'v107_magitek_runic'))
        if not temporary and not selected:
            return await old(self, mob)
        # The same incoming action can reach the realtime and fallback paths.
        # Do not give two independent random rolls for one monster turn.
        token = (id(mob), int(getattr(mob, 'combat_turn', 0)))
        if getattr(self, '_v107_last_runic_attempt', None) == token:
            return await old(self, mob)
        self._v107_last_runic_attempt = token
        level = 1
        which = 'v107_magitek_runicweapon' if temporary else 'v107_magitek_runic'
        progress = self.server.db.skill_progress(self.account_id, which)
        if progress:
            level = max(1, int(progress['level']))
        wisdom = max(0, int(self.effective_intelligence()))
        willpower = max(0, int(self.effective_willpower()))
        weapon_power = max(0, int(self.equipment_flat_power_totals_v11187().get('attack', 0)))
        chance = min(.65, .18 + min(.25, level / 1500.0) + min(.15, willpower / 3000.0))
        success, mp = runic_interception(magical_attack=True, roll=random.random(),
                                         chance=chance, wisdom=wisdom,
                                         willpower=willpower, weapon_power=weapon_power)
        if success:
            gained = min(max(0, self.max_mana() - self.current_mana), mp)
            self.current_mana += gained
            await self.send(f'Runic przechwytuje magię. Odzyskano {gained} MP.')
            return True
        return await old(self, mob)

    skill_learning_mixin.mec_intercept_incoming_attack_v11196 = intercept
