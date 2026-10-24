# -*- coding: utf-8 -*-
"""v47: admin live read-only controls, real dispatch and zero-mutation checks."""
import asyncio
import copy
import random
from types import SimpleNamespace
from systems.live_content_v1204 import LiveContentV1204
from validation.v3600_admin_guardian2 import Fake
from data.quests import QUESTS

async def _suite():
    good=Fake()
    database=good.server.db
    good.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=database.conn))
    service=good.server.live_content_v1204
    guest=Fake(False,database)
    guest.server.live_content_v1204=service
    initial_draft=copy.deepcopy(service.draft)
    initial_active=copy.deepcopy(service.active)
    sql_before=list(database.conn.execute('select * from quests'))
    qs_before=copy.deepcopy(QUESTS['bandit_patrol'])
    random_before=random.getstate()
    counter=0
    def check(cond,msg):
        nonlocal counter
        assert cond,msg
        counter+=1
    async def command(text,actor=good):
        await actor.admin_command('live '+text)
        return actor.messages[-1]
    check('ADMIN LIVE POMOC 4/4' in await command('pomoc 4'),'help')
    check('GOTOWOSC WYDANIA' in await command('gotowosc'),'ready')
    check('60/60 PLUS' in await command('gotowosc'),'gate')
    check('QUEST EXP bandit_patrol' in await command('questy exp bandit_patrol'),'exp ID')
    check('AKTYWNE' in await command('questy exp bandit_patrol'),'exp active')
    check('DRAFT' in await command('questy exp bandit_patrol'),'exp draft')
    check('wspolny' in await command('questy exp bandit_patrol'),'exp common')
    check('wspolnie' in await command('questy exp bandit_patrol'),'exp fallback')
    check('ADMIN LIVE:' in await command('questy exp DOES_NOT_EXIST'),'exp unknown')
    check('QUEST GLOBAL:' in await command('questy global'),'full scan')
    check('sprawdzono' in await command('questy global 1'),'count scan')
    check('ADMIN LIVE:' in await command('questy global 0'),'zero page')
    check('ADMIN LIVE:' in await command('questy global abc'),'text page')
    check('ADMIN LIVE:' in await command('questy global 999999'),'oversized page')
    check('OLC PREFLIGHT' in await command('questy preflight'),'preflight')
    check('ARENA ZGODNOSC' in await command('arena zgodnosc'),'arena limitations')
    check('NIEZGODNE 1:1' in await command('arena zgodnosc black_rabite'),'arena honest')
    check('ADMIN LIVE:' in await command('arena zgodnosc DOES_NOT_EXIST'),'bad boss')
    check('Nieznana' in await command('gotowosc',guest),'permission 1')
    check('Nieznana' in await command('questy exp bandit_patrol',guest),'permission 2')
    check('Nieznana' in await command('questy global',guest),'permission 3')
    check('Nieznana' in await command('arena zgodnosc',guest),'permission 4')
    # Existing commands keep their original meanings.
    check('bandit_patrol' in await command('questy szukaj bandit'),'older lookup')
    check('bandit_patrol' in await command('questy nagrody bandit_patrol'),'older rewards')
    check('ADMIN LIVE ULTIMATE' in await command('pomoc 3'),'older help')
    check(service.draft==initial_draft,'draft untouched')
    check(service.active==initial_active,'active untouched')
    check(list(database.conn.execute('select * from quests'))==sql_before,'quests sql untouched')
    check(QUESTS['bandit_patrol']==qs_before,'quest def untouched')
    check(random.getstate()==random_before,'RNG untouched')
    return counter

def run():
    return asyncio.run(_suite())
if __name__=='__main__':
    print('V47 ADMIN LIVE SAFETY:',run(),'checks PASS')
