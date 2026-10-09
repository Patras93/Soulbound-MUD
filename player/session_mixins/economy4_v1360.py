# -*- coding: utf-8 -*-
"""NVDA-friendly commands for economy 4.0; all commerce settled by systems layer."""
from __future__ import annotations
import time
from systems import economy4_v1360 as trade
from core.bootstrap_economy_professions import currency_price_text
from data.catalogs import ITEMS


class SessionEconomy4V1360Mixin:
    def _trade_v1360(self):
        conn=self._econ_v1321()
        if not getattr(self.server.db,'_economy1360_initialized',False):
            trade.init(conn)
            self.server.db._economy1360_initialized=True
        return conn

    async def economy4_command_v1360(self,args=''):
        conn=self._trade_v1360()
        parts=str(args or '').lower().split()
        cmd=parts[0] if parts else 'pomoc'
        now=int(time.time())
        account=self.account_id
        if cmd in ('pomoc','help','info'):
            await self.send('GOSPODARKA 4.0: gospodarka ceny; gospodarka karawany; gospodarka wyslij <kod> potwierdz; gospodarka transport; gospodarka obron; gospodarka odbierz; gospodarka zamowienia; gospodarka wykonaj <kod> potwierdz; gospodarka produkcja; gospodarka rozbuduj <budynek> potwierdz; gospodarka zbierz; gospodarka rekordy.')
            await self.send('Karawany zużywają rzeczywiste towary z jednego magazynu; morskie wymagają portu, aktywnego statku i ładowni. Nagrody odbierasz po dotarciu. Brak automatycznych wypłat. Produkcja gildii pobiera koszt utrzymania ze skarbca.')
            return
        if cmd in ('ceny','karawany','szlaki'):
            await self.send('AKTUALNE KONTRAKTY TRANSPORTOWE (ceny zmieniają się co 6 godzin):')
            for code,name,item,qty,price,kind,seconds in trade.caravan_quotes(now=now):
                await self.send(f'{code}: {name}. Towar: {ITEMS[item]["name"]} x{qty}. ' +
                                f'Transport {"morski" if kind=="sea" else "lądowy"}. {seconds//60} minut. Zapłata do {currency_price_text(price)}; bez eskorty 80%.')
            await self.send('Wysyłka: gospodarka wyslij <kod> potwierdz. Towary zostaną pobrane natychmiast.')
            return
        if cmd=='transport':
            r=trade.convoy(conn,account)
            if r is None:await self.send('Nie masz bieżącego transportu.');return
            left=max(0,int(r['arrival'])-now)
            await self.send(f'Transport {r["code"]}. Ładunek: {ITEMS[r["item_id"]]["name"]} x{r["quantity"]}. '+
                            f'Pozostało {left} sekund. Eskorta: {"obroniona" if r["defended"] else "bez obrony"}. '+
                            ('Wpisz gospodarka odbierz.' if not left else 'Wpisz gospodarka obron, aby odeprzeć najazd NPC.'))
            return
        if cmd=='wyslij' and len(parts)>=2:
            code=parts[1]
            if code not in trade.ROUTES:await self.send('Nie ma takiego szlaku. Wpisz gospodarka karawany.');return
            name,item,qty,base,kind,seconds=trade.ROUTES[code]
            if kind=='sea':
                # Load Ocean 4.0 ship-condition tables before checking hull/active battles.
                self._naval_v1350()
            if kind=='sea' and not (self.ocean_port_name_v1000(self.character.room_id) or self.character.room_id=='v1310_ocean_departure'):
                await self.send('Transport morski odprawiasz w porcie.');return
            if len(parts)<3 or parts[2]!='potwierdz':
                await self.send(f'Wysłanie {name} zużyje {qty} szt. {ITEMS[item]["name"]}. Potwierdź: gospodarka wyslij {code} potwierdz.')
                return
            try:r=trade.start_convoy(conn,account,code,now=now)
            except ValueError as e:await self.send(str(e));return
            await self.send(f'Wysłano: {r["name"]}. Towary pobrano z magazynu {r["source"]}. Przybycie za {seconds//60} minut. Zysk maksymalny: {currency_price_text(r["reward"])}. Wpisz gospodarka transport.')
            return
        if cmd=='obron':
            try:msg=trade.defend_convoy(conn,account,now=now)
            except ValueError as e:await self.send(str(e));return
            await self.send(msg);return
        if cmd=='odbierz':
            try:reward,balance=trade.collect_convoy(conn,account,now=now)
            except ValueError as e:await self.send(str(e));return
            self.character.silver=balance;self.character.gold=0;self.character.mithril=0
            await self.send(f'Transport ukończony. Zarobiono {currency_price_text(reward)}. Towar zużyty, nagroda odebrana jeden raz.')
            return
        if cmd in ('zamowienia','zlecenia'):
            await self.send('WIELKIE ZAMÓWIENIA KRÓLESTW:')
            for code,name,ingredients,price in trade.order_quotes(now=now):
                items=', '.join(f'{ITEMS[i]["name"]} x{n}' for i,n in ingredients.items())
                await self.send(f'{code}: {name}. {items}. Nagroda {currency_price_text(price)}.')
            await self.send('Wykonanie: gospodarka wykonaj <kod> potwierdz. Jedno zamówienie co 2 godziny.')
            return
        if cmd=='wykonaj' and len(parts)>=2:
            code=parts[1]
            if code not in trade.ORDERS:await self.send('Nieznane zamówienie. Wpisz gospodarka zamowienia.');return
            if len(parts)<3 or parts[2]!='potwierdz':
                await self.send(f'Potwierdź przekazanie wszystkich składników: gospodarka wykonaj {code} potwierdz.')
                return
            try:name,paid,balance=trade.finish_order(conn,account,code,now=now)
            except ValueError as e:await self.send(str(e));return
            self.character.silver=balance;self.character.gold=0;self.character.mithril=0
            await self.send(f'ZAMÓWIENIE UKOŃCZONE: {name}. Nagroda: {currency_price_text(paid)}. Kolejne za 2 godziny.')
            return
        if cmd in ('produkcja','budynki'):
            guild=self.guild_row_v0926()
            if not guild:await self.send('Produkcja wymaga członkostwa w gildii.');return
            clan=int(guild['clan_id']);owned=trade.production_levels(conn,clan)
            treasury=conn.execute('SELECT treasury FROM player_clans WHERE id=?',(clan,)).fetchone()
            await self.send(f'PRODUKCJA GILDII. Skarbiec: {currency_price_text(int(treasury[0]))}. Cykl 6 godzin, maksymalnie 4 cykle do nadrobienia.')
            for key,(name,item,n,base,maint) in trade.BUILDINGS.items():
                level,last=owned.get(key,(0,now));needed=base*(level+1)**2
                ready=min(4,max(0,(now-last)//trade.SIX_HOURS))
                await self.send(f'{key}: {name}, poziom {level}/10, gotowe cykle {ready}. Produkcja {ITEMS[item]["name"]} x{n*level} na cykl. Utrzymanie {currency_price_text(maint*level)} za cykl. Rozbudowa {currency_price_text(needed)}.')
            await self.send('Komendy: gospodarka rozbuduj kopalnia/tartak/farma/warsztat potwierdz; gospodarka zbierz. Produkcja trafia do banku gildii.')
            return
        if cmd in ('rozbuduj','zbierz'):
            leader=self._leader_v1320()
            if not leader:
                await self.send('Tylko lider gildii może zarządzać produkcją i skarbcem.');return
            clan=int(leader['clan_id'])
            if cmd=='rozbuduj':
                if len(parts)<3 or parts[2]!='potwierdz':
                    await self.send('Potwierdź: gospodarka rozbuduj <kopalnia/tartak/farma/warsztat> potwierdz.');return
                try:level,cost=trade.upgrade_building(conn,clan,parts[1],now=now)
                except ValueError as e:await self.send(str(e));return
                await self.send(f'Rozbudowa zakończona. Poziom {level}. Koszt {currency_price_text(cost)} ze skarbca gildii.');return
            try:output=trade.collect_production(conn,clan,now=now)
            except ValueError as e:await self.send(str(e));return
            if not output:await self.send('Brak gotowej produkcji lub środków na utrzymanie.');return
            for name,item,qty,cost in output:
                await self.send(f'{name}: przekazano do banku gildii {ITEMS[item]["name"]} x{qty}, utrzymanie {currency_price_text(cost)}.')
            return
        if cmd=='rekordy':
            row=trade.records(conn,account)
            if row:await self.send(f'Handel: {row["convoys"]} konwojów, {row["orders"]} zamówień, zarobiono {currency_price_text(row["earned"])}.')
            else:await self.send('Brak ukończonych kontraktów.')
            return
        await self.send('Nieznana komenda. Wpisz gospodarka pomoc.')
