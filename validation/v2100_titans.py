# -*- coding: utf-8 -*-
"""Focused safety, persistence and lazy generation tests for v2.10.0."""
from __future__ import annotations
import sqlite3
from types import SimpleNamespace


def run_regression():
    from systems.titans_v2100 import (
        TITANS, FAMILIES, challenge_kind, chamber_id, chamber_identity,
        titan_for_floor, titan_round_v2100, titan_attack_multiplier_v2100,
        install_titans_v2100,
    )
    from systems.content_registry import ITEMS
    from storage.db_titans_v2100 import DatabaseTitansV2100Mixin
    checks=0
    def check(value, why):
        nonlocal checks
        checks+=1
        if not value:
            raise AssertionError('v2.10.0: '+why)
    check(len(TITANS)==8 and len({s[0] for s in TITANS})==8,'8 unique Titans')
    check(len(FAMILIES)==8,'dungeon identities present')
    for n in (25,50,75,100,500,1000,5000):
        kind=challenge_kind(n)
        check(kind==('titan' if n%50==0 else 'secret'),'milestone '+str(n))
        for family in FAMILIES:
            rid=chamber_id(kind,family,n)
            check(chamber_identity(rid)==(kind,family,n),'roundtrip '+rid)
    check(challenge_kind(24) is None,'no earlier chambers')
    check(challenge_kind(51) is None,'no arbitrary chambers')
    check(titan_for_floor(450)[0]=='ragnor','repeat cycle')
    check(titan_for_floor(100)[0]=='velira','second titan')
    check(titan_for_floor(51) is None,'bad floor not a titan')

    # Localized registration only: existing exits are preserved.
    rooms={'crypt_floor_50':{'name':'Stara Krypta','desc':'Autorska komnata',
                             'exits':{'west':'crypt_floor_49','down':'crypt_floor_51'}},
           'v1500_echo_25_shrine':{'name':'Echo','desc':'Stara komnata','exits':{'west':'a','east':'b'}}}
    items={}
    class MockWorld:
        def __init__(self): self.generated=[]; self.spawns=[]
        def _generatorize_runtime_room(self,rid): self.generated.append(rid)
        def _register_runtime_spawn(self,rid,mid): self.spawns.append((rid,mid))
        def ensure_infinite_dungeon_floor(self,rid): return rid in rooms
    # Regression: wrapping another lazy generator must keep its validated
    # on-demand-floor capability visible to the full exit audit.
    MockWorld.ensure_infinite_dungeon_floor._v1500_echo = True
    install_titans_v2100(rooms,items,MockWorld)
    check(getattr(MockWorld.ensure_infinite_dungeon_floor, '_v1500_echo', False),
          'Echo generator capability survives Titan wrapper')
    check(len([x for x in items if x.startswith('v2100_relic_')])==8,'eight authored EQ artefacts')
    check('v2100_titan_essence' in items,'essence item installed')
    world=MockWorld()
    check(world.ensure_infinite_dungeon_floor('crypt_floor_50'),'old room still exists')
    check(rooms['crypt_floor_50']['exits']['west']=='crypt_floor_49','old route preserved')
    check(rooms['crypt_floor_50']['exits']['down']=='crypt_floor_51','old stairs preserved')
    check(rooms['crypt_floor_50']['exits']['north']=='v2100_titan_crypt_50','side exit')
    check('v2100_titan_crypt_50' not in rooms,'arena lazy')
    check(world.ensure_infinite_dungeon_floor('v2100_titan_crypt_50'),'arena enters')
    check(rooms['v2100_titan_crypt_50']['exits']['south']=='crypt_floor_50','arena returns')
    check(len(world.spawns)==1,'one real boss registered')
    check(world.ensure_infinite_dungeon_floor('v2100_titan_crypt_50'),'arena remains')
    check(len(world.spawns)==1,'no duplicate spawn')
    check(world.ensure_infinite_dungeon_floor('v1500_echo_25_shrine'),'old shrine exists')
    check(rooms['v1500_echo_25_shrine']['exits']['north']=='v2100_secret_echo_25','secret entrance')
    check(world.ensure_infinite_dungeon_floor('v2100_secret_echo_25'),'secret enters')
    check(rooms['v2100_secret_echo_25']['exits']['south']=='v1500_echo_25_shrine','secret returns')
    check(len(world.spawns)==1,'secret does not spawn a boss')

    # Exact turn telegraph, guard consumes on special only, phases preserved.
    mob=SimpleNamespace(key='test',combat_turn=1,hp=100000,adaptive_max_hp_v11330=100000)
    template={'v2100_titan':'ragnor','max_hp':100000}
    check('Faza I' in titan_round_v2100(mob,template),'first phase spoken')
    mob.combat_turn=2; titan_round_v2100(mob,template)
    mob.combat_turn=3
    check('przygotowuje' in titan_round_v2100(mob,template),'warning')
    check(titan_attack_multiplier_v2100(mob,template,SimpleNamespace(v2100_guard_mob='test'))==1.0,'not spent on warning')
    mob.combat_turn=4
    check('uwalnia' in titan_round_v2100(mob,template),'release')
    target=SimpleNamespace(v2100_guard_mob='test')
    check(titan_attack_multiplier_v2100(mob,template,target)==0.65,'guard mitigates attack')
    check(target.v2100_guard_mob=='','guard consumed')
    check(titan_attack_multiplier_v2100(mob,template,target)>1.0,'unguarded burst harder')
    mob.combat_turn=5;mob.hp=35000
    check('faza 3' in titan_round_v2100(mob,template).casefold(),'phase transition')
    check(titan_attack_multiplier_v2100(mob,{},target)==1.0,'non-Titan unchanged')

    # Full SQLite transaction bookkeeping. Independently owned rewards,
    # no character reset and no bonus before 24h.
    class TinyDB(DatabaseTitansV2100Mixin):
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
            self.conn.row_factory=sqlite3.Row
            self.conn.executescript('''CREATE TABLE accounts(id INTEGER PRIMARY KEY);
                INSERT INTO accounts VALUES(1),(2);
                CREATE TABLE inventory(account_id INT,item_id TEXT,quantity INT,
                  PRIMARY KEY(account_id,item_id));''')
            self.create_titans_schema_v2100()
        def add_item(self,aid,iid,qty=1,commit=True):
            self.conn.execute('INSERT INTO inventory VALUES(?,?,?) '
              'ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity',
              (int(aid),str(iid),int(qty)))
            if commit: self.conn.commit()
    db=TinyDB()
    # Item catalog comes from the actual installed runtime; temporary testing
    # of the DB uses the real catalogue only for the first relic existence guard.
    saved={i:ITEMS.get(i) for i in items}
    ITEMS.update(items)
    try:
        r=db.record_titan_defeat_v2100(1,'ragnor','crypt',50,now=1_000_000)
        check(r['first_titan'] and r['first_floor'] and r['essence']==4,'first trophy')
        r=db.record_titan_defeat_v2100(1,'ragnor','crypt',50,now=1_000_001)
        check(not r['first_titan'] and not r['first_floor'] and not r['essence'],'anti-repeat')
        r=db.record_titan_defeat_v2100(1,'ragnor','deep',450,now=1_000_002)
        check(r['first_floor'] and not r['first_titan'] and not r['essence'],'floor clear but global cooldown')
        r=db.record_titan_defeat_v2100(1,'ragnor','deep',450,now=1_000_000+86400)
        check(r['essence']==6 and not r['first_floor'],'bonus after 24h')
        r=db.record_titan_defeat_v2100(2,'ragnor','crypt',50,now=1_000_003)
        check(r['first_titan'] and r['essence']==4,'separate player')
        check(db.claim_titan_secret_v2100(1,'crypt',25),'first secret')
        check(not db.claim_titan_secret_v2100(1,'crypt',25),'secret not farmable')
        check(db.claim_titan_secret_v2100(2,'crypt',25),'other player own secret')
        check(db.titan_secret_known_v2100(1,'crypt',25),'secret persisted')
        rows=db.conn.execute('SELECT quantity FROM inventory '
            'WHERE account_id=1 AND item_id=?',('v2100_relic_ragnor',)).fetchone()
        check(int(rows[0])==1,'relic awarded exactly once')
        rows=db.conn.execute('SELECT quantity FROM inventory '
            'WHERE account_id=1 AND item_id=?',('v2100_titan_essence',)).fetchone()
        check(int(rows[0])==11,'essence count 4+6+1')
        check(len(db.titan_records_v2100(1))==1,'one persistent Titan record')
    finally:
        for item, previous in saved.items():
            if previous is None: ITEMS.pop(item,None)
            else: ITEMS[item]=previous
        db.conn.close()
    return checks

if __name__=='__main__':
    print('TYTANI v2.10.0:',run_regression(),'checks PASS')
