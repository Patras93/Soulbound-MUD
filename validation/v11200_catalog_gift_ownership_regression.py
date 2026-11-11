# -*- coding: utf-8 -*-
"""v112 immutable catalog/gift migration and current-only gift authorization.

No old server start, no user data. Protects installed code, reward and item IDs.
"""
from __future__ import annotations
import ast
import hashlib
import os
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
CATALOG_HASHES = {'__init__.py': '69aff67e1d5e5a132fea20e6bfcbe523712e8a59bb8daac40e317676ef523e51', 'items_01.py': 'f99bc72a52c82c56a093cb8496e41f33bf669541f1e5e6132b10f681df28db9b', 'items_02.py': 'cdc1602154c9a6049659a9922ab19a85254807dea008b9a0cd1e258ecc9ad066', 'items_03.py': '138406767458a58c8698fe2a14d18b6d566ab3102fa9b20cce6ecc2eb7a026a2', 'items_04.py': '95cb33e08d94f7d524cfcefdf50eed580326741914299a9eac6ffdc5e0721b66', 'items_05.py': '6affba7e52047895f901a937231e13e8531260afe9a41d4aeef7aca5e283104d', 'items_06.py': '971b1455ea6018a345f718eba326e816a1c16daf31c8bb7a75d96b00cbe0df95', 'items_07.py': 'f03c46f3de5b20762ab813e51e620e3f9ecbfaf40ab5385c06672cdf6a712030', 'mobs_01.py': '6862a7749f7e09e32e937cc551d8861463597468af41a76a5c3ab5caecbe0a95', 'mobs_02.py': 'c47ba2e933c974dbc8131b40a6f232145684fb64b98c0328911d0db1fd0bc6f5', 'npcs_01.py': '2485fbc58bd80bf065c67299cd61dd8c4abd23c23b036454458d7bbfe906ae84', 'npcs_02.py': '851a04edb3b7e35b111b55cd3b6379717ebeb5ec7cd9e174ab652c56c0bca621', 'rooms_01.py': '53c5a6d69a372a28f4375afe97caabfa62d50a9a86a4f84111a30583735e6261', 'rooms_02.py': 'aaff9aa528ca752606358006b8021cb03e3613458fbab20530ba7e1cc3a05488', 'rooms_03.py': '6e28260c2e1494a5a17d8614b405a65f7645ca5e11bd849baf36713e9f7b90b6', 'rooms_04.py': '9244ea9f1fde30a08750220e30afc7cbcfabbfb7172f1edbde8f82a2e9f01b64'}
GIFT_HASHES = {'__init__.py': '20006257f3339adc7b3d04e9620a1fd312c8b89b7e11cd062444164a8c65b308', 'delivery.py': 'efc64768caf27ef102b97f8f2fe35a6bc147fb5c502b533e83535c6484c59433', 'legacy.py': '7c627e07a10b8d3055718f81b53075fb156efe570a14f5785cc8e0b79ab0b4d7', 'payout.py': 'daf3ae3d119f9bc849896b95f5dd0fd06c423158f241b19b7f1484d5ff77dee3', 'rewards.py': '4c5879be6b5ccc406a9516bd5598f28673e27f62e7fbb2cb523460478439d90c'}


def run():
    from aktualizuj_soulbound import v111_live_release_mapping
    from systems.v11200_activation import REQUIRED
    from systems import gift_runtime
    from systems.gift_parts import policy
    checks=0
    names={p.relative_to(ROOT).as_posix():None for p in ROOT.rglob('*') if p.is_file()}
    shipped={p.as_posix() for p in v111_live_release_mapping({Path(p):None for p in names})}
    for old in ('data/catalogs_v109','systems/gifts_v109'):
        assert not (ROOT/old).exists(),('stary katalog',old)
        assert not any(p.startswith(old+'/') for p in shipped)
        checks+=2
    assert not (ROOT/'systems/v10900_gifts.py').exists()
    assert 'systems/gift_runtime.py' in shipped and 'systems/gift_runtime.py' in REQUIRED
    checks+=2
    for package,hashes in [('data/catalog_parts',CATALOG_HASHES),('systems/gift_parts',GIFT_HASHES)]:
        for filename, expected in hashes.items():
            rel=package+'/'+filename
            source=ROOT/rel
            assert source.is_file() and rel in shipped and rel in REQUIRED,rel
            assert hashlib.sha256(source.read_bytes()).hexdigest()==expected,rel
            checks+=1
    # Only v112 release gate can authorize daily/advent gifts.
    assert gift_runtime.DELAY_SECONDS == 120
    assert gift_runtime.TABLE == 'v109_gift_claims'
    checks+=2
    from core import bootstrap_economy_professions as core
    assert core.VERSION=='112.00.0'
    with patch('systems.v11200_activation.enabled',return_value=False):
        with patch.dict(os.environ,{
            'SOULBOUND_V107_STAGING':'1','SOULBOUND_V109_STAGING':'1',
            'SOULBOUND_V110_STAGING':'1','SOULBOUND_V111_STAGING':'1'
        }):
            assert not policy.enabled(), 'old flags bypassed authorization'
        checks+=1
    with patch('systems.v11200_activation.enabled',return_value=True):
        assert policy.enabled(), 'current release gate ignored'
        checks+=1
    with patch.object(core,'VERSION','111.00.0'):
        with patch('systems.v11200_activation.enabled',return_value=True):
            assert not policy.enabled(), 'old version accepted'
        checks+=1
    # Current code has no direct imports of relocated old packages.
    for py in ROOT.rglob('*.py'):
        if 'validation' in py.parts or py.relative_to(ROOT).as_posix() in ('systems/v10900_activation.py','systems/v11100_holiday_activation.py'):
            continue
        tree=ast.parse(py.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): mods=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom): mods=[node.module or '']
            else: continue
            assert not any(m.startswith(('data.catalogs_v109','systems.gifts_v109','systems.v10900_gifts')) for m in mods),py
    checks+=1
    print(f'V112 KATALOGI I PREZENTY: {checks} PASS (byte identity, release authorization, installed payload)')
    return checks

if __name__=='__main__':run()
