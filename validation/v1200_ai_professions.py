# -*- coding: utf-8 -*-
"""v12: 22 autonomous AI profiles, Jammer safety, 22 real projects and SQLite."""
import asyncio
import os
import tempfile
from types import SimpleNamespace

from systems.summon_ai_v1200 import (CLASS_AI,plan_for_class,jammer_eligible,
                                      paralysis_token)
from systems.profession_projects_v1200 import (PROJECTS,LEVELS,recipe,
                                                 project_item_id,resolve,ensure_schema as schema12)
from systems.class_minions_v1119 import CLASS_MINIONS_BY_CLASS_V1119
from data.items import ITEMS
from player.session_mixins.profesje6 import SessionProfesje6Mixin, _sum,ensure_schema as schema6
from core.classes_skills import RACES,CLASSES
from storage.database import Database


def ai_rules():
    checks=0
    classes={r[0] for r in CLASSES}
    assert classes==set(CLASS_AI)
    checks+=1
    for cls,(title,role,bonus) in CLASS_AI.items():
        assert title and bonus>0
        base=dict(owner_hp=1000,owner_max=1000,ally_needs_heal=False,
                  guarded=False,enemy_hp=1000,enemy_max=1000,boss=False,
                  marked=False,controlled=False,step=3)
        plan=plan_for_class(cls,**base)
        if role=='heal':
            assert plan['action']!='heal'
            plan=plan_for_class(cls,**(base|{'ally_needs_heal':True}))
            assert plan['action']=='heal'
            checks+=2
        elif role=='guard':
            assert plan['action']!='guard'
            assert plan_for_class(cls,**(base|{'owner_hp':150}))['action']=='guard'
            assert plan_for_class(cls,**(base|{'owner_hp':150,'guarded':True}))['action']!='guard'
            checks+=3
        elif role in ('slow','curse'):
            assert plan['action']==role
            assert plan_for_class(cls,**(base|{'boss':True}))['action']=='strike'
            assert plan_for_class(cls,**(base|{'controlled':True}))['action']=='strike'
            checks+=3
        elif role=='mark':
            assert plan['action']=='mark'
            assert plan_for_class(cls,**(base|{'marked':True}))['action']=='strike'
            checks+=2
        elif role=='execute':
            assert plan['action']=='strike'
            assert plan_for_class(cls,**(base|{'enemy_hp':250}))['action']=='execute'
            checks+=2
        assert bonus<=.12
        checks+=2
    assert len(CLASS_MINIONS_BY_CLASS_V1119)==19
    checks+=1
    mob=SimpleNamespace(alive=True,v11196_logic_bomb_rounds=2,
                        v11196_logic_bomb_effects={'slow'},v11196_jammer_stop_rounds=0)
    assert paralysis_token(mob) is None
    assert not jammer_eligible(mob,{'name':'Zwykły','level':1})
    mob.v11196_logic_bomb_effects.add('paralyze');mob.v1200_logic_paralyze_token=3
    assert paralysis_token(mob)==3
    assert jammer_eligible(mob,{'name':'Zwykły','level':1})
    mob.v1200_jammer_attempted_token=3
    assert not jammer_eligible(mob,{'name':'Zwykły','level':1})
    mob.v1200_logic_paralyze_token=4
    assert jammer_eligible(mob,{'name':'Zwykły','level':1})
    mob.v11196_jammer_stop_rounds=2
    assert not jammer_eligible(mob,{'name':'Zwykły','level':1})
    mob.v11196_jammer_stop_rounds=0;mob.v11196_logic_bomb_rounds=0
    assert not jammer_eligible(mob,{'name':'Zwykły','level':1})
    checks+=8
    return checks



def amulet_storage_regression():
    """Do not break minimalist Mage fixtures; recognize real craftbox items."""
    from systems.summon_ai_v1200 import profession_amulet_bonus
    from systems.profession_projects_v1200 import project_item_id
    import sqlite3
    checks=0
    class MinimalDB:
        # This deliberately has no inventory table, as in legacy v1702 Mage tests.
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
        def item_qty(self,*args):return 0
        def storage_qty(self,*args):return 0
    stub=MinimalDB()
    assert profession_amulet_bonus(stub,42)==0.0
    stub.conn.close()
    checks+=1
    with tempfile.TemporaryDirectory(prefix='sb12_amulet_') as path:
        db=Database(os.path.join(path,'items.db'))
        master=db.create_account('BonusTester','ValidPassword2026!')
        forms={k:'Testowy' for k in ('nom','gen','dat','acc','ins','loc','voc')}
        aid,_=db.create_character_for_master(master,'BonusTest',RACES[0],CLASSES[0],forms)
        assert profession_amulet_bonus(db,aid)==0.0
        checks+=1
        item=project_item_id('Kowalstwo')
        db.add_item(aid,item,1)
        assert db.item_qty(aid,item)==0
        assert db.storage_qty(aid,'craftbox',item)==1
        assert profession_amulet_bonus(db,aid)==.04
        checks+=3
        db.remove_storage_item(aid,'craftbox',item,1)
        assert profession_amulet_bonus(db,aid)==0.0
        checks+=1
        # Retain support for older item copies stored directly in inventory.
        db.add_item(aid,'small_fish',1)
        db.conn.execute('INSERT INTO inventory(account_id,item_id,quantity) VALUES (?,?,1)',(aid,item))
        db.conn.commit()
        assert profession_amulet_bonus(db,aid)==.04
        checks+=1
        db.conn.close()
    return checks


class Practice(SessionProfesje6Mixin):
    def __init__(self,db,aid):
        self.server=SimpleNamespace(db=db)
        self.account_id=aid
        self.character=SimpleNamespace(room_id='market',silver=25000,gold=0,mithril=0)
        self.output=[]
        self.break_xp=False
    async def send(self,msg):self.output.append(str(msg))
    def grant_profession_progress(self,prof,xp,tool,tool_xp,*,content_level=None,**kw):
        db=self.server.db
        # Progress queries are pre-initialized by the test or handler.
        db.conn.execute('UPDATE professions SET xp=xp+?,actions=actions+1 WHERE account_id=? AND profession=?',(xp,self.account_id,prof))
        db.conn.execute('UPDATE tools SET xp=xp+?,uses=uses+1 WHERE account_id=? AND tool_type=?',(tool_xp,self.account_id,tool))
        if self.break_xp:raise RuntimeError('Intentional regression rollback')
        return ([f'{prof} EXP +{xp}; narzędzie EXP +{tool_xp}'],600,600)
    async def do(self,cmd):
        self.output=[]
        await self.profesje6_command(cmd)
        return '\n'.join(self.output)


async def professions_sqlite():
    checks=0
    assert len(PROJECTS)==22
    assert len({x.code for x in PROJECTS.values()})==22
    for name,p in PROJECTS.items():
        assert p.primary in ITEMS and p.partner in ITEMS,(name,p.primary,p.partner)
        assert project_item_id(name) in ITEMS
        assert resolve(name)==name and resolve(p.code)==name
        for tier in LEVELS:
            ingredients=recipe(name,tier)
            assert len(ingredients)==2 and all(q>0 for i,q in ingredients)
            checks+=2
        checks+=3
    with tempfile.TemporaryDirectory(prefix='sb12_regress_') as d:
        db=Database(os.path.join(d,'test.db'))
        master=db.create_account('TesterSb12','ValidPassword2026!')
        forms={k:'Testowy' for k in ('nom','gen','dat','acc','ins','loc','voc')}
        aid,_=db.create_character_for_master(master,'PrawdziwyMistrz',RACES[0],CLASSES[0],forms)
        db.set_shared_wallet_for_master(master,25000,0,0)
        session=Practice(db,aid)
        schema6(db);schema12(db.conn);db.conn.commit()
        from systems.new_professions import PROFESSIONS
        for name,p in PROJECTS.items():
            db.profession(aid,name);db.tool(aid,p.tool)
            db.conn.execute('UPDATE professions SET level=600 WHERE account_id=? AND profession=?',(aid,name))
            db.conn.execute('UPDATE tools SET level=600 WHERE account_id=? AND tool_type=?',(aid,p.tool))
            if name in PROFESSIONS:
                t,item,_=PROFESSIONS[name]
                db.conn.execute('INSERT OR IGNORE INTO prof6_tools_owned VALUES(?,?)',(aid,item))
                db.add_item(aid,item,1)
        db.conn.commit()
        for name,p in PROJECTS.items():
            for item,qty in recipe(name,600):db.add_item(aid,item,qty*7)
            db.conn.commit()
            before=db.profession(aid,name)['xp']
            for i in range(5):
                result=await session.do('projekt wykonaj '+name+' 600')
                assert 'Wykonano' in result,(name,i,result)
            assert _sum(db,aid,project_item_id(name))==5
            assert db.profession(aid,name)['xp']>before
            assert db.conn.execute('SELECT made FROM prof12_masterworks WHERE account_id=? AND profession=?',(aid,name)).fetchone()[0]==5
            result=await session.do('projekt oddaj '+name)
            assert 'ukończony' in result,(name,result)
            assert _sum(db,aid,project_item_id(name))==0
            result=await session.do('projekt oddaj '+name)
            assert 'już dziś' in result,(name,result)
            assert db.conn.execute('SELECT turned_in FROM prof12_masterworks WHERE account_id=? AND profession=?',(aid,name)).fetchone()[0]==5
            checks+=10
        # Pre-charge guard: required level and existing tool prevent free crafting.
        db.conn.execute('UPDATE professions SET level=24 WHERE account_id=? AND profession=?',(aid,'Rolnictwo'))
        db.conn.commit()
        before=_sum(db,aid,'field_grain')
        result=await session.do('projekt wykonaj Rolnictwo 25')
        assert 'zablokowany' in result or 'poziomu 25' in result
        assert _sum(db,aid,'field_grain')==before
        checks+=2
        # Cross-profession resources in herb bag, not merely loose inventory.
        db.conn.execute('UPDATE professions SET level=600 WHERE account_id=? AND profession=?',(aid,'Łowiectwo'))
        db.conn.execute('DELETE FROM inventory WHERE account_id=? AND item_id=?',(aid,'mint'))
        db.conn.execute('DELETE FROM profession_storage WHERE account_id=? AND item_id=?',(aid,'mint'))
        db.conn.commit()
        db.add_storage_item(aid,'herbbag','mint',6)
        assert _sum(db,aid,'mint')==6
        result=await session.do('projekt wykonaj Łowiectwo 25')
        assert 'Wykonano' in result,result
        assert db.storage_qty(aid,'herbbag','mint')==5
        checks+=3
        # Atomic material removal and XP: error must not grant or lose anything.
        project=PROJECTS['Łowiectwo']
        db.add_item(aid,project.primary,10)
        beforeitem=_sum(db,aid,project.primary)
        beforexp=db.profession(aid,'Łowiectwo')['xp']
        beforemade=db.conn.execute('SELECT made FROM prof12_masterworks WHERE account_id=? AND profession=?',(aid,'Łowiectwo')).fetchone()[0]
        session.break_xp=True
        try:
            await session.do('projekt wykonaj Łowiectwo 25')
            raise AssertionError('expected rollback')
        except RuntimeError as exc:
            assert 'Intentional' in str(exc)
        finally:session.break_xp=False
        assert _sum(db,aid,project.primary)==beforeitem
        assert db.profession(aid,'Łowiectwo')['xp']==beforexp
        assert db.conn.execute('SELECT made FROM prof12_masterworks WHERE account_id=? AND profession=?',(aid,'Łowiectwo')).fetchone()[0]==beforemade
        checks+=4
        db.conn.close()
    return checks


async def battle_runtime_smoke():
    """Real registered combat loop: healer heals injured, never full HP."""
    import sqlite3
    from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin,ensure_schema
    checks=0
    class LocalDB:
        _v1700_ready=True
        def __init__(self):
            self.conn=sqlite3.connect(':memory:');self.conn.row_factory=sqlite3.Row
            ensure_schema(self.conn)
            self.conn.execute('CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER)')
            self.conn.commit()
    class LocalServer:
        def __init__(self,db):self.db=db
        def party_sessions(self,aid,same_room=None):return [hero]
        async def party_combat_broadcast(self,*a,**kw):pass
    class Healer(SessionSkyV1700Mixin):
        def __init__(self):
            self.account_id=1
            self.character=SimpleNamespace(name='Kontrola',room_id='temple',character_level=300)
            self.current_hp=800;self.current_mana=5000;self.skill_guard=0
            self.server=LocalServer(LocalDB());self.closed=False;self.messages=[]
        def _v1702_prepare_summon_lives(self,*a):pass
        def _v1710_refresh_summon_health(self,*a):pass
        def _v1700_city_bonuses(self):return (0,0,0)
        def _v1800_form_bonus(self):return (1.0,0)
        def _v1800_tactic(self):return 'atak'
        def max_hp(self):return 5000
        def spell_power(self):return 1200
        def physical_power(self):return 1200
        def active_class_names(self):return ('Kapłan',)
        async def send_combat(self,text,**kw):self.messages.append(text)
        async def send(self,text):self.messages.append(text)
        async def apply_boss_defense(self,mob,amount):return amount
        def v0210_adjust_player_damage(self,amount):return amount
        async def mob_defeated(self,mob):pass
    hero=Healer()
    c=hero.server.db.conn
    c.execute("INSERT INTO summons_v1700(account_id,summon_type,level,active,hp,max_hp,stance) "
              "VALUES(1,'aniol_laski',300,1,500,500,'atakuj')")
    c.commit()
    mob=SimpleNamespace(alive=True,room_id='temple',template_id='training_dummy',max_hp=500000,hp=500000)
    await hero.summon_combat_turn_v1700(mob)
    assert hero.current_hp>800 and any('Łaska uzdrowienia' in msg for msg in hero.messages)
    assert mob.hp<500000
    checks+=3
    hero.current_hp=hero.max_hp();hero.messages.clear()
    hp=hero.current_hp
    await hero.summon_combat_turn_v1700(mob)
    assert hero.current_hp==hp
    assert all('Łaska uzdrowienia' not in msg for msg in hero.messages)
    checks+=2
    await hero.summons_v1700('ai off')
    assert c.execute('SELECT enabled FROM summon_ai_prefs_v1200 WHERE account_id=1').fetchone()[0]==0
    hero.messages.clear();await hero.summons_v1700('ai on')
    assert c.execute('SELECT enabled FROM summon_ai_prefs_v1200 WHERE account_id=1').fetchone()[0]==1
    checks+=2
    c.close()
    return checks


async def party_summon_visibility():
    """Summon combat messages reach every nearby party member once; distant players never."""
    from importlib.util import spec_from_file_location, module_from_spec
    from pathlib import Path
    spec=spec_from_file_location('sb12_party_server',Path(__file__).resolve().parents[1]/'server'/'mud_server.py')
    module=module_from_spec(spec)
    spec.loader.exec_module(module)
    MudServer=module.MudServer
    count=0
    class Session:
        def __init__(self, aid, room):
            self.account_id=aid
            self.character=SimpleNamespace(room_id=room,name=f'Gracz{aid}')
            self.closed=False
            self.messages=[]
        async def send(self, text, **kwargs):
            self.messages.append((text,kwargs))
    owner=Session(1,'arena')
    friend1=Session(2,'arena')
    friend2=Session(3,'arena')
    distant=Session(4,'temple')
    solo=Session(5,'arena')
    class Bus:
        party_nearby_broadcast=MudServer.party_nearby_broadcast
        party_combat_broadcast=MudServer.party_combat_broadcast
        def party_key_for_account(self,aid):
            return 'squad' if aid in (1,2,3,4) else None
        def party_sessions(self,aid,same_room=None):
            people=(owner,friend1,friend2,distant)
            return [x for x in people if same_room is None or x.character.room_id==same_room]
    bus=Bus()
    text='Anioł Łaski (przywołanie Gracz1, poziom 200) trafia Smoka za 12500 obrażeń. AI: Łaska uzdrowienia.'
    assert await bus.party_combat_broadcast(owner,text,detail='essential')==2
    count+=1
    for friend in (friend1,friend2):
        assert friend.messages==[(text,{'combat_detail':'essential','history_category':'combat'})]
        count+=1
    assert not distant.messages and not solo.messages
    count+=1
    assert await bus.party_combat_broadcast(solo,text,detail='essential')==0
    count+=1
    friend2.closed=True
    assert await bus.party_combat_broadcast(owner,text,detail='essential')==1
    assert len(friend1.messages)==2 and len(friend2.messages)==1
    count+=2
    return count


def run_regression():
    return (ai_rules()+amulet_storage_regression()+asyncio.run(professions_sqlite())
            +asyncio.run(battle_runtime_smoke())
            +asyncio.run(party_summon_visibility()))

if __name__=='__main__':
    print(f'v12: AI 22 KLAS / JAMMER / PROJEKTY 22 PROFESJI: {run_regression()} checks PASS')
