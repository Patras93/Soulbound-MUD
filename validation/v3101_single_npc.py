# -*- coding: utf-8 -*-
"""v3.10.1: full-registry NPC room isolation + short quest acceptance.

Only uses in-memory catalogs; no production SQLite modification.
"""
from __future__ import annotations
from collections import defaultdict, deque
from types import SimpleNamespace

REVERSE = {'north':'south','south':'north','east':'west','west':'east',
 'northeast':'southwest','southwest':'northeast',
 'northwest':'southeast','southeast':'northwest', 'up':'down','down':'up'}


def run_regression(rooms, npcs, stats, shop_sellers=None, original_npc_ids=None):
    checks=0
    def test(condition, message):
        nonlocal checks
        assert condition,'JEDEN NPC NA POKOJ v3.10.1: '+message
        checks+=1

    for rid,seller_id in (shop_sellers or {}).items():
        if seller_id in npcs:
            test(npcs[seller_id]['room']==rid, 'shopkeeper relocated without moving shop: '+seller_id)
    test(bool(stats.get('shared_rooms_fixed')), 'expected repaired shared NPC rooms')
    test(stats['npcs_moved']==len(stats['relocated_npc_ids']), 'count of relocated NPCs')
    # Full historical audits may register temporary test NPCs. Compare IDs,
    # not registry length: additions are allowed only if all room invariants hold.
    # The initial call (without a snapshot) retains its strict catalog count.
    if original_npc_ids is None:
        test(stats['total_npcs']==len(npcs), 'initial NPC registry size differs from isolation snapshot')
    else:
        original_npc_ids = frozenset(original_npc_ids)
        test(len(original_npc_ids)==stats['total_npcs'], 'initial snapshot size does not match isolation stats')
        missing = original_npc_ids.difference(npcs)
        test(not missing, 'original NPC disappeared: '+repr(sorted(missing)[:20]))

    occupied=defaultdict(list)
    for npc_id,npc in npcs.items():
        room_id=npc.get('room')
        if room_id:
            test(room_id in rooms, 'NPC room missing: '+npc_id)
            occupied[room_id].append(npc_id)
    for room_id,names in occupied.items():
        test(len(names)<=1,'shared room: '+room_id+': '+str(names))

    for rid,room in rooms.items():
        if not rid.startswith('npc_v3101_'):
            continue
        exits=room.get('exits',{})
        test(bool(exits), 'island in NPC annexe: '+rid)
        for direction,target in exits.items():
            test(direction in REVERSE,'invalid direction: '+rid+': '+direction)
            test(target in rooms, 'missing exit destination: '+rid+'->'+str(target))
            test(rooms[target].get('exits',{}).get(REVERSE[direction])==rid,
                 'non-reversible exit: '+rid+': '+direction)
        if rid.startswith('npc_v3101_private_'):
            test(len(occupied[rid])==1, 'private NPC room not occupied by exactly one NPC')
        else:
            test(not occupied[rid], 'hub contains NPC: '+rid)

    # The temple is where the user/predeploy saw the ambiguity. Both NPCs must
    # remain present, in different walkable rooms with their OWN quest numbers.
    test(npcs['priest_elor']['room']=='temple','Elor must stay in Temple')
    remia_room=npcs['v3100_old_0_npc']['room']
    test(remia_room!='temple' and remia_room.startswith('npc_v3101_private_'),
         'Remia must receive her own room')
    test(any(target==remia_room for target in rooms['temple']['exits'].values()),
         'Temple has a direct accessible door to Remia')

    for class_name in ('mec','mag','wojownik','kaplan'):
        seller_id={'mec':'class_eq_shop_mec','mag':'class_eq_shop_mag','wojownik':'class_eq_shop_wojownik','kaplan':'class_eq_shop_kaplan'}[class_name]
        seller=npcs[seller_id]
        test(not seller['room'].startswith('npc_v3101_'),'original class shop room preserved')
        teacher_id={'mec':'teacher_mec','mag':'teacher_mage','wojownik':'teacher_warrior','kaplan':'teacher_priest'}[class_name]
        test(npcs[teacher_id]['room'].startswith('npc_v3101_private_'), 'teacher has own classroom')
    from player.session_mixins.quest_offers import SessionQuestOffersMixin
    class Dummy(SessionQuestOffersMixin):
        def __init__(self, room):
            self.character=SimpleNamespace(room_id=room)
            self.quest_list_context=None
        def quest_ids_for_npc(self, npc_id, npc):
            return list(npc.get('quest_chain') or ([npc['quest']] if npc.get('quest') else []))
        def quest_is_available_to_accept_v099(self, qid): return True

    # Simulates exactly the quest resolution called by `przyjmij 1`, without
    # requiring a previous `talk` or `quest list`.
    for npc_id in ('priest_elor','v3100_old_0_npc'):
        npc=npcs[npc_id]
        session=Dummy(npc['room'])
        quest_id,got_npc_id,error=session.direct_local_quest_for_number('1')
        test(got_npc_id==npc_id,'przyjmij 1 wrong NPC: '+npc_id)
        test(bool(quest_id) and error is None, 'przyjmij 1 failed: '+npc_id)
        test(session.quest_list_context['npc_id']==npc_id, 'quest context missing: '+npc_id)
        if len(session.quest_ids_for_npc(npc_id,npc))>1:
            q2,n2,error2=session.direct_local_quest_for_number('2')
            test(n2==npc_id and q2!=quest_id and error2 is None,
                 'przyjmij 2 should choose next quest: '+npc_id)
    return checks


if __name__=='__main__':
    import server
    print('JEDEN NPC NA POKOJ v3.10.1:',run_regression(server.ROOMS,server.NPCS,server.SINGLE_NPC_ROOMS_V3101),'PASS')
