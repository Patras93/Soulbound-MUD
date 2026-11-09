# -*- coding: utf-8 -*-
"""Soulbound v109: oryginalne metody, wydzielone bez zmiany kodu."""
from __future__ import annotations
from .dependencies import *

class SkyCompanionHealingV109Mixin:
    def _v1711_companions_for_healing(self, include_party=False):
        """Living, active summons of local allies only; never foreign/hidden/dead."""
        sessions=[self]
        if include_party:
            sessions=list(self.server.party_sessions(
                self.account_id, same_room=self.character.room_id) or ())
            if self not in sessions:sessions.append(self)
        results=[]
        for owner in sessions:
            if (getattr(owner,'closed',False) or not owner.character
                    or owner.character.room_id!=self.character.room_id
                    or owner.current_hp<=0):continue
            conn=owner._v1700_conn()
            owner._v1702_prepare_summon_lives(conn)
            owner._v1710_refresh_summon_health(conn)
            for row in conn.execute('SELECT summon_type,level,soul_rank,hp,max_hp '
                                    'FROM summons_v1700 WHERE account_id=? AND active=1 AND hp>0',
                                    (owner.account_id,)).fetchall():
                kind=row['summon_type']
                if kind in SUMMONS and owner._v1700_class(SUMMONS[kind][1]):
                    results.append((owner,row))
        return results

    def _v1711_find_companion(self, name, include_party=False):
        wanted=ascii_fold(name)
        if not wanted:return None
        found=[]
        for owner,row in self._v1711_companions_for_healing(include_party):
            key=row['summon_type']; grade=int(row['soul_rank'] or 0)
            names={ascii_fold(key),ascii_fold(SUMMONS[key][0]),ascii_fold(summon_display(key,grade))}
            if wanted in names:
                found.append((owner,row))
        # Own creature takes precedence. Ambiguous party matches are not guessed.
        own=[target for target in found if target[0] is self]
        if own:return own[0]
        return found[0] if len(found)==1 else None

    def _v1711_heal_companion(self, owner, row, amount):
        """Heal surviving summoned ally without resurrecting a dead one.

        SQL guard and transactional update prevent an obsolete row snapshot from
        restoring HP after a summon was destroyed or dismissed.
        """
        from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
        if superboss_healing_blocked_v11179(owner):return 0
        amount=max(0,int(amount))
        if amount<=0:return 0
        conn=owner._v1700_conn()
        current=conn.execute('SELECT hp,max_hp FROM summons_v1700 '
                             'WHERE account_id=? AND summon_type=? AND active=1 AND hp>0',
                             (owner.account_id,row['summon_type'])).fetchone()
        if not current:return 0
        before=int(current['hp']);maximum=int(current['max_hp'])
        restored=min(amount,max(0,maximum-before))
        if restored<=0:return 0
        cur=conn.execute('UPDATE summons_v1700 SET hp=hp+? '
                         'WHERE account_id=? AND summon_type=? AND active=1 AND hp=? AND max_hp=?',
                         (restored,owner.account_id,row['summon_type'],before,maximum))
        conn.commit()
        return restored if cur.rowcount==1 else 0

    async def _v1711_summon_heal_command(self, raw):
        if not self.character:return
        from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
        value=ascii_fold(raw)
        targets=self._v1711_companions_for_healing()
        if not value:
            await self.send('Użycie: chowaniec lecz <nazwa> albo chowaniec lecz wszystko. Czar kosztuje manę i nie wskrzesza pokonanych pomocników.')
            return
        if superboss_healing_blocked_v11179(self):
            await self.send('Nullify Healing blokuje leczenie przywołań.')
            return
        if value in ('wszystko','all'):
            selected=[(owner,row) for owner,row in targets if int(row['hp'])<int(row['max_hp'])]
        else:
            match=self._v1711_find_companion(value)
            if not match:
                await self.send('Nie masz aktywnego, żywego przywołania o tej nazwie. Sprawdź chowaniec lista.')
                return
            selected=[match] if int(match[1]['hp'])<int(match[1]['max_hp']) else []
        if not selected:
            await self.send('Żadne żywe przywołanie nie potrzebuje leczenia. Martwy pomocnik wymaga ponownego przywołania.')
            return
        cost=60 if len(selected)==1 else 85+25*(len(selected)-1)
        if self.current_mana<cost:
            await self.send(f'Za mało many: leczenie wymaga {cost} MP, masz {self.current_mana}.')
            return
        restored=[]
        for owner,row in selected:
            # Hybrid heal scales with summoner HP and the caster's magic/healing.
            power=max(1,int(self.healing_power_v1125()))
            amount=max(1,int(row['max_hp']*.25)+power//5)
            actual=self._v1711_heal_companion(owner,row,amount)
            if actual:
                restored.append((row['summon_type'],actual))
        if not restored:
            await self.send('Nie udało się uleczyć przywołań. Mana nie została pobrana.')
            return
        self.current_mana-=cost
        names=', '.join(f'{SUMMONS[k][0]} +{hp} HP' for k,hp in restored)
        await self.send(f'Wyleczono: {names}. Mana -{cost} MP; pozostało {self.current_mana} MP.')

