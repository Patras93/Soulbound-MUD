# -*- coding: utf-8 -*-
"""v107: independent integration tests; isolated ephemeral SQLite and TCP port.

This is a CONTENT test, not deployment permission. Production EQ migrations,
auto-event scheduling and safe v106->v107 updater need distinct gates.
"""
from __future__ import annotations
import os
from pathlib import Path
import socket
import tempfile
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))


def run():
    if os.environ.get('SOULBOUND_V107_STAGING')!='1':
        raise RuntimeError('Bramka v107: nowe systemy nieaktywne')
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0))
        private_port=probe.getsockname()[1]
    os.environ.update(SOULBOUND_HOST='127.0.0.1',SOULBOUND_PORT=str(private_port))
    os.environ.pop('PORT',None)
    os.environ.pop('RAILWAY_TCP_APPLICATION_PORT',None)
    import server
    from collections import Counter
    from core.classes_skills import CLASSES,RACES,CLASS_SKILLS
    from core.archetypes.chaos import CLASS_SPECS,RACE_SPECS,PROFESSION_SPECS
    from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP
    from systems.v10700_profession_work import process, product_id
    from storage.database import Database
    from systems.content_registry import QUESTS,ROOMS,NPCS,ITEMS,MOB_TEMPLATES
    checks=0
    def check(cond,why):
        nonlocal checks
        assert cond, 'v107: '+why
        checks+=1
    from core.archetypes.expansion import CLASS_SPECS as V110_CLASSES, RACE_SPECS as V110_RACES
    old_class_names={r[0] for r in CLASSES}-{r[0] for r in V110_CLASSES}
    old_race_names={r[0] for r in RACES}-{r[0] for r in V110_RACES}
    check(len(old_class_names)==30 and len(old_class_names)+len(V110_CLASSES)==len(CLASSES),'30 historical classes + new v110 classes')
    check(len(old_race_names)==30 and len(old_race_names)+len(V110_RACES)==len(RACES),'30 historical races + new v110 races')
    class_names={x[0] for x in CLASSES}
    new_names=('Magitek',)+tuple(x[0] for x in CLASS_SPECS)
    check(len(set(new_names))==8,'8 unikalnych nowych klas')
    skill_ids=[]
    for name in new_names:
        check(name in class_names,'brak klasy '+name)
        check(name in CLASS_SKILLS and len(CLASS_SKILLS[name])>=7,'brak skilli '+name)
        skill_ids.extend(row['id'] for row in CLASS_SKILLS[name])
    check(len(set(skill_ids))==len(skill_ids),'duplikaty skill ID')
    for name,*_ in RACE_SPECS:
        found=next((r for r in RACES if r[0]==name),None)
        check(found is not None and sum(found[2:])==50,'niewlasciwa rasa/statystyki '+name)
    for name,tool,_,mat in PROFESSION_SPECS:
        check(TOOL_PROFESSION_MAP.get(tool)==name,'brak profesji '+name)
        check(mat in ITEMS,'brak prawdziwego surowca '+mat)
    quest_counters=Counter()
    for qid in QUESTS:
        if qid.startswith('v10700_chaos_'): quest_counters['regional']+=1
        elif qid.startswith('v10700_saga_'): quest_counters['saga']+=1
        elif qid.startswith('v10700_insects_'): quest_counters['owady']+=1
    check(quest_counters==Counter(regional=1200,saga=760,owady=40),'dokladnie 2000 questow')
    spawns=set(mid for room,mid in server.MOB_SPAWNS if room in ROOMS)
    for qid,quest in QUESTS.items():
        if not qid.startswith('v10700_'):continue
        check(quest.get('kind') in ('kill','collect','profession_action','talk_npc'), 'typ zadania '+qid)
        if quest['kind']=='kill':
            check(quest.get('target') in MOB_TEMPLATES and quest['target'] in spawns,'niedostepny potwor '+qid)
        elif quest['kind']=='collect':
            check(quest.get('target') in ITEMS,'niedostepny material '+qid)
        elif quest['kind']=='profession_action':
            check(quest.get('target') in set(TOOL_PROFESSION_MAP.values()),'nieznana profesja '+qid)
        elif quest['kind']=='talk_npc':
            check(quest.get('target_npc') in NPCS,'brak celu rozmowy '+qid)
        if quest.get('requires_quest'):
            check(quest['requires_quest'] in QUESTS,'brak poprzedniego questu '+qid)
    for n,(name,tool,_,ingredient) in enumerate(PROFESSION_SPECS):
        check(product_id(n) in ITEMS,'nie ma nowego wyrobu '+name)
    # Real SQLite - two independent accounts and real material storage.
    with tempfile.TemporaryDirectory(prefix='sb107_content_') as td:
        db=Database(str(Path(td)/'disposable.db'))
        try:
            account=db.create_account('sb107_private_one','private password 123')
            other=db.create_account('sb107_private_two','private password 234')
            cases={key:'Testera' for key in ('nom','gen','dat','acc','ins','loc','voc')}
            race=next(r for r in RACES if r[0]=='Astralici')
            cls=next(c for c in CLASSES if c[0]=='Chronotechnik')
            db.create_character(account,'Testera',race,cls,cases)
            char=db.character_for_account(account)
            check(char['race']=='Astralici' and char['class_name']=='Chronotechnik', 'zapis rasy i klasy')
            def native_test_grant(name,xp,tool,tool_xp,**kwargs):
                db.conn.execute('CREATE TABLE IF NOT EXISTS v107_test_xp('
                                'account_id INTEGER, profession TEXT, amount INTEGER)')
                db.conn.execute('INSERT INTO v107_test_xp VALUES(?,?,?)',(account,name,xp))
                db.conn.commit()
                return (['Otrzymano EXP '+name],1,1)
            for n,(name,tool,_,ingredient) in enumerate(PROFESSION_SPECS):
                qid=f'v10700_saga_prof_{n*40+1:03d}'
                db.start_quest(account,qid)
                db.add_item(account,ingredient,3)
                before=db.storage_qty(account,'craftbox',ingredient)
                result=process(db,account,n,native_test_grant,now=1000)
                check(result[0] is not None and result[2]==product_id(n),'rzemioslo '+name)
                check(db.storage_qty(account,'craftbox',ingredient)==before-1,'pobranie materialu '+name)
                check(db.storage_qty(account,'craftbox',product_id(n))==1,'wyrob '+name)
                check(db.quest(account,qid)['progress']==1,'postep zawodowego questa '+name)
                check(process(db,account,n,native_test_grant,now=1001)[0] is None,'cooldown '+name)
                check(db.quest(other,qid) is None,'izolacja konta '+name)
            # A thrown post-consumption XP exception rolls back consumed material AND product.
            n=0;name,tool,_,ingredient=PROFESSION_SPECS[n]
            before=db.storage_qty(account,'craftbox',ingredient)
            product_before=db.storage_qty(account,'craftbox',product_id(n))
            def fail_grant(*args,**kwargs):raise RuntimeError('symulowana awaria XP')
            try:
                process(db,account,n,fail_grant,now=2000)
            except RuntimeError:  # AUDIT_INTENTIONAL_PASS: simulated XP failure must roll back
                pass
            else:raise AssertionError('Brak wymaganej odmowy po awarii XP')
            check(db.storage_qty(account,'craftbox',ingredient)==before,'rollback materialu')
            check(db.storage_qty(account,'craftbox',product_id(n))==product_before,'rollback wyrobu')
            check(db.quest(account,'v10700_saga_prof_001')['progress']==1,'rollback postepu')
        finally:
            # Windows SQLite WAL keeps the disposable DB locked while this connection is open.
            # Always release the handle before TemporaryDirectory deletes it.
            db.conn.close()
    # No direct protocol mock is accepted as a live TCP PASS.
    print('V107 ZINTEGROWANY KATALOG: 30 klas, 30 ras, 8 nowych profesji, 2000 questow, SQLite - '
          f'{checks} kontroli PASS; NIE oznacza gotowosci do wdrozenia.',flush=True)
    return checks

if __name__=='__main__':
    run()
