# -*- coding: utf-8 -*-
"""Ocean 4.0: transactional, resumable PvE fleet combat. No legacy save mutation.

Battle damage is stored separately from Ocean 2.0 voyages/modules; no PvP.
"""
from __future__ import annotations

import time
from systems.imperial_economy_v1320 import atomic
from systems.imperial_economy_v1321 import fleet_rows, snapshot_active, _wallet, _pay

ENEMIES = {
    'korsarze': ('Eskadra Czarnych Korsarzy', 160000, 7200, 27000, 'boarding', 21000),
    'blokada': ('Żelazna Blokada Portowa', 300000, 12500, 53000, 'siege', 41000),
    'kraken': ('Kraken Głębinowego Rozłamu', 490000, 15800, 90000, 'monster', 66000),
    'lewiatan': ('Lewiatan Bezdennego Prądu', 850000, 25500, 155000, 'monster', 102000),
    'smok': ('Smok Szafirowych Sztormów', 1350000, 38500, 270000, 'monster', 170000),
}
MOVES = ('salwa', 'manewr', 'oslona', 'abordaz')
MAX_ESCORTS = 2
COOLDOWN = 2 * 3600
MATERIALS = {'korsarze': 'iron_ingot', 'blokada': 'cobalt_ingot', 'kraken':'v1000_abyss_pearl', 'lewiatan':'v1000_sunken_relic', 'smok':'v1000_navigator_seal'}


def init(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS ocean4_escort_v1350 (
      account_id INTEGER NOT NULL, ship_id INTEGER NOT NULL,
      PRIMARY KEY(account_id, ship_id));
    CREATE TABLE IF NOT EXISTS ocean4_ship_condition_v1350 (
      ship_id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL,
      hp INTEGER NOT NULL CHECK(hp>=0));
    CREATE TABLE IF NOT EXISTS ocean4_battles_v1350 (
      account_id INTEGER PRIMARY KEY, enemy TEXT NOT NULL,
      enemy_hp INTEGER NOT NULL, enemy_max_hp INTEGER NOT NULL,
      turn INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
      started_at INTEGER NOT NULL, resolved_at INTEGER NOT NULL DEFAULT 0,
      last_outcome TEXT NOT NULL DEFAULT '', reward INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS ocean4_battle_ships_v1350 (
      account_id INTEGER NOT NULL, ship_id INTEGER NOT NULL,
      PRIMARY KEY(account_id,ship_id));
    CREATE TABLE IF NOT EXISTS ocean4_records_v1350 (
      account_id INTEGER NOT NULL, enemy TEXT NOT NULL,
      victories INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(account_id,enemy));
    ''')
    conn.commit()


def max_hp(row):
    return 64000 + int(row['ship_class']) * 52000 + int(row['hull']) * 21000


def _owned(conn, account):
    return {int(r['id']): r for r in fleet_rows(conn, account)}


def _hp(conn, account, ship):
    row = conn.execute('SELECT hp FROM ocean4_ship_condition_v1350 WHERE ship_id=? AND account_id=?',
                       (ship['id'], account)).fetchone()
    return min(max_hp(ship), int(row['hp'])) if row else max_hp(ship)


def _set_hp(conn, account, ship_id, hp):
    conn.execute('INSERT INTO ocean4_ship_condition_v1350(ship_id,account_id,hp) VALUES(?,?,?) '
                 'ON CONFLICT(ship_id) DO UPDATE SET hp=excluded.hp,account_id=excluded.account_id',
                 (ship_id, account, max(0,int(hp))))


def _active_battle(conn, account):
    return conn.execute('SELECT * FROM ocean4_battles_v1350 WHERE account_id=?',(account,)).fetchone()


def _selected(conn, account, owned=None):
    owned = _owned(conn, account) if owned is None else owned
    flagship = next((k for k,v in owned.items() if int(v['active'])), None)
    escorts = [int(r['ship_id']) for r in conn.execute('SELECT ship_id FROM ocean4_escort_v1350 WHERE account_id=? ORDER BY ship_id',(account,))]
    return ([flagship] if flagship is not None else []) + [i for i in escorts if i in owned and i != flagship][:MAX_ESCORTS]


def fleet_status(conn, account):
    owned = _owned(conn, account)
    active = next((i for i,s in owned.items() if s['active']), None)
    escorts = {int(r[0]) for r in conn.execute('SELECT ship_id FROM ocean4_escort_v1350 WHERE account_id=?',(account,))}
    return [{'id':i,'name':s['name'],'class':int(s['ship_class']), 'hp':_hp(conn,account,s),
             'max_hp':max_hp(s),'active':i==active,'escort':i in escorts} for i,s in sorted(owned.items())]


def escort(conn, account, ship_id, *, enable=True):
    with atomic(conn):
        battle = _active_battle(conn, account)
        if battle and battle['active']:
            raise ValueError('Nie zmieniaj eskorty w trakcie bitwy.')
        owned = _owned(conn,account)
        if ship_id not in owned: raise ValueError('Nie masz statku o takim numerze.')
        if owned[ship_id]['active']:raise ValueError('Okręt flagowy nie może być swoją eskortą.')
        if enable:
            already=conn.execute('SELECT 1 FROM ocean4_escort_v1350 WHERE account_id=? AND ship_id=?', (account,ship_id)).fetchone()
            if already:return
            if _hp(conn,account,owned[ship_id])<=0:raise ValueError('Najpierw napraw zatopiony okręt eskorty.')
            current = conn.execute('SELECT COUNT(*) FROM ocean4_escort_v1350 WHERE account_id=?',(account,)).fetchone()[0]
            if current>=MAX_ESCORTS:raise ValueError('Maksymalnie dwa okręty eskortowe. Odłącz jeden.')
            conn.execute('INSERT OR IGNORE INTO ocean4_escort_v1350(account_id,ship_id) VALUES(?,?)',(account,ship_id))
        else:
            conn.execute('DELETE FROM ocean4_escort_v1350 WHERE account_id=? AND ship_id=?',(account,ship_id))


def repair(conn, account, ship_id):
    with atomic(conn):
        battle=_active_battle(conn,account)
        if battle and battle['active']:raise ValueError('Naprawy wymagają zakończenia bitwy.')
        owned=_owned(conn,account)
        if ship_id not in owned:raise ValueError('Nie masz tego statku.')
        old=_hp(conn,account,owned[ship_id]);missing=max_hp(owned[ship_id])-old
        if not missing:return 0, _wallet(conn,account)
        cost=max(500, (missing+7)//8)
        remain=_pay(conn,account,cost)
        _set_hp(conn,account,ship_id,max_hp(owned[ship_id]))
        return cost,remain


def begin(conn, account, enemy, *, now=None):
    now=int(time.time()) if now is None else int(now)
    if enemy not in ENEMIES:raise ValueError('Nieznany wróg. Wpisz ocean4 cele.')
    with atomic(conn):
        battle=_active_battle(conn,account)
        if battle and battle['active']:raise ValueError('Trwa już bitwa. Wpisz ocean4 status.')
        if battle and now-int(battle['resolved_at'])<COOLDOWN:
            raise ValueError(f'Flota odpoczywa jeszcze {COOLDOWN-(now-int(battle["resolved_at"]))} sekund.')
        owned=_owned(conn,account)
        selected=_selected(conn,account,owned)
        if not selected:raise ValueError('Najpierw kup statek w porcie.')
        if len(set(selected))!=len(selected):raise ValueError('Eskorta powtarza okręt flagowy.')
        if any(_hp(conn,account,owned[i])==0 for i in selected):raise ValueError('Napraw uszkodzony okręt przed bitwą.')
        name,ehp,attack,reward,kind,_threat=ENEMIES[enemy]
        # Larger fleets attract stronger fleets and monsters: no trivial auto-wins.
        hp=int(ehp*(1+.38*(len(selected)-1)))
        conn.execute('INSERT INTO ocean4_battles_v1350(account_id,enemy,enemy_hp,enemy_max_hp,turn,active,started_at,resolved_at,last_outcome,reward) '
                     'VALUES(?,?,?,?,0,1,?,0,\'\',0) ON CONFLICT(account_id) DO UPDATE SET enemy=excluded.enemy,enemy_hp=excluded.enemy_hp,enemy_max_hp=excluded.enemy_max_hp,turn=0,active=1,started_at=excluded.started_at,resolved_at=0,last_outcome=\'\',reward=0',
                     (account,enemy,hp,hp,now))
        conn.execute('DELETE FROM ocean4_battle_ships_v1350 WHERE account_id=?',(account,))
        for i in selected:conn.execute('INSERT INTO ocean4_battle_ships_v1350(account_id,ship_id) VALUES(?,?)',(account,i))
        return name,hp,len(selected)


def battle_state(conn,account):
    battle=_active_battle(conn,account)
    if not battle:return None
    owned=_owned(conn,account)
    ships=[]
    for r in conn.execute('SELECT ship_id FROM ocean4_battle_ships_v1350 WHERE account_id=? ORDER BY ship_id',(account,)):
        if r['ship_id'] in owned:
            s=owned[r['ship_id']];ships.append((s['name'],_hp(conn,account,s),max_hp(s)))
    return {'enemy':battle['enemy'],'name':ENEMIES[battle['enemy']][0], 'enemy_hp':battle['enemy_hp'],
            'enemy_max_hp':battle['enemy_max_hp'],'turn':battle['turn'],'active':bool(battle['active']),
            'outcome':battle['last_outcome'],'reward':battle['reward'],'ships':ships}


def action(conn, account, move, *, now=None):
    now=int(time.time()) if now is None else int(now)
    if move not in MOVES:raise ValueError('Rozkazy: salwa, manewr, oslona, abordaz.')
    with atomic(conn):
        b=_active_battle(conn,account)
        if not b or not b['active']:raise ValueError('Brak aktywnej bitwy. Wpisz ocean4 atak <cel>.')
        name,_,enemy_attack,reward,kind,_=ENEMIES[b['enemy']]
        if move=='abordaz' and kind=='monster':raise ValueError('Nie można abordażować morskiego potwora!')
        if move=='abordaz' and int(b['enemy_hp'])>int(b['enemy_max_hp'])*.45:
            raise ValueError('Najpierw osłab wrogie okręty do 45% wytrzymałości.')
        owned=_owned(conn,account)
        ship_ids=[int(r[0]) for r in conn.execute('SELECT ship_id FROM ocean4_battle_ships_v1350 WHERE account_id=?',(account,))]
        ships=[owned[i] for i in ship_ids if i in owned and _hp(conn,account,owned[i])>0]
        if not ships:
            conn.execute("UPDATE ocean4_battles_v1350 SET active=0,resolved_at=?,last_outcome='porazka' WHERE account_id=?",(now,account))
            return {'outcome':'porazka','damage':0,'enemy_damage':0,'losses':[], 'reward':0}
        turn=int(b['turn'])+1
        power=sum((18000 + 8000*int(s['ship_class']) + 5200*int(s['hull']) + 1200*int(s['navigation'])) for s in ships)
        speed=sum(int(s['sails']) for s in ships)
        if move=='salwa':damage=power
        elif move=='manewr':damage=round(power*.77)+speed*1100
        elif move=='oslona':damage=round(power*.35)
        else:damage=round(power*1.55)
        # Boss mechanics are audible/visible through a plain-text battle report.
        hazard=(turn%3==0 and kind=='monster')
        counter=int(enemy_attack*(1+.06*turn)*(1.65 if hazard else 1))
        if move=='oslona':counter=round(counter*.34)
        elif move=='manewr':counter=round(counter*.63)
        if kind=='siege' and turn%4==0:counter=round(counter*1.3)
        new_hp=max(0,int(b['enemy_hp'])-damage)
        losses=[]
        # Enemy gets no counterattack after the decisive blow.
        if new_hp>0:
            alive=len(ships)
            for s in ships:
                harm=max(1000,(counter+alive-1)//alive)
                if move=='manewr': harm=max(500,harm-int(s['sails'])*700)
                before=_hp(conn,account,s)
                after=max(0,before-harm)
                _set_hp(conn,account,int(s['id']),after)
                losses.append((s['name'],after,max_hp(s)))
        else:
            losses=[(s['name'],_hp(conn,account,s),max_hp(s)) for s in ships]
        surviving = [s for s in ships if _hp(conn,account,s)>0]
        outcome='trwa'
        earned=0
        if new_hp==0:
            outcome='zwyciestwo';earned=reward
            # Persist both reward and resolution atomically, once only.
            balance=_wallet(conn,account)
            if balance+earned>8_000_000_000_000_000_000:raise ValueError('Przekroczono limit bezpieczeństwa salda.')
            conn.execute('UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?',(balance+earned,account))
            # Guarantee modest resources, but only for a completed challenge.
            material=MATERIALS[b['enemy']]
            count=1+(1 if b['enemy'] in ('lewiatan','smok') else 0)
            conn.execute('INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?) '
                         'ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity',
                         (account,material,count))
            conn.execute('INSERT INTO ocean4_records_v1350(account_id,enemy,victories) VALUES(?,?,1) '
                         'ON CONFLICT(account_id,enemy) DO UPDATE SET victories=victories+1',(account,b['enemy']))
        elif not surviving:
            outcome='porazka'
        conn.execute('UPDATE ocean4_battles_v1350 SET enemy_hp=?,turn=?,active=?,resolved_at=?,last_outcome=?,reward=? WHERE account_id=?',
                     (new_hp,turn,int(outcome=='trwa'),0 if outcome=='trwa' else now,'' if outcome=='trwa' else outcome,earned,account))
        return {'outcome':outcome,'damage':damage,'enemy_damage':counter if new_hp>0 else 0,'enemy_hp':new_hp,
                'enemy_max_hp':int(b['enemy_max_hp']),'turn':turn,'losses':losses,'reward':earned,
                'material':MATERIALS[b['enemy']] if outcome=='zwyciestwo' else None,
                'hazard':hazard, 'balance':_wallet(conn,account) if outcome=='zwyciestwo' else None}



def retreat(conn, account, *, now=None):
    # Withdrawal yields no loot and preserves existing hull damage.
    now=int(time.time()) if now is None else int(now)
    with atomic(conn):
        row=_active_battle(conn,account)
        if not row or not row['active']:raise ValueError('Nie ma aktywnej bitwy.')
        conn.execute("UPDATE ocean4_battles_v1350 SET active=0,resolved_at=?,last_outcome='odwrot',reward=0 WHERE account_id=?",
                     (now,account))


def records(conn,account):
    return [(r['enemy'],r['victories']) for r in conn.execute('SELECT enemy,victories FROM ocean4_records_v1350 WHERE account_id=? ORDER BY victories DESC',(account,))]
