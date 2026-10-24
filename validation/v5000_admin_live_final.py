# -*- coding: utf-8 -*-
"""v50 live command routing; safe repair transactions, DAG cycles, NVDA text."""
from __future__ import annotations
import asyncio, copy, random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from data.quests import QUESTS
from systems.admin_live_final_v5000 import (
    _fixable,_fix_rows,_fix_list,_repair_plan,_repair_apply,_repair_undo,
    _graph_report,_coverage,_scenario,_COUNT_KINDS,HELP7)
from systems.admin_live_expansion_v4800 import KINDS

async def suite():
    owner=Fake(); db=owner.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    owner.server.live_content_v1204=service
    guest=Fake(False,db);guest.server.live_content_v1204=service
    successes=0
    def ok(value,name):
        nonlocal successes
        assert value,name
        successes+=1
    async def cmd(command,session=owner):
        await session.admin_command('live '+command)
        return session.messages[-1]
    original_draft=copy.deepcopy(service.draft)
    original_active=copy.deepcopy(service.active)
    original_sql=list(db.conn.execute('select * from quests'))
    original_rng=random.getstate()
    ok(len(KINDS)==18,'18 quest kinds')
    ok(len(QUESTS)>=90,'canonical static quests')
    ok('ADMIN LIVE POMOC 7/7' in await cmd('pomoc 7'),'NVDA help route')
    ok('KOREKTA LISTA' in await cmd('questy korekta lista'),'fixable list')
    ok('QUEST CYKLE' in await cmd('questy cykle'),'global dependencies')
    ok('QUEST POKRYCIE' in await cmd('questy pokrycie'),'coverage 18')
    for kind in KINDS:
        ok(kind in _coverage(service),'coverage includes '+kind)
    ok(len(_COUNT_KINDS)==9,'nine positive quantity kinds')
    for kind in _COUNT_KINDS:
        patch,alerts=_fixable('lab',{'kind':kind,'needed':0,'target':'*'}, {'lab':{'kind':kind}})
        ok(patch=={'needed':1},'repair count kind '+kind)
    no_changes=[
        {'kind':'kill','needed':'NaN'},
        {'kind':'kill','needed':None},
        {'kind':'kill','reward_gold':-1,'target':'*'},
        {'kind':'kill','needed':2,'target':'missing_boss'},
        {'kind':'deliver_npc','target_npc':'missing_person'},
        {'kind':'kill','needed':True},
        {'kind':'kill','needed':1},
    ]
    for record in no_changes:
        patch,alerts=_fixable('lab',record,{'lab':record})
        ok(not patch,'refuse invented repair')
    for val in (-1,-100):
        patch,alerts=_fixable('lab',{'kind':'world_event','repeat_cooldown':val}, {'lab':{'kind':'world_event'}})
        ok(patch=={'repeat_cooldown':0},'negative cooldown correction')
    for invalid in ('questy korekta lista 0','questy korekta plan missing',
                    'questy korekta zastosuj','questy korekta cofnij POTWIERDZAM',
                    'questy cykle 999999', 'arena scenariusze 0'):
        ok('ADMIN LIVE:' in await cmd(invalid),'bad input '+invalid)
    for raw in ('pomoc 7','questy korekta lista','questy korekta plan bandit_patrol',
                'questy korekta zastosuj POTWIERDZAM','questy cykle',
                'questy pokrycie', 'arena scenariusze 3'):
        ok('Nieznana' in await cmd(raw,guest),'owner guard '+raw)
    ok(service.draft==original_draft,'invalid ops do not mutate DRAFT')
    # Build a deliberately broken-but-correctable DRAFT record in an isolated
    # clone of LiveContentV1204; source world/active remain immutable.
    service.draft['quest_edits']['bandit_patrol']={'needed':0}
    old=copy.deepcopy(service.draft)
    ok('bandit_patrol' in _fix_list(service),'candidate listed')
    ok('0 -> 1' in await cmd('questy korekta plan bandit_patrol'),'exact diff')
    ok(service.draft==old,'plan read only')
    ok('Brak planu' not in await cmd('questy korekta zastosuj POTWIERDZAM'),'commit valid')
    ok(service.draft['quest_edits']['bandit_patrol']['needed']==1,'DRAFT corrected')
    ok(service.active==original_active,'active not published')
    ok('COFNIETA' in await cmd('questy korekta cofnij POTWIERDZAM'),'undo command')
    ok(service.draft==old,'exact undo')
    ok('anulowany' in await cmd('questy korekta anuluj'),'cancel')
    # Reject stale changes between plan and commit, including changed active.
    ok('KOREKTA PLAN' in await cmd('questy korekta plan bandit_patrol'),'replan')
    service.draft['quest_edits']['bandit_patrol']['needed']=-5
    stale=copy.deepcopy(service.draft)
    ok('zmienione' in await cmd('questy korekta zastosuj POTWIERDZAM'),'stale-draft denial')
    ok(service.draft==stale,'stale denial unchanged')
    service.draft=copy.deepcopy(old)
    ok('KOREKTA PLAN' in await cmd('questy korekta plan bandit_patrol'),'plan for active test')
    service.active['quest_edits']['bandit_patrol']={'reward_gold':12}
    ok('zmienione' in await cmd('questy korekta zastosuj POTWIERDZAM'),'stale-active denial')
    service.active=copy.deepcopy(original_active)
    service.draft=copy.deepcopy(old)
    ok('KOREKTA PLAN' in await cmd('questy korekta plan bandit_patrol'),'plan for undo conflict')
    ok('KOREKTA DRAFT' in await cmd('questy korekta zastosuj POTWIERDZAM'),'commit for undo conflict')
    service.draft['quest_edits']['bandit_patrol']['reward_silver']=99
    conflict=copy.deepcopy(service.draft)
    ok('odmowa' in (await cmd('questy korekta cofnij POTWIERDZAM')).lower(),'undo denies concurrent edits')
    ok(service.draft==conflict,'preserve unrelated edit')
    # Multiple IDs; a missing ID must reject atomically.
    service.draft=copy.deepcopy(old)
    before=copy.deepcopy(service.draft)
    msg=await cmd('questy korekta plan bandit_patrol missing')
    ok('Nie znaleziono ID' in msg,'reject unknown batch ID')
    ok(service.draft==before,'batch atomic fail')
    too_many=' '.join('foo'+str(n) for n in range(9))
    ok('od 1 do 8' in await cmd('questy korekta plan '+too_many),'batch upper limit')
    ok('8 roznych' in await cmd('questy korekta plan bandit_patrol bandit_patrol'),'batch duplicate')
    # Test global DAG cycles and dangling identifiers without publishing them.
    service.draft['quests']['aaa_test50']={'kind':'talk_npc','name':'A','requires_quest':'bbb_test50'}
    service.draft['quests']['bbb_test50']={'kind':'talk_npc','name':'B','requires_quest':'ccc_test50'}
    service.draft['quests']['ccc_test50']={'kind':'talk_npc','name':'C','requires_quest':'aaa_test50'}
    service.draft['quests']['broken_test50']={'kind':'talk_npc','name':'D','requires_quest':'missing_test50'}
    graph=_graph_report(service)
    ok('cykle 1' in graph,'cycle counted')
    ok('aaa_test50, bbb_test50, ccc_test50' in graph,'SCC exact')
    ok('brakujace ID 1' in graph,'missing count')
    ok('missing_test50' in graph,'missing ID reported')
    ok('QUEST CYKLE' in await cmd('questy cykle'),'cycle routed')
    # v44+ LAB matches isolated UI, does not alter world RNG or player progress.
    service.draft=copy.deepcopy(original_draft)
    ok('ARENA11 START' in await cmd('arena start black_rabite 1000000 20000'),'lab start')
    ok('dodano' in await cmd('arena druzyna gotowy Wojownik 20 1000 5000 150 POTWIERDZAM'),'lab party')
    start=copy.deepcopy(owner.guardian7_lab)
    digest=lambda x:(x['boss'].hp,x['hero_hp'],x['round'],x['total_dealt'],x['total_taken'],
                     x.get('_guardian10_rng'),copy.deepcopy(x.get('_adminlive46_party')))
    snapshot=digest(start)
    for turns in (1,4,12):
        result=await cmd('arena scenariusze '+str(turns))
        ok('ARENA SCENARIUSZE' in result,'three strategies')
        ok(all(x in result for x in ('atak:','obrona:','druzyna:')),'all compared')
        ok(digest(owner.guardian7_lab)==snapshot,'arena not mutated')
        ok(random.getstate()==original_rng,'global RNG not changed')
    ok(original_sql==list(db.conn.execute('select * from quests')),'SQLite quest table immutable')
    ok(original_active==service.active,'final active unchanged')
    ok(original_draft==service.draft,'final draft unchanged')
    ok('QUEST BLEDY' in await cmd('questy bledy'),'v49 command')
    ok('QUEST SZUKAJ' in await cmd('questy szukaj bandit'),'v46 command')
    ok('QUEST EXP' in await cmd('questy exp bandit_patrol'),'v47 common/individual EXP')
    return successes

def run():return asyncio.run(suite())
if __name__=='__main__': print('V50 ADMIN LIVE FINAL:',run(),'checks PASS')
