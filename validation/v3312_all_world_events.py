# -*- coding: utf-8 -*-
"""Release gate for v3.31.2: time-bound event actions and current event atlas.

No production DB required. Event schedules are deterministic; inspect multiple
slots and ensure unrelated rooms/professions never obtain bonus access.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace


def run_regression(runtime=None):
    from world.generation_systems import (
        V014_EVENT_DEFS, V018_LEGENDARY_EVENT_DEFS,
        active_profession_event_for_room, v0140_active_world_events,
        v0140_gather_event_bonus, v0180_active_legendary_events,
        v0130_frontier_room_id,
    )
    from core.progression_resources import is_mining_room, FISHING_ROOMS, WOODCUTTING_ROOMS, HERBALISM_ROOMS
    from player.session_mixins.gathering import SessionGatheringMixin
    from player.session_mixins.gathering_actions import SessionGatheringActionsMixin
    from player.session_mixins.exploration_professions import SessionExplorationProfessionsV1100Mixin
    from player.session_mixins.world_crises_v1220 import SessionWorldCrisesV1220Mixin
    from player.session_mixins.world_events_endgame import SessionWorldEventsEndgameMixin
    from systems.world_events_v12812 import active_city_event_v12812
    from systems.era_legends_v1600 import active_invasion_v1600
    from world.great_world import v1200_rotating_events

    checks=0
    def check(ok, msg):
        nonlocal checks
        assert ok, f"EVENT v3.31.2 regression: {msg}"
        checks+=1

    kinds = {"fish_run":"fishing","herb_bloom":"herbalism","rich_vein":"mining",
             "forest_growth":"woodcutting","ancient_dig":"archaeology"}
    check(len(V014_EVENT_DEFS)==8, '8 procedural world-event categories')
    check(len(V018_LEGENDARY_EVENT_DEFS)==5, '5 legendary definitions')
    check(len(v0140_active_world_events(1_800_000_000.0))==8, '8 active event locations')
    # Multi-slot audit: correct location, relevant tool, deterministic rotations,
    # static mining/crafting/gathering gates remain closed outside real event.
    for slot in range(1, 14):
        now=(slot+100_000)*1800.0+3
        events=v0140_active_world_events(now)
        check(len({e['room_id'] for e in events})==8, 'no two procedural event rooms overlap')
        check(events==v0140_active_world_events(now), 'slot determinism')
        for event in events:
            tool=kinds.get(event['type'])
            check(bool(event['title']) and event['room_id'].startswith('v0130_frontier_'), 'event metadata')
            if not tool:
                continue
            found=active_profession_event_for_room(event['room_id'],tool,now=now)
            check(found is not None and found['type']==event['type'],f"{event['type']} actionable")
            for other in ("fishing","herbalism","mining","woodcutting","archaeology"):
                if other==tool: continue
                # Coincident legendary events may genuinely grant a second tool.
                alt=active_profession_event_for_room(event['room_id'],other,now=now)
                if alt: check(alt.get('tool')==other, 'other tool must be independently active')
                else: check(True,'no false tool access')
            if tool=='mining':
                check(not is_mining_room(event['room_id']), 'mining event is outside classic Deep Mine')
                check(v0140_gather_event_bonus(event['room_id'],'mining',now)['quantity_bonus']==2,'mining bonus applied')
            elif tool=='fishing':check(event['room_id'] not in FISHING_ROOMS, 'fishing event expands actual habitat')
            elif tool=='herbalism':check(event['room_id'] not in HERBALISM_ROOMS,'herbal event expands actual source')
            elif tool=='woodcutting':check(event['room_id'] not in WOODCUTTING_ROOMS,'wood event expands actual source')
            elif tool=='archaeology':
                archaeology=object.__new__(SessionExplorationProfessionsV1100Mixin)
                archaeology.character=SimpleNamespace(room_id=event['room_id'])
                # Live function uses current slot, validated in the current-slot test below.
        # Off-event room in known frontier valid for no event of any type.
        inactive=v0130_frontier_room_id('mountain',0,0)
        occupied={e['room_id'] for e in events} | {e['room_id'] for e in v0180_active_legendary_events(now)}
        if inactive not in occupied:
            for tool in ('mining','archaeology'):
                check(active_profession_event_for_room(inactive, tool, now) is None,'no permanent excavation/mine unlocking')
    # Every legendary type is actually reachable in real periodic rotations;
    # profession events expose their tool in the correct changing cell.
    seen=set()
    for slot in range(160):
        now=(slot+100_000)*4*3600.0+7
        events=v0180_active_legendary_events(now)
        check(len(events)==2, 'two legendary events active')
        check(len({e['room_id'] for e in events})==2, 'legendary events must have different rooms')
        for e in events:
            seen.add(e['type'])
            check(e['expires_at']>now, 'legend active')
            if e.get('tool'):
                resolved=active_profession_event_for_room(e['room_id'], e['tool'], now)
                check(resolved is not None, f"legendary {e['type']} actionable")
    check(seen==set(V018_LEGENDARY_EVENT_DEFS),f'legendary roster reachability: {seen}')
    # Reproduce the production bug regardless of the randomly generated
    # world seed. In the original implementation both legendary events land
    # in the same meadow tile and woodcutting becomes inaccessible.
    from world.generation_systems import v0180_active_legendary_events as _legend_generator
    _g = _legend_generator.__globals__
    _original_hash = _g['_v0140_hash_int']
    def _force_legend_collision(*parts):
        tag = parts[0] if parts else None
        n = parts[2] if len(parts) > 2 else 0
        if tag == 'v018-legend-event-type':
            return (4, 1)[n]  # ancient_growth + great_bloom
        if tag == 'v018-legend-event-kind':
            return (2, 0)[n]  # both choose meadow
        if tag == 'v018-legend-event-x':
            return 5
        if tag == 'v018-legend-event-y':
            return 7
        if tag == 'v018-legend-event-retry-index':
            return 102  # meadow x=6, y=8
        return _original_hash(*parts)
    try:
        _g['_v0140_hash_int'] = _force_legend_collision
        collision_now = (100_024 * 4 * 3600) + 7
        colliding = v0180_active_legendary_events(collision_now)
        check(len(colliding)==2, 'forced collision preserves both legendary events')
        check({e['type'] for e in colliding} == {'ancient_growth','great_bloom'}, 'forced types unchanged')
        check(len({e['room_id'] for e in colliding})==2, 'forced collision reroutes only duplicate room')
        for event in colliding:
            resolved = active_profession_event_for_room(event['room_id'], event['tool'], collision_now)
            check(resolved is not None,
                  f"forced {event['type']} actionable")
        check(colliding == v0180_active_legendary_events(collision_now), 'forced collision deterministic')
    finally:
        _g['_v0140_hash_int'] = _original_hash
    # Real current event can be excavated; ordinary rock cannot.
    present=v0140_active_world_events()
    action=object.__new__(SessionGatheringActionsMixin)
    for event in present:
        if event['type'] in kinds and event['type']!='ancient_dig':
            action.character=SimpleNamespace(room_id=event['room_id'])
            feat=action.current_infinite_gather_feature(kinds[event['type']])
            check(feat['quantity_bonus']>=2, f"{event['type']} actual profession quantity bonus")
            check(feat['xp_mult']>=1.25, f"{event['type']} actual profession XP bonus")
            check(event['title'] in feat['label'], f"{event['type']} visible NVDA event bonus")
    dig=next(e for e in present if e['type']=='ancient_dig')
    arch=object.__new__(SessionExplorationProfessionsV1100Mixin)
    arch.character=SimpleNamespace(room_id=dig['room_id'])
    check(arch.v1100_archaeology_site(), 'real active excavation site')
    gather=object.__new__(SessionGatheringMixin)
    for e in present:
        if e['type']=='fish_run':
            gather.character=SimpleNamespace(room_id=e['room_id'])
            check(gather.active_event_fishery_v3312(),'auto-fishing accepts only event fishing room')
            check(gather.fishing_habitat() in ('river','lake','sea','ocean'), 'event fish habitat mapped')
    action.character=SimpleNamespace(room_id='temple')
    baseline=action.current_infinite_gather_feature('mining')
    check('WYDARZENIE ŚWIATA — Bogata żyła' not in baseline['label'], 'no permanent ore event boost')
    gather.character=SimpleNamespace(room_id='temple')
    check(not gather.active_event_fishery_v3312(), 'non-fish site remains blocked')
    check(active_city_event_v12812()['room_id'].startswith('v12812_city_'),'subterranean event available')
    check('room_id' in active_invasion_v1600(), 'invasion event available')
    check(callable(v1200_rotating_events),'regional events registered')

    # User-facing messages for all categories; isolated session, no DB mutation.
    class FakeEvents(SessionWorldEventsEndgameMixin):
        def __init__(self): self.out=[]
        async def send(self,text): self.out.append(str(text))
        async def show_double_xp_event(self): pass
        async def show_dynamic_events_v029(self): pass
    fake=FakeEvents()
    asyncio.run(fake.show_world_events())
    body=' '.join(fake.out)
    for mark in ('Bogata żyła','stanowisko wykopaliskowe','NAJAZD PODZIEMI','KRYZYSY','INWAZJA','KRÓLESTWA'):
        check(mark.casefold() in body.casefold(),f'world events atlas contains {mark}')
    # Check dispatch contract of 'kryzys pomoc': it must reach rescue branch.
    import inspect
    src=inspect.getsource(SessionWorldCrisesV1220Mixin.handle_world_crises_v1220)
    check('"pomoc", "help"' not in src,'crisis pomoc no longer swallowed by list branch')
    check('("ratuj", "pomoc")' in src,'crisis pomoc and rescue dispatch together')
    return checks


if __name__=='__main__':
    print('EVENTS v3.31.2:',run_regression(),'PASS')
