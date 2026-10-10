# -*- coding: utf-8 -*-
"""Soulbound v1.36.0: bounded PvE trade, crafting orders and guild production.

All movements of goods/currency are escrowed in SQLite savepoints. No background
threads, no write to old schema, no player-versus-player market manipulation.
"""
from __future__ import annotations
import time
from data.catalogs import ITEMS
from systems import imperial_economy_v1320 as econ
from systems import imperial_economy_v1321 as fleet
from storage.db_schema import legacy_currency_to_coins

MAX_COIN = 8_000_000_000_000_000_000
SIX_HOURS = 21600
ROUTES = {
    'zelazo': ('Karawana Żelaza do Gor-Khaz', 'iron_ore', 30, 1200, 'land', 1800),
    'drewno': ('Karawana drewna do Podziemnego Królestwa', 'oak_log', 35, 1500, 'land', 1800),
    'ryby': ('Konwój ryb do Podniebnych Portów', 'salmon', 16, 2000, 'sea', 2700),
    'deski': ('Morski transport materiałów stoczniowych', 'oak_plank', 12, 1900, 'sea', 2700),
    'ziola': ('Dostawa kwiatów do Astralnej Enklawy', 'moonflower', 12, 2400, 'land', 1800),
}
ORDERS = {
    'uzbrojenie': ('Wyposażenie garnizonu', {'iron_ingot': 15, 'oak_plank': 8}, 8500),
    'okrety': ('Zamówienie części floty', {'oak_plank': 20, 'iron_ingot': 12}, 11500),
    'uczta': ('Wielka uczta królewska', {'salmon': 18, 'moonflower': 6}, 7800),
}
BUILDINGS = {
    'kopalnia': ('Kopalnia gildii', 'iron_ore', 12, 22000, 800),
    'tartak': ('Tartak gildii', 'oak_log', 10, 26000, 800),
    'farma': ('Ogrody gildii', 'moonflower', 3, 34000, 800),
    'warsztat': ('Warsztat gildii', 'iron_ingot', 3, 44000, 1000),
}


def init(conn):
    """Create only new tables; never migrate or truncate old character data."""
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS trade_convoys_v1360 (
      account_id INTEGER PRIMARY KEY, code TEXT NOT NULL, item_id TEXT NOT NULL,
      quantity INTEGER NOT NULL, reward INTEGER NOT NULL, transport TEXT NOT NULL,
      departed INTEGER NOT NULL, arrival INTEGER NOT NULL, defended INTEGER NOT NULL DEFAULT 0,
      complete INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS trade_cooldowns_v1360 (
      account_id INTEGER PRIMARY KEY, next_convoy INTEGER NOT NULL DEFAULT 0,
      next_order INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS trade_orders_v1360 (
      account_id INTEGER NOT NULL, code TEXT NOT NULL, completed_at INTEGER NOT NULL,
      PRIMARY KEY(account_id, code));
    CREATE TABLE IF NOT EXISTS trade_records_v1360 (
      account_id INTEGER PRIMARY KEY, convoys INTEGER NOT NULL DEFAULT 0,
      orders INTEGER NOT NULL DEFAULT 0, earned INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS guild_production_v1360 (
      clan_id INTEGER NOT NULL, building TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 0,
      last_collection INTEGER NOT NULL, PRIMARY KEY(clan_id, building));
    ''')
    conn.commit()


def _coins(conn, account):
    row=conn.execute('SELECT silver,gold,mithril FROM characters WHERE account_id=?',(account,)).fetchone()
    if row is None: raise ValueError('Brak portfela postaci.')
    return legacy_currency_to_coins(row['silver'],row['gold'],row['mithril'])


def _credit(conn, account, coins):
    assert 0 <= coins <= 10**15
    current=_coins(conn, account)
    if current+coins>MAX_COIN: raise ValueError('Za dużo monet w portfelu. Odbierz nagrodę później.')
    conn.execute('UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?',(current+coins,account))
    return current+coins


def _item_value(item):
    d=ITEMS.get(item,{})
    # Economy reward tied to authored item sale values, no unlimited multiplier
    return max(15,min(50000,max(int(d.get('sell_silver') or 0)+100*int(d.get('sell_gold') or 0),int(d.get('value') or 0))))


def demand(code, *, now=None):
    now=int(time.time()) if now is None else int(now)
    keys=list(ROUTES)+list(ORDERS)
    index=keys.index(code)
    # Stable per six-hour window and route, not random per request.
    tier=(now//SIX_HOURS*7 + index*11)%5
    return (85,95,105,115,125)[tier]


def caravan_quotes(*, now=None):
    result=[]
    for code,(name,item,qty,base,kind,seconds) in ROUTES.items():
        price=max(qty*_item_value(item),base)*demand(code,now=now)//100
        result.append((code,name,item,qty,price,kind,seconds))
    return result


def _cooldown(conn, account):
    return conn.execute('SELECT next_convoy,next_order FROM trade_cooldowns_v1360 WHERE account_id=?',(account,)).fetchone()


def _consume(conn, account, item, qty):
    """Withdraw goods across inventory and profession stores in one savepoint."""
    remaining=qty
    used=[]
    for box in econ.STORAGE:
        if box=='inventory':
            r=conn.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',(account,item)).fetchone()
        else:
            r=conn.execute('SELECT quantity FROM profession_storage WHERE account_id=? AND container=? AND item_id=?',(account,box,item)).fetchone()
        n=min(remaining,max(0,int(r[0]))) if r else 0
        if n:
            econ.take(conn,account,item,n,box)
            used.append(f'{box} x{n}')
            remaining-=n
        if not remaining: break
    if remaining:
        raise ValueError(f'Brakuje {remaining} szt. {ITEMS[item]["name"]} (sprawdzono ekwipunek i magazyny).')
    return ', '.join(used)


def _check_ship(conn, account, qty):
    # Ocean 4.0 fleet belongs to same account; require undamaged flagship.
    ships=fleet.fleet_rows(conn, account)
    ship=next((s for s in ships if int(s['active'])),None)
    if ship is None: raise ValueError('Do transportu morskiego potrzebujesz aktywnego statku ze stoczni.')
    from systems import ocean4_v1350 as ocean
    if ocean._hp(conn,account,ship)<=0: raise ValueError('Najpierw napraw aktywny okręt.')
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ocean4_battles_v1350'").fetchone() and conn.execute('SELECT 1 FROM ocean4_battles_v1350 WHERE account_id=? AND active=1',(account,)).fetchone():
        raise ValueError('Nie wysyłaj transportu podczas aktywnej bitwy Ocean 4.0.')
    capacity=12+int(ship['ship_class'])*12+int(ship['cargo'])*8
    if qty>capacity:raise ValueError(f'Ładownia za mała: {capacity} jednostek, potrzebne {qty}.')
    return ship


def start_convoy(conn, account, code, *, now=None):
    now=int(time.time()) if now is None else int(now)
    if code not in ROUTES:raise ValueError('Nieznany szlak karawany.')
    name,item,qty,base,kind,seconds=ROUTES[code]
    with econ.atomic(conn):
        if conn.execute('SELECT 1 FROM trade_convoys_v1360 WHERE account_id=?',(account,)).fetchone():
            raise ValueError('Masz już aktywny lub nieodebrany transport.')
        cd=_cooldown(conn, account)
        if cd and int(cd['next_convoy'])>now:
            raise ValueError(f'Następny transport za {int(cd["next_convoy"])-now} sekund.')
        if kind=='sea':_check_ship(conn,account,qty)
        source=_consume(conn,account,item,qty)
        reward=max(qty*_item_value(item),base)*demand(code,now=now)//100
        # Player hands over goods NOW, before the voyage starts.
        conn.execute('INSERT INTO trade_convoys_v1360(account_id,code,item_id,quantity,reward,transport,departed,arrival) VALUES(?,?,?,?,?,?,?,?)',
                     (account,code,item,qty,reward,kind,now,now+seconds))
        conn.execute('INSERT INTO trade_cooldowns_v1360(account_id,next_convoy) VALUES(?,?) '
                     'ON CONFLICT(account_id) DO UPDATE SET next_convoy=excluded.next_convoy',(account,now+max(3600,seconds)))
        return {'name':name,'reward':reward,'arrival':now+seconds,'source':source}


def convoy(conn,account):
    return conn.execute('SELECT * FROM trade_convoys_v1360 WHERE account_id=?',(account,)).fetchone()


def defend_convoy(conn, account, *, now=None):
    now=int(time.time()) if now is None else int(now)
    with econ.atomic(conn):
        row=convoy(conn,account)
        if row is None:raise ValueError('Nie prowadzisz transportu.')
        if now>=int(row['arrival']):raise ValueError('Transport już dotarł. Wpisz gospodarka odbierz.')
        if int(row['defended']):raise ValueError('Eskorta już odparła napad na tej trasie.')
        # Strategic PvE protection, no global world mob nor unbounded reward.
        conn.execute('UPDATE trade_convoys_v1360 SET defended=1 WHERE account_id=?',(account,))
        return 'Eskorta odparła atak bandytów NPC. Towary są bezpieczniejsze.'


def collect_convoy(conn, account, *, now=None):
    now=int(time.time()) if now is None else int(now)
    with econ.atomic(conn):
        row=convoy(conn,account)
        if row is None:raise ValueError('Nie masz transportu do odebrania.')
        if now<int(row['arrival']):raise ValueError(f'Transport dotrze za {int(row["arrival"])-now} sekund.')
        # Unprotected routes yield 80%; defense keeps 100%. Goods do not return.
        reward=int(row['reward'])*(100 if int(row['defended']) else 80)//100
        balance=_credit(conn,account,reward)
        conn.execute('DELETE FROM trade_convoys_v1360 WHERE account_id=?',(account,))
        conn.execute('INSERT INTO trade_records_v1360(account_id,convoys,earned) VALUES(?,1,?) '
                     'ON CONFLICT(account_id) DO UPDATE SET convoys=convoys+1,earned=earned+excluded.earned',(account,reward))
        return reward,balance


def order_reward_v1406(code, *, now=None):
    name, ingredients, base = ORDERS[code]
    cost = sum(qty*_item_value(item) for item,qty in ingredients.items())
    # A kingdom's major order must cover the materials AND reward the labor;
    # keep six-hour demand rotation and the existing 2h payout cooldown.
    return max(base*4, cost*3)*demand(code,now=now)//100


def order_quotes(*,now=None):
    return [(code,name,ingredients,order_reward_v1406(code,now=now))
            for code,(name,ingredients,price) in ORDERS.items()]


def finish_order(conn,account,code,*,now=None):
    now=int(time.time()) if now is None else int(now)
    if code not in ORDERS:raise ValueError('Nie ma takiego zamówienia.')
    with econ.atomic(conn):
        cd=_cooldown(conn,account)
        if cd and int(cd['next_order'])>now:
            raise ValueError(f'Kolejne zamówienie za {int(cd["next_order"])-now} sekund.')
        name,ingredients,base=ORDERS[code]
        # Reserve ALL ingredients before paying; savepoint rolls back shortfalls.
        for item,qty in ingredients.items():
            _consume(conn,account,item,qty)
        price=order_reward_v1406(code,now=now)
        balance=_credit(conn,account,price)
        conn.execute('INSERT INTO trade_cooldowns_v1360(account_id,next_order) VALUES(?,?) '
                     'ON CONFLICT(account_id) DO UPDATE SET next_order=excluded.next_order',(account,now+7200))
        conn.execute('INSERT INTO trade_orders_v1360(account_id,code,completed_at) VALUES(?,?,?) '
                     'ON CONFLICT(account_id,code) DO UPDATE SET completed_at=excluded.completed_at',(account,code,now))
        conn.execute('INSERT INTO trade_records_v1360(account_id,orders,earned) VALUES(?,1,?) '
                     'ON CONFLICT(account_id) DO UPDATE SET orders=orders+1,earned=earned+excluded.earned',(account,price))
        return name,price,balance


def production_levels(conn,clan):
    return {r['building']:(int(r['level']),int(r['last_collection'])) for r in conn.execute(
        'SELECT building,level,last_collection FROM guild_production_v1360 WHERE clan_id=?',(clan,)).fetchall()}


def upgrade_building(conn,clan,building,*,now=None):
    now=int(time.time()) if now is None else int(now)
    if building not in BUILDINGS:raise ValueError('Nieznany budynek gildii.')
    with econ.atomic(conn):
        row=conn.execute('SELECT level FROM guild_production_v1360 WHERE clan_id=? AND building=?',(clan,building)).fetchone()
        level=int(row['level']) if row else 0
        if level>=10:raise ValueError('Budynek osiągnął maksymalny poziom 10.')
        if row and conn.execute('SELECT last_collection FROM guild_production_v1360 WHERE clan_id=? AND building=?',(clan,building)).fetchone()[0] <= now-SIX_HOURS:
            raise ValueError('Najpierw odbierz gotową produkcję, aby nie przeliczyć starych cykli na nowy poziom.')
        cost=BUILDINGS[building][3]*(level+1)**2
        changed=conn.execute('UPDATE player_clans SET treasury=treasury-? WHERE id=? AND treasury>=?',(cost,clan,cost))
        if changed.rowcount!=1:raise ValueError('Za mało pieniędzy w skarbcu gildii.')
        conn.execute('INSERT INTO guild_production_v1360(clan_id,building,level,last_collection) VALUES(?,?,1,?) '
                     'ON CONFLICT(clan_id,building) DO UPDATE SET level=level+1',(clan,building,now))
        return level+1,cost


def collect_production(conn,clan,*,now=None):
    now=int(time.time()) if now is None else int(now)
    with econ.atomic(conn):
        if conn.execute('SELECT 1 FROM player_clans WHERE id=?',(clan,)).fetchone() is None:
            raise ValueError('Nie znaleziono gildii.')
        output=[]
        for r in conn.execute('SELECT building,level,last_collection FROM guild_production_v1360 WHERE clan_id=?',(clan,)).fetchall():
            building=r['building'];level=int(r['level'])
            name,item,per_level,_,maintenance=BUILDINGS[building]
            delta=max(0,now-int(r['last_collection']))
            cycles=min(4,delta//SIX_HOURS)
            if not cycles:continue
            qty=level*per_level*cycles
            cost=maintenance*level*cycles
            treasury=conn.execute('UPDATE player_clans SET treasury=treasury-? WHERE id=? AND treasury>=?',(cost,clan,cost))
            if treasury.rowcount!=1:
                # Insufficient maintenance: no free materials, but do not discard elapsed time.
                continue
            conn.execute('INSERT INTO player_clan_bank(clan_id,item_id,quantity) VALUES(?,?,?) '
                         'ON CONFLICT(clan_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity',(clan,item,qty))
            conn.execute('UPDATE guild_production_v1360 SET last_collection=? WHERE clan_id=? AND building=?',
                         (now-(delta%SIX_HOURS),clan,building))
            output.append((name,item,qty,cost))
        return output


def records(conn,account):
    return conn.execute('SELECT convoys,orders,earned FROM trade_records_v1360 WHERE account_id=?',(account,)).fetchone()
