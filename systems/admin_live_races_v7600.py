# -*- coding: utf-8 -*-
"""v76: playable, persistent additive races using existing balanced passives.

No class/skill injection, no code execution, no DB migrations. Races are appended
in-place to the authoritative character-creator catalog after base heritage loads.
Deleting a race which has a saved character is forbidden.
"""
from __future__ import annotations

import copy
import json
import os
import re
import tempfile
from pathlib import Path

from core.classes_skills import RACES, RACE_CLASS_RECOMMENDATIONS
from core.character_resources import (AUTHORED_RACE_PASSIVE_PROFILES,
                                      race_passive_text_pl, passive_text_pl)
from systems.custom_passives_v9500 import parse_profile, validate_profile

CONFIG_PATH=Path(__file__).resolve().parent.parent/'LIVE_CONTENT'/'custom_races_v7600.json'
_ORIGINAL_RACES=None
_ORIGINAL_PASSIVES=None
_ORIGINAL_RECOMMENDATIONS=None
_SETTINGS=None
_MAX_NEW_RACES=32
_NAME=re.compile(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9 -]{1,27}\Z")
HELP=('ADMIN LIVE POMOC 36: rodowod nowa rasa lista; rodowod nowa rasa karta NAZWA; '
      'rodowod nowa rasa plan NAZWA | RASA_BAZOWA | SILA ZRE KON INT WOLA [| RODZAJ_PASYWU | PROCENT]; '
      'rodowod nowa rasa zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
      'Tworzy NOWA grywalna rase w kreatorze; 50 punktow statystyk, '
      'pasyw dziedziczony lub wlasna moc istniejacego rodzaju (limit sprawdzonego archetypu); maks. 32. '
      'Bez zmiany statystyk istniejacych postaci. Usuwanie tylko przez '
      'cofnij i tylko jesli nikt nie utworzyl postaci tej rasy. '
      'Nie dodaje nowych rodzajow pasywow ani skryptow.')


def _ensure_base():
    global _ORIGINAL_RACES,_ORIGINAL_PASSIVES,_ORIGINAL_RECOMMENDATIONS
    if _ORIGINAL_RACES is None:
        _ORIGINAL_RACES=tuple(copy.deepcopy(RACES))
        _ORIGINAL_PASSIVES=copy.deepcopy(AUTHORED_RACE_PASSIVE_PROFILES)
        _ORIGINAL_RECOMMENDATIONS=copy.deepcopy(RACE_CLASS_RECOMMENDATIONS)
    return _ORIGINAL_RACES


def _validated(rows):
    if type(rows) is not dict or len(rows)>_MAX_NEW_RACES:
        raise ValueError('Maksymalnie 32 nowe rasy w slowniku.')
    bases={row[0].casefold():row[0] for row in _ensure_base()}
    used=set(bases)
    result={}
    for name,setting in rows.items():
        if not isinstance(name,str) or not _NAME.fullmatch(name) or name.strip()!=name:
            raise ValueError('Nazwa rasy: 2-28 liter/cyfr/spacji/minusow, bez znakow sterujacych.')
        if name.casefold() in used:
            raise ValueError('Powtarzajaca sie nazwa rasy lub kolizja z oryginalna.')
        used.add(name.casefold())
        if type(setting) is not dict or not {'parent','stats'} <= set(setting) or set(setting)-{'parent','stats','passive_override'}:
            raise ValueError('Rasa musi posiadac parent oraz stats.')
        parent=setting['parent']; stats=setting['stats']
        if not isinstance(parent,str) or parent.casefold() not in bases:
            raise ValueError('Pasyw musi pochodzic z istniejacej rasy bazowej.')
        if type(stats) is not list or len(stats)!=5 or any(type(x) is not int or not 1<=x<=30 for x in stats) or sum(stats)!=50:
            raise ValueError('Wymagane 5 statystyk 1..30 o sumie dokladnie 50.')
        result[name]={'parent':bases[parent.casefold()], 'stats':list(stats)}
        if 'passive_override' in setting:result[name]['passive_override']=validate_profile(setting['passive_override'])
    return result


def current():
    global _SETTINGS
    if _SETTINGS is None:
        if CONFIG_PATH.is_file():
            raw=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            if type(raw) is not dict or set(raw)!={'schema','races'} or raw['schema']!=1:
                raise ValueError('Niepoprawny plik custom_races_v7600.json.')
            _SETTINGS=_validated(raw['races'])
        else:
            _SETTINGS={}
    return copy.deepcopy(_SETTINGS)


def _apply(rows):
    rows=_validated(rows)
    base=_ensure_base()
    existing={row[0] for row in base}
    expected=existing|set(current() if _SETTINGS is not None else {})
    if not all(row[0] in expected for row in RACES):
        raise ValueError('Nieznane dodatkowe rasy w katalogu; odmowa nadpisania.')
    # Preserve the identity of RACES imported throughout the server.
    RACES[:]=list(copy.deepcopy(base)) + [
        (name,'Nowa rasa. Pasyw: '+(passive_text_pl(**row['passive_override']) if 'passive_override' in row else race_passive_text_pl(row['parent']))+'.', *row['stats'])
        for name,row in rows.items()
    ]
    AUTHORED_RACE_PASSIVE_PROFILES.clear()
    AUTHORED_RACE_PASSIVE_PROFILES.update(copy.deepcopy(_ORIGINAL_PASSIVES))
    RACE_CLASS_RECOMMENDATIONS.clear()
    RACE_CLASS_RECOMMENDATIONS.update(copy.deepcopy(_ORIGINAL_RECOMMENDATIONS))
    for name,row in rows.items():
        AUTHORED_RACE_PASSIVE_PROFILES[name]=copy.deepcopy(row.get('passive_override',_ORIGINAL_PASSIVES[row['parent']]))
        RACE_CLASS_RECOMMENDATIONS[name]=copy.deepcopy(_ORIGINAL_RECOMMENDATIONS[row['parent']])


def restore():
    _apply(current())


def rebase_after_heritage():
    """Rebuild additive races after a validated edit to original race budgets."""
    global _ORIGINAL_RACES
    _ORIGINAL_RACES=tuple(copy.deepcopy(RACES))
    _apply(current())


def _save(rows):
    global _SETTINGS
    rows=_validated(rows)
    original=current()
    folder=CONFIG_PATH.parent
    folder.mkdir(parents=True,exist_ok=True)
    payload=json.dumps({'schema':1,'races':rows},ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    fd,temp_path=tempfile.mkstemp(prefix='.custom_races_',suffix='.tmp',dir=str(folder))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            stream.write(payload);stream.flush();os.fsync(stream.fileno())
        # Preserve old runtime on write failure. This catalog operation cannot
        # fail if preflight validation passed and no external code changed it.
        _apply(rows)
        try:
            os.replace(temp_path,CONFIG_PATH)
        except OSError:
            _apply(original)
            raise
        _SETTINGS=copy.deepcopy(rows)
    finally:
        if os.path.exists(temp_path):os.unlink(temp_path)


def _plan(session,value):
    session.adminlive7600_race_plan=None
    pieces=[part.strip() for part in value.split('|')]
    if len(pieces) not in (3,5):
        raise ValueError('rodowod nowa rasa plan NAZWA | BAZA | SILA ZRE KON INT WOLA [| PASYW | PROCENT]')
    name,parent,raw_stats=pieces[:3]
    stats_str=raw_stats.split()
    if len(stats_str)!=5 or any(not s.isascii() or not s.isdecimal() or len(s)>2 for s in stats_str):
        raise ValueError('Podaj dokladnie 5 liczb od 1 do 30.')
    before=current()
    if any(n.casefold()==name.casefold() for n in before):
        raise ValueError('Rasa juz istnieje; tworzenie nowych ras nie edytuje zapisanych archetypow.')
    after=copy.deepcopy(before)
    after[name]={'parent':parent,'stats':[int(s) for s in stats_str]}
    if len(pieces)==5:after[name]['passive_override']=parse_profile(pieces[3],pieces[4])
    after=_validated(after)
    if before==after:raise ValueError('Brak zmian.')
    session.adminlive7600_race_plan=(before,after,name)
    return (f'NOWA RASA PLAN {name}: pasyw {after[name].get("passive_override",parent)}, statystyki {stats_str}, suma 50. '
            'Bez zapisu. rodowod nowa rasa zatwierdz POTWIERDZAM.')


def _commit(session):
    data=getattr(session,'adminlive7600_race_plan',None)
    if not data:raise ValueError('Nie przygotowano planu.')
    before,after,name=data
    if current()!=before:
        session.adminlive7600_race_plan=None
        raise ValueError('Rasy zmieniono od czasu utworzenia planu.')
    _save(after)
    session.adminlive7600_race_undo=(before,after,name)
    session.adminlive7600_race_plan=None
    return f'NOWA RASA ZAPISANA {name}: dostepna przy tworzeniu postaci. Bez zmian istniejacych graczy.'


def _undo(session):
    data=getattr(session,'adminlive7600_race_undo',None)
    if not data:raise ValueError('Brak ostatniej nowej rasy do cofniecia.')
    before,after,name=data
    if current()!=after:raise ValueError('Rasy byly zmieniane; cofniecie zablokowane.')
    # Prevent orphaned class/race identities in permanent save data.
    conn=session.server.db.conn
    row=conn.execute('SELECT 1 FROM characters WHERE race=? COLLATE NOCASE LIMIT 1',(name,)).fetchone()
    if row:raise ValueError('Rasa jest uzywana przez zapisana postac; nie mozna jej usunac.')
    _save(before)
    session.adminlive7600_race_undo=None
    return f'NOWA RASA COFNIETA {name}. Zaden zapis postaci nie zostal zmieniony.'


async def dispatch_v7600(session,group,raw):
    words=str(raw or '').strip().split()
    matched=(group=='pomoc' and words==['36']) or (group=='rodowod' and words[:2]==['nowa','rasa'])
    if not matched:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':out=HELP
        elif len(words)==3 and words[2]=='lista':
            saved=current()
            out='NOWE RASY '+str(len(saved))+': '+(', '.join(saved) if saved else 'BRAK')
        elif len(words)>=4 and words[2]=='karta':
            name=str(raw).split('karta',1)[1].strip()
            saved=current()
            if name not in saved:raise ValueError('Nie ma takiej nowej rasy.')
            spec=saved[name]
            out=f'NOWA RASA {name}: bazowa {spec["parent"]}; statystyki {spec["stats"]}; pasyw {race_passive_text_pl(name)}.'
        elif len(words)>=4 and words[2]=='plan':
            out=_plan(session,str(raw).split('plan',1)[1].strip())
        elif words==['nowa','rasa','zatwierdz','POTWIERDZAM']:
            out=_commit(session)
        elif words==['nowa','rasa','cofnij','POTWIERDZAM']:
            out=_undo(session)
        elif words==['nowa','rasa','anuluj']:
            session.adminlive7600_race_plan=None
            out='NOWA RASA: plan anulowano.'
        else:raise ValueError('rodowod nowa rasa lista/karta/plan/zatwierdz/cofnij/anuluj. Pomoc 36.')
    except (ValueError,TypeError,KeyError,AttributeError,OSError,json.JSONDecodeError) as exc:
        out='ADMIN LIVE NOWE RASY: '+str(exc)[:260]
    await session.send(out)
    return True
