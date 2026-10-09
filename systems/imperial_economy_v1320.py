# -*- coding: utf-8 -*-
"""v1.32.0: persistent imperial territories, army, player market and shipyards.

This module owns no world generator and never rewrites legacy tables or saves.
New tables are additive; escrow and payments use one SQLite transaction.
"""
from __future__ import annotations

from contextlib import contextmanager
import time

FORTS = {
    'bazalt': ('Bastion Bazaltu', 120, 300_000),
    'chmury': ('Twierdza Chmur', 230, 550_000),
    'valdoria': ('Warownia Valdorii', 320, 900_000),
    'orkowie': ('Warownia Czterech Klanów', 400, 1_300_000),
}
TROOPS = {'wojownik': (14000, 3), 'lucznik': (19000, 4), 'mag': (26000, 6)}
SHIPS = {
    'bryg': (1, 160000, {'oak_plank': 10, 'iron_ingot': 5}),
    'fregata': (2, 450000, {'oak_plank': 20, 'iron_ingot': 12, 'cobalt_ingot': 3}),
    'galeon': (3, 950000, {'oak_plank': 35, 'iron_ingot': 22, 'eternium_ingot': 3}),
}
STORAGE = ('inventory', 'craftbox', 'net', 'bag', 'woodpile', 'herbbag')


def init(conn):
    """Idempotent, additive schema. No modification of old save layout."""
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS empire_armies_v1320 (
       clan_id INTEGER NOT NULL, troop TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 0,
       PRIMARY KEY (clan_id,troop));
    CREATE TABLE IF NOT EXISTS empire_forts_v1320 (
       fort TEXT PRIMARY KEY, clan_id INTEGER NOT NULL, walls INTEGER NOT NULL DEFAULT 1,
       conquered_at INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS empire_sieges_v1320 (
       clan_id INTEGER NOT NULL, fort TEXT NOT NULL, ready_at INTEGER NOT NULL DEFAULT 0,
       victories INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(clan_id,fort));
    CREATE TABLE IF NOT EXISTS market_listings_v1320 (
       id INTEGER PRIMARY KEY AUTOINCREMENT, seller INTEGER NOT NULL,
       item_id TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0),
       container TEXT NOT NULL, price INTEGER NOT NULL CHECK(price>0),
       state TEXT NOT NULL DEFAULT 'active', buyer INTEGER,
       created_at INTEGER NOT NULL, closed_at INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS market_basis_v1320 (
       listing_id INTEGER NOT NULL, paid_silver INTEGER NOT NULL, quantity INTEGER NOT NULL,
       PRIMARY KEY(listing_id,paid_silver));
    CREATE INDEX IF NOT EXISTS idx_market_active_v1320 ON market_listings_v1320(state,id);
    CREATE TABLE IF NOT EXISTS market_payouts_v1320 (
       account_id INTEGER PRIMARY KEY, coins INTEGER NOT NULL DEFAULT 0 CHECK(coins>=0));
    CREATE TABLE IF NOT EXISTS shipyard_fleet_v1320 (
       account_id INTEGER PRIMARY KEY, ship_class INTEGER NOT NULL DEFAULT 0,
       last_build INTEGER NOT NULL DEFAULT 0);
    ''')
    conn.commit()


@contextmanager
def atomic(conn):
    """Savepoint protects caller-owned transactions and can undo all escrow updates."""
    conn.execute('SAVEPOINT empire1320')
    try:
        yield
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT empire1320')
        conn.execute('RELEASE SAVEPOINT empire1320')
        raise
    else:
        conn.execute('RELEASE SAVEPOINT empire1320')
        conn.commit()


def select_source(conn, account, item, qty, *, allowed=STORAGE):
    for box in allowed:
        if box=='inventory':
            row=conn.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',
                             (account,item)).fetchone()
        else:
            row=conn.execute('SELECT quantity FROM profession_storage WHERE account_id=? AND container=? AND item_id=?',
                             (account,box,item)).fetchone()
        if row and int(row['quantity'])>=qty:
            return box
    return None


def take(conn, account, item, qty, box):
    if box=='inventory':
        cur=conn.execute('UPDATE inventory SET quantity=quantity-? WHERE account_id=? AND item_id=? AND quantity>=?',
                         (qty,account,item,qty))
        conn.execute('DELETE FROM inventory WHERE account_id=? AND item_id=? AND quantity=0',(account,item))
    else:
        if box not in STORAGE: raise ValueError('Niedozwolony magazyn.')
        cur=conn.execute('UPDATE profession_storage SET quantity=quantity-? WHERE account_id=? AND container=? AND item_id=? AND quantity>=?',
                         (qty,account,box,item,qty))
        conn.execute('DELETE FROM profession_storage WHERE account_id=? AND container=? AND item_id=? AND quantity=0',
                     (account,box,item))
    if cur.rowcount != 1: raise ValueError('Brak przedmiotów w magazynie.')


def give(conn, account, item, qty, box):
    if box=='inventory':
        conn.execute('INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?) '
                     'ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity',
                     (account,item,qty))
    elif box in STORAGE:
        conn.execute('INSERT INTO profession_storage(account_id,container,item_id,quantity) VALUES(?,?,?,?) '
                     'ON CONFLICT(account_id,container,item_id) DO UPDATE SET quantity=quantity+excluded.quantity',
                     (account,box,item,qty))
    else: raise ValueError('Niedozwolony magazyn.')


def _escrow_basis(conn, seller, item, qty, listing):
    """Transfer purchase-cost lots into escrow to avoid double resale credits."""
    remains=qty
    for r in conn.execute('SELECT paid_silver,quantity FROM shop_purchase_lots_v1175 WHERE account_id=? AND item_id=? ORDER BY paid_silver',
                          (seller,item)).fetchall():
        n=min(remains,int(r['quantity']))
        if n<=0:break
        conn.execute('UPDATE shop_purchase_lots_v1175 SET quantity=quantity-? WHERE account_id=? AND item_id=? AND paid_silver=?',
                     (n,seller,item,r['paid_silver']))
        conn.execute('INSERT INTO market_basis_v1320(listing_id,paid_silver,quantity) VALUES(?,?,?)',
                     (listing,int(r['paid_silver']),n))
        remains-=n
    conn.execute('DELETE FROM shop_purchase_lots_v1175 WHERE account_id=? AND item_id=? AND quantity=0',(seller,item))


def _restore_basis(conn, listing, account, item):
    for r in conn.execute('SELECT paid_silver,quantity FROM market_basis_v1320 WHERE listing_id=?',(listing,)).fetchall():
        conn.execute('INSERT INTO shop_purchase_lots_v1175(account_id,item_id,paid_silver,quantity) VALUES(?,?,?,?) '
                     'ON CONFLICT(account_id,item_id,paid_silver) DO UPDATE SET quantity=quantity+excluded.quantity',
                     (account,item,int(r['paid_silver']),int(r['quantity'])))
    conn.execute('DELETE FROM market_basis_v1320 WHERE listing_id=?',(listing,))


def list_item(conn, seller, item, qty, price, source):
    if not (1<=qty<=1_000_000 and 1<=price<=10**15): raise ValueError('Nieprawidłowa ilość lub cena.')
    with atomic(conn):
        count=conn.execute("SELECT COUNT(*) FROM market_listings_v1320 WHERE seller=? AND state='active'",(seller,)).fetchone()[0]
        if count>=30: raise ValueError('Możesz wystawić maksymalnie 30 aktywnych ofert.')
        take(conn,seller,item,qty,source)
        cur=conn.execute('INSERT INTO market_listings_v1320(seller,item_id,quantity,container,price,created_at) '
                         'VALUES(?,?,?,?,?,?)',(seller,item,qty,source,price,int(time.time())))
        _escrow_basis(conn,seller,item,qty,cur.lastrowid)
        return cur.lastrowid


def purchase(conn, buyer, listing_id, available_coins):
    """Item transferred to buyer; seller proceeds held in durable payout escrow."""
    with atomic(conn):
        row=conn.execute('SELECT * FROM market_listings_v1320 WHERE id=? AND state=?',
                         (listing_id,'active')).fetchone()
        if row is None: raise ValueError('Oferta nie istnieje lub została zakończona.')
        if conn.execute("SELECT 1 FROM sqlite_master WHERE name='market_auctions_v1321'").fetchone() and conn.execute('SELECT 1 FROM market_auctions_v1321 WHERE listing_id=?',(listing_id,)).fetchone():
            raise ValueError('To licytacja. Wpisz aukcja licytuj <nr> <kwota>.')
        if row['seller']==buyer: raise ValueError('Nie kupujesz własnej oferty.')
        price=int(row['price'])
        from storage.db_schema import legacy_currency_to_coins
        wallet_row=conn.execute('SELECT silver,gold,mithril FROM characters WHERE account_id=?',(buyer,)).fetchone()
        if wallet_row is None:raise ValueError('Nie znaleziono portfela kupującego.')
        wallet=legacy_currency_to_coins(wallet_row['silver'],wallet_row['gold'],wallet_row['mithril'])
        if wallet<price: raise ValueError('Nie masz tyle monet.')
        cur=conn.execute('UPDATE market_listings_v1320 SET state=?,buyer=?,closed_at=? '
                         'WHERE id=? AND state=?',('sold',buyer,int(time.time()),listing_id,'active'))
        if cur.rowcount!=1: raise ValueError('Oferta została już zakończona.')
        give(conn,buyer,row['item_id'],row['quantity'],row['container'])
        _restore_basis(conn,listing_id,buyer,row['item_id'])
        conn.execute('INSERT INTO market_payouts_v1320(account_id,coins) VALUES(?,?) '
                     'ON CONFLICT(account_id) DO UPDATE SET coins=coins+excluded.coins',
                     (row['seller'],price))
        # Make deduction in the *same* transaction as ownership of the item.
        # Caller syncs the live character only after this succeeds.
        remain=wallet-price
        conn.execute('UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?',
                     (remain,buyer))
        return row,remain


def cancel(conn, seller, listing_id):
    with atomic(conn):
        row=conn.execute('SELECT * FROM market_listings_v1320 WHERE id=? AND seller=? AND state=?',
                         (listing_id,seller,'active')).fetchone()
        if row is None: raise ValueError('Nie masz takiej aktywnej oferty.')
        if conn.execute("SELECT 1 FROM sqlite_master WHERE name='market_auctions_v1321'").fetchone() and conn.execute('SELECT 1 FROM market_auctions_v1321 WHERE listing_id=?',(listing_id,)).fetchone():
            raise ValueError('Licytację anuluj przez aukcja anuluj <nr>, bez złożonych ofert.')
        conn.execute('UPDATE market_listings_v1320 SET state=?,closed_at=? WHERE id=?',
                     ('cancelled',int(time.time()),listing_id))
        give(conn,seller,row['item_id'],row['quantity'],row['container'])
        _restore_basis(conn,listing_id,seller,row['item_id'])
        return row


def take_payout(conn, account, current_coins):
    with atomic(conn):
        from storage.db_schema import legacy_currency_to_coins
        balance_row=conn.execute('SELECT silver,gold,mithril FROM characters WHERE account_id=?',(account,)).fetchone()
        if balance_row is None:raise ValueError('Nie znaleziono portfela sprzedającego.')
        current_coins=legacy_currency_to_coins(balance_row['silver'],balance_row['gold'],balance_row['mithril'])
        row=conn.execute('SELECT coins FROM market_payouts_v1320 WHERE account_id=?',(account,)).fetchone()
        amount=int(row['coins']) if row else 0
        if not amount:return 0,current_coins
        if current_coins+amount>8_000_000_000_000_000_000: raise ValueError('Saldo zbyt duże. Skontaktuj się z administracją.')
        conn.execute('UPDATE market_payouts_v1320 SET coins=0 WHERE account_id=?',(account,))
        new=current_coins+amount
        conn.execute('UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?',(new,account))
        return amount,new


def fort_strength(conn, fort):
    row=conn.execute('SELECT clan_id,walls FROM empire_forts_v1320 WHERE fort=?',(fort,)).fetchone()
    strength=FORTS[fort][2]
    defense=strength + (int(row['walls'])-1)*strength//5 if row else strength
    if row:
        from systems.living_empires_v1340 import garrison_strength
        defense += garrison_strength(conn,fort)
    return defense


def troop_strength(conn, clan):
    rows=conn.execute('SELECT troop,quantity FROM empire_armies_v1320 WHERE clan_id=?',(clan,)).fetchall()
    return sum(TROOPS[r['troop']][1]*int(r['quantity'])*1000 for r in rows if r['troop'] in TROOPS)


def siege_result(power, defender):
    return power>=defender
