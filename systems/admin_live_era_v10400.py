# -*- coding: utf-8 -*-
"""Owner-only v104 live content fields with DRAFT, CAS, atomic publish and undo.

Only numeric whitelisted fields of v10400_* are editable. Never modifies
players, historical catalog IDs, executable code, or another admin's settings.
"""
from __future__ import annotations
from pathlib import Path
import json
import os
from tempfile import NamedTemporaryFile

PATH=Path(__file__).resolve().parent.parent/'LIVE_CONTENT'/'era_v10400_overrides.json'
FIELDS={
  'mob': {'max_hp':(1,(1<<63)-1),'damage':(1,(1<<63)-1),'gold':(0,(1<<63)-1),
          'silver':(0,(1<<63)-1),'mithril':(0,(1<<63)-1),
          'class_xp_reward':(0,(1<<63)-1),'soul_reward':(0,(1<<63)-1),'stat_reward':(0,(1<<63)-1)},
  'quest': {'needed':(1,100000),'reward_gold':(0,(1<<63)-1),
            'reward_mithril':(0,(1<<63)-1),'reward_stat_progress':(0,(1<<63)-1)},
  'item': {'defense':(0,(1<<63)-1),'affix_amount':(0,(1<<63)-1)},
  'recipe': {'min_profession_level':(1,10**9),'quantity':(1,100000)},
  'room': {'recommended_mastery':(1,10**9),'generator_level':(1,10**9)},
}
Draft=None
Baseline=None
State=None

def _empty():return {'schema':1,'rev':0,'active':{},'previous':None,'base':{}}

def _validate(data):
    if not isinstance(data,dict) or set(data)!={'schema','rev','active','previous','base'} or data['schema']!=1:
        raise ValueError('Nieprawidłowy format override v104')
    if type(data['rev']) is not int or data['rev']<0:raise ValueError('Nieprawidłowa rewizja')
    for rows in (data['active'],data['previous'],data['base']):
        if rows is None:continue
        if type(rows) is not dict:raise ValueError('Niepoprawne zmiany')
        if len(rows)>1000:raise ValueError('Zbyt wiele zmian')
        for key,val in rows.items():
            parts=key.split('|')
            if len(parts)!=3:raise ValueError('Nieprawidłowy klucz')
            typ,identifier,field=parts
            if typ not in FIELDS or field not in FIELDS[typ] or not identifier.startswith('v10400_'):
                raise ValueError('Pole spoza v104 lub niedozwolone')
            lo,hi=FIELDS[typ][field]
            if type(val) is not int or not lo<=val<=hi:raise ValueError('Wartość poza zakresem')
    return data

def _load():
    global State
    if State is None:
        State=_validate(json.loads(PATH.read_text(encoding='utf-8'))) if PATH.exists() else _empty()
    return State

def _save(state):
    _validate(state)
    PATH.parent.mkdir(parents=True,exist_ok=True)
    temp=None
    try:
        with NamedTemporaryFile('w',encoding='utf-8',dir=PATH.parent,prefix='.era_v104_',suffix='.tmp',delete=False) as f:
            temp=f.name; json.dump(state,f,ensure_ascii=False,indent=2,sort_keys=True)
            f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temp,PATH)
    finally:
        if temp and os.path.exists(temp):os.unlink(temp)

def _registry(kind,registries):
    keys={'mob':'mobs','quest':'quests','item':'items','recipe':'recipes','room':'rooms'}
    return registries[keys[kind]]

def apply(registries):
    data=_load()
    # all-or-nothing prevalidation: only existing v104 objects and values.
    for key in data['active']:
        kind,identifier,field=key.split('|')
        registry=_registry(kind,registries)
        if identifier not in registry or field not in registry[identifier]:
            raise RuntimeError(f'Brak definicji dla opublikowanej zmiany: {key}')
    for key,value in data['base'].items():
        kind,identifier,field=key.split('|')
        _registry(kind,registries)[identifier][field]=value
    for key,value in data['active'].items():
        kind,identifier,field=key.split('|')
        _registry(kind,registries)[identifier][field]=value
    return len(data['active'])

def reset_for_tests():
    global Draft,Baseline,State
    Draft=Baseline=State=None

def command(tail,registries):
    global Draft,Baseline,State
    args=str(tail or '').split()
    action=args[0].casefold() if args else ''
    helpmsg=('V104 ADMIN: podglad TYP ID POLE / ustaw TYP ID POLE LICZBA / '
             'sprawdz / porownaj / aktywuj POTWIERDZAM / anuluj / cofnij POTWIERDZAM. '
             'Typy: mob, quest, item, recipe, room. Tylko v10400_.')
    if action in ('','pomoc','help'):return helpmsg
    try:state=_load()
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        return f'V104: nie można wczytać ustawień ({type(exc).__name__}). Nic nie zapisano.'
    if action=='wydarzenia':
        return 'V104: 10 kontraktów inwazji odnawianych co 7 dni od oddania. Wspólna rotacja serwerowa i licznik udziału nie są jeszcze aktywne.'
    if action=='status':return f'V104 Admin Live: rewizja {state["rev"]}, aktywnych pól {len(state["active"])}, DRAFT {len(Draft) if Draft is not None else 0}.'
    if action in ('podglad','ustaw') and len(args) in (4,5):
        kind=args[1].casefold();identifier=args[2];field=args[3]
        if kind not in FIELDS or field not in FIELDS[kind] or not identifier.startswith('v10400_'):
            return 'Nieobsługiwane pole lub identyfikator. '+helpmsg
        obj=_registry(kind,registries).get(identifier)
        if obj is None or field not in obj:return 'Nie istnieje takie pole w rejestrze v104.'
        key='|'.join((kind,identifier,field))
        if action=='podglad' and len(args)==4:
            return f'V104 {kind} {identifier} {field}: aktualnie {obj[field]}; DRAFT {Draft.get(key) if Draft and key in Draft else "brak"}.'
        if action=='ustaw' and len(args)==5:
            raw=args[4]
            if not raw.isascii() or not raw.isdecimal() or len(raw)>19:return 'Podaj nieujemną liczbę całkowitą bez separatorów.'
            n=int(raw); lo,hi=FIELDS[kind][field]
            if not lo<=n<=hi:return f'Zakres pola {field}: {lo}–{hi}.'
            if Draft is None:
                Draft=dict(state['active']);Baseline=state['rev']
            Draft[key]=n
            return f'V104 DRAFT: {identifier} {field}: {obj[field]} -> {n}; opublikuj po sprawdzeniu.'
    if action in ('sprawdz','porownaj') and len(args)==1:
        if Draft is None:return 'V104: brak zmian DRAFT.'
        try:_validate({'schema':1,'rev':state['rev'],'active':Draft,'previous':None,'base':dict(state['base'])})
        except ValueError as exc:return f'V104 DRAFT odrzucony: {exc}'
        missing=[k for k in Draft if k.split('|')[2] not in _registry(k.split('|')[0],registries).get(k.split('|')[1],{})]
        if missing:return f'V104 DRAFT: brak pola {missing[0]}.'
        return f'V104: DRAFT {len(Draft)} pól, CAS {Baseline}->{state["rev"]}; '+ '; '.join(f'{k}={v}' for k,v in list(Draft.items())[:5])
    if action=='anuluj' and len(args)==1:
        Draft=Baseline=None;return 'V104: DRAFT anulowany, aktywne ustawienia niezmienione.'
    if action=='aktywuj' and args[1:]==['POTWIERDZAM']:
        if Draft is None:return 'V104: brak DRAFT.'
        if Baseline!=state['rev']:return 'V104: konflikt rewizji CAS, odśwież DRAFT.'
        result=command('sprawdz',registries)
        if 'brak pola' in result or 'odrzucony' in result:return result
        base=dict(state['base'])
        for key in Draft:
            if key not in base:
                kind,identifier,field=key.split('|')
                base[key]=int(_registry(kind,registries)[identifier][field])
        new={'schema':1,'rev':state['rev']+1,'active':dict(Draft),'previous':dict(state['active']),'base':base}
        _save(new)
        State=new
        apply(registries)
        Draft=Baseline=None
        return f'V104: opublikowano rewizję {new["rev"]}, {len(new["active"])} pól. Bez restartu.'
    if action=='cofnij' and args[1:]==['POTWIERDZAM']:
        if state['previous'] is None:return 'V104: nie ma poprzedniej rewizji.'
        previous=dict(state['previous'])
        new={'schema':1,'rev':state['rev']+1,'active':previous,
             'previous':dict(state['active']),'base':dict(state['base'])}
        _save(new);State=new;apply(registries);Draft=Baseline=None
        return f'V104: cofnięto wartości w pamięci; rewizja {new["rev"]}.'
    return helpmsg
