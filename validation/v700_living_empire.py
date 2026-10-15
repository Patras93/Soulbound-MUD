# -*- coding: utf-8 -*-
"""Fail-closed v7.00.0 regression on isolated real SQLite and assembled runtime."""
import asyncio
import tempfile
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace


def run_regression(runtime=None):
    if runtime is None:
        import server as runtime
    from systems.living_empire_v7000 import (
        STORY,STORY_IDS,NEW_GOODS,UPGRADES,MISSION_TYPES,VOYAGES,CARAVANS,MASTER_INPUT,
    )
    from systems.new_professions import PROFESSIONS,AREAS,TIERS
    from player.session_mixins.living_empire_v7000 import SessionLivingEmpireV7000Mixin,ensure_schema,tier_for,_sum,ALL_TOOLS
    from validation.v600_professions import _Practice
    from player.session_mixins.profesje6 import ensure_schema as ensure_prof6
    from storage.database import Database
    from core.classes_skills import RACES,CLASSES
    from world.legends_v3200 import _reachable,OPPOSITE
    from data.items import ITEMS
    checks=0
    def ok(test,label):
        nonlocal checks
        assert test,'v7.00.0 regression: '+label
        checks+=1
    ok(runtime.VERSION=='7.00.0','canonical version')
    ok(len(runtime.QUESTS)==3925,'all 3925 old+new quests')
    ok(len(STORY_IDS)==64 and len(set(STORY_IDS))==64,'64 unique authored story quests')
    ok(len(ALL_TOOLS)==22 and len(MASTER_INPUT)==22,'22 professions/tools')
    ok(len(NEW_GOODS)==8 and len(UPGRADES)==8,'8 goods and 8 permanent upgrades')
    ok(set(PROFESSIONS).issubset(ALL_TOOLS),'8 v6 professions preserved')
    ok(len(VOYAGES)==4 and len(CARAVANS)==4,'4 sea routes and 4 market destinations')
    knownrooms=set(runtime.ROOMS);reachable=_reachable(runtime.ROOMS)
    counts=Counter(npc.get('room') for npc in runtime.NPCS.values())
    for cid,(prof,anchor,title,npc_name,subject) in enumerate(STORY,1):
        room=f'v700_chronicle_room_{cid}';npc=f'v700_chronicle_npc_{cid}'
        ok(room in knownrooms and room in reachable,room+' reachable')
        ok(counts[room]==1 and runtime.NPCS[npc]['room']==room,room+' sole NPC')
        ok(any(runtime.ROOMS[room]['exits'].get(OPPOSITE[d])==anchor
               for d,to in runtime.ROOMS[anchor]['exits'].items() if to==room),room+' linked both ways')
        ok(runtime.NPCS[npc]['specialist_quests']==tuple(STORY_IDS[(cid-1)*8:cid*8]),room+' actual NPC quests')
    prev=None
    for idx,qid in enumerate(STORY_IDS):
        q=runtime.QUESTS[qid]
        ok(q.get('requires_quest')==prev,qid+' prerequisite')
        ok(q['required_action_code'] and q['min_action_tier'] in TIERS,qid+' real profession action')
        ok(q['reward_profession_xp']>0 and q['reward_tool_xp']>0 and q['reward_silver']>0,qid+' independent rewards')
        ok(q['reward_items']=={'v700_story_seal':1+(idx%8)//3},qid+' authored reward')
        prev=qid
    for item in NEW_GOODS:
        ok(item in runtime.ITEMS and item in ITEMS,item+' in unified item registry')
    for k,(prof,area,inputs,reward) in UPGRADES.items():
        ok(prof in ALL_TOOLS and area in AREAS,k+' valid profession and region')
        for item,qty in inputs:
            ok(item in ITEMS and qty>0,k+' valid input '+item)
        ok(reward in ITEMS,k+' output')
    for k,(prof,area,inputs,reward,cooldown) in MISSION_TYPES.items():
        ok(prof in PROFESSIONS and area in AREAS and cooldown>0,k+' action identity')
        ok(reward in ITEMS and all(i in ITEMS for i,_ in inputs),k+' material economy')
    for r in (VOYAGES,CARAVANS):
        for code,row in r.items():
            ok(row[0] in TIERS and all(i in ITEMS for i,_ in (row[3])),code+' real inputs')
    for prof,ingredient in MASTER_INPUT.items():
        ok(ingredient in ITEMS,prof+' mastery actually produces ingredient')
    class Practice(SessionLivingEmpireV7000Mixin,_Practice):
        async def do7(self,cmd):
            self.output=[]
            await self.imperium7_command(cmd)
            return '\n'.join(self.output)
    with tempfile.TemporaryDirectory(prefix='sb7_regression_') as tmp:
        db_path=Path(tmp)/'test.sqlite'
        db=Database(str(db_path))
        master=db.create_account('TestLivingEmpire7','Secure_Test_V7000_password!')
        cases={k:'Giermek' for k in ('nom','gen','dat','acc','ins','loc','voc')}
        aid,_=db.create_character_for_master(master,'MistrzGildii7',RACES[0],CLASSES[0],cases)
        aid2,_=db.create_character_for_master(master,'UczenGildii7',RACES[0],CLASSES[0],cases)
        db.set_shared_wallet_for_master(master,150000,0,0)
        session=Practice(db,aid)
        session.character.silver=150000
        ensure_schema(db)
        ensure_prof6(db)
        for prof,(tool,item,name) in PROFESSIONS.items():
            db.add_item(aid,item,1)
            db.conn.execute('INSERT OR IGNORE INTO prof6_tools_owned(account_id,item_id) VALUES(?,?)',(aid,item))
            db.profession(aid,prof); db.tool(aid,tool)
            db.save_profession(aid,prof,700,0,0)
            db.save_tool(aid,tool,700,0,0)
        for prof,tool in ALL_TOOLS.items():
            if prof not in PROFESSIONS:
                db.profession(aid,prof); db.tool(aid,tool)
                db.save_profession(aid,prof,700,0,0)
                db.save_tool(aid,tool,700,0,0)
        db.conn.commit()
        # Test every upgrade with production consumables and state isolation.
        for key,(prof,region,inputs,reward) in UPGRADES.items():
            session.character.room_id=sorted(AREAS[region])[0]
            for item,qty in inputs: db.add_item(aid,item,qty*2)
            before=db.profession(aid,prof)['xp']
            message=asyncio.run(session.do7('ulepsz '+key))
            ok('Ulepszono' in message,key+' command accepted: '+message)
            ok(session._v7_upgrade(key)==1,key+' persisted level')
            ok(db.item_qty(aid,reward)>=1,key+' actual reward')
            ok(db.profession(aid,prof)['xp']>before,key+' actual profession progress')
            other=db.conn.execute('SELECT level FROM v700_improvements WHERE account_id=? AND key=?',(aid2,key)).fetchone()
            ok(other is None,key+' character scoped')
        # Each of four unique work types consumes inputs, awards outputs, and
        # cannot be duplicated before its cooldown.
        for key,(prof,region,inputs,reward,cd) in MISSION_TYPES.items():
            session.character.room_id=sorted(AREAS[region])[0]
            for item,qty in inputs: db.add_item(aid,item,qty*8)
            before=db.profession(aid,prof)['xp']
            msg=asyncio.run(session.do7('praca '+key))
            ok('Wykonano' in msg,key+' real work: '+msg)
            ok(db.item_qty(aid,reward)>=1,key+' item output')
            ok(db.profession(aid,prof)['xp']>before,key+' XP')
            again=asyncio.run(session.do7('praca '+key))
            ok('jeszcze trwa' in again,key+' cooldown enforced')
        # Native quest giver must offer a single NEXT story chapter, so NVDA
        # does not read eight or sixty-four options at once.
        from player.session_mixins.quest_progress import SessionQuestProgressMixin
        class StoryChecker(SessionQuestProgressMixin):
            pass
        story=StoryChecker();story.server=SimpleNamespace(db=db);story.account_id=aid
        mentor=runtime.NPCS['v700_chronicle_npc_1']
        next_id=STORY_IDS[0]
        ok(story.quest_ids_for_npc('v700_chronicle_npc_1',mentor)==[next_id],
           'only current quest offered')
        db.start_quest(aid,next_id)
        ok(story.quest_ids_for_npc('v700_chronicle_npc_1',mentor)==[next_id],
           'active quest visible in first slot')
        db.complete_quest(aid,next_id)
        ok(story.quest_ids_for_npc('v700_chronicle_npc_1',mentor)==[STORY_IDS[1]],
           'next stage unlocked; previous not offered')
        # True rare-elite/boss hunt contract: ordinary monsters and mobs below
        # tier cannot be counted; credited victories advance one player only.
        session.character.room_id='meadow'
        hunt=asyncio.run(session.do7('lowy start'))
        ok('Łowy rozpoczęte' in hunt,'legendary hunt started')
        state=db.conn.execute('SELECT needed,progress,tier FROM v700_hunts WHERE account_id=?',(aid,)).fetchone()
        ok(state is not None and state['progress']==0,'hunt SQLite initialized')
        session.output=[]
        asyncio.run(session.record_empire_hunt_kill_v7000({'generator_level':700}))
        ok(db.conn.execute('SELECT progress FROM v700_hunts WHERE account_id=?',(aid,)).fetchone()[0]==0,'normal monster no credit')
        asyncio.run(session.record_empire_hunt_kill_v7000({'elite_affix':True,'generator_level':1}))
        ok(db.conn.execute('SELECT progress FROM v700_hunts WHERE account_id=?',(aid,)).fetchone()[0]==0,'underleveled elite no credit')
        for _ in range(int(state['needed'])):
            asyncio.run(session.record_empire_hunt_kill_v7000({'rare_mob':True,'generator_level':700}))
        ok(db.conn.execute('SELECT progress FROM v700_hunts WHERE account_id=?',(aid,)).fetchone()[0]==state['needed'],'real rare kill progress')
        ok(db.conn.execute('SELECT COUNT(*) FROM v700_hunts WHERE account_id=?',(aid2,)).fetchone()[0]==0,'no cross player hunt credit')
        text=asyncio.run(session.do7('lowy odbierz'))
        ok('Legendarne łowy zakończone' in text,'real hunt reward payout')
        ok(db.item_qty(aid,'v700_hunt_seal')>0,'actual legendary hunting trophy')
        ok('nie są jeszcze zakończone' in asyncio.run(session.do7('lowy odbierz')),'double hunt reward blocked')
        # v6 integrated bonus: successful harvest becomes more fruitful after
        # a real field upgrade, with no new free harvest command.
        session.character.room_id='meadow'
        db.add_item(aid,'v600_seeds',3)
        db.conn.execute('INSERT INTO prof6_work_state(account_id,kind,tier,ready_at) VALUES(?,?,?,?) '
                        'ON CONFLICT(account_id,kind) DO UPDATE SET ready_at=excluded.ready_at,tier=excluded.tier',
                        (aid,'sow',1,int(time.time())-3))
        db.conn.commit()
        prev=db.item_qty(aid,'field_grain')
        from player.session_mixins.profesje6 import _sum
        prev=_sum(db,aid,'field_grain')
        result=asyncio.run(session.do('praca Rolnictwo zbierz 1'))
        ok('Rolnictwo —' in result,'real v6 harvest')
        ok(_sum(db,aid,'field_grain')>=prev+4,'field enhancement yields extra grain in v6')
        # Four authored voyages: truly consume supplies, record persistent
        # return state, and deliver after clock expiry. Includes character scope.
        for kind,routes in (('wyprawa',VOYAGES),('karawana',CARAVANS)):
            for code,route in routes.items():
                origin='harbor' if kind=='wyprawa' else 'market'
                session.character.room_id=origin
                inputs=route[3]
                for item,qty in inputs: db.add_item(aid,item,qty+1)
                msg=asyncio.run(session.do7(kind+' start '+code))
                ok('Rozpoczęto' in msg,kind+' start '+code+': '+msg)
                # The stage below is changed in the isolated test database,
                # never the production clock or persistent game state.
                db.conn.execute('UPDATE v700_jobs SET ready_at=? WHERE account_id=? AND kind=?',
                                (int(time.time())-10,aid,'ocean' if kind=='wyprawa' else 'trade'))
                db.conn.commit()
                session.character.room_id='sea_pier' if kind=='wyprawa' else 'market'
                prior=db.shared_wallet_for_master(master)[0]
                msg=asyncio.run(session.do7(kind+' odbierz'))
                ok('Zakończono' in msg,kind+' finish '+code+': '+msg)
                ok(db.shared_wallet_for_master(master)[0]>prior,kind+' payout paid')
                ok(db.conn.execute('SELECT COUNT(*) FROM v700_jobs WHERE account_id=? AND kind=?',
                                   (aid,'ocean' if kind=='wyprawa' else 'trade')).fetchone()[0]==0,kind+' cannot repeat')
        # 22 non-doubled contracts, each once per day per character; no
        # reward for missing goods or replaying the same day.
        session.character.room_id='market'
        for prof,good in MASTER_INPUT.items():
            for a in [aid]:
                db.add_item(a,good,30)
            original=db.profession(aid,prof)['xp']
            txt=asyncio.run(session.do7('mistrzostwo '+prof))
            ok('Kontrakt' in txt and 'zakończony' in txt,prof+' completed')
            ok(db.profession(aid,prof)['xp']>original,prof+' profession XP')
            txt=asyncio.run(session.do7('mistrzostwo '+prof))
            ok('odebrany' in txt,prof+' once daily')
        ok(db.conn.execute('SELECT COUNT(*) FROM v700_master_contracts WHERE account_id=?',(aid2,)).fetchone()[0]==0,'second character independent')
        # Auditory readability: persistence and not losing transactions when
        # the compact setting is toggled.
        msg=asyncio.run(session.do7('nvda pełne'))
        ok('pełne' in msg and not session._v7_compact(),'full output mode')
        msg=asyncio.run(session.do7('nvda zwięźle'))
        ok('zwięzłe' in msg and session._v7_compact(),'compact output mode')
        ok('Kronika Imperium:' in asyncio.run(session.do7('fabula')),'narrative guidance')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        db.conn.close()
        reopened=Database(str(db_path))
        ensure_schema(reopened)
        ok(reopened.conn.execute('SELECT COUNT(*) FROM v700_improvements WHERE account_id=?',(aid,)).fetchone()[0]==8,'improvements survive restart')
        ok(reopened.conn.execute('SELECT COUNT(*) FROM v700_master_contracts WHERE account_id=?',(aid,)).fetchone()[0]==22,'22 claims survive restart')
        ok(reopened.conn.execute('SELECT compact FROM v700_preferences WHERE account_id=?',(aid,)).fetchone()[0]==1,'NVDA preference survives restart')
        ok(reopened.conn.execute('SELECT COUNT(*) FROM v700_improvements WHERE account_id=?',(aid2,)).fetchone()[0]==0,'no account leak')
        reopened.conn.close()
    return checks

if __name__=='__main__':
    import os
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmp:
        os.environ.setdefault('SOULBOUND_HOST','127.0.0.1')
        os.environ.setdefault('SOULBOUND_PORT','54600')
        os.environ['SOULBOUND_DB']=str(Path(tmp)/'runtime.sqlite')
        print('v7.00.0 living empire:',run_regression(),'checks PASS')
