# -*- coding: utf-8 -*-
"""v110: izolowane definicje klas, ras i profesji; wspólny atomowy kontrakt.

Brak skanowania globali i podmiany historycznych metod. Przed modyfikacją
katalogów pełna walidacja kolizji, statystyk, umiejętności i narzędzi.
"""
from __future__ import annotations
from core.archetypes_v110.classes.wirtuoz_echa import SPEC as C0
from core.archetypes_v110.classes.fantomowy_szermierz import SPEC as C1
from core.archetypes_v110.classes.szeptacz_bestii import SPEC as C2
from core.archetypes_v110.classes.paladyn_zmierzchu import SPEC as C3
from core.archetypes_v110.classes.kartograf_przestrzeni import SPEC as C4
from core.archetypes_v110.classes.straznik_przypywow import SPEC as C5
from core.archetypes_v110.classes.egzekutor_pieczeci import SPEC as C6
from core.archetypes_v110.classes.zarowy_zniwiarz import SPEC as C7
from core.archetypes_v110.races.rezonanci import SPEC as R0
from core.archetypes_v110.races.lustrzanie import SPEC as R1
from core.archetypes_v110.races.zarodnikowcy import SPEC as R2
from core.archetypes_v110.races.zaranie import SPEC as R3
from core.archetypes_v110.races.selenici import SPEC as R4
from core.archetypes_v110.races.gebinowcy import SPEC as R5
from core.archetypes_v110.races.miedzianie import SPEC as R6
from core.archetypes_v110.races.zarborny import SPEC as R7
from core.archetypes_v110.professions.alchemia_dzwieku import SPEC as P0
from core.archetypes_v110.professions.zwierciadlarstwo import SPEC as P1
from core.archetypes_v110.professions.paleoekologia import SPEC as P2
from core.archetypes_v110.professions.fitoarchitektura import SPEC as P3
from core.archetypes_v110.professions.hydrokartografia import SPEC as P4
from core.archetypes_v110.professions.technometeorologia import SPEC as P5
from core.archetypes_v110.professions.kronikarstwo_materii import SPEC as P6
from core.archetypes_v110.professions.burzotronika import SPEC as P7

CLASS_SPECS = (C0,C1,C2,C3,C4,C5,C6,C7,)
RACE_SPECS = (R0,R1,R2,R3,R4,R5,R6,R7,)
PROFESSION_SPECS = (P0,P1,P2,P3,P4,P5,P6,P7,)


def _skills(name, tag, stat, magical, labels):
    mana = 35 if magical else 0
    base = 'v11000_' + tag + '_'
    def skill(index, label, kind, unlock, cooldown, mult=1.0, **extra):
        d = dict(id=base+index, name=label, aliases=[tag+' '+index],
                 unlock=unlock, kind=kind, cooldown=cooldown, mana=mana+max(0,unlock//50),
                 scale=stat, mult=mult, desc=name+': '+label+'.')
        d.update(extra)
        return d
    return [
        skill('strike',labels[0],'damage',1,4,1.40),
        skill('wave',labels[1],'aoe_damage',10,10,1.17),
        skill('execute','Werdykt '+name,'execute',35,14,1.50,execute_mult=1.65),
        skill('guard',labels[2],'guard',22,18,guard=21),
        skill('boost','Przebudzenie '+name,'boost',75,28,boost=1.28,duration=12),
        skill('heal','Odnowa '+name,'heal',110,24,heal_pct=.17),
        skill('mastery','Mistrzostwo '+name,'damage',200,18,2.06),
        skill('counter','Kontruderzenie '+name,'damage',350,19,2.15),
        skill('storm','Burza '+name,'aoe_damage',600,25,1.46),
        skill('legacy','Dziedzictwo '+name,'damage',1000,32,2.55),
    ]


def validate(namespace, professions, ranks, specialties, classpassives, racepassives):
    assert len(CLASS_SPECS)==len(RACE_SPECS)==len(PROFESSION_SPECS)==8
    names=([r[0] for r in CLASS_SPECS], [r[0] for r in RACE_SPECS],
           [r[0] for r in PROFESSION_SPECS])
    for label,rows in zip(('klasy','rasy','profesje'),names):
        if len(rows)!=len(set(rows)):
            raise ValueError('v110: zduplikowane '+label)
    existing_classes={row[0] for row in namespace['CLASSES']}
    existing_races={row[0] for row in namespace['RACES']}
    existing_professions=set(professions.values())
    for label,old,new in (("klasy",existing_classes,names[0]),
                          ("rasy",existing_races,names[1]),
                          ("profesje",existing_professions,names[2])):
        overlap=set(new)&old
        if overlap:raise ValueError('v110: kolizja '+label+' '+min(overlap))
    if any(tool in professions for _,tool,*_ in PROFESSION_SPECS):
        raise ValueError('v110: zajęte identyfikatory narzędzi')
    if any(name in ranks or name in specialties for name in names[2]):
        raise ValueError('v110: istniejące profile profesji')
    if any(name in classpassives for name in names[0]):
        raise ValueError('v110: zajęte pasywy klas')
    if any(name in racepassives for name in names[1]):
        raise ValueError('v110: zajęte pasywy ras')
    for name,kind,value,stats in RACE_SPECS:
        if len(stats)!=5 or sum(stats)!=50 or min(stats)<1 or not 0<value<.2:
            raise ValueError('v110: błędne statystyki rasy '+name)
    ids=set();skillnames=set()
    for name,mode,weapon,stat,passive,value,*labels in CLASS_SPECS:
        if mode not in ('magic','physical') or len(labels)!=3 or not 0<value<.2:
            raise ValueError('v110: błędna klasa '+name)
        tag = name.casefold().translate(str.maketrans('ąćęłńóśźż','acelnoszz')).replace(' ','_')
        sk = _skills(name,tag,stat,mode=='magic',labels)
        if len(sk)!=10 or any(s['id'] in ids or s['name'] in skillnames for s in sk):
            raise ValueError('v110: duplikat umiejętności '+name)
        ids.update(s['id'] for s in sk);skillnames.update(s['name'] for s in sk)
    return True


def install(namespace):
    """Install after v107 originals; no DB writes; collisions checked before changes."""
    from core.character_resources import (AUTHORED_CLASS_PASSIVE_PROFILES as cp,
                                          AUTHORED_RACE_PASSIVE_PROFILES as rp)
    from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP as prof, PROFESSION_RANK_NAMES as ranks
    from systems.profession_mastery_v2200 import SPECIALTIES as specials
    from core.profession_timing import TOOL_ACTION_BASE_SECONDS, TOOL_ACTION_MIN_SECONDS
    from core.archetypes_v110.profession_timing_v110 import register_timing
    validate(namespace,prof,ranks,specials,cp,rp)
    # All checks before global registry writes; old authored times remain untouched.
    # Timings belong to an independent v110 module instead of modifying v1.13.16.
    register_timing(PROFESSION_SPECS, TOOL_ACTION_BASE_SECONDS, TOOL_ACTION_MIN_SECONDS)
    # Build new rows and skills before writing any shared registry.
    class_rows=[];race_rows=[];skills={};passives_c={};passives_r={}
    classbonuses={};descriptions={};soulweapons={};recommendations={}
    for name,mode,weapon,stat,passive,value,*labels in CLASS_SPECS:
        tag=name.casefold().translate(str.maketrans('ąćęłńóśźż','acelnoszz')).replace(' ','_')
        class_rows.append((name,mode,weapon,7))
        skills[name]=_skills(name,tag,stat,mode=='magic',labels)
        # New classes must match the v0.9.0 authored 9-point starting budget.
        classbonuses[name]={'strength':1,'dexterity':2,'constitution':1,
                            'intelligence':2,'willpower':3,'charisma':0}
        descriptions[name]=name+'. 10 autorskich umiejętności 1–1000. Pasyw: '+passive+'.'
        passives_c[name]={'kind':passive,'value':value}
        soulweapons[name]=labels[0]
    for name,kind,value,stats in RACE_SPECS:
        race_rows.append((name,'Rasa v110. Pasyw '+kind+'.',*stats))
        passives_r[name]={'kind':kind,'value':value}
        recommendations[name]={'classes':[], 'reason':'Rasa dostępna dla wszystkich klas.'}
    namespace['CLASSES'].extend(class_rows)
    namespace['RACES'].extend(race_rows)
    namespace['CLASS_SKILLS'].update(skills)
    namespace['CLASS_STARTING_STAT_BONUSES'].update(classbonuses)
    namespace['V0876_CLASS_STARTING_STAT_BONUSES'].update(
        {key:dict(value) for key,value in classbonuses.items()})
    namespace['SOUL_WEAPON_ATTACK_TECHNIQUES'].update(soulweapons)
    namespace['CLASS_DESCRIPTIONS'].update(descriptions)
    namespace['RACE_CLASS_RECOMMENDATIONS'].update(recommendations)
    cp.update(passives_c);rp.update(passives_r)
    for name,tool,label,material in PROFESSION_SPECS:
        prof[tool]=name
        ranks[name]=tuple(rank+' '+name for rank in ('Uczeń','Adept','Czeladnik','Mistrz',
                         'Arcymistrz','Legenda','Astralny','Wieczny'))
        specials[name]=('Mistrz '+name,'Arcymistrz '+name,'Legenda '+name)
    return dict(classes=8,races=8,professions=8,skills=80)
