# -*- coding: utf-8 -*-
"""v51 owner-only in-memory multi-field OLC transactions, 22-class lab matrix."""
from __future__ import annotations
import asyncio,copy,random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_complete_v5100 import _class_matrix,_planned_edits
from core.classes_skills import CLASS_SKILLS
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

async def suite():
    owner=Fake();db=owner.server.db
    svc=LiveContentV1204(SimpleNamespace(conn=db.conn))
    owner.server.live_content_v1204=svc
    guest=Fake(False,db);guest.server.live_content_v1204=svc
    original_draft=copy.deepcopy(svc.draft)
    original_active=copy.deepcopy(svc.active)
    original_sql=list(db.conn.execute('select * from quests'))
    rnd=random.getstate(); checks=0
    def ok(cond,reason):
        nonlocal checks
        assert cond,reason
        checks+=1
    async def cmd(txt,who=owner):
        await who.admin_command('live '+txt)
        return who.messages[-1]
    ok(len(CLASS_SKILLS)==22,'22 classes')
    ok('POMOC 8/8' in await cmd('pomoc 8'),'single admin live help')
    ok('EDYCJA STATUS' in await cmd('questy edycja status'),'edit status')
    sample='questy edycja plan bandit_patrol | reward_stat_xp | 88 ; bandit_patrol | reward_stat_strength | 44'
    msg=await cmd(sample)
    ok('QUEST EDYCJA PLAN' in msg,msg)
    ok('olc_reward_stat_xp' in msg,'common EXP alias')
    ok('olc_reward_stat_strength' in msg,'individual EXP alias')
    ok(svc.draft==original_draft,'planning not persisted')
    ok(svc.active==original_active,'active untouched')
    msg=await cmd('questy edycja zatwierdz POTWIERDZAM')
    ok('QUEST EDYCJA DRAFT' in msg,msg)
    ok(svc.draft['quest_edits']['bandit_patrol']['olc_reward_stat_xp']==88,'common in draft')
    ok(svc.draft['quest_edits']['bandit_patrol']['olc_reward_stat_strength']==44,'strength in draft')
    ok(svc.active==original_active,'active still unchanged')
    ok('COFNIETA' in await cmd('questy edycja cofnij POTWIERDZAM'),'undo')
    ok(svc.draft==original_draft,'undo exact')
    # A transaction that touches linked fields atomically.
    msg=await cmd('questy edycja plan bandit_patrol | reward_gold | 100 ; bandit_patrol | reward_stat_charisma | 11')
    ok('QUEST EDYCJA PLAN' in msg,msg)
    ok('DRAFT' in await cmd('questy edycja zatwierdz POTWIERDZAM'),'two linked edits')
    ok(svc.draft['quest_edits']['bandit_patrol']['reward_gold']==100,'linked 2 fields')
    ok('COFNIETA' in await cmd('questy edycja cofnij POTWIERDZAM'),'two edits undo')
    # Unchanged draft on failure, invalid IDs, duplicate patch, invalid values.
    invalid=[
        'questy edycja plan bandit_patrol | needed | 0',
        'questy edycja plan bandit_patrol | reward_gold | -1',
        'questy edycja plan bandit_patrol | reward_stat_xp | 1 ; bandit_patrol | olc_reward_stat_xp | 2',
        'questy edycja plan missing_quest | reward_gold | 1',
        'questy edycja plan bandit_patrol | zz_unknown | 1',
        'questy edycja plan bandit_patrol | requires_quest | missing_quest',
        'questy edycja plan bandit_patrol | reward_gold | xyz',
        'questy edycja plan bandit_patrol | target | missing_mob',
        'questy edycja plan bandit_patrol | reward_items | {"not_an_item":1}',
        'questy edycja plan bandit_patrol | reward_stat_xp | 1 ; ;',
        'questy edycja plan bandit_patrol | reward_stat_xp',
    ]
    for query in invalid:
        before=copy.deepcopy(svc.draft)
        answer=await cmd(query)
        ok('ADMIN LIVE:' in answer,'bad input '+query+' '+answer)
        ok(svc.draft==before,'bad request must not alter draft')
    # Stale plan MUST not overwrite another editor or deployed Active.
    ok('EDYCJA PLAN' in await cmd(sample),'replan')
    svc.draft['quest_edits']['bandit_patrol']={'reward_silver':7}
    changed=copy.deepcopy(svc.draft)
    ok('zmienily' in await cmd('questy edycja zatwierdz POTWIERDZAM'),'stale draft rejection')
    ok(svc.draft==changed,'stale draft unchanged')
    svc.draft=copy.deepcopy(original_draft)
    ok('EDYCJA PLAN' in await cmd(sample),'replan active')
    svc.active['quest_edits']['bandit_patrol']={'reward_gold':8}
    ok('zmienily' in await cmd('questy edycja zatwierdz POTWIERDZAM'),'stale active rejection')
    svc.active=copy.deepcopy(original_active)
    ok('EDYCJA PLAN' in await cmd(sample),'replan for undo conflicts')
    ok('DRAFT' in await cmd('questy edycja zatwierdz POTWIERDZAM'),'commit for undo conflict')
    svc.draft['quest_edits']['bandit_patrol']['reward_gold']=8
    changed=copy.deepcopy(svc.draft)
    ok('Nie cofne cudzych zmian' in await cmd('questy edycja cofnij POTWIERDZAM'),'undo conflict denial')
    ok(svc.draft==changed,'preserve later edit')
    svc.draft=copy.deepcopy(original_draft)
    for text in ('pomoc 8','questy edycja status',sample,
                 'questy edycja zatwierdz POTWIERDZAM',
                 'questy edycja cofnij POTWIERDZAM',
                 'arena klasy test 1', 'arena bossy test 1'):
        ok('Nieznana' in await cmd(text,guest),'permission '+text)
    ok(svc.draft==original_draft,'guest changes none')
    ok('ARENA11 START' in await cmd('arena start black_rabite 1000000 20000'),'boss lab')
    before=copy.deepcopy(owner.guardian7_lab)
    def digest(s):return (s['boss'].hp,s['hero_hp'],s['round'],s['total_dealt'],s['total_taken'],s['_guardian10_rng'])
    for page in ('1','2','3'):
        msg=await cmd('arena klasy test 2 '+page)
        ok('ARENA TEST KLAS: 22 klas' in msg,'22 classes report '+page+' '+msg)
        ok('MODELEM' in msg,'honest label '+page)
        ok(digest(owner.guardian7_lab)==digest(before),'lab unchanged '+page)
        ok(random.getstate()==rnd,'production PRNG unchanged '+page)
    ok(len(UOSS_SUPERBOSS_ENCOUNTERS_V11134)==21,'21 UOSS unique bosses')
    for page in ('1','2','3'):
        msg=await cmd('arena bossy test 3 '+page)
        ok('ARENA TEST BOSSY UOSS: 21' in msg,'21 boss source report '+page)
        ok('model odmowil' not in msg,'source test completed '+page)
        ok(digest(owner.guardian7_lab)==digest(before),'boss matrix leaves arena unchanged '+page)
        ok(random.getstate()==rnd,'boss matrix RNG isolation '+page)
    for turns in ('0','4','abc'):
        ok('ADMIN LIVE:' in await cmd('arena bossy test '+turns),'boss bad input')
    ok('ADMIN LIVE:' in await cmd('arena bossy test 2 4'),'boss invalid page')
    for turns in ('0','4','abc'):
        ok('ADMIN LIVE:' in await cmd('arena klasy test '+turns),'bad turns')
    ok('ADMIN LIVE:' in await cmd('arena klasy test 1 4'),'bad page')
    ok('QUEST BLEDY' in await cmd('questy bledy'),'older v49')
    ok('QUEST CYKLE' in await cmd('questy cykle'),'older v50')
    ok('QUEST EXP' in await cmd('questy exp bandit_patrol'),'older v47')
    ok('ARENA SCENARIUSZE' in await cmd('arena scenariusze 1'),'older v50 arena')
    ok(svc.active==original_active,'no active mut')
    ok(svc.draft==original_draft,'no draft final')
    ok(list(db.conn.execute('select * from quests'))==original_sql,'no quest SQL mut')
    ok(random.getstate()==rnd,'no RNG mut')
    return checks

def run():return asyncio.run(suite())
if __name__=='__main__':print('V51 ADMIN LIVE COMPLETE:',run(),'checks PASS')
