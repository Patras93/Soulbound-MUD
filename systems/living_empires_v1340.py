# -*- coding: utf-8 -*-
"""v1.34: żyjące terytoria gildii, garnizony i odpierane najazdy.

Wszystkie mutacje atomowe; rozliczenie upływu czasu dopiero na żądanie.
Bez generatora świata, bez zmian istniejących tabel postaci.
"""
from __future__ import annotations
import time
from systems import imperial_economy_v1320 as empire

CYCLE = 6*3600
RAID = 12*3600
FACTIONS = ('Legion Popiołów', 'Horda Rozbitych Sztandarów', 'Zakon Pustki', 'Korsarze Żelaznego Szlaku')
BUILDINGS = {'farmy': (60000, 3400), 'targ': (90000, 5200), 'kuznia': (130000, 7100)}


def init(conn):
    empire.init(conn)
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS empire_territories_v1340 (
      fort TEXT PRIMARY KEY, owner_id INTEGER NOT NULL, farms INTEGER NOT NULL DEFAULT 0,
      market INTEGER NOT NULL DEFAULT 0, forge INTEGER NOT NULL DEFAULT 0,
      reserve INTEGER NOT NULL DEFAULT 0, stability INTEGER NOT NULL DEFAULT 100,
      raids INTEGER NOT NULL DEFAULT 0, last_cycle INTEGER NOT NULL,
      last_raid INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS empire_garrisons_v1340 (
      fort TEXT NOT NULL, owner_id INTEGER NOT NULL, troop TEXT NOT NULL,
      quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0), PRIMARY KEY(fort,troop));
    CREATE TABLE IF NOT EXISTS empire_history_v1340 (
      id INTEGER PRIMARY KEY AUTOINCREMENT, fort TEXT NOT NULL, owner_id INTEGER NOT NULL,
      attacker TEXT NOT NULL, victory INTEGER NOT NULL, losses INTEGER NOT NULL,
      occurred_at INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_empire_history_fort_v1340 ON empire_history_v1340(fort,occurred_at);
    CREATE TABLE IF NOT EXISTS empire_pve_raids_v1340 (
      fort TEXT NOT NULL, clan_id INTEGER NOT NULL,
      ready_at INTEGER NOT NULL DEFAULT 0, victories INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(fort,clan_id));
    -- Captures/ownership changes invalidate the old owner's defensive soldiers and income.
    CREATE TRIGGER IF NOT EXISTS empire_fort_transfer_v1340
    AFTER UPDATE OF clan_id ON empire_forts_v1320
    WHEN OLD.clan_id != NEW.clan_id
    BEGIN
      DELETE FROM empire_garrisons_v1340 WHERE fort=NEW.fort;
      DELETE FROM empire_territories_v1340 WHERE fort=NEW.fort;
      DELETE FROM empire_pve_raids_v1340 WHERE fort=NEW.fort;
    END;
    CREATE TRIGGER IF NOT EXISTS empire_fort_delete_v1340
    AFTER DELETE ON empire_forts_v1320
    BEGIN
      DELETE FROM empire_garrisons_v1340 WHERE fort=OLD.fort;
      DELETE FROM empire_territories_v1340 WHERE fort=OLD.fort;
      DELETE FROM empire_pve_raids_v1340 WHERE fort=OLD.fort;
    END;
    ''')
    conn.commit()


def owner_of(conn,fort):
    if fort not in empire.FORTS: raise ValueError('Nieznana twierdza.')
    row=conn.execute('SELECT clan_id,conquered_at,walls FROM empire_forts_v1320 WHERE fort=?',(fort,)).fetchone()
    return row


def _ensure(conn,fort,now):
    row=owner_of(conn,fort)
    if not row: return None
    owner=int(row['clan_id'])
    first=max(int(row['conquered_at'] or now),0)
    conn.execute('INSERT INTO empire_territories_v1340(fort,owner_id,last_cycle,last_raid) VALUES(?,?,?,?) '
                 'ON CONFLICT(fort) DO NOTHING',(fort,owner,first,first))
    state=conn.execute('SELECT * FROM empire_territories_v1340 WHERE fort=?',(fort,)).fetchone()
    if int(state['owner_id'])!=owner:
        # For old saves or databases where an older trigger was absent.
        conn.execute('DELETE FROM empire_garrisons_v1340 WHERE fort=?',(fort,))
        conn.execute('DELETE FROM empire_territories_v1340 WHERE fort=?',(fort,))
        conn.execute('INSERT INTO empire_territories_v1340(fort,owner_id,last_cycle,last_raid) VALUES(?,?,?,?)',(fort,owner,first,first))
        state=conn.execute('SELECT * FROM empire_territories_v1340 WHERE fort=?',(fort,)).fetchone()
    return state


def garrison_strength(conn,fort):
    exists=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='empire_garrisons_v1340'").fetchone()
    if not exists:return 0
    rows=conn.execute('SELECT troop,quantity FROM empire_garrisons_v1340 WHERE fort=?',(fort,)).fetchall()
    return sum(empire.TROOPS[r['troop']][1]*int(r['quantity'])*1000 for r in rows if r['troop'] in empire.TROOPS)


def front(fort,now=None):
    now=int(time.time()) if now is None else int(now)
    return FACTIONS[(list(empire.FORTS).index(fort) + now//(3*3600))%len(FACTIONS)]


def _raid(conn,fort,state,owner,now):
    soldiers={r['troop']:int(r['quantity']) for r in conn.execute('SELECT troop,quantity FROM empire_garrisons_v1340 WHERE fort=?',(fort,)).fetchall()}
    current_strength=sum(empire.TROOPS[k][1]*v*1000 for k,v in soldiers.items() if k in empire.TROOPS)
    severity=(empire.FORTS[fort][2]*7)//10 + (int(state['raids'])%4)*empire.FORTS[fort][2]//10
    defense=current_strength + int(owner['walls'])*empire.FORTS[fort][2]//3
    victory=defense >= severity
    losses=0
    # Attrition even on victory, but never negative. No surprise loss of fort ownership.
    for troop,qty in soldiers.items():
        if qty<=0:continue
        lost=min(qty,max(1,(qty*(7 if victory else 17)+99)//100))
        conn.execute('UPDATE empire_garrisons_v1340 SET quantity=quantity-? WHERE fort=? AND troop=?',(lost,fort,troop))
        losses+=lost
    if not victory:
        conn.execute('UPDATE empire_forts_v1320 SET walls=MAX(1,walls-1) WHERE fort=?',(fort,))
    stability=max(10,min(100,int(state['stability'])+(4 if victory else -16)))
    conn.execute('UPDATE empire_territories_v1340 SET stability=?,raids=raids+1,last_raid=? WHERE fort=?',
                 (stability,now,fort))
    conn.execute('INSERT INTO empire_history_v1340(fort,owner_id,attacker,victory,losses,occurred_at) VALUES(?,?,?,?,?,?)',
                 (fort,int(owner['clan_id']),front(fort,now),int(victory),losses,now))
    return {'defended':victory,'attacker':front(fort,now),'losses':losses,'stability':stability}


def refresh(conn,fort,*,now=None):
    now=int(time.time()) if now is None else int(now)
    with empire.atomic(conn):
        state=_ensure(conn,fort,now)
        if not state:return {'owned':False,'raid':None,'income':0}
        # At most 4 paid cycles since last check; offline years are never a windfall.
        delta=max(0,now-int(state['last_cycle']))
        cycles=min(4,delta//CYCLE)
        earned=0
        if cycles:
            earned=cycles*(900 + int(state['farms'])*BUILDINGS['farmy'][1]
                          + int(state['market'])*BUILDINGS['targ'][1]
                          + int(state['forge'])*BUILDINGS['kuznia'][1])
            # Large future timestamp changes must not duplicate elapsed cycles.
            new_mark=now-(delta%CYCLE)
            conn.execute('UPDATE empire_territories_v1340 SET reserve=reserve+?,last_cycle=? WHERE fort=?',(earned,new_mark,fort))
        event=None
        if now-int(state['last_raid'])>=RAID:
            owner=owner_of(conn,fort)
            event=_raid(conn,fort,state,owner,now)
        return {'owned':True,'raid':event,'income':earned}


def detail(conn,fort,*,now=None):
    refresh(conn,fort,now=now)
    owner=owner_of(conn,fort)
    if not owner:return None
    state=conn.execute('SELECT * FROM empire_territories_v1340 WHERE fort=?',(fort,)).fetchone()
    troop={r['troop']:int(r['quantity']) for r in conn.execute('SELECT troop,quantity FROM empire_garrisons_v1340 WHERE fort=?',(fort,)).fetchall()}
    return {'owner':int(owner['clan_id']),'walls':int(owner['walls']), 'garrison':troop,
            'reserve':int(state['reserve']), 'stability':int(state['stability']),
            'farms':int(state['farms']), 'targ':int(state['market']), 'kuznia':int(state['forge']),
            'raids':int(state['raids']), 'strength':garrison_strength(conn,fort)}


def move_garrison(conn,clan,fort,troop,quantity,*,return_to_army=False):
    if troop not in empire.TROOPS or not 1<=quantity<=1000000:raise ValueError('Nieprawidłowy oddział lub ilość.')
    with empire.atomic(conn):
        owner=owner_of(conn,fort)
        if not owner or int(owner['clan_id'])!=clan:raise ValueError('Ta twierdza nie należy do twojej gildii.')
        _ensure(conn,fort,int(time.time()))
        if return_to_army:
            cur=conn.execute('UPDATE empire_garrisons_v1340 SET quantity=quantity-? WHERE fort=? AND troop=? AND quantity>=?',(quantity,fort,troop,quantity))
            if cur.rowcount!=1:raise ValueError('Za mało żołnierzy w garnizonie.')
            conn.execute('INSERT INTO empire_armies_v1320(clan_id,troop,quantity) VALUES(?,?,?) '
                         'ON CONFLICT(clan_id,troop) DO UPDATE SET quantity=quantity+excluded.quantity',(clan,troop,quantity))
        else:
            cur=conn.execute('UPDATE empire_armies_v1320 SET quantity=quantity-? WHERE clan_id=? AND troop=? AND quantity>=?',(quantity,clan,troop,quantity))
            if cur.rowcount!=1:raise ValueError('Za mało żołnierzy w armii gildii.')
            conn.execute('INSERT INTO empire_garrisons_v1340(fort,owner_id,troop,quantity) VALUES(?,?,?,?) '
                         'ON CONFLICT(fort,troop) DO UPDATE SET quantity=quantity+excluded.quantity',(fort,clan,troop,quantity))
        return garrison_strength(conn,fort)


def upgrade(conn,clan,fort,kind):
    if kind not in BUILDINGS:raise ValueError('Budynki: farmy, targ, kuznia.')
    column={'farmy':'farms','targ':'market','kuznia':'forge'}[kind]
    with empire.atomic(conn):
        owner=owner_of(conn,fort)
        if not owner or int(owner['clan_id'])!=clan:raise ValueError('Ta twierdza nie należy do twojej gildii.')
        state=_ensure(conn,fort,int(time.time()))
        level=int(state[column]); price=BUILDINGS[kind][0]*(level+1)**2
        if price>8_000_000_000_000_000_000:raise ValueError('Koszt rozbudowy przekracza zakres waluty.')
        cur=conn.execute('UPDATE player_clans SET treasury=treasury-? WHERE id=? AND treasury>=?',(price,clan,price))
        if cur.rowcount!=1:raise ValueError('Brak monet w skarbcu gildii.')
        conn.execute(f'UPDATE empire_territories_v1340 SET {column}={column}+1 WHERE fort=?',(fort,))
        return level+1,price


def collect(conn,clan,fort,*,now=None):
    refresh(conn,fort,now=now)
    with empire.atomic(conn):
        owner=owner_of(conn,fort)
        if not owner or int(owner['clan_id'])!=clan:raise ValueError('Ta twierdza nie należy do twojej gildii.')
        row=conn.execute('SELECT reserve FROM empire_territories_v1340 WHERE fort=?',(fort,)).fetchone()
        amount=int(row['reserve']) if row else 0
        if amount:
            cur=conn.execute('UPDATE player_clans SET treasury=treasury+? WHERE id=? AND treasury<=?',
                             (amount,clan,8_000_000_000_000_000_000-amount))
            if cur.rowcount!=1:raise ValueError('Skarbiec gildii nie przyjmie większej kwoty.')
            conn.execute('UPDATE empire_territories_v1340 SET reserve=0 WHERE fort=?',(fort,))
        return amount


def history(conn,fort,limit=5):
    return conn.execute('SELECT * FROM empire_history_v1340 WHERE fort=? ORDER BY id DESC LIMIT ?', (fort,limit)).fetchall()


COUNTERATTACK_COOLDOWN = 3 * 3600
COUNTERATTACK_TACTICS = {
    'natarcie': {'wojownik': 3, 'lucznik': 2, 'mag': 2},
    'ostrzal': {'wojownik': 2, 'lucznik': 3, 'mag': 2},
    'magia': {'wojownik': 2, 'lucznik': 2, 'mag': 3},
}


def enemy_camp(conn, clan, fort, tactic='natarcie', *, now=None):
    """Gildia walczy TYLKO z armią NPC. Strategiczna ekspedycja, nie PvP.

    W jednej transakcji: koszt w żołnierzach, cooldown, wynik i łup do skarbca.
    Bez automatycznych skoków poziomu, lootów postaci ani nowej waluty.
    """
    if fort not in empire.FORTS: raise ValueError('Nieznana twierdza.')
    if tactic not in COUNTERATTACK_TACTICS: raise ValueError('Taktyki: natarcie, ostrzal, magia.')
    now=int(time.time()) if now is None else int(now)
    with empire.atomic(conn):
        owner=owner_of(conn,fort)
        if not owner or int(owner['clan_id'])!=int(clan):
            raise ValueError('Wyprawę odwetową może prowadzić tylko gildia broniąca tej twierdzy.')
        _ensure(conn,fort,now)
        row=conn.execute('SELECT ready_at FROM empire_pve_raids_v1340 WHERE fort=? AND clan_id=?',
                         (fort,clan)).fetchone()
        if row and int(row['ready_at'])>now:
            raise ValueError(f'Oddziały odpoczywają jeszcze {int(row["ready_at"])-now} sekund.')
        troops={r['troop']:int(r['quantity']) for r in conn.execute(
            'SELECT troop,quantity FROM empire_armies_v1320 WHERE clan_id=?',(clan,)).fetchall()}
        if not any(qty>0 for qty in troops.values()):
            raise ValueError('Brak dostępnych oddziałów. Użyj armia rekrutuj.')
        modifiers=COUNTERATTACK_TACTICS[tactic]
        power=sum(empire.TROOPS[key][1]*max(0,qty)*1000*modifiers[key]//2
                  for key,qty in troops.items() if key in empire.TROOPS)
        state=conn.execute('SELECT raids,stability FROM empire_territories_v1340 WHERE fort=?',(fort,)).fetchone()
        threat=empire.FORTS[fort][2]//2 + int(state['raids']%5)*empire.FORTS[fort][2]//10
        victory=power>=threat
        casualties={}
        for key,qty in troops.items():
            if key not in empire.TROOPS or qty<=0: continue
            lost=min(qty,max(1,qty*(4 if victory else 13)//100))
            cur=conn.execute('UPDATE empire_armies_v1320 SET quantity=quantity-? WHERE clan_id=? AND troop=? AND quantity>=?',
                             (lost,clan,key,lost))
            if cur.rowcount!=1:raise ValueError('Brak dostępnego oddziału.')
            casualties[key]=lost
        reward=0
        if victory:
            # A useful guild bounty, not a passive, limitless source of huge wealth.
            reward=1500 + min(15_000,empire.FORTS[fort][2]//150)
            cur=conn.execute('UPDATE player_clans SET treasury=treasury+? WHERE id=? AND treasury<=?',
                             (reward,clan,8_000_000_000_000_000_000-reward))
            if cur.rowcount!=1:raise ValueError('Nie można zapisać nagrody w skarbcu gildii.')
            conn.execute('UPDATE empire_territories_v1340 SET stability=MIN(100,stability+8) WHERE fort=?',(fort,))
        conn.execute('INSERT INTO empire_pve_raids_v1340(fort,clan_id,ready_at,victories) VALUES(?,?,?,?) '
                     'ON CONFLICT(fort,clan_id) DO UPDATE SET ready_at=excluded.ready_at,victories=victories+excluded.victories',
                     (fort,clan,now+COUNTERATTACK_COOLDOWN,int(victory)))
        enemy=front(fort,now)
        conn.execute('INSERT INTO empire_history_v1340(fort,owner_id,attacker,victory,losses,occurred_at) VALUES(?,?,?,?,?,?)',
                     (fort,clan,'Wyprawa na: '+enemy,int(victory),sum(casualties.values()),now))
        return {'won':victory,'enemy':enemy,'power':power,'threat':threat,
                'losses':casualties,'reward':reward,'next_at':now+COUNTERATTACK_COOLDOWN}
