# -*- coding: utf-8 -*-
"""Staged v106: OLC33/34 material rewards are part of the main SQL craft."""
import asyncio
import os
import sqlite3
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v10600_full_recipe_atomic_flow import make_db,CraftSession
from systems.equipment_crafting_rewards_v10600 import preview_resources
from systems.live_olc33_mechanics import ACTIVE as OLC33
from systems.live_olc34_integration import ACTIVE as OLC34
from player.session_mixins import crafting as c


def run():
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    n=0
    def ck(value,message):
        nonlocal n
        if not value: raise AssertionError(message)
        n+=1
    try:
        db,raw=make_db()
        session=CraftSession(db)
        recipe={'name':'Hełm testowy','ingredients':{'ore':2},'output':'helm',
                'quantity':1,'stations':['forge'],'tool_xp':50,'profession_xp':50}
        recipes={'bonus_helm_test':recipe}
        from player.session_mixins import crafting as c
        patches=[
            patch.object(c,'find_by_name',lambda *args:('bonus_helm_test',recipe)),
            patch.object(c,'tool_tier',lambda level:1),
            patch.object(c,'required_tool_tier_for_level',lambda level:1),
            patch.object(c,'tool_tier_bonus_chance',lambda level:0),
            patch.object(c,'craft_inspiration_v11324',lambda *args:None),
            patch.object(c,'crafting_quality_roll_v03054',lambda *args:'good'),
            patch.object(c,'material_grade_v1250',lambda *args:0),
            patch.object(c,'material_quality_upgrade_v1250',lambda q,*args:q),
            patch.object(c,'masterpiece_promote_v12812',lambda q,*args:(q,False)),
            patch.object(c,'crafting_critical_chance_v03054',lambda *args:0),
            patch.object(c,'crafting_quality_output_v03054',lambda iid,*args:(iid,None)),
            patch.object(c,'crafting_mastery_category_v03054',lambda *args:'eq'),
            patch.object(c,'crafting_output_is_quality_equipment_v03054',lambda iid:False),
            patch.object(c,'ITEMS', {'ore':{'name':'Ruda','type':'material'},
                                   'gem':{'name':'Klejnot','type':'material'},
                                   'helm':{'name':'Hełm','type':'armor'},
                                   'hammer':{'name':'Młot'}}),
            patch('systems.endless_crafting_v5500.endless_crafted_equipment_v5500',lambda iid,*a:iid),
            patch('systems.live_olc28_expansion.craft_yield',lambda prof,qty:qty),
            patch('systems.live_olc32_finale.crafting_bonus',lambda *args:args[-1]),
            patch('systems.live_olc35_finale.city_craft_bonus',lambda *args:args[-1]),
            patch.dict(OLC33['professions'],{
                'bonus_helm_test':{'byproduct':'gem','amount':2,'every':2}},clear=False),
            patch.dict(OLC34['professions'],{
                'bonus_helm_test':{'material':'gem','amount':3,'every':2}},clear=False),
        ]
        def gem(): return db.item_qty(1,'gem')
        def helm(): return db.item_qty(1,'helm')
        def ore(): return db.item_qty(1,'ore')+db.storage_qty(1,'craftbox','ore')
        def snapshot():
            return tuple((table,tuple(tuple(row) for row in raw.execute('SELECT * FROM '+table+' ORDER BY 1,2')))
                         for table in ('inventory','profession_storage','v106_item_instances'))
        with ExitStack() as stack:
            for p in patches:stack.enter_context(p)
            ck(preview_resources(session,'bonus_helm_test')[0]==(),
               'first successful craft has no bonuses')
            ck(not hasattr(session,'_olc33_craft_counts'),'preview did not mutate real counter')
            ck(asyncio.run(session.perform_recipe('bonus_helm_test',recipes,'rzemiosło')) is True,
               'first high-level craft succeeds')
            ck(session._olc33_craft_counts['bonus_helm_test']==1 and
               session._olc34_craft_counts['bonus_helm_test']==1,'successful craft advances both counters once')
            ck(preview_resources(session,'bonus_helm_test')[0]==(('gem',2),('gem',3)),
               'second craft plans both byproducts ahead of mutation')
            before=snapshot();g=gem();h=helm();o=ore();awards=len(session.awards)
            raw.execute('''CREATE TRIGGER fail_bonus BEFORE UPDATE ON inventory
                WHEN NEW.item_id='gem' AND NEW.quantity>OLD.quantity
                BEGIN SELECT RAISE(ABORT,'test byproduct failed'); END''');raw.commit()
            ck(asyncio.run(session.perform_recipe('bonus_helm_test',recipes,'rzemiosło')) is False,
               'byproduct failure denies entire craft')
            ck(snapshot()==before and gem()==g and helm()==h and ore()==o,
               'byproduct failure restores output and ingredients')
            ck(session._olc33_craft_counts['bonus_helm_test']==1 and
               session._olc34_craft_counts['bonus_helm_test']==1,
               'failed byproduct does not advance reward rhythm')
            ck(len(session.awards)==awards,'failed byproduct cannot grant XP/quest')
            raw.execute('DROP TRIGGER fail_bonus');raw.commit()
            ck(asyncio.run(session.perform_recipe('bonus_helm_test',recipes,'rzemiosło')) is True,
               'next attempted craft can succeed')
            ck(gem()==g+5 and helm()==h+1 and ore()==o-2,
               'both bonus materials and main physical equipment committed together')
            ck(session._olc33_craft_counts['bonus_helm_test']==2 and
               session._olc34_craft_counts['bonus_helm_test']==2,
               'successful bonus craft advances rhythm exactly once')
            ck(session.awards.count('collection')==4,
               'collection hooks fire for one base and two bonus materials on success')
            ck(raw.execute("SELECT COUNT(*) FROM v106_item_instances WHERE item_id='helm'").fetchone()[0]==2,
               'physical identifiers match two successful crafts')
            # Reject malformed extra rewards before any SQL side effects.
            before=snapshot()
            for extra in ((('',2),), (('gem',-3),), (('missing',1),)):
                try: db.craft_item_atomic_v106(1,{'ore':1},'helm',1,extra_outputs=extra)
                except (ValueError,OverflowError): n+=1
                else:raise AssertionError('invalid bonus was accepted')
            ck(snapshot()==before,'invalid bonuses never consume materials')
            # A caller may own a larger transaction; its rollback must restore
            # the main EQ as well as the OLC33/34 byproducts.
            raw.execute("INSERT OR REPLACE INTO profession_storage VALUES(1,'craftbox','ore',2)")
            raw.commit()
            baseline=snapshot()
            raw.execute('SAVEPOINT caller_bonus')
            ck(db.craft_item_atomic_v106(1,{'ore':1},'helm',1,
                  containers={'ore':'craftbox'},extra_outputs=(('gem',2),('gem',3))) is True,
               'caller-owned bonus transaction succeeds provisionally')
            ck(snapshot()!=baseline and db.item_qty(1,'gem')==g+10,
               'provisional bonus outputs are visible before outer rollback')
            raw.execute('ROLLBACK TO SAVEPOINT caller_bonus')
            raw.execute('RELEASE SAVEPOINT caller_bonus')
            ck(snapshot()==baseline,'outer rollback restores main and bonus items')
        raw.close()
        return n
    finally:
        if previous is None: os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=previous

if __name__=='__main__':print('V106 CRAFT BONUS ATOMIC:',run(),'PASS',flush=True)
