# -*- coding: utf-8 -*-
"""v1.32.1 player commands: accessible strategic sieges, escrow bids and ship fleet."""
from __future__ import annotations

import time
from core.bootstrap_economy_professions import currency_price_text
from core.mines_threat import ITEMS
from systems import imperial_economy_v1320 as old
from systems import imperial_economy_v1321 as new
from player.session_mixins.imperial_economy_v1320 import _norm


class SessionImperialEconomyV1321Mixin:
    def _econ_v1321(self):
        conn=self._econ_v1320()
        if not getattr(self.server.db,'_economy1321_initialized',False):
            new.init(conn)
            self.server.db._economy1321_initialized=True
        return conn

    async def siege_command_v1320(self,args=''):
        conn=self._econ_v1321()
        parts=_norm(args).split()
        if not parts or parts[0] not in old.FORTS:
            await self.send('OBLĘŻENIA 2.0: oblezenie <kod> rozpocznij potwierdz; oblezenie <kod> status; oblezenie <kod> rozkaz natarcie/ostrzal/magia/oslona; oblezenie <kod> odwrot potwierdz. Dawna komenda oblezenie <kod> potwierdz rozpoczyna teraz bitwę w trzech etapach.')
            return
        key=parts[0]
        if len(parts)>1 and parts[1] in ('potwierdz','tak','confirm'):
            # Backward-compatible command syntax: it STARTS the strategic siege,
            # never skips its three phases and casualties.
            parts=[key,'rozpocznij','potwierdz']
        if len(parts)==1 or parts[1] not in ('rozpocznij','start','status','rozkaz','odwrot'):
            await self.send('Oblężenie: oblezenie <kod> rozpocznij potwierdz; oblezenie <kod> status; oblezenie <kod> rozkaz natarcie/ostrzal/magia/oslona.')
            return
        leader=self._leader_v1320()
        if not leader:
            await self.send('Oblężeniem kieruje lider gildii.');return
        cid=int(leader['clan_id'])
        slugs={'bazalt':'emp_deep','chmury':'emp_sky','valdoria':'emp_lost','orkowie':'emp_orc'}
        if str(self.character.room_id) not in (f'v1310_{slugs[key]}_gate',f'v1310_{slugs[key]}_outpost'):
            await self.send('Do oblężenia idź pod bramę lub na posterunek tej twierdzy. Wpisz ery imperia.');return
        action=parts[1]
        if action=='status':
            row=conn.execute('SELECT * FROM siege_battles_v1321 WHERE fort=?',(key,)).fetchone()
            if not row:
                await self.send('Żadne strategiczne oblężenie tej twierdzy nie trwa.');return
            if int(row['clan_id'])!=cid:
                await self.send('Inna gildia prowadzi obecnie oblężenie.');return
            await self.send(f'OBLĘŻENIE {old.FORTS[key][0]}. Etap {row["phase"]}/3: {new.PHASES[int(row["phase"])-1]}. Pozostała obrona {row["remaining"]}. Liczba rozkazów {row["turns"]}/24. Siła armii {old.troop_strength(conn,cid)}.')
            await self.send('Rozkazy: natarcie, ostrzal, magia, oslona. Najskuteczniej: brama natarcie, dziedziniec ostrzal, cytadela magia.');return
        if action in ('rozpocznij','start'):
            if len(parts)<3 or parts[2] not in ('potwierdz','tak','confirm'):
                await self.send(f'Strategiczne oblężenie {old.FORTS[key][0]}: trzy etapy, straty za każdy rozkaz. Potwierdź: oblezenie {key} rozpocznij potwierdz.');return
            try:res=new.start_siege(conn,cid,key)
            except ValueError as exc:await self.send(str(exc));return
            await self.send(f'ROZPOCZĘTO OBLĘŻENIE {old.FORTS[key][0]}! Brama: {res} punktów obrony. Wpisz oblezenie {key} rozkaz natarcie/ostrzal/magia/oslona.');return
        if action=='rozkaz':
            if len(parts)!=3 or parts[2] not in new.ORDERS:
                await self.send('Rozkaz: natarcie, ostrzal, magia albo oslona.');return
            try:result=new.siege_order(conn,cid,key,parts[2])
            except ValueError as exc:await self.send(str(exc));return
            casualty=', '.join(f'{k}: {v}' for k,v in result['casualties'].items()) or 'brak'
            await self.send(f'Rozkaz {parts[2]}. Zniszczono {result["damage"]} obrony. Straty: {casualty}. Etap {result["phase"]}/3: {new.PHASES[result["phase"]-1]}. Obrona pozostała {result["remaining"]}.')
            if result['outcome']=='victory':await self.send('ZWYCIĘSTWO! Gildia zdobyła twierdzę. Przegrupowanie: 4 godziny. Przejścia dla innych graczy pozostają otwarte.')
            elif result['outcome']=='retreat':await self.send('ARMIA WYCOFAŁA SIĘ. Przegrupowanie: 4 godziny.')
            return
        if action=='odwrot':
            if len(parts)<3 or parts[2] not in ('potwierdz','tak','confirm'):
                await self.send(f'Potwierdź: oblezenie {key} odwrot potwierdz.');return
            try:new.retreat(conn,cid,key)
            except ValueError as exc:await self.send(str(exc));return
            await self.send('Wycofano oddziały. Przegrupowanie trwa 4 godziny.');return

    async def auction_command_v1320(self,args=''):
        conn=self._econ_v1321()
        raw=str(args or '').strip();parts=raw.split(); action=_norm(parts[0]) if parts else 'lista'
        if action in ('lista','list','info'):
            rows=conn.execute('SELECT l.id,l.item_id,l.quantity,l.price,l.seller,a.expires_at,a.highest_bid,a.bidder_id '
                              "FROM market_listings_v1320 l LEFT JOIN market_auctions_v1321 a ON a.listing_id=l.id WHERE l.state='active' ORDER BY l.id DESC LIMIT 30").fetchall()
            await self.send('GIEŁDA: ceny za cały pakiet, w srebrnych monetach. Licytacja i kup teraz to różne rodzaje ofert.')
            now=int(time.time())
            for r in rows:
                name=ITEMS.get(r['item_id'],{}).get('name',r['item_id'])
                if r['expires_at'] is None:
                    await self.send(f'{r["id"]}. {name} x{r["quantity"]}. Kup teraz: {r["price"]}.')
                else:
                    left=max(0,int(r['expires_at'])-now)
                    await self.send(f'{r["id"]}. LICYTACJA: {name} x{r["quantity"]}. Cena startowa {r["price"]}, najwyższa oferta {r["highest_bid"]}, do końca {left} sekund. '+('Rozlicz zakończoną licytację.' if not left else ''))
            if not rows:await self.send('Brak aktywnych ofert.')
            await self.send('aukcja licytacja <przedmiot> <ile> <cena startowa> <1/6/12/24/48 godzin>; aukcja licytuj <nr> <kwota>; aukcja rozlicz [nr]; aukcja odbierz.')
            return
        if action=='licytacja' and len(parts)>=5:
            try:
                qty=int(parts[-3]);starting=int(parts[-2]);hours=int(parts[-1])
            except ValueError:
                await self.send('Podaj ilość, cenę startową i czas: 1, 6, 12, 24 lub 48 godzin.');return
            if not(1<=qty<=1_000_000 and 1<=starting<=10**15 and hours in (1,6,12,24,48)):
                await self.send('Nieprawidłowa ilość, cena lub czas.');return
            found=self._auction_item_v1320(' '.join(parts[1:-3]))
            found=[(i,b,q) for i,b,q in found if q>=qty and (ITEMS[i].get('type')!='armor' or self.free_equipment_quantity(i)>=qty)]
            if len(found)!=1:
                await self.send('Brak niezabezpieczonego przedmiotu w podanej ilości albo niejednoznaczna nazwa.');return
            item,box,_=found[0]
            try:n=new.offer_auction(conn,self.account_id,item,qty,starting,hours,box)
            except ValueError as exc:await self.send(str(exc));return
            await self.send(f'Wystawiono licytację {n}: {ITEMS[item].get("name",item)} x{qty}, start {starting} monet, czas {hours} godzin. Przedmioty są w depozycie.');return
        if action=='licytuj' and len(parts)==3:
            try:n=int(parts[1]);amount=int(parts[2])
            except ValueError:await self.send('Użycie: aukcja licytuj <nr> <kwota w srebrze>.');return
            try:balance,_minimum=new.bid(conn,self.account_id,n,amount)
            except ValueError as exc:await self.send(str(exc));return
            self.character.silver=balance;self.character.gold=0;self.character.mithril=0
            await self.send(f'Złożono ofertę {amount} srebrnych monet. Kwota jest w depozycie. Jeżeli ktoś Cię przebije, odbierz zwrot komendą aukcja odbierz.');return
        if action=='rozlicz':
            if len(parts)==2:
                try:ids=[int(parts[1])]
                except ValueError:await self.send('Użycie: aukcja rozlicz <nr>.');return
            elif len(parts)==1:
                now=int(time.time());ids=[r['listing_id'] for r in conn.execute('SELECT a.listing_id FROM market_auctions_v1321 a JOIN market_listings_v1320 l ON l.id=a.listing_id '
                    "WHERE l.state='active' AND a.expires_at<=? ORDER BY a.expires_at LIMIT 50",(now,)).fetchall()]
            else:await self.send('Użycie: aukcja rozlicz [nr].');return
            if not ids:await self.send('Brak zakończonych licytacji do rozliczenia.');return
            success=0
            for n in ids:
                try:state,_=new.settle(conn,n)
                except ValueError as exc:
                    if len(ids)==1:await self.send(str(exc))
                    continue
                success+=1
                await self.send(f'Licytacja {n}: '+('sprzedana; kupujący otrzymał przedmioty, sprzedawca może odebrać zapłatę.' if state=='sold' else 'brak ofert; przedmioty wróciły do właściciela.'))
            if len(ids)>1:await self.send(f'Rozliczono {success} licytacji.');return
            return
        if action=='anuluj' and len(parts)==2 and parts[1].isdigit():
            n=int(parts[1]);row=conn.execute('SELECT 1 FROM market_auctions_v1321 WHERE listing_id=?',(n,)).fetchone()
            if row:
                try:new.cancel_auction(conn,self.account_id,n)
                except ValueError as exc:await self.send(str(exc));return
                await self.send(f'Anulowano licytację {n} bez ofert. Przedmiot wrócił do magazynu.');return
        if action=='moje':
            rows=conn.execute('SELECT l.id,l.item_id,l.quantity,l.price,a.highest_bid FROM market_listings_v1320 l LEFT JOIN market_auctions_v1321 a '
                              "ON a.listing_id=l.id WHERE l.seller=? AND l.state='active' ORDER BY l.id DESC",(self.account_id,)).fetchall()
            for r in rows:
                label='licytacja' if r['highest_bid'] is not None else 'kup teraz'
                await self.send(f'{r["id"]}. {ITEMS.get(r["item_id"],{}).get("name",r["item_id"])} x{r["quantity"]}. {label} {r["price"]}. '+(f'Najwyższa oferta {r["highest_bid"]}.' if r['highest_bid'] is not None else ''))
            if not rows:await self.send('Nie masz aktywnych ofert.')
            return
        return await super().auction_command_v1320(args)

    async def shipyard_command_v1320(self,args=''):
        conn=self._econ_v1321(); parts=_norm(args).split(); port=self.ocean_port_name_v1000(self.character.room_id)
        if self.character.room_id=='v1310_ocean_departure':port='Port Trzech Rejsów'
        account=self.account_id
        if not parts or parts[0] in ('flota','lista','status','info'):
            new.migrate_fleet(conn,account)
            new.snapshot_active(conn,account);conn.commit()
            ships=new.fleet_rows(conn,account)
            await self.send(f'FLOTA: {len(ships)} statków. Port: {port or "brak"}. Ulepszenia każdego statku zapisywane są osobno.')
            for s in ships:
                await self.send(f'{s["id"]}. {s["name"]}, {new.CLASSES[int(s["ship_class"])]}, '+('AKTYWNY. ' if s['active'] else '')+
                                f'Kadłub {s["hull"]}, żagle {s["sails"]}, ładownia {s["cargo"]}, nawigacja {s["navigation"]}.')
            for key,(rank,cost,materials) in old.SHIPS.items():
                await self.send(f'Budowa {key}: {currency_price_text(cost)}, materiały '+', '.join(f'{ITEMS.get(k,{}).get("name",k)} x{v}' for k,v in materials.items())+'.')
            await self.send('stocznia buduj <bryg/fregata/galeon> potwierdz; stocznia wybierz <nr>; stocznia nazwij <nr> <nazwa>. Budowa i zmiana aktywnego statku tylko w porcie.')
            return
        if len(parts)==2 and parts[0]=='wybierz':
            if not port:await self.send('Wybór statku tylko w porcie.');return
            try:n=int(parts[1]);name=new.choose_ship(conn,account,n)
            except ValueError as exc:await self.send(str(exc));return
            await self.send(f'Wybrano statek numer {n}: {name}. Jego własne moduły Ocean 2.0 są aktywne.');return
        if parts[0]=='nazwij' and len(parts)>=3:
            if not port:await self.send('Nazwę statku zmienia się w porcie.');return
            try:new.rename_ship(conn,account,int(parts[1]),' '.join(raw_parts for raw_parts in str(args).split()[2:]))
            except ValueError as exc:await self.send(str(exc));return
            await self.send('Zmieniono nazwę statku.');return
        if len(parts) in (2,3) and parts[0]=='buduj' and parts[1] in old.SHIPS:
            if not port:await self.send('Stocznia buduje statki wyłącznie w porcie.');return
            key=parts[1];tier,price,materials=old.SHIPS[key]
            if self.character_wallet_silver_value()<price:await self.send(f'Brak monet. Potrzeba {currency_price_text(price)}.');return
            sources={item:old.select_source(conn,account,item,qty) for item,qty in materials.items()}
            if any(v is None for v in sources.values()):await self.send('Brakuje surowców do budowy statku.');return
            if len(parts)<3 or parts[2] not in ('potwierdz','tak','confirm'):
                await self.send(f'Budowa dodatkowego statku {key}: {currency_price_text(price)}. Potwierdź stocznia buduj {key} potwierdz.');return
            try:n,balance=new.build_ship(conn,account,key,sources)
            except ValueError as exc:await self.send(str(exc));return
            self.character.silver=balance;self.character.gold=0;self.character.mithril=0
            await self.send(f'Zbudowano statek {n}: {key}. Jest teraz aktywny. Poprzednie statki i ich ulepszenia pozostały we flocie.');return
        await self.send('Użycie: stocznia; stocznia flota; stocznia buduj bryg/fregata/galeon potwierdz; stocznia wybierz <nr>; stocznia nazwij <nr> <nazwa>.')
