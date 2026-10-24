# -*- coding: utf-8 -*-
"""Admin Guardian 2.0. Conservative owner controls with isolated simulations.

No arena rewards or mutations of characters, quests, real mob instances or OLC
active content. Real-game interventions reuse pre-existing guarded commands.
"""
import copy
import json
import re
import sqlite3
import time
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS
from data.rooms import ROOMS
from systems.live_content_v1204 import ID, DIRECTIONS

ROLE_ORDER = ('pomocnik', 'moderator', 'administrator')
TUTORIAL = (
    'admin guardian pomoc: test, moc, ratunek, wsparcie, spawn, event, '
    'kraina, balans, panel, questdiag, questnapraw, historia, role. '
    'Komendy nieopublikowanych mobow na arenie nie daja EXP ani przedmiotow.'
)


def ensure_roles(db):
    db.conn.execute('''CREATE TABLE IF NOT EXISTS admin_guardian_roles_v3600 (
        account_id INTEGER PRIMARY KEY, role TEXT NOT NULL CHECK(role IN
        ('pomocnik','moderator','administrator')), granted_by TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
    db.conn.commit()


def find_online(session, nick):
    if not nick or len(nick) > 80:
        return None
    candidate = session.server.find_character_session(nick)
    return candidate if candidate and not candidate.closed and candidate.character and candidate.character.name.casefold() == nick.casefold() else None


def resolve_mob(service, mid):
    """DRAFT has priority; never add its template to the live catalog."""
    if mid in service.draft.get('mobs', {}):
        return copy.deepcopy(service.draft['mobs'][mid]), 'DRAFT'
    if mid in MOB_TEMPLATES:
        meta = copy.deepcopy(MOB_TEMPLATES[mid]); edits = service.draft.get('mob_edits', {}).get(mid, {})
        if isinstance(edits, dict):
            meta.update(copy.deepcopy(edits))
        balance = service.draft.get('balances', {}).get(mid, {})
        if isinstance(balance, dict):
            meta.update(copy.deepcopy(balance))
        return meta, 'DRAFT' if edits or balance else 'OPUBLIKOWANY'
    return None, ''


def safe_text(s, n=90):
    s = str(s or '').strip()
    if not s or len(s)>n or any(ord(c)<32 for c in s):
        raise ValueError('Niepoprawny tekst lub za dlugi argument.')
    return s


def _number(s, low, high):
    try: v = int(s)
    except (ValueError, TypeError) as exc: raise ValueError('Wymagana liczba calkowita.') from exc
    if not low<=v<=high: raise ValueError(f'Zakres {low} do {high}.')
    return v


def mob_summary(meta):
    return (f"{meta.get('name','mob')}: poziom {meta.get('generator_level','?')}, "
            f"HP {meta.get('max_hp','?')}, obrazenia {meta.get('damage','?')}, "
            f"EXP {meta.get('class_xp_reward',meta.get('xp','?'))}.")


def arena_start(s, mid):
    meta, origin = resolve_mob(s.server.live_content_v1204, mid)
    if not meta: raise ValueError('Nieznany ID potwora. Najpierw utworz go w admin live.')
    hp = _number(meta.get('max_hp', 0),1,10**15)
    damage = _number(meta.get('damage', 0),1,10**12)
    s.guardian_arena_v3600 = {'id':mid, 'origin':origin, 'meta':meta, 'hp':hp,
        'max_hp':hp,'enemy_damage':damage,'turns':0,'dealt':0,'received':0,'began':time.monotonic()}
    return f"ARENA TESTOWA {origin}: {mob_summary(meta)} Brak nagrod i skutkow w prawdziwej grze. admin test atak [OBRAZENIA]."


def arena_hit(s, value):
    state = getattr(s,'guardian_arena_v3600',None)
    if not state: raise ValueError('Brak areny. Uzyj admin test arena mob ID.')
    if state['hp'] <= 0: return 'ARENA: mob juz pokonany. admin test wynik.'
    damage = _number(value,1,10**15)
    actual = min(damage,state['hp'])
    state['hp'] -= actual
    state['turns'] += 1
    state['dealt'] += actual
    state['received'] += state['enemy_damage'] if state['hp'] else 0
    return (f"ARENA, TURA {state['turns']}: zadano {actual}, HP przeciwnika {state['hp']}/{state['max_hp']}; "
      f"obrazenia potwora modelowo {state['enemy_damage']}. "
      "Nie symulowano realnych faz, odpornosci, AI, pancerza ani druzyny.")


def arena_report(s):
    a = getattr(s, 'guardian_arena_v3600', None)
    if not a: return 'Brak aktywnego raportu areny.'
    return (f"ARENA {a['id']}: {a['origin']}; tur {a['turns']}; zadano {a['dealt']}; "
     f"symulowane obrazenia wroga {a['received']}; pozostalo HP {a['hp']}/{a['max_hp']}. "
     'To symulacja liczbowa, nie test realnych umiejetnosci lub dropow.')


def _party_members(s):
    if not s.character or s.party_key() is None:
        return []
    room = s.character.room_id
    return [p for p in s.server.sessions if p.character and not p.closed
            and p.party_key() == s.party_key() and p.character.room_id == room]


def _audit(s, action, target=''):
    s.server.db.record_admin_action_v1224(
        s.server.db.account_name(s.master_account_id), 'g2_'+action, str(target)[:96])


def _staged_region(s, region_id, name, lower, upper):
    from systems.live_content_v1204 import ID as ROOM_ID
    key = 'live_'+region_id
    if not ROOM_ID.fullmatch(key): raise ValueError('Id krainy: 4-30 malych liter/cyfr/_.')
    service = s.server.live_content_v1204
    ids = [key+'_brama',key+'_szlak',key+'_ruiny']
    if any(not ROOM_ID.fullmatch(r) or r in ROOMS or r in service.draft['rooms'] for r in ids):
        raise ValueError('Id pokoi zajete lub niepoprawne. Wybierz inna nazwe krainy.')
    old = copy.deepcopy(service.draft)
    try:
        for rid,lv,nm,desc in zip(ids,(lower,(lower+upper)//2,upper),
                        ('Brama','Szlak','Ruiny'),
                        ('Wejscie do nowej krainy.','Sciezka przez nieznany teren.','Zabytkowe ruiny.')):
            service.stage_room(rid,lv,f'{nm} - {name}',desc,name)
        service.stage_link(ids[0],'north',ids[1]); service.stage_link(ids[1],'south',ids[0])
        service.stage_link(ids[1],'east',ids[2]); service.stage_link(ids[2],'west',ids[1])
    except (ValueError, TypeError):
        service.draft=old
        raise
    return (f"KRAINA DRAFT: {name}; pokoje {', '.join(ids)}. "
       'Bez NPC i potworow; dodaj je przez admin live. Polacz brame z istniejacym swiatem, '
       'a nastepnie admin live sprawdz / porownaj / aktywuj POTWIERDZAM.')


def _role(s, nick):
    row=s.server.db.conn.execute(
        'SELECT role FROM admin_guardian_roles_v3600 r JOIN accounts a ON a.id=r.account_id '
        'WHERE a.username=? COLLATE NOCASE',(nick,)).fetchone()
    return str(row['role']) if row else 'gracz'


def _quest_row(s, nick, qid):
    row=s.server.db.conn.execute('SELECT account_id,name FROM characters WHERE name=? COLLATE NOCASE',(nick,)).fetchone()
    if not row: raise ValueError('Nieznany nick. Podaj dokladna nazwe postaci.')
    quest=QUESTS.get(qid)
    if not quest: raise ValueError('Nieznany ID questa.')
    saved=s.server.db.quest(int(row['account_id']),qid)
    return row,quest,saved


def _quest_data(s, nick, qid):
    row, quest, saved=_quest_row(s,nick,qid)
    if not saved: return f"QUEST {row['name']} {qid}: nieprzyjety. Brak automatycznej zmiany."
    state='BLEDNY UJEMNY POSTEP: MOZLIWA NAPRAWA DO ZERO TYLKO OFFLINE.' if saved['status']=='active' and int(saved['progress'])<0 else 'Brak jednoznacznej, automatycznej naprawy.'
    return (f"QUEST {row['name']} {qid}: status {saved['status']}, postep {saved['progress']}, "
       f"cel {quest.get('needed','?')}, zakonczono {saved['completion_count']} razy; " + state)


def _quest_repair(s, nick, qid):
    row, quest, saved=_quest_row(s,nick,qid)
    if not saved or saved['status']!='active' or int(saved['progress'])>=0:
        raise ValueError('Brak jednoznacznie blednego ujemnego postepu. Nic nie zmieniono.')
    if find_online(s,nick): raise ValueError('Gracz musi byc offline podczas korekty postepu.')
    conn=s.server.db.conn
    conn.execute('''CREATE TABLE IF NOT EXISTS admin_guardian_quest_repairs_v3600(
      id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL,
      quest_id TEXT NOT NULL, before_progress INTEGER NOT NULL,
      fixed_progress INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      reverted INTEGER NOT NULL DEFAULT 0)''')
    conn.commit()
    old=int(saved['progress'])
    cursor=conn.execute("UPDATE quests SET progress=0 WHERE account_id=? AND quest_id=? AND status='active' AND progress=?",
       (row['account_id'],qid,old))
    if cursor.rowcount!=1:
        conn.rollback(); raise ValueError('Stan questa ulegl zmianie. Sprobuj ponownie diagnostyke.')
    cur=conn.execute('INSERT INTO admin_guardian_quest_repairs_v3600(account_id,quest_id,before_progress,fixed_progress) VALUES (?,?,?,0)',(row['account_id'],qid,old))
    conn.commit()
    return f"QUESTNAPRAW: numer korekty {cur.lastrowid}; {row['name']} {qid} postep {old}->0. Pozostale pola i nagrody bez zmian."


def _quest_revert(s, repair_id):
    conn=s.server.db.conn
    try:
        row=conn.execute('SELECT * FROM admin_guardian_quest_repairs_v3600 WHERE id=?',(repair_id,)).fetchone()
    except sqlite3.OperationalError as exc:
        raise ValueError('Brak historii korekt questu. Nic nie zmieniono.') from exc
    if not row or row['reverted']: raise ValueError('Nie ma aktywnej korekty o takim ID.')
    cid,qid=row['account_id'],row['quest_id']
    online=next((x for x in s.server.sessions if x.character and not x.closed and x.account_id==cid),None)
    if online: raise ValueError('Gracz musi byc offline przed wycofaniem korekty.')
    cursor=conn.execute("UPDATE quests SET progress=? WHERE account_id=? AND quest_id=? AND status='active' AND progress=?",
        (row['before_progress'],cid,qid,row['fixed_progress']))
    if cursor.rowcount!=1:
        conn.rollback(); raise ValueError('Stan questa od korekty sie zmienil; nie mozna bezpiecznie cofnac.')
    conn.execute('UPDATE admin_guardian_quest_repairs_v3600 SET reverted=1 WHERE id=?',(repair_id,))
    conn.commit()
    return f'COFNIETO KOREKTE QUEST #{repair_id}. Przywrocono tylko poprzedni postep.'


def _event_catalog():
    # Fixed, reviewed base templates; never DRAFT and never UOSS.
    return {'inwazja': [('bandit', 3)], 'najazd': [('bandit_captain', 1)],
            'manewry': [('temple_rat', 3)]}


async def _event_expiration(server, event_name, keys):
    import asyncio
    await asyncio.sleep(1800)
    for _ in range(40):
        if not any((server.world.mobs.get(k) and
                    (server.world.mobs[k].engaged_by or server.world.mobs[k].aoe_engaged_by))
                   for k in keys):
            break
        await asyncio.sleep(30)
    else:
        # Never silently despawn a monster in combat.
        return
    for k in keys:
        server.world.mobs.pop(k, None)
        getattr(server, 'guardian_spawns_v3600', {}).pop(k, None)
    getattr(server, 'guardian_events_v3600', {}).pop(event_name, None)
    server.world._last_refresh_at = 0


def _resolve_source_event(event_id):
    from world.world_state import v0290_active_world_events
    for idx, ev in enumerate(v0290_active_world_events()):
        if str(ev.get('id',idx)) == event_id:
            return ev
    return None


async def handle_guardian(s, raw):
    """Return True only for this command subtree; no privilege bypass for old admin."""
    if not str(raw).casefold().startswith('guardian'):
        return False
    args=str(raw).strip().split()[1:]
    sub=args[0].casefold() if args else 'pomoc'
    tail=args[1:]
    db=s.server.db
    ensure_roles(db)
    owner=s.is_admin()
    assigned = _role(s, db.account_name(s.master_account_id)) if s.master_account_id is not None else 'gracz'
    delegate_rights={'pomocnik':{'pomoc','status'},
        'moderator':{'pomoc','status','panel','balans'},
        'administrator':{'pomoc','status','panel','balans','questdiag'}}
    if not owner and sub not in delegate_rights.get(assigned, set()):
        await s.send('Brak uprawnien Admin Guardian.'); return True
    try:
        if sub in ('pomoc','help'):
            await s.send(TUTORIAL)
        elif sub == 'status':
            await s.send(f'GUARDIAN: rola {"wlasciciel" if owner else assigned}; GOD {"ON" if getattr(s,"admin_god_v35005",False) else "OFF"}; arena {"TAK" if getattr(s,"guardian_arena_v3600",None) else "NIE"}; wsparcie {"ON" if getattr(s,"guardian_support_v3600",False) else "OFF"}.')
        elif sub == 'test':
            act=tail[0].casefold() if tail else 'status'
            if act=='arena' and len(tail)==3 and tail[1].casefold() in ('mob','boss'):
                await s.send(arena_start(s,tail[2]))
            elif act=='atak':
                if len(tail)!=2: raise ValueError('Uzycie: admin guardian test atak OBRAZENIA (liczba).')
                await s.send(arena_hit(s,tail[1]))
            elif act=='skill': await s.send('ARENA SKILL: odwzorowanie realnego skilla niedostepne. Uzyj liczbowej symulacji admin test atak LICZBA.')
            elif act in ('wynik','status'): await s.send(arena_report(s))
            elif act in ('wyjdz','koniec'):
                s.guardian_arena_v3600=None; await s.send('ARENA ZAMKNIETA. Brak zmian w grze.')
            else: raise ValueError('Uzycie: admin guardian test arena mob/boss ID; atak LICZBA; wynik; wyjdz.')
        elif sub == 'moc':
            act=tail[0].casefold() if tail else ''
            if act=='tarcza':
                await s.send('TARCZA: '+ ('GOD juz chroni twoja postac.' if getattr(s,'admin_god_v35005',False) else 'Najpierw wlacz admin god on.'))
            elif act in ('leczenie','wskrzeszenie'):
                members=_party_members(s)
                if not members: raise ValueError('Brak twojej druzyny w tym samym pokoju.')
                for member in members:
                    if act=='leczenie' and member.current_hp>0:
                        member.current_hp=member.max_hp(); member.current_mana=member.max_mana()
                        await member.send('ADMIN GUARDIAN: uzdrowiono cie.')
                    elif act=='wskrzeszenie' and (member.current_hp<=0 or member.is_downed_v0371()):
                        member.clear_downed_v0371(cancel_task=True)
                        member.server.release_all_engagements_for_session(member)
                        member.combat_mob_key=None; await member.stop_realtime_combat()
                        member.current_hp=member.max_hp(); member.current_mana=member.max_mana()
                        await member.send('ADMIN GUARDIAN: wskrzeszono cie.')
                _audit(s,'moc_'+act,','.join(m.character.name for m in members))
                await s.send(f'MOC {act}: obsluzono {len(members)} czlonkow druzyny w pokoju.')
            elif act in ('meteor','furia'):
                # Delegate to the existing canonical kill/reward path; no duplicate mob death.
                await s.admin_unique_strike_v35005(('nawalnica' if act=='meteor' else 'wyrok') + ' ' + ' '.join(tail[1:]))
                _audit(s,'moc_'+act)
            elif act=='zamroz':
                await s.send('ZAMROZENIE: niedostepne w prawdziwej walce; silnik nie ma bezpiecznego kontrolera odpornego na UOSS. Brak zmian.')
            else: raise ValueError('Moc: tarcza, leczenie, wskrzeszenie, meteor, furia, zamroz.')
        elif sub == 'ratunek':
            if len(tail)<2: raise ValueError('Uzycie: admin guardian ratunek NICK status/ulecz/wskrzes/do_mnie/do_swiatyni [POTWIERDZAM].')
            nick,act=tail[0],tail[1].casefold()
            target=find_online(s,nick)
            if act=='status':
                if not target: raise ValueError('Gracz musi byc online.')
                await s.send(f'RATUNEK: {target.character.name}, {target.character.room_id}, HP {target.current_hp}/{target.max_hp()}, walka {bool(target.combat_mob_key)}.')
            elif act in ('ulecz','wskrzes','do_mnie','do_swiatyni'):
                if not target: raise ValueError('Gracz musi byc online.')
                if len(tail)!=3 or tail[2]!='POTWIERDZAM':
                    raise ValueError(f'Potwierdz: admin guardian ratunek {nick} {act} POTWIERDZAM.')
                mapped={'ulecz':'ulecz','wskrzes':'wskrzes','do_mnie':'przywolaj','do_swiatyni':'odbuguj'}[act]
                await s.admin_tools_v1224(f'{mapped} {target.character.name} POTWIERDZAM')
            else: raise ValueError('Ratunek: status/ulecz/wskrzes/do_mnie/do_swiatyni.')
        elif sub == 'wsparcie':
            act=tail[0].casefold() if tail else 'status'
            if act in ('on','off'):
                if act=='on' and not _party_members(s): raise ValueError('Dolacz najpierw do druzyny.')
                s.guardian_support_v3600=act=='on'; _audit(s,'wsparcie_'+act)
            elif act not in ('status','raport'): raise ValueError('Wsparcie: on/off/status/raport.')
            members=_party_members(s)
            if not members: s.guardian_support_v3600=False
            await s.send(f'WSPARCIE: {"ON" if getattr(s,"guardian_support_v3600",False) else "OFF"}; wspollokatorow z druzyny {len(members)}. Normalny system EXP i zwyciestw bez zmian.')
        elif sub=='spawn':
            act=tail[0].casefold() if tail else ''
            mid=tail[1] if len(tail)>1 else ''
            created=getattr(s.server,'guardian_spawns_v3600',{})
            if act=='moje':
                await s.send('SPAWN: '+(', '.join(f'{k}:{v}' for k,v in created.items()) or 'brak'))
            elif act=='podglad':
                if mid not in MOB_TEMPLATES: raise ValueError('Nieznany opublikowany mob.')
                await s.send('SPAWN PODGLAD: '+mob_summary(MOB_TEMPLATES[mid])+f' Pokoj {tail[2] if len(tail)>2 else s.character.room_id}.')
            elif act=='usun':
                if len(tail)!=3 or tail[2]!='POTWIERDZAM': raise ValueError('Potwierdz: admin guardian spawn usun KLUCZ POTWIERDZAM.')
                if mid not in created: raise ValueError('Brak instancji administracyjnej o tym kluczu.')
                if ':event:' in mid: raise ValueError('Mob eventowy: zarzadzaj przez admin event zakoncz ID POTWIERDZAM.')
                mob=s.server.world.mobs.get(mid)
                if mob and mob.engaged_by: raise ValueError('Mob walczy. Nie usuwam aktywnego przeciwnika.')
                s.server.world.mobs.pop(mid,None); created.pop(mid,None); s.server.world._last_refresh_at=0
                _audit(s,'spawn_usun',mid); await s.send('SPAWN usuniety bez zmian respawn katalogu.')
            elif act=='staw':
                if len(tail)!=5 or tail[-1]!='POTWIERDZAM': raise ValueError('Uzycie: admin guardian spawn staw MOB_ID POKOJ ILOSC POTWIERDZAM.')
                rid=tail[2]; count=_number(tail[3],1,5)
                if rid not in ROOMS or mid not in MOB_TEMPLATES: raise ValueError('Wymagany istniejacy pokoj i opublikowany mob.')
                if rid=='temple' or sum(1 for member in s.server.sessions if member.character and member.character.room_id==rid)>0:
                    raise ValueError('Nie spawnuje w swiatyni ani pokojach graczy.')
                if len(created)+count>20: raise ValueError('Limit 20 tymczasowych mobow administracyjnych.')
                from world.world_state import MobState
                spawned=[]
                for _ in range(count):
                    seq=getattr(s.server,'guardian_seq_v3600',0)+1; s.server.guardian_seq_v3600=seq
                    key=f'guardian3600:{seq}'
                    mob=MobState(key=key,room_id=rid,template_id=mid,hp=int(MOB_TEMPLATES[mid]['max_hp']),home_room_id=rid)
                    s.server.world.mobs[key]=mob; created[key]=mid; spawned.append(key)
                s.server.guardian_spawns_v3600=created; s.server.world._last_refresh_at=0
                _audit(s,'spawn_staw',f'{mid}@{rid}x{count}'); await s.send(f'SPAWN: {", ".join(spawned)}. Zniknie po restarcie. Usun: admin guardian spawn usun KLUCZ POTWIERDZAM.')
            else: raise ValueError('Spawn: podglad MOB_ID [POKOJ]; staw MOB_ID POKOJ ILOSC POTWIERDZAM; moje; usun KLUCZ POTWIERDZAM.')
        elif sub=='event':
            act=tail[0].casefold() if tail else ''
            events=getattr(s.server,'guardian_events_v3600',{})
            catalog=_event_catalog()
            if act=='katalog':
                await s.send('EVENTY RECZNE: '+', '.join(f"{name} ({', '.join(x[0] for x in troops)})" for name,troops in catalog.items())+'. Pokoj bez graczy; czas 30 min.')
            elif act=='status':
                await s.send('EVENTY ADMINA: '+ ('; '.join(f"{k}:{v['room']}" for k,v in events.items()) if events else 'brak.'))
            elif act=='podglad' and len(tail)==2:
                spec=catalog.get(tail[1])
                if not spec: raise ValueError('Nieznany event. admin event katalog.')
                await s.send('EVENT PODGLAD: '+tail[1]+': '+str(spec)+'. Prawdziwe walki, normalny EXP, bez UOSS.')
            elif act=='start':
                if len(tail)!=4 or tail[3]!='POTWIERDZAM':
                    raise ValueError('Event: start ID POKOJ POTWIERDZAM.')
                event_id,rid=tail[1:3]
                if event_id not in catalog or event_id in events: raise ValueError('Nieznany lub aktywny event.')
                if rid not in ROOMS or rid=='temple': raise ValueError('Wybierz istniejacy pokoj poza swiatynia.')
                if any(p.character and p.character.room_id==rid for p in s.server.sessions):
                    raise ValueError('W pokoju sa gracze. Wybierz pusta lokacje.')
                spawns=getattr(s.server,'guardian_spawns_v3600',{})
                troop=catalog[event_id]
                if not all(mid in MOB_TEMPLATES for mid,count in troop): raise ValueError('Niekompletny katalog eventu.')
                if len(spawns)+sum(x[1] for x in troop)>20: raise ValueError('Przekroczony limit 20 sesyjnych mobow.')
                from world.world_state import MobState
                keys=[]
                for mid,count in troop:
                    for _ in range(count):
                        seq=getattr(s.server,'guardian_seq_v3600',0)+1; s.server.guardian_seq_v3600=seq
                        key=f'guardian3600:event:{seq}'
                        s.server.world.mobs[key]=MobState(key=key,room_id=rid,template_id=mid,
                            hp=int(MOB_TEMPLATES[mid]['max_hp']),home_room_id=rid)
                        spawns[key]=mid;keys.append(key)
                events[event_id]={'room':rid,'keys':keys,'started':time.time()}
                s.server.guardian_events_v3600=events;s.server.guardian_spawns_v3600=spawns
                s.server.world._last_refresh_at=0
                import asyncio
                asyncio.create_task(_event_expiration(s.server,event_id,keys))
                _audit(s,'event_start',event_id+'@'+rid)
                await s.server.broadcast_all(f'WYDARZENIE ADMINA: {event_id} w {ROOMS[rid].get("name",rid)}. Potwory beda dostepne przez maksymalnie 30 minut poza walka.')
                await s.send('EVENT URUCHOMIONY: '+event_id+'. Walki i nagrody odbywaja sie normalnie.')
            elif act=='zakoncz':
                if len(tail)!=3 or tail[2]!='POTWIERDZAM': raise ValueError('Event: zakoncz ID POTWIERDZAM.')
                event_id=tail[1]; ev=events.get(event_id)
                if not ev: raise ValueError('Brak aktywnego eventu.')
                if any(s.server.world.mobs.get(k) and (s.server.world.mobs[k].engaged_by or s.server.world.mobs[k].aoe_engaged_by) for k in ev['keys']):
                    raise ValueError('Wydarzenie trwa w walce; zakończ później.')
                for k in ev['keys']:
                    s.server.world.mobs.pop(k,None)
                    getattr(s.server,'guardian_spawns_v3600',{}).pop(k,None)
                events.pop(event_id,None);s.server.world._last_refresh_at=0
                _audit(s,'event_stop',event_id)
                await s.send('EVENT ZAKONCZONY. Usunieto tylko instancje administracyjne.')
            else: raise ValueError('Event: katalog / podglad ID / status / start ID POKOJ POTWIERDZAM / zakoncz ID POTWIERDZAM.')
        elif sub=='kraina':
            act=tail[0].casefold() if tail else ''
            if act=='nowa':
                spec=' '.join(tail[1:]).split('|')
                if len(spec)!=4: raise ValueError('Kraina: nowa id | Nazwa | MinLevel | MaxLevel.')
                key,name=safe_text(spec[0],30),safe_text(spec[1],60)
                low,high=_number(spec[2],1,800),_number(spec[3],1,800)
                if high<low: raise ValueError('Maksymalny poziom mniejszy od minimalnego.')
                await s.send(_staged_region(s,key,name,low,high)); _audit(s,'kraina_draft',key)
            elif act in ('status','sprawdz') and len(tail)==2:
                key='live_'+tail[1]+'_'
                srv=s.server.live_content_v1204
                ids=sorted(r for r in srv.draft['rooms'] if r.startswith(key))
                if not ids: raise ValueError('Nie ma takiej krainy DRAFT.')
                srv.validate(srv.draft)
                await s.send(f'KRAINA DRAFT: {len(ids)} pokoi; {", ".join(ids)}. Publikacja tylko przez admin live aktywuj POTWIERDZAM.')
            elif act=='anuluj':
                await s.send('Bezpieczne anulowanie: admin live wczytaj / cofnij wg statusu roboczego; automatyczne kasowanie wspolnego DRAFT wstrzymane.')
            else: raise ValueError('Kraina: nowa ID | NAZWA | MIN | MAX; status ID; sprawdz ID.')
        elif sub=='balans':
            act=tail[0].casefold() if tail else ''
            if act in ('mob','boss','porownaj','druzyna') and len(tail)>=2:
                mid=tail[1]; service=s.server.live_content_v1204
                meta,origin=resolve_mob(service,mid)
                if not meta: raise ValueError('Nieznany mob.')
                await s.send(f'BALANS {origin}: '+mob_summary(meta))
                if act=='porownaj' and mid in MOB_TEMPLATES:
                    await s.send('PRZED ZMIANA: '+mob_summary(MOB_TEMPLATES[mid]))
                if act=='druzyna':
                    n=_number(tail[2] if len(tail)>2 else '1',1,5)
                    await s.send(f'DRUZYNA {n}: brak wiarygodnej estymacji tur bez leveli, skilli i EQ. Uruchom oddzielna arene.')
            else: raise ValueError('Balans: mob/boss ID; porownaj ID; druzyna ID LICZBA.')
        elif sub=='panel':
            if not tail: raise ValueError('Panel: NICK [questy/profesje/eq/lokalizacja].')
            nick=tail[0]; row=db.conn.execute('SELECT account_id,name,character_level,room_id FROM characters WHERE name=? COLLATE NOCASE',(nick,)).fetchone()
            if not row: raise ValueError('Nie znaleziono postaci.')
            view=tail[1].casefold() if len(tail)>1 else 'status'
            if view in ('status','lokalizacja'):
                await s.send(f'PANEL {row["name"]}: poziom {row["character_level"]}; lokacja {row["room_id"]}; rola {_role(s,db.account_name(row["account_id"]))}. Tylko odczyt.')
            elif view=='questy':
                rows=db.quest_rows(row['account_id']); await s.send(f'PANEL QUESTY {nick}: {len(rows)} wpisow; pierwsze '+', '.join(f"{r['quest_id']}:{r['status']}" for r in rows[:15]))
            elif view=='profesje':
                rows=db.conn.execute('SELECT profession,level FROM professions WHERE account_id=? ORDER BY profession',(row['account_id'],)).fetchall()
                await s.send('PANEL PROFESJE: '+', '.join(f"{r['profession']}:{r['level']}" for r in rows[:22]))
            elif view=='eq':
                await s.admin_tools_v1224('eq '+row['name'])
            else: raise ValueError('Widoki: status/lokalizacja/questy/profesje/eq.')
        elif sub in ('questdiag','questnapraw'):
            if len(tail)<2: raise ValueError('Quest: NICK ID [podglad/synchronizuj POTWIERDZAM].')
            if sub=='questnapraw' and len(tail)>=3 and tail[2]=='synchronizuj':
                if len(tail)!=4 or tail[3]!='POTWIERDZAM': raise ValueError(f'Potwierdz: admin questnapraw {tail[0]} {tail[1]} synchronizuj POTWIERDZAM.')
                result=_quest_repair(s,tail[0],tail[1]);_audit(s,'quest_repair',tail[0]+'/'+tail[1]);await s.send(result);return True
            await s.send(_quest_data(s,tail[0],tail[1]))
        elif sub=='historia':
            act=tail[0].casefold() if tail else 'ostatnie'
            if act in ('ostatnie','olc'):
                lim=_number(tail[1] if len(tail)>1 else '10',1,30)
                q="SELECT id,created_at,action,target FROM admin_actions_v1224 "
                if act=='olc': q+="WHERE action LIKE 'live_%' "
                rows=db.conn.execute(q+'ORDER BY id DESC LIMIT ?',(lim,)).fetchall()
                for r in rows: await s.send(f"{r['id']} {r['created_at']} {r['action']} {r['target']}")
                if not rows: await s.send('HISTORIA: brak wpisow.')
            elif act=='szczegoly' and len(tail)==2:
                rid=_number(tail[1],1,2**31-1)
                r=db.conn.execute('SELECT * FROM admin_actions_v1224 WHERE id=?',(rid,)).fetchone()
                await s.send('HISTORIA: '+ (f"{r['id']} {r['created_at']} {r['admin_login']} {r['action']} {r['target']}" if r else 'brak ID.'))
            elif act=='quest':
                try: rows=db.conn.execute('SELECT id,quest_id,before_progress,reverted FROM admin_guardian_quest_repairs_v3600 ORDER BY id DESC LIMIT 20').fetchall()
                except sqlite3.OperationalError: rows=[]
                await s.send('KOREKTY QUEST: '+('; '.join(f"#{r['id']} {r['quest_id']} poprzedni {r['before_progress']} cofnieta {r['reverted']}" for r in rows) if rows else 'brak.'))
            elif act=='cofnij':
                if len(tail)!=3 or tail[2]!='POTWIERDZAM': raise ValueError('Historia: cofnij NUMER_KOREKTY POTWIERDZAM; inne rodzaje zmian tylko admin live cofnij POTWIERDZAM.')
                repair_id=_number(tail[1],1,2**31-1)
                await s.send(_quest_revert(s,repair_id));_audit(s,'quest_revert',str(repair_id))
            else: raise ValueError('Historia: ostatnie N / olc N / szczegoly ID / cofnij ID.')
        elif sub=='role':
            act=tail[0].casefold() if tail else ''
            if act=='lista':
                rows=db.conn.execute('SELECT a.username,r.role FROM admin_guardian_roles_v3600 r JOIN accounts a ON a.id=r.account_id ORDER BY a.username').fetchall()
                await s.send('ROLE: '+('; '.join(f"{r['username']}={r['role']}" for r in rows) if rows else 'Brak ról delegowanych.'))
            elif act=='podglad' and len(tail)==2:
                await s.send(f'ROLA: {tail[1]} = {_role(s,tail[1])}.')
            elif act in ('nadaj','odbierz'):
                if len(tail)<3 or tail[-1]!='POTWIERDZAM': raise ValueError('Rola: nadaj LOGIN pomocnik/moderator/administrator POTWIERDZAM; odbierz LOGIN POTWIERDZAM.')
                nick=tail[1]; master=db.master_account_by_name(nick)
                if not master: raise ValueError('Nieznane konto.')
                if str(master['username']).casefold() == db.account_name(s.master_account_id).casefold(): raise ValueError('Nie wolno modyfikowac konta wlasciciela.')
                from core.bootstrap_economy_professions import ADMIN_ACCOUNT_NAMES
                if str(master['username']).casefold() in ADMIN_ACCOUNT_NAMES: raise ValueError('Nie mozna modyfikowac uprawnien innego wlasciciela.')
                if act=='nadaj':
                    if len(tail)!=4 or tail[2] not in ROLE_ORDER: raise ValueError('Niepoprawna rola.')
                    db.conn.execute('INSERT INTO admin_guardian_roles_v3600(account_id,role,granted_by) VALUES(?,?,?) ON CONFLICT(account_id) DO UPDATE SET role=excluded.role,granted_by=excluded.granted_by',(master['id'],tail[2],db.account_name(s.master_account_id)))
                else:
                    if len(tail)!=3: raise ValueError('Odbierz: LOGIN POTWIERDZAM.')
                    db.conn.execute('DELETE FROM admin_guardian_roles_v3600 WHERE account_id=?',(master['id'],))
                db.conn.commit(); _audit(s,'role_'+act,nick); await s.send('Rola zapisana. Delegowane komendy ograniczone do Guardian: pomoc/status/panel/questdiag/balans. Brak dostepu do starego admin.')
            else: raise ValueError('Role: lista / podglad LOGIN / nadaj LOGIN ROLA POTWIERDZAM / odbierz LOGIN POTWIERDZAM.')
        else: raise ValueError(TUTORIAL)
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        await s.send('GUARDIAN: '+str(exc)[:280])
    return True
