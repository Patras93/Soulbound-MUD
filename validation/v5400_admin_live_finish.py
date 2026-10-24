# -*- coding: utf-8 -*-
"""v54 owner and in-memory DRAFT safety tests; no production DB mutation."""
import asyncio
import copy
import random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_finish_v5400 import (
    HELP,quest_type_review,quest_fix_advice,arena_suite,equipment_coverage,
    progression_safety,final_readiness,dispatch_v54)
from systems.admin_live_integrity_v4900 import _effective
from systems.admin_live_expansion_v4800 import KINDS
from core import live_level_caps_v5200 as caps
from core.classes_skills import CLASS_SKILLS
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

async def suite():
    owner=Fake()
    db=owner.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    owner.server.live_content_v1204=service
    guest=Fake(False,db)
    guest.server.live_content_v1204=service
    before_draft=copy.deepcopy(service.draft)
    before_active=copy.deepcopy(service.active)
    before_quests=list(db.conn.execute('select * from quests'))
    original_rng=random.getstate()
    checks=0
    def check(flag,why=''):
        nonlocal checks
        assert flag,why
        checks+=1
    async def run(command,who=owner):
        await who.admin_command('live '+command)
        return who.messages[-1]
    check(len(KINDS)==18)
    check(len(CLASS_SKILLS)==22)
    check(len(UOSS_SUPERBOSS_ENCOUNTERS_V11134)==21)
    check('POMOC 9' in HELP)
    check('POMOC 9' in await run('pomoc 9'))
    check('QUESTY PRZEGLAD' in await run('questy przeglad'))
    check('strona 1/' in await run('questy przeglad 1'))
    check('strona 2/' in await run('questy przeglad 2'))
    check('strona 3/' in await run('questy przeglad 3'))
    for page in (1,2,3):
        result=quest_type_review(service,str(page))
        check('bledy' in result,'quest audit '+str(page))
        check('pewne poprawki' in result,'fix catalog '+str(page))
    check('ADMIN LIVE:' in await run('questy przeglad 0'))
    check('ADMIN LIVE:' in await run('questy przeglad 999'))
    check('ADMIN LIVE:' in await run('questy przeglad abc'))
    check('QUEST NAPRAW' in await run('questy napraw bandit_patrol'))
    check('tylko w DRAFT' in await run('questy napraw bandit_patrol') or 'Zapis tylko w DRAFT' in await run('questy napraw bandit_patrol'))
    for ident in ('nonexistent_quest','@'*101):
        check('ADMIN LIVE:' in await run('questy napraw '+ident),'unknown id '+ident)
    check('EQ POKRYCIE' in await run('eq pokrycie'))
    check('5 zrodel' in equipment_coverage())
    check('bledy 0' in equipment_coverage())
    check('LIMITY KONTROLA' in await run('limity kontrola 801'))
    check('int64' in await run('limity kontrola 99999'))
    for wrong in ('0','-1','100001','x','10000000000000'):
        check('ADMIN LIVE:' in await run('limity kontrola '+wrong),wrong)
    check('GOTOWOSC FINALNA' in await run('gotowosc finalna'))
    check('60/60 PLUS' in final_readiness())
    check('UOSS 1:1' in final_readiness())
    check('ADMIN LIVE:' in await run('arena przeglad 0'))
    check('ADMIN LIVE:' in await run('arena przeglad 7'))
    check('ADMIN LIVE:' in await run('arena przeglad x'))
    check('ADMIN LIVE:' in await run('arena przeglad 1 4'))
    check('Nieznana komenda' in await run('pomoc 9',guest))
    for request in ('questy przeglad','questy napraw bandit_patrol','arena przeglad','eq pokrycie','limity kontrola 801','gotowosc finalna'):
        answer=await run(request,guest)
        check('Nieznana komenda' in answer,'guest '+request)
    # Test all three boss pages; no real arena needed.
    for p in (4,5,6):
        answer=await run('arena przeglad '+str(p)+' 1')
        check('ARENA PRZEGLAD' in answer and 'BOSSY' in answer,'boss '+str(p)+' '+answer[:200])
    # Test class pages after creating a private arena.
    answer=await run('arena start black_rabite 1000000 20000')
    check('ARENA' in answer,answer)
    check(getattr(owner,'guardian7_lab',None) is not None,'arena created')
    snapshot=copy.deepcopy(owner.guardian7_lab)
    for p in (1,2,3):
        answer=await run('arena przeglad '+str(p)+' 1')
        check('ARENA PRZEGLAD klasy' in answer,'classes '+str(p)+' '+answer[:140])
        check(owner.guardian7_lab['hero_hp']==snapshot['hero_hp'])
        check(owner.guardian7_lab['boss'].hp==snapshot['boss'].hp)
    check(service.draft==before_draft,'draft untouched')
    check(service.active==before_active,'active untouched')
    check(before_quests==list(db.conn.execute('select * from quests')),'sql untouched')
    check(random.getstate()==original_rng,'server RNG untouched')
    check(caps.current()==caps.DEFAULTS,'caps untouched')
    # No end-user API exposes our private diagnostic helper paths.
    for group,raw in [('arena','przeglad 6 0'),('questy','przeglad -1')]:
        check(await dispatch_v54(owner,group,raw) is True)
    check(await dispatch_v54(owner,'questy','nonexisting') is False)
    return checks

def run():
    result=asyncio.run(suite())
    print('ADMIN LIVE v54: %s PASS' % result)
    return result

if __name__=='__main__':run()
