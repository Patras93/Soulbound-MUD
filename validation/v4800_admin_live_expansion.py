# -*- coding: utf-8 -*-
"""v48 regression: live routing, quest categories, inert battle comparisons."""
import asyncio,copy,random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_expansion_v4800 import KINDS, _diagnose
from data.quests import QUESTS

async def suite():
    owner=Fake();db=owner.server.db
    owner.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    guest=Fake(False,db);guest.server.live_content_v1204=owner.server.live_content_v1204
    service=owner.server.live_content_v1204
    original_draft=copy.deepcopy(service.draft)
    original_active=copy.deepcopy(service.active)
    sql=list(db.conn.execute('select * from quests'))
    data=copy.deepcopy(QUESTS['bandit_patrol'])
    rng=random.getstate();n=0
    def ok(cond,label):
        nonlocal n
        assert cond,label
        n+=1
    async def cmd(value,user=owner):
        await user.admin_command('live '+value)
        return user.messages[-1]
    ok(len(KINDS)==18,'exact 18 kinds')
    ok('POMOC 5/5' in await cmd('pomoc 5'),'help')
    ok('QUEST TYPY' in await cmd('questy typy'),'types')
    ok('18 rodzajow' in await cmd('questy typy'),'18 types base')
    ok('strona 2/3' in await cmd('questy typy 2'),'pagination')
    for kind in KINDS:
        text=await cmd('questy typ '+kind)
        ok('QUEST TYP '+kind in text,'kind '+kind)
    # Every known quest kind gets a bounded diagnostic path even when no
    # such quest appears in the small static starter catalog.
    mock=SimpleNamespace(draft={'quests':{},'quest_edits':{},'mobs':{},'npcs':{},'items':{}},
                         active={'quest_edits':{}})
    for kind in KINDS:
        qid='lab_diag_'+kind
        mock.draft['quests'][qid]={'name':'Diagnostyka '+kind,'kind':kind,
          'target':'none','needed':2,'reward_silver':0,'giver':'Test'}
        result=_diagnose(mock,qid)
        ok('QUEST DIAGNOZA '+qid in result,'diagnostic for '+kind)
        ok('zero zmian' in result,'no modify for '+kind)
    mock.draft['quests']['lab_diag_kill']['needed']=-2
    ok('needed powinno' in _diagnose(mock,'lab_diag_kill'),'negative needed detected')
    mock.draft['quests']['lab_diag_kill']['requires_quests']=['quest_does_not_exist']
    ok('brak wymaganego questa' in _diagnose(mock,'lab_diag_kill'),'missing dependency detected')
    ok('bandit_patrol' in await cmd('questy typ kill'),'kill quest')
    ok('QUEST DIAGNOZA bandit_patrol' in await cmd('questy diagnoza bandit_patrol'),'diagnose')
    ok('admin live edytuj' in await cmd('questy diagnoza bandit_patrol'),'draft only')
    ok('ADMIN LIVE:' in await cmd('questy diagnoza none'),'invalid qid')
    for bad in ('questy typ kill 0','questy typ kill -1','questy typ kill 9999','questy typy 9999','questy typ /etc/passwd'):
        ok('ADMIN LIVE:' in await cmd(bad),'invalid '+bad)
    for val in ('questy typy','questy typ kill','questy diagnoza bandit_patrol', 'arena druzyna klasy','pomoc 5'):
        ok('Nieznana' in await cmd(val,guest),'permission '+val)
    ok('ARENA KLASY' in await cmd('arena druzyna klasy'),'classes')
    ok('22 klas' in await cmd('arena druzyna klasy'),'class count')
    ok('ARENA KLASY' in await cmd('arena druzyna klasy 3'),'third page')
    ok('ADMIN LIVE:' in await cmd('arena druzyna gotowy Wojownik 20 1000 5000 150 POTWIERDZAM'),'start required')
    ok('ARENA11 START' in await cmd('arena start black_rabite 1000000 20000'),'start')
    def digest():
        x=owner.guardian7_lab
        return (x['boss'].hp,x['hero_hp'],x['round'],x['total_dealt'],x['total_taken'],
                copy.deepcopy(x.get('_adminlive46_party')),copy.deepcopy(x['notes']),
                x.get('_guardian10_rng'))
    first=digest()
    for invalid in ('Wojownik 0 1000 5000 150 POTWIERDZAM','NieMa 20 1000 5000 150 POTWIERDZAM',
                    'Wojownik 20 1000 -10 150 POTWIERDZAM','Wojownik 20 1000 5000 150 NIE'):
        ok('ADMIN LIVE:' in await cmd('arena druzyna gotowy '+invalid),'bad '+invalid)
        ok(digest()==first,'bad no mutation '+invalid)
    ok('dodano 1' in await cmd('arena druzyna gotowy Wojownik 20 1000 5000 150 POTWIERDZAM'),'ready')
    ok('warrior_' in await cmd('arena druzyna sklad'),'autoselected skill shown')
    snapshot=digest()
    for count in (1,3,12):
        ok('ARENA POROWNANIE' in await cmd(f'arena druzyna porownaj {count}'),'compare')
        ok(digest()==snapshot,'compare not mutate')
        ok(random.getstate()==rng,'compare RNG')
    for invalid in ('0','13','abc'):
        ok('ADMIN LIVE:' in await cmd('arena druzyna porownaj '+invalid),'bad turns')
        ok(digest()==snapshot,'bad turns unchanged')
    ok(service.draft==original_draft,'draft immutable')
    ok(service.active==original_active,'active immutable')
    ok(list(db.conn.execute('select * from quests'))==sql,'sqlite no writes')
    ok(QUESTS['bandit_patrol']==data,'base quest unchanged')
    ok('QUEST EXP' in await cmd('questy exp bandit_patrol'),'old v47 EXP')
    ok('QUEST SZUKAJ' in await cmd('questy szukaj bandit'),'old v46 query')
    return n

def run():return asyncio.run(suite())
if __name__=='__main__':print('V48 ADMIN LIVE:',run(),'checks PASS')
