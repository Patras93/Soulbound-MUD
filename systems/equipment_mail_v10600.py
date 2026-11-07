# -*- coding: utf-8 -*-
"""v106 STAGING ONLY: lossless one-copy equipment mail escrow on disposable SQLite.

Mail contains the *same* physical instance, never a second minted copy. Keep
v105 mail schema untouched and fail closed for legacy/untracked attachments.
Normal v105 mail is unchanged when the staging flag is not enabled.
"""
from __future__ import annotations
import json
from systems.equipment_inventory_flow_v10600 import (
    tracked, _qty, _write_qty, _atomic, _stage_zero_not_worn,
    _legacy_modifiers,
)
from systems.equipment_shadow_slots_v10600 import _check_account
from systems.equipment_evolution_v10500 import is_evolved
from core.sqlite_numeric_guard_v10400 import require_sqlite_int64


def _require(db, item):
    if not tracked(db, item) or not getattr(db, '_v106_mail_shadow_disposable_copy', False):
        raise RuntimeError('v106 EQ: poczta fizycznych sztuk tylko na jawnej kopii testowej')


def _schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS v106_mail_equipment_escrow (
        mail_id INTEGER PRIMARY KEY, instance_id TEXT NOT NULL UNIQUE,
        sender_account_id INTEGER NOT NULL, recipient_account_id INTEGER NOT NULL,
        item_id TEXT NOT NULL, claimed INTEGER NOT NULL DEFAULT 0 CHECK(claimed IN(0,1)),
        FOREIGN KEY(instance_id) REFERENCES v106_item_instances(instance_id)
    )''')


def _move_cost(conn, db, old_owner, old_key, new_owner, new_key, qty):
    """Transfer *only* existing purchase lots; unpurchased loot stays unpriced.

    Always commit=False. All changes are enclosed by the caller's savepoint.
    """
    remaining = require_sqlite_int64('v106.mail.cost_qty', qty)
    rows = conn.execute('''SELECT paid_silver,quantity FROM shop_purchase_lots_v1175
       WHERE account_id=? AND item_id=? ORDER BY paid_silver''',
       (old_owner,old_key)).fetchall()
    for price, raw_qty in rows:
        units=min(remaining,require_sqlite_int64('v106.mail.purchased',raw_qty))
        if units<=0: continue
        if units==raw_qty:
            conn.execute('''DELETE FROM shop_purchase_lots_v1175
                WHERE account_id=? AND item_id=? AND paid_silver=?''',
                (old_owner,old_key,price))
        else:
            conn.execute('''UPDATE shop_purchase_lots_v1175 SET quantity=quantity-?
                WHERE account_id=? AND item_id=? AND paid_silver=?''',
                (units,old_owner,old_key,price))
        db.record_shop_purchase_v1175(new_owner,new_key,units,price,commit=False)
        remaining-=units
        if remaining==0: break


def send(db, from_account, to_account, sender_name, item, item_name=''):
    """Atomically create v105 mail row and escrow same free, stage-zero instance."""
    _require(db,item)
    sender=int(from_account);recipient=int(to_account);item=str(item)
    if sender==recipient:return None
    conn=db.conn;cat=db._v106_shadow_item_catalog
    def operation():
        _check_account(conn,sender,cat);_check_account(conn,recipient,cat)
        if (_qty(conn,sender,item)<1 or
            is_evolved(conn,sender,item) or _legacy_modifiers(conn,sender,item) or
            is_evolved(conn,recipient,item) or _legacy_modifiers(conn,recipient,item)):
            return None
        selected=_stage_zero_not_worn(conn,sender,item,1)
        if len(selected)!=1:return None
        uid=selected[0]
        _schema(conn)
        meta=json.dumps({'v106_equipment_instance':uid},separators=(',',':'))
        cur=conn.execute('''INSERT INTO player_mail_v03051
          (recipient_account_id,sender_account_id,sender_name,subject,body,
           attachment_kind,attachment_item_id,attachment_item_name,
           attachment_item_qty,attachment_meta_json)
          VALUES(?,?,?,?,?,'item',?,?,1,?)''',
          (recipient,sender,str(sender_name),'Przedmiot od gracza',
           'Załącznik: '+str(item_name or item)+' x1.',item,str(item_name or item),meta))
        mid=int(cur.lastrowid)
        conn.execute('''INSERT INTO v106_mail_equipment_escrow
            (mail_id,instance_id,sender_account_id,recipient_account_id,item_id)
            VALUES(?,?,?,?,?)''',(mid,uid,sender,recipient,item))
        conn.execute('''INSERT INTO v106_stored_instances
            (instance_id,account_id,storage_kind,container) VALUES(?,?,?,?)''',
            (uid,sender,'mail',str(mid)))
        _write_qty(conn,sender,item,_qty(conn,sender,item)-1)
        _move_cost(conn,db,sender,item,sender,_mail_basis(mid,item),1)
        _check_account(conn,sender,cat);_check_account(conn,recipient,cat)
        return mid
    return _atomic(conn,operation,commit=True)


def _mail_basis(mid,item):
    return '__mail_v106__:'+str(mid)+':'+str(item)


def claim(db, recipient, mail_id):
    """Receive only a verified unclaimed v106 mail, never remint an item."""
    recipient=int(recipient);mid=int(mail_id)
    conn=db.conn;cat=db._v106_shadow_item_catalog
    row=conn.execute('''SELECT * FROM player_mail_v03051
        WHERE id=? AND recipient_account_id=?''',(mid,recipient)).fetchone()
    if row is None or int(row['attachment_claimed'] or 0):return None
    item=str(row['attachment_item_id'] or '')
    _require(db,item)
    def operation():
        _check_account(conn,recipient,cat)
        _schema(conn)
        data=conn.execute('''SELECT instance_id,sender_account_id,recipient_account_id,
            item_id,claimed FROM v106_mail_equipment_escrow WHERE mail_id=?''',
            (mid,)).fetchone()
        if data is None:raise RuntimeError('v106 EQ: stary załącznik wymaga uzgodnienia na kopii bazy')
        uid,sender,destination,physical_item,claimed=data
        sender=int(sender)
        if (int(claimed)!=0 or int(destination)!=recipient or
            physical_item!=item or sender==recipient or
            row['attachment_kind']!='item' or int(row['attachment_item_qty'])!=1 or
            int(row['sender_account_id'])!=sender or
            row['attachment_coins'] not in (None,0)):
            raise RuntimeError('v106 EQ: niespójny pocztowy załącznik')
        try: meta=json.loads(row['attachment_meta_json'] or '{}')
        except (TypeError,ValueError):meta={}
        if not isinstance(meta,dict) or meta!={'v106_equipment_instance':uid}:
            raise RuntimeError('v106 EQ: zmienione metadane załącznika')
        stored=conn.execute('''SELECT st.account_id,st.storage_kind,st.container,
             i.account_id,i.item_id,i.evolution_stage
             FROM v106_stored_instances st JOIN v106_item_instances i
               ON st.instance_id=i.instance_id WHERE st.instance_id=?''',(uid,)).fetchone()
        if stored is None or tuple(stored)!=(sender,'mail',str(mid),sender,item,0):
            raise RuntimeError('v106 EQ: escrow nie wskazuje właściwej sztuki')
        _check_account(conn,sender,cat)
        if (is_evolved(conn,recipient,item) or _legacy_modifiers(conn,recipient,item)):
            raise RuntimeError('v106 EQ: odbiorca ma stare nieuzgodnione ulepszenia')
        qty=require_sqlite_int64('v106.mail.inventory',_qty(conn,recipient,item)+1)
        conn.execute('DELETE FROM v106_stored_instances WHERE instance_id=?',(uid,))
        changed=conn.execute('''UPDATE v106_item_instances SET account_id=?
          WHERE instance_id=? AND account_id=? AND item_id=? AND evolution_stage=0''',
          (recipient,uid,sender,item)).rowcount
        if changed!=1:raise RuntimeError('v106 EQ: sztuka zmieniła właściciela')
        _write_qty(conn,recipient,item,qty)
        _move_cost(conn,db,sender,_mail_basis(mid,item),recipient,item,1)
        if conn.execute('''UPDATE player_mail_v03051 SET attachment_claimed=1,is_read=1
             WHERE id=? AND recipient_account_id=? AND attachment_claimed=0''',
             (mid,recipient)).rowcount!=1:
            raise RuntimeError('v106 EQ: załącznik już odebrano')
        # The durable v105 mail row records receipt. Drop this transient
        # instance FK after claim, otherwise future selling/destroying the
        # physically received item would violate referential integrity.
        if conn.execute('''DELETE FROM v106_mail_equipment_escrow
             WHERE mail_id=? AND claimed=0''',(mid,)).rowcount!=1:
            raise RuntimeError('v106 EQ: escrow już zamknięto')
        _check_account(conn,sender,cat);_check_account(conn,recipient,cat)
        return {'ok':True,'kind':'item','item_id':item,
                'item_name':str(row['attachment_item_name'] or item),'qty':1}
    return _atomic(conn,operation,commit=True)
