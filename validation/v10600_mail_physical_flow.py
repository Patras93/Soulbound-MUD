# -*- coding: utf-8 -*-
"""Isolated staging validation: actual v105 mail methods, physical ID and SQL rollback."""
import json
import os
import sqlite3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.db_inventory import DatabaseInventoryMixin
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy,_check_account

CAT={'ring':{'type':'armor'},'plate':{'type':'armor'},'helm':{'type':'armor'}}
class DB(DatabaseInventoryMixin):
    def __init__(self,conn):
        self.conn=conn
        self._v106_shadow_item_catalog=CAT
        self._v106_shadow_slots_disposable_copy=True
        self._v106_mail_shadow_disposable_copy=True


def run():
    original=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.executescript('''
      CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
        PRIMARY KEY(account_id,item_id));
      CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
        PRIMARY KEY(account_id,slot));
      CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
        PRIMARY KEY(account_id,record_key));
      CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,
        paid_silver INTEGER,quantity INTEGER,PRIMARY KEY(account_id,item_id,paid_silver));
      CREATE TABLE player_mail_v03051(id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_account_id INTEGER NOT NULL,sender_account_id INTEGER,
        sender_name TEXT NOT NULL,subject TEXT NOT NULL DEFAULT '',body TEXT NOT NULL,
        is_read INTEGER NOT NULL DEFAULT 0,
        attachment_kind TEXT NOT NULL DEFAULT '',attachment_item_id TEXT NOT NULL DEFAULT '',
        attachment_item_name TEXT NOT NULL DEFAULT '',attachment_item_qty INTEGER NOT NULL DEFAULT 0,
        attachment_coins INTEGER NOT NULL DEFAULT 0,attachment_meta_json TEXT NOT NULL DEFAULT '{}',
        attachment_claimed INTEGER NOT NULL DEFAULT 0);
      INSERT INTO inventory VALUES(1,'ring',3),(1,'plate',1),(1,'helm',1);
      INSERT INTO equipment VALUES(1,'finger','ring');
      INSERT INTO player_records_v03051 VALUES(1,'eq_evolution_v10500:plate',4);
      INSERT INTO shop_purchase_lots_v1175 VALUES(1,'ring',70,1),(1,'ring',80,1);
    ''')
    checks=0
    def ck(ok,why):
        nonlocal checks
        if not ok:raise AssertionError(why)
        checks+=1
    def denied(fn,typ,why):
        try:fn()
        except typ:ck(True,why)
        else:raise AssertionError(why)
    def state():
        tables=['inventory','equipment','player_records_v03051',
                'shop_purchase_lots_v1175','v106_item_instances',
                'v106_equipped_instances','v106_stored_instances',
                'player_mail_v03051']
        if c.execute("SELECT 1 FROM sqlite_master WHERE name='v106_mail_equipment_escrow'").fetchone():
            tables+=['v106_mail_equipment_escrow']
        return {t:[tuple(r) for r in c.execute('SELECT * FROM '+t+' ORDER BY 1,2')]
                for t in tables}
    try:
        db=DB(c)
        prepare_on_disposable_copy(c,CAT,confirm_disposable_copy=True)
        initial=state()
        ck(db.send_mail_attachment_v0614(1,1,'Nadawca',kind='item',item_id='ring') is None,
            'cannot send to own account')
        ck(db.send_mail_attachment_v0614(1,2,'Nadawca',kind='item',item_id='plate') is None,
            'old evolved template cannot be mailed')
        ck(state()==initial,'denied sends have no changes')
        physical={r[0] for r in c.execute("SELECT instance_id FROM v106_item_instances WHERE account_id=1 AND item_id='ring'")}
        worn=c.execute('SELECT instance_id FROM v106_equipped_instances WHERE account_id=1').fetchone()[0]
        mid=db.send_mail_attachment_v0614(1,2,'Nadawca',kind='item',item_id='ring',item_name='Pierścień')
        ck(type(mid)==int and mid>0,'send through real DB method')
        ck(db.item_qty(1,'ring')==2 and db.item_qty(2,'ring')==0,'mail removes only sender free copy')
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]==5,
           'mail does not mint/delete physical copies')
        st=c.execute("SELECT instance_id,storage_kind,container FROM v106_stored_instances").fetchone()
        ck(st is not None and st[1]=='mail' and st[2]==str(mid),'mail escrow tracks exact instance')
        ck(st[0] in physical and st[0]!=worn,'equipped physical copy is never mailed')
        m=c.execute('SELECT * FROM player_mail_v03051 WHERE id=?',(mid,)).fetchone()
        ck(m['recipient_account_id']==2 and m['attachment_item_qty']==1 and not m['attachment_claimed'],
           'v105 mail item row preserved')
        ck(json.loads(m['attachment_meta_json'])=={'v106_equipment_instance':st[0]},
           'metadata references same physical identity')
        ck(c.execute('SELECT paid_silver FROM shop_purchase_lots_v1175 WHERE item_id=?',
           (f'__mail_v106__:{mid}:ring',)).fetchone()[0]==70,'cost basis moved into mail escrow')
        _check_account(c,1,CAT);ck(True,'sender ledger still valid')
        ck(db.claim_mail_attachment_v0614(3,mid) is None,'cannot receive another player mail')
        ck(db.claim_mail_attachment_v0614(2,999) is None,'nonexistent mail refused')
        # Malicious metadata may never trigger a second minted copy.
        c.execute('UPDATE player_mail_v03051 SET attachment_meta_json=? WHERE id=?',('{}',mid));c.commit()
        before=state()
        denied(lambda:db.claim_mail_attachment_v0614(2,mid),RuntimeError,'tampered metadata refused')
        ck(state()==before,'tampered claim rolled back')
        c.execute('UPDATE player_mail_v03051 SET attachment_meta_json=? WHERE id=?',
                  (json.dumps({'v106_equipment_instance':st[0]}),mid));c.commit()
        # Do not allow changing the item/kind to bypass the tracked-mail path.
        for field,bad in [('attachment_item_id','ore'),('attachment_kind','currency')]:
            old=c.execute('SELECT '+field+' FROM player_mail_v03051 WHERE id=?',
                          (mid,)).fetchone()[0]
            c.execute('UPDATE player_mail_v03051 SET '+field+'=? WHERE id=?',(bad,mid));c.commit()
            before=state()
            denied(lambda:db.claim_mail_attachment_v0614(2,mid),RuntimeError,
                   'changed '+field+' cannot downgrade physical mail to legacy')
            ck(state()==before,'tampered mail kind/id cannot change ownership or wallet')
            c.execute('UPDATE player_mail_v03051 SET '+field+'=? WHERE id=?',(old,mid));c.commit()
        # Fail after owner updates have begun, check full rollback.
        c.execute('''CREATE TRIGGER v106_mail_fail_claim BEFORE UPDATE ON player_mail_v03051
                WHEN NEW.attachment_claimed=1 BEGIN SELECT RAISE(ABORT,'fail claim'); END''');c.commit()
        before=state()
        denied(lambda:db.claim_mail_attachment_v0614(2,mid),sqlite3.IntegrityError,
               'failure to mark claimed rolls back transfer')
        ck(state()==before,'failed claim restores physical ID inventory and cost')
        c.execute('DROP TRIGGER v106_mail_fail_claim');c.commit()
        result=db.claim_mail_attachment_v0614(2,mid)
        ck(result=={'ok':True,'kind':'item','item_id':'ring','item_name':'Pierścień','qty':1},
           'mail claim uses existing return shape')
        ck(db.item_qty(1,'ring')==2 and db.item_qty(2,'ring')==1,'recipient received one copy')
        ck(c.execute('SELECT account_id FROM v106_item_instances WHERE instance_id=?',
           (st[0],)).fetchone()[0]==2,'same original ID transferred to recipient')
        ck(c.execute('SELECT 1 FROM v106_stored_instances WHERE instance_id=?',
           (st[0],)).fetchone() is None,'escrow storage cleared after claim')
        ck(c.execute('SELECT paid_silver FROM shop_purchase_lots_v1175 '
                     "WHERE account_id=2 AND item_id='ring'").fetchone()[0]==70,
           'recipient inherited original cost basis')
        ck(c.execute('SELECT COUNT(*) FROM shop_purchase_lots_v1175 WHERE item_id=?',
           (f'__mail_v106__:{mid}:ring',)).fetchone()[0]==0,
           'cost basis no longer in mail escrow')
        ck(db.claim_mail_attachment_v0614(2,mid) is None,'duplicate claim refused')
        ck(c.execute('SELECT 1 FROM v106_mail_equipment_escrow WHERE mail_id=?',
           (mid,)).fetchone() is None,'temporary escrow released after claim')
        ck(c.execute('SELECT attachment_claimed FROM player_mail_v03051 WHERE id=?',
           (mid,)).fetchone()[0]==1,'durable mail marks attachment claimed')
        _check_account(c,1,CAT);_check_account(c,2,CAT);ck(True,'both owner ledgers valid')
        db.equip(2,'neck','ring')
        ck(c.execute('SELECT instance_id FROM v106_equipped_instances WHERE account_id=2').fetchone()[0]==st[0],
           'recipient wears the very same mailed copy')
        db.unequip(2,'neck')
        ck(db.remove_item(2,'ring',1) is True,
           'received physical copy can be consumed without stale escrow FK')
        ck(c.execute('SELECT 1 FROM v106_item_instances WHERE instance_id=?',
           (st[0],)).fetchone() is None,'consumed received ID fully removed')
        # Refuse unresolved legacy attachments rather than mint new ID.
        c.execute('''INSERT INTO player_mail_v03051
             (recipient_account_id,sender_account_id,sender_name,subject,body,
              attachment_kind,attachment_item_id,attachment_item_name,attachment_item_qty)
             VALUES(2,1,'stary','stary','stary','item','ring','Pierścień',1)''');c.commit()
        oldmid=c.execute('SELECT max(id) FROM player_mail_v03051').fetchone()[0]
        before=state()
        denied(lambda:db.claim_mail_attachment_v0614(2,oldmid),RuntimeError,
               'untracked historical mail cannot create a physical clone')
        ck(state()==before,'historical mail remains claimable only after explicit reconciliation')
        db._v106_mail_shadow_disposable_copy=False
        before=state()
        denied(lambda:db.send_mail_attachment_v0614(1,2,'Nadawca',kind='item',item_id='ring'),RuntimeError,
               'mail requires explicit staging marker')
        ck(state()==before,'disabled staging prevents writes')
        db._v106_mail_shadow_disposable_copy=True
        # An interrupted SEND must not create an orphaned mail or drop inventory.
        c.execute('''CREATE TRIGGER v106_mail_fail_send BEFORE INSERT ON v106_mail_equipment_escrow
              BEGIN SELECT RAISE(ABORT,'fail send'); END''');c.commit()
        before=state()
        denied(lambda:db.send_mail_attachment_v0614(1,3,'Nadawca',kind='item',item_id='ring'),
               sqlite3.IntegrityError,'mail send failure rolls back inventory and cost')
        ck(state()==before,'failed send leaves all ledgers and mail unchanged')
        c.execute('DROP TRIGGER v106_mail_fail_send');c.commit()
        # An unauthorized stage change after sending must block reception.
        emid=db.send_mail_attachment_v0614(1,3,'Nadawca',kind='item',item_id='ring')
        sent_uid=c.execute('SELECT instance_id FROM v106_mail_equipment_escrow WHERE mail_id=?',
                           (emid,)).fetchone()[0]
        c.execute('UPDATE v106_item_instances SET evolution_stage=1 WHERE instance_id=?',
                  (sent_uid,));c.commit()
        before=state()
        denied(lambda:db.claim_mail_attachment_v0614(3,emid),RuntimeError,
               'evolution stage changed in escrow prevents receive')
        ck(state()==before,'tampered stage cannot be consumed')
        c.execute('UPDATE v106_item_instances SET evolution_stage=0 WHERE instance_id=?',
                  (sent_uid,));c.commit()
        ck(db.claim_mail_attachment_v0614(3,emid)['ok'],
           'valid escrow remains claimable after problem is resolved')
        # Sending unpurchased gear should not fabricate purchase lots.
        db.add_item(1,'helm',1)
        existing=db.item_qty(1,'helm')
        mh=db.send_mail_attachment_v0614(1,3,'Nadawca',kind='item',item_id='helm',item_name='Hełm')
        ck(type(mh)==int and db.item_qty(1,'helm')==existing-1,'unpriced gear mailed')
        ck(c.execute("SELECT COUNT(*) FROM shop_purchase_lots_v1175 WHERE account_id=3 AND item_id='helm'").fetchone()[0]==0,
           'mail does not invent paid cost')
        ck(db.claim_mail_attachment_v0614(3,mh)['ok'],'unpriced equipment received')
        ck(c.execute("SELECT COUNT(*) FROM shop_purchase_lots_v1175 WHERE account_id=3 AND item_id='helm'").fetchone()[0]==0,
           'unpriced receipt keeps no cost lots')
        _check_account(c,3,CAT);ck(True,'recipient of unpriced equipment consistent')
        ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        return checks
    finally:
        c.close()
        if original is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=original
if __name__=='__main__': print('V106 MAIL PHYSICAL EQ:',run(),'PASS')
