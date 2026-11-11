# -*- coding: utf-8 -*-
"""v112: 12 realm source modules, full ID invariants, install closure."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_SHA={'__init__.py': '46b1485c5a84f5700ce37c2ee3e6a89666f71ea0f6d6ba79084f49db7722b606', 'archipelag_sygnalow.py': 'cb69592beab85f83665e9a359ecffce9e3f0c2f6758608dd89d697a9b0bd5f99', 'bazylika_glosow.py': '96246eab84e098e86e89ffdbf58407958731c44e47495146771f9ca1ddf483be', 'delta_przyplywow.py': '269a0ba74d345955da13802d57a40e2c2de695bb06538ff056fdd25e22ee6d3a', 'entry.py': 'e583b3f07fb5fbfe9eacdfb6740626dcb4fbd4266d7f8f8ead3f3931dc99a1b0', 'forteca_slonc.py': '120056f13882abdf2fe9b62e948c952e59ab93ed3f93351b72b99e6d66a9389f', 'kanion_mechanizmow.py': '9449fa21c6fc6ca88e7949241cbad1c1e8d33e511615acdfbeadee15c2f3ce78', 'ogrod_zorz.py': '42709d6d71d4cfb584379e5b680804c52ee93172423c8b713f3fd32a906630fb', 'pustkowie_luster.py': 'aa5bd014869259300656443ab812c93548d5c1b326c808a42c4402e7fbdda7d2', 'puszcza_zarodnikow.py': '7f333462e829f666e831d29350d669666f7e4de88456b7d7c5ce112c91c398da', 'serce_kontynentu.py': 'b37aea342f2b0e36f0d6cc3d83cb1822a3e40c796d5e24160ca0f05819b52131', 'szczeliny_swiatla.py': 'c4d9cc8ec8e49f40afb1f9cf3584486419fe713964222fd3e3e9729ade1c3072', 'wulkan_popiolu.py': '3a0388fc616451a962822e7377bff4216e280968410f041b5e2600b2d6ba741b', 'ziemie_nocy.py': '7e5368dee7d8fa96e8a452d5e7d8dc46ac29b0c57b2ecb5b510bd167db1c9808'}
EXPECTED_IDS_SHA='7454df5884cf9e2f166ef0266e1899d11fa0425d0848628d7d18febd3ba9948c'
EXPECTED_REGIONS_SHA='a3c25678bd442f97444f90f3da32c82978cc1cb99484ae90c58ce186d5a4ac11'


def run():
    from aktualizuj_soulbound import v111_live_release_mapping
    from systems.v11200_activation import REQUIRED
    from world.v11000_realm_index import REGIONS
    from world.v11000_realms import planned_ids
    source=ROOT/'world/realms'
    assert not (ROOT/'world/realms_v110').exists(), 'Legacy realms directory remains in candidate'
    shipped={x.as_posix() for x in v111_live_release_mapping({p.relative_to(ROOT):None for p in ROOT.rglob('*') if p.is_file()})}
    checks=1
    for name,digest in EXPECTED_SHA.items():
        p=source/name
        rel='world/realms/'+name
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,rel
        assert rel in shipped and rel in REQUIRED,('omitted installed realm module',rel)
        checks+=2
    assert len(REGIONS)==12 and len({r[0] for r in REGIONS})==12
    assert hashlib.sha256(repr(REGIONS).encode()).hexdigest()==EXPECTED_REGIONS_SHA
    checks+=2
    ids=planned_ids()
    assert {k:len(v) for k,v in ids.items()} == {'rooms':360,'mobs':184,'npcs':48,'quests':700,'items':72,'recipes':12}
    blob=json.dumps({k:sorted(v) for k,v in sorted(ids.items())},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(blob).hexdigest()==EXPECTED_IDS_SHA
    checks+=2
    for p in ROOT.rglob('*.py'):
        if p==Path(__file__):continue
        text=p.read_text(encoding='utf-8-sig')
        assert 'world.realms_v110' not in text and 'world/realms_v110' not in text,p
    checks+=1
    print(f'V112 KRAINY: {checks} PASS; 12 krain; 700 questow; 1376 ID; zestaw instalacyjny kompletny')
    return checks

if __name__=='__main__':run()
