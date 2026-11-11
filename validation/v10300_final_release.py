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
    ok((base/'VERSION').read_text(encoding='utf-8-sig').strip()==release,'canonical version')
    registry=(base/'systems/content_registry.py').read_text(encoding='utf-8')
    titles=re.findall(r'^LATEST_CHANGES_TITLE\s*=\s*"Soulbound v([^\s]+)',registry,re.M)
    ok(titles and titles[-1]==release,'registry version')
    ok('LATEST_CHANGES_TITLE' in registry and 'Soulbound v' in registry,'live release history registry available')
    updater=(base/'aktualizuj_soulbound.py').read_text(encoding='utf-8')
    ok("'era_v10300.json'" in updater,'era admin config survives upgrade')
    ok("'admin_level_caps.json'" in updater,'level caps survive upgrade')
    ok(".endswith(SQLITE_SUFFIXES)" in updater,'SQLite protected')
    ok("if relative.name.lower().endswith(SQLITE_SUFFIXES)" in updater,'reject SQLite in release')
    ok(not (base/'LIVE_CONTENT/release_current.json').exists(),'approval marker not bundled')
    ok(not any(base.glob('*.db')),'no player database')
    ok(not any(base.glob('*.db-wal')),'no SQLite WAL')
    required=[
        'world/holiday_expareas.py',
        'systems/holiday/calendar.py',
        'systems/v11100_holiday_activation.py',
        'systems/holiday/challenges.py',
        'systems/holiday/prizes.py',
        'systems/holiday/combat.py',
        'validation/v11100_release_suite.py',
        'validation/v11100_release_activation_regression.py',
        'validation/v11100_holiday_combat_regression.py',
        'validation/v11100_holiday_prizes_regression.py',
        'validation/v11100_release_readiness.py',
        'PREDEPLOY_NOWEJ_WERSJI.bat',
        'WDROZ_PO_PREDEPLOY.bat',
    ]
    for item in required:ok((base/item).is_file(),'missing '+item)
    for historical in ('SPRAWDZ_RAJD_ERA_V103_TCP.bat',
                       'SPRAWDZ_INNE_RAJDY_ERA_V103_TCP.bat'):
        if tuple(map(int, release.split('.'))) >= (110, 0, 0):
            ok(not (base/historical).exists(), 'retired root BAT returned: '+historical)
        else:
            ok((base/historical).is_file(), 'missing historical BAT '+historical)
    for script in ('predeploy_check.py','predeploy_full.py'):
        source=(base/script).read_text(encoding='utf-8')
        ok('v10300_final_release' in source,'final release gate in '+script)
        ok('v10300_era_quest_rewards_runtime' in source,'rewards gate in '+script)
        ok('v10300_era_raid_party_sqlite' in source,'party gate in '+script)
        ok('v10300_era_tcp_fixture_gate' in source,'safe fixture gate in '+script)
    # Code is inspected without importing a live server or creating files.
    for item in ('world/holiday_expareas.py','systems/holiday/calendar.py',
                 'systems/v11100_holiday_activation.py','validation/v10300_final_release.py'):
        ast.parse((base/item).read_text(encoding='utf-8'),filename=item)
        checks+=1
    # The historical v103 shipping gate is also executed BEFORE v110's actual
    # Windows approval.  A v110 staging ZIP MUST be unmistakably non-deployable;
    # the old v103 final-release wording must not force an unsafe claim here.
    if release.startswith('110.'):
        ok(not (base/'LIVE_CONTENT/release_current.json').exists(), 'staging cannot contain approval marker')
    else:
        ok(not (base/'LIVE_CONTENT/release_current.json').exists(), 'staging cannot contain approval marker')
    return checks

if __name__=='__main__':
    print(f'V103 FINAL RELEASE GATE: {run()} checks PASS',flush=True)
