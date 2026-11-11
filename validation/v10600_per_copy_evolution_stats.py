# -*- coding: utf-8 -*-
"""v106 read-only stat/defense test using real equipment mixin and real SQLite slots."""
import os
import sys
import sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy, _check_account
from systems.equipment_evolution_v10500 import stage_stat_bonus, stage_defense_bonus
from systems.equipment_evolution_stats_v10600 import equipped_evolution_stage, evolve_equipped_copy_on_disposable_test
import ast
from systems.equipment_evolution_stats_v10600 import equipped_evolution_stage, evolve_equipped_copy_on_disposable_test
from systems.equipment_evolution_v10500 import stage_stat_bonus, stage_defense_bonus
# Execute exactly the TWO source methods from the actual session mixin.
# A narrow AST extraction avoids importing the entire heavy world in this test.
source=(ROOT/'player/session_mixins/equipment_stats.py').read_text(encoding='utf-8')
tree=ast.parse(source)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)
         and n.name=='SessionEquipmentStatsMixin')
selected=[n for n in cls.body if isinstance(n,ast.FunctionDef)
          and n.name in {'equipment_bonus_totals','defense'}]
assert len(selected)==2
holder=ast.ClassDef(name='SourceEquipmentStats',bases=[],keywords=[],body=selected,decorator_list=[])
mod=ast.fix_missing_locations(ast.Module(body=[holder],type_ignores=[]))
namespace={
 'ITEMS':{},'shield_multiplier':lambda s:1.0,
 'crossover_bonus_v3001':lambda item:({},{}),
 'v03042_upgrade_primary_stat':lambda item,affix:'constitution',
 'v03042_upgrade_stat_bonus':lambda lvl:0,
 'v03042_upgrade_defense_bonus':lambda item,lvl:0,
 'moogle_board_stat_bonus_v0313':lambda lvl:0,
 'TECH_SET_ITEMS_V03114':{},
 'physical_defense_base':lambda lvl,con:200,
}
exec(compile(mod,str(ROOT/'player/session_mixins/equipment_stats.py'),'exec'),namespace)
SourceEquipmentStats=namespace['SourceEquipmentStats']

CAT={'sb106_test_guard':{'type':'armor','defense':160,'affix_amount':80,
                         'stats':{'strength':7,'constitution':3}}}

class DB:
    def __init__(self, conn):
        self.conn=conn
        self._v106_shadow_item_catalog=CAT
        self._v106_shadow_slots_disposable_copy=True
    def equipment(self, aid):
        return self.conn.execute('SELECT slot,item_id FROM equipment WHERE account_id=? ORDER BY slot',(aid,)).fetchall()
    def equipment_reforge(self,*a):return None
    def equipment_runes_v0925(self,*a):return ()
    def equipment_upgrade_level_v03042(self,*a):return 0
    def equipment_enchants_v03053(self,*a):return ()

class Character:
    character_level=100
    def class_defense_multiplier(self):return 1.0
    def racial_defense_multiplier(self):return 1.0

class Player(SourceEquipmentStats):
    account_id=1
    character=Character()
    def __init__(self, db):self.server=type('Server',(),{'db':db})()
    def equipped_item_rows(self):return self.server.db.equipment(self.account_id)
    def active_soul_weapon_relic_v11176(self):return (None,None)
    def class_set_stat_bonus_totals(self):return {}
    def effective_constitution(self):return 10
    def equipment_total_socket_capacity_v03114(self,*a):return 0
    def equipment_flat_power_totals_v11187(self):return {'magic_defense':0,'attack':0,'magic_attack':0,'weapon_power':0}
    def total_set_defense_multiplier(self):return 1.0
    def equipment_property_totals(self):return {'physical_defense_pct':0}


def run():
    checks=0
    def ok(cond,msg):
        nonlocal checks
        if not cond:raise AssertionError(msg)
        checks+=1
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    namespace["ITEMS"]=CAT
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    try:
        conn.executescript('''
        CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,PRIMARY KEY(account_id,item_id));
        CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,PRIMARY KEY(account_id,slot));
        CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,PRIMARY KEY(account_id,record_key));
        INSERT INTO inventory VALUES(1,'sb106_test_guard',2),(2,'sb106_test_guard',1);
        INSERT INTO equipment VALUES(1,'body','sb106_test_guard'),(1,'secondary','sb106_test_guard');
        CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,quantity INTEGER,
         PRIMARY KEY(account_id,container,item_id));
        ''')
        db=DB(conn)
        prepare_on_disposable_copy(conn,CAT,confirm_disposable_copy=True)
        _check_account(conn,1,CAT);ok(True,'initial physical slots')
        player=Player(db)
        both=list(conn.execute('SELECT s.slot,s.instance_id FROM v106_equipped_instances s WHERE account_id=1 ORDER BY slot'))
        ok(len(both)==2 and both[0]['instance_id']!=both[1]['instance_id'],'two unique worn copies')
        zero_stats=player.equipment_bonus_totals();zero_def=player.defense()
        ok(zero_stats['constitution']==6,'zero stages do not add constitution')
        ok(zero_stats['strength']==14,'authored stats remain per piece')
        from systems.equipment_evolution_v10500 import required_materials
        target_materials=required_materials(1)
        for material,amount in target_materials.items():
            conn.execute('INSERT INTO profession_storage VALUES(?,?,?,?)',
                         (1,'craftbox',material,amount*3))
        # Mutate only one exact physical copy; material cost and stage are atomic.
        try:evolve_equipped_copy_on_disposable_test(db,1,both[0]['slot'],both[0]['instance_id'])
        except PermissionError:ok(True,'copy confirmation required')
        else:raise AssertionError('unconfirmed per-copy upgrade')
        done,stage=evolve_equipped_copy_on_disposable_test(
            db,1,both[0]['slot'],both[0]['instance_id'],confirm_disposable_copy=True)
        ok(done and stage==1,'paid exact-copy evolution stage 1')
        ok(equipped_evolution_stage(db,1,both[1]['slot'],'sb106_test_guard')==0,
           'other identical copy untouched')
        for material,amount in target_materials.items():
            qty=conn.execute('SELECT quantity FROM profession_storage WHERE '
                             'account_id=1 AND item_id=?',(material,)).fetchone()[0]
            ok(qty==amount*2,'evolution consumes exact material quantity')
        try:evolve_equipped_copy_on_disposable_test(
            db,2,both[0]['slot'],both[0]['instance_id'],confirm_disposable_copy=True)
        except RuntimeError:ok(True,'foreign copy upgrade blocked')
        else:raise AssertionError('foreign instance upgraded')
        # Test forced SQL error after material removal: both writes revert.
        for material,amount in required_materials(2).items():
            conn.execute('INSERT INTO profession_storage VALUES(?,?,?,?)',
                         (1,'craftbox',material,amount*2))
        conn.execute('CREATE TRIGGER block_sb106_evo BEFORE UPDATE ON v106_item_instances '
                     "WHEN NEW.evolution_stage=2 BEGIN SELECT RAISE(ABORT,'stop-evo'); END")
        before={m:conn.execute('SELECT quantity FROM profession_storage WHERE account_id=1 AND item_id=?',
                               (m,)).fetchone()[0] for m in set(target_materials)|set(required_materials(2))}
        try:evolve_equipped_copy_on_disposable_test(
            db,1,both[0]['slot'],both[0]['instance_id'],confirm_disposable_copy=True)
        except sqlite3.IntegrityError:ok(True,'injected SQL evolution error')
        else:raise AssertionError('SQL failure ignored')
        ok(equipped_evolution_stage(db,1,both[0]['slot'],'sb106_test_guard')==1,
           'SQL failure restores original stage')
        ok(all(conn.execute('SELECT quantity FROM profession_storage WHERE account_id=1 AND item_id=?',
                            (m,)).fetchone()[0]==qty for m,qty in before.items()),
           'SQL failure restores all materials')
        conn.execute('DROP TRIGGER block_sb106_evo')
        # An unowned transaction with commit=False must NOT be committed by
        # the staged upgrade: caller still controls it.
        conn.commit()
        done,stage=evolve_equipped_copy_on_disposable_test(
            db,1,both[0]['slot'],both[0]['instance_id'],
            confirm_disposable_copy=True,commit=False)
        ok(done and stage==2,'commit=False performed one physical upgrade')
        ok(conn.in_transaction,'commit=False kept transaction open')
        conn.rollback()
        ok(equipped_evolution_stage(db,1,both[0]['slot'],'sb106_test_guard')==1,
           'explicit rollback after commit=False restored stage')
        ok(all(conn.execute('SELECT quantity FROM profession_storage WHERE account_id=1 AND item_id=?',
                            (m,)).fetchone()[0]==qty for m,qty in before.items()),
           'explicit rollback after commit=False restored materials')
        # A caller-owned transaction can roll back both cost and upgrade.
        conn.execute('SAVEPOINT outside_upgrade_v106')
        done,stage=evolve_equipped_copy_on_disposable_test(
            db,1,both[0]['slot'],both[0]['instance_id'],confirm_disposable_copy=True)
        ok(done and stage==2,'upgrade inside external transaction')
        conn.execute('ROLLBACK TO SAVEPOINT outside_upgrade_v106')
        conn.execute('RELEASE SAVEPOINT outside_upgrade_v106')
        ok(equipped_evolution_stage(db,1,both[0]['slot'],'sb106_test_guard')==1,
           'outer rollback restores physical stage')
        ok(all(conn.execute('SELECT quantity FROM profession_storage WHERE account_id=1 AND item_id=?',
                            (m,)).fetchone()[0]==qty for m,qty in before.items()),
           'outer rollback restores materials')
        conn.execute('UPDATE v106_item_instances SET evolution_stage=5 WHERE instance_id=?',(both[0]['instance_id'],))
        conn.execute('UPDATE v106_item_instances SET evolution_stage=2 WHERE instance_id=?',(both[1]['instance_id'],))
        ok(equipped_evolution_stage(db,1,both[0]['slot'],'sb106_test_guard')==5,'first instance stage')
        ok(equipped_evolution_stage(db,1,both[1]['slot'],'sb106_test_guard')==2,'second instance stage')
        expected_stat=stage_stat_bonus(5,CAT['sb106_test_guard'])+stage_stat_bonus(2,CAT['sb106_test_guard'])
        expected_def=stage_defense_bonus(5,CAT['sb106_test_guard'])+stage_defense_bonus(2,CAT['sb106_test_guard'])
        ok(player.equipment_bonus_totals()['constitution']==6+expected_stat,'actual equipment_bonus_totals per physical copy')
        ok(player.defense()==zero_def+expected_def,'actual defense per physical copy')
        ok(player.equipment_bonus_totals()['strength']==14,'no duplicated authored strength')
        # Legacy template stage must NOT be applied twice or to wrong copy in staging.
        conn.execute("INSERT INTO player_records_v03051 VALUES(1,'eq_evolution_v10500:sb106_test_guard',9)")
        ok(player.equipment_bonus_totals()['constitution']==6+expected_stat,'legacy stage ignored in staging')
        db._v106_shadow_slots_disposable_copy=False
        ok(equipped_evolution_stage(db,1,both[0]['slot'],'sb106_test_guard')==9,'v105 path remains unchanged without marker')
        ok(player.equipment_bonus_totals()['constitution']==6+2*stage_stat_bonus(9,CAT['sb106_test_guard']),
           'legacy equipment_bonus_totals unchanged')
        db._v106_shadow_slots_disposable_copy=True
        os.environ.pop('SOULBOUND_V106_STAGING')
        try:player.equipment_bonus_totals()
        except PermissionError:ok(True,'staging flag required')
        else:raise AssertionError('missing staging guard')
        os.environ['SOULBOUND_V106_STAGING']='1'
        try:equipped_evolution_stage(db,2,both[0]['slot'],'sb106_test_guard')
        except RuntimeError:ok(True,'cannot read foreign slot')
        else:raise AssertionError('cross-owner physical read')
        try:equipped_evolution_stage(db,1,both[0]['slot'],'missing_item')
        except sqlite3.OperationalError:
            # Missing catalog members follow legacy, which would have no stage row.
            raise
        else:ok(True,'non-equipment legacy fallback')
        try:
            conn.execute('UPDATE v106_item_instances SET evolution_stage=11 WHERE instance_id=?',
                         (both[0]['instance_id'],))
        except sqlite3.IntegrityError:ok(True,'SQLite blocks invalid evolution stage')
        else:raise AssertionError('out-of-range physical stage accepted')
        ok(player.defense()==zero_def+expected_def,'invalid SQL attempt did not change defense')
        conn.execute("UPDATE equipment SET item_id='wrong' WHERE account_id=1 AND slot='body'")
        try:player.equipment_bonus_totals()
        except RuntimeError:ok(True,'untracked legacy slot mutation is rejected')
        else:raise AssertionError('untracked slot accepted')
        conn.execute("UPDATE equipment SET item_id='sb106_test_guard' WHERE account_id=1 AND slot='body'")
        # The actual Haldor command must be fail-closed in staging: otherwise
        # it would charge materials for a legacy per-template stage that no
        # longer contributes to bonuses of the physical instance.
        import asyncio
        forge_source=(ROOT/'player/session_mixins/forge_guilds.py').read_text(encoding='utf-8')
        forge_cls=next(n for n in ast.parse(forge_source).body
                       if isinstance(n,ast.ClassDef) and n.name=='SessionForgeGuildsMixin')
        forge_method=next(n for n in forge_cls.body if isinstance(n,ast.AsyncFunctionDef)
                          and n.name=='evolve_equipment_v10500')
        forge_def=ast.fix_missing_locations(ast.Module(body=[forge_method],type_ignores=[]))
        forge_ns={}
        exec(compile(forge_def,str(ROOT/'player/session_mixins/forge_guilds.py'),'exec'),forge_ns)
        class Forge:
            server=type('S',(),{'db':db})()
            def __init__(self):self.messages=[]
            async def send(self,text):self.messages.append(str(text))
        f=Forge()
        before_stage=equipped_evolution_stage(db,1,both[0]['slot'],'sb106_test_guard')
        asyncio.run(forge_ns['evolve_equipment_v10500'](f,'sb106_test_guard'))
        ok(len(f.messages)==1 and 'wstrzymana' in f.messages[0],
           'legacy forge command fail-closed in per-copy staging')
        ok(equipped_evolution_stage(db,1,both[0]['slot'],'sb106_test_guard')==before_stage,
           'forge legacy command did not change stage')
        asyncio.run(forge_ns['evolve_equipment_v10500'](f,'wyzeruj sb106_test_guard POTWIERDZAM'))
        ok(len(f.messages)==2 and 'wstrzymana' in f.messages[1],
           'legacy destructive reset also blocked')
        ok(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integral')
        return checks
    finally:
        conn.close()
        if previous is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=previous

if __name__=='__main__':print('V106 PER-COPY EVO BONUSES:',run(),'PASS')
