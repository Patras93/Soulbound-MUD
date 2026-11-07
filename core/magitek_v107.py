# -*- coding: utf-8 -*-
"""Soulbound 107.00.0 -- explicitly sourced UOSS Magitek Knight catalogue.

Source: ability descriptions provided by the player, 2026-11-05.
UOSS 'Base AP' is *learning/training AP*, NOT damage or mana cost.
The class itself has NO level or quest gate in Soulbound (player decision).
Individual ability level gates are retained.  Other numbers below marked as
soulbound_* are provisional Soulbound balance, NOT alleged UOSS coefficients.

Staging catalogue until special effects, save-state and TCP are finished.
"""
from __future__ import annotations

CLASS_NAME = 'Magitek'
CLASS_INFO = (CLASS_NAME, 'magic', 'Rdzeń Magiteka', 7)
CLASS_BONUSES = {
    'strength': 2, 'dexterity': 2, 'constitution': 0,
    'intelligence': 3, 'willpower': 2, 'charisma': 0,
}
SOURCE_WEAPONS = ('Greatsword', 'Gun', 'Rod', 'Sword')
SOURCE_ARMOR = ('Armor', 'Robe', 'Helmet', 'Shield')
SOURCE_JOB_NAME = 'Magitek Knight'

# id, name, AP, unlock, kind, target, scaled stats, source-specific flags
_DEFINITIONS = (
    ('firebeam', 'Fire Beam', 1000, 1, 'damage', 'enemy', ('attack','magic_attack'), {'element': 'fire', 'v107_infuses': 'fire'}),
    ('icebeam', 'Ice Beam', 1000, 1, 'damage', 'enemy', ('attack','magic_attack'), {'element': 'ice', 'v107_infuses': 'ice'}),
    ('boltbeam', 'Bolt Beam', 1000, 1, 'damage', 'enemy', ('attack','magic_attack'), {'element': 'lightning', 'v107_infuses': 'lightning'}),
    ('healforce', 'Heal Force', 1000, 1, 'heal', 'ally', ('willpower',), {'v107_ability': 'heal'}),
    ('tekshield', 'TekShield', 400, 1, 'guard', 'ally', ('willpower',), {'v107_ability': 'protect_shell', 'v107_excludes': 'tekbarrier', 'source_dispellable': True, 'source_extendable': True}),
    ('tekbarrier', 'TekBarrier', 400, 1, 'guard', 'ally', ('willpower',), {'v107_ability': 'protect_reflect', 'v107_excludes': 'tekshield', 'source_dispellable': True, 'source_extendable': True}),
    ('gravitybomb', 'Gravity Bomb', 750, 1, 'damage', 'enemy', ('willpower',), {'v107_ability': 'half_hp_chance', 'v107_level_effect': 'accuracy'}),
    ('bioblast', 'Bio Blast', 1800, 1, 'aoe_damage', 'all_enemies', ('attack','magic_attack','willpower'), {'element': 'poison', 'v107_infuses': 'poison', 'v107_poison': True, 'source_nondiminishing': True, 'source_cleanseable': True}),
    ('tekmissile', 'TekMissile', 2000, 1, 'damage', 'enemy', ('attack','magic_attack'), {'v107_ability': 'infused_missile', 'source_damage_defense': 'physical'}),
    ('xfer', 'X-Fer', 1000, 1, 'utility', 'all_allies', (), {'v107_ability': 'party_teleport', 'soulbound_destination': 'square'}),
    ('diffuser', 'Diffuser', 1000, 8, 'utility', 'self_ally_enemy', (), {'v107_ability': 'dispel_beneficial'}),
    ('runicweapon', 'Runic Weapon', 800, 12, 'utility', 'self', ('intelligence','willpower','weapon'), {'v107_ability': 'temporary_runic', 'v107_level_effect': 'duration_and_mana_heal'}),
    ('magicitelink', 'Magicite Link', 1200, 15, 'aoe_damage', 'all_enemies', ('linked_magicite',), {'v107_ability': 'linked_summon', 'source_unique_unlock': True, 'source_mp_cost': 'varies', 'source_multicastable': True, 'source_silenceable': True, 'source_no_eidolon_echo': True}),
    ('runic', 'Runic', 400, 1, 'passive', 'counter', ('intelligence','willpower','weapon'), {'v107_ability': 'counter_magic', 'source_counter_slot': True}),
    ('esperinfusion', 'Esper Infusion', 2000, 1, 'passive', 'automatic', (), {'v107_ability': 'offense_passive'}),
    ('tekmastery', 'Tek Mastery', 5000, 12, 'passive', 'automatic', (), {'v107_ability': 'infusion_passive'}),
)

_DESC = {
    'firebeam': 'Ognisty promień: Atak + Atak Magiczny, odporność magiczna; przygotowuje ognisty TekMissile.',
    'icebeam': 'Lodowy promień: Atak + Atak Magiczny, odporność magiczna; przygotowuje lodowy TekMissile.',
    'boltbeam': 'Piorunujący promień: Atak + Atak Magiczny, odporność magiczna; przygotowuje TekMissile błyskawicą.',
    'healforce': 'Leczy siebie lub sojusznika. Moc oparta na Woli, rośnie wraz z poziomem skilla.',
    'tekshield': 'Krótka osłona Protect + Shell; wyklucza TekBarrier; rozpraszalna i przedłużalna.',
    'tekbarrier': 'Krótka osłona Protect + Reflect; wyklucza TekShield; rozpraszalna i przedłużalna.',
    'gravitybomb': 'Szansa na zmniejszenie aktualnego HP przeciwnika o połowę; skuteczność rośnie z poziomem.',
    'bioblast': 'Wszyscy przeciwnicy: obrażenia + trucizna, zależna od Woli. Bez malejącej mocy AoE.',
    'tekmissile': 'Silny pocisk bez żywiołu, odpierany obroną fizyczną. Może eksplodować energią poprzedniego ataku.',
    'xfer': 'Transportuje drużynę do centrum miasta; adaptacja Soulbound: Plac Dusz.',
    'diffuser': 'Rozprasza pozytywne efekty na sobie, sojuszniku albo przeciwniku.',
    'runicweapon': 'Na krótko daje szansę na przechwytywanie czarów i odzyskiwanie Many.',
    'magicitelink': 'Przywołanie przy użyciu powiązanego magicite. Wymaga osobnego odblokowania umiejętności.',
    'runic': 'Kontrumiejętność: czasami przechwytuje wrogie czary i odzyskuje MP.',
    'esperinfusion': 'Automatycznie zwiększa moc promieni, Bio Blast i TekMissile; wzmacnia truciznę.',
    'tekmastery': 'Automatyczna szansa na naładowanie TekMissile ogniem, lodem, piorunem lub trucizną.',
}


def skill_catalogue():
    """Fresh dicts, original AP/unlocks intact. No fabricated source MP costs."""
    rows = []
    for slug, name, ap, level, kind, target, stats, flags in _DEFINITIONS:
        row = {
            'id': 'v107_magitek_' + slug, 'name': name,
            'aliases': [slug, name.casefold(), 'mtek ' + slug],
            'unlock': level, 'kind': kind, 'mana': 0, 'cooldown': 0,
            'desc': _DESC[slug], 'source_job': SOURCE_JOB_NAME,
            'source_ap_cost': ap, 'source_ap_semantics': 'training',
            'v107_magitek_authored': True, 'v107_skill': slug,
            'source_target': target, 'source_stat_influence': stats,
            'soulbound_runtime_stage': 'experimental',
        }
        row.update(flags)
        if kind in ('damage', 'aoe_damage'):
            row.update({'scale': 'intelligence', 'secondary_scale': 'strength',
                        'mult': 1.30 if slug != 'tekmissile' else 1.80})
        if kind == 'heal':
            row['heal_pct'] = 0.18  # Soulbound scaling, source gives no percentage
        if kind == 'guard':
            row['guard'] = 18  # Placeholder in old generic engine, NOT source Protect/Shell
        if slug == 'runic':
            row['mec_role'] = 'counter'  # Reuse real Soulbound job set counter slot.
            row['aliases'].append('magitek runic')
        if slug == 'bioblast':
            row['olc_status'] = {'kind':'poison','chance':0.32}  # Soulbound adaptation
        rows.append(row)
    return rows


def install(namespace):
    """Staging-only Magitek registration AFTER all legacy 22-class audits.

    Safe on v106: no existing IDs mutated, no class/quest migration or DB write.
    """
    rows = namespace['CLASSES']
    if any(c[0] == CLASS_NAME for c in rows):
        raise RuntimeError('v107 duplicate Magitek class')
    current_ids = {skill['id'] for skills in namespace['CLASS_SKILLS'].values() for skill in skills}
    skills = skill_catalogue()
    if current_ids.intersection(s['id'] for s in skills):
        raise RuntimeError('v107 duplicate Magitek skill IDs')
    rows.append(CLASS_INFO)
    namespace['CLASS_SKILLS'][CLASS_NAME] = skills
    namespace['CLASS_STARTING_STAT_BONUSES'][CLASS_NAME] = dict(CLASS_BONUSES)
    namespace['V0876_CLASS_STARTING_STAT_BONUSES'][CLASS_NAME] = dict(CLASS_BONUSES)
    namespace['SOUL_WEAPON_ATTACK_TECHNIQUES'][CLASS_NAME] = 'Impuls Rdzenia Magiteka'
    namespace['CLASS_DESCRIPTIONS'][CLASS_NAME] = (
        'Magitek Knight UOSS zaadaptowany do Soulbound. Klasa hybrydowa: Atak + Magia, '
        'broń dystansowa skaluje Atak ze Zręczności, pozostała z Siły. '
        'Dostępna od poziomu 1 bez misji. Nauczyciel: Inżynierka Iria, Komnata Arkanów.'
    )
    from core.character_resources import AUTHORED_CLASS_PASSIVE_PROFILES
    AUTHORED_CLASS_PASSIVE_PROFILES[CLASS_NAME] = {'kind': 'all_damage', 'value': 0.0}
    return len(skills)
