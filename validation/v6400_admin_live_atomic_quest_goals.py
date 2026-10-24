# -*- coding: utf-8 -*-
"""v64: end-of-bundle OLC validation, derived count, cycles, admin ACL, privacy."""
from __future__ import annotations
import asyncio, copy, json, random
from systems.admin_live_bundle_v6200 import plan_bundle, commit_bundle, undo_bundle
from systems.admin_live_v6400 import count_preview
from systems.admin_live_integrity_v4900 import _effective
from validation.v6200_admin_live_bundle import strict_service
from validation.v3600_admin_guardian2 import Fake


def run():return asyncio.run(suite())

async def suite():
    n=0
    def ck(ok,msg=''):
        nonlocal n
        assert ok,msg
        n+=1
    owner=Fake();guest=Fake(False,owner.server.db)
    db_changes=owner.server.db.conn.total_changes
    rng=random.getstate()
    service=strict_service();before=copy.deepcopy(service.draft)
    owner.server.live_content_v1204=service
    qid='live_v64_multi_goals'
    base={'name':'Wielocelowy test admina','description':'Test bez produkcyjnej publikacji',
          'giver':'Rybak Borys','kind':'multi_objective','target':'temple_rat',
          'needed':6,'objectives':{'kill':{'temple_rat':2},
            'collect':{'iron_ore':3},'talk':['fisher_tomas']},'reward_silver':0}
    service.draft['quests'][qid]=copy.deepcopy(base)
    service.validate(service.draft)
    initial=copy.deepcopy(service.draft)
    try:
        ck('ZGODNY' in count_preview(service,qid))
        changed={'kill':{'temple_rat':3},'collect':{'iron_ore':5},'talk':['fisher_tomas']}
        encoded=json.dumps(changed,separators=(',',':'))
        spec=f'pole {qid} objectives {encoded} ; dopasuj {qid}'
        ck('PLAN' in plan_bundle(owner,service,spec))
        ck('2 operacji' in plan_bundle(owner,service,spec))
        ck('needed: 6 -> 9' in plan_bundle(owner,service,spec))
        ck(service.draft==initial)
        ck(owner.adminlive62_plan is not None)
        ck('DRAFT' in commit_bundle(owner,service))
        ck(_effective(service)[qid]['needed']==9)
        ck(_effective(service)[qid]['objectives']==changed)
        ck('ZGODNY' in count_preview(service,qid))
        ck(service.active.get('quest_edits',{})=={})
        ck('COFNIETO' in undo_bundle(owner,service))
        ck(service.draft==initial)
        # Without synced needed the canonical validator MUST reject the final patch.
        try:plan_bundle(owner,service,f'pole {qid} objectives {encoded}')
        except ValueError:ck(True)
        else:ck(False,'unmatched objective count accepted')
        ck(owner.adminlive62_plan is None)
        ck(service.draft==initial)
        # A raw count change with unchanged objectives is also unsafe.
        try:plan_bundle(owner,service,f'pole {qid} needed 9')
        except ValueError:ck(True)
        else:ck(False,'invalid solo needed accepted')
        ck(service.draft==initial)
        # A linked update in the opposite order is safely validated at plan end.
        ck('PLAN' in plan_bundle(owner,service,f'pole {qid} needed 9 ; pole {qid} objectives {encoded}'))
        ck('DRAFT' in commit_bundle(owner,service))
        ck('COFNIETO' in undo_bundle(owner,service))
        ck(service.draft==initial)
        # Resource sets currently have legacy no-target definitions: explicit target required.
        source='toren_ore_samples_v0929'
        rs=_effective(service)[source]
        ck(rs['kind']=='collect_resource_set')
        ck(rs['needed']==15)
        group={'copper_ore':7,'iron_ore':6,'silver_ore':5}
        raw=json.dumps(group,separators=(',',':'))
        instructions=(f'pole {source} resource_targets {raw} ; '
                      f'pole {source} target copper_ore ; dopasuj {source}')
        ck('PLAN' in plan_bundle(owner,service,instructions))
        ck('needed: 15 -> 18' in plan_bundle(owner,service,instructions))
        ck('DRAFT' in commit_bundle(owner,service))
        ck(_effective(service)[source]['needed']==18)
        ck(_effective(service)[source]['target']=='copper_ore')
        ck(_effective(service)[source]['resource_targets']==group)
        ck('ZGODNY' in count_preview(service,source))
        ck('COFNIETO' in undo_bundle(owner,service))
        ck(service.draft==initial)
        # Missing explicitly chosen target is not guessed by auto.
        try:plan_bundle(owner,service,f'pole {source} resource_targets {raw} ; dopasuj {source}')
        except ValueError:ck(True)
        else:ck(False,'automatically invented target')
        ck(service.draft==initial)
        # Can't auto-sync unrelated quests or already matching values.
        bad=[f'dopasuj temple_rats',f'dopasuj {qid}',
             f'dopasuj {qid} ; pole {qid} reward_gold 4',
             f'pole {qid} needed 5 ; dopasuj {qid} ; dopasuj {source}',
             f'pole {qid} objectives {{}} ; dopasuj {qid}',
             f'pole {qid} objectives not_json ; dopasuj {qid}',
             f'pole {source} resource_targets {{"copper_ore":-1,"iron_ore":1}} ; dopasuj {source}',
             f'dopasuj wrong_id_v64']
        for item in bad:
            try:plan_bundle(owner,service,item)
            except (ValueError,TypeError):ck(True,item)
            else:ck(False,'unexpectedly accepted '+item)
            ck(service.draft==initial)
            ck(owner.adminlive62_plan is None)
        # No retained authorization from an earlier, valid plan after a later failure.
        ck('PLAN' in plan_bundle(owner,service,spec))
        try:plan_bundle(owner,service,'this is not a plan')
        except ValueError:ck(True)
        else:ck(False,'accepted malformed plan')
        try:commit_bundle(owner,service)
        except ValueError:ck(True)
        else:ck(False,'committed a stale plan')
        ck(service.draft==initial)
        # End-of-bundle full graph check, not only direct self-edge checks.
        for label in ('a','b','c'):
            service.draft['quests']['live_v64_chain_'+label]={
                'name':'Graf '+label,'description':'Graf testowy','giver':'Rybak Borys',
                'kind':'kill','target':'temple_rat','needed':1,'reward_silver':1}
        service.validate(service.draft)
        chain_start=copy.deepcopy(service.draft)
        chain=('pole live_v64_chain_a requires_quest live_v64_chain_b ; '
               'pole live_v64_chain_b requires_quest live_v64_chain_c ; '
               'pole live_v64_chain_c requires_quest live_v64_chain_a')
        try:plan_bundle(owner,service,chain)
        except ValueError as exc:ck('cykl' in str(exc).lower(),str(exc))
        else:ck(False,'cycle accepted')
        ck(service.draft==chain_start)
        ck(owner.adminlive62_plan is None)
        ck('PLAN' in plan_bundle(owner,service,chain.rsplit(' ; ',1)[0]))
        ck('DRAFT' in commit_bundle(owner,service))
        ck('COFNIETO' in undo_bundle(owner,service))
        ck(service.draft==chain_start)
        # Owner-only command routing, read-only count, short NVDA help.
        async def ask(who,cmd):
            await who.admin_command('live '+cmd)
            return who.messages[-1]
        ck('POMOC 19' in await ask(owner,'pomoc 19'))
        ck('ZGODNY' in await ask(owner,'questy pakiet licznik '+qid))
        ck('ADMIN LIVE V64' in await ask(owner,'questy pakiet licznik temple_rats'))
        ck('Nieznana komenda' in await ask(guest,'pomoc 19'))
        ck('Nieznana komenda' in await ask(guest,'questy pakiet licznik '+qid))
        ck('PLAN' in await ask(owner,'questy pakiet plan '+spec))
        ck('DRAFT' in await ask(owner,'questy pakiet zatwierdz POTWIERDZAM'))
        ck('COFNIETO' in await ask(owner,'questy pakiet cofnij POTWIERDZAM'))
        ck(service.draft==chain_start)
        ck(service.active==strict_service().active)
        ck(owner.server.db.conn.total_changes==db_changes)
        ck(random.getstate()==rng)
        return n
    finally:
        service.draft=before

if __name__=='__main__':print('V64 ATOMIC QUEST GOALS:',run(),'PASS')
