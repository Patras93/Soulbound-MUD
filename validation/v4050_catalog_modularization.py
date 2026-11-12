# -*- coding: utf-8 -*-
"""v4.00.5 static and runtime regression: no aliasing and no content loss."""
from __future__ import annotations
from validation.v1100_release_counts import expected_quest_total_v1100
import ast
import hashlib
import json
from pathlib import Path

EXPECTED = {'HELP_TOPICS': 'f3a849fa4acd34c131f9ef5fe7e7c5c229accbcd3b94c8b9f2f6050f471b3b70',
 'HELP_TOPIC_ALIASES': '9d8bba640c600b740f7d72ae3633752b2068b2c454e724012446adfd0a50e066',
 'MOB_DESCRIPTIONS': '5350de94ecfdee76cf92107c45929caa7299c3a789e1584cd009c061b45c4483',
 'NPC_DESCRIPTIONS': '298e36a628f90b4649b8b1941b0bc4ef800faa7964a0e949ef3c0fa03300877a',
 'STAT_DESCRIPTIONS': '7bdb95931b321fa88904eee0514c68ae3463f79ddb4433218968404fe4a8fe9d',
 'SYSTEM_DESCRIPTIONS': '9c92e2d7f3fd3ead40efa15b6b1425266cfc5d726f8b0cba9b657a22fa178f60'}
EXPECTED_COUNTS = {'HELP_TOPICS': 118,
 'HELP_TOPIC_ALIASES': 202,
 'MOB_DESCRIPTIONS': 34,
 'NPC_DESCRIPTIONS': 33,
 'STAT_DESCRIPTIONS': 16,
 'SYSTEM_DESCRIPTIONS': 27}
ROOT = Path(__file__).resolve().parents[1]

def _hash(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()

def run_regression():
    from core.bootstrap_economy_professions import VERSION
    from data import help_base_catalog_v405 as help_catalog
    from data import world_description_catalog_v405 as descriptions
    import server
    from core.runtime_manifest import FULL_RUNTIME_MODULES, RUNTIME_MODULES
    counts=0
    source=(ROOT/'systems/content_registry.py').read_text(encoding='utf-8')
    assert ast.parse(source)
    counts+=1
    assert 'systems/content_registry.py' in RUNTIME_MODULES and 'systems/content_registry.py' in FULL_RUNTIME_MODULES
    counts+=1
    for name,expected in EXPECTED.items():
        builder=getattr(help_catalog if name.startswith('HELP_') else descriptions,'make_'+name.lower()+'_v405')
        a=builder();b=builder()
        assert isinstance(a,dict) and a is not b and a==b
        assert len(a)==EXPECTED_COUNTS[name] and _hash(a)==expected,name
        assert all(a[key] is not b[key] for key in a if isinstance(a[key],(dict,list))),name
        assert name in server.__dict__ and isinstance(server.__dict__[name],dict),name
        assert set(a).issubset(server.__dict__[name]) or name in ('HELP_TOPICS','HELP_TOPIC_ALIASES'),name
        counts+=7
    # v104.00.3 — katalog jest nadal kompletny, a jedynymi świadomymi
    # zmianami opisu NPC/systemu są teksty dotyczące Broni Duszy i Elora.
    # Weryfikuj wszystkie NIEZMIENIONE wpisy względem historycznego v4.00.5,
    # aby aktualizacja dawnego hasha nie ukryła przypadkowej utraty treści.
    npcs=descriptions.make_npc_descriptions_v405()
    sys_descriptions=descriptions.make_system_descriptions_v405()
    assert _hash({k:v for k,v in npcs.items() if k!='priest_elor'}) == '6ccf86c65ac7d30bd860d0fea30d65a275fd817747193506f0066e1a5da13e79'
    soul_keys=('bron duszy','broń duszy','proby duszy','próby duszy','soul weapon','soul trials')
    assert _hash({k:v for k,v in sys_descriptions.items() if k not in soul_keys}) == '425873beda1c450d9196fd39af58a844635dfa62c2bb05411a80cf5b564f3099'
    assert '2–1000' in npcs['priest_elor'] and 'quest list Elor 81' in npcs['priest_elor']
    assert '1000' in sys_descriptions['broń duszy'] and 'Elora' in sys_descriptions['próby duszy']
    counts+=4
    # v107 intentionally installs eight classes AFTER the historical 22-class
    # bootstrap. In an unactivated TEMP candidate, early audits see 22;
    # in the fully enabled v107+/production runtime they must see 30.
    # Never infer activation solely from VERSION: offline tests MUST NOT
    # fabricate a production marker or bypass the install guard.
    major=int(VERSION.split('.',1)[0])
    from systems.universal_activation import enabled as universal_enabled
    if universal_enabled():
        # The current, staged or approved catalog contains all 38 historical
        # class definitions; future releases may add classes, never drop them.
        assert len(server.CLASS_SKILLS) >= 38, (VERSION, len(server.CLASS_SKILLS), 'expected at least 38')
    else:
        # Legacy pre-universal releases retain their original activation rules.
        if major>=110:
            from systems.v10700_activation import enabled as v107_active
            from systems.v11000_activation import enabled as v110_active
            expected_classes=38 if v110_active() else 30 if v107_active() else 22
        elif major>=107:
            from systems.v10700_activation import enabled as v107_active
            expected_classes=30 if v107_active() else 22
        else:
            expected_classes=22 if major>=9 else 14
        assert len(server.CLASS_SKILLS)==expected_classes,(VERSION,len(server.CLASS_SKILLS),expected_classes)
    counts+=1
    assert (len(server.QUESTS) >= 6745 if int(VERSION.split('.',1)[0]) >= 23 else len(server.QUESTS) == (expected_quest_total_v1100() if int(VERSION.split('.',1)[0]) >= 11 else 6585 if int(VERSION.split('.',1)[0]) == 10 else 6573 if int(VERSION.split('.',1)[0]) == 9 else 5605 if int(VERSION.split('.',1)[0]) == 8 else 3925 if int(VERSION.split('.',1)[0]) == 7 else 3861 if VERSION == '6.00.1' else 2901 if int(VERSION.split('.',1)[0]) in (5,6) else 2701))
    counts+=1
    assert all(name in server.__dict__ for name in ('HELP_TOPICS','HELP_TOPIC_ALIASES','NPC_DESCRIPTIONS'))
    counts+=1
    # Each normal runtime help expansion mutates its local dictionary; builders
    # must be immune, even when help/audit code is executed more than once.
    server.HELP_TOPICS.setdefault('_v405_test_only', ['check'])
    try:
        assert '_v405_test_only' not in help_catalog.make_help_topics_v405()
        counts+=1
    finally:
        server.HELP_TOPICS.pop('_v405_test_only',None)
    return counts
