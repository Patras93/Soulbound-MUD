# -*- coding: utf-8 -*-
"""v97: tested multi-character stat and inventory repairs + real UOSS OLC profile copy."""
from __future__ import annotations
import asyncio,copy,sqlite3
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems import admin_live_offline_v9700 as offline
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
from core.mines_threat import ITEMS


async def main():
    n=0
    def ok(value,label=''):
        nonlocal n
        assert value,label;n+=1
    db=Fake().server.db
    con=db.conn
    con.executescript('''DROP TABLE characters;
      CREATE TABLE characters(account_id INTEGER PRIMARY KEY,name TEXT UNIQUE COLLATE NOCASE,
        character_level INTEGER,character_xp INTEGER,soul_level INTEGER,soul_xp INTEGER,
        soul_weapon_mastery_level INTEGER,soul_weapon_mastery_xp INTEGER,
        strength INTEGER,dexterity INTEGER,constitution INTEGER,intelligence INTEGER,
        willpower INTEGER,charisma INTEGER,deaths INTEGER);
      INSERT INTO characters VALUES(2,'Friend',30,50,3,20,4,10,10,15,20,25,30,12,0);
      INSERT INTO accounts VALUES(3,'another');
      INSERT INTO characters VALUES(3,'Another',40,60,3,20,4,10,18,15,20,25,30,12,2);
      CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,PRIMARY KEY(account_id,item_id));
      CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,paid_silver INTEGER,quantity INTEGER);
      CREATE TABLE protected_inventory_v1280(account_id INTEGER,item_id TEXT,PRIMARY KEY(account_id,item_id));
      CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,PRIMARY KEY(account_id,slot));
      CREATE TABLE experience_bank_v2011(account_id INTEGER,kind TEXT,source_key TEXT,balance TEXT);
      INSERT INTO experience_bank_v2011 VALUES(2,'character','boss','12345');
    ''')
    ids=[x for x,meta in ITEMS.items() if not x.startswith(('live_','deepq_','craftq_')) and meta.get('slot') in ('ring','body','head','shield','necklace')]
    # In tests we use two existing, mundane template IDs for inventory quantities.
    assert len(ids)>=3
    safe,bought,protected=ids[:3]
    con.execute('INSERT INTO inventory VALUES(?,?,?)',(2,safe,6))
    con.execute('INSERT INTO inventory VALUES(?,?,?)',(3,safe,7))
    con.execute('INSERT INTO inventory VALUES(?,?,?)',(2,bought,5))
    con.execute('INSERT INTO inventory VALUES(?,?,?)',(2,protected,3))
    con.execute('INSERT INTO shop_purchase_lots_v1175 VALUES(?,?,?,?)',(2,bought,10,1))
    con.execute('INSERT INTO protected_inventory_v1280 VALUES(?,?)',(2,protected))
    con.commit()
    host=Fake(True,db);guest=Fake(False,db)
    host.server.sessions=[host];guest.server.sessions=[host]
    content=LiveContentV1204(SimpleNamespace(conn=con));host.server.live_content_v1204=content;guest.server.live_content_v1204=content
    async def call(command,actor=host):
        await actor.admin_command('live '+command)
        return actor.messages[-1]
    try:
        ok('POMOC 55' in await call('pomoc 55'),'help stat')
        ok('POMOC 56' in await call('pomoc 56'),'help boss')
        for txt in ('pomoc 55','pomoc 56','postacie plecak karta Friend',
                    'postacie staty pakiet plan Friend | strength=60',
                    'boss uoss profil karta black_rabite'):
            ok('Nieznana komenda' in await call(txt,guest),'guest '+txt)
        ok('PLECAK Friend' in await call('postacie plecak karta Friend'),'inventory card')
        ok('EDYTOWALNY' in host.messages[-1],'editable inventory identified')
        ok('CHRONIONY' in host.messages[-1],'protected inventory identified')
        ok('STATY PAKIET PLAN' in await call('postacie staty pakiet plan Friend | strength=60,dexterity=33 / Another | charisma=40,deaths=4'),'stat plan')
        ok(con.execute('SELECT strength FROM characters WHERE account_id=2').fetchone()[0]==10,'stat plan read only')
        ok('STATY PAKIET ZAPISANO' in await call('postacie staty pakiet zatwierdz POTWIERDZAM'),'stat commit')
        ok(tuple(con.execute('SELECT strength,dexterity FROM characters WHERE account_id=2').fetchone())==(60,33),'friend stat change')
        ok(tuple(con.execute('SELECT charisma,deaths FROM characters WHERE account_id=3').fetchone())==(40,4),'another stat change')
        ok('STATY PAKIET COFNIETO' in await call('postacie staty pakiet cofnij POTWIERDZAM'),'stat undo')
        ok(con.execute('SELECT strength FROM characters WHERE account_id=2').fetchone()[0]==10,'undo friend')
        ok(con.execute('SELECT charisma FROM characters WHERE account_id=3').fetchone()[0]==12,'undo another')
        for bad in ('Friend | gold=200','Friend | strength=-5','Friend | charisma=1000000001',
                    'Friend | strength=2,strength=3','Friend | strength=0',
                    'Friend | strength=30 / Friend | deaths=3','Missing | charisma=40'):
            ok('ADMIN LIVE V97 OFFLINE' in await call('postacie staty pakiet plan '+bad),'bad stat '+bad)
            ok(con.execute('SELECT strength FROM characters WHERE account_id=2').fetchone()[0]==10,'stat unchanged '+bad)
        ok('STATY PAKIET PLAN' in await call('postacie staty pakiet plan Friend | strength=44 / Another | intelligence=66'),'CAS plan')
        con.execute('UPDATE characters SET intelligence=67 WHERE account_id=3')
        ok('Konflikt statystyk' in await call('postacie staty pakiet zatwierdz POTWIERDZAM'),'stat CAS blocked')
        ok(con.execute('SELECT strength FROM characters WHERE account_id=2').fetchone()[0]==10,'stat CAS rollback first account')
        con.execute('UPDATE characters SET intelligence=25 WHERE account_id=3')
        ok('STATY PAKIET ZAPISANO' in await call('postacie staty pakiet zatwierdz POTWIERDZAM'),'stat retry')
        ok('STATY PAKIET COFNIETO' in await call('postacie staty pakiet cofnij POTWIERDZAM'),'stat retry undo')
        ok('STATY PAKIET PLAN' in await call('postacie staty pakiet plan Friend | strength=70'),'audit plan')
        con.execute('DROP TABLE admin_actions_v1224')
        try:offline._stats_write(host,host.adminlive9700_stats_plan)
        except sqlite3.OperationalError:n+=1
        else:raise AssertionError('stat audit error expected')
        ok(con.execute('SELECT strength FROM characters WHERE account_id=2').fetchone()[0]==10,'stat audit rollback')
        con.execute('CREATE TABLE admin_actions_v1224(id INTEGER PRIMARY KEY AUTOINCREMENT, admin_login TEXT,action TEXT,target TEXT)')
        ok('STATY PAKIET ZAPISANO' in await call('postacie staty pakiet zatwierdz POTWIERDZAM'),'stat audit retry')
        ok('STATY PAKIET COFNIETO' in await call('postacie staty pakiet cofnij POTWIERDZAM'),'stat audit undo')
        ok('PLECAK PLAN' in await call(f'postacie plecak plan Friend | {safe}=11; Another | {safe}=12'),'inventory plan')
        ok(con.execute('SELECT quantity FROM inventory WHERE account_id=2 AND item_id=?',(safe,)).fetchone()[0]==6,'inventory no write at plan')
        ok('PLECAK ZAPISANO' in await call('postacie plecak zatwierdz POTWIERDZAM'),'inventory commit')
        ok(con.execute('SELECT quantity FROM inventory WHERE account_id=2 AND item_id=?',(safe,)).fetchone()[0]==11,'item friend changed')
        ok(con.execute('SELECT quantity FROM inventory WHERE account_id=3 AND item_id=?',(safe,)).fetchone()[0]==12,'item another changed')
        ok('PLECAK COFNIETO' in await call('postacie plecak cofnij POTWIERDZAM'),'inventory undo')
        ok(con.execute('SELECT quantity FROM inventory WHERE account_id=2 AND item_id=?',(safe,)).fetchone()[0]==6,'inventory undo exact')
        for bad in (f'Friend | {bought}=8',f'Friend | {protected}=8',
                    f'Friend | {safe}=0',f'Friend | {safe}=1000000001',
                    'Friend | unknown_item=15',f'Friend | {safe}=20; Friend | {safe}=30',
                    f'Missing | {safe}=20'):
            ok('ADMIN LIVE V97 OFFLINE' in await call('postacie plecak plan '+bad),'inventory invalid '+bad)
            ok(con.execute('SELECT quantity FROM inventory WHERE account_id=2 AND item_id=?',(safe,)).fetchone()[0]==6,'inventory untouched '+bad)
        ok('PLECAK PLAN' in await call(f'postacie plecak plan Friend | {safe}=8; Another | {safe}=9'),'item CAS plan')
        con.execute('UPDATE inventory SET quantity=8 WHERE account_id=3 AND item_id=?',(safe,))
        ok('Plecak zmieniony' in await call('postacie plecak zatwierdz POTWIERDZAM'),'item CAS conflict')
        ok(con.execute('SELECT quantity FROM inventory WHERE account_id=2 AND item_id=?',(safe,)).fetchone()[0]==6,'item CAS rollback first')
        con.execute('UPDATE inventory SET quantity=7 WHERE account_id=3 AND item_id=?',(safe,))
        ok('PLECAK ZAPISANO' in await call('postacie plecak zatwierdz POTWIERDZAM'),'item CAS retry')
        ok('PLECAK COFNIETO' in await call('postacie plecak cofnij POTWIERDZAM'),'item CAS undo')
        ok('PLECAK PLAN' in await call(f'postacie plecak plan Friend | {safe}=8'),'lot insertion protection plan')
        con.execute('INSERT INTO shop_purchase_lots_v1175 VALUES(?,?,?,?)',(2,safe,20,2))
        ok('historie zakupu' in await call('postacie plecak zatwierdz POTWIERDZAM'),'late purchase guard')
        con.execute('DELETE FROM shop_purchase_lots_v1175 WHERE account_id=2 AND item_id=?',(safe,))
        ok('PLECAK ZAPISANO' in await call('postacie plecak zatwierdz POTWIERDZAM'),'item late guard retry')
        ok('PLECAK COFNIETO' in await call('postacie plecak cofnij POTWIERDZAM'),'item late guard undo')
        host.server.sessions.append(SimpleNamespace(closed=False,character=SimpleNamespace(name='Friend'),account_id=2))
        ok('ADMIN LIVE V97 OFFLINE' in await call('postacie staty pakiet plan Friend | strength=55'),'online stat guard')
        ok('ADMIN LIVE V97 OFFLINE' in await call(f'postacie plecak plan Friend | {safe}=15'),'online item guard')
        host.server.sessions.pop()
        ok(con.execute('SELECT balance FROM experience_bank_v2011').fetchone()[0]=='12345','exp bank unchanged')
        ok(con.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        # Real native OLC v24/32/33/34 profile copying, draft-only, no fake combat rules.
        bosses=list(UOSS_SUPERBOSS_ENCOUNTERS_V11134)
        ok('black_rabite' in bosses,'black rabite exists')
        a='black_rabite';b=next(key for key in bosses if key!=a)
        original_draft=copy.deepcopy(content.draft);original_active=copy.deepcopy(content.active)
        ok('UOSS PROFIL' in await call('boss uoss profil karta '+a),'boss card')
        for bad in ('missing | black_rabite | ACTIVE',
                    'black_rabite | black_rabite | DRAFT',
                    f'{b} | black_rabite | wrong',
                    f'{b} | black_rabite | DRAFT; {b} | black_rabite | DRAFT'):
            ok('ADMIN LIVE V97 UOSS' in await call('boss uoss profil plan '+bad),'bad uoss '+bad)
            ok(content.draft==original_draft,'bad uoss no draft '+bad)
        # author a source via the existing, executable v75 editor, then clone it.
        from systems.admin_live_v7500 import plan as author
        ok('PLAN' in author(host,content,f'{a} | fazy=75:2:160,40:3:220;leczenie=35:4:3;furia=3:115:4;skala=150:130'),'source v75 plan')
        ok('zatwierdzono' in await call('boss uoss mechaniki zatwierdz POTWIERDZAM'),'author commit')
        with_source=copy.deepcopy(content.draft)
        ok('UOSS PROFIL PLAN' in await call(f'boss uoss profil plan {b} | {a} | DRAFT'),'clone plan')
        ok(content.draft==with_source,'clone plan does not change draft')
        ok('zatwierdzono' in await call('boss uoss profil zatwierdz POTWIERDZAM'),'clone commit')
        for section in ('v24_rules','v32_rules','v33_rules','v34_rules'):
            ok(content.draft[section]['uoss'][a]==content.draft[section]['uoss'][b],section+' cloned')
            ok(content.active==original_active,section+' not published')
        ok('Cofnieto' in await call('boss uoss profil cofnij POTWIERDZAM'),'clone undo')
        ok(content.draft==with_source,'clone undo exact')
        # Give the target its own rule before testing ACTIVE -> AUTO reset.
        ok('PLAN' in author(host,content,f'{b} | furia=2:111:2'),'target v75 plan')
        ok('zatwierdzono' in await call('boss uoss mechaniki zatwierdz POTWIERDZAM'),'target author commit')
        with_target=copy.deepcopy(content.draft)
        ok('UOSS PROFIL PLAN' in await call(f'boss uoss profil plan {b} | {a} | ACTIVE'),'active source plan')
        ok('zatwierdzono' in await call('boss uoss profil zatwierdz POTWIERDZAM'),'active source commit')
        for section in ('v24_rules','v32_rules','v33_rules','v34_rules'):
            ok(b not in content.draft[section]['uoss'],'active auto copied '+section)
        ok('Cofnieto' in await call('boss uoss profil cofnij POTWIERDZAM'),'active undo')
        ok(content.draft==with_target,'active undo exact')
        ok('Cofnieto' in await call('boss uoss mechaniki cofnij POTWIERDZAM'),'undo target v75')
        ok(content.draft==with_source,'target v75 undo exact')
        ok('UOSS PROFIL PLAN' in await call(f'boss uoss profil plan {b} | {a} | DRAFT'),'conflict profile plan')
        content.draft['v34_rules']['uoss'][a]['every']=7
        ok('ADMIN LIVE V97 UOSS' in await call('boss uoss profil zatwierdz POTWIERDZAM'),'cross editor conflict')
        content.draft=copy.deepcopy(with_source)
        ok('UOSS PROFIL PLAN' in await call(f'boss uoss profil plan {b} | {a} | DRAFT'),'plan after conflict')
        ok('anulowano' in await call('boss uoss profil anuluj'),'profile cancel')
        ok('ADMIN LIVE V97 UOSS' in await call('boss uoss profil zatwierdz POTWIERDZAM'),'cannot approve cancelled')
        # v75 intentionally remembers only one undo, replaced by the later target edit.
        # Verify no silent DRAFT mutation from the cancelled v97 plan instead.
        ok(content.draft==with_source,'cancel preserved DRAFT')
        ok(content.active==original_active,'no ACTIVE mutation')
        print(f'V97 LARGE ADMIN UPDATE: {n} PASS',flush=True)
    finally:con.close()

if __name__=='__main__':asyncio.run(main())
