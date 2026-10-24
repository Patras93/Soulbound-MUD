# -*- coding: utf-8 -*-
"""Admin Guardian 4.0: bounded diagnostics and DRAFT-only authoring.

No rewards, combat instances, quest progress writes, production OLC activation,
or modifications to the live database. Owner-only, with explicit confirmation
for the single DRAFT write.
"""
import copy
import math
import re
import sqlite3
import time
from collections import Counter, deque
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS
from systems.admin_guardian2_v3600 import resolve_mob, _number, _audit
from systems.admin_guardian3_v3700 import _numeric_meta

HELP = ('GUARDIAN4: arena prognoza MOB_ID HP_POSTACI ATAK [MAX_TUR 1-1000]; '
        'arena porownaj MOB_ID HP_POSTACI ATAK1 ATAK2; '
        'kraina sprawdz ID; kraina polacz ID NUMER1 NUMER2 KIERUNEK POTWIERDZAM; '
        'questy skan NICK; questy katalog QUEST_ID; '
        'balans porownaj MOB_ID ATAK1 ATAK2; '
        'event raport; historia filtruj FRAGMENT_AKCJI [ILE]; role raport; status. '
        'Tylko kraina polacz modyfikuje DRAFT; nigdy nie publikuje. '
        'Prognoza nie jest prawdziwa walka AI/UOSS.')

_REVERSE = {'north':'south','south':'north','east':'west','west':'east',
            'up':'down','down':'up','northeast':'southwest','southwest':'northeast',
            'northwest':'southeast','southeast':'northwest'}


def _area_key(key):
    if not re.fullmatch(r'[a-z][a-z0-9_]{3,19}',key):
        raise ValueError('Kraina: ID musi zawierac 4-20 malych liter, cyfr lub _.')
    return key


def _area_rooms(service,key):
    _area_key(key)
    prefix='live_'+key+'_r'
    rooms={rid for rid in service.draft['rooms'] if rid.startswith(prefix) and re.fullmatch(r'\d{2}',rid[len(prefix):])}
    if not rooms: raise ValueError('Nie ma takiej krainy w DRAFT.')
    return rooms


def _area_report(service,key):
    rooms=_area_rooms(service,key)
    links=[(a,b,c) for a,b,c in service.draft['links'] if a in rooms or c in rooms]
    inside=[(a,b,c) for a,b,c in links if a in rooms and c in rooms]
    entry=[(a,b,c) for a,b,c in links if a not in rooms and c in rooms]
    reverse={(a,b,c) for a,b,c in inside}
    missing=sum((c,_REVERSE[b],a) not in reverse for a,b,c in inside)
    reachable=set(); start=min(rooms)
    frontier=deque([start]); graph={r:[] for r in rooms}
    for a,b,c in inside: graph[a].append(c)
    while frontier:
        x=frontier.popleft()
        if x in reachable:continue
        reachable.add(x);frontier.extend(v for v in graph[x] if v not in reachable)
    npcs=[n for n in service.draft['npcs'].values() if n.get('room') in rooms]
    npc_counts=Counter(n.get('room') for n in npcs)
    collisions=sum(v>1 for v in npc_counts.values())
    spawn_count=sum(r in rooms for r,_ in service.draft['spawns'])
    stores=sum(r in rooms for r in service.draft['shops'])
    quests=sum(q.get('giver') in {n.get('name') for n in npcs} for q in service.draft['quests'].values())
    return (f'KRAINA {key} DRAFT: {len(rooms)} pokoi, osiagalne {len(reachable)}/{len(rooms)}, '
            f'{len(inside)} przejsc wewnetrznych, brak odwrotnych {missing}, '
            f'wejsc z zewnatrz {len(entry)}, NPC {len(npcs)}, kolizje NPC {collisions}, '
            f'spawn {spawn_count}, sklepy {stores}, questy dawcy {quests}. '
            'To diagnostyka DRAFT. Przed publikacja: admin live sprawdz / porownaj.')


def _area_connect(service,key,from_num,to_num,direction):
    rooms=_area_rooms(service,key)
    a=f'live_{key}_r{_number(from_num,1,20):02}'
    b=f'live_{key}_r{_number(to_num,1,20):02}'
    if a==b or a not in rooms or b not in rooms:
        raise ValueError('Podaj dwa rozne, istniejace pokoje krainy.')
    direction=direction.lower()
    if direction not in _REVERSE: raise ValueError('Nieznany kierunek; np. north, south, east, west.')
    rev=_REVERSE[direction]
    existing=service.draft['links']
    if any(x==a and y==direction for x,y,z in existing) or any(x==b and y==rev for x,y,z in existing):
        raise ValueError('Kierunek zajety w DRAFT; nie nadpisuje istniejacego przejscia.')
    candidate=copy.deepcopy(service.draft)
    candidate['links'].extend(([a,direction,b],[b,rev,a]))
    service.validate(candidate)  # validate FIRST, then stage atomically
    service.draft=candidate
    return (f'KRAINA DRAFT: polaczono {a} {direction} {b} oraz powrot {rev}. '
            'Nie opublikowano. Uzyj admin live sprawdz / porownaj / aktywuj POTWIERDZAM.')


def _arena_projection(service,mob_id,hp,attack,cap=1000):
    meta, origin=resolve_mob(service,mob_id)
    if not meta: raise ValueError('Nieznany mob lub DRAFT.')
    mob_hp,mob_damage=_numeric_meta(meta)
    hp=_number(hp,1,10**15);attack=_number(attack,1,10**15);cap=_number(cap,1,1000)
    needed=(mob_hp+attack-1)//attack
    attacks_before_win=needed-1
    survived=hp>attacks_before_win*mob_damage
    victory=survived and needed<=cap
    death_turn=(hp+mob_damage-1)//mob_damage if mob_damage else cap+1
    turns=needed if victory else min(cap,death_turn,needed)
    remaining=max(0,mob_hp-turns*attack)
    damage_received=min(max(0,turns if remaining else turns-1)*mob_damage,hp)
    hero_remaining=max(0,hp-damage_received)
    result='WYGRANA' if victory else 'PORAZKA' if hero_remaining==0 else 'LIMIT_TUR'
    return (f'ARENA PROGNOZA {mob_id} ({origin}): {result}; tur {turns}, '
            f'HP moba {remaining}/{mob_hp}, postaci {hero_remaining}/{hp}; '
            f'obrazenia bazowe moba {mob_damage}; pelna wygrana wymaga {needed} tur. '
            'Model statyczny: bez AI, faz UOSS, odpornosci, tarcz i losowosci. Bez nagrod.')


def _quest_scan(db,nick,service):
    if not nick or len(nick)>80: raise ValueError('Podaj dokladny nick.')
    character=db.conn.execute('SELECT account_id,name FROM characters WHERE name=? COLLATE NOCASE',(nick,)).fetchone()
    if not character: raise ValueError('Nieznany nick.')
    rows=db.quest_rows(character['account_id'])
    anomalies=[]; active=0
    for q in rows:
        qid=str(q['quest_id']); status=str(q['status'])
        if status=='active': active+=1
        reasons=[]
        if int(q['progress'])<0: reasons.append('ujemny postep')
        if int(q['completion_count'])<0: reasons.append('ujemny licznik')
        if qid not in QUESTS and qid not in service.active.get('quests', {}) and qid not in service.draft.get('quests', {}):
            reasons.append('brak w obecnym katalogu bazowym/OLC; sprawdz historie')
        if status not in ('active','completed','abandoned'): reasons.append('nietypowy status')
        if reasons: anomalies.append(f'{qid}: {", ".join(reasons)}')
    return (f'QUESTY {character["name"]}: wszystkich {len(rows)}, aktywnych {active}, '
            f'sygnalow do sprawdzenia {len(anomalies)}. '
            + ('; '.join(anomalies[:20]) if anomalies else 'Brak oczywistych anomalii.')
            + ('; dalsze pominięto.' if len(anomalies)>20 else '')
            + ' To poszlaki, nie automatyczny dowod bledu. Brak zmian.')


def _quest_catalog(service,qid):
    if not qid or len(qid)>90: raise ValueError('Podaj ID questu.')
    quest=service.draft['quests'].get(qid) or QUESTS.get(qid)
    if not quest: raise ValueError('Nieznany QUEST_ID.')
    kind=quest.get('kind','?');target=str(quest.get('target',''))
    check=''
    if kind=='kill':
        check=('cel moba istnieje' if target in MOB_TEMPLATES or target in service.draft['mobs']
               else 'UWAGA: cel moba nieznany w katalogu bazowym/DRAFT')
    elif kind in ('collect','deliver','deliver_item'):
        from data.items import ITEMS
        check=('cel przedmiotu istnieje' if target in ITEMS or target in service.draft['items']
               else 'cel przedmiotu wymaga weryfikacji')
    else: check='mechanika celu wymaga osobnej diagnostyki'
    return (f'QUEST KATALOG {qid}: {quest.get("name","?")}; typ {kind}, cel {target or "brak"}, '
            f'wymagane {quest.get("needed","?")}, dawca {quest.get("giver","?")}; {check}. '
            'Odczyt, bez zmian postepu, nagrod lub ukonczenia.')


def _balance_compare(service,mob_id,attack_a,attack_b):
    meta,origin=resolve_mob(service,mob_id)
    if not meta: raise ValueError('Nieznany mob.')
    hp,damage=_numeric_meta(meta)
    aa=_number(attack_a,1,10**15);bb=_number(attack_b,1,10**15)
    ta=(hp+aa-1)//aa;tb=(hp+bb-1)//bb
    return (f'BALANS POROWNAJ {mob_id} ({origin}): HP {hp}, bazowy atak {damage}; '
            f'wariant A {aa} obrazen/ture = {ta} tur; wariant B {bb} obrazen/ture = {tb} tur; '
            f'roznica {abs(ta-tb)} tur. Bez AI, faz, odpornosci i prognozy rzeczywistego czasu.')


def _event_report(server):
    events=getattr(server,'guardian_events_v3600',{})
    spawned=getattr(server,'guardian_spawns_v3600',{})
    now=time.time()
    lines=[]
    for name,ev in list(events.items())[:10]:
        live=sum(k in getattr(server.world,'mobs',{}) for k in ev.get('keys',[]))
        duration=max(0,int(now-float(ev.get('started',now))))//60
        lines.append(f'{name} pokoj {ev.get("room","?")}, {live}/{len(ev.get("keys",[]))} mobow, {duration} min od startu')
    return 'EVENTY GUARDIAN: '+('; '.join(lines) if lines else 'brak aktywnych')+f'; lacznie {len(spawned)} sesyjnych spawn. Raport tylko do odczytu.'


def _history_filter(db,token,count):
    if not 2<=len(token)<=40 or not re.fullmatch(r'[a-zA-Z0-9_\-]+',token):
        raise ValueError('Fragment akcji: 2-40 liter/cyfr/_/-.')
    count=_number(count,1,30)
    # Parameterized query; wildcard characters intentionally not accepted.
    try:
        rows=db.conn.execute('SELECT id,action,target FROM admin_actions_v1224 WHERE action LIKE ? ORDER BY id DESC LIMIT ?',('%'+token+'%',count)).fetchall()
    except sqlite3.OperationalError:
        rows=[]
    return 'HISTORIA FILTR: '+('; '.join(f'{x["id"]} {x["action"]} {x["target"]}' for x in rows) if rows else 'brak dopasowan.')


def _role_report(db):
    try:
        rows=db.conn.execute('SELECT role,COUNT(*) AS n FROM admin_guardian_roles_v3600 GROUP BY role ORDER BY role').fetchall()
    except sqlite3.OperationalError:
        rows=[]
    return 'ROLE GUARDIAN: '+('; '.join(f'{r["role"]}: {r["n"]}' for r in rows) if rows else 'brak delegowanych rol.')


async def handle_guardian4(s,raw):
    parts=str(raw).strip().split()
    if not parts or parts[0].casefold()!='guardian4': return False
    if not s.is_admin():
        await s.send('GUARDIAN4: tylko wlasciciel-administrator.');return True
    args=parts[1:];sub=args[0].casefold() if args else 'pomoc';tail=args[1:]
    try:
        service=s.server.live_content_v1204
        if sub in ('pomoc','help'): msg=HELP
        elif sub=='status': msg='GUARDIAN4 v38: diagnostyka siedmiu obszarow, jedna odwracalna zmiana DRAFT; bez realnej areny AI/UOSS.'
        elif sub=='arena':
            action=tail[0].casefold() if tail else ''
            if action=='prognoza' and len(tail) in (4,5):
                msg=_arena_projection(service,tail[1],tail[2],tail[3],tail[4] if len(tail)==5 else 1000)
            elif action=='porownaj' and len(tail)==5:
                first=_arena_projection(service,tail[1],tail[2],tail[3])
                second=_arena_projection(service,tail[1],tail[2],tail[4])
                msg='WARIANT A: '+first+' WARIANT B: '+second
            else: raise ValueError('arena prognoza MOB_ID HP_POSTACI ATAK [MAX_TUR] / porownaj MOB_ID HP ATAK1 ATAK2')
        elif sub=='kraina':
            action=tail[0].casefold() if tail else ''
            if action=='sprawdz' and len(tail)==2: msg=_area_report(service,tail[1])
            elif action=='polacz' and len(tail)==6 and tail[-1]=='POTWIERDZAM':
                msg=_area_connect(service,tail[1],tail[2],tail[3],tail[4]);_audit(s,'g4_region_link',tail[1])
            else: raise ValueError('kraina sprawdz ID / polacz ID NUMER1 NUMER2 KIERUNEK POTWIERDZAM')
        elif sub=='questy':
            action=tail[0].casefold() if tail else ''
            if action=='skan' and len(tail)==2: msg=_quest_scan(s.server.db,tail[1],service)
            elif action=='katalog' and len(tail)==2: msg=_quest_catalog(service,tail[1])
            else: raise ValueError('questy skan NICK / katalog QUEST_ID')
        elif sub=='balans':
            if len(tail)==4 and tail[0].casefold()=='porownaj': msg=_balance_compare(service,tail[1],tail[2],tail[3])
            else: raise ValueError('balans porownaj MOB_ID ATAK1 ATAK2')
        elif sub=='event':
            if tail!=['raport']:raise ValueError('event raport')
            msg=_event_report(s.server)
        elif sub=='historia':
            if len(tail) in (2,3) and tail[0].casefold()=='filtruj':
                msg=_history_filter(s.server.db,tail[1],tail[2] if len(tail)==3 else 15)
            else: raise ValueError('historia filtruj FRAGMENT_AKCJI [ILE]')
        elif sub=='role':
            if tail!=['raport']:raise ValueError('role raport')
            msg=_role_report(s.server.db)
        else: raise ValueError(HELP)
        await s.send(msg)
    except (ValueError,TypeError,KeyError,OverflowError,AttributeError,sqlite3.DatabaseError) as exc:
        await s.send('GUARDIAN4: '+str(exc)[:350])
    return True
