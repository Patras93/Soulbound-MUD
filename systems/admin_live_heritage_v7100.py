# -*- coding: utf-8 -*-
"""v71: conservative persisted edits to EXISTING starting race budgets and class weapon names.

No new race passive or new combat class is invented. In-place list updates keep
imports used by the character creator stable. Existing characters are untouched.
"""
from __future__ import annotations
import copy
import json
import os
import tempfile
from pathlib import Path

CONFIG_PATH=Path(__file__).resolve().parent.parent/'LIVE_CONTENT'/'heritage_v7100.json'
_SETTINGS=None
_BASE_REGISTRY=None

HELP=('ADMIN LIVE POMOC 30: rodowod rasa karta NAZWA; '
      'rodowod rasa plan NAZWA | SILA ZRE KON INT WOLA; '
      'rodowod klasa karta NAZWA; rodowod klasa plan NAZWA | BRON_DUSZY; '
      'rodowod zatwierdz POTWIERDZAM / rodowod cofnij POTWIERDZAM / rodowod anuluj. '
      'TYLKO istniejace rasy i klasy, nowe postaci po zmianie; 50 pkt statystyk rasy. '
      'Nowe pasywy, nowe klasy i nowe skille NIE sa tu tworzone. Brak zmian istniejacych postaci.')


def _registry():
    from core.classes_skills import RACES,CLASSES
    return RACES,CLASSES


def _lookup(kind,name):
    races,classes=_registry()
    entries=races if kind=='rasa' else classes
    for i,row in enumerate(entries):
        if row[0].casefold()==name.casefold():return i,row
    raise ValueError('Nieznana '+kind+': tylko istniejace nazwy z kreatora.')


def _validate(payload):
    if type(payload) is not dict or set(payload) not in (set(),{'races'},{'classes'},{'races','classes'}):
        raise ValueError('Niepoprawne ustawienia rodowodu.')
    data={'races':payload.get('races',{}),'classes':payload.get('classes',{})}
    if any(type(data[x]) is not dict or len(data[x])>64 for x in data):
        raise ValueError('Zbyt wiele zmian rodowodu.')
    for name,stats in data['races'].items():
        _lookup('rasa',name)
        if _BASE_REGISTRY is not None and name not in {row[0] for row in _BASE_REGISTRY[0]}:
            raise ValueError('Statystyki nowych ras edytuje sie tylko przy tworzeniu nowej rasy.')
        if (not isinstance(stats,list) or len(stats)!=5 or any(type(v) is not int or not 1<=v<=30 for v in stats)
                or sum(stats)!=50):
            raise ValueError('Rasa: dokladnie 50 punktow, 5 statystyk 1..30.')
    for name,weapon in data['classes'].items():
        _lookup('klasa',name)
        if _BASE_REGISTRY is not None and name not in {row[0] for row in _BASE_REGISTRY[1]}:
            raise ValueError('Klasy dodane edytuj przez rodowod nowa klasa.')
        if (not isinstance(weapon,str) or not 1<=len(weapon)<=70
                or any(ord(x)<32 or ord(x)==127 for x in weapon)):
            raise ValueError('Bron Duszy: nazwa 1..70 znakow bez sterujacych.')
    return data


def current():
    global _SETTINGS
    if _SETTINGS is None:
        if CONFIG_PATH.exists():
            raw=json.loads(CONFIG_PATH.read_text('utf-8'))
            if type(raw) is not dict or raw.get('schema')!=1:
                raise ValueError('Niepoprawny plik heritage_v7100.json.')
            _SETTINGS=_validate(raw.get('settings'))
        else:_SETTINGS={'races':{},'classes':{}}
    return copy.deepcopy(_SETTINGS)


def _apply(data):
    global _BASE_REGISTRY
    races, classes = _registry()
    if _BASE_REGISTRY is None:
        _BASE_REGISTRY = (tuple(races), tuple(classes))
    originals_r, originals_c = _BASE_REGISTRY
    if len(classes) < len(originals_c) or len(races) < len(originals_r):
        raise ValueError('Katalog klas lub ras zmienil rozmiar; odmowa odtwarzania.')
    # Custom playable races from v76 must survive edits to original race stats.
    # Refuse to touch an unrecognized extension (do not silently delete it).
    from sys import modules
    custom = modules.get('systems.admin_live_races_v7600')
    extra_names = [row[0] for row in races[len(originals_r):]]
    if extra_names and (custom is None or set(extra_names) != set(custom.current())):
        raise ValueError('Nieznane nowe rasy w katalogu; odmowa nadpisania.')
    new_classes=modules.get('systems.admin_live_classes_v7700')
    extra_classes={row[0] for row in classes[len(originals_c):]}
    if extra_classes and (new_classes is None or extra_classes != set(new_classes.current())):
        raise ValueError('Nieznane dodatkowe klasy w katalogu; odmowa nadpisania.')
    races[:] = originals_r
    classes[:] = originals_c
    for name, stats in data['races'].items():
        idx, old = _lookup('rasa', name)
        races[idx] = (old[0], old[1], *stats)
    for name, weapon in data['classes'].items():
        idx, old = _lookup('klasa', name)
        classes[idx] = (old[0], old[1], weapon, old[3])
    if custom is not None and custom._ORIGINAL_RACES is not None:
        custom.rebase_after_heritage()
    if new_classes is not None and new_classes._ORIGINAL is not None:
        new_classes.rebase_after_heritage()


def restore():
    _apply(current())


def _save(updated):
    global _SETTINGS
    updated=_validate(updated)
    CONFIG_PATH.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps({'schema':1,'settings':updated},ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    fd,tmp=tempfile.mkstemp(dir=str(CONFIG_PATH.parent),prefix='.heritage_',suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            f.write(payload);f.flush();os.fsync(f.fileno())
        os.replace(tmp,CONFIG_PATH)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    _SETTINGS=copy.deepcopy(updated)
    _apply(updated)


def card(kind,name):
    _,row=_lookup(kind,name)
    if kind=='rasa':
        return f'RASA {row[0]}: {row[1][:100]}; sila, zre, kon, int, wola = {list(row[2:])}, suma {sum(row[2:])}. Wplyw tylko na przyszle postacie.'
    return f'KLASA {row[0]}: {row[1]}, Bron Duszy {row[2]}, moc {row[3]}. Wplyw nazwy broni na przyszle postacie.'


def plan(session,kind,raw):
    session.adminlive7100_heritage_plan=None
    if '|' not in raw:raise ValueError('Wymagany separator | po nazwie.')
    name,value=(p.strip() for p in raw.split('|',1))
    idx,row=_lookup(kind,name)
    before=current();after=copy.deepcopy(before)
    if kind=='rasa':
        parts=value.split()
        if len(parts)!=5 or any(not v.isascii() or not v.isdecimal() or len(v)>2 for v in parts):
            raise ValueError('Wpisz piec calkowitych statystyk 1..30.')
        after['races'][row[0]]=[int(x) for x in parts]
    else:after['classes'][row[0]]=value
    _validate(after)
    if before==after:raise ValueError('Nie ma zmiany do wprowadzenia.')
    session.adminlive7100_heritage_plan=(before,after,kind,row[0])
    return f'RODOWOD PLAN {kind} {row[0]}: {value}. Tylko nowe postacie. rodowod zatwierdz POTWIERDZAM.'


def commit(session):
    plan=getattr(session,'adminlive7100_heritage_plan',None)
    if not plan:raise ValueError('Brak planu.')
    before,after,kind,name=plan
    if current()!=before:
        session.adminlive7100_heritage_plan=None
        raise ValueError('Plik rodowodu zmieniony po planie.')
    _save(after)
    session.adminlive7100_heritage_undo=(before,after)
    session.adminlive7100_heritage_plan=None
    return f'RODOWOD ZAPISANO: {kind} {name}. Tylko przyszle postacie.'


def undo(session):
    data = getattr(session, 'adminlive7100_heritage_undo', None)
    if not data:
        raise ValueError('Brak operacji do cofniecia.')
    before, after = data
    if current() != after:
        raise ValueError('Zmiany po zapisie: cofniecie zablokowane.')
    _save(before)
    session.adminlive7100_heritage_undo = None
    return 'RODOWOD: cofnieto zapis. Tylko nowe postacie.'


async def dispatch_v7100_heritage(session,group,raw):
    if not ((group=='pomoc' and raw.strip()=='30') or group=='rodowod'):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    parts=str(raw or '').strip().split(maxsplit=2)
    try:
        if group=='pomoc':out=HELP
        elif len(parts)>=2 and parts[0] in ('rasa','klasa') and parts[1]=='karta' and len(parts)==3:
            out=card(parts[0],parts[2])
        elif len(parts)==3 and parts[0] in ('rasa','klasa') and parts[1]=='plan':
            out=plan(session,parts[0],parts[2])
        elif parts==['zatwierdz','POTWIERDZAM']:out=commit(session)
        elif parts==['cofnij','POTWIERDZAM']:out=undo(session)
        elif parts==['anuluj']:
            session.adminlive7100_heritage_plan=None;out='RODOWOD: plan anulowany.'
        else:raise ValueError('rodowod rasa/klasa karta NAZWA, plan NAZWA | WARTOSCI, zatwierdz POTWIERDZAM')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,OSError,json.JSONDecodeError) as exc:
        out='ADMIN LIVE RODOWOD: '+str(exc)[:260]
    await session.send(out)
    return True
