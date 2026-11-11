# -*- coding: utf-8 -*-
"""v49: inspect real command routing, 18 quest kinds, LAB/SQLite invariants."""
import asyncio,copy,random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_integrity_v4900 import (_issues,_effective,_problems,_one,
      _chain,_integer, _party_report,_party_trace)
from systems.admin_live_expansion_v4800 import KINDS
from data.quests import QUESTS

async def suite():
    admin=Fake();db=admin.server.db
    admin.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    guest=Fake(False,db);guest.server.live_content_v1204=admin.server.live_content_v1204
    svc=admin.server.live_content_v1204
    n=0
    def ok(value, label):
        nonlocal n
        assert value,label
        n+=1
    async def cmd(raw,who=admin):
        await who.admin_command('live '+raw)
        return who.messages[-1]
    assert 'bandit_patrol' in QUESTS
    original_draft=copy.deepcopy(svc.draft)
    original_active=copy.deepcopy(svc.active)
    sql=list(db.conn.execute('select * from quests'))
    rnd=random.getstate()
    ok(_integer('0')==0,'numeric 0');ok(_integer('-7')==-7,'negative parse')
    for invalid in (True,False,1.5,'abc',None):ok(_integer(invalid) is None,'strict number')
    # A defined synthetic quest for each kind without touching runtime registries.
    for kind in KINDS:
        data={'name':'test','kind':kind,'target':'*','needed':2,'reward_silver':4,
              'reward_items':{},'repeat_cooldown':3}
        faults,hints=_issues('synth',data,{'synth':data})
        ok(not faults,kind+' normal shape')
        data['needed']=0
        faults,hints=_issues('synth',data,{'synth':data})
        if kind in {'collect','collect_category','collect_distinct_category','collect_resource',
                    'collect_resource_set','craft_set','kill','party_contract','profession_action'}:
            ok(any('needed:' in error for error in faults),kind+' needed 0')
        else:ok(not any('needed:' in error for error in faults),kind+' non count')
    examples=[
      ({'kind':'kill','needed':'NaN'},'needed: nieprawidlowa'),
      ({'kind':'kill','needed':-2},'needed: mniej'),
      ({'kind':'collect','needed':2,'reward_silver':-1},'wartosc ujemna'),
      ({'kind':'kill','needed':2,'requires_quest':'unknown'},'brak quest ID'),
      ({'kind':'kill','needed':2,'requires_quest':'lab'},'zaleznosc do siebie'),
      ({'kind':'kill','needed':2,'requires_quests':'unvalidated'},'wymagana lista'),
      ({'kind':'kill','needed':2,'reward_items':{'token':-2}},'niepoprawna ilosc'),
      ({'kind':'kill','needed':2,'reward_items':[12]},'wymagana mapa'),
      ({'kind':'collect_resource_set','needed':2,'resource_targets':{'x':0}},'resource_targets'),
      ({'kind':'kill','needed':2,'repeat_cooldown':-1},'repeat_cooldown'),
    ]
    for sample,expected in examples:
        errs,hints=_issues('lab',sample,{'lab':sample})
        ok(any(expected in e for e in errs),expected)
    bad={'kind':'kill','needed':2,'target':'legacy_event_target'}
    errs,hints=_issues('lab',bad,{'lab':bad})
    ok(not errs and any('statycznymi mobami' in w for w in hints),'unresolved alias only warning')
    ok('POMOC 6/6' in await cmd('pomoc 6'),'help')
    ok('QUEST BLEDY' in await cmd('questy bledy'),'global')
    ok('QUEST BLEDY kill' in await cmd('questy bledytyp kill'),'filter')
    ok('QUEST SPRAWDZ bandit_patrol' in await cmd('questy sprawdz bandit_patrol'),'details')
    ok('QUEST LANCUCH bandit_patrol' in await cmd('questy lancuch bandit_patrol'),'chain')
    for invalid in ('questy bledy 0','questy bledy -1','questy bledytyp bogus',
                    'questy sprawdz missing','questy lancuch missing'):
        ok('ADMIN LIVE:' in await cmd(invalid),'bad request '+invalid)
    for valid in ('pomoc 6','questy bledy','questy bledytyp kill',
                  'questy sprawdz bandit_patrol','questy lancuch bandit_patrol'):
        ok('Nieznana' in await cmd(valid,guest),'unauthorized '+valid)
    ok('ARENA11 START' in await cmd('arena start black_rabite 1000000 20000'),'arena start')
    ok('ARENA DRUZYNA: dodano' in await cmd('arena druzyna gotowy Wojownik 20 1000 5000 150 POTWIERDZAM'),'add')
    ok('ARENA DRUZYNA RAPORT' in await cmd('arena druzyna raport'),'party report')
    def digest():
        s=admin.guardian7_lab
        return (s['boss'].hp, s['hero_hp'], s['round'], s['total_dealt'], s['total_taken'],
                copy.deepcopy(s.get('_adminlive46_party')), copy.deepcopy(s['notes']),
                s.get('_guardian10_rng'))
    snapshot=digest()
    for steps in (1,3,12):
        msg=await cmd(f'arena druzyna przebieg {steps}')
        ok('ARENA DRUZYNA PRZEBIEG' in msg,'preview '+str(steps))
        ok('bez zmian' in msg,'preview inert '+str(steps))
        ok(digest()==snapshot,'state unchanged '+str(steps))
        ok(random.getstate()==rnd,'random unchanged '+str(steps))
    for invalid in ('0','13','notint'):
        ok('ADMIN LIVE:' in await cmd('arena druzyna przebieg '+invalid),'invalid steps')
        ok(digest()==snapshot,'failed trace unchanged')
    ok('Nieznana' in await cmd('arena druzyna przebieg 2',guest),'no unauthorized trace')
    ok(original_draft==svc.draft,'no OLC draft change')
    ok(original_active==svc.active,'no OLC published change')
    ok(sql==list(db.conn.execute('select * from quests')),'no DB quest write')
    ok('QUEST DIAGNOZA bandit_patrol' in await cmd('questy diagnoza bandit_patrol'),'legacy quest diag')
    ok('QUEST SZUKAJ' in await cmd('questy szukaj bandit'),'legacy search')
    ok('QUEST EXP' in await cmd('questy exp bandit_patrol'),'legacy stat EXP')
    return n

def run():return asyncio.run(suite())
if __name__=='__main__':print('V49 ADMIN LIVE INTEGRITY:',run(),'checks PASS')
