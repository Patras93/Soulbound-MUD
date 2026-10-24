# -*- coding: utf-8 -*-
"""v37 Guardian 3: owner-only tools built on canonical OLC and SQLite.

This module does not replace live combat with a fabricated PvE simulation. It
never publishes a DRAFT or grants rewards. Every write is bounded and explicit.
"""
import copy
import json
import math
import sqlite3
import re
import time
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS
from data.rooms import ROOMS
from systems.live_content_v1204 import ID, DIRECTIONS
from systems.admin_guardian2_v3600 import resolve_mob, _number, _audit, _party_members, find_online

HELP = ('ADMIN GUARDIAN3: arena START MOB_ID HP_GRACZA ATAK_GRACZA; arena TURA; arena WYNIK; '
        'arena KONIEC; moc oslonadruzyny POTWIERDZAM (leczenie + ostrzezenie, NIE niewrazliwosc); '
        'kraina plan ID | NAZWA | POZIOM | POKOJE (4-20); kraina tworz ... POTWIERDZAM; '
        'kraina potwor ID_KRAINY MOB_ID | NAZWA | HP | OBRAZENIA | EXP | POKOJ_NR POTWIERDZAM; '
        'kraina npc ID_KRAINY NPC_ID | NAZWA | POKOJ_NR | kupiec/zleceniodawca | DIALOG POTWIERDZAM; '
        'kraina sklep ID_KRAINY POKOJ_NR | ITEM_ID,ITEM_ID POTWIERDZAM; '
        'kraina quest ID_KRAINY QUEST_ID | NAZWA | DAWCA | CEL_MOB | LICZBA | SREBRO POTWIERDZAM; '
        'quest kontrola NICK QUEST_ID; quest korekta NICK QUEST_ID licznik_ukonczen POTWIERDZAM; '
        'quest historia; quest cofnij NUMER POTWIERDZAM; balans raport MOB_ID [DPS]; '
        'event fala MOB_ID POKOJ ILOSC POTWIERDZAM; event raport; '
        'historia ostatnie [ILE]; role raport; status. Wszystkie zmiany zapisu musza byc zatwierdzone.')


def _text(value, n=90):
    value = str(value).strip()
    if not value or len(value)>n or any(ord(c)<32 for c in value):
        raise ValueError('Niepoprawny tekst albo zbyt dlugi argument.')
    return value


def _numeric_meta(meta):
    return (_number(meta.get('max_hp'),1,10**15), _number(meta.get('damage'),1,10**12))


def _arena_start(s, mid, hp, attack):
    meta, origin=resolve_mob(s.server.live_content_v1204,mid)
    if not meta: raise ValueError('Nieznany mob lub DRAFT.')
    mh,damage=_numeric_meta(meta)
    player_hp=_number(hp,1,10**15); player_attack=_number(attack,1,10**15)
    # No persistent or live-world mutation; the fighter is NOT a real Session.
    s.guardian3_arena={'mob':mid,'origin':origin,'enemy_hp':mh,'enemy_max':mh,
        'enemy_damage':damage,'hero_hp':player_hp,'hero_max':player_hp,
        'hero_attack':player_attack,'turn':0,'received':0,'dealt':0,'started':time.monotonic(),
        'damage_type':str(meta.get('damage_type','nieznany'))[:60]}
    return (f'ARENA 3.0: {mid} ({origin}), HP {mh}, obrazenia bazowe {damage}, '
            f'gracz HP {player_hp}, atak {player_attack}. Komenda: admin guardian3 arena tura. '
            'ODIZOLOWANA SYMULACJA liczbowa; NIE wykonuje AI, faz, odpornosci, questow, EXP ani walki sieciowej.')


def _arena_turn(s):
    a=getattr(s,'guardian3_arena',None)
    if not a: raise ValueError('Najpierw uruchom arenę START.')
    if a['enemy_hp']<=0 or a['hero_hp']<=0: return 'ARENA: zakonczona. Wpisz arena wynik.'
    hit=min(a['hero_attack'],a['enemy_hp']);a['enemy_hp']-=hit;a['dealt']+=hit;a['turn']+=1
    incoming=min(a['enemy_damage'],a['hero_hp']) if a['enemy_hp']>0 else 0
    a['hero_hp']-=incoming;a['received']+=incoming
    result=('wygrana' if a['enemy_hp']==0 else 'porażka' if a['hero_hp']==0 else 'walka trwa')
    return (f'ARENA tura {a["turn"]}: trafiasz za {hit}; przeciwnik trafia za {incoming}; '
            f'HP potwora {a["enemy_hp"]}/{a["enemy_max"]}; twoje HP {a["hero_hp"]}/{a["hero_max"]}; {result}. '
            'Model bez realnych skilli/AI i odporności.')


def _arena_report(s):
    a=getattr(s,'guardian3_arena',None)
    if not a: return 'ARENA: nie ma aktywnego testu.'
    rounds_ideal=math.ceil(a['enemy_max']/a['hero_attack'])
    return (f'ARENA {a["mob"]}: {a["turn"]} tur, zadane {a["dealt"]}, otrzymane {a["received"]}; '
            f'pozostale HP {a["enemy_hp"]}, postac {a["hero_hp"]}; '
            f'minimum {rounds_ideal} tur przy stalym ataku, typ obrazen moba {a["damage_type"]}. '
            'To teoria, NIE raport prawdziwej walki ani gwarancja przezycia.')


def _region_spec(parts):
    pieces=[x.strip() for x in ' '.join(parts).split('|')]
    if len(pieces)!=4: raise ValueError('Uzycie: kraina plan/tworz ID | NAZWA | POZIOM | POKOJE [POTWIERDZAM].')
    key,name,level,count=pieces
    if not re.fullmatch(r'[a-z][a-z0-9_]{3,19}',key): raise ValueError('ID krainy: 4-20 malych liter/cyfr/_.')
    return key,_text(name,64),_number(level,1,800),_number(count,4,20)


def _region_ids(key,count):
    return [f'live_{key}_r{i:02}' for i in range(1,count+1)]


def _build_region(service,key,name,level,count):
    ids=_region_ids(key,count)
    if any(not ID.fullmatch(r) or r in ROOMS or r in service.draft['rooms'] for r in ids):
        raise ValueError('Wystepuja zajete ID; wybierz inna nazwe krainy.')
    orig=copy.deepcopy(service.draft)
    # Existing OLC enforces all catalog caps and validates each step.
    try:
        for i,rid in enumerate(ids):
            service.stage_room(rid,min(800,level+(i//5)),f'{name}: sektor {i+1}',
                f'Nowa lokacja krainy {name}, sektor {i+1}.',name)
        for a,b in zip(ids,ids[1:]):
            service.stage_link(a,'east',b);service.stage_link(b,'west',a)
        service.validate(service.draft)
    except Exception:
        service.draft=orig
        raise
    return (f'KRAINA DRAFT {name}: {count} pokoi, {2*(count-1)} przejsc; '
            f'brama {ids[0]}, koniec {ids[-1]}. Aby dodac wejscie z istniejacego swiata: '
            f'admin live polacz STARY_POKOJ KIERUNEK {ids[0]}. Publikacja tylko przez admin live aktywuj POTWIERDZAM.')


def _add_region_mob(service,key,pieces):
    if len(pieces)!=6: raise ValueError('Potwor: MOB_ID | NAZWA | HP | OBRAZENIA | EXP | POKOJ_NR.')
    mobid,name,hp,damage,exp,roomno=pieces
    if not ID.fullmatch(mobid) or mobid in MOB_TEMPLATES or mobid in service.draft['mobs']:
        raise ValueError('Mob musi miec nowe, wolne ID live_.')
    rid=f'live_{key}_r{_number(roomno,1,20):02}'
    if rid not in service.draft['rooms']: raise ValueError('Taki pokoj krainy nie istnieje w DRAFT.')
    old=copy.deepcopy(service.draft)
    try:
        level=int(service.draft['rooms'][rid]['generator_level'])
        service.stage_mob(mobid,_text(name,100),level,_number(hp,1,10**15),
                          _number(damage,1,10**12),_number(exp,1,10**15))
        service.stage_spawn(rid,mobid)
        service.validate(service.draft)
    except Exception:
        service.draft=old
        raise
    return f'KRAINA DRAFT: dodano {mobid} w {rid}; brak aktywacji.'


def _add_region_quest(service,key,pieces):
    if len(pieces)!=6: raise ValueError('Quest: QUEST_ID | NAZWA | DAWCA | CEL_MOB | LICZBA | SREBRO.')
    qid,name,giver,mobid,needed,silver=pieces
    if not ID.fullmatch(qid) or qid in QUESTS or qid in service.draft['quests']:
        raise ValueError('Quest wymaga nowego ID live_.')
    if mobid not in service.draft['mobs'] and mobid not in MOB_TEMPLATES:
        raise ValueError('Najpierw utworz potwora lub wybierz istniejący ID.')
    if f'live_{key}_r01' not in service.draft['rooms']: raise ValueError('Najpierw utworz kraine DRAFT.')
    old=copy.deepcopy(service.draft)
    try:
        giver_name=_text(giver,100)
        service.stage_new_quest(qid,_text(name,100),giver_name,'kill',mobid,
          _number(needed,1,10000),_number(silver,0,10**12),f'Pokonaj wskazane potwory w krainie {key}.')
        # Attach to an explicitly staged quest giver, without hijacking any
        # published or existing NPC's quest slot.
        target_npc=next((n for n in service.draft['npcs'].values()
                         if n.get('name','').casefold()==giver_name.casefold()
                         and n.get('room','').startswith('live_'+key+'_')),None)
        if target_npc is not None:
            if target_npc.get('quest'): raise ValueError('NPC ma juz quest. Nie nadpisuje istniejacej oferty.')
            target_npc['quest']=qid
        service.validate(service.draft)
    except Exception:
        service.draft=old;raise
    return ('QUEST DRAFT: '+qid+'. Jezeli DAWCA to nowy NPC tej krainy, quest przypisano do niego. '
        'Sprawdz jego powiazanie i oferte przed publikacja; brak automatycznego podpinania do NPC.')


def _add_region_npc(service,key,pieces):
    if len(pieces)!=5: raise ValueError('NPC: NPC_ID | NAZWA | POKOJ_NR | ROLA | DIALOG.')
    nid,name,roomno,role,dialogue=pieces
    if not ID.fullmatch(nid) or nid in service.draft['npcs']:
        raise ValueError('NPC wymaga nowego, wolnego ID live_.')
    rid=f'live_{key}_r{_number(roomno,1,20):02}'
    if rid not in service.draft['rooms']: raise ValueError('Pokoj krainy nie istnieje w DRAFT.')
    if role not in ('kupiec','zleceniodawca'): raise ValueError('Rola NPC: kupiec albo zleceniodawca.')
    old=copy.deepcopy(service.draft)
    try:
        service.draft['npcs'][nid]={'name':_text(name,100),'room':rid,
            'dialogue':_text(dialogue,100),'shopkeeper':role=='kupiec'}
        service.validate(service.draft)
    except Exception:
        service.draft=old;raise
    return f'NPC DRAFT: {nid} w {rid} ({role}). Jeden NPC na pokoj; nie opublikowano.'


def _add_region_shop(service,key,pieces):
    from data.items import ITEMS
    if len(pieces)!=2: raise ValueError('Sklep: POKOJ_NR | ITEM_ID,ITEM_ID.')
    roomno,stock=pieces
    rid=f'live_{key}_r{_number(roomno,1,20):02}'
    if rid not in service.draft['rooms']: raise ValueError('Pokoj krainy nie istnieje w DRAFT.')
    goods=[g.strip() for g in stock.split(',')]
    if not 1<=len(goods)<=20 or len(set(goods))!=len(goods) or any(g not in ITEMS and g not in service.draft['items'] for g in goods):
        raise ValueError('Towary: 1-20 unikalnych, istniejacych ID przedmiotow.')
    if not any(n.get('room')==rid and n.get('shopkeeper') is True for n in service.draft['npcs'].values()):
        raise ValueError('Najpierw dodaj w tym pokoju NPC z rola kupiec.')
    old=copy.deepcopy(service.draft)
    try:
        service.draft['shops'][rid]=goods
        service.validate(service.draft)
    except Exception:
        service.draft=old;raise
    return f'SKLEP DRAFT: {rid}, {len(goods)} przedmiotow; nie opublikowano.'


def _quest_completion_problem(db,nick,qid):
    from systems.admin_guardian2_v3600 import _quest_row
    row,quest,saved=_quest_row(type('Shim',(),{'server':type('Srv',(),{'db':db})()})(),nick,qid)
    if not saved: return row,quest,saved,'Brak wiersza aktywnego questa.'
    num=int(saved['completion_count'])
    if num<0 and saved['status']=='active':
        return row,quest,saved,f'BLEDUJACY LICZNIK ukonczen {num}; mozliwa korekta do 0 przy offline.'
    return row,quest,saved,'Brak bezpiecznej korekty licznika. Nie wymuszam zaliczen ani nagrod.'


def _quest_fix_count(s,nick,qid):
    row,quest,saved,note=_quest_completion_problem(s.server.db,nick,qid)
    if not saved or saved['status']!='active' or int(saved['completion_count'])>=0:
        raise ValueError('Brak ujemnego licznika ukonczen aktywnego questa. Nic nie zmieniono.')
    if find_online(s,nick): raise ValueError('Gracz musi byc offline.')
    conn=s.server.db.conn
    conn.execute('''CREATE TABLE IF NOT EXISTS admin_guardian3_quest_fixes(
      id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL,
      quest_id TEXT NOT NULL, old_count INTEGER NOT NULL, new_count INTEGER NOT NULL DEFAULT 0,
      reverted INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    old=int(saved['completion_count'])
    try:
        cur=conn.execute("UPDATE quests SET completion_count=0 WHERE account_id=? AND quest_id=? AND status='active' AND completion_count=?",
          (row['account_id'],qid,old))
        if cur.rowcount!=1: raise ValueError('Stan zmienil sie od podgladu; nie naprawiono.')
        hist=conn.execute('INSERT INTO admin_guardian3_quest_fixes(account_id,quest_id,old_count) VALUES(?,?,?)',(row['account_id'],qid,old))
        conn.commit()
    except Exception:
        conn.rollback();raise
    return f'QUEST KOREKTA #{hist.lastrowid}: {nick} {qid}, ukonczenia {old}->0; brak nagrod, postep bez zmian.'


def _quest_revert(s,number):
    conn=s.server.db.conn
    try: saved=conn.execute('SELECT * FROM admin_guardian3_quest_fixes WHERE id=?',(number,)).fetchone()
    except Exception as exc: raise ValueError('Brak historii korekt v37.') from exc
    if not saved or saved['reverted']: raise ValueError('Nie ma aktywnej korekty pod numerem.')
    if any(x.character and not x.closed and x.account_id==saved['account_id'] for x in s.server.sessions):
        raise ValueError('Gracz musi byc offline.')
    try:
        cur=conn.execute("UPDATE quests SET completion_count=? WHERE account_id=? AND quest_id=? AND status='active' AND completion_count=0",
                         (saved['old_count'],saved['account_id'],saved['quest_id']))
        if cur.rowcount!=1: raise ValueError('Stan zmienil sie po korekcie; nie cofam.')
        conn.execute('UPDATE admin_guardian3_quest_fixes SET reverted=1 WHERE id=?',(number,))
        conn.commit()
    except Exception:
        conn.rollback();raise
    return f'COFNIETO korekte v37 #{number}. Nie dotknieto EXP, zlota ani postepu.'


def _balance(s,mid,player_dps):
    meta,origin=resolve_mob(s.server.live_content_v1204,mid)
    if not meta: raise ValueError('Nieznany mob.')
    hp,damage=_numeric_meta(meta)
    base=MOB_TEMPLATES.get(mid)
    before=(f'poprzednie HP {base.get("max_hp")}, obrazenia {base.get("damage")}; '
            if base else 'nowy mob DRAFT; ')
    if not player_dps:
        return f'BALANS {mid}: {origin}; HP {hp}, bazowe obrazenia {damage}; '+before+'podaj DPS, aby obliczyc scenariusz.'
    dps=_number(player_dps,1,10**15)
    turns=math.ceil(hp/dps)
    # Even rounds don't assert concrete real-time cadence or armor/resistance.
    return (f'BALANS {mid} ({origin}): HP {hp}, bazowe obrazenia {damage}; {before}'
            f' przy hipotetycznych {dps} obrazeniach na ture minimum {turns} tur, '
            f'suma ciosow bossa przy pelnym atakowaniu max {max(0,turns-1)*damage}. '
            'NIE uwzglednia AI, uniku, krytykow, klas, faz ani rzeczywistych czasow.')


async def handle_guardian3(s,raw):
    if not str(raw).casefold().startswith('guardian3'):
        return False
    if not s.is_admin():
        await s.send('GUARDIAN3: tylko wlasciciel-administrator.');return True
    parts=str(raw).strip().split()[1:]
    sub=parts[0].casefold() if parts else 'pomoc'; tail=parts[1:]
    try:
        if sub in ('pomoc','help'):
            await s.send(HELP)
        elif sub=='status':
            await s.send('GUARDIAN3 v37: arena liczbowa; krainy DRAFT; quest korekta offline; eventy limitowane; role diagnostyczne. Brak prawdziwej areny AI/UOSS.')
        elif sub=='arena':
            act=tail[0].casefold() if tail else ''
            if act=='start' and len(tail)==4: await s.send(_arena_start(s,tail[1],tail[2],tail[3]))
            elif act=='tura' and len(tail)==1: await s.send(_arena_turn(s))
            elif act=='wynik' and len(tail)==1: await s.send(_arena_report(s))
            elif act=='koniec' and len(tail)==1:
                s.guardian3_arena=None;await s.send('ARENA ZAMKNIETA. Nic nie zapisano.')
            else: raise ValueError('Arena: start MOB_ID HP_GRACZA ATAK_GRACZA / tura / wynik / koniec.')
        elif sub=='moc':
            if tail==['oslonadruzyny','POTWIERDZAM']:
                members=_party_members(s)
                if not members: raise ValueError('Brak druzyny w pokoju.')
                for x in members:
                    if x.current_hp>0:
                        x.current_hp=x.max_hp();x.current_mana=x.max_mana()
                        await x.send('ADMIN: odnowiono HP i mane. To nie jest niesmiertelnosc.')
                _audit(s,'g3_party_heal',len(members))
                await s.send(f'OSLONA DRUZYNY: uzdrowiono dostepnych czlonkow {len(members)}. '
                             'UWAGA: brak rzeczywistej bariery przeciw ciosom; bossowie normalnie atakuja.')
            else: raise ValueError('Moc: oslonadruzyny POTWIERDZAM. Zamrozenie UOSS pozostaje zablokowane.')
        elif sub=='kraina':
            action=tail[0].casefold() if tail else ''
            if action in ('plan','tworz'):
                confirm=tail[-1]=='POTWIERDZAM' if tail else False
                spec=tail[1:-1] if action=='tworz' and confirm else tail[1:]
                key,name,lv,cnt=_region_spec(spec)
                if action=='plan': await s.send(f'PLAN DRAFT: {name}, lvl {lv}, {cnt} pokoi, {2*(cnt-1)} przejsc. Nic nie zapisano.')
                else:
                    if not confirm: raise ValueError('Dodaj na koncu POTWIERDZAM.')
                    await s.send(_build_region(s.server.live_content_v1204,key,name,lv,cnt));_audit(s,'g3_region',key)
            elif action in ('potwor','quest','npc','sklep'):
                if len(tail)<4 or tail[-1]!='POTWIERDZAM': raise ValueError('Wymagane ID krainy, pola oddzielone | i POTWIERDZAM.')
                key=tail[1]
                if not re.fullmatch(r'[a-z][a-z0-9_]{3,19}',key): raise ValueError('Bledne ID krainy.')
                pieces=[_text(x.strip(),100) for x in ' '.join(tail[2:-1]).split('|')]
                if action=='potwor': msg=_add_region_mob(s.server.live_content_v1204,key,pieces)
                elif action=='quest': msg=_add_region_quest(s.server.live_content_v1204,key,pieces)
                elif action=='npc': msg=_add_region_npc(s.server.live_content_v1204,key,pieces)
                else: msg=_add_region_shop(s.server.live_content_v1204,key,pieces)
                await s.send(msg);_audit(s,'g3_region_'+action,key)
            else: raise ValueError('Kraina: plan/tworz ID | NAZWA | LEVEL | POKOJE [POTWIERDZAM]; potwor/npc/sklep/quest ID_KRAINY ... POTWIERDZAM.')
        elif sub=='quest':
            action=tail[0].casefold() if tail else ''
            if action=='kontrola' and len(tail)==3:
                row,meta,saved,note=_quest_completion_problem(s.server.db,tail[1],tail[2])
                await s.send(f'QUEST {tail[1]} {tail[2]}: '+note)
            elif action=='korekta' and len(tail)==5 and tail[3]=='licznik_ukonczen' and tail[4]=='POTWIERDZAM':
                msg=_quest_fix_count(s,tail[1],tail[2]);_audit(s,'g3_quest_fix',tail[1]+'/'+tail[2]);await s.send(msg)
            elif action=='cofnij' and len(tail)==3 and tail[2]=='POTWIERDZAM':
                msg=_quest_revert(s,_number(tail[1],1,2**31-1));_audit(s,'g3_quest_undo',tail[1]);await s.send(msg)
            elif action=='historia' and len(tail)==1:
                try: rows=s.server.db.conn.execute('SELECT id,quest_id,old_count,reverted FROM admin_guardian3_quest_fixes ORDER BY id DESC LIMIT 15').fetchall()
                except sqlite3.OperationalError: rows=[]
                await s.send('QUEST HISTORIA v37: '+('; '.join(f'{x["id"]} {x["quest_id"]} {x["old_count"]}->0 cofnięto:{x["reverted"]}' for x in rows) if rows else 'brak.'))
            else: raise ValueError('Quest: kontrola NICK ID / korekta NICK ID licznik_ukonczen POTWIERDZAM / historia / cofnij NUMER POTWIERDZAM.')
        elif sub=='balans':
            if len(tail)<2 or tail[0].casefold()!='raport': raise ValueError('Balans: raport MOB_ID [OBRAZENIA_NA_TURE].')
            await s.send(_balance(s,tail[1],tail[2] if len(tail)>2 else None))
        elif sub=='event':
            action=tail[0].casefold() if tail else ''
            if action=='raport':
                events=getattr(s.server,'guardian_events_v3600',{})
                live_spawns=getattr(s.server,'guardian_spawns_v3600',{})
                await s.send('EVENTY AKTYWNE: '+(', '.join(f'{eid} {ev["room"]} {len(ev["keys"])} mobow' for eid,ev in events.items()) if events else 'brak.')+f' Tymczasowe instancje lacznie: {len(live_spawns)}.')
            elif action=='fala' and len(tail)==5 and tail[-1]=='POTWIERDZAM':
                # Reuse the existing guarded session-spawn path, no parallel handler.
                mob,room,count=tail[1:4]
                before=len(getattr(s.server,'guardian_spawns_v3600',{}))
                await s.admin_command('guardian spawn staw '+mob+' '+room+' '+count+' POTWIERDZAM')
                after=len(getattr(s.server,'guardian_spawns_v3600',{}))
                if after>before:
                    _audit(s,'g3_wave',f'{mob}@{room}x{after-before}')
                    await s.send('FALA URUCHOMIONA: usun instancje po wydarzeniu przez admin spawn moje / admin spawn usun KLUCZ POTWIERDZAM. Nie sa automatycznie usuwane po czasie.')
            else: raise ValueError('Event: raport / fala MOB_ID POKOJ ILOSC POTWIERDZAM (istniejace zabezpieczenia spawnu).')
        elif sub=='historia':
            if not tail or tail[0].casefold()!='ostatnie': raise ValueError('Historia: ostatnie [ILE].')
            n=_number(tail[1] if len(tail)>1 else '15',1,30)
            rows=s.server.db.conn.execute('SELECT id,created_at,action,target FROM admin_actions_v1224 ORDER BY id DESC LIMIT ?',(n,)).fetchall()
            await s.send('HISTORIA v37: '+('; '.join(f'{x["id"]} {x["action"]} {x["target"]}' for x in rows) if rows else 'brak.'))
        elif sub=='role':
            if tail!=['raport']: raise ValueError('Role: raport. Nadawanie przez admin role nadaj ... POTWIERDZAM.')
            try: rows=s.server.db.conn.execute('SELECT role,COUNT(*) AS n FROM admin_guardian_roles_v3600 GROUP BY role ORDER BY role').fetchall()
            except sqlite3.OperationalError: rows=[]
            await s.send('ROLE v37: '+(', '.join(f'{x["role"]} {x["n"]}' for x in rows) if rows else 'brak delegacji.'))
        else: raise ValueError(HELP)
    except (ValueError,TypeError,KeyError,OverflowError,AttributeError) as exc:
        await s.send('GUARDIAN3: '+str(exc)[:350])
    return True
