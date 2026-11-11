# -*- coding: utf-8 -*-
"""v108: PREDEPLOY TCP private-fixture authorization; no server or user DB."""
from __future__ import annotations
import os
from pathlib import Path
import tempfile
from systems.v10800_predeploy_isolation import authorized_predeploy_test

ROOT = Path(__file__).resolve().parents[1]


def run():
    checks=0
    def ck(value, desc):
        nonlocal checks
        assert value,desc
        checks+=1
    with tempfile.TemporaryDirectory(prefix='sb108_guard_regression_') as d:
        temp=Path(d).resolve()
        # TEMP is replaceable so tests are independent of Windows TEMP naming.
        worker=temp/'soulbound-predeploy-workers-abc'/'candidate-0'
        first=temp/'soulbound_predeploy_new'/'Soulbound-MUD'
        nested=temp/'sb103-real-tcp-123'/'server_source'
        env={'SOULBOUND_V108_PREDEPLOY':'1','SOULBOUND_HOST':'127.0.0.1',
             'SOULBOUND_PORT':'58031','SOULBOUND_DB':str(temp/'production.db')}
        samples=(
            (worker,temp/'soulbound-predeploy-stage-123'/'audit.sqlite'),
            (first,temp/'soulbound-predeploy-stage-123'/'audit.sqlite'),
            (worker,temp/'soulbound-tcp5-123'/'five_players.sqlite'),
            (worker,temp/'soulbound-tcp5-v105-boss-123'/'five_players.sqlite'),
            (worker,temp/'sb-ultra-5-tcp-123'/'stress.db'),
            (worker,temp/'sb-ultimate-tcp-waves-123'/'wave.sqlite'),
            (worker,temp/'sb104_tcp_lab_123'/'tcp_test.sqlite'),
            (nested,nested/'five_players.sqlite'),
            (temp/'sb103-other-raids-123'/'private_game',
             temp/'sb103-other-raids-123'/'private_game'/'five_players.sqlite'),
        )
        uoss=temp/'Soulbound_UOSS_REAL_8af4'/'gra'
        samples += ((uoss,uoss/'soulbound.db'),)
        for root,db in samples:
            ck(authorized_predeploy_test(root,db,env,temp),
               f'Expected private fixture denied: {root} / {db}')
            for override in (
                {'SOULBOUND_V108_PREDEPLOY':'0'},
                {'SOULBOUND_V108_PREDEPLOY':''},
                {'SOULBOUND_HOST':'0.0.0.0'},
                {'SOULBOUND_HOST':'localhost'},
                {'SOULBOUND_PORT':'4000'},
                {'SOULBOUND_PORT':'0'},
                {'SOULBOUND_PORT':'invalid'},
            ):
                ck(not authorized_predeploy_test(root,db,{**env,**override},temp),
                   'Unsafe TCP configuration was admitted')
        db=temp/'soulbound-tcp5-123'/'five_players.sqlite'
        for invalid in (
            '/opt/Soulbound-MUD',
            str(temp/'production'),
            str(temp/'soulbound-predeploy-workers-123'/'not-a-candidate'),
            str(temp/'soulbound-predeploy-workers-123'/'candidate-0'/'subproject'),
        ):
            ck(not authorized_predeploy_test(invalid,db,env,temp),
               'Unrecognized source root authorized')
        for invalid in (
            '/outside/soulbound.db',
            str(temp/'soulbound.db'),
            str(temp/'soulbound-predeploy-stage-123'/'soulbound.db'),
            str(temp/'soulbound-tcp5-123'/'soulbound.db'),
            str(temp/'soulbound-predeploy-stage-123'/'five_players.sqlite'),
            str(temp/'sb-ultra-5-tcp-123'/'five_players.sqlite'),
        ):
            ck(not authorized_predeploy_test(worker,invalid,env,temp),
               'Nonfixture SQLite authorized: '+invalid)
        # UOSS authorization is strictly bound to its private database path.
        for invalid in (
            uoss/'production.db', uoss/'other.sqlite', uoss/'..'/'soulbound.db',
            temp/'live_install'/'soulbound.db',
            temp/'Soulbound_UOSS_REAL_8af4'/'other'/'soulbound.db',
        ):
            ck(not authorized_predeploy_test(uoss, invalid, env, temp),
               'UOSS accepted non-private/mismatched DB: '+str(invalid))
        ck(not authorized_predeploy_test(temp/'Soulbound_UOSS_REAL_8af4'/'other',
                                         uoss/'soulbound.db',env,temp),
           'UOSS accepted unrecognized source root')
        # The launcher MUST NOT transfer credentials or enable predeploy mode
        # unless its parent test was already explicitly marked as PREDEPLOY.
        from unittest.mock import patch
        from arena_real_izolowana import _private_env
        with patch.dict(os.environ, {'SOULBOUND_V108_PREDEPLOY':'1',
                                     'SOULBOUND_CONTROL_TOKEN':'never-copy',
                                     'SOULBOUND_DB':'C:/production/soulbound.db'}):
            safe=_private_env(uoss, 58031)
        ck(safe.get('SOULBOUND_V108_PREDEPLOY')=='1',
           'UOSS child lost inherited PREDEPLOY marker')
        ck(safe.get('SOULBOUND_CONTROL_TOKEN') is None,
           'Private UOSS inherited control token')
        ck(safe['SOULBOUND_DB']==str(uoss/'soulbound.db'),
           'Private UOSS inherited production DB path')
        with patch.dict(os.environ, {'SOULBOUND_V108_PREDEPLOY':'0'}):
            ck('SOULBOUND_V108_PREDEPLOY' not in _private_env(uoss, 58031),
               'UOSS elevated an ordinary runtime to PREDEPLOY')
        # Actual candidate source is neither TEMP nor entitled to test bypass.
        ck(not authorized_predeploy_test(ROOT,db,env,temp),
           'Working or production source must not be test-authorized')
        # Check wiring and hash-bound source: test-only entrypoint is not a
        # standalone production bypass and is part of updater's hashed surface.
        server=(ROOT/'server/mud_server.py').read_text(encoding='utf-8')
        from systems.v10800_activation import REQUIRED
        ck('authorized_predeploy_test' in server, 'Runtime does not enforce guarded helper')
        ck('systems/v10800_predeploy_isolation.py' in REQUIRED, 'Missing hash-bound helper')
        for p in ('validation/predeploy_ultra_v2327.py',
                  'validation/predeploy_ultimate_v2328.py'):
            code=(ROOT/p).read_text(encoding='utf-8')
            ck("SOULBOUND_V108_PREDEPLOY=os.environ.get('SOULBOUND_V108_PREDEPLOY','')" in code,
               'Legacy TCP test did not explicitly re-propagate predeploy flag')
        from core.bootstrap_economy_professions import VERSION
        ck((ROOT/'VERSION').read_text(encoding='utf-8-sig').strip() == VERSION, 'Historical executable version identity')
        from systems.content_registry import LATEST_CHANGES_TITLE
        ck(LATEST_CHANGES_TITLE.startswith(f'Soulbound v{VERSION} '),
           'Game changes command version identity')
    return checks


if __name__=='__main__':
    print(f'V108 WINDOWS TCP ISOLATION: {run()} checks PASS',flush=True)
