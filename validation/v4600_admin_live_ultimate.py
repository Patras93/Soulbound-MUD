# -*- coding: utf-8 -*-
"""v46: focused, in-memory admin live contracts; no real database writes."""
import asyncio
import copy
import random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS

async def suite():
    count=0
    owner=Fake();db=owner.server.db
    owner.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    service=owner.server.live_content_v1204
    guest=Fake(False,db)
    guest.server.live_content_v1204=service
    original_draft=copy.deepcopy(service.draft)
    original_active=copy.deepcopy(service.active)
    original_quest=copy.deepcopy(QUESTS['bandit_patrol'])
    original_mob=copy.deepcopy(MOB_TEMPLATES['uoss_superboss_black_rabite_v11136'])
    original_sql=list(db.conn.execute('SELECT * FROM quests'))
    original_hp=owner.current_hp;original_mana=owner.current_mana
    def yes(condition,tag):
        nonlocal count
        assert condition,tag
        count+=1
    async def live(line,user=owner):
        await user.admin_command('live '+line)
        return user.messages[-1]
    for page in ('1','2','3'):
        yes('ADMIN LIVE ULTIMATE' in await live('pomoc '+page),'help '+page)
    yes('ADMIN LIVE POMOC' in await live('pomoc 4'),'help invalid')
    yes('Nieznana' in await live('arena druzyna sklad',guest),'permissions')
    yes('ARENA DRUZYNA' not in await live('arena druzyna sklad'),'no arena')
    rng=random.getstate()
    yes('ARENA11 START' in await live('arena start black_rabite 1000000 20000'),'start')
    yes(random.getstate()==rng,'rng startup')
    baseline=copy.deepcopy(owner.guardian7_lab)
    yes('ARENA DRUZYNA: tylko lider' in await live('arena druzyna sklad'),'empty')
    for args in ('Zla 1 100 100 0 POTWIERDZAM','Wojownik 0 100 100 0 POTWIERDZAM',
                 'Wojownik 10 -2 100 0 POTWIERDZAM','Wojownik 10 100 100 0 NIE',
                 'Mag 1 100 100 0'):
        yes('ADMIN LIVE:' in await live('arena druzyna dodaj '+args),'invalid add '+args)
        yes(len(owner.guardian7_lab['_adminlive46_party'])==0,'no changed add')
    yes('dodano 1' in await live('arena druzyna dodaj Wojownik 10 1000 5000 100 POTWIERDZAM'),'add1')
    yes('dodano 2' in await live('arena druzyna dodaj Mag 50 1000 2500 200 POTWIERDZAM'),'add2')
    yes('dodano 3' in await live('arena druzyna dodaj Nekromanta 20 1000 2000 500 POTWIERDZAM'),'add3')
    yes('dodano 4' in await live('arena druzyna dodaj Druid 15 1000 1000 50 POTWIERDZAM'),'add4')
    yes('limit' in (await live('arena druzyna dodaj Wojownik 3 1000 1000 10 POTWIERDZAM')).lower(),'cap')
    yes('lider plus 4' in await live('arena druzyna sklad'),'status')
    yes('warrior_power_slash' in await live('arena druzyna skille 1'),'catalog')
    yes('ADMIN LIVE:' in await live('arena druzyna skille 9'),'invalid index')
    yes('ADMIN LIVE:' in await live('arena druzyna skille 1 999'),'invalid page')
    yes('ADMIN LIVE:' in await live('arena druzyna skill 1 none POTWIERDZAM'),'invalid skill')
    yes('ADMIN LIVE:' in await live('arena druzyna skill 1 warrior_power_slash NIE'),'confirmation')
    yes('skill dla postaci 1' in await live('arena druzyna skill 1 warrior_power_slash POTWIERDZAM'),'skill selected')
    def view():
        a=owner.guardian7_lab
        return (a['round'],a['boss'].hp,a['hero_hp'],a['total_dealt'],a['total_taken'],
                copy.deepcopy(a['_adminlive46_party']),a['_guardian10_rng'],copy.deepcopy(a['notes']))
    snap=view();state_random=random.getstate()
    for n in (1,3,12):
        yes('ARENA DRUZYNA PROGNOZA' in await live(f'arena druzyna prognoza {n}'),'preview')
        yes(view()==snap,'preview no mutation')
        yes(random.getstate()==state_random,'preview RNG')
    for n in ('0','13','abc'):
        yes('ADMIN LIVE:' in await live('arena druzyna tury '+n+' POTWIERDZAM'),'invalid turns')
        yes(view()==snap,'invalid no mutation')
    yes('ADMIN LIVE:' in await live('arena druzyna tury 3 NIE'),'confirmation turns')
    yes(view()==snap,'confirmation unchanged')
    yes('ARENA DRUZYNA TURY 3/3' in await live('arena druzyna tury 3 POTWIERDZAM'),'turns')
    yes(owner.guardian7_lab['round']==3,'advance')
    yes(random.getstate()==state_random,'committed isolated RNG')
    yes('ARENA' in await live('arena migawka'),'snapshot')
    copied=view()
    yes('ARENA DRUZYNA TURY' in await live('arena druzyna tury 2 POTWIERDZAM'),'more turns')
    yes('PRZYWROCONO' in await live('arena przywroc POTWIERDZAM'),'restore')
    yes(view()==copied,'restore party and RNG')
    yes('ARENA DRUZYNA TURY' in await live('arena druzyna tury 2 POTWIERDZAM'),'replay')
    replay=view()
    yes('PRZYWROCONO' in await live('arena przywroc POTWIERDZAM'),'restore again')
    yes('ARENA DRUZYNA TURY' in await live('arena druzyna tury 2 POTWIERDZAM'),'replay again')
    yes(view()==replay,'identical replay')
    yes('ADMIN LIVE:' in await live('arena druzyna usun 4 NIE'),'delete without confirm')
    yes('usunieto' in await live('arena druzyna usun 4 POTWIERDZAM'),'delete')
    yes('lider plus 3' in await live('arena druzyna sklad'),'after delete')
    yes('usunieto sklad' in await live('arena druzyna wyczysc POTWIERDZAM'),'clear')
    yes('tylko lider' in await live('arena druzyna sklad'),'empty after clear')
    yes('ARENA11' in await live('arena wyjdz'),'exit')
    yes(owner.guardian7_lab is None,'arena freed')
    yes('bandit_patrol' in await live('questy karta bandit_patrol'),'quest card')
    yes('bandit_patrol' in await live('questy szukaj bandit'),'quest find')
    yes('ADMIN LIVE:' in await live('questy karta no_such_quest'),'unknown quest')
    yes('ADMIN LIVE:' in await live('questy szukaj bandit 999'),'unknown page')
    yes('bandit_patrol' in await live('questy nagrody bandit_patrol'),'old reward route')
    yes('bandit_patrol' in await live('questy porownaj bandit_patrol'),'old compare route')
    yes('bez zmian' in (await live('questy napraw plan bandit')).lower(),'plan valid')
    yes('ADMIN LIVE:' in await live('questy napraw zatwierdz POTWIERDZAM'),'empty plan')
    yes(service.draft==original_draft,'no planned writes')
    # Inject deliberately bad *unpublished* OLC row. Never touch the source QUESTS.
    service.draft['quest_edits']['bandit_patrol']={'needed':0}
    invalid_before=copy.deepcopy(service.draft)
    yes('mozliwe proste poprawki 1' in await live('questy napraw plan bandit'),'real plan')
    yes(service.draft==invalid_before,'plan read only')
    yes('ADMIN LIVE:' in await live('questy napraw zatwierdz NIE'),'no confirm')
    yes(service.draft==invalid_before,'no confirm no write')
    yes('QUEST NAPRAW DRAFT' in await live('questy napraw zatwierdz POTWIERDZAM'),'batch commit')
    yes(service.draft['quest_edits']['bandit_patrol']['needed']==1,'fixed needed')
    yes(service.active==original_active,'active unchanged')
    yes('QUEST NAPRAW COFNIETO' in await live('questy napraw cofnij POTWIERDZAM'),'undo')
    yes(service.draft==invalid_before,'undo exact old state')
    # Optimistic concurrency: a stale plan MUST be rejected if another edit occurs.
    yes('QUEST NAPRAW PLAN' in await live('questy napraw plan bandit'),'plan2')
    service.draft['quest_edits']['bandit_patrol']['name']='Patrol sprawdzony'
    stale=copy.deepcopy(service.draft)
    yes('ADMIN LIVE:' in await live('questy napraw zatwierdz POTWIERDZAM'),'stale reject')
    yes(service.draft==stale,'stale preserve')
    yes('QUEST NAPRAW PLAN' in await live('questy napraw plan bandit'),'plan3')
    yes('QUEST NAPRAW DRAFT' in await live('questy napraw zatwierdz POTWIERDZAM'),'commit3')
    service.draft['quest_edits']['bandit_patrol']['reward_gold']=120
    altered=copy.deepcopy(service.draft)
    yes('ADMIN LIVE:' in await live('questy napraw cofnij POTWIERDZAM'),'undo stale reject')
    yes(service.draft==altered,'undo stale preserves')
    # Reset only the fake service to test completeness/no side effects.
    service.draft=original_draft
    yes(service.active==original_active and QUESTS['bandit_patrol']==original_quest,'actual definitions unaffected')
    yes(MOB_TEMPLATES['uoss_superboss_black_rabite_v11136']==original_mob,'boss unchanged')
    yes(db.logged==[],'no admin records')
    yes(list(db.conn.execute('SELECT * FROM quests'))==original_sql,'sqlite unaffected')
    yes(owner.server.world.mobs=={},'world unaffected')
    yes(owner.current_hp==original_hp and owner.current_mana==original_mana,'character untouched')
    yes(random.getstate()==rng,'global rng untouched')
    db.conn.close()
    return count

def run():return asyncio.run(suite())
if __name__=='__main__':print('ADMIN LIVE ULTIMATE v46:',run(),'checks PASS')
