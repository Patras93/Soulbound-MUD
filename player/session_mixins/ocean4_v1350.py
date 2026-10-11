# -*- coding: utf-8 -*-
"""Accessible Ocean 4.0 commands; standalone against NPC, no PvP."""
from __future__ import annotations
from systems import ocean4_v1350 as navy
from systems import ocean5_modules_v2201 as ship_modules
from world.ocean_expansion import DEEP_OCEAN_ROOMS
from data.catalogs import ITEMS

class SessionOcean4V1350Mixin:
    def _naval_v1350(self):
        conn=self._econ_v1321()
        if not getattr(self.server.db,'_naval1350_initialized',False):
            navy.init(conn)
            self.server.db._naval1350_initialized=True
        return conn

    def _naval_port_v1350(self):
        return bool(self.ocean_port_name_v1000(self.character.room_id) or self.character.room_id in ('v1310_ocean_departure', 'v2000_ocean_hub'))

    async def ocean4_command_v1350(self,args=''):
        parts=str(args or '').lower().split()
        cmd=parts[0] if parts else 'pomoc'
        conn=self._naval_v1350();account=self.account_id
        if cmd in ('pomoc','help','info'):
            await self.send('OCEAN 4.0 — FLOTA PvE. Komendy: ocean4 flota; ocean4 eskorta dodaj <nr> / usun <nr>; ocean4 napraw <nr> potwierdz; ocean4 cele; ocean4 atak <cel> (także Ocean 5.0); ocean4 status; ocean4 rozkaz salwa/manewr/oslona/abordaz; ocean4 odwrot potwierdz; ocean4 rekordy; ocean4 modul lista / zaloz <statek> <1..4> / zdejmij <statek> <slot>.')
            await self.send('Dwa okręty eskortowe + aktywny okręt flagowy. Abordaż możliwy przeciw statkom poniżej 45% HP. Każda bitwa zachowuje stan po wylogowaniu. Nie potrzeba drugiej gildii.')
            return
        if cmd=='flota':
            for s in navy.fleet_status(conn,account):
                await self.send(f'{s["id"]}. {s["name"]}. Kadłub bojowy {s["hp"]}/{s["max_hp"]}. '+('FLAGOWY. ' if s['active'] else '')+('ESKORTA.' if s['escort'] else ''))
            await self.send('W stoczni możesz przełączać flagowy statek i budować kolejne. Ocean4: maksymalnie dwie eskorty.')
            return
        if cmd=='cele':
            for key,enemy in navy.ENEMIES.items():
                await self.send(f'{key}: {enemy[0]}. Typ: {enemy[4]}. Nagroda za zwycięstwo: {enemy[3]} srebra i surowce.')
            return
        if cmd=='modul':
            if len(parts)==1 or parts[1]=='lista':
                for no,(slot,item,name) in ship_modules.MODULES.items():
                    await self.send(f'{no}. {name} — slot {slot}, przedmiot {item}. Wytwórz: mistrzprof receptury <profesja>.')
                for sh in navy.fleet_status(conn,account):
                    mods=ship_modules.modules(conn,account,sh['id'])
                    await self.send(f'Statek {sh["id"]}: '+(', '.join(f'{slot}: {iid}' for slot,iid in mods.items()) or 'brak modułów'))
                return
            if not self._naval_port_v1350():
                await self.send('Moduły można montować tylko w porcie.');return
            if len(parts)!=4 or parts[1] not in ('zaloz','zdejmij'):
                await self.send('Użycie: ocean4 modul zaloz <numer statku> <1..4> lub ocean4 modul zdejmij <numer statku> <slot>.');return
            try:
                ship_id=int(parts[2])
                if parts[1]=='zaloz':
                    name=ship_modules.equip(conn,account,ship_id,parts[3])
                    await self.send('Zamontowano: '+name)
                else:
                    item=ship_modules.remove(conn,account,ship_id,parts[3])
                    await self.send('Zwrócono do ekwipunku: '+ITEMS.get(item,{}).get('name',item))
            except ValueError as exc:await self.send(str(exc))
            return
        if cmd=='rekordy':
            rows=navy.records(conn,account)
            for key,n in rows: await self.send(f'{navy.ENEMIES[key][0]}: zwycięstwa {n}.')
            if not rows: await self.send('Brak zwycięstw na morzu.')
            return
        if cmd=='status':
            s=navy.battle_state(conn,account)
            if not s:await self.send('Nie stoczono jeszcze bitwy Ocean 4.0.');return
            await self.send(f'{s["name"]}. '+('TRWA' if s['active'] else 'ZAKOŃCZONA: '+s['outcome'])+f'. Tura {s["turn"]}. Wróg {s["enemy_hp"]}/{s["enemy_max_hp"]} HP.')
            for n,h,m in s['ships']:await self.send(f'{n}: kadłub {h}/{m}.')
            if s['active']:await self.send('ocean4 rozkaz salwa/manewr/oslona/abordaz')
            return
        if cmd=='eskorta' and len(parts)==3 and parts[1] in ('dodaj','usun'):
            if not self._naval_port_v1350():await self.send('Dobór eskorty jest dostępny tylko w porcie.');return
            try:navy.escort(conn,account,int(parts[2]),enable=parts[1]=='dodaj')
            except ValueError as e:await self.send(str(e));return
            await self.send('Zmieniono skład eskorty.');return
        if cmd=='napraw' and len(parts)>=2:
            if not self._naval_port_v1350():await self.send('Naprawa tylko w porcie.');return
            try:n=int(parts[1])
            except ValueError:await self.send('Podaj numer statku.');return
            rows=navy.fleet_status(conn,account);s=next((s for s in rows if s['id']==n),None)
            if not s:await self.send('Nie masz takiego statku.');return
            cost=max(500,(s['max_hp']-s['hp']+7)//8) if s['hp']<s['max_hp'] else 0
            if len(parts)<3 or parts[2]!='potwierdz':
                await self.send(f'Naprawa {s["name"]}: {cost} srebra. Potwierdź ocean4 napraw {n} potwierdz.');return
            try:price,balance=navy.repair(conn,account,n)
            except ValueError as e:await self.send(str(e));return
            self.character.silver=balance;self.character.gold=0;self.character.mithril=0
            await self.send(f'Naprawiono statek. Koszt {price} srebra.');return
        if cmd=='atak' and len(parts)==2:
            if not (self._naval_port_v1350() or self.character.room_id in DEEP_OCEAN_ROOMS or str(self.character.room_id).startswith(('v2200_', 'v2300_'))):
                await self.send('Wypłyń do portu lub na szlak oceanu, aby rozpocząć bitwę flot.');return
            try:name,hp,n=navy.begin(conn,account,parts[1])
            except ValueError as e:await self.send(str(e));return
            await self.send(f'BITWA MORSKA! Przeciwnik: {name}, HP {hp}. Twoje okręty: {n}. Wpisz ocean4 rozkaz salwa, manewr, oslona lub abordaz.');return
        if cmd=='odwrot':
            if len(parts)!=2 or parts[1]!='potwierdz':
                await self.send('Aby wycofać flotę bez łupów, wpisz ocean4 odwrot potwierdz.');return
            try:navy.retreat(conn,account)
            except ValueError as e:await self.send(str(e));return
            await self.send('Flota wycofała się bez nagrody. Okręty zachowują uszkodzenia i odpoczywają 2 godziny.');return
        if cmd=='rozkaz' and len(parts)==2:
            try:r=navy.action(conn,account,parts[1])
            except ValueError as e:await self.send(str(e));return
            await self.send(f'Tura {r.get("turn",0)}: {parts[1]}, zadano {r["damage"]} obrażeń. Wróg: {r.get("enemy_hp",0)}/{r.get("enemy_max_hp",0)} HP.')
            if r.get('hazard') and r['enemy_damage']:await self.send('UWAGA: morski potwór uruchomił specjalny atak żywiołowy!')
            if r.get('hazard_notice'):await self.send(r['hazard_notice'])
            if r['enemy_damage']:await self.send(f'Kontratak przeciwnika: {r["enemy_damage"]} obrażeń podzielonych między okręty.')
            for name,h,m in r['losses']:await self.send(f'{name}: kadłub {h}/{m}.')
            if r['outcome']=='zwyciestwo':
                self.character.silver=r['balance'];self.character.gold=0;self.character.mithril=0
                await self.send(f'ZWYCIĘSTWO! {r["reward"]} srebra i materiał {ITEMS.get(r["material"],{}).get("name", r["material"])} w ekwipunku. Kolejna bitwa po 2 godzinach.')
            elif r['outcome']=='porazka':await self.send('PORAŻKA! Flota wymaga naprawy. Żaden statek nie znika z kolekcji.')
            return
        await self.send('Nieznana komenda. Wpisz ocean4 pomoc.')
