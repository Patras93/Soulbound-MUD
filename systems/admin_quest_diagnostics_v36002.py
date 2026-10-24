# -*- coding: utf-8 -*-
"""Read-only, bounded evidence for owner triage of live quests.

A saved progress counter does not prove that a kill occurred or an item was
handed in. This module never manufactures such evidence, writes to accounts,
or marks error reports resolved. Dynamic world catalogs are only inspected as
currently registered, with no promises about NPC routing or item provenance.
"""
import sqlite3
from data.quests import QUESTS
from data.npcs import NPCS
from data.mobs import MOB_TEMPLATES
from data.items import ITEMS
from data.rooms import ROOMS

READ_HELP = ('admin blad trop NICK QUEST_ID / npc QUEST_ID / skan NICK [ILE]. '
             'Wszystko tylko do odczytu; zadnego recznego zaliczania zabojstw, '
             'nagrod ani ukonczenia zadania.')


def _character(db, nick):
    if not nick or len(nick)>80:
        raise ValueError('Podaj dokladny nick postaci (maksymalnie 80 znakow).')
    row=db.conn.execute('SELECT account_id,name FROM characters WHERE name=? COLLATE NOCASE',(nick,)).fetchone()
    if row is None:
        raise ValueError('Nie znaleziono postaci. Nic nie zmieniono.')
    return row


def _giver_candidates(qid,quest):
    name=str(quest.get('giver') or '').casefold().strip()
    explicit=[]; names=[]
    for npc_id,npc in NPCS.items():
        if not isinstance(npc,dict):
            continue
        offers=[npc.get('quest')]
        offers.extend(npc.get('specialist_quests') or ())
        if qid in offers:
            explicit.append((npc_id,npc))
        elif name and str(npc.get('name') or '').casefold().strip()==name:
            names.append((npc_id,npc))
    return (explicit or names)[:5], bool(explicit)


def _npc_info(qid,quest):
    matches,explicit=_giver_candidates(qid,quest)
    label='Powiazania NPC (jawne)' if explicit else 'NPC zgodni z nazwa zleceniodawcy (poszlaka)'
    if not matches:
        return (f'NPC oferujacy: {quest.get("giver","nieustalony")}. '
                'Nie znaleziono jednoznacznego powiazania w aktualnym katalogu NPC; '
                'to nie jest jeszcze dowod, ze zadanie jest zepsute.')
    parts=[]
    for mid,npc in matches:
        room=npc.get('room','?')
        place=str(ROOMS.get(room,{}).get('name',room)) if room in ROOMS else 'NIEZNANA LOKACJA '+str(room)
        parts.append(f'{mid} w {place} ({room})')
    return label+': '+'; '.join(parts)+'.'


def _quest_required(db,account,quest):
    required=[]
    single=quest.get('requires_quest')
    if isinstance(single,str) and single:
        required.append(single)
    many=quest.get('requires_quests',())
    if isinstance(many,(list,tuple,set)):
        required.extend(q for q in many if isinstance(q,str))
    if not required:
        return 'Poprzednie zadania: brak jawnie wymaganych w tej definicji.'
    output=[]
    for qid in dict.fromkeys(required):
        row=db.conn.execute('SELECT status,completion_count FROM quests WHERE account_id=? AND quest_id=?',(account,qid)).fetchone()
        passed=bool(row and (row['status']=='completed' or int(row['completion_count'] or 0)>0))
        output.append(f'{qid} {"UKONCZONE" if passed else "BRAK POTWIERDZENIA"}')
        if len(output)==8:
            break
    return 'Wymagania: '+', '.join(output)+(' (pokazano pierwsze 8)' if len(required)>8 else '')+'.'


def _inventory_qty(db,account,item):
    try:
        row=db.conn.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',(account,item)).fetchone()
    except sqlite3.OperationalError as exc:
        if 'no such table' in str(exc).lower():
            return None
        raise
    return int(row['quantity']) if row else 0


def _objective(db,account,quest):
    kind=str(quest.get('kind','?'))
    target=quest.get('target')
    needed=quest.get('needed','?')
    lines=[f'Cel: typ {kind}; target {target}; wymagane {needed}.']
    if kind in ('kill','world_boss','legendary_rare'):
        if isinstance(target,str) and target:
            candidates=[(mid,m) for mid,m in MOB_TEMPLATES.items()
                        if mid==target or str(m.get('quest_target') or '')==target]
            if candidates:
                show=', '.join(str(meta.get('name',mid))+' ('+str(mid)+')' for mid,meta in candidates[:6])
                lines.append('Potwory pasujace do celu w AKTUALNYM katalogu: '+show+
                    (f'; inne warianty: {len(candidates)-6}' if len(candidates)>6 else '')+'.')
            else:
                lines.append('Brak potwierdzonego dopasowania w biezacym katalogu mobow. '
                    'Sprawdz alias celu, spawn oraz publikacje OLC; nie dopisuj zabojstw na slepo.')
        lines.append('Zapis zabojstwa nie zawiera pelnego dziennika kazdego kill; '
                    'licznik questu nie dowodzi, kto i kiedy zabil moba.')
    elif kind in ('collect','deliver_npc'):
        item=quest.get('quest_item') if kind=='deliver_npc' else target
        if isinstance(item,str) and item:
            label=ITEMS.get(item,{}).get('name',item)
            qty=_inventory_qty(db,account,item)
            lines.append(f'Przedmiot: {label} ({item}); '
                         + ('brak odczytu plecaka' if qty is None else f'w plecaku {qty}')+'. '
                         'To podglad plecaka, nie dowod zdobycia po przyjeciu ani zawartosci schowka.')
        if kind=='deliver_npc':
            dest=quest.get('target_npc')
            info=NPCS.get(dest)
            if info:
                room=info.get('room','?')
                lines.append(f'Odbiorca: {info.get("name",dest)} ({dest}), pokoj {room}; '
                             +('lokacja istnieje.' if room in ROOMS else 'BRAK pokoju w aktywnym katalogu.'))
            else:
                lines.append(f'Odbiorca target_npc {dest}: niepotwierdzony w katalogu. '
                             'Sprawdz konfiguracje NPC lub OLC.')
    elif kind in ('collect_category','collect_resource','collect_resource_set','profession_action'):
        lines.append('Zadanie wymaga okreslonych czynnosci lub kategorii; '
                     'sam stan plecaka nie jest dowodem zdobycia po przyjeciu questu.')
    else:
        lines.append('Ten typ zadania moze wymagac rozmowy, eksploracji lub skryptu fabularnego; '
                     'brak automatycznego dopisywania postepu.')
    return lines


def trace_quest(db,nick,qid):
    character=_character(db,nick)
    quest=QUESTS.get(qid)
    if quest is None:
        raise ValueError('ID questu nie istnieje w aktualnie zaladowanym katalogu. Nic nie zmieniono.')
    row=db.quest(character['account_id'],qid)
    state=(f'status {row["status"]}, postep {row["progress"]}, '
           f'ukonczen {row["completion_count"]}' if row else 'NIEPRZYJETY; brak wiersza postepu')
    lines=[f'TROP QUEST: {character["name"]}; {qid} — {quest.get("name",qid)}.',
           'BAZA: '+state+'.']
    if row and row['status']=='active' and int(row['progress'])<0:
        lines.append('BLAD DANYCH: ujemny postep; dostepna bezpieczna korekta tylko offline.')
    lines.extend(_objective(db,character['account_id'],quest))
    lines.append(_npc_info(qid,quest))
    lines.append(_quest_required(db,character['account_id'],quest))
    lines.append('DIAGNOZA, NIE NAPRAWA: sprawdz log SB, NPC, wymagany cel i rzeczywisty event. '
                 'Nie przyznano EXP, gold, przedmiotow ani postepu.')
    return lines


def scan_quests(db,nick,limit=20):
    character=_character(db,nick)
    rows=db.quest_rows(character['account_id'])
    out=[]
    for row in rows:
        qid=row['quest_id']
        issues=[]
        if qid not in QUESTS:
            issues.append('NIE MA ID W BIEZACYM KATALOGU')
        try:
            if int(row['progress'])<0: issues.append('UJEMNY POSTEP')
        except (TypeError,ValueError,OverflowError): issues.append('NIEPRAWIDLOWY LICZNIK')
        try:
            if int(row['completion_count'])<0: issues.append('UJEMNA LICZBA UKONCZEN')
        except (TypeError,ValueError,OverflowError): issues.append('NIEPRAWIDLOWE UKONCZENIA')
        if row['status'] not in ('active','completed','abandoned'):
            issues.append('NIETYPOWY STATUS '+str(row['status']))
        if issues:
            out.append(f'{qid}: '+', '.join(issues)+'.')
    return ([f'SKAN QUESTOW {character["name"]}: {len(rows)} zapisow; '
             f'{len(out)} wymagajacych sprawdzenia. Pokazuje do {limit}.']
            +out[:limit]
            +(['Wiecej wpisow: sprawdz kolejne osobno przez admin blad trop NICK QUEST_ID.'] if len(out)>limit else [])
            +['To nie oznacza, ze kazdy wpis jest bledem; skan niczego nie zmienia.'])


def npc_quest(qid):
    quest=QUESTS.get(qid)
    if not quest: raise ValueError('Nieznany QUEST_ID; nie zmieniono swiata.')
    result=[f'NPC QUEST {qid}: {quest.get("name",qid)}.']
    result.append(_npc_info(qid,quest))
    if quest.get('kind')=='deliver_npc':
        target=quest.get('target_npc')
        npc=NPCS.get(target)
        result.append(f'Odbiorca: {npc.get("name",target)} ({target}) w {npc.get("room","?")}. '
                      if npc else f'Brak odbiorcy {target} w aktywnym katalogu NPC.')
    result.append('Podglad bez publikacji i bez zmian w NPC.')
    return result
