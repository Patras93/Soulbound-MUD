# -*- coding: utf-8 -*-
"""v87 integration: 2 full multi-object plans + native fresh process isolation."""
import asyncio
import copy
import os
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_integrity_v4900 import _effective

async def run():
    counter=0
    def check(test,label=''):
        nonlocal counter
        assert test,label
        counter+=1
    host=Fake();db=host.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    host.server.live_content_v1204=service
    guest=Fake(False,db);guest.server.live_content_v1204=service
    original=copy.deepcopy(service.draft)
    active=copy.deepcopy(service.active)
    async def call(cmd, session=host):
        await session.admin_command('live '+cmd)
        return session.messages[-1]
    try:
        check('POMOC 45' in await call('pomoc 45'))
        check('Nieznana komenda' in await call('pomoc 45',guest))
        check('Nieznana komenda' in await call('questy caly pakiet plan mirella_jewel_gold | stare=BRAK | dodatkowe=BRAK',guest))
        check('Nieznana komenda' in await call('boss uoss zbiorczy plan black_rabite | furia=3:115:4',guest))
        checks=(
          'questy caly pakiet plan nieznany | stare=BRAK | dodatkowe=BRAK',
          'questy caly pakiet plan mirella_jewel_gold | stare=mirella_jewel_gold | dodatkowe=BRAK',
          'questy caly pakiet plan mirella_jewel_gold | stare=nieznany | dodatkowe=BRAK',
          'questy caly pakiet plan mirella_jewel_gold | stare=BRAK | dodatkowe=nieznany',
          'questy caly pakiet plan mirella_jewel_gold | stare=mirella_jewel_iron | dodatkowe=mirella_jewel_iron',
          'questy caly pakiet plan mirella_jewel_gold | stare=BRAK | dodatkowe=mirella_jewel_iron,mirella_jewel_iron',
          'questy caly pakiet plan mirella_jewel_gold | stare= | dodatkowe=BRAK',
          'questy caly pakiet plan mirella_jewel_gold | stare=BRAK | dodatkowe=',
          'questy caly pakiet plan mirella_jewel_gold | stare=BRAK | dodatkowe=BRAK; mirella_jewel_gold | stare=BRAK | dodatkowe=BRAK',
          'questy caly pakiet plan mirella_jewel_iron | stare=mirella_jewel_gold | dodatkowe=BRAK',
        )
        for cmd in checks:
            check('ADMIN LIVE V87' in await call(cmd),cmd)
            check(service.draft==original,cmd+' unexpectedly mutated draft')
        # Single transaction repairs both link types across multiple quest IDs.
        good='questy caly pakiet plan mirella_jewel_gold | stare=BRAK | dodatkowe=haldor_crafting_order; mirella_jewel_iron | stare=BRAK | dodatkowe=BRAK'
        check('CALY PAKIET PLAN' in await call(good))
        check(service.draft==original)
        check('zatwierdzono' in await call('questy caly pakiet zatwierdz POTWIERDZAM'))
        catalog=_effective(service)
        check(catalog['mirella_jewel_gold']['requires_quest'] is None)
        check(catalog['mirella_jewel_gold']['requires_quests']==['haldor_crafting_order'])
        check(catalog['mirella_jewel_iron']['requires_quests']==[])
        check(service.active==active)
        check('Cofnieto' in await call('questy caly pakiet cofnij POTWIERDZAM'))
        check(service.draft==original)
        check('ADMIN LIVE V87' in await call('questy caly pakiet cofnij POTWIERDZAM'))
        check('CALY PAKIET PLAN' in await call(good))
        service.draft.setdefault('quest_edits',{}).setdefault('mirella_jewel_gold',{})['reward_silver']=123
        check('ADMIN LIVE V87' in await call('questy caly pakiet zatwierdz POTWIERDZAM'))
        service.draft=copy.deepcopy(original)
        check('CALY PAKIET PLAN' in await call(good))
        check('anulowany' in await call('questy caly pakiet anuluj'))
        check('ADMIN LIVE V87' in await call('questy caly pakiet zatwierdz POTWIERDZAM'))
        # Scripted UOSS native combat rules; no need for a special NPC.
        from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
        bosses=list(UOSS_SUPERBOSS_ENCOUNTERS_V11134)
        check('black_rabite' in bosses)
        other=next(x for x in bosses if x!='black_rabite')
        invalid=(
          'boss uoss zbiorczy plan missing | furia=3:115:4',
          'boss uoss zbiorczy plan black_rabite | furia=3:115:4+furia=3:115:4',
          'boss uoss zbiorczy plan black_rabite | nieznane=1:2',
          'boss uoss zbiorczy plan black_rabite | fazy=80:2:160,85:3:210',
          'boss uoss zbiorczy plan black_rabite | skala=0:100',
          'boss uoss zbiorczy plan black_rabite | furia=3:115:4;black_rabite | skala=150:130',
        )
        for cmd in invalid:
            check('ADMIN LIVE V87' in await call(cmd),cmd)
            check(service.draft==original)
        boss_cmd=(f'boss uoss zbiorczy plan black_rabite | fazy=75:2:160,40:3:220+leczenie=35:4:3+furia=3:115:4+skala=150:130;'
                  f'{other} | skala=120:125+furia=3:110:3')
        check('ZBIORCZY PLAN' in await call(boss_cmd))
        check(service.draft==original)
        check('zatwierdzono' in await call('boss uoss zbiorczy zatwierdz POTWIERDZAM'))
        check(service.draft['v24_rules']['uoss']['black_rabite']['max_hp_percent']==150)
        check(service.draft['v34_rules']['uoss'][other]['stack_percent']==110)
        check(len(service.draft['v32_rules']['uoss']['black_rabite']['phases'])==2)
        check(service.active==active)
        check('Cofnieto' in await call('boss uoss zbiorczy cofnij POTWIERDZAM'))
        check(service.draft==original)
        check('ZBIORCZY PLAN' in await call(boss_cmd))
        check('anulowany' in await call('boss uoss zbiorczy anuluj'))
        check('ADMIN LIVE V87' in await call('boss uoss zbiorczy zatwierdz POTWIERDZAM'))
        # Old edit commands still route unchanged.
        check('POMOC 35' in await call('pomoc 35'))
        check('POMOC 34' in await call('pomoc 34'))
        check('POMOC 33' in await call('pomoc 33'))
        # Fresh native arena cannot consult even a deliberately unavailable DB.
        from systems import admin_live_native_arena_v8600 as lab
        from core.bootstrap_economy_professions import VERSION
        from validation.release_contracts import release_valid
        check(release_valid(VERSION, '87.00.0'), 'v87 minimum release and exact packaged engine version')
        class NoDB:
            @property
            def db(self):
                raise AssertionError('Arena fresh MUST NOT access DB')
        old=lab._loopback_port_free
        class RejectSpawn(Exception):pass
        # Verify fresh branch without launching: fail at a known safe chokepoint
        # after input validation, *before* any read of the source DB.
        def fake_port(port):
            raise RejectSpawn
        lab._loopback_port_free=fake_port
        try:
            try:
                lab.arena_start(NoDB(),fresh=True)
            except RejectSpawn:pass  # AUDIT_INTENTIONAL_PASS: deliberately rejected port probe
            else:raise AssertionError('No port probe in fresh mode')
            check(True)
        finally:
            lab._loopback_port_free=old
        check('pusta' in lab.HELP)
        check(service.draft==original and service.active==active)
    finally:
        db.conn.close()
    print(f'ADMIN LIVE v87 BIG UPDATE: {counter} PASS',flush=True)
    return counter

if __name__=='__main__':
    asyncio.run(run())
