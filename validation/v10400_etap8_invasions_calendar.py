# -*- coding: utf-8 -*-
"""Isolated v104 stage 8 regression. No sockets, no production DB or game state."""
from __future__ import annotations
from datetime import datetime, timezone
from types import SimpleNamespace
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch
from systems.quest_calendar_v10400 import remaining_seconds, cadence_for_quest
from systems import world_invasions_v10400 as inv


def _dt(year,month,day,hour=0,minute=0):
    return int(datetime(year,month,day,hour,minute,tzinfo=timezone.utc).timestamp())


def run():
    checks = 0
    def ok(condition, message):
        nonlocal checks
        if not condition:
            raise AssertionError(message)
        checks+=1

    friday = _dt(2026,10,30,23,50)
    saturday = _dt(2026,10,31)
    monday = _dt(2026,11,2)
    ok(remaining_seconds(friday,'day_utc',friday) == 600, 'daily at next midnight')
    ok(remaining_seconds(friday,'day_utc',saturday) == 0, 'daily renews next day')
    ok(remaining_seconds(friday,'week_utc',friday) == monday-friday,'weekly to Monday')
    ok(remaining_seconds(friday,'week_utc',monday) == 0,'weekly renews Monday')
    ok(remaining_seconds(friday,'week_utc',friday-3600) > monday-friday,'clock rollback fail closed')
    ok(remaining_seconds(0,'day_utc',friday)==0,'not completed')
    ok(cadence_for_quest('v10400_contract_sztorm_daily',dict(repeatable=True,repeat_calendar_v104='day_utc'))=='day_utc','calendar authorized')
    ok(cadence_for_quest('older_quest',dict(repeatable=True,repeat_calendar_v104='day_utc')) is None,'legacy stays legacy')
    try:
        remaining_seconds(friday,'every_minute',friday)
    except ValueError:
        checks+=1
    else:
        raise AssertionError('invalid cadence accepted')

    with tempfile.TemporaryDirectory() as t:
        f=Path(t)/'invasions-temp.sqlite3'
        c=sqlite3.connect(f)
        inv.create_schema(c)
        # One slot, deterministic three fronts. Test only *authentic* mob states.
        now=_dt(2026,10,30,13)
        rotation=inv.rotation(now)
        ok(len(rotation['fronts'])==3 and len(set(rotation['fronts']))==3,'distinct fronts')
        ok(inv.status(c,now)['counts']=={slug:0 for slug in rotation['fronts']},'initial empty')
        final_slug=rotation['fronts'][-1]
        def mob(slug,kind,instance,respawn,room=None):
            return SimpleNamespace(alive=False, template_id=f'v10400_{slug}_{kind}',
                                   room_id=room or f'v10400_{slug}_11',
                                   key=f'mob-state-{instance}',respawn_at=respawn)
        # Boss cannot prematurely complete the event.
        premob=mob(final_slug,'boss_2','boss',float(now)+200)
        ok(inv.record_real_defeat(c,premob,{'boss':True},now=now) is None,'no early boss credit')
        ok(not inv.status(c,now)['completed'],'early boss no finish')
        # Wrong room, not-dead mob and summoned adds must not earn global credit.
        first=rotation['fronts'][0]
        wrong=mob(first,'mob_3','wrong',now+300,'v10400_other_01')
        ok(inv.record_real_defeat(c,wrong,{'name':'sample'},now=now) is None,'wrong room')
        living=mob(first,'mob_3','living',now+300);living.alive=True
        ok(inv.record_real_defeat(c,living,{'name':'sample'},now=now) is None,'living not credited')
        summon=mob(first,'mob_3','summon',now+300);summon.monster_ai_summoned_v1160=True
        ok(inv.record_real_defeat(c,summon,{'name':'sample'},now=now) is None,'summon not credited')
        for slug in rotation['fronts']:
            for n in range(inv.REQUIRED_PER_FRONT):
                enemy=mob(slug,'mob_3',f'{slug}_{n}',now+100+n/1000)
                result=inv.record_real_defeat(c,enemy,{'name':'real mob'},now=now)
                ok(result==('front',slug,n+1),f'real front kill: {slug} {n+1}')
                ok(inv.record_real_defeat(c,enemy,{'name':'real mob'},now=now) is None,'same death deduplicated')
            ok(inv.status(c,now)['counts'][slug]==inv.REQUIRED_PER_FRONT,'front complete')
        ok(not inv.status(c,now)['completed'],'fronts not final')
        boss=mob(final_slug,'boss_2','actual-final',now+999)
        ok(inv.record_real_defeat(c,boss,{'boss':True},now=now)==('final',final_slug,inv.REQUIRED_PER_FRONT),'final credited')
        ok(inv.status(c,now)['completed'],'final recorded')
        ok(inv.record_real_defeat(c,boss,{'boss':True},now=now) is None,'final deduplicated')
        # New fight of the same respawned creature shouldn't be confused with
        # earlier death; however completed invasion has no extra progression.
        extra=mob(first,'mob_3','other',now+1111)
        ok(inv.record_real_defeat(c,extra,{'name':'real'},now=now) is None,'no post-completion points')
        c.close()
        c=sqlite3.connect(f)
        ok(inv.status(c,now)['completed'],'restart persistent completion')
        new_time=rotation['expires_at']+2
        ok(not inv.status(c,new_time)['completed'],'new slot not completed')
        ok(inv.status(c,new_time)['counts']=={slug:0 for slug in inv.rotation(new_time)['fronts']},'new rotation empty')
        ok(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','db intact')
        ok('INWAZJA V104' in inv.status_text(c,now),'NVDA short status')
        c.close()

    # Verify calendar is used by *native* DB quest method (not only helper).
    import storage.db_quests as dbq
    qid='v10400_contract_sztorm_daily'
    original_quests = dbq.QUESTS
    c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
    c.execute('CREATE TABLE quests(account_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,completed_at INTEGER,completion_count INTEGER)')
    c.execute("INSERT INTO quests VALUES (1,?,'completed',8,?,1)",(qid,friday))
    class D(dbq.DatabaseQuestMixin):
        conn=c
    try:
        dbq.QUESTS={qid:{'repeatable':True,'repeat_calendar_v104':'day_utc'},'old':{'repeatable':True}}
        with patch.object(dbq.time,'time',return_value=friday):
            ok(D().repeat_quest_seconds_remaining(1,qid,86400)==600,'native daily exact')
        with patch.object(dbq.time,'time',return_value=saturday):
            ok(D().repeat_quest_seconds_remaining(1,qid,86400)==0,'native daily rollover')
        c.execute("INSERT INTO quests VALUES (1,'old','completed',8,?,1)",(friday,))
        with patch.object(dbq.time,'time',return_value=friday+60):
            ok(D().repeat_quest_seconds_remaining(1,'old',3600)==3540,'old untouched')
    finally:
        dbq.QUESTS=original_quests
        c.close()
    return checks

if __name__=='__main__':
    print(f'V104 STAGE8 {run()} PASS')
