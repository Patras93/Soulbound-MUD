# -*- coding: utf-8 -*-
"""v94: final-state atomic quest fixes, exact counters, real skill combos."""
import asyncio,copy,json
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_integrity_v4900 import _effective
from systems.live_olc19_status_skills import apply_skill_effects_v9300
from systems.summon_status_v1808 import summon_status_enemy_turn_v1808

async def main():
    n=0
    def ok(cond,label):
        nonlocal n
        assert cond,label;n+=1
    user=Fake();guest=Fake(False,user.server.db)
    service=LiveContentV1204(SimpleNamespace(conn=user.server.db.conn))
    user.server.live_content_v1204=service
    guest.server.live_content_v1204=service
    async def run(text,who=user):
        await who.admin_command('live '+text)
        return who.messages[-1]
    try:
        before=copy.deepcopy(service.draft);active=copy.deepcopy(service.active)
        ok('POMOC 52' in await run('pomoc 52'),'help routed')
        ok('Nieznana komenda' in await run('pomoc 52',guest),'guest refused')
        ok('Nieznana komenda' in await run('questy pakiet plan temple_rats needed | 4',guest),'guest quest refused')
        ok('Nieznana komenda' in await run('skill efekty pakiet plan warrior_power_slash | AUTO',guest),'guest skill refused')
        ok('QUEST PAKIET PLAN' in await run('questy pakiet plan temple_rats needed | 4; temple_rats reward_gold | 100'), 'quest plan')
        ok(service.draft==before,'quest plan no mutation')
        ok('zatwierdzono' in await run('questy pakiet zatwierdz POTWIERDZAM'),'quest commit')
        ok(_effective(service)['temple_rats']['needed']==4,'needed changed')
        ok(_effective(service)['temple_rats']['reward_gold']==100,'gold changed')
        ok(service.active==active,'ACTIVE unchanged')
        ok('Cofnieto' in await run('questy pakiet cofnij POTWIERDZAM'),'quest undo')
        ok(service.draft==before,'quest exact undo')
        for invalid in ('temple_rats needed | 0','temple_rats reward_gold | -1',
                        'temple_rats fake_field | 1','bad_quest needed | 1',
                        'temple_rats needed | 2; temple_rats needed | 3',
                        'temple_rats repeat_cooldown | 60',
                        'temple_rats required_quest | __import__("os")'):
            ok('ADMIN LIVE v94' in await run('questy pakiet plan '+invalid),'invalid quest blocked')
            ok(service.draft==before,'invalid quest atomic')
        ok('QUEST PAKIET PLAN' in await run('questy pakiet plan temple_rats needed | 4'),'quest plan for race')
        user.server.db.conn.execute("INSERT INTO quests VALUES(2,'temple_rats','active',0,0,0)")
        ok('zablokowan' in (await run('questy pakiet zatwierdz POTWIERDZAM')).lower(),'quest race blocked')
        ok(service.draft==before,'quest race atomic')
        user.server.db.conn.execute("DELETE FROM quests WHERE quest_id='temple_rats'")
        # A real OLC multi-objective quest: both target map and needed are edited
        # in ONE final-state validation, never through an invalid intermediate.
        service.draft['quests']['live_multi94']={
            'name':'Test trzech celow','giver':'Kapłan Elor','kind':'multi_objective',
            'target':'temple_rat','needed':4,'description':'Scenariusz testowy',
            'reward_silver':1,'objectives':{'kill':{'temple_rat':2},
                 'collect':{'healing_potion':1},'talk':['priest_elor']},
        }
        service.validate(service.draft)
        with_multi=copy.deepcopy(service.draft)
        goals={'kill':{'temple_rat':3},'collect':{'healing_potion':2},'talk':['priest_elor']}
        command='questy pakiet plan live_multi94 objectives | '+json.dumps(goals,separators=(',',':'))+'; live_multi94 needed | 6'
        ok('QUEST PAKIET PLAN' in await run(command),'multi objective atomic final')
        ok(service.draft==with_multi,'multi plan read only')
        ok('zatwierdzono' in await run('questy pakiet zatwierdz POTWIERDZAM'),'multi commit')
        ok(_effective(service)['live_multi94']['needed']==6,'multi computed total persisted')
        ok(_effective(service)['live_multi94']['objectives']==goals,'multi objectives persisted')
        ok('Cofnieto' in await run('questy pakiet cofnij POTWIERDZAM'),'multi undo')
        ok(service.draft==with_multi,'multi undo exact')
        service.draft=copy.deepcopy(before)
        questid=None
        # Introduce a deliberately inconsistent manual DRAFT row, test exact repair.
        setid=next((qid for qid,q in _effective(service).items() if q.get('kind')=='collect_resource_set' and
            isinstance(q.get('resource_targets'),dict) and len(q['resource_targets'])>=2),None)
        badid=setid or questid
        if badid:
            record=_effective(service)[badid]
            needed=int(record['needed']);service.draft.setdefault('quest_edits',{}).setdefault(badid,{})['needed']=needed+1
            broken=copy.deepcopy(service.draft)
            ok(badid in await run('questy liczniki skan'),'counter scan')
            ok('LICZNIKI PLAN' in await run('questy liczniki plan 1'),'counter computed plan')
            ok(service.draft==broken,'counter plan read only')
            ok('zatwierdzono' in await run('questy liczniki zatwierdz POTWIERDZAM'),'counter commit')
            ok(_effective(service)[badid]['needed']==needed,'counter correct')
            ok('Cofnieto' in await run('questy liczniki cofnij POTWIERDZAM'),'counter undo')
            ok(service.draft==broken,'counter original restored')
            service.draft=copy.deepcopy(before)
            user.server.db.conn.execute('DELETE FROM quests')
        ok('ADMIN LIVE v94' in await run('questy liczniki plan 0'),'invalid counter limit')
        # On-hit effects are actual engine statuses, not display-only flags.
        combos=[{'kind':'poison','chance':1.0,'ticks':2}, {'kind':'burn','chance':1.0,'ticks':2}]
        magic=json.dumps(combos,separators=(',',':'))
        ok('SKILL EFEKTY PLAN' in await run('skill efekty pakiet plan warrior_power_slash | '+magic),'skill plan')
        ok(service.draft==before,'skill plan read only')
        ok('zatwierdzono' in await run('skill efekty pakiet zatwierdz POTWIERDZAM'),'skill commit')
        ok(service.draft['skill_edits']['warrior_power_slash']['olc_statuses']==combos,'skill stored')
        ok('Cofnieto' in await run('skill efekty pakiet cofnij POTWIERDZAM'),'skill undo')
        ok(service.draft==before,'skill undo exact')
        for invalid in ('warrior_power_slash | []','warrior_power_slash | NOT_JSON',
                        'warrior_power_slash | '+json.dumps([{'kind':'freeze','chance':1.},{'kind':'shock','chance':1.}]),
                        'not_skill | '+magic, 'not_skill | AUTO',
                        'warrior_power_slash | '+magic+'; warrior_power_slash | AUTO'):
            ok('ADMIN LIVE v94' in await run('skill efekty pakiet plan '+invalid),'invalid skill rejected')
            ok(service.draft==before,'invalid skill atomic')
        # Replace prior OLC single effect without requiring two separate writes.
        service.draft.setdefault('skill_edits',{}).setdefault('warrior_power_slash',{})['olc_status']={'kind':'freeze','chance':1.0}
        legacy=copy.deepcopy(service.draft)
        ok('SKILL EFEKTY PLAN' in await run('skill efekty pakiet plan warrior_power_slash | '+magic),'legacy migrate plan')
        ok(service.draft==legacy,'migrate plan read only')
        ok('zatwierdzono' in await run('skill efekty pakiet zatwierdz POTWIERDZAM'),'legacy migrate commit')
        ok('olc_status' not in service.draft['skill_edits']['warrior_power_slash'],'old effect dropped')
        ok(service.draft['skill_edits']['warrior_power_slash']['olc_statuses']==combos,'new effects set')
        ok('Cofnieto' in await run('skill efekty pakiet cofnij POTWIERDZAM'),'legacy undo')
        ok(service.draft==legacy,'legacy exact undo')
        service.draft=before
        mob=SimpleNamespace(hp=1000,alive=True)
        ok(len(apply_skill_effects_v9300(mob,combos,200,now=10,rolls=[0.,0.]))==2,'real combat status')
        lines,_,_=summon_status_enemy_turn_v1808(mob,now=14)
        ok(mob.hp<1000 and bool(lines),'damage over time applied')
        ok(service.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite remains intact')
        ok(service.active==active,'ACTIVE unchanged final')
        print(f'V94 FULL QUESTS AND EFFECTS: {n} PASS',flush=True)
    finally:user.server.db.conn.close()

if __name__=='__main__':asyncio.run(main())
