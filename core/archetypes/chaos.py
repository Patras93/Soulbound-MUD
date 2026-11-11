# -*- coding: utf-8 -*-
"""v107: seven original, playable classes, eight races and eight profession identities.

Installed only after old historical 14/22 class audit. Never touches character rows.
Skills use the existing native combat engine; all coefficients are Soulbound-authored.
"""
from __future__ import annotations

CLASS_SPECS = (
 ('Chronotechnik','magic','Zegar Duszy','intelligence','magic_damage',.10, ('Pęknięcie Sekundy','Fala Eonów','Zatrzymanie Czasu')),
 ('Runiczny Obrońca','physical','Tarcza Run','constitution','damage_reduction',.10, ('Cięcie Runiczne','Fala Straży','Pieczęć Ocalenia')),
 ('Władca Burz','magic','Berło Gromu','intelligence','magic_damage',.12, ('Piorun Burzy','Gniew Niebios','Oko Cyklonu')),
 ('Łowca Anomalii','physical','Ostrze Tropiciela','dexterity','dodge',.05, ('Cios Zakłócenia','Polowanie na Cienie','Przeskok Wymiaru')),
 ('Tkacz Dusz','magic','Nić Dusz','willpower','healing',.12, ('Szpon Echa','Fala Wspomnień','Splot Ocalenia')),
 ('Alchemik Bitewny','magic','Kolba Ognia','intelligence','all_damage',.07, ('Wybuch Destylatu','Toksyczna Chmura','Osłona Reakcji')),
 ('Wędrowiec Pustki','physical','Szabla Próżni','dexterity','physical_damage',.10, ('Rozcięcie Pustki','Fala Bezczasowa','Zasłona Mroku')),
)
# Five-stat allocation ALWAYS sums to 50, preserving six-stat/charyzma convention.
RACE_SPECS = (
 ('Astralici','magic_damage',.08,(8,9,9,14,10)),
 ('Runokrwiści','physical_damage',.08,(12,9,11,8,10)),
 ('Mgłowcy','dodge',.04,(8,13,8,10,11)),
 ('Kryształowcy','magic_defense',.10,(8,8,12,11,11)),
 ('Popielni','physical_reduction',.08,(12,8,11,9,10)),
 ('Pustkowcy','all_damage',.06,(10,11,9,10,10)),
 ('Luminarzy','healing',.10,(8,9,10,12,11)),
 ('Eterianie','max_mana',.10,(8,11,8,13,10)),
)
PROFESSION_SPECS = (
 ('Runotechnika','runotech','Rylce Runiczne','v10700_chaos_rozdarcie_material_1'),
 ('Biometalurgia','biometal','Skalpel Biometalu','v10700_chaos_mechaniczne_korzenie_material_2'),
 ('Chronometria','chronometr','Zegar Warsztatowy','v10700_chaos_pekniete_zegary_material_1'),
 ('Kryształotechnika','kryształotechnika','Szczypce Kryształowe','v10700_chaos_gory_eteru_material_1'),
 ('Esencjologia','esencjologia','Ekstraktor Esencji','v10700_chaos_morze_wspomnien_material_2'),
 ('Relikwiarstwo','relikwiarstwo','Rylec Relikwii','v10700_chaos_rozproszona_dusza_material_3'),
 ('Astralna Nawigacja','astralnav','Astrolabium','v10700_chaos_mosty_konstelacji_material_1'),
 ('Pieczęciarstwo','pieczeciarstwo','Prasa Pieczęci','v10700_chaos_rozdarcie_material_4'),
)


def _skills(name, slug, stat, magical, label):
    root='v10700_'+slug+'_'
    # One distinct single-target, AoE, special execution, defense, offensive buff,
    # recovery ability and a stronger late single-target attack.
    cost=30 if magical else 0
    return [
       dict(id=root+'strike',name=label[0],aliases=[slug+' cios'],unlock=1,
         kind='damage',cooldown=4,mana=cost,scale=stat,mult=1.40,
         desc=f'{name}: szybki atak, skala {stat}.'),
       dict(id=root+'wave',name=label[1],aliases=[slug+' fala'],unlock=10,
         kind='aoe_damage',cooldown=10,mana=cost+20,scale=stat,mult=1.16,
         desc=f'{name}: uderzenie w całe pomieszczenie.'),
       dict(id=root+'execute',name='Werdykt '+name,aliases=[slug+' werdykt'],unlock=35,
         kind='execute',cooldown=14,mana=cost+35,scale=stat,mult=1.50,execute_mult=1.70,
         desc='Wzmocniony cios przeciw osłabionemu wrogowi.'),
       dict(id=root+'guard',name=label[2],aliases=[slug+' osłona'],unlock=22,
         kind='guard',cooldown=18,mana=cost,guard=22,
         desc=f'{name}: osłona ograniczająca następne trafienie.'),
       dict(id=root+'boost',name='Przebudzenie '+name,aliases=[slug+' moc'],unlock=75,
         kind='boost',cooldown=28,mana=cost+25,boost=1.30,duration=12,
         desc='Krótki wzrost mocy umiejętności.'),
       dict(id=root+'recovery',name='Odnowa '+name,aliases=[slug+' odnowa'],unlock=110,
         kind='heal',cooldown=24,mana=cost+30,heal_pct=.18,
         desc='Leczenie własnych ran.'),
       dict(id=root+'mastery',name='Mistrzostwo '+name,aliases=[slug+' mistrzostwo'],unlock=200,
         kind='damage',cooldown=18,mana=cost+80,scale=stat,mult=2.10,
         desc='Potężny atak mistrzowski.'),
    ]


def install(namespace):
    from core.character_resources import (AUTHORED_CLASS_PASSIVE_PROFILES,
                                          AUTHORED_RACE_PASSIVE_PROFILES)
    from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP, PROFESSION_RANK_NAMES
    from systems.profession_mastery_v2200 import SPECIALTIES
    from world.legends_v3100 import OPPOSITE
    assert len(OPPOSITE)==10 and all(OPPOSITE.get(v)==k for k,v in OPPOSITE.items())  # all 10 direction pairs
    classes=namespace['CLASSES']; races=namespace['RACES']
    class_names={row[0] for row in classes}; race_names={row[0] for row in races}
    if any(row[0] in class_names for row in CLASS_SPECS):
        raise RuntimeError('v107 klasy: ponowna lub częściowa instalacja')
    if any(row[0] in race_names for row in RACE_SPECS):
        raise RuntimeError('v107 rasy: ponowna lub częściowa instalacja')
    if any(row[0] in TOOL_PROFESSION_MAP.values() for row in PROFESSION_SPECS):
        raise RuntimeError('v107 profesje: kolizja')
    for name,mode,weapon,stat,passive,value,labels in CLASS_SPECS:
        slug=str(name).lower().replace('ł','l').replace(' ','_')
        classes.append((name,mode,weapon,7))
        namespace['CLASS_SKILLS'][name]=_skills(name,slug,stat,mode=='magic',labels)
        namespace['CLASS_STARTING_STAT_BONUSES'][name]={
            'strength':1,'dexterity':2,'constitution':1,'intelligence':2,'willpower':2,'charisma':0}
        namespace['V0876_CLASS_STARTING_STAT_BONUSES'][name]=dict(namespace['CLASS_STARTING_STAT_BONUSES'][name])
        namespace['SOUL_WEAPON_ATTACK_TECHNIQUES'][name]=labels[0]
        namespace['CLASS_DESCRIPTIONS'][name]=(f'{name}. Nowa klasa Chaosu v107. '
           f'7 autorskich umiejętności z poziomami 1–200. Pasyw: {passive} {int(value*100)}%.')
        AUTHORED_CLASS_PASSIVE_PROFILES[name]={'kind':passive,'value':value}
    for name,kind,value,stats in RACE_SPECS:
        assert sum(stats)==50
        races.append((name,f'Rasa Chaosu. Pasyw {kind}: {int(value*100)} procent.',*stats))
        namespace['RACE_CLASS_RECOMMENDATIONS'][name]={
            'classes':[CLASS_SPECS[(len(races)-1)%len(CLASS_SPECS)][0]],
            'reason':'statystyki pomagają rozwijać klasę, wybór pozostałych klas pozostaje wolny'}
        AUTHORED_RACE_PASSIVE_PROFILES[name]={'kind':kind,'value':value}
    for name,tool,label,material in PROFESSION_SPECS:
        TOOL_PROFESSION_MAP[tool]=name
        PROFESSION_RANK_NAMES[name]=tuple(f'{rank} {name}' for rank in (
            'Uczeń','Adept','Czeladnik','Mistrz','Arcymistrz','Legenda','Astralny','Wieczny'))
        SPECIALTIES[name]=(f'Mistrz {name}',f'Arcymistrz {name}',f'Legenda {name}')
    return dict(classes=len(CLASS_SPECS),races=len(RACE_SPECS),professions=len(PROFESSION_SPECS),skills=len(CLASS_SPECS)*7)
