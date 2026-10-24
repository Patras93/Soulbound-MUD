# -*- coding: utf-8 -*-
"""Guardian 11: source-catalog class skills, modelled gear and rehearsed sequences.

No production session methods, DB writes, reward hooks or world spawning run
from this module. All changes remain in session.guardian7_lab. Class skill
multipliers and MP costs are read from canonical skill data; the damage and
armor application are intentionally simplified LAB rules, not live combat.
"""
from __future__ import annotations

import copy
from types import SimpleNamespace
from core.classes_skills import CLASS_SKILLS, effective_skill_mana_cost
from data.items import ITEMS
from systems.admin_guardian7_v4100 import _number, _id
from systems.admin_guardian9_v4300 import _state, _sync_actor
from systems.admin_guardian10_v4400 import _lab_start10, _lab_turn10, _seed_change

_MAX_SCRIPT=12
_MAX_MASTERY=800
_MAX_MANA=10**12
_ALLOWED_SKILL_KINDS={'damage':'atak','heal':'lecz','guard':'obrona','evade':'obrona'}

_HELP={
'1':('GUARDIAN11 pomoc 1/3: arena start BOSS HP ATAK [HELPER]; '
     'arena klasa NAZWA BIEGLOSC MANA POTWIERDZAM; '
     'arena skille [STRONA]; arena skill ID [CEL]; arena atak [CEL]; '
     'arena status. Skille z katalogu, modelowane skutki LAB.'),
'2':('GUARDIAN11 pomoc 2/3: arena przedmiot ID; arena zaloz ID POTWIERDZAM; '
     'arena zdejmij SLOT POTWIERDZAM; arena ekwipunek; '
     'arena sekwencja plan AKCJE; arena sekwencja wykonaj AKCJE POTWIERDZAM. '
     'Akcje po przecinku: atak, atak:1, obrona, lecz, magia:ogien, skill:ID.'),
'3':('GUARDIAN11 pomoc 3/3: arena sekwencja porownaj AKCJE / AKCJE; '
     'arena ziarno LICZBA POTWIERDZAM; arena wynik; arena wyjdz. '
     'Do 12 tur w sekwencji; prognozy zachowuja RNG i stan. '
     'Sprzet: liniowy model ataku/obrony z danych przedmiotow, '
     'NIE jest prawdziwym zestawem gracza ani pelna walka produkcyjna.'),
}


def _arena(session):
    state=_state(session)
    if '_guardian10_rng' not in state: raise ValueError('Uruchom arena start w guardian11.')
    state.setdefault('_guardian11_build',{'class':None,'mastery':0,'mana':0,'max_mana':0,'items':{}})
    return state


def _class_name(value):
    return next((c for c in CLASS_SKILLS if c.casefold()==str(value).casefold()), None)


def _class_set(session, classname, mastery, mana):
    c=_class_name(classname)
    if not c:raise ValueError('Nieznana klasa. Wpisz nazwe klasy z Soulbound.')
    from core.live_level_caps_v5200 import cap, effective_number
    lvl=_number(mastery,1,effective_number(cap('bieglosc')))
    mp=_number(mana,0,_MAX_MANA)
    build=_arena(session)['_guardian11_build']
    build.update({'class':c,'mastery':lvl,'mana':mp,'max_mana':mp})
    return f'ARENA11 KLASA {c}: bieglosc {lvl}, modelowa mana {mp}. Prawdziwa postac bez zmian.'


def _skill_rows(state):
    b=state['_guardian11_build']
    name=b['class']
    if not name:raise ValueError('Ustaw najpierw: arena klasa KLASA BIEGLOSC MANA POTWIERDZAM.')
    return [row for row in CLASS_SKILLS[name]
            if int(row.get('unlock',1) or 1)<=b['mastery']]


def _skill_page(session, page='1'):
    state=_arena(session);rows=_skill_rows(state)
    p=_number(page,1,10000);pages=max(1,(len(rows)+7)//8)
    if p>pages:raise ValueError(f'Dostepne strony: 1-{pages}.')
    lines=[]
    for row in rows[(p-1)*8:p*8]:
        cost=effective_skill_mana_cost(row,state['_guardian11_build']['class'])
        lines.append(f'{row["id"]}: {row["name"]}, {row["kind"]}, mana {cost}')
    return f'ARENA11 SKILLE {p}/{pages}, dostepnych {len(rows)}: '+('; '.join(lines) or 'brak')+'.'


def _skill(state, ident):
    ident=_id(ident)
    result=next((r for r in _skill_rows(state) if r['id']==ident),None)
    if result is None: raise ValueError('Nie znaleziono odblokowanego skilla o podanym ID.')
    if result.get('kind') not in _ALLOWED_SKILL_KINDS:
        raise ValueError('Ten rodzaj skilla wymaga pelnego silnika. Test LAB odmawia symulacji zamiast zmyslac efekt.')
    return result


def _item_row(ident):
    ident=_id(ident)
    item=ITEMS.get(ident)
    if not item:raise ValueError('Nieznane ID przedmiotu.')
    return item


def _item_stats(item):
    # Narrow, explicit lab arithmetic, no implicit magic or production bonuses.
    def safe_int(key):
        value=item.get(key,0) or 0
        if isinstance(value,bool) or not isinstance(value,(float,int)):return 0
        return max(0,min(10**10,int(value)))
    return safe_int('attack')+safe_int('weapon_power'), safe_int('defense')


def _item_info(ident):
    item=_item_row(ident); atk, defense=_item_stats(item)
    return (f'ARENA11 PRZEDMIOT {ident}: {str(item.get("name",ident))[:70]}; '
            f'typ {item.get("type","?")}, slot {item.get("slot","brak")}; '
            f'w modelu +{atk} do ciosu i -{defense} otrzymanych obrazen. '
            'Inne premie sa tylko w produkcyjnym silniku.')


def _equip(session, ident):
    item=_item_row(ident)
    slot=str(item.get('slot') or '').strip()
    if (item.get('type') not in ('weapon','armor','equipment','accessory','shield')
            or not slot or len(slot)>30):
        raise ValueError('To nie jest wyposazenie ze slotem dla laboratorium.')
    state=_arena(session)
    state['_guardian11_build']['items'][slot]=_id(ident)
    return f'ARENA11 ZALOZONO W LAB {ident}, slot {slot}. Bez zmian prawdziwego EQ.'


def _unequip(session,slot):
    slot=_id(slot)
    items=_arena(session)['_guardian11_build']['items']
    if slot not in items:raise ValueError('Brak testowego przedmiotu w tym slocie.')
    del items[slot]
    return f'ARENA11 ZDJETO LAB {slot}. Prawdziwe EQ nietkniete.'


def _equipment(state):
    b=state['_guardian11_build']
    atk=defense=0
    for ident in b['items'].values():
        i=ITEMS.get(ident)
        if i is None:continue
        a,d=_item_stats(i);atk+=a;defense+=d
    return atk,defense


def _equip_status(session):
    state=_arena(session)
    b=state['_guardian11_build']; atk,defense=_equipment(state)
    items=', '.join(f'{slot}: {id}' for slot,id in sorted(b['items'].items())) or 'brak'
    return (f'ARENA11 EKWIPUNEK LAB: {items}; liniowy bonus do ataku {atk}, '
            f'obrona {defense}; bez prawdziwych przedmiotow, statystyk i EQ.')


def _parse_actions(spec):
    actions=[]
    for raw in str(spec).split(','):
        part=raw.strip()
        if not part:raise ValueError('Pusta akcja w sekwencji.')
        op,sep,arg=part.partition(':')
        op=op.casefold()
        if op in ('atak','obrona','lecz') and (not sep or (op=='atak' and arg.strip())):
            if op=='atak' and sep: _number(arg.strip(),1,99)
            actions.append((op,arg.strip() if sep else 'boss'))
        elif op=='magia' and sep and arg.strip() and len(arg.strip())<=30:
            actions.append((op,arg.strip()))
        elif op=='skill' and sep:
            actions.append((op,_id(arg.strip())))
        else:raise ValueError('Akcje: atak[:NUMER], obrona, lecz, magia:ZYW, skill:ID.')
    if not 1<=len(actions)<=_MAX_SCRIPT:raise ValueError('Od 1 do 12 akcji w sekwencji.')
    return actions


def _turn(session,op,arg):
    state=_arena(session)
    if state['finished']:raise ValueError('Arena zakonczona.')
    original=copy.deepcopy(state)
    b=state['_guardian11_build']
    try:
        action,target,element=op,'boss',None
        multiplier=1.0;cost=0;name=''
        if op=='skill':
            row=_skill(state,arg)
            action=_ALLOWED_SKILL_KINDS[row['kind']]
            cost=effective_skill_mana_cost(row,b['class'])
            if cost>b['mana']:raise ValueError(f'Za malo many LAB: potrzeba {cost}, masz {b["mana"]}.')
            multiplier=float(row.get('mult',1) or 1)
            if not 0<=multiplier<=1000000:raise ValueError('Nieprawidlowy mnoznik skilla.')
            name=str(row.get('name','skill'))[:60]
        elif op=='magia': action='magia';element=arg
        elif op=='atak':target=arg
        boost,defense=_equipment(state)
        base=state['hero_attack']
        if action in ('atak','magia'):
            state['hero_attack']=max(0,int((base+boost)*multiplier))
        hp_before=state['hero_hp'];taken_before=state['total_taken']
        response=_lab_turn10(session,action,target,element)
        current=_arena(session)
        current['hero_attack']=base
        delta=current['total_taken']-taken_before
        # This is explicit model armor after canonical UOSS source effects.
        # An instant-death boss event must never be cancelled by equipment.
        if defense and delta>0 and 'modelowa porazka' not in response:
            guard=min(delta,defense)
            current['total_taken']-=guard
            current['hero_hp']=max(0,current['hero_hp']+guard)
            if hp_before>0 and current['hero_hp']>0 and current['boss'].hp>0 and current['round']<250:
                current['finished']=False
            _sync_actor(current)
            response+=f' MODELOWY PANCERZ: -{guard} obrazen.'
        current['_guardian11_build']['mana']-=cost
        if name:response=f'ARENA11 SKILL {name}, koszt MP {cost}, mnoznik katalogowy {multiplier}. '+response
        return response.replace('ARENA10','ARENA11')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError):
        session.guardian7_lab=original
        raise


def _sequence(session,spec,preview):
    actions=_parse_actions(spec)
    current=_arena(session)
    if current['finished']:raise ValueError('Arena zakonczona.')
    # Validate all static action prerequisites BEFORE first turn.
    for op,arg in actions:
        if op=='skill':_skill(current,arg)
    clone=SimpleNamespace(guardian7_lab=copy.deepcopy(current)) if preview else session
    before=copy.deepcopy(current)
    played=[]
    try:
        for op,arg in actions:
            if clone.guardian7_lab['finished']:break
            played.append(_turn(clone,op,arg))
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError):
        if not preview:session.guardian7_lab=before
        raise
    result=clone.guardian7_lab
    return (f'ARENA11 {"PLAN" if preview else "WYKONANO"}: {len(played)}/{len(actions)} akcji; '
        f'runda {result["round"]}; boss HP {result["boss"].hp}; postac HP {result["hero_hp"]}; '
        f'mana {result["_guardian11_build"]["mana"]}; '
        f'zadane +{result["total_dealt"]-before["total_dealt"]}; '
        f'otrzymane +{result["total_taken"]-before["total_taken"]}. '
        +('Biezaca arena, RNG, EQ i SQLite bez zmian.' if preview else 'Zmieniono tylko stan LAB.'))


def _compare(session,left,right):
    current=_arena(session)
    results=[]
    for i,spec in enumerate((left,right),1):
        results.append(f'{i}: '+_sequence(session,spec,True))
    return 'ARENA11 POROWNAJ: '+'; '.join(results)+ ' Identyczny stan poczatkowy i RNG; bez zapisow.'


async def handle_guardian11(session,raw):
    parts=str(raw or '').strip().split(maxsplit=1)
    if not parts or parts[0].casefold()!='guardian11':return False
    if not session.is_admin():
        await session.send('GUARDIAN11: tylko administrator-wlasciciel.');return True
    service=session.server.live_content_v1204
    rest=parts[1].strip() if len(parts)>1 else 'pomoc 1'
    args=rest.split()
    try:
        mode=args[0].casefold() if args else 'pomoc'
        if mode=='pomoc':
            page=args[1] if len(args)>1 else '1'
            if len(args)>2 or page not in _HELP:raise ValueError('Pomoc: 1, 2, 3.')
            output=_HELP[page]
        elif mode=='status' and len(args)==1:
            output='GUARDIAN11: '+('arena aktywna' if getattr(session,'guardian7_lab',None) else 'arena nieaktywna')+'; tylko LAB.'
        elif mode=='arena':
            op=args[1].casefold() if len(args)>1 else ''
            if op=='start' and len(args) in (5,6):
                output=_lab_start10(session,service,args[2],args[3],args[4],args[5] if len(args)==6 else 'brak').replace('ARENA10','ARENA11')
                _arena(session)
            elif op=='klasa' and len(args)==6 and args[5]=='POTWIERDZAM':
                output=_class_set(session,args[2],args[3],args[4])
            elif op=='skille' and len(args) in (2,3):output=_skill_page(session,args[2] if len(args)==3 else '1')
            elif op=='skill' and len(args) in (3,4):output=_turn(session,'skill',args[2]) if len(args)==3 else 'GUARDIAN11: skill wybranego celu jeszcze nie jest symulowany; uzyj skill ID.'
            elif op in ('atak','obrona','lecz') and (len(args)==2 or (op=='atak' and len(args)==3)):
                output=_turn(session,op,args[2] if len(args)==3 else 'boss')
            elif op=='magia' and len(args)==3:output=_turn(session,'magia',args[2])
            elif op=='przedmiot' and len(args)==3:output=_item_info(args[2])
            elif op=='zaloz' and len(args)==4 and args[3]=='POTWIERDZAM':output=_equip(session,args[2])
            elif op=='zdejmij' and len(args)==4 and args[3]=='POTWIERDZAM':output=_unequip(session,args[2])
            elif op=='ekwipunek' and len(args)==2:output=_equip_status(session)
            elif op=='sekwencja':
                sections=rest.split(None,3)
                if len(sections)<4:raise ValueError('arena sekwencja plan/wykonaj/porownaj AKCJE')
                sub=sections[2].casefold();payload=sections[3].strip()
                if sub=='plan':output=_sequence(session,payload,True)
                elif sub=='wykonaj':
                    if not payload.endswith(' POTWIERDZAM'):raise ValueError('Potwierdz przez POTWIERDZAM.')
                    output=_sequence(session,payload[:-len(' POTWIERDZAM')].strip(),False)
                elif sub=='porownaj':
                    variants=payload.split(' / ')
                    if len(variants)!=2:raise ValueError('Oddziel dwa warianty: AKCJE / AKCJE.')
                    output=_compare(session,*variants)
                else:raise ValueError('sekwencja plan / wykonaj / porownaj')
            elif op=='ziarno' and len(args)==4 and args[3]=='POTWIERDZAM':output=_seed_change(session,args[2]).replace('ARENA10','ARENA11')
            elif op=='status' and len(args)==2:
                a=_arena(session);b=a['_guardian11_build']
                output=(f'ARENA11 runda {a["round"]}, boss HP {a["boss"].hp}, hero HP {a["hero_hp"]}; '
                    f'klasa {b["class"] or "brak"}, bieglosc {b["mastery"]}, mana {b["mana"]}/{b["max_mana"]}; '
                    'postac i swiat bez zmian.')
            elif op=='wynik' and len(args)==2:
                a=_arena(session);output=(f'ARENA11 WYNIK rundy {a["round"]}, zadane {a["total_dealt"]}, '
                  f'otrzymane {a["total_taken"]}; 0 EXP, 0 zlota, 0 dropow.')
            elif op=='wyjdz' and len(args)==2:
                session.guardian7_lab=None;session.guardian9_snapshot=None
                output='ARENA11: zakonczono prywatna symulacje bez zapisow.'
            else:raise ValueError(_HELP['1'])
        else:raise ValueError('Uzyj admin guardian11 pomoc 1/2/3.')
        await session.send(output)
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError) as exc:
        await session.send('GUARDIAN11: '+str(exc)[:350])
    return True
