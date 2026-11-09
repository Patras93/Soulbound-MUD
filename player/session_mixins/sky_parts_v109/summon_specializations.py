# -*- coding: utf-8 -*-
"""v109: oryginalne specjalizacje przywołań i klas."""
from __future__ import annotations
from .dependencies import *

class SkySummonSpecializationsV109Mixin:
    def _v1700_class(self, name):
        return bool(self.character and name in self.active_class_names())

    async def mage_elementals_v1702(self,raw=''):
        """Player-facing Polish and English-friendly elemental spell command."""
        if not self.character:return
        if not self._v1700_class('Mag'):
            await self.send('Przywoływanie żywiołaków wymaga aktywnej klasy Maga.');return
        args=ascii_fold(raw).split()
        if not args or args[0] in ('lista','pomoc','status','info'):
            await self.send('MAG — ŻYWIOŁAKI: mag przywolaj <ogien|blyskawice|lod|krysztal> [mniejszy|zwykly|potezny].')
            await self.send('Mag schowaj <żywioł> [stopień]; mag aktywuj <żywioł> [stopień]. Każde wezwanie kosztuje MP i każde trafienie zużywa trochę many. Bez materiałów.')
            for element,(label,_) in ELEMENTS.items():
                costs=', '.join(f'{RANKS[i]} {ELEMENTALS[f"zywiolak_{element}_{RANKS[i]}"]["mana"]} MP' for i in range(3))
                await self.send(f'Żywiołak {label}: {costs}.')
            await self.summons_v1700('lista')
            return
        action=args[0]
        if action in ('wezwij','summon'):action='przywolaj'
        if action in ('ukryj','odwolaj'):action='schowaj'
        if action in ('przywroc','wlacz'):action='aktywuj'
        if action not in ('przywolaj','schowaj','aktywuj'):
            await self.send('Użyj mag przywolaj, mag schowaj albo mag aktywuj, a następnie żywioł i moc.');return
        kind=resolve_elemental(args[1:])
        if kind is None:
            await self.send('Nieznany żywioł lub stopień. Przykład: mag przywolaj lod potezny.');return
        await self.summons_v1700(f'{action} {kind}')

    async def necro_v1700(self,raw=''):
        query=ascii_fold(raw)
        if query in ('lista','konstrukty','przywolania','pomoc'):
            await self.send('NEKROMANTA — konstrukty i nieumarli. Wybierz: nekro przywolaj <nazwa>. Mana za przywołanie i utrzymanie w walce; materiały z kopalni, drwalstwa i łupów. Limit 3 aktywnych. Ulepszanie szkieletów: Kamienie Duszy.')
            for key,spec in NECRO_MINIONS.items():
                mat=', '.join(f'{n} x {qty}' for n,qty in spec[3].items())
                await self.send(f'{spec[0]} ({key}): poziom {spec[1]}+, {spec[2]} MP, utrzymanie {spec[8]} MP/atak, {mat}; rola: {spec[7]}.')
            await self.send('Szkielety: pajak (zęby zwykłe), wojownik i mag (smocze zęby). Wszystkie przywołania mają poziom właściciela i nie zdobywają własnego EXP; Kamienie Duszy nadal zwiększają rezonans szkieletów.')
            return
        if query.startswith('wyrwij'):
            await self._v1700_rip_soul()
        elif ascii_fold(raw).startswith('scal '):
            await self._v1701_forge(ascii_fold(raw)[5:])
        else:
            await self.summons_v1700(raw)

    async def druid_call_v1708(self, raw=''):
        """Area-sensitive druid calls; a squirrel brings materials then leaves."""
        if not self._v1700_class('Druid'):
            await self.send('Tylko Druid może użyć call.');return
        from data.rooms import ROOMS
        area=biome_for_room(ROOMS.get(self.character.room_id, {}), self.character.room_id)
        available=terrain_animals(area)
        druid_level=max(1,int(getattr(self.character,'character_level',1) or 1))
        cmd=ascii_fold(raw)
        if cmd.startswith(('odwolaj ', 'dismiss ')):
            who = cmd.split(' ', 1)[1].strip()
            if who in ('all', 'wszystkie', 'wszystko'):
                # `call` specifically dismisses Druids' animals, not allied
                # Necromancer or Mage summons on a multi-class character.
                conn = self._v1700_conn()
                keys = tuple(k for k in ANIMALS if k in SUMMONS)
                if not keys:
                    await self.send('Brak zwierząt do odwołania.');return
                cur = conn.execute('UPDATE summons_v1700 SET active=0 WHERE account_id=? AND active=1 AND summon_type IN (' + ','.join('?' for _ in keys) + ')', (self.account_id,*keys))
                conn.commit()
                await self.send(f'Odwołano {cur.rowcount} aktywnych zwierząt. Postęp pozostaje zapisany.')
                return
            kind = normalize_animal(who)
            if kind not in ANIMALS:
                await self.send('Nieznane zwierzę. Sprawdź call list.');return
            await self.summons_v1700('odwolaj ' + kind)
            return
        if cmd in ('odwolaj','dismiss'):
            await self.send('Użycie: call odwolaj <zwierzę|wszystkie>.');return
        if not cmd or cmd in ('list','lista','zwierzeta'):
            await self.send(f'CALL LIST — teren: {area}. Dostępne zwierzęta:')
            for kind in available:
                if kind=='squirrel':
                    await self.send('wiewiórka (squirrel) — 20 MP, przynosi szyszki i ucieka; nie zajmuje miejsca w drużynie.')
                else:
                    desc=ANIMALS[kind]
                    unlock=desc.get('min_level',0)
                    locked=f' — wymaga poziomu Druida {unlock}' if druid_level<unlock else ''
                    await self.send(f"{desc['name']} ({desc['call']}) — {desc['mana']} MP; {desc['role']}; {desc['rarity']}{locked}.")
            return
        kind=normalize_animal(cmd)
        if kind not in available:
            await self.send('Tego zwierzęcia nie przywołasz na tym terenie. Wpisz call list.');return
        if kind!='squirrel' and druid_level<ANIMALS[kind].get('min_level',0):
            await self.send(f'Ten pomocnik wymaga poziomu Druida {ANIMALS[kind]["min_level"]}. Twoja mana i materiały pozostały bez zmian.');return
        if self.combat_mob_key:
            await self.send('Przywołanie zwierzęcia wymaga zakończenia walki.');return
        if kind=='squirrel':
            cost=20
            conn=self._v1700_conn();now=int(time.time())
            row=conn.execute('SELECT last_gather FROM druid_pinecones_v1702 WHERE account_id=?',(self.account_id,)).fetchone()
            remain=90-(now-int(row['last_gather']) if row else 9999)
            if remain>0:
                await self.send(f'Wiewiórka wróci najwcześniej za {remain} s.');return
            if not await self._v1701_need_mana(cost):return
            amount=2+min(2,max(0,int(self.character.character_level)//200))
            conn.execute('SAVEPOINT v1708_squirrel')
            try:
                self.server.db.add_item(self.account_id,'v1702_pinecone',amount,commit=False)
                conn.execute('INSERT INTO druid_pinecones_v1702(account_id,last_gather) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET last_gather=excluded.last_gather',(self.account_id,now))
                conn.execute('RELEASE SAVEPOINT v1708_squirrel');conn.commit()
            except Exception:
                conn.execute('ROLLBACK TO SAVEPOINT v1708_squirrel');conn.execute('RELEASE SAVEPOINT v1708_squirrel');raise
            self.current_mana-=cost
            await self.send(f'Przybiega wiewiórka, rzuca w Ciebie {amount} szyszkami i ucieka. Otrzymujesz {amount} Szyszki Pradawnego Gaju. Mana -{cost} MP. Razem: {self._v1700_qty("v1702_pinecone")}.')
            return
        await self.summons_v1700(f'przywolaj {kind}')

    async def druid_order_v1708(self, raw=''):
        """Orders alter real summoned companions' combat behavior."""
        if not (self._v1700_class('Druid') or self._v1700_class('Nekromanta')):
            await self.send('Rozkazy wymagają klasy Druida lub Nekromanty.');return
        allowed=lambda kind: kind in ANIMALS if self._v1700_class('Druid') else kind in SUMMONS and SUMMONS[kind][1]=='Nekromanta'
        text=ascii_fold(raw).split()
        if text in (['list'],['lista']):
            conn=self._v1700_conn()
            rows=conn.execute('SELECT summon_type,stance FROM summons_v1700 WHERE account_id=? AND active=1 AND hp>0',(self.account_id,)).fetchall()
            active=[r for r in rows if allowed(r['summon_type'])]
            if not active:
                await self.send('Nie masz aktywnych przywołań. Sprawdź call list albo nekro lista.');return
            for r in active:
                await self.send(f"{SUMMONS[r['summon_type']][0]}: {r['stance']}.")
            return
        if len(text)<2:
            await self.send('Rozkazy: order <pomocnik|all> <atakuj|bron|wspieraj|czekaj>. Możesz też wpisać order list.');return
        stance={'atakuj':'atakuj','attack':'atakuj','bron':'bron','defend':'bron',
                'wspieraj':'wspieraj','support':'wspieraj','czekaj':'czekaj','stay':'czekaj'}.get(text[-1])
        if stance is None:
            await self.send('Dostępne rozkazy: atakuj, bron, wspieraj, czekaj.');return
        name=' '.join(text[:-1]);conn=self._v1700_conn()
        if name in ('all','wszystkie'):
            active=[r['summon_type'] for r in conn.execute('SELECT summon_type FROM summons_v1700 WHERE account_id=? AND active=1 AND hp>0',(self.account_id,)) if allowed(r['summon_type'])]
            if not active:
                await self.send('Nie masz aktywnych zwierząt do wydawania rozkazów.');return
            conn.executemany('UPDATE summons_v1700 SET stance=? WHERE account_id=? AND summon_type=?',[(stance,self.account_id,k) for k in active]);conn.commit()
            await self.send(f'Rozkaz {stance} otrzymują {len(active)} zwierzęta.');return
        kind=normalize_animal(name) if self._v1700_class('Druid') else summon_key(name)
        if not allowed(kind):
            await self.send('Nieznane przywołanie. Wpisz call list albo nekro lista.');return
        cur=conn.execute('UPDATE summons_v1700 SET stance=? WHERE account_id=? AND summon_type=? AND active=1 AND hp>0',(stance,self.account_id,kind))
        conn.commit()
        if not cur.rowcount:
            await self.send('Najpierw przywołaj żywego pomocnika przez call lub nekro przywolaj.');return
        await self.send(f"{SUMMONS[kind][0]} otrzymuje rozkaz: {stance}.")

    async def druid_v1700(self,raw=''):
        if not self._v1700_class('Druid'):
            await self.send('Tylko Druid może używać magii natury.');return
        cmd=ascii_fold(raw)
        if cmd in ('szyszki','materialy','materiały'):
            await self.send(f'Szyszki Pradawnego Gaju: {self._v1700_qty("v1702_pinecone")}. Life Oak: poziom 150+, 2 szyszki i 80 MP; Ancient Oak: poziom 400+, 5 szyszek i 180 MP. Zdobywaj: call squirrel. Wymień stare nasiona: druid wymien.')
            return
        if cmd in ('zbierz','zbierz szyszki','szukaj szyszek'):
            await self.send('Szyszki przynosi wiewiórka. Wpisz call squirrel (koszt 20 MP, odnowienie 90 s).')
            return
        if cmd in ('lista','zwierzeta','zwierzęta','call list'):
            await self.druid_call_v1708('list')
            return
        if cmd in ('wymien','wymien nasiona','wymien nasiono'):
            old='v1700_nature_seed'; owned=self._v1700_qty(old)
            if owned<1:
                await self.send('Nie masz Nasion Pradawnego Gaju do wymiany.');return
            conn=self._v1700_conn();db=self.server.db
            conn.execute('SAVEPOINT v1702_exchange')
            try:
                from_box=min(owned,db.storage_qty(self.account_id,'craftbox',old))
                if from_box and not db.remove_storage_item(self.account_id,'craftbox',old,from_box,commit=False):raise RuntimeError('Brak nasion')
                if owned>from_box and not db.remove_item(self.account_id,old,owned-from_box,commit=False):raise RuntimeError('Brak nasion')
                db.add_item(self.account_id,'v1702_pinecone',owned*2,commit=False)
                conn.execute('RELEASE SAVEPOINT v1702_exchange');conn.commit()
            except Exception:
                conn.execute('ROLLBACK TO SAVEPOINT v1702_exchange');conn.execute('RELEASE SAVEPOINT v1702_exchange');raise
            await self.send(f'Wymieniono {owned} nasion na {owned*2} szyszek bez utraty wartości zapasów.');return
        await self.summons_v1700(raw)

