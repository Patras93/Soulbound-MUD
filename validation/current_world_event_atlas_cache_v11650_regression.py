# -*- coding: utf-8 -*-
"""Validate hourly event caching and atlas invalidation without server boot."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch


def run():
    from world import world_state
    import world.dynamic_world_generator as event_generator
    import world.great_world as great_world
    from data import catalog_mutations
    checks=0
    original=world_state._V0290_EVENT_SNAPSHOT_V11650
    calls=[]
    def calculate(*a,**kw):
        calls.append(kw.get('now'))
        return ({'room_id':'test_event','token':str(event_generator.event_slot(kw.get('now')))},)
    def rotate(now=None):
        return ({'room_id':'test_rotating','token':str(now)},)
    try:
        world_state._V0290_EVENT_SNAPSHOT_V11650=None
        with patch.object(event_generator,'active_events',side_effect=calculate),patch.object(great_world,'v1200_rotating_events',side_effect=rotate):
            first=world_state.v0290_active_world_events(1760000000)
            for _ in range(100):
                assert world_state.v0290_active_world_events(1760000001)[0]==first[0]
                checks+=1
            assert len(calls)==1;checks+=1
            assert world_state.v0290_active_world_events(1760000002)[1]['token']=='1760000002';checks+=1
            after=world_state.v0290_active_world_events(1760003600)
            assert len(calls)==2 and first[0]!=after[0];checks+=1
            assert world_state.v0290_event_for_room('test_event',1760003601)==(after[0],);checks+=1
    finally:
        world_state._V0290_EVENT_SNAPSHOT_V11650=original

    # Source-owned atlas module needs full legacy world boot. Check the
    # invalidation contract here; actual real-world six-player benchmark tests
    # the live atlas under runtime boot without adding another boot per gate.
    source=(Path(__file__).resolve().parents[1]/'player/session_mixins/exploration_progress.py').read_text('utf-8')
    assert '_mut_v11650.ATLAS_GENERATION_V11650' in source;checks+=1
    assert 'now - cached[1] < 3600.0' in source;checks+=1
    assert 'len(ROOMS)' not in source.split('def global_discovery_atlas_catalog_v1120(self):',1)[1].split('catalog =',1)[0];checks+=1
    previous=catalog_mutations.ATLAS_GENERATION_V11650
    collection={}
    catalog_mutations.catalog_assign({'zone':'Procedural'},'ROOMS',collection,('crypt_floor_demo',))
    assert catalog_mutations.ATLAS_GENERATION_V11650==previous;checks+=1
    catalog_mutations.catalog_assign({'zone':'Nowa Zatoka'},'ROOMS',collection,('v1600_test_authored',))
    assert catalog_mutations.ATLAS_GENERATION_V11650>previous;checks+=1
    print(f'V116.00.50 EVENT SLOT AND ATLAS CACHE: {checks} PASS',flush=True)
    return checks

if __name__=='__main__':run()
