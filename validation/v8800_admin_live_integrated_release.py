# -*- coding: utf-8 -*-
"""v88 regression: one verified cross-domain transaction instead of 7 partial edits."""
import asyncio
import copy
import random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems import admin_live_v8800 as editor

async def main():
    count=0
    def ok(value,message=''):
        nonlocal count
        assert value,message
        count+=1
    owner=Fake()
    db=owner.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    owner.server.live_content_v1204=service
    guest=Fake(False,db)
    guest.server.live_content_v1204=service
    initial=copy.deepcopy(service.draft)
    active=copy.deepcopy(service.active)
    rng=random.getstate()
    start_changes=db.conn.total_changes
    async def ask(text,user=owner):
        await user.admin_command('live '+text)
        return user.messages[-1]
    try:
        for c in ('pomoc 46','aktualizacja status','aktualizacja karta quest temple_rats needed',
                  'aktualizacja plan quest temple_rats reward_gold | 100'):
            ok('Nieznana komenda' in await ask(c,guest),'Permissions '+c)
        ok('POMOC 46' in await ask('pomoc 46'))
        ok('plan=NIE' in await ask('aktualizacja status'))
        ok('ACTIVE=10; DRAFT=10' in await ask('aktualizacja karta quest temple_rats needed'))
        ok('ACTIVE=3; DRAFT=3' in await ask('aktualizacja karta mob temple_rat damage'))
        ok('ACTIVE=48; DRAFT=48' in await ask('aktualizacja karta item leather_vest price'))
        ok('AUTO' in await ask('aktualizacja karta uoss black_rabite furia'))
        suite=[
            'aktualizacja plan quest not_here reward_gold | 5',
            'aktualizacja plan skill not_here mana | 3',
            'aktualizacja plan mob not_here damage | 9',
            'aktualizacja plan item not_here price | 9',
            'aktualizacja plan recipe not_here quantity | 9',
            'aktualizacja plan shop not_here inventory | ["healing_potion"]',
            'aktualizacja plan uoss not_here skala | 150:110',
            'aktualizacja plan quest temple_rats reward_gold | -1',
            'aktualizacja plan mob temple_rat damage | -1',
            'aktualizacja plan shop market inventory | ["no_such_item"]',
            'aktualizacja plan shop market inventory | ["healing_potion","healing_potion"]',
            'aktualizacja plan uoss black_rabite fazy | 80:2:160,95:3:160',
            'aktualizacja plan uoss black_rabite furia | 0:110:5',
            'aktualizacja plan skill warrior_power_slash mana | -5',
            'aktualizacja plan recipe iron_ingot shop | 2',
            'aktualizacja plan npc fisher_tomas room | forge',
            'aktualizacja plan npc fisher_tomas shopkeeper | unclear',
            'aktualizacja plan item leather_vest magic_attack | 50',
            'aktualizacja plan quest temple_rats reward_gold | 15; quest temple_rats reward_gold | 20',
            'aktualizacja plan quest temple_rats reward_gold | 15;; mob temple_rat damage | 4',
            'aktualizacja plan quest temple_rats requires_quest | temple_rats',
            'aktualizacja plan quest temple_rats requires_quest | unknown_id',
            'aktualizacja plan quest mirella_jewel_iron requires_quest | mirella_jewel_gold',
            'aktualizacja zatwierdz NIE',
            'aktualizacja karta item leather_vest name | 24; mob temple_rat damage | 4',
            'aktualizacja plan quest temple_rats reward_gold | 100; mob temple_rat damage | UNKNOWN',
        ]
        for bad in suite:
            ret=await ask(bad)
            ok('ADMIN LIVE V88' in ret or ('Nieznana komenda' in ret and bad.endswith('NIE')),bad+' yielded '+ret)
            ok(service.draft==initial,'DRAFT modified by invalid plan '+bad)
            ok(service.active==active,'ACTIVE modified by invalid plan '+bad)
        ok('Brak planu' in await ask('aktualizacja zatwierdz POTWIERDZAM'))
        good=(
            'aktualizacja plan quest temple_rats reward_gold | 100;'
            ' quest temple_rats needed | 11;'
            ' mob temple_rat damage | 5;'
            ' skill warrior_power_slash mana | 8;'
            ' item leather_vest price | 90;'
            ' recipe iron_ingot quantity | 2;'
            ' shop market inventory | ["healing_potion","leather_vest"];'
            ' npc fisher_tomas dialogue | Witaj, wedkarzu.;'
            ' uoss black_rabite furia | 3:115:4'
        )
        ok('9 pol, 8 dziedzin' in await ask(good))
        ok(service.draft==initial and service.active==active)
        ok('plan=TAK' in await ask('aktualizacja status'))
        ok('zatwierdzono' in await ask('aktualizacja zatwierdz POTWIERDZAM'))
        ok(service.draft['quest_edits']['temple_rats']['needed']==11)
        ok(service.draft['quest_edits']['temple_rats']['reward_gold']==100)
        ok(service.draft['mob_edits']['temple_rat']['damage']==5)
        ok(service.draft['skill_edits']['warrior_power_slash']['mana']==8)
        ok(service.draft['item_edits']['leather_vest']['price']==90)
        ok(service.draft['recipe_edits']['iron_ingot']['quantity']==2)
        ok(service.draft['shop_edits']['market']['inventory']==['healing_potion','leather_vest'])
        ok(service.draft['v34_rules']['uoss']['black_rabite']['stack_percent']==115)
        ok(service.draft['npc_edits']['fisher_tomas']['dialogue']=='Witaj, wedkarzu.')
        ok('ACTIVE=3; DRAFT=5' in await ask('aktualizacja karta mob temple_rat damage'))
        ok(service.active==active,'a staged change leaked into active content')
        ok('Cofnieto' in await ask('aktualizacja cofnij POTWIERDZAM'))
        ok(service.draft==initial and service.active==active)
        ok('Brak ostatniej' in await ask('aktualizacja cofnij POTWIERDZAM'))
        ok('9 pol' in await ask(good))
        service.draft['quest_edits'].setdefault('temple_rats',{})['reward_silver']=999
        ok('DRAFT/ACTIVE zmienione' in await ask('aktualizacja zatwierdz POTWIERDZAM'))
        service.draft=copy.deepcopy(initial)
        ok('9 pol' in await ask(good))
        service.active['quest_edits']['temple_rats']={'reward_gold':10000}
        ok('DRAFT/ACTIVE zmienione' in await ask('aktualizacja zatwierdz POTWIERDZAM'))
        service.active=copy.deepcopy(active)
        ok('9 pol' in await ask(good))
        ok('anulowany' in await ask('aktualizacja anuluj'))
        ok('Brak planu' in await ask('aktualizacja zatwierdz POTWIERDZAM'))
        ok(service.draft==initial and service.active==active)
        ok(random.getstate()==rng)
        ok(db.conn.total_changes==start_changes,'SQL writes from DRAFT plans')
        print(f'ADMIN LIVE v88 INTEGRATED: {count} PASS',flush=True)
        return count
    finally:
        db.conn.close()

if __name__=='__main__':
    asyncio.run(main())
