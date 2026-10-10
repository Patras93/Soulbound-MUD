# -*- coding: utf-8 -*-
"""v2.00.0: additive SQLite progress for real faction hunts and PvE arena.

No separate XP counters, no PvP, no changes to old saves. Combat credits from
existing party-recipient list, not from command submissions.
"""
from __future__ import annotations
import time
from systems.imperial_economy_v1320 import atomic
from systems.imperial_economy_v1321 import _wallet
from systems.parallel_worlds_v2000 import ARENAS

FACTIONS={
    'sny':('Kolegium Śniących','v2000_sny_mob_8',360),
    'smoki':('Zakon Smoczych Kronikarzy','v2000_smoki_mob_8',500),
    'duchy':('Strażnicy Przeprawy Dusz','v2000_duchy_mob_8',610),
    'pustka':('Badacze Bezkresu','v2000_pustka_mob_8',740),
    'perly':('Kartografowie Perłowych Mórz','v2000_sea_perly_mob_3',390),
    'otchlan':('Bractwo Czarnej Głębi','v2000_sea_otchlan_mob_3',570),
    'burze':('Strażnicy Morskich Burz','v2000_sea_burze_mob_3',690),
}
ARENA={slug:(name,level,f'v2000_arena_boss_{slug}') for slug,name,level,_ in ARENAS}


def init(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS v2000_factions (
      account_id INTEGER NOT NULL, faction TEXT NOT NULL, renown INTEGER NOT NULL DEFAULT 0,
      claimed_rank INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(account_id,faction))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS v2000_faction_hunts (
      account_id INTEGER NOT NULL, faction TEXT NOT NULL,
      active INTEGER NOT NULL DEFAULT 0, progress INTEGER NOT NULL DEFAULT 0,
      ready_at INTEGER NOT NULL DEFAULT 0, completions INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(account_id,faction))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS v2000_arena_trials (
      account_id INTEGER NOT NULL, challenge TEXT NOT NULL,
      state INTEGER NOT NULL DEFAULT 0, progress INTEGER NOT NULL DEFAULT 0, ready_at INTEGER NOT NULL DEFAULT 0,
      victories INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(account_id,challenge))''')
    conn.commit()


def fame_status(conn,account):
    rows=conn.execute('SELECT faction,renown FROM v2000_factions WHERE account_id=?',(account,))
    return {str(r[0]):int(r[1]) for r in rows}


def faction_start(conn,account,key,now=None):
    if key not in FACTIONS:raise ValueError('Nieznana frakcja. Wpisz frakcje lista.')
    now=int(time.time()) if now is None else int(now)
    with atomic(conn):
        row=conn.execute('SELECT * FROM v2000_faction_hunts WHERE account_id=? AND faction=?',(account,key)).fetchone()
        if row and int(row['active']):raise ValueError('Masz aktywny kontrakt tej frakcji. Wpisz frakcje status.')
        if row and int(row['ready_at'])>now:raise ValueError(f'Kolejny kontrakt za {int(row["ready_at"])-now} sekund.')
        conn.execute('''INSERT INTO v2000_faction_hunts(account_id,faction,active,progress,ready_at)
            VALUES(?,?,1,0,0) ON CONFLICT(account_id,faction)
            DO UPDATE SET active=1, progress=0, ready_at=0''',(account,key))
    return FACTIONS[key][1]


def arena_start(conn,account,key,now=None):
    if key not in ARENA:raise ValueError('Nieznana próba. Wpisz arena lista.')
    now=int(time.time()) if now is None else int(now)
    with atomic(conn):
        running=conn.execute('SELECT challenge FROM v2000_arena_trials WHERE account_id=? AND state IN (1,2)',(account,)).fetchone()
        if running:raise ValueError(f'Najpierw ukończ lub rozlicz próbę {running[0]}.')
        row=conn.execute('SELECT ready_at FROM v2000_arena_trials WHERE account_id=? AND challenge=?',(account,key)).fetchone()
        if row and int(row['ready_at'])>now:raise ValueError(f'Próba dostępna za {int(row["ready_at"])-now} sekund.')
        conn.execute('''INSERT INTO v2000_arena_trials(account_id,challenge,state,ready_at)
          VALUES(?,?,1,0) ON CONFLICT(account_id,challenge)
          DO UPDATE SET state=1,progress=0,ready_at=0''',(account,key))
    return ARENA[key][2]


def record_kill(conn,accounts,mob_id):
    """Called once after a real kill, for actual eligible recipients only.

    Never grants currency here; claims are explicit and atomic. No scanning the
    full world or every logged-in user; at most seven indexed rows per recipient.
    """
    notes=[]
    for account in set(int(a) for a in accounts if a is not None):
        if mob_id.startswith('v2000_'):
            for key,(_name,target,_level) in FACTIONS.items():
                if target==mob_id:
                    cur=conn.execute('''UPDATE v2000_faction_hunts SET progress=1
                        WHERE account_id=? AND faction=? AND active=1 AND progress=0''',(account,key))
                    if cur.rowcount:notes.append((account,f'Kontrakt frakcji {FACTIONS[key][0]} gotowy. Wpisz frakcje odbierz {key}.'))
            for key,(_name,_level,target) in ARENA.items():
                bit = 8 if mob_id==target else next(
                    (1 << w for w in range(3)
                     if mob_id==f'v2000_arena_wave_{key}_{w}'), 0)
                if not bit:
                    continue
                row=conn.execute('SELECT state,progress FROM v2000_arena_trials WHERE account_id=? AND challenge=?',(account,key)).fetchone()
                if not row or int(row['state'])!=1:
                    continue
                previous=int(row['progress'])
                progress=previous | bit
                if progress==previous:
                    continue
                completed=progress==15
                conn.execute('UPDATE v2000_arena_trials SET progress=?,state=? WHERE account_id=? AND challenge=? AND state=1',
                             (progress,2 if completed else 1,account,key))
                if completed:
                    notes.append((account,f'Arena Legend: próba {key} ukończona. Wpisz arena odbierz {key}.'))
                else:
                    notes.append((account,f'Arena {key}: pokonane rodzaje fal {(progress & 7).bit_count()}/3; boss '+
                                  ('pokonany.' if progress & 8 else 'pozostał.')))
    # This callback can happen during other save operations. Let caller commit
    # with regular combat rewards (or commit for standalone tests below).
    return notes


def claim_faction(conn,account,key,now=None):
    if key not in FACTIONS:raise ValueError('Nieznana frakcja.')
    now=int(time.time()) if now is None else int(now)
    with atomic(conn):
        row=conn.execute('SELECT active,progress FROM v2000_faction_hunts WHERE account_id=? AND faction=?',(account,key)).fetchone()
        if not row or int(row['active'])!=1 or int(row['progress'])!=1:
            raise ValueError('Kontrakt nie jest gotowy do odbioru.')
        level=FACTIONS[key][2]
        coins=level*5500
        new_balance=_wallet(conn,account)+coins
        if new_balance>8_000_000_000_000_000_000:raise ValueError('Przekroczono limit bezpieczeństwa salda.')
        cur=conn.execute('UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?',(new_balance,account))
        if cur.rowcount!=1:raise ValueError('Brak konta do wypłaty nagrody.')
        conn.execute('INSERT INTO v2000_factions(account_id,faction,renown) VALUES(?,?,25) '
                     'ON CONFLICT(account_id,faction) DO UPDATE SET renown=renown+25',(account,key))
        conn.execute('''UPDATE v2000_faction_hunts SET active=0,progress=0,
                        ready_at=?,completions=completions+1 WHERE account_id=? AND faction=?''',
                        (now+3600,account,key))
        renown=int(conn.execute('SELECT renown FROM v2000_factions WHERE account_id=? AND faction=?',(account,key)).fetchone()[0])
        balance=int(conn.execute('SELECT silver FROM characters WHERE account_id=?',(account,)).fetchone()[0])
    return coins,renown,balance


def claim_arena(conn,account,key,now=None):
    if key not in ARENA:raise ValueError('Nieznana próba areny.')
    now=int(time.time()) if now is None else int(now)
    with atomic(conn):
        row=conn.execute('SELECT state,victories FROM v2000_arena_trials WHERE account_id=? AND challenge=?',(account,key)).fetchone()
        if not row or int(row['state'])!=2:raise ValueError('Próba nie jest jeszcze ukończona.')
        level=ARENA[key][1]
        coins=level*11000
        new_balance=_wallet(conn,account)+coins
        if new_balance>8_000_000_000_000_000_000:raise ValueError('Przekroczono limit bezpieczeństwa salda.')
        cur=conn.execute('UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?',(new_balance,account))
        if cur.rowcount!=1:raise ValueError('Brak konta do wypłaty nagrody.')
        conn.execute('''UPDATE v2000_arena_trials SET state=0,ready_at=?,victories=victories+1
                    WHERE account_id=? AND challenge=?''',(now+5400,account,key))
        balance=int(conn.execute('SELECT silver FROM characters WHERE account_id=?',(account,)).fetchone()[0])
        victories=int(row['victories'])+1
    return coins,victories,balance


def claim_rank(conn,account,key):
    if key not in FACTIONS:raise ValueError('Nieznana frakcja.')
    levels=(100,300,600)
    with atomic(conn):
        row=conn.execute('SELECT renown,claimed_rank FROM v2000_factions WHERE account_id=? AND faction=?',(account,key)).fetchone()
        if not row:raise ValueError('Najpierw zdobądź reputację frakcji.')
        old=int(row['claimed_rank']);renown=int(row['renown'])
        rank=old+1
        if rank>3:raise ValueError('Odebrano już wszystkie trzy odznaki.')
        if renown<levels[old]:raise ValueError(f'Kolejna odznaka wymaga {levels[old]} reputacji. Masz {renown}.')
        iid=f'v2000_faction_{key}_rank_{rank}'
        conn.execute('INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,1) ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+1',(account,iid))
        conn.execute('UPDATE v2000_factions SET claimed_rank=? WHERE account_id=? AND faction=?',(rank,account,key))
    return rank,iid,renown
