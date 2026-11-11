# -*- coding: utf-8 -*-
"""v107 stage5: real catalog tests, never touches production SQLite or TCP."""
from __future__ import annotations
import os
import sys
from copy import deepcopy


def main():
    with_v106 = '--with-v106' in sys.argv[1:]
    os.environ['SOULBOUND_V106_STAGING'] = '1' if with_v106 else '0'
    # Read *unmodified* baseline; exercise the v107 retirement on private copies.
    os.environ['SOULBOUND_V107_STAGING'] = '0'
    from world import dynamic_content as w
    from world.v10700_no_raids import (retire_all_raids_v107, raid_return_room_v107,
                                        _raid_groups)
    from systems.era_npc_offers_v10300 import visible_era_quests

    checks = 0
    def check(test, why):
        nonlocal checks
        assert test, why
        checks += 1
    groups = [g for g in _raid_groups() if with_v106 or g['era'] != 'v106']
    before_quests = {q: deepcopy(w.QUESTS[q]) for g in groups for q in g['quests']}
    before_items = {i: deepcopy(w.ITEMS[i]) for g in groups for i in
                    (g['fragment'],g['relic'],g['seal']) if i}
    before_recipes = {g['relic']: deepcopy(w.CRAFT_RECIPES[g['relic']]) for g in groups}
    wrooms = deepcopy(w.ROOMS)
    wmobs = deepcopy(w.MOB_TEMPLATES)
    wnpcs = deepcopy(w.NPCS)
    wquests = deepcopy(w.QUESTS)
    witems = deepcopy(w.ITEMS)
    wrecipes = deepcopy(w.CRAFT_RECIPES)
    wspawns = list(w.MOB_SPAWNS)
    init_sizes = (len(wrooms),len(wmobs),len(wquests),len(wspawns))
    result = retire_all_raids_v107(wrooms,wmobs,wspawns,wnpcs,wquests,witems,wrecipes)
    check(result['retired_raids'] == len(groups), 'all raids retired')
    check(result['removed_rooms'] == 3*len(groups), 'raid rooms removed')
    check(result['removed_bosses'] == 3*len(groups), 'raid bosses removed')
    check(result['replaced_solo_quests'] == 3*len(groups), 'quests converted')
    check((len(wrooms),len(wmobs),len(wquests)) ==
          (init_sizes[0]-3*len(groups),init_sizes[1]-3*len(groups),init_sizes[2]),
          'registry counts / stable quest IDs')
    check(not any('_raid_' in rid for rid in wrooms if rid.startswith(('v10300_','v10400_','v10600_'))),
          'no active raid rooms')
    check(not any('_raid_' in mid for mid in wmobs if mid.startswith(('v10300_','v10400_','v10600_'))),
          'no active raid enemies')
    check(not any('_raid_' in rid or '_raid_' in mid for rid,mid in wspawns),
          'no raid spawns')
    check(not any('_raid_' in target for room in wrooms.values()
                  for target in room.get('exits',{}).values()), 'no raid routes')
    check(not any('rajd' in (q.get('name','')+' '+q.get('description','')).casefold()
                  for q in wquests.values()), 'no active raid quest texts')
    check(not any('rajd' in (n.get('name','')+' '+n.get('dialogue','')).casefold()
                  for n in wnpcs.values()), 'no NPC raid talk')
    for g in groups:
        check(g['entry'] in wrooms, 'main world remains accessible')
        check(raid_return_room_v107(g['rooms'][0],wrooms) == g['entry'], 'saved character rescue')
        for stage,qid in enumerate(g['quests'],1):
            old,now=before_quests[qid],wquests[qid]
            target=now['target']
            check(target in wmobs and any(mid==target and rid in wrooms for rid,mid in wspawns),
                  'solo quest target spawns on real map')
            check(now['name'].casefold().find('rajd')<0, 'name is no longer raid')
            check(now.get('v107_retired_raid_converted') is True, 'legacy marker')
            check(now.get('giver')==old.get('giver'), 'same NPC claims reward')
            for key in ('reward_gold','reward_mithril','reward_stat_progress','requires_quest'):
                check(now.get(key)==old.get(key), 'historical reward/prerequisite kept')
            check(all(now['reward_items'].get(i,0)>=amount
                      for i,amount in old.get('reward_items',{}).items()), 'existing rewards unchanged')
        check(all(witems[i]['type']==before_items[i]['type'] for i in
                  (g['fragment'],g['relic'],g['seal']) if i), 'item types remain')
        for iid in (g['fragment'],g['seal'],g['relic']):
            if not iid: continue
            check({k:v for k,v in witems[iid].items() if k not in ('name','desc')} ==
                  {k:v for k,v in before_items[iid].items() if k not in ('name','desc')},
                  'item strength/trade stats unchanged')
            check('rajd' not in (witems[iid].get('name','')+' '+witems[iid].get('desc','')).casefold(),
                  'no raid on item label')
        rec=wrecipes[g['relic']]
        check(rec['ingredients']==before_recipes[g['relic']]['ingredients'],
              'craft input and quantities unchanged')
        check(rec['output']==before_recipes[g['relic']]['output'], 'same item crafted')
        normal_boss=wmobs[f'{g["target_base"]}_boss_1']
        check(normal_boss['drops'].get(g['fragment'],0)>0, 'fragments from normal world boss')
        if g['seal']:
            check(normal_boss['drops'].get(g['seal'],0)>0, 'seals from normal world boss')
            check(wquests[g['quests'][-1]]['reward_items'].get(g['seal'],0)>=1,
                  'seal also earnable by solo quest')
        # Legacy quests must still be visible for normal acceptance, not orphaned.
        provider=next((npc for npc in wnpcs.values() if g['quests'][0] in
                       npc.get('specialist_quests',())),None)
        check(provider is not None, 'quest giver still offers regional solo hunts')
        offered=visible_era_quests(provider['specialist_quests'], wquests,
                                  lambda qid:None,())
        check(g['quests'][0] in offered or any(q in offered for q in g['quests']),
              'NPC can offer converted quest without completed historical quests')
    # Admin Live must not advertise or modify retired raids in staging.
    from systems.admin_live_era_v10300 import report as era_report
    from systems.admin_live_era_v10400 import _parse_key
    from systems.admin_live_era_v10600 import command as v106_command
    previous=os.environ.get('SOULBOUND_V107_STAGING')
    os.environ['SOULBOUND_V107_STAGING']='1'
    try:
        for cmd in ('rajdy','rajd swit','rajdy104'):
            check('wycofane' in era_report(cmd,wquests,wrooms,wnpcs,wmobs),
                  'no raid command in admin era')
        check('rajd' not in era_report('region swit',wquests,wrooms,wnpcs,wmobs).casefold(),
              'admin region never advertises old raid entrance')
        try:_parse_key('raid_phase|v10400_raid_12_boss_1|p1_attack_pct')
        except ValueError:pass  # AUDIT_INTENTIONAL_PASS: retired raid editor must reject
        else:raise AssertionError('retired raid editing must be blocked')
        check(True,'historical raid editor refuses old phases')
        if with_v106:
            registries={'rooms':wrooms,'mobs':wmobs,'quests':wquests,'items':witems,'recipes':wrecipes}
            check('wycofane' in v106_command('rajdy',registries),
                  'v106 Admin Live raids disabled')
            check('aktywnych rajdów 0' in v106_command('audyt',registries),
                  'v106 admin audit reports zero raids')
            old_v106=os.environ.get('SOULBOUND_V106_STAGING')
            os.environ['SOULBOUND_V106_STAGING']='0'
            try:
                check('V106 KRAINY' in v106_command('regiony',registries),
                      'v107 grants historical v106 non-raid region browsing')
            finally:
                if old_v106 is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
                else:os.environ['SOULBOUND_V106_STAGING']=old_v106

    finally:
        if previous is None:os.environ.pop('SOULBOUND_V107_STAGING',None)
        else:os.environ['SOULBOUND_V107_STAGING']=previous
    # Explicitly exercise saved active-quest progress and preserved quest IDs.
    provider=next(npc for npc in wnpcs.values() if groups[0]['quests'][0] in npc.get('specialist_quests',()))
    active_qid=groups[0]['quests'][0]
    fake_row={'status':'active','completion_count':0}
    active_offers=visible_era_quests(provider['specialist_quests'],wquests,
                                  lambda q:fake_row if q==active_qid else None,())
    check(active_qid in active_offers,'active historical quest remains visible')
    # Invalid data must never be partially retired.
    badrooms = deepcopy(w.ROOMS)
    badmobs = deepcopy(w.MOB_TEMPLATES)
    badquests = deepcopy(w.QUESTS)
    badnpcs = deepcopy(w.NPCS)
    baditems = deepcopy(w.ITEMS)
    badrecipes = deepcopy(w.CRAFT_RECIPES)
    badspawns = list(w.MOB_SPAWNS)
    badmobs.pop(groups[0]['mobs'][1])
    sentinel = deepcopy(badrooms[groups[0]['entry']]['exits'])
    try:
        retire_all_raids_v107(badrooms,badmobs,badspawns,badnpcs,badquests,baditems,badrecipes)
    except RuntimeError:  # AUDIT_INTENTIONAL_PASS: expected invalid catalogue rejection
        pass
    else:
        raise AssertionError('incomplete old raid catalogue must be rejected')
    check(badrooms[groups[0]['entry']]['exits']==sentinel and
          groups[0]['quests'][0] in badquests and groups[0]['rooms'][0] in badrooms,
          'bad input rejected without partial deletion')
    # No accidental rescue of ordinary rooms; fallback for unavailable v106 regions.
    check(raid_return_room_v107('square',wrooms) is None, 'normal rooms unchanged')
    check(raid_return_room_v107('v10600_raid_35_stage_3',wrooms)==
          (f'v10600_serce_23' if with_v106 else 'square'), 'missing old v106 -> square')
    check(raid_return_room_v107('v10400_raid_99_stage_1',wrooms) is None,
          'unknown raid never guessed')
    # Confirm only in-memory world data changed, no storage/DB access.
    check(w.QUESTS[groups[0]['quests'][0]]==before_quests[groups[0]['quests'][0]],
          'original baseline registry untouched by copy test')
    print(f'V107 BEZ RAJDOW {"V106 ON" if with_v106 else "V106 OFF"}: '
          f'{checks} kontroli PASS; usunięto {result["retired_raids"]} rajdów, '
          f'{result["removed_rooms"]} komnat, przeniesiono {result["replaced_solo_quests"]} questów')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
