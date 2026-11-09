# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: mail; AST bez zmian."""
from .dependencies import *

class MailV109Mixin:
    def send_mail_attachment_v0614(self, from_account_id, to_account_id, sender_name, *, kind, item_id="", item_name="", amount_silver=0):
        """Atomowo odkłada jeden przedmiot albo walutę w pocztowym escrow."""
        from_account_id=int(from_account_id); to_account_id=int(to_account_id)
        kind=str(kind or "")
        if from_account_id==to_account_id or kind not in ("item","currency"):
            return None

        meta={}
        current=0
        if kind=="item":
            item_id=str(item_id or "")
            from systems.equipment_inventory_flow_v10600 import tracked
            if tracked(self, item_id):
                from systems.equipment_mail_v10600 import send
                return send(self, from_account_id, to_account_id, sender_name, item_id, item_name)

            from systems.equipment_evolution_v10500 import is_evolved
            if is_evolved(self.conn, from_account_id, item_id):
                return None  # no evolved equipment in mail escrow
            row=self.conn.execute(
                "SELECT quantity FROM inventory WHERE account_id=? AND item_id=?",
                (from_account_id,item_id),
            ).fetchone()
            current=int(row["quantity"] or 0) if row else 0
            if current<1:
                return None
            # Dane ulepszeń są per account+item_id. Gdy ostatnia sztuka opuszcza
            # konto, przenosimy je do escrow i odtwarzamy przy odbiorze.
            if current==1:
                ref=self.conn.execute(
                    "SELECT affix,affix_amount,rerolls FROM equipment_reforges WHERE account_id=? AND item_id=?",
                    (from_account_id,item_id),
                ).fetchone()
                up=self.conn.execute(
                    "SELECT upgrade_level FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
                    (from_account_id,item_id),
                ).fetchone()
                runes=self.conn.execute(
                    "SELECT socket_index,rune_id FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? ORDER BY socket_index",
                    (from_account_id,item_id),
                ).fetchall()
                bonus=self.conn.execute(
                    "SELECT bonus_sockets FROM equipment_socket_bonus_v03114 WHERE account_id=? AND item_id=?",
                    (from_account_id,item_id),
                ).fetchone()
                mark=self.conn.execute(
                    "SELECT mark FROM tech_set_upgrades_v0320 WHERE account_id=? AND item_id=?",
                    (from_account_id,item_id),
                ).fetchone()
                if ref: meta["reforge"]={"affix":ref["affix"],"affix_amount":int(ref["affix_amount"]),"rerolls":int(ref["rerolls"])}
                if up: meta["upgrade_level"]=int(up["upgrade_level"] or 0)
                if runes: meta["runes"]=[{"socket_index":int(r["socket_index"]),"rune_id":str(r["rune_id"])} for r in runes]
                if bonus: meta["bonus_sockets"]=int(bonus["bonus_sockets"] or 0)
                if mark: meta["tech_mark"]=int(mark["mark"] or 1)
        else:
            amount_silver=int(amount_silver or 0)
            if amount_silver<=0 or amount_silver>CURRENCY_SQLITE_SAFE_TOTAL:
                return None
            from_master=self.master_account_for_character(from_account_id)
            to_master=self.master_account_for_character(to_account_id)
            if int(from_master)==int(to_master):
                return None
            from_total=int(self.shared_wallet_for_master(from_master)[0])
            to_total=int(self.shared_wallet_for_master(to_master)[0])
            if from_total<amount_silver or to_total+amount_silver>CURRENCY_SQLITE_SAFE_TOTAL:
                return None

        try:
            self.conn.execute("BEGIN")
            if kind=="item":
                if current<=1:
                    self.conn.execute("DELETE FROM inventory WHERE account_id=? AND item_id=?",(from_account_id,item_id))
                    for table in ("equipment_reforges","equipment_upgrades_v03042","equipment_runes_v0925","equipment_socket_bonus_v03114","tech_set_upgrades_v0320"):
                        self.conn.execute(f"DELETE FROM {table} WHERE account_id=? AND item_id=?",(from_account_id,item_id))
                else:
                    self.conn.execute("UPDATE inventory SET quantity=quantity-1 WHERE account_id=? AND item_id=?",(from_account_id,item_id))
                subject="Przedmiot od gracza"
                body=f"Załącznik: {item_name or item_id} x1."
                cur=self.conn.execute(
                    "INSERT INTO player_mail_v03051(recipient_account_id,sender_account_id,sender_name,subject,body,attachment_kind,attachment_item_id,attachment_item_name,attachment_item_qty,attachment_meta_json) "
                    "VALUES(?,?,?,?,?,'item',?,?,1,?)",
                    (to_account_id,from_account_id,str(sender_name),subject,body,item_id,str(item_name or item_id),json.dumps(meta,ensure_ascii=False,separators=(',',':'))),
                )
            else:
                self.set_shared_wallet_for_master(from_master,from_total-amount_silver,0,0,commit=False)
                subject="Waluta od gracza"
                body=f"Załącznik walutowy: {amount_silver} jednostek srebra bazowego."
                cur=self.conn.execute(
                    "INSERT INTO player_mail_v03051(recipient_account_id,sender_account_id,sender_name,subject,body,attachment_kind,attachment_coins) "
                    "VALUES(?,?,?,?,?,'currency',?)",
                    (to_account_id,from_account_id,str(sender_name),subject,body,amount_silver),
                )
            self.conn.commit()
            return int(cur.lastrowid)
        except Exception:
            self.conn.rollback()
            raise

    def claim_mail_attachment_v0614(self, account_id, mail_id):
        """Atomowo odbiera załącznik i oznacza go jako odebrany."""
        account_id=int(account_id); mail_id=int(mail_id)
        row=self.conn.execute(
            "SELECT * FROM player_mail_v03051 WHERE id=? AND recipient_account_id=?",
            (mail_id,account_id),
        ).fetchone()
        if not row or int(row["attachment_claimed"] or 0):
            return None
        # A staging physical escrow must never fall through the v105 generic
        # item/currency path after its mail row was edited or corrupted.
        if (getattr(self, '_v106_shadow_slots_disposable_copy', False) and
                getattr(self, '_v106_mail_shadow_disposable_copy', False)):
            from systems.equipment_inventory_flow_v10600 import tracked as _v106_tracked_mail
            from systems.v10700_eq_runtime_gate import is_enabled as _v107_eq_is_enabled
            if _v107_eq_is_enabled(self):
                linked_table=self.conn.execute("SELECT 1 FROM sqlite_master "
                    "WHERE type='table' AND name='v106_mail_equipment_escrow'").fetchone()
                if linked_table and self.conn.execute(
                    'SELECT 1 FROM v106_mail_equipment_escrow WHERE mail_id=?',
                    (mail_id,)).fetchone():
                    from systems.equipment_mail_v10600 import claim
                    return claim(self, account_id, mail_id)
        kind=str(row["attachment_kind"] or "")
        if kind=="item":
            from systems.equipment_inventory_flow_v10600 import tracked
            if tracked(self, row["attachment_item_id"]):
                from systems.equipment_mail_v10600 import claim
                return claim(self, account_id, mail_id)
        if kind not in ("item","currency"):
            return None
        if kind=="currency":
            amount=int(row["attachment_coins"] or 0)
            master=self.master_account_for_character(account_id)
            current=int(self.shared_wallet_for_master(master)[0])
            if amount<=0 or current+amount>CURRENCY_SQLITE_SAFE_TOTAL:
                return {"ok":False,"reason":"wallet_cap","kind":kind,"amount":amount}
        try:
            self.conn.execute("BEGIN")
            if kind=="item":
                item_id=str(row["attachment_item_id"] or "")
                qty=max(1,int(row["attachment_item_qty"] or 1))
                self.conn.execute(
                    "INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?) "
                    "ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity",
                    (account_id,item_id,qty),
                )
                try: meta=json.loads(str(row["attachment_meta_json"] or "{}"))
                except Exception: meta={}
                ref=meta.get("reforge") if isinstance(meta,dict) else None
                if isinstance(ref,dict):
                    self.conn.execute(
                        "INSERT OR REPLACE INTO equipment_reforges(account_id,item_id,affix,affix_amount,rerolls) VALUES(?,?,?,?,?)",
                        (account_id,item_id,str(ref.get("affix") or ""),int(ref.get("affix_amount") or 0),int(ref.get("rerolls") or 0)),
                    )
                level=int(meta.get("upgrade_level",0) or 0) if isinstance(meta,dict) else 0
                if level>0:
                    self.conn.execute("INSERT OR REPLACE INTO equipment_upgrades_v03042(account_id,item_id,upgrade_level) VALUES(?,?,?)",(account_id,item_id,level))
                for rr in (meta.get("runes") or []) if isinstance(meta,dict) else []:
                    self.conn.execute("INSERT OR REPLACE INTO equipment_runes_v0925(account_id,item_id,socket_index,rune_id) VALUES(?,?,?,?)",(account_id,item_id,int(rr.get("socket_index") or 0),str(rr.get("rune_id") or "")))
                bonus=int(meta.get("bonus_sockets",0) or 0) if isinstance(meta,dict) else 0
                if bonus>0:
                    self.conn.execute("INSERT OR REPLACE INTO equipment_socket_bonus_v03114(account_id,item_id,bonus_sockets) VALUES(?,?,?)",(account_id,item_id,bonus))
                mark=int(meta.get("tech_mark",1) or 1) if isinstance(meta,dict) else 1
                if mark>1:
                    self.conn.execute("INSERT OR REPLACE INTO tech_set_upgrades_v0320(account_id,item_id,mark) VALUES(?,?,?)",(account_id,item_id,mark))
                result={"ok":True,"kind":"item","item_id":item_id,"item_name":str(row["attachment_item_name"] or item_id),"qty":qty}
            else:
                amount=int(row["attachment_coins"] or 0)
                self.set_shared_wallet_for_master(master,current+amount,0,0,commit=False)
                result={"ok":True,"kind":"currency","amount":amount}
            self.conn.execute("UPDATE player_mail_v03051 SET attachment_claimed=1,is_read=1 WHERE id=? AND recipient_account_id=?",(mail_id,account_id))
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
