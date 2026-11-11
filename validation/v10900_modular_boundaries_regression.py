# -*- coding: utf-8 -*-
"""v109: historyczne dane i nowe moduly zachowuja zachowanie z v108.

Testy porownuja pelna kanoniczna tresc, nie tylko liczby plikow.
Zadna kontrola nie dotyka produkcyjnej bazy SQLite ani GitHuba.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
from validation.v4050_catalog_modularization import EXPECTED as HISTORICAL_HASHES,_hash
from validation.modularity import validate_modular_boundaries

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOTS={
    'ITEMS':(318,'01b2eeb64e6e92e1228fde3ed4c3e8d011d767da2493f5289d96554da76f9022'),
    'ROOMS':(107,'5fa7c09d7be284360b61acc45aa01be89f5953ae4085d0f888b896daf604da0b'),
    'MOB_TEMPLATES':(40,'29824dfb12792ed1d1133dafef8dedc590089b4694c243c8614fc165b534ac09'),
    'NPCS':(46,'5b64736dec47ecabb4d3b07859111aef85f85f0119de4b9ca052cb1205774d36'),
    'QUESTS':(46,'216b20c736f71a9a3b50aa41370ebf26468fb85c914b3043643e3d2d33b4cff8'),
}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
           default=str,separators=(',',':')).encode('utf-8')).hexdigest()


def run():
    from data.items import ITEMS
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES
    from data.npcs import NPCS
    from data.quests import QUESTS
    from data.help_base_catalog_v405 import make_help_topics_v405,make_help_topic_aliases_v405
    from data.world_description_catalog_v405 import (
        make_mob_descriptions_v405, make_npc_descriptions_v405,
        make_stat_descriptions_v405, make_system_descriptions_v405)
    from world.horizon_index import REGIONS,CHAPTERS
    from systems.gift_runtime import gift_kind,reward_plan,claim_once,award_after_delay
    from systems.v11200_activation import REQUIRED
    from aktualizuj_soulbound import v111_live_release_mapping
    checks=0
    catalogs=dict(ITEMS=ITEMS,ROOMS=ROOMS,MOB_TEMPLATES=MOB_TEMPLATES,NPCS=NPCS,QUESTS=QUESTS)
    for name,old in SNAPSHOTS.items():
        if name=='NPCS' and os.environ.get('SOULBOUND_V107_STAGING')=='1':
            old=(47,'9910a1df30ea4580dcd14ad6f9ac26cffdc1e86f25dedceb2d43c1bfef9569ba')
        assert (len(catalogs[name]),fingerprint(catalogs[name]))==old,name
        checks+=1
    assert not validate_modular_boundaries(ROOT)['errors'],validate_modular_boundaries(ROOT)
    checks+=1
    for name,builder in [
        ('HELP_TOPICS',make_help_topics_v405),('HELP_TOPIC_ALIASES',make_help_topic_aliases_v405),
        ('NPC_DESCRIPTIONS',make_npc_descriptions_v405),
        ('MOB_DESCRIPTIONS',make_mob_descriptions_v405),
        ('STAT_DESCRIPTIONS',make_stat_descriptions_v405),
        ('SYSTEM_DESCRIPTIONS',make_system_descriptions_v405)]:
        first=builder();second=builder()
        assert _hash(first)==HISTORICAL_HASHES[name] and first==second,name
        assert first is not second,name
        for k in first:
            if isinstance(first[k],(list,dict)):
                assert first[k] is not second[k],(name,k)
        checks+=1
    assert len(REGIONS)==12 and tuple(len(c) for c in CHAPTERS)==(4,4,4)
    checks+=1
    from datetime import date
    assert gift_kind(date(2026,12,1))=='advent'
    assert gift_kind(date(2027,1,1))=='daily'
    assert all(callable(x) for x in (reward_plan,claim_once,award_after_delay))
    checks+=3
    current_quests=int((ROOT/'VERSION').read_text(encoding='utf-8-sig').split('.',1)[0])>=111
    quest_sources=([f'world/quests/base_{i:02d}.py' for i in range(1,4)]
                   if current_quests else
                   [f'data/catalogs_v109/quests_{i:02d}.py' for i in range(1,4)])
    paths=[
        *(f'data/catalog_parts/items_{i:02d}.py' for i in range(1,8)),
        *(f'data/catalog_parts/rooms_{i:02d}.py' for i in range(1,5)),
        *(f'data/catalog_parts/npcs_{i:02d}.py' for i in range(1,3)),
        *(f'data/catalog_parts/mobs_{i:02d}.py' for i in range(1,3)),
        *quest_sources,
        *(f'data/help_topics_v405/{name}.py' for name in (
            'economy_social','navigation_craft','quests_resources','world_exploration',
            'professions_equipment','progression')),
        *(f'data/descriptions_v405/{name}.py' for name in ('npc','mob','stat','system')),
        *(f'world/horizons/{name}.py' for name in ('entry','przebudzenie','zapomniani','wiecznosc')),
        *(f'systems/gift_parts/{name}.py' for name in ('policy','rewards','legacy','payout','delivery')),
    ]
    assert len(paths)==len(set(paths))
    # Current installed mapping is authoritative, not the obsolete v109 release list.
    installed={p.as_posix() for p in v111_live_release_mapping(
        {p.relative_to(ROOT):None for p in ROOT.rglob('*') if p.is_file()})}
    for relative in paths:
        path=ROOT/relative
        assert path.is_file() and relative in installed,relative
        if relative.startswith(('data/catalog_parts/','systems/gift_parts/')):
            assert relative in REQUIRED, 'v112 missing required module: '+relative
        src=path.read_text(encoding='utf-8')
        ast.parse(src,filename=relative)
        assert path.stat().st_size<30000,relative
        assert 'import server' not in src and 'from server import' not in src,relative
        checks+=1
    for source in ('data/items.py','data/rooms.py','data/npcs.py','data/mobs.py',
                   'data/quests.py','data/help_base_catalog_v405.py',
                   'data/world_description_catalog_v405.py','systems/gift_runtime.py',
                   'world/horizon_index.py'):
        assert ast.parse((ROOT/source).read_text(encoding='utf-8')),source
        checks+=1
    print(f'V109 MODULAR BOUNDARIES: {checks} PASS; '
          'historyczne dane bitowo rownowazne po kanonizacji',flush=True)
    return checks

if __name__=='__main__':run()
