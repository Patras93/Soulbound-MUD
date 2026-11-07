# -*- coding: utf-8 -*-
"""V106: canonical bootstrap and real in-memory SQLite calendar integration.

All stages run in separate Python processes and :memory: SQLite. No player DB,
no production TCP, and no Windows PREDEPLOY claims.
"""
from __future__ import annotations
import ast
import asyncio
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def worker():
    import world.dynamic_content as d
    from systems.quest_calendar_v10400 import cadence_for_quest
    from storage import db_quests
    from systems.quest_visibility_v10600 import filter_quest_offers_v10600

    enabled = os.environ.get('SOULBOUND_V106_STAGING') == '1'
    if enabled != bool(d.V10600_STAGING_BUILD):
        raise AssertionError('flag not matched to actual bootstrap')
    flags = d.V10600_STAGING_BUILD
    from core.progression_600 import SOUL_MAX_TIER,SOUL_TIER_THRESHOLDS,SOUL_TRIAL_QUEST_IDS
    counts = [len(d.ROOMS),len(d.MOB_TEMPLATES),len(d.QUESTS),len(d.NPCS)]
    checks=0
    def ck(cond,why):
        nonlocal checks
        if not cond:raise AssertionError('v106 bootstrap: '+why)
        checks+=1
    ck('v10500_przelom_14' in d.ROOMS,'historic room')
    ck('v10500_przesmyk_story_01' in d.QUESTS,'historic v105 quest')
    ck(cadence_for_quest('older_hourly',{'repeatable':True,'repeat_calendar_v104':'day_utc'}) is None,'no calendar to old quests')
    if not enabled:
        ck(SOUL_MAX_TIER==3000,'v105 tier unchanged')
        ck(flags is None,'feature must be OFF by default')
        ck('v10600_przedmurze_01' not in d.ROOMS,'no new rooms in normal v105')
        ck('v10600_przedmurze_story_01' not in d.QUESTS,'no new quests in normal v105')
        ck('east' not in d.ROOMS['v10500_przelom_14']['exits'],'historic room exits unchanged')
        ck('soul_tier_3010_trial' not in d.QUESTS,'no premature trial in v105')
        print('RESULT_JSON='+json.dumps({'enabled':False,'counts':counts,'checks':checks}))
        return

    ck(SOUL_MAX_TIER==6000 and len(SOUL_TIER_THRESHOLDS)==6000,'actual v106 Tier cap and thresholds')
    ck(SOUL_TIER_THRESHOLDS[2999]==30000 and SOUL_TIER_THRESHOLDS[5999]==60000,'historical prefix and new max')
    ck(flags['new_quests']==2190 and flags['world_install_quests']==1890,'full additional quest count')
    ck(flags['regions']['rooms']==720 and flags['raids']['rooms']==30,'regions and raid rooms')
    ck(flags['regions']['npcs']==120 and flags['regions']['mobs']==360,'regional NPC and mob counts')
    ck(flags['raids']['bosses']==30 and flags['trials_catalogued']==300 and flags['trials']==0,'bosses and tier trial definitions')
    ck(flags['contracts']['contracts']==60,'calendar contracts')
    ck(d.ROOMS['v10500_przelom_14']['exits']['east']=='v10600_przedmurze_01','historic entrance connected')
    ck('v10600_przedmurze_story_01' in d.QUESTS,'first story active in real registry')
    ck('v10600_serce_story_15' in d.QUESTS,'last story active in real registry')
    ck('v10600_raid_35_quest_3' in d.QUESTS,'last raid active in real registry')
    ck('soul_tier_6000_trial' in d.QUESTS,'final trial authored in registry')
    ck(d.QUESTS[SOUL_TRIAL_QUEST_IDS[3010]]['target']=='v10600_przedmurze_boss_1','first real trial target')
    ck(d.QUESTS[SOUL_TRIAL_QUEST_IDS[6000]]['target']=='v10600_serce_boss_2','last real trial target')
    ck(all(30000 <= d.QUESTS[f'v10600_contract_{slug}_daily']['generator_level'] <= 60000 for slug in ('przedmurze','serce')),'contract levels')
    ck(len(flags['areas'])==30,'30 visible exp area rows')
    ck(any(z.get('id')=='v10600_serce' for z in d.EXP_AREAS),'last region in displayed area list')
    ck(all(room in d.ROOMS and mob in d.MOB_TEMPLATES for room,mob in d.MOB_SPAWNS if str(mob).startswith('v10600_')), 'all new physical spawns valid')
    ck(all(q['target'] in d.MOB_TEMPLATES for q in d.QUESTS.values() if q.get('kind')=='kill' and str(q.get('target')).startswith('v10600_')),'all new quest kill targets valid')

    # The same concrete quest-catalogue data drive production's canonical
    # v104/v106 calendar and DatabaseQuestMixin, with a disposable SQLite db.
    daily='v10600_contract_przedmurze_daily'
    weekly='v10600_contract_przedmurze_weekly'
    date=lambda y,m,day,h=0,mi=0: int(datetime(y,m,day,h,mi,tzinfo=timezone.utc).timestamp())
    friday=date(2026,10,30,23,50)
    saturday=date(2026,10,31)
    monday=date(2026,11,2)
    for qid,cadence in ((daily,'day_utc'),(weekly,'week_utc')):
        ck(cadence_for_quest(qid,d.QUESTS[qid])==cadence,'real authored calendar '+qid)
    ck(cadence_for_quest('v10600_contract_fake_daily',{'repeatable':False,'repeat_calendar_v104':'day_utc'}) is None,'nonrepeatable forged quest')
    ck(cadence_for_quest('v10600_contract_fake_daily',{'repeatable':True,'repeat_calendar_v104':'bad'}) is None,'bad calendar value')
    con=sqlite3.connect(':memory:')
    con.row_factory=sqlite3.Row
    con.execute('CREATE TABLE quests(account_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,completed_at INTEGER,completion_count INTEGER)')
    con.executemany('INSERT INTO quests VALUES (1,?,"completed",8,?,1)',[(daily,friday),(weekly,friday)])
    class D(db_quests.DatabaseQuestMixin):
        conn=con
    old=db_quests.QUESTS
    db_quests.QUESTS=d.QUESTS
    try:
        with patch.object(db_quests.time,'time',return_value=friday):
            ck(D().repeat_quest_seconds_remaining(1,daily,86400)==600,'real db midnight wait')
            ck(D().repeat_quest_seconds_remaining(1,weekly,7*86400)==monday-friday,'real db Monday wait')
        with patch.object(db_quests.time,'time',return_value=saturday):
            ck(D().repeat_quest_seconds_remaining(1,daily,86400)==0,'daily resets at UTC midnight')
            ck(D().repeat_quest_seconds_remaining(1,weekly,7*86400)>0,'weekly still blocked on Saturday')
        with patch.object(db_quests.time,'time',return_value=monday):
            ck(D().repeat_quest_seconds_remaining(1,weekly,7*86400)==0,'weekly resets at Monday UTC')
        ck(con.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite memory healthy')
    finally:
        db_quests.QUESTS=old
        con.close()

    # Exact v106 NPC offer method from source (not a rewritten mock).
    fn=ROOT/'player/session_mixins/quest_progress.py'
    tree=ast.parse(fn.read_text(encoding='utf8'))
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='SessionQuestProgressMixin')
    method=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='quest_ids_for_npc')
    method.decorator_list=[]
    context={'QUESTS':d.QUESTS}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(fn),'exec'),context)
    class Rows:
        def __init__(self):self.rows={}
        def quest(self, account, qid):return self.rows.get(qid)
    rows=Rows()
    class Session:
        server=SimpleNamespace(db=rows)
        account_id=1
        character=SimpleNamespace(soul_tier=1)
        def normalize_description_query(self,value):return str(value).casefold()
    Session.quest_ids_for_npc=context['quest_ids_for_npc']
    s=Session()
    npc_id='v10600_przedmurze_npc_4'
    npc=d.NPCS[npc_id]
    available=s.quest_ids_for_npc(npc_id,npc)
    ck(len(available)>=2,'new NPC offers multiple quests')
    ck(daily in available and weekly in available,'real v106 contracts on NPC')
    once=next(q for q in available if q not in (daily,weekly))
    rows.rows[once]={'status':'completed','completion_count':1}
    rows.rows[daily]={'status':'completed','completion_count':1}
    actual=s.quest_ids_for_npc(npc_id,npc)
    ck(once not in actual and daily in actual,'completed one-time hidden, repeatable remains')
    ck(weekly in actual,'weekly still in offer')
    ck(len(actual)==len(available)-1,'NPC numbering contains no gap')

    # Run actual v106 NVDA pagination / numbered choice methods from the
    # production source, not a separate simplified implementation.
    from validation.v10600_one_time_quest_offers import _method
    from systems.quest_visibility_v10600 import filter_quest_offers_v10600
    import re
    display_scope={'QUESTS':d.QUESTS,'NPCS':d.NPCS,'re':re,
         'filter_quest_offers_v10600':filter_quest_offers_v10600,
         'currency_reading_text':lambda val,*args:f'{val} złota',
         'v0190_quest_currency_reward':lambda quest:quest.get('reward_gold',0),
         'QUEST_REPEAT_COOLDOWN_SECONDS':3600}
    class ListSession:
        account_id=1
        character=SimpleNamespace(room_id='v10600_przedmurze_08',soul_tier=3000)
        server=SimpleNamespace(db=rows)
        quest_list_context=None
        def __init__(self):self.messages=[]
        async def send(self,message):self.messages.append(message)
        def quest_offer_state(self,qid):return 'dostępne'
    ListSession.quest_ids_for_npc=context['quest_ids_for_npc']
    ListSession.show_npc_quest_offers=_method('quest_offers.py','show_npc_quest_offers',display_scope)
    ListSession.quest_from_context=_method('quest_offers.py','quest_from_context',display_scope)
    ui=ListSession()
    npc_id='v10600_przedmurze_npc_2'
    qids=ui.quest_ids_for_npc(npc_id,d.NPCS[npc_id])
    ck(len(qids)>10,'new regional NPC has multiple NVDA pages')
    first=qids[0]
    rows.rows[first]={'status':'completed','completion_count':1}
    page1=asyncio.run(ui.show_npc_quest_offers(npc_id,d.NPCS[npc_id]))
    ck(len(page1)==10 and first not in page1,'first v106 page filters one-time completed')
    ck('Strona 1' in ui.messages[0],'v106 NVDA page announcement')
    ui.messages.clear()
    page2=asyncio.run(ui.show_npc_quest_offers(npc_id,d.NPCS[npc_id],page_number=2))
    ck(bool(page2) and 'Strona 2' in ui.messages[0],'second v106 page works')
    resolved,error=ui.quest_from_context('1')
    ck(resolved==page2[0] and error is None,'v106 numeric accept matches visible second page')
    ck(ui.quest_list_context['quest_ids']==page2,'v106 page context has only visible items')

    print('RESULT_JSON='+json.dumps({'enabled':True,'counts':counts,'checks':checks,
                                    'v106_new_quests':flags['new_quests']}))


def run():
    observations=[]
    for enabled in (False,True):
        env=dict(os.environ)
        env.pop('SOULBOUND_V106_STAGING',None)
        if enabled:env['SOULBOUND_V106_STAGING']='1'
        env['PYTHONDONTWRITEBYTECODE']='1'
        env['PYTHONPATH']=str(ROOT)
        completed=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'worker'],
                                 cwd=str(ROOT),env=env,text=True,capture_output=True,timeout=100)
        if completed.returncode:
            raise AssertionError('v106 worker failed '+str(enabled)+'\n'+completed.stdout+'\n'+completed.stderr)
        lines=[l for l in completed.stdout.splitlines() if l.startswith('RESULT_JSON=')]
        if len(lines)!=1:raise AssertionError('missing single result from v106 worker')
        data=json.loads(lines[0].split('=',1)[1]);observations.append(data)
        if data['enabled']!=enabled:raise AssertionError('worker wrong flag')
    old,new=observations
    if [b-a for a,b in zip(old['counts'],new['counts'])] != [750,390,2190,120]:
        raise AssertionError('v106 bootstrap catalogues differ from expected additive delta')
    return {'checks':old['checks']+new['checks']+4,
            'v105_unchanged_without_flag':True,'v106_rooms':750,
            'v106_mobs':390,'v106_quests':2190,'v106_npcs':120,
            'native_sqlite_calendar':True,'one_time_quest_filter':True}


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='worker':
        worker()
    else:
        print('V106 BOOTSTRAP REAL REGISTRIES + SQLITE: '+json.dumps(run(),ensure_ascii=False)+' PASS',flush=True)
