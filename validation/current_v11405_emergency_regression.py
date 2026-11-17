# -*- coding: utf-8 -*-
"""v114.00.5: safely restore boss combat, character deletion and menu look.

Disposable databases only; the production database is not opened or mutated.
"""
from __future__ import annotations
import asyncio
import ast
import importlib
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace


def run():
    checks=0
    from systems import published_34_integration as published
    saved={k:dict(v) for k,v in published.ACTIVE.items()}
    try:
        mob=SimpleNamespace(hp=500)
        meta={'uoss_unique_superboss_key':'emergency_test_boss'}
        assert published.boss_pressure(mob,meta)==1.0
        assert not hasattr(mob,'_olc34_attacks')
        checks+=2
        published.ACTIVE['uoss']['emergency_test_boss']={'every':2,'stack_percent':120,'max_stacks':2}
        result=[published.boss_pressure(mob,meta) for _ in range(6)]
        assert result==[1.0,1.2,1.2,1.44,1.44,1.44],result
        assert mob._olc34_attacks==6
        checks+=2
    finally:
        for k,v in saved.items():
            published.ACTIVE[k].clear();published.ACTIVE[k].update(v)
    from systems import published_32_finale as published32
    previous=dict(published32.ACTIVE['uoss'])
    try:
        enemy=SimpleNamespace(hp=40,max_hp=100)
        assert published32.uoss_phase_multiplier(enemy,meta)==1.0
        assert not hasattr(enemy,'_olc32_attack_turn')
        checks+=2
        published32.ACTIVE['uoss']['emergency_test_boss']={'phases':[
            {'below_hp':50,'interval':2,'damage_percent':180},
            {'below_hp':20,'interval':2,'damage_percent':200}]}
        assert published32.uoss_phase_multiplier(enemy,meta)==1.0
        assert published32.uoss_phase_multiplier(enemy,meta)==1.8
        checks+=2
    finally:
        published32.ACTIVE['uoss'].clear()
        published32.ACTIVE['uoss'].update(previous)
    # Preflight every static gameplay import from published-32..35, including
    # __import__(..., fromlist=[...]); missing functions must fail before TCP.
    module_names=tuple(f'systems.published_{n}_{suffix}' for n,suffix in (
        (32,'finale'),(33,'mechanics'),(34,'integration'),(35,'finale')))
    modules={name:importlib.import_module(name) for name in module_names}
    root=Path(__file__).resolve().parents[1]
    count=0
    for folder in ('player','world','systems'):
        for source in (root/folder).rglob('*.py'):
            tree=ast.parse(source.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.module in modules:
                    for imported in node.names:
                        if imported.name!='*':
                            assert hasattr(modules[node.module],imported.name),(
                                source,node.module,imported.name)
                            count+=1
                if (isinstance(node,ast.Call) and isinstance(node.func,ast.Name)
                    and node.func.id=='__import__' and node.args
                    and isinstance(node.args[0],ast.Constant)
                    and node.args[0].value in modules):
                    for keyword in node.keywords:
                        if keyword.arg=='fromlist' and isinstance(keyword.value,(ast.Tuple,ast.List)):
                            for entry in keyword.value.elts:
                                if isinstance(entry,ast.Constant):
                                    assert hasattr(modules[node.args[0].value],entry.value),(
                                        source,node.args[0].value,entry.value)
                                    count+=1
    assert count>=50,count
    checks+=1
    from player.session_mixins.perception_maps import SessionPerceptionMapsMixin
    # Execute the exact Session.look wrapper AST without importing the entire
    # server bootstrap (its static catalog requires runtime initialization).
    root=Path(__file__).resolve().parents[1]
    tree=ast.parse((root/'player/session.py').read_text(encoding='utf-8'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Session')
    method=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='look')
    ns={'SessionPerceptionMapsMixin':SessionPerceptionMapsMixin}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),
                 '<v11405-real-Session-look>', 'exec'),ns)
    class FakeSession:
        character=None
        def __init__(self):self.messages=[]
        async def send(self,message,**kwargs):self.messages.append(str(message))
    test=FakeSession()
    asyncio.run(ns['look'](test,''))
    assert test.messages==['Najpierw wybierz postać w menu.']
    checks+=1
    from core.classes_skills import RACES,CLASSES
    from storage.database import Database
    from systems.v10700_equipment_write_barrier import install_on_migrated_connection,approved_instance_operation
    from data.items import ITEMS
    item=next(i for i,v in ITEMS.items() if isinstance(v,dict) and v.get('type')=='armor')
    with tempfile.TemporaryDirectory(prefix='soulbound_v11405_') as tmp:
        db=Database(str(Path(tmp)/'safe.sqlite'))
        catalog=dict(ITEMS)
        from systems.current_install_ledger import initialize_empty_ledger
        initialize_empty_ledger(db.conn)
        def make(name,owner=None):
            if owner is None:owner=db.create_account(name,'valid-password-long')
            forms={k:name for k in ('nom','gen','dat','acc','ins','loc','voc')}
            cid,slot=db.create_character_for_master(owner,name,RACES[0],CLASSES[0],forms)
            return owner,cid,slot
        owner,main,_=make('SafetestMain')
        _,alt,_=make('SafetestAlt',owner)
        other,foreign,_=make('SafetestForeign')
        assert main==owner and alt!=owner and foreign==other
        checks+=1
        def physical(cid):
            db.conn.execute('INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,1)',(cid,item))
            uid=f'v11405_safe_{cid}'
            db.conn.execute('INSERT INTO v106_item_instances(instance_id,account_id,item_id,evolution_stage,origin) VALUES(?,?,?,0,?)',
                            (uid,cid,item,'v11405_test'))
            db.conn.execute('INSERT INTO equipment(account_id,slot,item_id) VALUES(?,?,?)',(cid,'body',item))
            db.conn.execute('INSERT INTO v106_equipped_instances(account_id,slot,instance_id) VALUES(?,?,?)',
                            (cid,'body',uid))
            return uid
        ids={cid:physical(cid) for cid in (main,alt,foreign)}
        db.conn.commit()
        db._v106_shadow_slots_disposable_copy=True
        db._v106_shadow_item_catalog=catalog
        assert install_on_migrated_connection(db,catalog,approved_test_copy=True)>0
        checks+=1
        try:
            db.conn.execute('DELETE FROM inventory WHERE account_id=?',(alt,))
            raise AssertionError('raw SQL bypassed protective trigger')
        except sqlite3.IntegrityError:
            checks+=1
        # An aborted later deletion must restore the ledger as well as row data.
        db.conn.execute(f'''CREATE TEMP TRIGGER v11405_test_block
            BEFORE DELETE ON main.characters WHEN OLD.account_id={alt}
            BEGIN SELECT RAISE(ABORT,'v11405 test forced rollback'); END''')
        try:
            db.delete_character_for_master(owner,alt)
            raise AssertionError('expected rollback')
        except sqlite3.IntegrityError:
            checks+=1  # Explicitly verified the full rollback path.
        assert db.conn.execute('SELECT 1 FROM v106_item_instances WHERE instance_id=?',(ids[alt],)).fetchone()
        assert db.conn.execute('SELECT 1 FROM equipment WHERE account_id=?',(alt,)).fetchone()
        assert db.conn.execute('SELECT 1 FROM account_characters WHERE character_account_id=?',(alt,)).fetchone()
        assert getattr(db.conn,'_v107_eq_write_depth',0)==0
        checks+=4
        db.conn.execute('DROP TRIGGER v11405_test_block')
        deleted=db.delete_character_for_master(owner,alt)
        assert deleted and deleted['name']=='SafetestAlt'
        assert db.conn.execute('SELECT 1 FROM v106_item_instances WHERE account_id=?',(alt,)).fetchone() is None
        assert db.conn.execute('SELECT 1 FROM accounts WHERE id=?',(alt,)).fetchone() is None
        assert db.conn.execute('SELECT 1 FROM accounts WHERE id=?',(owner,)).fetchone() is not None
        assert db.conn.execute('SELECT 1 FROM inventory WHERE account_id=?',(foreign,)).fetchone()
        checks+=5
        removed=db.delete_character_for_master(owner,main)
        assert removed and removed['name']=='SafetestMain'
        assert db.conn.execute('SELECT 1 FROM v106_item_instances WHERE account_id=?',(main,)).fetchone() is None
        assert db.conn.execute('SELECT 1 FROM accounts WHERE id=?',(owner,)).fetchone() is not None
        assert db.conn.execute('SELECT 1 FROM inventory WHERE account_id=?',(foreign,)).fetchone()
        assert db.conn.execute('PRAGMA foreign_key_check').fetchone() is None
        assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        checks+=6
        # Wipe also uses the checked physical route, preserving login identity.
        assert db.wipe_characters_for_master(other)==1
        assert db.conn.execute('SELECT 1 FROM v106_item_instances WHERE account_id=?',(foreign,)).fetchone() is None
        assert db.conn.execute('SELECT 1 FROM accounts WHERE id=?',(other,)).fetchone() is not None
        assert db.conn.execute('PRAGMA foreign_key_check').fetchone() is None
        assert getattr(db.conn,'_v107_eq_write_depth',0)==0
        checks+=5
        db.conn.close()
    print(f'V11405 EMERGENCY: {checks}/{checks} PASS')
    return checks

if __name__=='__main__':run()
