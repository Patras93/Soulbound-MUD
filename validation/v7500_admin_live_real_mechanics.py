# -*- coding: utf-8 -*-
"""Disposable SQLite and true runtime-consumer checks for v75."""
import asyncio
import copy
import tempfile
from pathlib import Path
from types import SimpleNamespace

from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems import admin_live_heritage_v7100 as heritage
from systems.live_olc32_finale import ACTIVE as PHASE_ACTIVE, uoss_phase_multiplier
from systems.live_olc33_mechanics import ACTIVE as HEAL_ACTIVE, uoss_restore
from systems.live_olc34_integration import ACTIVE as FURY_ACTIVE, boss_pressure
from core.classes_skills import RACES,CLASSES

async def run():
    checks=0
    def ok(x,n=''):
        nonlocal checks
        assert x,n
        checks+=1
    admin=Fake();db=admin.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    admin.server.live_content_v1204=service
    guest=Fake(False,db);guest.server.live_content_v1204=service
    before=copy.deepcopy(service.draft)
    old_path=heritage.CONFIG_PATH; old_settings=heritage._SETTINGS;old_base=heritage._BASE_REGISTRY
    races0=list(RACES);classes0=list(CLASSES)
    async def call(cmd, who=admin):
        await who.admin_command('live '+cmd)
        return who.messages[-1]
    try:
        with tempfile.TemporaryDirectory() as directory:
            heritage.CONFIG_PATH=Path(directory)/'heritage.json';heritage._SETTINGS=None
            heritage._BASE_REGISTRY=None
            ok('POMOC 35' in await call('pomoc 35'))
            for line in (
                'pomoc 35', 'boss uoss mechaniki karta black_rabite',
                'boss uoss mechaniki plan black_rabite | fazy=75:2:160',
                'boss uoss mechaniki zatwierdz POTWIERDZAM',
                'boss uoss mechaniki cofnij POTWIERDZAM',
                'questy zaleznosci stare usun plan mirella_jewel_gold',
                'questy zaleznosci stare zatwierdz POTWIERDZAM',
            ):
                ok('Nieznana komenda' in await call(line,guest),line)
            ok(service.draft==before)
            ok('skrypt' in (await call('boss uoss lista')).lower())
            ok('aktywne=AUTO' in await call('boss uoss mechaniki karta black_rabite'))
            for line in (
                'boss uoss mechaniki plan nothing | furia=3:120:4',
                'boss uoss mechaniki plan black_rabite | fazy=75:2:160,80:3:220',
                'boss uoss mechaniki plan black_rabite | leczenie=35:1:3',
                'boss uoss mechaniki plan black_rabite | furia=3:200:4',
                'boss uoss mechaniki plan black_rabite | skala=10:130',
                'boss uoss mechaniki plan black_rabite | furia=3:115:4;furia=4:120:4',
                'boss uoss mechaniki plan black_rabite | fazy=75:2:160;extra=1',
                'boss uoss mechaniki plan black_rabite | fazy=75:2:160;leczenie=bad',
            ):
                ok('ADMIN LIVE V75:' in await call(line),line)
                ok(service.draft==before,'bad plan mutated draft '+line)
            command=('boss uoss mechaniki plan black_rabite | '
                     'fazy=75:2:160,40:3:220;leczenie=35:4:3;furia=3:115:4;skala=150:130')
            ok('BOSS UOSS MECHANIKI PLAN' in await call(command))
            ok(service.draft==before)
            ok('zatwierdzono' in await call('boss uoss mechaniki zatwierdz POTWIERDZAM'))
            ok(service.active==before)
            ok(service.draft['v24_rules']['uoss']['black_rabite']['max_hp_percent']==150)
            ok(len(service.draft['v32_rules']['uoss']['black_rabite']['phases'])==2)
            ok('DRAFT=' in await call('boss uoss mechaniki karta black_rabite'))
            # Real combat hooks, not a mock combat loop: use the policy consumers.
            original_phase=copy.deepcopy(PHASE_ACTIVE['uoss']); original_heal=copy.deepcopy(HEAL_ACTIVE['uoss']); original_fury=copy.deepcopy(FURY_ACTIVE['uoss'])
            try:
                for catalog, section in ((PHASE_ACTIVE,'v32_rules'),(HEAL_ACTIVE,'v33_rules'),(FURY_ACTIVE,'v34_rules')):
                    catalog['uoss'].clear();catalog['uoss'].update(service.draft[section]['uoss'])
                template={'uoss_unique_superboss_key':'black_rabite','max_hp':1000}
                mob=SimpleNamespace(hp=300,max_hp=1000)
                phase_results=[uoss_phase_multiplier(mob,template) for _ in range(3)]
                ok(any(value>1 for value in phase_results))
                power_results=[boss_pressure(mob,template) for _ in range(4)]
                ok(any(value>1 for value in power_results))
                mob=SimpleNamespace(hp=300,max_hp=1000)
                heals=[uoss_restore(mob,template) for _ in range(4)]
                ok(heals[3]>0 and mob.hp>300)
            finally:
                for catalog,original in ((PHASE_ACTIVE,original_phase),(HEAL_ACTIVE,original_heal),(FURY_ACTIVE,original_fury)):
                    catalog['uoss'].clear();catalog['uoss'].update(original)
            # Race/classes reversible after editor session loses transient originals.
            ok('RODOWOD PLAN' in await call('rodowod rasa plan Elf | 9 14 8 11 8'))
            ok('RODOWOD ZAPISANO' in await call('rodowod zatwierdz POTWIERDZAM'))
            ok(list(next(row for row in RACES if row[0]=='Elf')[2:])==[9,14,8,11,8])
            if hasattr(admin,'adminlive7100_heritage_originals'):
                del admin.adminlive7100_heritage_originals
            ok('RODOWOD: cofnieto' in await call('rodowod cofnij POTWIERDZAM'))
            ok(RACES==races0)
            ok('RODOWOD PLAN' in await call('rodowod klasa plan Wojownik | Wlocznia Duszy'))
            ok('RODOWOD ZAPISANO' in await call('rodowod zatwierdz POTWIERDZAM'))
            ok('RODOWOD: cofnieto' in await call('rodowod cofnij POTWIERDZAM'))
            ok(CLASSES==classes0)
            # Removing old quest parent is a null-shadow, not a dropped patch.
            ok('STARE USUN PLAN' in await call('questy zaleznosci stare usun plan mirella_jewel_gold'))
            ok(service.draft['quest_edits']==before['quest_edits'])
            ok('zatwierdzono' in await call('questy zaleznosci stare zatwierdz POTWIERDZAM'))
            ok(service.draft['quest_edits']['mirella_jewel_gold']['requires_quest'] is None)
            ok('requires_quest=BRAK' in await call('questy zaleznosci stare karta mirella_jewel_gold'))
            ok('Cofnieto' in await call('questy zaleznosci stare cofnij POTWIERDZAM'))
            ok(service.draft['quest_edits']==before['quest_edits'])
            ok('STARE USUN PLAN' in await call('questy zaleznosci stare usun plan mirella_jewel_gold'))
            ok('zatwierdzono' in await call('questy zaleznosci stare zatwierdz POTWIERDZAM'))
            ok('STARE USUN PLAN' not in await call('questy zaleznosci stare usun plan mirella_jewel_gold'))
            ok(service.draft['quest_edits']['mirella_jewel_gold']['requires_quest'] is None)
            ok(db.conn.execute('SELECT COUNT(*) FROM live_content_history_v1204').fetchone()[0] == 0)
            # No persistence happened before the normal OLC activation path.
            ok(db.conn.execute('SELECT COUNT(*) FROM live_content_v1204').fetchone()[0] == 0)
    finally:
        heritage.CONFIG_PATH=old_path;heritage._SETTINGS=old_settings
        heritage._BASE_REGISTRY=old_base
        RACES[:]=races0;CLASSES[:]=classes0
        service._remove(None)
        db.conn.close()
    return checks

if __name__=='__main__':
    print('V75.00.0 ADMIN LIVE VERIFIED:',asyncio.run(run()),'PASS')
