# -*- coding: utf-8 -*-
"""Soulbound v109: oryginalne metody, wydzielone bez zmiany kodu."""
from __future__ import annotations
from .dependencies import *

class SkySummonStateV109Mixin:
    def _v1700_conn(self):
        conn=self.server.db.conn
        if not getattr(self.server.db,'_v1700_ready',False):
            ensure_schema(conn)
            self.server.db._v1700_ready=True
        return conn

    def _v1700_qty(self, item):
        db=self.server.db
        return db.item_qty(self.account_id,item)+db.storage_qty(self.account_id,'craftbox',item)

    def _v1700_spend_and_write(self,required,sql,params):
        """Atomically consume mats and persist summon or upgrade, or change nothing."""
        db=self.server.db
        if any(self._v1700_qty(k)<v for k,v in required.items()):return False
        conn=db.conn
        conn.execute('SAVEPOINT v1700_summon')
        try:
            for item,qty in required.items():
                from_box=min(db.storage_qty(self.account_id,'craftbox',item),qty)
                if from_box and not db.remove_storage_item(self.account_id,'craftbox',item,from_box,commit=False):
                    raise RuntimeError('Błąd rezerwacji materiału')
                if qty>from_box and not db.remove_item(self.account_id,item,qty-from_box,commit=False):
                    raise RuntimeError('Błąd rezerwacji materiału')
            conn.execute(sql,params)
            conn.execute('RELEASE SAVEPOINT v1700_summon')
            conn.commit()
            return True
        except Exception:
            conn.execute('ROLLBACK TO SAVEPOINT v1700_summon')
            conn.execute('RELEASE SAVEPOINT v1700_summon')
            raise

    def _v1702_summon_max_hp(self, kind, level=1, owner_hp=None):
        """Give each summon its own durable life pool, scaled to its owner."""
        if owner_hp is None:
            try:
                owner_hp=max(1,int(self.max_hp()))
            except (AttributeError,TypeError,ValueError):
                owner_hp=max(100,int(getattr(self.character,'character_level',1) or 1)*100)
        kind_spec=SUMMONS[kind]
        factor={'pajak':.35,'wojownik':.80,'mag':.55,'lifeoak':.95,
                'ancientoak':1.55,'wilk':.50,'sowa':.42,'niedzwiedz':1.1}.get(kind,.65)
        elemental=ELEMENTALS.get(kind)
        if elemental:
            factor=(.40,.65,.95)[elemental['rank']]
            if elemental['element'] in ('lod','krysztal'):
                factor*=1.35
        if kind in ANIMALS:
            factor=ANIMALS[kind]['hp_factor']
        if kind in NECRO_MINIONS:
            factor=NECRO_MINIONS[kind][6]
        if kind in CLASS_MINIONS_V1119:
            factor=CLASS_MINIONS_V1119[kind][7]
        from systems.live_olc24_revolution import summon_factor
        from systems.live_olc29_creation import ACTIVE as _custom_summons30
        authored_hp = _custom_summons30['summons'].get(kind,{}).get('hp_percent',100)
        return max(40,int(owner_hp*factor*(1+max(0,int(level)-1)*.075)*summon_factor(kind,'hp_percent')/100*authored_hp/100))

    def _v1806_owner_summon_level(self, kind, fallback=1):
        """Battle level follows the owner, never a second creature XP curve."""
        character = getattr(self, 'character', None)
        own = getattr(character, 'character_level', None)
        if own is None:
            own = getattr(character, 'level', fallback)
        try:
            return max(1, int(own or fallback))
        except (TypeError, ValueError):
            return max(1, int(fallback or 1))

    def _v1710_refresh_summon_health(self, conn):
        """Synchronize every acquired summon to owner level/stats, retaining wounds.

        Existing soulstone rank and known creatures stay in SQLite. Dormant/dead
        creatures never get resurrected by this migration or by level changes.
        Legacy creature EXP is cleared only for the current account.
        """
        rows = conn.execute('SELECT summon_type,level,xp,hp,max_hp,active FROM summons_v1700 '
                            'WHERE account_id=?', (self.account_id,)).fetchall()
        changed = 0
        # Owner HP is invariant within one synchronization; compute it once
        # instead of repeating its full equipment/stat calculation per minion.
        try:
            owner_hp = max(1, int(self.max_hp()))
        except (AttributeError, TypeError, ValueError):
            owner_hp = max(100, int(getattr(self.character, 'character_level', 1) or 1) * 100)
        for r in rows:
            kind = r['summon_type']
            if kind not in SUMMONS:
                continue
            owner_level = self._v1806_owner_summon_level(kind, r['level'])
            old_max = max(1, int(r['max_hp'] or 0))
            new_max = self._v1702_summon_max_hp(kind, owner_level, owner_hp=owner_hp)
            old_hp = max(0, int(r['hp'] or 0))
            # Preserve an actual death and the relative HP of a wounded summon.
            new_hp = (0 if old_hp <= 0 else
                      max(1, min(new_max, (old_hp * new_max + old_max - 1) // old_max)))
            if (int(r['level']) == owner_level and int(r['xp'] or 0) == 0
                    and int(r['max_hp']) == new_max and old_hp == new_hp):
                continue
            conn.execute('UPDATE summons_v1700 SET level=?,xp=0,hp=?,max_hp=? '
                         'WHERE account_id=? AND summon_type=?',
                         (owner_level, new_hp, new_max, self.account_id, kind))
            changed += 1
        if changed:
            conn.commit()
        return changed

    def _v1710_earn_summon_xp(self, conn, kind, damage):
        """Compatibility method: summons no longer earn separate combat EXP."""
        return False

    def _v1806_summon_rest_regen(self):
        """Quiet out-of-combat HP regeneration, including when owner HP is full.

        Called every five seconds by the existing standing-regen task. Regenerate
        any alive/active creature; never revive a fallen or dismissed summon.
        """
        if (not getattr(self, 'character', None) or getattr(self, 'closed', False)
                or getattr(self, 'combat_mob_key', None)
                or int(getattr(self, 'current_hp', 0) or 0) <= 0):
            return 0
        from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
        if superboss_healing_blocked_v11179(self):
            return 0
        conn = self._v1700_conn()
        self._v1702_prepare_summon_lives(conn)
        self._v1710_refresh_summon_health(conn)
        rows = conn.execute('SELECT summon_type,hp,max_hp FROM summons_v1700 '
                            'WHERE account_id=? AND active=1 AND hp>0 AND hp<max_hp',
                            (self.account_id,)).fetchall()
        healed = 0
        for r in rows:
            kind = r['summon_type']
            if kind not in SUMMONS or not self._v1700_class(SUMMONS[kind][1]):
                continue
            maximum = max(1, int(r['max_hp']))
            from systems.live_olc24_revolution import summon_factor
            gain = max(1, (maximum * 3 * summon_factor(kind,'regen_percent') + 9999) // 10000)
            new_hp = min(maximum, int(r['hp']) + gain)
            if new_hp <= int(r['hp']):
                continue
            cur = conn.execute('UPDATE summons_v1700 SET hp=? WHERE '
                               'account_id=? AND summon_type=? AND active=1 '
                               'AND hp=? AND hp>0',
                               (new_hp, self.account_id, kind, int(r['hp'])))
            healed += int(cur.rowcount == 1)
        if healed:
            conn.commit()
        return healed

    def _v1702_prepare_summon_lives(self,conn):
        """One-time backfill of pre-HP live pets. Dead (max_hp>0) stay dead."""
        rows=conn.execute('SELECT summon_type,level,active,max_hp FROM summons_v1700 '
                          'WHERE account_id=? AND max_hp=0',(self.account_id,)).fetchall()
        for row in rows:
            kind=row['summon_type']
            if kind not in SUMMONS:continue
            maximum=self._v1702_summon_max_hp(kind,row['level'])
            conn.execute('UPDATE summons_v1700 SET hp=?,max_hp=? '
                         'WHERE account_id=? AND summon_type=? AND max_hp=0',
                         (maximum if row['active'] else 0,maximum,self.account_id,kind))
        if rows:conn.commit()

    def _v1703_dismiss_summons_on_login(self):
        """No summon survives a new session, but mastery/rank are permanent.

        Do not infer existence from the old persisted `active` flag: on a new
        login every companion (including hidden ones) must be cast anew.
        This applies to skeletons, druid creatures/trees and elementals alike.
        The next cast always requires mana and its original physical materials.
        """
        if not self.character or self.account_id is None:
            return 0
        conn=self._v1700_conn()
        self._v1702_prepare_summon_lives(conn)  # migrate older schemas first
        cur=conn.execute('UPDATE summons_v1700 SET active=0, hp=0 '
                         'WHERE account_id=? AND (active<>0 OR hp<>0)',
                         (self.account_id,))
        conn.commit()
        return max(0,int(cur.rowcount))

    def _v1702_upgrade_summon_life(self,conn,kind,level):
        """More levels add max HP, but never bring a fallen servant to life."""
        row=conn.execute('SELECT hp,max_hp FROM summons_v1700 WHERE account_id=? AND summon_type=?',
                         (self.account_id,kind)).fetchone()
        if not row:return
        old_max=max(0,int(row['max_hp']))
        new_max=self._v1702_summon_max_hp(kind,level)
        current=int(row['hp'])
        new_hp=0 if current<=0 else min(new_max,max(1,current+max(0,new_max-old_max)))
        conn.execute('UPDATE summons_v1700 SET hp=?,max_hp=? WHERE account_id=? AND summon_type=?',
                     (new_hp,new_max,self.account_id,kind));conn.commit()

