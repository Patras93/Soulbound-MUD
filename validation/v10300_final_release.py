# -*- coding: utf-8 -*-
"""Final v103 shipping gate: identity, upgrade protection and era integration.

No live database reads, writes or network access.
"""
from pathlib import Path
import ast
import re


def run():
    base=Path(__file__).resolve().parents[1]
    checks=0
    def ok(value, message):
        nonlocal checks
        assert value, message
        checks+=1
    # Bramka Ery v103 pozostaje obowiązkowa dla następców (w tym v104).
    # Weryfikuj rzeczywistą spójną tożsamość, nie sztywną dawną wersję.
    release=(base/'VERSION').read_text(encoding='utf-8').strip()
    ok(tuple(map(int, release.split('.'))) >= (103,0,0),'minimum Era v103')
    bootstrap=(base/'core/bootstrap_economy_professions.py').read_text(encoding='utf-8')
    ok(re.search(r'^VERSION\s*=\s*"'+re.escape(release)+r'"',bootstrap,re.M),'bootstrap version')
    changelog=(base/'CHANGELOG_PL.txt').read_text(encoding='utf-8')
    ok(changelog.startswith('Aktualna paczka: v'+release+'\n'),'changelog version')
    registry=(base/'systems/content_registry.py').read_text(encoding='utf-8')
    titles=re.findall(r'^LATEST_CHANGES_TITLE\s*=\s*"Soulbound v([^\s]+)',registry,re.M)
    ok(titles and titles[-1]==release,'registry version')
    ok('Era Bez Granic' in registry and 'era bez granic' in changelog.casefold(),'release described')
    updater=(base/'aktualizuj_soulbound.py').read_text(encoding='utf-8')
    ok("'era_v10300.json'" in updater,'era admin config survives upgrade')
    ok("'admin_level_caps.json'" in updater,'level caps survive upgrade')
    ok(".endswith(SQLITE_SUFFIXES)" in updater,'SQLite protected')
    ok("if relative.name.lower().endswith(SQLITE_SUFFIXES)" in updater,'reject SQLite in release')
    ok('SOULBOUND_DB' not in changelog[:500],'no secrets in changes')
    ok(not any(base.glob('*.db')),'no player database')
    ok(not any(base.glob('*.db-wal')),'no SQLite WAL')
    required=[
        'world/v10300_era_bez_granic.py',
        'world/v10300_era_raids.py',
        'systems/era_npc_offers_v10300.py',
        'validation/v10300_era_quest_sqlite.py',
        'validation/v10300_era_quest_rewards_runtime.py',
        'validation/v10300_era_raid_phases_runtime.py',
        'validation/v10300_era_tcp_other_raids.py',
        'validation/v10300_era_tcp_raid_journey.py',
        'validation/v10300_era_tcp_fixture_gate.py',
        'validation/v10300_era_crafting_runtime.py',
        'validation/v10300_era_crypt_unlock_runtime.py',
        'SPRAWDZ_RAJD_ERA_V103_TCP.bat',
        'SPRAWDZ_INNE_RAJDY_ERA_V103_TCP.bat',
        'PREDEPLOY_NOWEJ_WERSJI.bat',
        'WDROZ_PO_PREDEPLOY.bat',
    ]
    for item in required:ok((base/item).is_file(),'missing '+item)
    for script in ('predeploy_check.py','predeploy_full.py'):
        source=(base/script).read_text(encoding='utf-8')
        ok('v10300_final_release' in source,'final release gate in '+script)
        ok('v10300_era_quest_rewards_runtime' in source,'rewards gate in '+script)
        ok('v10300_era_raid_party_sqlite' in source,'party gate in '+script)
        ok('v10300_era_tcp_fixture_gate' in source,'safe fixture gate in '+script)
    # Code is inspected without importing a live server or creating files.
    for item in ('world/v10300_era_bez_granic.py','world/v10300_era_raids.py',
                 'systems/era_npc_offers_v10300.py','validation/v10300_final_release.py'):
        ast.parse((base/item).read_text(encoding='utf-8'),filename=item)
        checks+=1
    ok('Nie wdrazaj' not in changelog[:300], 'release is not labeled as a draft')
    return checks

if __name__=='__main__':
    print(f'V103 FINAL RELEASE GATE: {run()} checks PASS',flush=True)
