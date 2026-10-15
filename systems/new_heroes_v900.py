# -*- coding: utf-8 -*-
"""Soulbound v9.00.0: additive authored class/race expansion.

Stable legacy IDs and saved character identity stay unchanged. The new class
soul weapon comes directly from the canonical class entry, never from an EQ item.
"""
NEW_CLASSES = (
    ('Paladyn','physical','Święty Miecz Duszy',7,'paladyn','Przysięgi Świtu','strength','physical_damage',.09,'holy',('Uderzenie Przysięgi','Tarcza Miłosierdzia','Świt Sprawiedliwości')),
    ('Samuraj','physical','Katana Duszy',8,'samuraj','Ostrza Honoru','dexterity','dodge',.04,'physical',('Cięcie Wschodu','Kontra Stali','Tysiąc Ostrzy')),
    ('Korsarz','physical','Szabla Duszy',7,'korsarz','Burzowego Morza','dexterity','physical_damage',.09,'water',('Cięcie Abordażowe','Salwa Korsarza','Sztorm Szabel')),
    ('Gladiator','physical','Gladius Duszy',8,'gladiator','Areny Bohaterów','strength','physical_damage',.10,'physical',('Cios Areny','Przełamanie Pancerza','Werdykt Areny')),
    ('Chronomanta','magic','Klepsydra Duszy',7,'chronomanta','Węzła Czasu','intelligence','magic_damage',.09,'arcane',('Impuls Czasu','Przyspieszenie Run','Pętla Eonów')),
    ('Iluzjonista','magic','Zwierciadło Duszy',7,'iluzjonista','Lustrzanych Snów','intelligence','dodge',.04,'arcane',('Pęknięcie Iluzji','Lustrzana Zasłona','Burza Zwierciadeł')),
    ('Bard','magic','Lutnia Duszy',7,'bard','Pieśni Wieczności','intelligence','healing',.09,'arcane',('Akord Burzy','Pieśń Odwagi','Symfonia Gwiazd')),
    ('Szaman','magic','Totem Duszy',8,'szaman','Pradawnych Duchów','intelligence','magic_damage',.10,'lightning',('Zew Duchów','Totem Burzy','Gniew Przodków')),
)
NEW_RACES = (
    ('Wampir','Nocny wędrowiec. Pasyw: +8 procent wszystkich obrażeń.',10,11,8,12,9,'all_damage',.08),
    ('Wilkołak','Drapieżnik dziczy. Pasyw: +10 procent obrażeń fizycznych.',14,11,12,6,7,'physical_damage',.10),
    ('Minotaur','Potężny obrońca. Pasyw: 10 procent redukcji obrażeń fizycznych.',15,7,14,6,8,'physical_reduction',.10),
    ('Tryton','Mieszkaniec głębin. Pasyw: +3 punkty procentowe do dodatkowego zbioru profesji.',9,10,12,9,10,'profession_bonus',.03),
    ('Feniksjanin','Dziedzic płomieni odnowy. Pasyw: +12 procent mocy leczenia.',8,10,9,12,11,'healing',.12),
    ('Dżin','Duch żywiołów. Pasyw: +15 procent maksymalnej Many.',6,10,8,15,11,'max_mana',.15),
    ('Kitsune','Lis iluzji i zręczności. Pasyw: +5 punktów procentowych uniku.',7,15,8,12,8,'dodge',.05),
    ('Kryształowiec','Żywy kryształ. Pasyw: +12 procent obrony magicznej.',8,7,15,10,10,'magic_defense',.12),
)
CLASS_BONUSES = {
    'Paladyn':(3,1,3,0,2,0),'Samuraj':(2,4,2,0,1,0),
    'Korsarz':(2,4,1,1,1,0),'Gladiator':(4,2,3,0,0,0),
    'Chronomanta':(0,1,1,4,3,0),'Iluzjonista':(0,2,1,4,2,0),
    'Bard':(0,1,1,3,4,0),'Szaman':(0,1,2,3,3,0),
}
RACE_RECOMMENDATIONS = {
    'Wampir':('Czarownik','Nekromanta','Iluzjonista'),
    'Wilkołak':('Berserker','Łowca','Samuraj'),
    'Minotaur':('Strażnik','Gladiator','Paladyn'),
    'Tryton':('Korsarz','Szaman','Druid'),
    'Feniksjanin':('Paladyn','Kapłan','Bard'),
    'Dżin':('Mag','Chronomanta','Szaman'),
    'Kitsune':('Łotrzyk','Iluzjonista','Samuraj'),
    'Kryształowiec':('Strażnik','Psionik','Chronomanta'),
}
# The existing supported Soul Weapon effects, never a fallback to Wojownik.
_SOUL_EFFECTS = (
 ('damage_percent',1.08),('crit_chance',.0045),
 ('boss_damage_percent',1.12),('crit_damage_percent',2.95),
 ('execute_damage_percent',1.22),('lifesteal_percent',.40),
 ('mana_restore_percent',.50),
)
SOUL_TRAITS = {
 name:{'theme':theme,'cycle':tuple(_SOUL_EFFECTS[(i+j)%len(_SOUL_EFFECTS)] for j in range(5))}
 for i,(name,_,_,_,_,theme,*_) in enumerate(NEW_CLASSES)
}
EQUIPMENT = {
    name:{'prefix':'v900_'+slug,'set_name':theme,'affix':'intelligence' if kind=='magic' else scale,
          'base_defense':1 if kind=='magic' else 2,
          'room': 'guild_arcane_chamber' if kind=='magic' else 'guild_martial_hall',
          'styles':(theme,'Mistrza '+theme,'Arcymistrza '+theme),
          'primary_ratio':(.69 if kind=='magic' else .62),
          'properties':({'magic_damage_pct':.55+.05*(i%4),'max_mana_pct':.45-.05*(i%4)} if kind=='magic'
                        else {'physical_damage_pct':.55+.05*(i%4),'physical_defense_pct':.45-.05*(i%4)})}
    for i,(name,kind,_,_,slug,theme,scale,*_) in enumerate(NEW_CLASSES)
}

def class_skills(class_info, mastery_levels, mastery_titles):
    """Three usable, distinct abilities at every class mastery threshold 1..800.

    Eleven original signature actions retain their IDs.  Alternative abilities
    are genuine spells/attacks/defences rather than empty catalogue entries.
    The historical 3-per-tier contract remains valid for new as well as old
    classes.  No ordinary cooldown is added to the new class abilities.
    """
    name, kind, weapon, power, slug, theme, scale, passive, value, element, titles = class_info
    magic = kind == 'magic'
    signature_levels = (1, 10, 20, 40, 60, 100, 200, 350, 500, 700, 800)
    signature_actions = ('damage', 'damage', 'boost', 'aoe_damage', 'guard', 'execute',
                         'damage', 'aoe_damage', 'execute', 'aoe_damage', 'damage')
    if name in ('Paladyn', 'Bard', 'Szaman'):
        signature_actions = ('damage', 'heal', 'boost', 'aoe_damage', 'guard', 'execute',
                             'heal', 'aoe_damage', 'execute', 'aoe_damage', 'damage')
    if name in ('Samuraj', 'Iluzjonista'):
        signature_actions = ('damage', 'damage', 'evade', 'aoe_damage', 'guard', 'execute',
                             'damage', 'aoe_damage', 'execute', 'aoe_damage', 'damage')
    variants = {
        'Paladyn': ('damage', 'guard', 'heal'),
        'Samuraj': ('damage', 'evade', 'execute'),
        'Korsarz': ('damage', 'aoe_damage', 'boost'),
        'Gladiator': ('execute', 'guard', 'aoe_damage'),
        'Chronomanta': ('damage', 'boost', 'aoe_damage'),
        'Iluzjonista': ('damage', 'evade', 'aoe_damage'),
        'Bard': ('damage', 'group_heal', 'boost'),
        'Szaman': ('damage', 'heal', 'aoe_damage'),
    }[name]
    assert len(mastery_levels) == len(mastery_titles) == 81
    signature = dict(zip(signature_levels, signature_actions))
    rows = []
    for idx, level in enumerate(mastery_levels):
        epithet = str(mastery_titles[idx])
        main_kind = signature.get(level)
        for variant_idx in range(3):
            ability = main_kind if (variant_idx == 0 and main_kind) else variants[variant_idx]
            title = titles[variant_idx]
            if main_kind and variant_idx == 0 and level in (1, 10, 20):
                display_name = titles[(1, 10, 20).index(level)]
            else:
                display_name = f'{title}: {epithet}'
            skill_id = (f'v900_{slug}_{level}' if main_kind and variant_idx == 0
                        else f'v900_{slug}_mastery_{level}_{variant_idx + 1}')
            row = {
                'id': skill_id, 'name': display_name,
                'aliases': [display_name.lower()],
                'natural_tags': [slug, element, 'legenda'],
                'unlock': int(level), 'kind': ability, 'cooldown': 0,
                'mana': (max(4, 8 + int(level) // 12) if magic else 0),
                'mastery_choice_group': f'{name}:{int(level)}',
                'desc': (f'{name}: {display_name}. Biegłość {level}. '
                         f'Broń Duszy: {weapon}.')
            }
            progression = float(level) / 800.0
            if ability in ('damage', 'aoe_damage', 'execute', 'drain'):
                row.update({'scale': scale,
                            'mult': round(1.20 + 3.45 * progression + variant_idx * .07, 2)})
            if ability == 'execute':
                row['execute_mult'] = round(1.55 + .55 * progression, 2)
            if ability == 'drain':
                row['drain_pct'] = round(.20 + .19 * progression, 3)
            if ability in ('heal', 'group_heal'):
                row['heal_pct'] = round(.14 + .33 * progression, 3)
            if ability == 'boost':
                row.update({'boost': round(1.25 + .55 * progression, 3), 'duration': 14})
            if ability == 'guard':
                row['guard'] = 18 + int(level * .35)
            if ability == 'evade':
                row['duration'] = 12
            rows.append(row)
    assert len(rows) == len(mastery_levels) * 3
    return rows


def register_classes(namespace):
    from core.character_resources import AUTHORED_CLASS_PASSIVE_PROFILES, AUTHORED_RACE_PASSIVE_PROFILES
    race_roster=namespace['RACES'];class_roster=namespace['CLASSES']
    for name,description,strength,dexterity,constitution,intelligence,willpower,p_kind,p_value in NEW_RACES:
        if name in {row[0] for row in race_roster}:raise RuntimeError('duplicate race '+name)
        assert sum((strength,dexterity,constitution,intelligence,willpower))==50
        race_roster.append((name,description,strength,dexterity,constitution,intelligence,willpower))
        AUTHORED_RACE_PASSIVE_PROFILES[name]={'kind':p_kind,'value':p_value}
        namespace['RACE_CLASS_RECOMMENDATIONS'][name]={
            'classes':list(RACE_RECOMMENDATIONS[name]),'reason':description}
    for entry in NEW_CLASSES:
        name,kind,weapon,power,slug,theme,scale,passive,value,element,titles=entry
        if name in {row[0] for row in class_roster}:raise RuntimeError('duplicate class '+name)
        class_roster.append((name,kind,weapon,power))
        namespace['SOUL_WEAPON_ATTACK_TECHNIQUES'][name]=titles[0]
        attrs=CLASS_BONUSES[name]
        namespace['CLASS_STARTING_STAT_BONUSES'][name]=dict(zip(
            ('strength','dexterity','constitution','intelligence','willpower','charisma'),attrs))
        namespace['V0876_CLASS_STARTING_STAT_BONUSES'][name]=dict(namespace['CLASS_STARTING_STAT_BONUSES'][name])
        namespace['CLASS_DESCRIPTIONS'][name]=(
            f'Klasa {"magiczna" if kind=="magic" else "fizyczna"}. '
            f'Własna Broń Duszy: {weapon}. {theme}. '
            'Jedna klasa na postać. '+
            f'Pasyw: {int(value*100)} procent w kategorii {passive}.')
        AUTHORED_CLASS_PASSIVE_PROFILES[name]={'kind':passive,'value':value}
        namespace['CLASS_SKILLS'][name]=class_skills(entry, namespace['_V0922_MASTERY_LEVELS'], namespace['_V03014_SKILL_TITLES'])
    # Sets and traits are registered before their existing engines materialize.
    assert len(race_roster)==len(class_roster)==22
