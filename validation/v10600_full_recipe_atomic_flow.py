# -*- coding: utf-8 -*-
"""v106: staged high-level perform_recipe + actual database ingredient/output flow.

No real player files.  SQLite memory only; v105 path and v106 fail-closed.
"""
import asyncio
import os
import sqlite3
import sys
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.database import _DeferredCommitConnection
from validation.v10600_crafting_materials_atomic import DB, CAT
from player.session_mixins.crafting import SessionCraftingMixin
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy, _check_account
from systems.equipment_crafting_recipe_v10600 import plan_recipe_ingredients
from systems.equipment_crafting_guard_v10600 import guard_recipe


class CraftDB(DB):
    def __init__(self, conn):
        super().__init__(conn)
        self.achievements=[]
    def tool(self,aid,tool_type): return {'level':1}
    def profession(self,aid,profession): return {'level':1}
    def crafting_mastery_v03054(self,*args): return {'actions':0}
    def add_crafting_mastery_action_v03054(self,*args,**kwargs): return {'actions':1}
    def add_lifetime_stat(self,*args): self.achievements.append(args)


class CraftSession(SessionCraftingMixin):
    def __init__(self,db):
        self.account_id=1
        self.server=SimpleNamespace(db=db)
        self.character=SimpleNamespace(name='TEST',room_id='forge')
        self.combat_mob_key=None
        self.messages=[]
        self.awards=[]
    def recipe_container_for_item(self,iid): return 'craftbox' if iid in ('ore','gem') else None
    def recipe_tool_info(self,recipes,recipe): return ('smithing','hammer','Młot')
    def recipe_profession_name(self,recipes,recipe): return 'Kowalstwo'
    def recipe_action_seconds(self,*args): return 0
    def recipe_station_text(self,stations): return ', '.join(map(str,stations))
    def tool_action_label(self,tool_type): return 'Praca młota'
    def guild_row_v0926(self): return None
    def profession_content_level_v11342(self,**kwargs): return 10
    async def send(self,s): self.messages.append(s)
    async def record_item_collection(self,*args,**kwargs): self.awards.append('collection')
    async def announce_craft_quest_progress(self,*args,**kwargs): self.awards.append('quest')
    async def advance_class_guild_quest_v11132(self,*args,**kwargs): self.awards.append('guild')
    async def sync_extended_achievements(self): self.awards.append('achievements')
    def grant_profession_progress(self,*args,**kwargs):
        self.awards.append('exp')
        return [],1,1


def make_db():
    raw=sqlite3.connect(':memory:');raw.row_factory=sqlite3.Row
    raw.executescript('''
        CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
            PRIMARY KEY(account_id,item_id));
        CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
            PRIMARY KEY(account_id,slot));
        CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
            PRIMARY KEY(account_id,record_key));
        CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,
            quantity INTEGER,PRIMARY KEY(account_id,container,item_id));
        CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,
            paid_silver INTEGER,quantity INTEGER,PRIMARY KEY(account_id,item_id,paid_silver));
        CREATE TABLE crafting_mastery_v03054(
            account_id INTEGER NOT NULL, profession TEXT NOT NULL, category TEXT NOT NULL,
            actions INTEGER NOT NULL DEFAULT 0, criticals INTEGER NOT NULL DEFAULT 0,
            legendary_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(account_id,profession,category));
        CREATE TABLE lifetime_statistics(
            account_id INTEGER NOT NULL,stat_key TEXT NOT NULL,value INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(account_id,stat_key));
        INSERT INTO inventory VALUES(1,'ore',3),(1,'gem',2),(1,'hammer',1),(2,'ore',7);
        INSERT INTO profession_storage VALUES(1,'craftbox','ore',3),(1,'craftbox','gem',2);
    ''')
    db=CraftDB(_DeferredCommitConnection(raw))
    prepare_on_disposable_copy(db.conn,CAT,confirm_disposable_copy=True)
    return db,raw


def run():
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    n=0
    def ck(condition,detail):
        nonlocal n
        if not condition: raise AssertionError(detail)
        n+=1
    def snap(raw):
        return tuple((t,tuple(tuple(r) for r in raw.execute('SELECT * FROM '+t+' ORDER BY 1,2')))
             for t in ('inventory','profession_storage','shop_purchase_lots_v1175','v106_item_instances','crafting_mastery_v03054','lifetime_statistics'))

    try:
        db,raw=make_db()
        s=CraftSession(db)
        recipe={'ingredients':{'ore':2},'distinct_ingredient_pool':['ore','gem'],
                'distinct_ingredient_count':2,'pooled_ingredient_pool':['ore','gem'],
                'pooled_ingredient_count':2}
        before=snap(raw)
        plan=plan_recipe_ingredients(db,1,recipe,s.recipe_container_for_item)
        ck(plan[0]=={'ore':5,'gem':1},'one allocation across all three ingredient groups')
        ck(plan[1]=={'ore':'craftbox','gem':'craftbox'},'original containers preserved')
        ck(snap(raw)==before,'planner never mutates SQLite')
        ck(plan_recipe_ingredients(db,1,dict(recipe,ingredients={'ore':6}),s.recipe_container_for_item) is None,
           'cannot reuse ore quantity both as direct and distinct/pooled ingredient')
        ck(plan_recipe_ingredients(db,1,{'pooled_ingredient_pool':['ore','ore'],
                   'pooled_ingredient_count':7},s.recipe_container_for_item) is None,
           'duplicate pool entry cannot double available stock')
        ck(plan_recipe_ingredients(db,1,{'distinct_ingredient_pool':['gem','gem'],
                   'distinct_ingredient_count':2},s.recipe_container_for_item) is None,
           'duplicate distinct entry cannot masquerade as two species')
        ck(plan_recipe_ingredients(db,1,{'ingredients':{'ore':1},
                   'pooled_ingredient_pool':['ore'],'pooled_ingredient_count':5},
                   s.recipe_container_for_item)[0]=={'ore':6},'shared direct+pooled stock counted exactly')
        rare={'ingredients':{'ore':5},'distinct_ingredient_pool':['ore','gem'],
              'distinct_ingredient_count':1,'pooled_ingredient_pool':['ore'],
              'pooled_ingredient_count':1}
        ck(plan_recipe_ingredients(db,1,rare,s.recipe_container_for_item)[0]=={'ore':6,'gem':1},
           'distinct picks non-pooled species to preserve rare pooled material')
        # Unchosen pooled/distinct candidates must NOT become zero-quantity
        # ingredient entries: the atomic guard correctly rejects qty <= 0.
        optional={'ingredients':{'ore':2},
                  'distinct_ingredient_pool':['ore','gem'],
                  'distinct_ingredient_count':1,
                  'pooled_ingredient_pool':['gem','ore'],
                  'pooled_ingredient_count':1}
        optional_plan=plan_recipe_ingredients(db,1,optional,s.recipe_container_for_item)
        ck(optional_plan[0]=={'ore':3,'gem':1},
           'unused distinct candidate is not a zero-quantity ingredient')
        ck(all(v>0 for v in optional_plan[0].values()),
           'planner emits only strictly positive ingredient quantities')
        # A candidate that is unavailable must also not appear as a zero entry.
        unavailable={'ingredients':{'ore':1},
                     'pooled_ingredient_pool':['nonexistent','gem'],
                     'pooled_ingredient_count':1}
        unavailable_plan=plan_recipe_ingredients(db,1,unavailable,s.recipe_container_for_item)
        ck(unavailable_plan[0]=={'ore':1,'gem':1},
           'unavailable pooled choice is omitted from final plan')
        ck(snap(raw)==before,'optional pool planning does not change data')
        ck(db.craft_item_atomic_v106(1,plan[0],'helm',2,containers=plan[1]) is True,
           'actual physical-gear production consumes all categories together')
        ck(db.item_qty(1,'helm')==2,'crafted count equals output inventory')
        ck(raw.execute("SELECT COUNT(*) FROM v106_item_instances WHERE item_id='helm'").fetchone()[0]==2,
           'two newly crafted gear instances have unique identities')
        ck(db.storage_qty(1,'craftbox','ore')==0 and db.item_qty(1,'ore')==1,
           'materials consumed without using more than available')
        ck(db.storage_qty(1,'craftbox','gem')==1 and db.item_qty(1,'gem')==2,
           'distinct and pooled gem reserved correctly')
        ck(db.item_qty(2,'ore')==7,'account isolation')
        _check_account(db.conn,1,CAT);ck(True,'v106 shadow ledger valid')
        raw.close()

        # Exercise the ACTUAL async perform_recipe entrypoint with actual SQLite.
        db,raw=make_db();s=CraftSession(db)
        recipe={'name':'Testowe Hełmy','tool_type':'smithing',
                'ingredients':{'ore':2},'distinct_ingredient_pool':['gem'],
                'distinct_ingredient_count':1,'pooled_ingredient_pool':['ore','gem'],
                'pooled_ingredient_count':2,'output':'helm','quantity':1,
                'stations':['forge'],'tool_xp':100,'profession_xp':100}
        recipes={'helm_test':recipe}
        from player.session_mixins import crafting as c
        # Quality selection and yield are deliberately deterministic; keep
        # genuine transaction, original async recipe method and its side-effects.
        patches=[
            patch.object(c,'find_by_name',lambda table,q:('helm_test',recipe)),
            patch.object(c,'tool_tier',lambda level:1),
            patch.object(c,'required_tool_tier_for_level',lambda level:1),
            patch.object(c,'tool_tier_bonus_chance',lambda level:0),
            patch.object(c,'craft_inspiration_v11324',lambda *args:None),
            patch.object(c,'crafting_quality_roll_v03054',lambda *args:'good'),
            patch.object(c,'material_grade_v1250',lambda *args:0),
            patch.object(c,'material_quality_upgrade_v1250',lambda quality,*args: quality),
            patch.object(c,'masterpiece_promote_v12812',lambda q,*args: (q,False)),
            patch.object(c,'crafting_critical_chance_v03054',lambda *args:0),
            patch.object(c,'crafting_quality_output_v03054',lambda iid,*args: (iid+'_quality',None)),
            patch.object(c,'crafting_mastery_category_v03054',lambda *args:'equipment'),
            patch.object(c,'crafting_output_is_quality_equipment_v03054',lambda iid:False),
            patch.object(c,'ITEMS', {'ore':{'name':'Ruda'},'gem':{'name':'Klejnot'},
                                      'helm':{'name':'Hełm','type':'armor'},
                                      'helm_quality':{'name':'Dobry Hełm','type':'armor'},
                                      'hammer':{'name':'Młot'}}),
            patch('systems.endless_crafting_v5500.endless_crafted_equipment_v5500',lambda iid,*a:iid),
            patch('systems.live_olc28_expansion.craft_yield',lambda prof,qty:qty),
            patch('systems.live_olc32_finale.crafting_bonus',lambda rid,room,qty:2*qty),
            patch('systems.live_olc35_finale.city_craft_bonus',lambda *args:args[-1]),
            patch('systems.live_olc33_mechanics.craft_byproduct',lambda *args:None),
            patch('systems.live_olc34_integration.profession_find',lambda *args:None),
        ]
        with ExitStack() as stack:
            for pp in patches: stack.enter_context(pp)
            ok=asyncio.run(s.perform_recipe('helm_test',recipes,'rzemiosło'))
            ck(ok is True,'real perform_recipe succeeds')
            ck(db.item_qty(1,'helm_quality')==2 and db.item_qty(1,'helm')==0,
               'quality variant+city yield preserved before atomic craft')
            ck(raw.execute("SELECT COUNT(*) FROM v106_item_instances WHERE item_id='helm_quality'").fetchone()[0]==2,
               'high-level recipe created physical instance IDs')
            ck(db.item_qty(1,'ore')==2 and db.storage_qty(1,'craftbox','ore')==0,
               'main ingredients consumed just once')
            ck(db.item_qty(1,'gem')==2 and db.storage_qty(1,'craftbox','gem')==1,
               'distinct+pooled allocation respects stock')
            ck(tuple(raw.execute('SELECT actions,criticals,legendary_count FROM crafting_mastery_v03054 WHERE account_id=1').fetchone())==(1,0,0),
               'mastery recorded once inside item transaction')
            ck(tuple(raw.execute("SELECT value FROM lifetime_statistics WHERE account_id=1 ORDER BY stat_key").fetchall()[i][0] for i in range(3))==(1,2,1),
               'craft, items and profession lifetime totals recorded once')
            ck('exp' in s.awards and 'quest' in s.awards,'existing EXP and quest hooks run once')
            ck(s.awards.count('exp')==1 and s.awards.count('quest')==1,
               'no doubled XP or quest hooks for bonus output')
            _check_account(db.conn,1,db._v106_shadow_item_catalog)
            ck('helm_quality' in db._v106_shadow_item_catalog,
               'dynamic quality variant is registered as physical EQ')
            # One more execution models the existing craft-max call pattern:
            # each run has its own transaction and new, unique equipment IDs.
            first_ids={r[0] for r in raw.execute(
                "SELECT instance_id FROM v106_item_instances WHERE item_id='helm_quality'")}
            raw.execute("INSERT OR REPLACE INTO profession_storage VALUES(1,'craftbox','ore',2)")
            raw.commit()
            ck(asyncio.run(s.perform_recipe('helm_test',recipes,'rzemiosło')) is True,
               'second real recipe succeeds without duplicating previous instances')
            later_ids={r[0] for r in raw.execute(
                "SELECT instance_id FROM v106_item_instances WHERE item_id='helm_quality'")}
            ck(len(first_ids)==2 and len(later_ids)==4 and first_ids.issubset(later_ids),
               'successive crafts preserve old instance IDs and mint two new IDs')
            ck(s.awards.count('exp')==2 and s.awards.count('quest')==2,
               'two separate successful crafts give exactly two sets of XP/quests')
            ck(raw.execute('SELECT actions FROM crafting_mastery_v03054 WHERE account_id=1').fetchone()[0]==2,
               'high-level craft did not double-increment mastery')
            ck(raw.execute("SELECT value FROM lifetime_statistics WHERE account_id=1 AND stat_key='crafted_items'").fetchone()[0]==4,
               'high-level craft did not double-increment lifetime output')
            _check_account(db.conn,1,db._v106_shadow_item_catalog)
            ck(True,'multi-craft preserves physical ledger')
            # Trigger an exception AFTER input removal.  Real perform_recipe
            # must report failure, restore every ingredient and grant no XP.
            raw.execute("INSERT OR REPLACE INTO profession_storage VALUES(1,'craftbox','ore',4)")
            raw.execute('''CREATE TRIGGER reject_quality BEFORE INSERT ON v106_item_instances
                WHEN NEW.item_id='helm_quality'
                BEGIN SELECT RAISE(ABORT,'blocked physical variant'); END''')
            raw.commit()
            old=snap(raw);s.awards.clear()
            ck(asyncio.run(s.perform_recipe('helm_test',recipes,'rzemiosło')) is False,
               'high-level crafting refuses SQL failure')
            ck(snap(raw)==old and s.awards==[],
               'high-level SQL failure restores input, gear and prevents XP')
            raw.execute('DROP TRIGGER reject_quality');raw.commit()
            # Induce missing distinct resource BEFORE preflight, ensure no awards.
            s.awards.clear();old=snap(raw)
            raw.execute("DELETE FROM profession_storage WHERE account_id=1 AND item_id='gem'")
            raw.execute("DELETE FROM inventory WHERE account_id=1 AND item_id='gem'")
            raw.commit();old=snap(raw)
            ck(asyncio.run(s.perform_recipe('helm_test',recipes,'rzemiosło')) is False,
               'second recipe with missing ingredients safely denied')
            ck(s.awards==[] and snap(raw)==old,'denied recipe never awards XP or consumes materials')
        raw.close()
        return n
    finally:
        if previous is None: os.environ.pop('SOULBOUND_V106_STAGING',None)
        else: os.environ['SOULBOUND_V106_STAGING']=previous

if __name__=='__main__':print('V106 FULL RECIPE ATOMIC:',run(),'PASS',flush=True)
