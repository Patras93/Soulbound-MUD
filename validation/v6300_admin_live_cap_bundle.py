# -*- coding: utf-8 -*-
"""Release v63: cap-safe admin LAB, atomic mixed OLC bundle, no player writes."""
from __future__ import annotations
import asyncio, copy, random
from types import SimpleNamespace
from systems.admin_live_bundle_v6200 import plan_bundle,commit_bundle,undo_bundle
from systems.admin_live_v6300 import class_comparison,dispatch_v63
from systems.admin_live_ultimate_v4600 import _add_party,_party
from systems.admin_live_expansion_v4800 import _ready_member
from systems.admin_guardian10_v4400 import _lab_start10
from systems.admin_guardian11_v4500 import _arena
from systems.live_content_v1204 import LiveContentV1204,blank
from core import live_level_caps_v5200 as caps
from validation.v3600_admin_guardian2 import Fake


def run():return asyncio.run(suite())


async def suite():
    n=0
    def ck(value, label=''):
        nonlocal n
        assert value,label
        n+=1
    admin=Fake(); guest=Fake(False,admin.server.db)
    old_draft=copy.deepcopy(admin.server.live_content_v1204.draft)
    old_active=copy.deepcopy(admin.server.live_content_v1204.active)
    db_changes=admin.server.db.conn.total_changes
    original_rng=random.getstate()
    original_caps=dict(caps.current())
    service=object.__new__(LiveContentV1204)
    service.active=blank();service.draft=blank()
    try:
        admin.server.live_content_v1204=service
        bare=copy.deepcopy(service.draft)
        plan='pole temple_rats needed 4 ; pole temple_rats reward_stat_xp 1000'
        text=plan_bundle(admin,service,plan)
        ck('2 operacji' in text)
        ck('temple_rats needed' in text)
        ck('olc_reward_stat_xp' in text)
        ck(service.draft==bare)
        ck('DRAFT' in commit_bundle(admin,service))
        ck(service.draft['quest_edits']['temple_rats']['needed']==4)
        ck(service.draft['quest_edits']['temple_rats']['olc_reward_stat_xp']==1000)
        ck(service.active==blank())
        ck('COFNIETO' in undo_bundle(admin,service))
        ck(service.draft==bare)
        # Combine replacement ID and several numeric OLC fields across quests.
        mixed=('nagroda healing_potion greater_healing_potion temple_rats ; '
               'pole temple_rats needed 3 ; '
               'pole temple_rats reward_stat_strength 75 ; '
               'pole fisher_30_fish reward_gold 100')
        ck('4 operacji' in plan_bundle(admin,service,mixed))
        ck('DRAFT' in commit_bundle(admin,service))
        patches=service.draft['quest_edits']
        ck(patches['temple_rats']['reward_items']=={'greater_healing_potion':1})
        ck(patches['temple_rats']['needed']==3)
        ck(patches['temple_rats']['olc_reward_stat_strength']==75)
        ck(patches['fisher_30_fish']['reward_gold']==100)
        ck('COFNIETO' in undo_bundle(admin,service))
        ck(service.draft==bare)
        # Every field is canonical OLC validated, including JSON and aliases.
        ck('PLAN' in plan_bundle(admin,service,'pole temple_rats repeatable true'))
        ck('DRAFT' in commit_bundle(admin,service))
        ck(service.draft['quest_edits']['temple_rats']['repeatable'] is True)
        ck('COFNIETO' in undo_bundle(admin,service))
        # No partial write even after an earlier operation would have succeeded.
        bad=[
            'pole temple_rats needed 0',
            'pole temple_rats reward_stat_xp -1',
            'pole temple_rats nonexistent 3',
            'pole temple_rats reward_gold 3 ; pole temple_rats needed 0',
            'pole temple_rats generator_level 801',
            'pole temple_rats needed',
            'pole temple_rats needed 4 extra',
            'pole missing_v63 needed 5',
            'pole temple_rats needed 4 ; pole temple_rats needed 4',
            'pole temple_rats reward_gold 999999999999999999999',
            'pole temple_rats reward_stat_xp x',
        ]
        for cmd in bad:
            try:plan_bundle(admin,service,cmd)
            except (ValueError,TypeError,OverflowError):ck(True)
            else:ck(False,'accepted bad plan '+cmd)
            ck(service.draft==bare)
        ck('PLAN' in plan_bundle(admin,service,mixed))
        service.draft['quest_edits']['unrelated_v63']={'needed':2}
        try:commit_bundle(admin,service)
        except ValueError:ck(True)
        else:ck(False,'stale commit')
        service.draft=copy.deepcopy(bare)
        ck('PLAN' in plan_bundle(admin,service,mixed))
        ck('DRAFT' in commit_bundle(admin,service))
        service.draft['quest_edits']['unrelated_v63']={'needed':2}
        try:undo_bundle(admin,service)
        except ValueError:ck(True)
        else:ck(False,'stale undo')
        service.draft=copy.deepcopy(bare)
        # Lab uses configuration, not hard-coded 800; real sessions not touched.
        caps._state['bieglosc']=800
        dummy=SimpleNamespace(guardian7_lab=None,guardian9_snapshot=None)
        _lab_start10(dummy,service,'black_rabite','1000000','20000')
        try:_add_party(dummy,['Wojownik','801','5000','1000','100','POTWIERDZAM'])
        except ValueError:ck(True)
        else:ck(False,'party bypassed cap')
        try:class_comparison(dummy,'1','1','801')
        except ValueError:ck(True)
        else:ck(False,'matrix bypassed cap')
        caps._state['bieglosc']=1800
        ck('bieg. 1200' in _add_party(dummy,['Wojownik','1200','5000','1000','100','POTWIERDZAM']))
        ck(_party(_arena(dummy))[-1]['mastery']==1200)
        ck('bieg. 1300' in _ready_member(dummy,['Mag','1300','5000','1000','100','POTWIERDZAM']))
        ck(_party(_arena(dummy))[-1]['mastery']==1300)
        before=copy.deepcopy(dummy.guardian7_lab)
        def signature(lab):
            return (lab['round'],lab['hero_hp'],lab['boss'].hp,lab['total_dealt'],
                    lab['total_taken'],lab['_guardian10_rng'],
                    tuple((m['class'],m['mastery'],m['hp'],m['mana'],m['skill']) for m in _party(lab)))
        ck('TESTOWA 1200' in class_comparison(dummy,'1','1','1200'))
        ck('22 klas' in class_comparison(dummy,'1','3','1200'))
        ck(signature(dummy.guardian7_lab)==signature(before))
        ck(random.getstate()==original_rng)
        for invalid in ('-1','b','9999999999'):
            try:class_comparison(dummy,'1','1',invalid)
            except ValueError:ck(True)
            else:ck(False,'accepted invalid class level')
        # Native admin live command routing, owner vs nonadmin.
        admin.guardian7_lab=copy.deepcopy(dummy.guardian7_lab)
        async def ask(who,cmd):
            await who.admin_command('live '+cmd)
            return who.messages[-1]
        ck('POMOC 18' in await ask(admin,'pomoc 18'))
        ck('TESTOWA 1200' in await ask(admin,'arena klasy porownaj 1 1 1200'))
        ck('PLAN' in await ask(admin,'questy pakiet plan '+mixed))
        ck('DRAFT' in await ask(admin,'questy pakiet zatwierdz POTWIERDZAM'))
        ck('COFNIETO' in await ask(admin,'questy pakiet cofnij POTWIERDZAM'))
        for cmd in ('pomoc 18','arena klasy porownaj 1 1 1200','questy pakiet plan '+mixed):
            ck('Nieznana komenda' in await ask(guest,cmd))
        ck(admin.server.db.conn.total_changes==db_changes)
        ck(random.getstate()==original_rng)
        ck(service.draft==bare)
        ck(service.active==blank())
        return n
    finally:
        caps._state.update(original_caps)
        admin.server.live_content_v1204.draft=old_draft
        admin.server.live_content_v1204.active=old_active


if __name__=='__main__':print('V63 ADMIN LIVE:',run(),'PASS')
