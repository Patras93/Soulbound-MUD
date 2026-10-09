# -*- coding: utf-8 -*-
"""Accessible commands for v1.32.0 empire, auction and native Ocean shipyards."""
from __future__ import annotations
import time
import unicodedata
from core.bootstrap_economy_professions import currency_price_text
from systems import imperial_economy_v1320 as econ


def _norm(s):
    s=''.join(ch for ch in unicodedata.normalize('NFKD',str(s).casefold()) if not unicodedata.combining(ch))
    return ' '.join(s.split())

class SessionImperialEconomyV1320Mixin:
    def _econ_v1320(self):
        db=self.server.db
        if not getattr(db,'_economy1320_initialized',False):
            econ.init(db.conn)
            db._economy1320_initialized=True
        return db.conn

    def _leader_v1320(self):
        member=self.guild_row_v0926()
        return member if member and str(member['rank'])=='leader' else None

    async def imperial_command_v1320(self, args=''):
        conn=self._econ_v1320(); parts=_norm(args).split(); member=self.guild_row_v0926()
        if not parts or parts[0] in ('status','lista','info'):
            await self.send('IMPERIA: cztery twierdze. Armia i zdobyte posterunki są własnością gildii; przejścia świata pozostają otwarte.')
            for key,(name,_lvl,_base) in econ.FORTS.items():
                row=conn.execute('SELECT clan_id,walls FROM empire_forts_v1320 WHERE fort=?',(key,)).fetchone()
                owner=('niezdobyta' if row is None else ('twoja gildia' if member and int(row['clan_id'])==int(member['clan_id']) else f'gildia {row["clan_id"]}'))
                await self.send(f'{name}, kod {key}: {owner}. Mury {row["walls"] if row else 1}. Obrona {econ.fort_strength(conn,key)}.')
            await self.send('Komendy: armia; armia rekrutuj <wojownik/lucznik/mag> <ile> potwierdz; oblezenie <kod> potwierdz; imperium mury <kod> potwierdz.')
            return
        if parts[0]=='mury' and len(parts)>=2:
            key=parts[1]
            if key not in econ.FORTS: await self.send('Nieznana twierdza. Wpisz imperium.'); return
            leader=self._leader_v1320()
            if not leader: await self.send('Mury może rozbudować wyłącznie lider gildii.'); return
            cid=int(leader['clan_id'])
            row=conn.execute('SELECT walls FROM empire_forts_v1320 WHERE fort=? AND clan_id=?',(key,cid)).fetchone()
            if not row: await self.send('Twoja gildia nie kontroluje tej twierdzy.'); return
            level=int(row['walls']); cost=econ.FORTS[key][2]*level
            if len(parts)<3 or parts[2] not in ('potwierdz','tak','confirm'):
                await self.send(f'Mury {level}->{level+1}. Koszt {currency_price_text(cost)} ze skarbca gildii. Wpisz imperium mury {key} potwierdz.'); return
            try:
                with econ.atomic(conn):
                    cur=conn.execute('UPDATE player_clans SET treasury=treasury-? WHERE id=? AND treasury>=?',(cost,cid,cost))
                    if cur.rowcount!=1: raise ValueError('Brakuje środków w skarbcu gildii.')
                    conn.execute('UPDATE empire_forts_v1320 SET walls=walls+1 WHERE fort=? AND clan_id=?',(key,cid))
            except ValueError as exc: await self.send(str(exc)); return
            await self.send(f'Mury twierdzy {key} osiągnęły poziom {level+1}.'); return
        await self.send('Użycie: imperium; imperium mury <kod> potwierdz.')

    async def army_command_v1320(self,args=''):
        conn=self._econ_v1320(); parts=_norm(args).split(); row=self.guild_row_v0926()
        if not row: await self.send('Do budowy armii potrzebujesz gildii.'); return
        cid=int(row['clan_id'])
        if not parts or parts[0] in ('status','lista'):
            entries={r['troop']:int(r['quantity']) for r in conn.execute('SELECT troop,quantity FROM empire_armies_v1320 WHERE clan_id=?',(cid,)).fetchall()}
            await self.send('ARMIA GILDII: '+'; '.join(f'{k}: {entries.get(k,0)}' for k in econ.TROOPS)+f'. Siła {econ.troop_strength(conn,cid)}.')
            await self.send('Jednostki kosztują ze skarbca: wojownik 14000, lucznik 19000, mag 26000 monet. Armia rekrutuj <typ> <ilość> potwierdz.'); return
        if len(parts) in (3,4) and parts[0]=='rekrutuj' and parts[1] in econ.TROOPS:
            if not self._leader_v1320(): await self.send('Tylko lider gildii rekrutuje oddziały.'); return
            try: qty=int(parts[2]); assert 1<=qty<=1000
            except (ValueError,AssertionError): await self.send('Liczba jednostek: od 1 do 1000 na jedno zlecenie.'); return
            price=econ.TROOPS[parts[1]][0]*qty
            if len(parts)<4 or parts[3] not in ('potwierdz','tak','confirm'):
                await self.send(f'Rekrutacja {qty} x {parts[1]}: {currency_price_text(price)}. Potwierdź: armia rekrutuj {parts[1]} {qty} potwierdz.'); return
            try:
                with econ.atomic(conn):
                    cur=conn.execute('UPDATE player_clans SET treasury=treasury-? WHERE id=? AND treasury>=?',(price,cid,price))
                    if cur.rowcount!=1:raise ValueError('W skarbcu gildii brakuje środków.')
                    conn.execute('INSERT INTO empire_armies_v1320(clan_id,troop,quantity) VALUES(?,?,?) ON CONFLICT(clan_id,troop) DO UPDATE SET quantity=quantity+excluded.quantity',(cid,parts[1],qty))
            except ValueError as exc: await self.send(str(exc)); return
            await self.send(f'Zrekrutowano {qty} {parts[1]}. Siła armii: {econ.troop_strength(conn,cid)}.'); return
        await self.send('Użycie: armia; armia rekrutuj <wojownik/lucznik/mag> <ilość> potwierdz.')

    async def siege_command_v1320(self,args=''):
        conn=self._econ_v1320(); parts=_norm(args).split(); leader=self._leader_v1320()
        if not leader: await self.send('Tylko lider gildii może rozpocząć oblężenie.'); return
        cid=int(leader['clan_id'])
        if not parts or parts[0] not in econ.FORTS:
            await self.send('OBLĘŻENIA. Wybierz: '+'; '.join(f'{k} ({v[0]})' for k,v in econ.FORTS.items())+'. Wpisz oblezenie <kod> potwierdz.'); return
        key=parts[0]
        slugs={'bazalt':'emp_deep','chmury':'emp_sky','valdoria':'emp_lost','orkowie':'emp_orc'}
        if str(self.character.room_id) not in (f'v1310_{slugs[key]}_gate',f'v1310_{slugs[key]}_outpost'):
            await self.send('Oblężenie rozpoczyna się przy bramie lub posterunku odpowiedniej twierdzy. Komenda ery imperia wskazuje dojście.');return
        now=int(time.time()); defense=econ.fort_strength(conn,key); attack=econ.troop_strength(conn,cid)
        current=conn.execute('SELECT clan_id FROM empire_forts_v1320 WHERE fort=?',(key,)).fetchone()
        if current and int(current['clan_id'])==cid: await self.send('Ta twierdza należy już do twojej gildii. Możesz rozbudować mury.'); return
        cool=conn.execute('SELECT ready_at FROM empire_sieges_v1320 WHERE clan_id=? AND fort=?',(cid,key)).fetchone()
        if cool and int(cool['ready_at'])>now:
            await self.send(f'Przegrupowanie armii: pozostało {int(cool["ready_at"])-now} sekund.');return
        if len(parts)<2 or parts[1] not in ('potwierdz','tak','confirm'):
            await self.send(f'Twierdza {key}. Twoja siła {attack}; obrona {defense}. Potwierdź: oblezenie {key} potwierdz.'); return
        rows=conn.execute('SELECT troop,quantity FROM empire_armies_v1320 WHERE clan_id=?',(cid,)).fetchall()
        if not rows or attack==0:await self.send('Najpierw zrekrutuj oddziały.');return
        success=econ.siege_result(attack,defense)
        loss_rate=0.09 if success else 0.24
        casualties={r['troop']:min(int(r['quantity']),max(1,int(int(r['quantity'])*loss_rate))) for r in rows if r['quantity']>0}
        with econ.atomic(conn):
            for troop,lost in casualties.items():
                conn.execute('UPDATE empire_armies_v1320 SET quantity=quantity-? WHERE clan_id=? AND troop=?',(lost,cid,troop))
            conn.execute('INSERT INTO empire_sieges_v1320(clan_id,fort,ready_at,victories) VALUES(?,?,?,?) '
                         'ON CONFLICT(clan_id,fort) DO UPDATE SET ready_at=excluded.ready_at,victories=victories+excluded.victories',
                         (cid,key,now+4*3600,int(success)))
            if success:
                conn.execute('INSERT INTO empire_forts_v1320(fort,clan_id,walls,conquered_at) VALUES(?,?,1,?) '
                             'ON CONFLICT(fort) DO UPDATE SET clan_id=excluded.clan_id,walls=1,conquered_at=excluded.conquered_at',(key,cid,now))
        await self.send(('ZWYCIĘSTWO' if success else 'ODWRÓT')+f' pod {econ.FORTS[key][0]}. Straty: '+', '.join(f'{k} {v}' for k,v in casualties.items())+'. Odpoczynek 4 godziny.')
        if success: await self.send('Zdobyta twierdza należy teraz do gildii. Lokacje pozostają otwarte dla wszystkich graczy.')

    def _auction_item_v1320(self,query):
        from core.mines_threat import ITEMS,is_character_bound_item
        query=_norm(query); matches=[]
        for box in econ.STORAGE:
            if box=='inventory':rows=self.server.db.inventory(self.account_id)
            else:rows=self.server.db.storage_rows(self.account_id,box)
            for r in rows:
                item_id=str(r['item_id']); item=ITEMS.get(item_id)
                if not item or is_character_bound_item(item_id):continue
                if self.item_is_protected_v1280(item_id):continue
                if item.get('type')=='armor' and self.equipped_quantity_of_item(item_id)>=int(r['quantity']):continue
                if _norm(item_id)==query or _norm(item.get('name',item_id))==query:
                    matches.append((item_id,box,int(r['quantity'])))
        return matches

    async def auction_command_v1320(self,args=''):
        from core.mines_threat import ITEMS
        conn=self._econ_v1320(); raw=str(args or '').strip(); parts=raw.split(); action=_norm(parts[0]) if parts else 'lista'
        if action in ('lista','list','info'):
            rows=conn.execute("SELECT l.id,l.item_id,l.quantity,l.price,l.seller,COALESCE(ch.name,a.username) seller_name FROM market_listings_v1320 l JOIN accounts a ON a.id=l.seller LEFT JOIN characters ch ON ch.account_id=l.seller WHERE l.state='active' ORDER BY l.id DESC LIMIT 30").fetchall()
            await self.send('AUKCJE GRACZY: ostatnie aktywne oferty. Cena w srebrnych monetach za cały pakiet.')
            for r in rows: await self.send(f'{r["id"]}. {ITEMS.get(r["item_id"],{}).get("name",r["item_id"])} x{r["quantity"]}. Cena {r["price"]}. Sprzedaje {r["seller_name"]}.')
            if not rows:await self.send('Brak ofert.')
            await self.send('Komendy: aukcja wystaw <nazwa lub ID> <ilość> <cena w srebrze>; aukcja kup <nr>; aukcja anuluj <nr>; aukcja odbierz.');return
        if action in ('moje','own'):
            rows=conn.execute("SELECT id,item_id,quantity,price FROM market_listings_v1320 WHERE seller=? AND state='active' ORDER BY id DESC",(self.account_id,)).fetchall()
            for r in rows:await self.send(f'{r["id"]}. {ITEMS.get(r["item_id"],{}).get("name",r["item_id"])} x{r["quantity"]}, cena {r["price"]}.')
            if not rows:await self.send('Nie masz aktywnych ofert.')
            return
        if action=='wystaw' and len(parts)>=4:
            try:qty=int(parts[-2]); price=int(parts[-1]); assert qty>0 and price>0
            except (ValueError,AssertionError):await self.send('Podaj dodatnią ilość i cenę.');return
            found=self._auction_item_v1320(' '.join(parts[1:-2])); found=[(i,b,q) for i,b,q in found if q>=qty and (ITEMS[i].get('type')!='armor' or self.free_equipment_quantity(i)>=qty)]
            if len(found)!=1:await self.send('Brak przedmiotu w podanej ilości albo niejednoznaczna nazwa. Użyj dokładnego ID i pamiętaj o założonym lub chronionym EQ.');return
            item,box,_=found[0]
            try:n=econ.list_item(conn,self.account_id,item,qty,price,box)
            except ValueError as exc:await self.send(str(exc));return
            await self.send(f'Wystawiono ofertę numer {n}: {ITEMS[item].get("name",item)} x{qty} za {price} srebrnych monet. Przedmiot zabezpieczono w depozycie.');return
        if action in ('kup','anuluj') and len(parts)==2 and parts[1].isdigit():
            n=int(parts[1]);
            try:
                if action=='kup':
                    row,balance=econ.purchase(conn,self.account_id,n,self.character_wallet_silver_value())
                    self.character.silver=balance;self.character.gold=0;self.character.mithril=0
                    await self.send(f'Kupiono {ITEMS.get(row["item_id"],{}).get("name",row["item_id"])} x{row["quantity"]}. Sprzedawca odbierze zapłatę komendą aukcja odbierz.')
                else:
                    row=econ.cancel(conn,self.account_id,n)
                    await self.send(f'Anulowano ofertę {n}. Przedmiot wrócił do poprzedniego magazynu.')
            except ValueError as exc:await self.send(str(exc))
            return
        if action in ('odbierz','wyplac'):
            try:amt,balance=econ.take_payout(conn,self.account_id,self.character_wallet_silver_value())
            except ValueError as exc:await self.send(str(exc));return
            if amt:
                self.character.silver=balance;self.character.gold=0;self.character.mithril=0
            await self.send(f'Odebrano {amt} srebrnych monet z zakończonych aukcji.');return
        await self.send('Użycie: aukcja lista; aukcja moje; aukcja wystaw <nazwa> <ile> <cena w srebrze>; aukcja kup <nr>; aukcja anuluj <nr>; aukcja odbierz.')

    async def shipyard_command_v1320(self,args=''):
        from core.mines_threat import ITEMS
        conn=self._econ_v1320(); parts=_norm(args).split(); port=self.ocean_port_name_v1000(self.character.room_id)
        if self.character.room_id=='v1310_ocean_departure':port='Port Trzech Rejsów'
        old=conn.execute('SELECT ship_class FROM shipyard_fleet_v1320 WHERE account_id=?',(self.account_id,)).fetchone()
        tier=int(old['ship_class']) if old else 0
        if not parts or parts[0] in ('lista','status','info'):
            await self.send(f'STOCZNIA 3.0. Twój typ statku: {("zwykły", "bryg", "fregata", "galeon")[tier]}. Port: {port or "brak"}.')
            for key,(rank,cost,materials) in econ.SHIPS.items():
                await self.send(f'{key}: koszt {currency_price_text(cost)}, materiały '+', '.join(f'{ITEMS.get(k,{}).get("name",k)} x{v}' for k,v in materials.items())+'.')
            await self.send('Stocznia buduj bryg/fregata/galeon potwierdz. Wymaga portu. Ulepsza istniejący statek Ocean 2.0.');return
        if len(parts) in (2,3) and parts[0]=='buduj' and parts[1] in econ.SHIPS:
            key=parts[1];rank,price,materials=econ.SHIPS[key]
            if not port:await self.send('Budowa statku jest możliwa wyłącznie w porcie.');return
            if rank!=tier+1:await self.send('Buduj kolejno bryg, fregata, galeon.');return
            if self.character_wallet_silver_value()<price:await self.send(f'Brak monet. Potrzeba {currency_price_text(price)}.');return
            sources={k:econ.select_source(conn,self.account_id,k,q) for k,q in materials.items()}
            if any(v is None for v in sources.values()):await self.send('Brak części materiałów. Wpisz stocznia po listę.');return
            if len(parts)<3 or parts[2] not in ('potwierdz','tak','confirm'):
                await self.send(f'Budowa {key}: {currency_price_text(price)}. Wpisz stocznia buduj {key} potwierdz.');return
            try:
                with econ.atomic(conn):
                    for item,qty in materials.items():econ.take(conn,self.account_id,item,qty,sources[item])
                    remaining=self.character_wallet_silver_value()-price
                    # Only this account is changed. Runtime character is synchronized after commit.
                    conn.execute('UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?',(remaining,self.account_id))
                    conn.execute('INSERT INTO ocean_ship_v1000(account_id,owned,hull,sails,cargo,navigation) VALUES(?,1,1,1,1,1) ON CONFLICT(account_id) DO UPDATE SET owned=1',(self.account_id,))
                    conn.execute('INSERT INTO shipyard_fleet_v1320(account_id,ship_class,last_build) VALUES(?,?,?) ON CONFLICT(account_id) DO UPDATE SET ship_class=excluded.ship_class,last_build=excluded.last_build',(self.account_id,rank,int(time.time())))
            except ValueError as exc:await self.send(str(exc));return
            self.character.silver=remaining;self.character.gold=0;self.character.mithril=0
            await self.send(f'Zbudowano {key}. Statek jest twój, moduły Ocean 2.0 pozostają zachowane; klasa jednostki wzmacnia nawigację, kadłub i ładownię.');return
        await self.send('Użycie: stocznia; stocznia buduj bryg/fregata/galeon potwierdz.')
