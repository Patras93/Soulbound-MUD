# -*- coding: utf-8 -*-
"""v106: interrupted post-commit rewards must not be blindly replayed.

Real perform_recipe + SQLite. Manual review required for uncertain grants.
No production database or game server; this is NOT an atomic XP/quest claim.
"""
import asyncio
import os
import sqlite3
from contextlib import ExitStack
from unittest.mock import patch

from validation.v10600_full_recipe_atomic_flow import make_db,CraftSession
from player.session_mixins import crafting as c
from systems.equipment_craft_reward_journal_v10600 import (
    pending,assert_ready,checkpoint,audit_pending,STAGES,
)


def run():
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    checks=0
    def ck(expr,msg):
        nonlocal checks
        if not expr:raise AssertionError(msg)
        checks+=1
    recipe={'name':'Hełm testowy','tool_type':'smithing',
            'ingredients':{'ore':1},'output':'helm','quantity':1,
            'stations':['forge'],'tool_xp':100,'profession_xp':100}
    recipes={'helm_test':recipe}
    patches=[
        patch.object(c,'find_by_name',lambda table,q:('helm_test',recipe)),
        patch.object(c,'tool_tier',lambda level:1),
        patch.object(c,'required_tool_tier_for_level',lambda level:1),
        patch.object(c,'tool_tier_bonus_chance',lambda level:0),
        patch.object(c,'craft_inspiration_v11324',lambda *args:None),
        patch.object(c,'crafting_quality_roll_v03054',lambda *args:'good'),
        patch.object(c,'material_grade_v1250',lambda *args:0),
        patch.object(c,'material_quality_upgrade_v1250',lambda q,*args:q),
        patch.object(c,'masterpiece_promote_v12812',lambda q,*args:(q,False)),
        patch.object(c,'crafting_critical_chance_v03054',lambda *args:0),
        patch.object(c,'crafting_quality_output_v03054',lambda iid,*args:(iid+'_quality',None)),
        patch.object(c,'crafting_mastery_category_v03054',lambda *args:'equipment'),
        patch.object(c,'crafting_output_is_quality_equipment_v03054',lambda iid:False),
        patch.object(c,'ITEMS',{'ore':{'name':'Ruda'},'gem':{'name':'Klejnot'},
                 'helm':{'name':'Hełm','type':'armor'},
                 'helm_quality':{'name':'Dobry Hełm','type':'armor'},
                 'hammer':{'name':'Młot'}}),
        patch('systems.endless_crafting_v5500.endless_crafted_equipment_v5500',lambda iid,*a:iid),
        patch('systems.live_olc28_expansion.craft_yield',lambda prof,qty:qty),
        patch('systems.live_olc32_finale.crafting_bonus',lambda rid,room,qty:qty),
        patch('systems.live_olc35_finale.city_craft_bonus',lambda *args:args[-1]),
        patch('systems.live_olc33_mechanics.craft_byproduct',lambda *args:None),
        patch('systems.live_olc34_integration.profession_find',lambda *args:None),
    ]
    try:
        with ExitStack() as stack:
            for p in patches:stack.enter_context(p)
            db,raw=make_db();s=CraftSession(db)
            ck(pending(db,1) is None,'clean account has no pending postcommit grants')
            ck(asyncio.run(s.perform_recipe('helm_test',recipes,'rzemiosło')) is True,
               'success completes real high-level recipe')
            rows=raw.execute('SELECT run_id,account_id,stage,recipe_id,output_id,output_qty '
                             'FROM v106_craft_reward_journal').fetchall()
            ck(len(rows)==1 and rows[0][2]=='complete','one completed durable journal row')
            ck(len(rows[0][0])==32 and rows[0][3]=='helm_test' and rows[0][4]=='helm_quality',
               'full IDs and resulting quality variant recorded')
            ck(pending(db,1) is None,'completed recipe does not block next craft')
            ck(raw.execute("SELECT quantity FROM inventory WHERE account_id=1 AND item_id='helm_quality'").fetchone()[0]==1,
               'physical output exists once after complete journal')
            old_ids={r[0] for r in raw.execute('SELECT instance_id FROM v106_item_instances')}
            # Injection AFTER physical item commit, BEFORE canonical quest progress.
            async def broken_quest(*a,**kw):raise RuntimeError('simulated quest storage error')
            with patch.object(s,'announce_craft_quest_progress',broken_quest):
                try:asyncio.run(s.perform_recipe('helm_test',recipes,'rzemiosło'))
                except RuntimeError as e:ck('simulated' in str(e),'quest failure surfaces')
                else:raise AssertionError('quest fault did not interrupt rewards')
            row=pending(db,1)
            ck(row is not None and row[2]=='collections','crashed side-effect leaves exact checkpoint')
            ck(raw.execute("SELECT quantity FROM inventory WHERE account_id=1 AND item_id='helm_quality'").fetchone()[0]==2,
               'previously committed crafted output not deleted/duplicated')
            ck(raw.execute("SELECT actions FROM crafting_mastery_v03054 WHERE account_id=1").fetchone()[0]==2,
               'craft mastery transaction not repeated after quest failure')
            ids_now={r[0] for r in raw.execute('SELECT instance_id FROM v106_item_instances')}
            ck(len(ids_now)==2 and old_ids.issubset(ids_now),'unique physical IDs conserved')
            result=asyncio.run(s.perform_recipe('helm_test',recipes,'rzemiosło'))
            ck(result is False,'next recipe denied rather than duplicating pending rewards')
            ck('wstrzymano nowe rzemiosło' in s.messages[-1], 'brief NVDA-readable pending warning')
            ck(raw.execute("SELECT quantity FROM inventory WHERE account_id=1 AND item_id='helm_quality'").fetchone()[0]==2,
               'blocked retry does not mint extra output')
            # Reconnect to same SQLite using a separate wrapped DB object.
            from storage.database import _DeferredCommitConnection
            db2=type(db)(_DeferredCommitConnection(raw))
            db2._v106_shadow_slots_disposable_copy=True
            db2._v106_shadow_item_catalog=db._v106_shadow_item_catalog
            ck(audit_pending(db2,1)[0]==row[0],'pending checkpoint survives session recreation')
            ck(pending(db,2) is None,'another account unaffected')
            ck(row[2]=='collections' and len(row[0])==32,'no replay happened')
            for stage in ('output','collections','guild','complete','invalid'):
                try:checkpoint(db,1,row[0],stage)
                except (ValueError,RuntimeError):checks+=1
                else:raise AssertionError('illegal reward checkpoint accepted: '+stage)
            ck(pending(db,1)[2]=='collections','illegal transitions leave stage intact')
            # Simulate DB fault *inside* the atomic output transaction:
            # no new run ID may remain pending when craft fails.
            db3,raw3=make_db();s3=CraftSession(db3)
            raw3.execute('''CREATE TRIGGER reject_helm BEFORE INSERT ON v106_item_instances
                WHEN NEW.item_id='helm_quality'
                BEGIN SELECT RAISE(ABORT,'SQL crafting fault'); END''');raw3.commit()
            ck(asyncio.run(s3.perform_recipe('helm_test',recipes,'rzemiosło')) is False,
               'SQL failure fails whole item transaction')
            ck(pending(db3,1) is None,'item rollback removes journal insert')
            ck(raw3.execute("SELECT COUNT(*) FROM v106_item_instances").fetchone()[0]==0,
               'no physical ID left after SQL fault')
            ck(raw3.execute("SELECT quantity FROM inventory WHERE account_id=1 AND item_id='ore'").fetchone()[0]==3,
               'item failure returns all inventory material')
            ck(raw3.execute('SELECT COUNT(*) FROM v106_craft_reward_journal').fetchone()[0]==0,
               'no false positive pending journal after failed craft')
            # Test rollback by another owner transaction, not just a SQL fault.
            db4,raw4=make_db()
            raw4.execute('SAVEPOINT external_tx')
            ck(db4.craft_item_atomic_v106(1,{'ore':1},'helm',1,reward_journal={
                 'run_id':'a'*32,'recipe_id':'helm_test','base_item_id':'helm'}) is True,
               'item and journal minted in caller-owned transaction')
            ck(pending(db4,1) is not None,'journal visible inside caller transaction')
            raw4.execute('ROLLBACK TO SAVEPOINT external_tx');raw4.execute('RELEASE SAVEPOINT external_tx')
            ck(raw4.execute("SELECT COUNT(*) FROM v106_item_instances").fetchone()[0]==0,
               'caller rollback restores all physical gear')
            # The journal table itself may be rolled back when first created.
            tables={r[0] for r in raw4.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            ck('v106_craft_reward_journal' not in tables or pending(db4,1) is None,
               'caller rollback restores journal or drops its initial schema')
            raw.close();raw3.close();raw4.close()
        return checks
    finally:
        if previous is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=previous

if __name__=='__main__':
    print('V106 CRAFT REWARD JOURNAL:',run(),'PASS',flush=True)
