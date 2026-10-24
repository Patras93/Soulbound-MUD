# -*- coding: utf-8 -*-
"""v73 disposable in-memory SQLite, real dispatcher and actual OLC validators."""
import asyncio
import copy
from types import SimpleNamespace
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_integrity_v4900 import _effective
from validation.v3600_admin_guardian2 import Fake

async def run():
    count = 0
    def ok(condition, detail=''):
        nonlocal count
        assert condition,detail
        count += 1
    admin = Fake()
    db = admin.server.db
    service = LiveContentV1204(SimpleNamespace(conn=db.conn))
    admin.server.live_content_v1204 = service
    guest = Fake(False,db)
    guest.server.live_content_v1204 = service
    draft,active = copy.deepcopy(service.draft),copy.deepcopy(service.active)
    async def call(cmd,who=admin):
        await who.admin_command('live '+cmd)
        return who.messages[-1]
    try:
        ok('POMOC 33' in await call('pomoc 33'))
        for raw in (
            'pomoc 33',
            'questy zaleznosci pakiet plan mirella_jewel_gold | BRAK',
            'questy zaleznosci pakiet zatwierdz POTWIERDZAM',
            'questy zaleznosci pakiet cofnij POTWIERDZAM',
            'boss fazy pakiet plan goblin_warchief | 1.hp_percent=85',
            'boss fazy pakiet zatwierdz POTWIERDZAM',
            'boss fazy raport goblin_warchief',
            'boss uoss ochrona black_rabite',
        ):
            ok('Nieznana komenda' in await call(raw,guest), 'guest '+raw)
        ok(service.draft==draft and service.active==active)
        for invalid in (
            'questy zaleznosci pakiet plan nope | BRAK',
            'questy zaleznosci pakiet plan mirella_jewel_gold | nope',
            'questy zaleznosci pakiet plan mirella_jewel_gold | mirella_jewel_gold',
            'questy zaleznosci pakiet plan mirella_jewel_gold | ',
            'questy zaleznosci pakiet plan mirella_jewel_gold | BRAK ; mirella_jewel_gold | BRAK',
            'questy zaleznosci pakiet plan mirella_jewel_gold | mirella_jewel_iron; mirella_jewel_iron | mirella_jewel_gold',
            'questy zaleznosci pakiet plan mirella_jewel_iron | mirella_jewel_gold',
            'questy zaleznosci pakiet plan mirella_jewel_gold | mirella_jewel_iron,mirella_jewel_iron',
        ):
            ok('ADMIN LIVE V73' in await call(invalid),invalid)
            ok(service.draft==draft and service.active==active,'no mutation')
        ok('PAKIET PLAN' in await call('questy zaleznosci pakiet plan mirella_jewel_gold | haldor_crafting_order; mirella_jewel_iron | BRAK'))
        ok(service.draft==draft)
        ok('zatwierdzono' in await call('questy zaleznosci pakiet zatwierdz POTWIERDZAM'))
        ok('haldor_crafting_order' in _effective(service)['mirella_jewel_gold']['requires_quests'])
        ok(service.active==active)
        ok('Cofnieto' in await call('questy zaleznosci pakiet cofnij POTWIERDZAM'))
        ok(service.draft==draft)
        ok('ADMIN LIVE V73' in await call('questy zaleznosci pakiet cofnij POTWIERDZAM'))
        ok('PAKIET PLAN' in await call('questy zaleznosci pakiet plan mirella_jewel_gold | haldor_crafting_order'))
        service.draft['quest_edits']['mirella_jewel_gold']={'reward_silver':100}
        ok('ADMIN LIVE V73' in await call('questy zaleznosci pakiet zatwierdz POTWIERDZAM'))
        service.draft=copy.deepcopy(draft)
        for invalid in (
            'boss fazy pakiet plan black_rabite | 1.hp_percent=90',
            'boss fazy pakiet plan goblin_warchief | 5.hp_percent=90',
            'boss fazy pakiet plan goblin_warchief | 1.hp_percent=0',
            'boss fazy pakiet plan goblin_warchief | 1.hp_percent=90; 2.hp_percent=92',
            'boss fazy pakiet plan goblin_warchief | 1.attack_multiplier=3.01',
            'boss fazy pakiet plan goblin_warchief | 1.duration_seconds=121',
            'boss fazy pakiet plan goblin_warchief | 1.message=',
            'boss fazy pakiet plan goblin_warchief | 1.cooldown=8',
            'boss fazy pakiet plan goblin_warchief | 1.hp_percent=86; 1.hp_percent=80',
        ):
            ok('ADMIN LIVE V73' in await call(invalid),invalid)
            ok(service.draft==draft,'invalid boss no mutation')
        ok('BOSS FAZY RAPORT' in await call('boss fazy raport goblin_warchief'))
        ok('edytowalne NIE' in await call('boss uoss ochrona black_rabite'))
        ok('edytowalne TAK' in await call('boss uoss ochrona goblin_warchief'))
        ok('PAKIET PLAN' in await call('boss fazy pakiet plan goblin_warchief | 1.hp_percent=85; 2.attack_multiplier=1.85; 3.message=Ostatni atak'))
        ok(service.draft==draft)
        ok('zatwierdzono' in await call('boss fazy pakiet zatwierdz POTWIERDZAM'))
        phases=service.draft['mob_edits']['goblin_warchief']['olc_boss_phases']
        ok(phases[0]['hp_percent']==85 and phases[1]['attack_multiplier']==1.85 and phases[2]['message']=='Ostatni atak')
        ok('Ostatni atak' in await call('boss fazy raport goblin_warchief'))
        ok('Cofnieto' in await call('boss fazy pakiet cofnij POTWIERDZAM'))
        ok(service.draft==draft and service.active==active)
        ok('PAKIET PLAN' in await call('boss fazy pakiet plan goblin_warchief | 1.hp_percent=88'))
        ok('anulowano' in await call('boss fazy pakiet anuluj'))
        ok('ADMIN LIVE V73' in await call('boss fazy pakiet zatwierdz POTWIERDZAM'))
        # Older single-operation commands remain available.
        ok('QUEST ZALEZNOSCI PLAN' in await call('questy zaleznosci plan mirella_jewel_gold | BRAK'))
        ok('anulowano' in await call('questy zaleznosci anuluj'))
        ok('BOSS FAZY PLAN' in await call('boss fazy ustaw goblin_warchief 1 hp_percent | 85'))
        ok('zatwierdzono' in await call('boss fazy zatwierdz POTWIERDZAM'))
        ok('Cofnieto' in await call('boss fazy cofnij POTWIERDZAM'))
        ok(service.draft==draft and service.active==active)
    finally:
        db.conn.close()
    return count

if __name__ == '__main__':
    print('V73.00.0 QUEST BOSS BATCHES:',asyncio.run(run()),'PASS')
