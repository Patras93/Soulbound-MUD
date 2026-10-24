# -*- coding: utf-8 -*-
"""v72 regression on memory-only fake database; never opens production DB."""
import asyncio
import copy
from types import SimpleNamespace
from systems.live_content_v1204 import LiveContentV1204
from validation.v3600_admin_guardian2 import Fake
from systems.admin_live_integrity_v4900 import _effective
from systems.live_olc17_quest_dependencies import quest_requirements

async def run():
    passed=0
    def ok(value, label=''):
        nonlocal passed
        assert value,label
        passed+=1
    owner=Fake()
    db=owner.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    owner.server.live_content_v1204=service
    guest=Fake(False,db);guest.server.live_content_v1204=service
    draft=copy.deepcopy(service.draft)
    active=copy.deepcopy(service.active)
    def unchanged():return service.draft == draft and service.active == active
    async def cmd(text, actor=owner):
        await actor.admin_command('live '+text)
        return actor.messages[-1]
    try:
        ok('POMOC 32' in await cmd('pomoc 32'))
        for command in (
            'pomoc 32', 'questy zaleznosci karta mirella_jewel_gold',
            'questy zaleznosci plan mirella_jewel_gold | haldor_crafting_order',
            'questy zaleznosci zatwierdz POTWIERDZAM',
            'boss fazy zestaw goblin_warchief 5',
            'boss fazy ustaw goblin_warchief 1 hp_percent | 85',
            'postacie pakiet plan Friend | strength=20; dexterity=22',
            'postacie pakiet zatwierdz POTWIERDZAM'):
            ok('Nieznana komenda' in await cmd(command,guest),command)
        ok(unchanged(),'guest non-mutation')
        ok('mirella_jewel_silver' in await cmd('questy zaleznosci karta mirella_jewel_gold'))
        for s in (
            'questy zaleznosci plan nope | haldor_crafting_order',
            'questy zaleznosci plan mirella_jewel_gold | nope',
            'questy zaleznosci plan mirella_jewel_gold | mirella_jewel_gold',
            'questy zaleznosci plan mirella_jewel_gold | mirella_jewel_iron,mirella_jewel_iron',
            'questy zaleznosci plan mirella_jewel_gold | ',
            'questy zaleznosci plan mirella_jewel_iron | mirella_jewel_gold',
        ):
            ok('ADMIN LIVE V72:' in await cmd(s),s)
            ok(unchanged(),s+' mutation')
        ok('QUEST ZALEZNOSCI PLAN' in await cmd('questy zaleznosci plan mirella_jewel_gold | haldor_crafting_order'))
        ok(unchanged(),'quest plan no mutation')
        ok('zatwierdzono' in await cmd('questy zaleznosci zatwierdz POTWIERDZAM'))
        ok('haldor_crafting_order' in quest_requirements(_effective(service)['mirella_jewel_gold']))
        ok('mirella_jewel_silver' in quest_requirements(_effective(service)['mirella_jewel_gold']))
        ok(service.active==active,'no live quest impact')
        ok('Cofnieto' in await cmd('questy zaleznosci cofnij POTWIERDZAM'))
        ok(unchanged(),'quest undo')
        ok('ADMIN LIVE V72:' in await cmd('questy zaleznosci zatwierdz POTWIERDZAM'))
        ok('QUEST ZALEZNOSCI PLAN' in await cmd('questy zaleznosci plan mirella_jewel_gold | BRAK'))
        ok('anulowano' in await cmd('questy zaleznosci anuluj'))
        ok(unchanged())
        for bad in ('boss fazy zestaw black_rabite 5',
                    'boss fazy zestaw goblin_warchief 6',
                    'boss fazy ustaw goblin_warchief 1 hp_percent | 0',
                    'boss fazy ustaw goblin_warchief 2 hp_percent | 90',
                    'boss fazy ustaw goblin_warchief 1 attack_multiplier | 99',
                    'boss fazy ustaw goblin_warchief 1 duration_seconds | 0',
                    'boss fazy ustaw goblin_warchief 1 message | ',
                    'boss fazy ustaw goblin_warchief 1 cooldown | 4',
                    'boss fazy ustaw goblin_warchief 0 hp_percent | 85'):
            ok('ADMIN LIVE V72:' in await cmd(bad),bad)
            ok(unchanged(),'boss invalid left draft clean')
        ok('BOSS FAZY PLAN' in await cmd('boss fazy zestaw goblin_warchief 5'))
        ok(unchanged())
        ok('zatwierdzono' in await cmd('boss fazy zatwierdz POTWIERDZAM'))
        ok(len(service.draft['mob_edits']['goblin_warchief']['olc_boss_phases'])==5)
        ok(service.active==active)
        ok('Cofnieto' in await cmd('boss fazy cofnij POTWIERDZAM'))
        ok(unchanged())
        ok('BOSS FAZY PLAN' in await cmd('boss fazy ustaw goblin_warchief 1 hp_percent | 85'))
        ok(unchanged())
        ok('zatwierdzono' in await cmd('boss fazy zatwierdz POTWIERDZAM'))
        ok(service.draft['mob_edits']['goblin_warchief']['olc_boss_phases'][0]['hp_percent']==85)
        ok('Cofnieto' in await cmd('boss fazy cofnij POTWIERDZAM'))
        ok(unchanged())
        for f in ('strength','dexterity','constitution','intelligence','willpower','charisma'):
            db.conn.execute(f'ALTER TABLE characters ADD COLUMN {f} INT NOT NULL DEFAULT 10')
        db.conn.execute('ALTER TABLE characters ADD COLUMN deaths INT NOT NULL DEFAULT 0')
        db.conn.commit()
        initial_row=db.conn.execute('SELECT strength,dexterity,character_level FROM characters WHERE name="Friend"').fetchone()
        ok(initial_row['strength']==10 and initial_row['dexterity']==10)
        for bad in (
            'postacie pakiet plan Friend | exp=9999',
            'postacie pakiet plan Friend | level=9999',
            'postacie pakiet plan Friend | gold=9999',
            'postacie pakiet plan Friend | strength=-10',
            'postacie pakiet plan Friend | strength=0',
            'postacie pakiet plan Friend | deaths=-1',
            'postacie pakiet plan Friend | strength=22; strength=33',
            'postacie pakiet plan Friend | strength=1000000001',
            'postacie pakiet plan Tester | strength=40',
        ):
            ok('ADMIN LIVE V72:' in await cmd(bad),bad)
        ok('POSTAC PAKIET PLAN' in await cmd('postacie pakiet plan Friend | strength=42; dexterity=55; deaths=0'))
        ok(db.conn.execute('SELECT strength,dexterity FROM characters WHERE name="Friend"').fetchone()['strength']==10)
        ok('POSTAC PAKIET ZAPISANO' in await cmd('postacie pakiet zatwierdz POTWIERDZAM'))
        row=db.conn.execute('SELECT strength,dexterity,character_level FROM characters WHERE name="Friend"').fetchone()
        ok(row['strength']==42 and row['dexterity']==55 and row['character_level']==initial_row['character_level'])
        ok(db.conn.execute("SELECT count(*) FROM admin_actions_v1224 WHERE action='admin_live_v7200_batch'").fetchone()[0]==1)
        ok('POSTAC PAKIET COFNIETO' in await cmd('postacie pakiet cofnij POTWIERDZAM'))
        row=db.conn.execute('SELECT strength,dexterity FROM characters WHERE name="Friend"').fetchone()
        ok(row['strength']==10 and row['dexterity']==10)
        ok(db.conn.execute("SELECT count(*) FROM admin_actions_v1224 WHERE action='admin_live_v7200_undo'").fetchone()[0]==1)
        ok('ADMIN LIVE V72:' in await cmd('postacie pakiet cofnij POTWIERDZAM'))
        ok('POSTAC PAKIET PLAN' in await cmd('postacie pakiet plan Friend | strength=30'))
        db.conn.execute('UPDATE characters SET strength=31 WHERE name="Friend"');db.conn.commit()
        ok('ADMIN LIVE V72:' in await cmd('postacie pakiet zatwierdz POTWIERDZAM'))
        ok(db.conn.execute('SELECT strength FROM characters WHERE name="Friend"').fetchone()[0]==31)
        ok('POSTAC PAKIET PLAN' in await cmd('postacie pakiet plan Friend | strength=30'))
        ok('anulowano' in await cmd('postacie pakiet anuluj'))
        ok('ADMIN LIVE V72:' in await cmd('postacie pakiet zatwierdz POTWIERDZAM'))
        ok(unchanged(),'no world changes')
    finally:
        db.conn.close()
    return passed

if __name__=='__main__':
    print('V72.00.0 ADVANCEMENT:',asyncio.run(run()),'PASS')
