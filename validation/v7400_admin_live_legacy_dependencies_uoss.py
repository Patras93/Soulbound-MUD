# -*- coding: utf-8 -*-
"""v74: real admin command dispatcher, disposable SQLite, and OLC validation."""
import asyncio
import copy
from types import SimpleNamespace
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_integrity_v4900 import _effective
from validation.v3600_admin_guardian2 import Fake
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

async def run():
    total=0
    def ok(condition, label=''):
        nonlocal total
        assert condition, label
        total += 1
    admin=Fake()
    db=admin.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    admin.server.live_content_v1204=service
    guest=Fake(False,db)
    guest.server.live_content_v1204=service
    original=copy.deepcopy(service.draft)
    active=copy.deepcopy(service.active)
    sql_changes=db.conn.total_changes
    async def call(line, person=admin):
        await person.admin_command('live '+line)
        return person.messages[-1]
    try:
        ok('POMOC 34' in await call('pomoc 34'))
        guest_commands=(
            'pomoc 34','questy zaleznosci stare karta mirella_jewel_gold',
            'questy zaleznosci stare plan mirella_jewel_gold | haldor_crafting_order',
            'questy zaleznosci stare zatwierdz POTWIERDZAM',
            'questy zaleznosci stare cofnij POTWIERDZAM',
            'questy zaleznosci wplyw mirella_jewel_iron',
            'questy zaleznosci sciezka mirella_jewel_gold',
            'boss uoss lista', 'boss uoss karta black_rabite',
        )
        for cmd in guest_commands:
            ok('Nieznana komenda' in await call(cmd,guest), 'guest '+cmd)
        ok(service.draft==original)
        ok('mirella_jewel_silver' in await call('questy zaleznosci stare karta mirella_jewel_gold'))
        ok('mirella_jewel_iron' in await call('questy zaleznosci sciezka mirella_jewel_gold'))
        ok('zalezne 8' in await call('questy zaleznosci wplyw mirella_jewel_iron'))
        ok('BRAK' in await call('questy zaleznosci wplyw mirella_jewel_eternium'))
        for cmd in (
            'questy zaleznosci stare karta brak_takiego_questa',
            'questy zaleznosci stare plan nie_ma | haldor_crafting_order',
            'questy zaleznosci stare plan mirella_jewel_gold | nie_ma',
            'questy zaleznosci stare plan mirella_jewel_gold | mirella_jewel_gold',
            'questy zaleznosci stare plan mirella_jewel_gold | mirella_jewel_silver',
            'questy zaleznosci stare plan mirella_jewel_gold | mirella_jewel_cobalt',
            'questy zaleznosci stare plan mirella_jewel_iron | haldor_crafting_order',
            'questy zaleznosci stare plan mirella_jewel_gold | BRAK',
            'questy zaleznosci stare plan mirella_jewel_gold | haldor_crafting_order | extra',
            'questy zaleznosci stare plan mirella_jewel_gold | bad ID',
            'questy zaleznosci stare plan mirella_jewel_gold | haldor_crafting_order\nX',
            'questy zaleznosci stare plan mirella_jewel_gold | ',
            'questy zaleznosci stare plan  | haldor_crafting_order',
            'questy zaleznosci wplyw bad_id',
            'questy zaleznosci sciezka bad_id',
            'questy zaleznosci wplyw mirella_jewel_gold 0',
            'questy zaleznosci sciezka mirella_jewel_gold -1',
            'questy zaleznosci sciezka mirella_jewel_gold 2',
            'questy zaleznosci wplyw mirella_jewel_iron 99999',
            'boss uoss karta not_a_boss',
            'boss uoss lista 0',
            'boss uoss lista 500',
            'boss uoss lista -1',
            'boss uoss lista 1extra',
            'boss uoss karta black rabite',
            'boss uoss lista 1 2',
            'questy zaleznosci stare zatwierdz POTWIERDZAM',
            'questy zaleznosci stare cofnij POTWIERDZAM',
        ):
            ok('ADMIN LIVE V74' in await call(cmd),cmd)
            ok(service.draft==original, 'no draft mutation for invalid '+cmd)
        ok('QUEST STARE PLAN' in await call('questy zaleznosci stare plan mirella_jewel_gold | haldor_crafting_order'))
        ok(service.draft==original and service.active==active,'plan only')
        ok('zatwierdzono' in await call('questy zaleznosci stare zatwierdz POTWIERDZAM'))
        ok(_effective(service)['mirella_jewel_gold']['requires_quest']=='haldor_crafting_order')
        ok(service.active==active, 'active unchanged')
        ok('haldor_crafting_order' in await call('questy zaleznosci stare karta mirella_jewel_gold'))
        ok('haldor_crafting_order' in await call('questy zaleznosci sciezka mirella_jewel_gold'))
        ok('Cofnieto' in await call('questy zaleznosci stare cofnij POTWIERDZAM'))
        ok(service.draft==original and service.active==active)
        ok('ADMIN LIVE V74' in await call('questy zaleznosci stare cofnij POTWIERDZAM'))
        ok('QUEST STARE PLAN' in await call('questy zaleznosci stare plan mirella_jewel_gold | haldor_crafting_order'))
        ok('anulowano' in await call('questy zaleznosci stare anuluj'))
        ok('ADMIN LIVE V74' in await call('questy zaleznosci stare zatwierdz POTWIERDZAM'))
        ok('QUEST STARE PLAN' in await call('questy zaleznosci stare plan mirella_jewel_gold | haldor_crafting_order'))
        service.draft['quest_edits']['mirella_jewel_gold']={'reward_gold':20}
        ok('ADMIN LIVE V74' in await call('questy zaleznosci stare zatwierdz POTWIERDZAM'))
        service.draft=copy.deepcopy(original)
        ok('QUEST STARE PLAN' in await call('questy zaleznosci stare plan mirella_jewel_gold | haldor_crafting_order'))
        service.active['quest_edits']['mirella_jewel_gold']={'reward_gold':30}
        ok('ADMIN LIVE V74' in await call('questy zaleznosci stare zatwierdz POTWIERDZAM'))
        service.active=copy.deepcopy(active)
        ok('QUEST STARE PLAN' in await call('questy zaleznosci stare plan mirella_jewel_gold | haldor_crafting_order'))
        ok('zatwierdzono' in await call('questy zaleznosci stare zatwierdz POTWIERDZAM'))
        service.draft['quest_edits']['mirella_jewel_gold']['reward_gold']=23
        ok('ADMIN LIVE V74' in await call('questy zaleznosci stare cofnij POTWIERDZAM'))
        service.draft=copy.deepcopy(original)
        ok('brakujacych ID 0' in await call('questy zaleznosci sciezka mirella_jewel_gold'))
        ok('spotkan' in await call('boss uoss lista'))
        ok('Black Rabite' in await call('boss uoss karta black_rabite'))
        ok('Primm' in await call('boss uoss karta black_rabite'))
        ok('Montblanc' in await call('boss uoss karta yiazmat'))
        ok('Dane z katalogu spotkan' in await call('boss uoss karta culex'))
        ok('skrypt' in (await call('boss uoss lista 4')).lower())
        ok(len(UOSS_SUPERBOSS_ENCOUNTERS_V11134)==21)
        for key in UOSS_SUPERBOSS_ENCOUNTERS_V11134:
            ok(('BOSS UOSS KARTA '+key) in await call('boss uoss karta '+key),key)
        # Backward compatibility with the immediately preceding release.
        ok('POMOC 33' in await call('pomoc 33'))
        ok('BOSS FAZY RAPORT' in await call('boss fazy raport goblin_warchief'))
        ok('QUEST ZALEZNOSCI PAKIET PLAN' in await call('questy zaleznosci pakiet plan mirella_jewel_gold | haldor_crafting_order'))
        ok('anulowano' in await call('questy zaleznosci pakiet anuluj'))
        ok('POMOC 32' in await call('pomoc 32'))
        ok('QUEST ZALEZNOSCI' in await call('questy zaleznosci karta mirella_jewel_gold'))
        ok('POMOC 31' in await call('pomoc 31'))
        ok('POMOC 30' in await call('pomoc 30'))
        ok('POMOC 29' in await call('pomoc 29'))
        ok(service.draft==original and service.active==active)
        ok(db.conn.total_changes==sql_changes,'read-only no SQL writes')
    finally:
        db.conn.close()
    return total

if __name__=='__main__':
    print('V74.00.0 LEGACY QUEST AND UOSS:',asyncio.run(run()),'PASS')
