# -*- coding: utf-8 -*-
"""v1.32.1: multi-round sieges, real escrow bids and independently equipped ships.

Additive tables only; no migration of old save data or world generation.
"""
from __future__ import annotations

import time
from systems import imperial_economy_v1320 as base
from storage.db_schema import legacy_currency_to_coins

MAX_COINS = 8_000_000_000_000_000_000
PHASES = ('brama', 'dziedziniec', 'cytadela')
ORDERS = {
    'natarcie': (1.55, .65, .85),
    'ostrzal': (.60, 1.55, .85),
    'magia': (.65, .80, 1.60),
    'oslona': (.90, .90, .95),
}
BONUS = (('natarcie', 1.20), ('ostrzal', 1.20), ('magia', 1.20))
MODULES = ('hull', 'sails', 'cargo', 'navigation')
CLASSES = ('kuter', 'bryg', 'fregata', 'galeon')


def init(conn):
    base.init(conn)
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS siege_battles_v1321 (
      fort TEXT PRIMARY KEY, clan_id INTEGER NOT NULL, phase INTEGER NOT NULL DEFAULT 1,
      remaining INTEGER NOT NULL, turns INTEGER NOT NULL DEFAULT 0,
      started_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS market_auctions_v1321 (
      listing_id INTEGER PRIMARY KEY, expires_at INTEGER NOT NULL,
      highest_bid INTEGER NOT NULL DEFAULT 0,
      bidder_id INTEGER, bid_count INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS shipyard_ships_v1321 (
      id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL,
      ship_class INTEGER NOT NULL, name TEXT NOT NULL,
      hull INTEGER NOT NULL DEFAULT 1, sails INTEGER NOT NULL DEFAULT 1,
      cargo INTEGER NOT NULL DEFAULT 1, navigation INTEGER NOT NULL DEFAULT 1,
      active INTEGER NOT NULL DEFAULT 0, built_at INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_fleet_account_v1321 ON shipyard_ships_v1321(account_id);
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fleet_active_v1321
      ON shipyard_ships_v1321(account_id) WHERE active=1;
    ''')
    conn.commit()


def _wallet(conn, account):
    row = conn.execute('SELECT silver,gold,mithril FROM characters WHERE account_id=?',(account,)).fetchone()
    if row is None:
        raise ValueError('Brak portfela postaci.')
    return legacy_currency_to_coins(row['silver'],row['gold'],row['mithril'])


def _pay(conn, account, price):
    wallet = _wallet(conn, account)
    if wallet < price:
        raise ValueError('Brakuje srebrnych monet.')
    remain = wallet-price
    conn.execute('UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?',(remain, account))
    return remain


def _payout(conn, account, coins):
    if coins<=0:return
    current=conn.execute('SELECT coins FROM market_payouts_v1320 WHERE account_id=?',(account,)).fetchone()
    if current and int(current['coins'])+coins>MAX_COINS:
        raise ValueError('Przekroczono bezpieczny limit depozytu.')
    conn.execute('INSERT INTO market_payouts_v1320(account_id,coins) VALUES(?,?) '
                 'ON CONFLICT(account_id) DO UPDATE SET coins=coins+excluded.coins',(account,coins))


def offer_auction(conn, seller, item, qty, starting, hours, source):
    if not (1<=qty<=1_000_000 and 1<=starting<=10**15 and hours in (1,6,12,24,48)):
        raise ValueError('Ilość, cena lub czas licytacji są nieprawidłowe.')
    with base.atomic(conn):
        count=conn.execute("SELECT COUNT(*) FROM market_listings_v1320 WHERE seller=? AND state='active'",(seller,)).fetchone()[0]
        if count>=30:raise ValueError('Możesz wystawić maksymalnie 30 aktywnych ofert.')
        base.take(conn,seller,item,qty,source)
        now=int(time.time())
        cur=conn.execute('INSERT INTO market_listings_v1320(seller,item_id,quantity,container,price,created_at) VALUES(?,?,?,?,?,?)',
                         (seller,item,qty,source,starting,now))
        base._escrow_basis(conn,seller,item,qty,cur.lastrowid)
        conn.execute('INSERT INTO market_auctions_v1321(listing_id,expires_at) VALUES(?,?)',
                     (cur.lastrowid,now+hours*3600))
        return cur.lastrowid


def bid(conn, bidder, listing_id, amount, *, now=None):
    now=int(time.time()) if now is None else now
    if not (1<=amount<=10**15):raise ValueError('Nieprawidłowa kwota licytacji.')
    with base.atomic(conn):
        row=conn.execute('SELECT l.seller,l.state,l.price,a.expires_at,a.highest_bid,a.bidder_id FROM market_listings_v1320 l '
                         'JOIN market_auctions_v1321 a ON a.listing_id=l.id WHERE l.id=?',(listing_id,)).fetchone()
        if not row or row['state']!='active':raise ValueError('Brak aktywnej licytacji.')
        if row['seller']==bidder:raise ValueError('Nie wolno licytować własnej oferty.')
        if now>=int(row['expires_at']):raise ValueError('Licytacja zakończona. Wpisz aukcja rozlicz.')
        if row['bidder_id']==bidder:raise ValueError('Już prowadzisz tę licytację.')
        minimum=max(int(row['price']),int(row['highest_bid'])+max(1,int(row['highest_bid'])//20))
        if amount<minimum:raise ValueError(f'Minimalna oferta: {minimum} srebrnych monet.')
        remaining=_pay(conn,bidder,amount)
        if row['bidder_id'] is not None:
            _payout(conn,int(row['bidder_id']),int(row['highest_bid']))
        conn.execute('UPDATE market_auctions_v1321 SET highest_bid=?,bidder_id=?,bid_count=bid_count+1 '
                     'WHERE listing_id=?',(amount,bidder,listing_id))
        return remaining, minimum


def settle(conn, listing_id, *, now=None):
    now=int(time.time()) if now is None else now
    with base.atomic(conn):
        row=conn.execute('SELECT l.*,a.expires_at,a.highest_bid,a.bidder_id FROM market_listings_v1320 l '
                         'JOIN market_auctions_v1321 a ON a.listing_id=l.id WHERE l.id=?',(listing_id,)).fetchone()
        if row is None: raise ValueError('Nie ma takiej licytacji.')
        if row['state']!='active':raise ValueError('Licytacja jest już rozliczona.')
        if now<int(row['expires_at']):raise ValueError(f'Do zakończenia zostało {int(row["expires_at"])-now} sekund.')
        if row['bidder_id'] is None:
            base.give(conn,row['seller'],row['item_id'],row['quantity'],row['container'])
            base._restore_basis(conn,listing_id,row['seller'],row['item_id'])
            conn.execute("UPDATE market_listings_v1320 SET state='cancelled',closed_at=? WHERE id=?",(now,listing_id))
            return ('unsold',row)
        base.give(conn,row['bidder_id'],row['item_id'],row['quantity'],row['container'])
        base._restore_basis(conn,listing_id,row['bidder_id'],row['item_id'])
        _payout(conn,row['seller'],int(row['highest_bid']))
        conn.execute("UPDATE market_listings_v1320 SET state='sold',buyer=?,closed_at=? WHERE id=?",(row['bidder_id'],now,listing_id))
        return ('sold',row)


def cancel_auction(conn, seller, listing_id):
    with base.atomic(conn):
        row=conn.execute('SELECT l.*, a.bidder_id FROM market_listings_v1320 l JOIN market_auctions_v1321 a '
                         "ON a.listing_id=l.id WHERE l.id=? AND l.seller=? AND l.state='active'",(listing_id,seller)).fetchone()
        if not row:raise ValueError('Brak twojej aktywnej licytacji.')
        if row['bidder_id'] is not None:raise ValueError('Nie można anulować licytacji, w której już złożono ofertę.')
        base.give(conn,row['seller'],row['item_id'],row['quantity'],row['container'])
        base._restore_basis(conn,listing_id,seller,row['item_id'])
        conn.execute("UPDATE market_listings_v1320 SET state='cancelled',closed_at=? WHERE id=?",(int(time.time()),listing_id))


def phase_strength(conn, fort, phase):
    return max(1000, round(base.fort_strength(conn,fort)*(.44,.33,.23)[phase-1]))


def start_siege(conn, clan, fort, *, now=None):
    now=int(time.time()) if now is None else now
    if fort not in base.FORTS:raise ValueError('Nieznana twierdza.')
    with base.atomic(conn):
        if base.troop_strength(conn,clan)<=0:raise ValueError('Nie masz żywej armii.')
        owner=conn.execute('SELECT clan_id FROM empire_forts_v1320 WHERE fort=?',(fort,)).fetchone()
        if owner and int(owner['clan_id'])==clan:raise ValueError('Twoja gildia kontroluje już tę twierdzę.')
        ready=conn.execute('SELECT ready_at FROM empire_sieges_v1320 WHERE clan_id=? AND fort=?',(clan,fort)).fetchone()
        if ready and int(ready['ready_at'])>now:raise ValueError(f'Przegrupowanie: {int(ready["ready_at"])-now} sekund.')
        previous=conn.execute('SELECT clan_id,started_at FROM siege_battles_v1321 WHERE fort=?',(fort,)).fetchone()
        if previous and now-int(previous['started_at'])<12*3600:
            if int(previous['clan_id'])==clan:raise ValueError('Bitwa już trwa. Wpisz oblezenie <kod> status.')
            raise ValueError('Inna gildia oblega tę twierdzę. Spróbuj później.')
        conn.execute('DELETE FROM siege_battles_v1321 WHERE fort=?',(fort,))
        conn.execute('INSERT INTO siege_battles_v1321(fort,clan_id,phase,remaining,turns,started_at,updated_at) VALUES(?,?,1,?,0,?,?)',
                     (fort,clan,phase_strength(conn,fort,1),now,now))
        return phase_strength(conn,fort,1)


def siege_order(conn, clan, fort, order, *, now=None):
    now=int(time.time()) if now is None else now
    if order not in ORDERS:raise ValueError('Nieznany rozkaz.')
    with base.atomic(conn):
        b=conn.execute('SELECT * FROM siege_battles_v1321 WHERE fort=? AND clan_id=?',(fort,clan)).fetchone()
        if b is None:raise ValueError('Brak twojej rozpoczętej bitwy o tę twierdzę.')
        if now-int(b['started_at'])>=12*3600:raise ValueError('Bitwa wygasła. Rozpocznij ją ponownie.')
        army={r['troop']:int(r['quantity']) for r in conn.execute('SELECT troop,quantity FROM empire_armies_v1320 WHERE clan_id=?',(clan,)).fetchall()}
        if not any(army.values()):raise ValueError('Twoja armia została rozbita.')
        phase=int(b['phase'])
        weights=ORDERS[order]
        power=round(sum(army.get(kind,0)*base.TROOPS[kind][1]*1000*weights[i] for i,kind in enumerate(('wojownik','lucznik','mag'))))
        if order==BONUS[phase-1][0]:power=round(power*BONUS[phase-1][1])
        dmg=max(1000,power)
        # Real attrition, stored on each order; defensive stance reduces losses.
        fraction = (.008 if order=='oslona' else .018) + (.006 if dmg<max(1,int(b['remaining']))//2 else 0)
        casualties={k:min(v,max(1,int(v*fraction))) for k,v in army.items() if v>0}
        for kind,lost in casualties.items():
            conn.execute('UPDATE empire_armies_v1320 SET quantity=quantity-? WHERE clan_id=? AND troop=?',(lost,clan,kind))
        rest=max(0,int(b['remaining'])-dmg)
        turn=int(b['turns'])+1
        end='continue'
        if rest==0:
            if phase==3:
                end='victory'
                conn.execute('INSERT INTO empire_forts_v1320(fort,clan_id,walls,conquered_at) VALUES(?,?,1,?) '
                             'ON CONFLICT(fort) DO UPDATE SET clan_id=excluded.clan_id,walls=1,conquered_at=excluded.conquered_at',(fort,clan,now))
            else:
                phase+=1
                rest=phase_strength(conn,fort,phase)
        if turn>=24 or not any(army[k]>casualties.get(k,0) for k in army):end='retreat' if end!='victory' else end
        if end!='continue':
            conn.execute('DELETE FROM siege_battles_v1321 WHERE fort=?',(fort,))
            conn.execute('INSERT INTO empire_sieges_v1320(clan_id,fort,ready_at,victories) VALUES(?,?,?,?) '
                         'ON CONFLICT(clan_id,fort) DO UPDATE SET ready_at=excluded.ready_at,victories=victories+excluded.victories',
                         (clan,fort,now+4*3600,int(end=='victory')))
        else:
            conn.execute('UPDATE siege_battles_v1321 SET phase=?,remaining=?,turns=?,updated_at=? WHERE fort=?',(phase,rest,turn,now,fort))
        return {'outcome':end,'phase':phase,'remaining':rest,'damage':dmg,'turn':turn,'casualties':casualties}


def retreat(conn, clan, fort, *, now=None):
    now=int(time.time()) if now is None else now
    with base.atomic(conn):
        cur=conn.execute('DELETE FROM siege_battles_v1321 WHERE fort=? AND clan_id=?',(fort,clan))
        if cur.rowcount!=1:raise ValueError('Nie prowadzisz tutaj oblężenia.')
        conn.execute('INSERT INTO empire_sieges_v1320(clan_id,fort,ready_at) VALUES(?,?,?) '
                     'ON CONFLICT(clan_id,fort) DO UPDATE SET ready_at=excluded.ready_at',(clan,fort,now+4*3600))


def migrate_fleet(conn, account):
    """Lazy import of the current Ocean 2.0 ship; repeated calls are harmless."""
    old=conn.execute('SELECT id FROM shipyard_ships_v1321 WHERE account_id=? LIMIT 1',(account,)).fetchone()
    if old:return
    legacy=conn.execute('SELECT * FROM ocean_ship_v1000 WHERE account_id=?',(account,)).fetchone()
    if not legacy or not int(legacy['owned']):return
    previous=conn.execute('SELECT ship_class FROM shipyard_fleet_v1320 WHERE account_id=?',(account,)).fetchone()
    tier=min(3,max(0,int(previous['ship_class']) if previous else 0))
    previous_tx=conn.in_transaction
    conn.execute('INSERT INTO shipyard_ships_v1321(account_id,ship_class,name,hull,sails,cargo,navigation,active,built_at) '
                 'VALUES(?,?,?,?,?,?,?,1,?)',(account,tier,CLASSES[tier].capitalize(),*(int(legacy[x]) for x in MODULES),int(time.time())))
    if not previous_tx:conn.commit()


def fleet_rows(conn, account):
    migrate_fleet(conn,account)
    return conn.execute('SELECT * FROM shipyard_ships_v1321 WHERE account_id=? ORDER BY id',(account,)).fetchall()


def snapshot_active(conn, account):
    row=conn.execute('SELECT id FROM shipyard_ships_v1321 WHERE account_id=? AND active=1',(account,)).fetchone()
    if not row:return
    legacy=conn.execute('SELECT * FROM ocean_ship_v1000 WHERE account_id=?',(account,)).fetchone()
    if legacy:
        conn.execute('UPDATE shipyard_ships_v1321 SET hull=?,sails=?,cargo=?,navigation=? WHERE id=?',
                     (*(int(legacy[m]) for m in MODULES),row['id']))


def choose_ship(conn, account, ship_id):
    with base.atomic(conn):
        migrate_fleet(conn,account)
        selected=conn.execute('SELECT * FROM shipyard_ships_v1321 WHERE id=? AND account_id=?',(ship_id,account)).fetchone()
        if not selected:raise ValueError('Nie masz statku o podanym numerze.')
        if selected['active']:return selected['name']
        snapshot_active(conn,account)
        conn.execute('UPDATE shipyard_ships_v1321 SET active=0 WHERE account_id=?',(account,))
        conn.execute('UPDATE shipyard_ships_v1321 SET active=1 WHERE id=?',(ship_id,))
        conn.execute('UPDATE ocean_ship_v1000 SET owned=1,hull=?,sails=?,cargo=?,navigation=? WHERE account_id=?',
                     (*(int(selected[m]) for m in MODULES),account))
        conn.execute('INSERT INTO shipyard_fleet_v1320(account_id,ship_class,last_build) VALUES(?,?,?) '
                     'ON CONFLICT(account_id) DO UPDATE SET ship_class=excluded.ship_class',(account,selected['ship_class'],int(time.time())))
        return selected['name']


def rename_ship(conn, account, ship_id, name):
    name=' '.join(str(name).strip().split())
    if not (2<=len(name)<=36 and all(ch.isalnum() or ch in ' -_' for ch in name)):
        raise ValueError('Nazwa 2–36 znaków: litery, cyfry, spacje, myślnik.')
    with base.atomic(conn):
        cur=conn.execute('UPDATE shipyard_ships_v1321 SET name=? WHERE id=? AND account_id=?',(name,ship_id,account))
        if cur.rowcount!=1:raise ValueError('Nie masz takiego statku.')


def build_ship(conn, account, kind, sources, *, now=None):
    if kind not in base.SHIPS:raise ValueError('Nieznana klasa statku.')
    now=int(time.time()) if now is None else now
    tier,cost,materials=base.SHIPS[kind]
    with base.atomic(conn):
        migrate_fleet(conn,account)
        for item,qty in materials.items():
            if sources.get(item) not in base.STORAGE:raise ValueError('Brak wymaganych materiałów.')
            base.take(conn,account,item,qty,sources[item])
        remaining=_pay(conn,account,cost)
        snapshot_active(conn,account)
        conn.execute('UPDATE shipyard_ships_v1321 SET active=0 WHERE account_id=?',(account,))
        cur=conn.execute('INSERT INTO shipyard_ships_v1321(account_id,ship_class,name,active,built_at) VALUES(?,?,?,1,?)',
                         (account,tier,kind.capitalize(),now))
        conn.execute('INSERT INTO ocean_ship_v1000(account_id,owned,hull,sails,cargo,navigation) VALUES(?,1,1,1,1,1) '
                     'ON CONFLICT(account_id) DO UPDATE SET owned=1,hull=1,sails=1,cargo=1,navigation=1',(account,))
        conn.execute('INSERT INTO shipyard_fleet_v1320(account_id,ship_class,last_build) VALUES(?,?,?) '
                     'ON CONFLICT(account_id) DO UPDATE SET ship_class=excluded.ship_class,last_build=excluded.last_build',
                     (account,tier,now))
        return cur.lastrowid,remaining
