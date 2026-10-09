# -*- coding: utf-8 -*-
"""v1.34: tekstowe komendy dla żyjących terytoriów, czytelne w NVDA."""
from __future__ import annotations
from systems import living_empires_v1340 as world
from systems import imperial_economy_v1320 as empire
from player.session_mixins.imperial_economy_v1320 import _norm
from core.bootstrap_economy_professions import currency_price_text

class SessionLivingEmpiresV1340Mixin:
    def _econ_v1340(self):
        conn=self._econ_v1321()
        if not getattr(self.server.db,'_living_empire1340_initialized',False):
            world.init(conn)
            self.server.db._living_empire1340_initialized=True
        return conn

    async def imperial_command_v1320(self,args=''):
        parts=_norm(args).split()
        if not parts or parts[0] in ('status','lista','info'):
            await super().imperial_command_v1320('')
            conn=self._econ_v1340()
            await self.send('ŻYJĄCE IMPERIA: kontrataki co 12 godzin, dochody co 6 godzin, maksymalnie 4 rozliczone cykle offline. Twierdze nie przepadają za samą nieobecność.')
            for fort in empire.FORTS:
                stat=world.detail(conn,fort)
                if stat:
                    await self.send(f'{fort}: stabilność {stat["stability"]}/100, siła garnizonu {stat["strength"]}, nierozliczony dochód {currency_price_text(stat["reserve"])}. Najazdy {stat["raids"]}.')
            await self.send('Komendy: imperium garnizon <fort>; imperium obsadz <fort> <wojownik/lucznik/mag> <ilość> potwierdz; imperium wycofaj <fort> <typ> <ilość> potwierdz; imperium rozbuduj <fort> <farmy/targ/kuznia> potwierdz; imperium pobierz <fort> potwierdz; imperium wojny; imperium raport <fort>; imperium wyprawa <fort> <natarcie/ostrzal/magia> potwierdz.')
            return
        conn=self._econ_v1340()
        action=parts[0]
        if action=='wojny':
            await self.send('FRONTY PvE: walczysz z wojskami NPC, nie potrzebujesz żadnej drugiej gildii. Każdy rejon kontratakuje co 12 godzin po zdobyciu twierdzy.')
            for fort in empire.FORTS:await self.send(f'{fort}: aktualny wróg {world.front(fort)}. Dostęp do miast pozostaje otwarty.')
            return
        if action in ('wyprawa','kontratak') and len(parts)>=2:
            fort=parts[1]
            if fort not in empire.FORTS:
                await self.send('Nieznana twierdza. Wpisz imperium wojny.');return
            tactic=parts[2] if len(parts)>=3 else 'natarcie'
            if tactic not in world.COUNTERATTACK_TACTICS:
                await self.send('Taktyki: natarcie, ostrzal, magia.');return
            if len(parts)<4 or parts[3] not in ('potwierdz','tak','confirm'):
                await self.send(f'Wyprawa na obóz NPC {world.front(fort)}. Potwierdź: imperium wyprawa {fort} {tactic} potwierdz.');return
            leader=self._leader_v1320()
            if not leader:
                await self.send('Wyprawę oddziałów prowadzi lider gildii. Innych gildii NIE potrzeba.');return
            try:result=world.enemy_camp(conn,int(leader['clan_id']),fort,tactic)
            except ValueError as exc:await self.send(str(exc));return
            await self.send(('ZWYCIĘSTWO PvE' if result['won'] else 'ODWRÓT PvE')+f' pod {fort}. Wróg: {result["enemy"]}. Siła {result["power"]}, opór {result["threat"]}.')
            await self.send('Straty jednostek: '+(', '.join(f'{k} {v}' for k,v in result['losses'].items()) or 'brak')+f'. Nagroda dla skarbca: {currency_price_text(result["reward"])}. Następna wyprawa za 3 godziny.')
            return
        if action in ('garnizon','raport') and len(parts)==2 and parts[1] in empire.FORTS:
            fort=parts[1]; stat=world.detail(conn,fort)
            if not stat:await self.send('Ta twierdza nie została jeszcze zdobyta.');return
            await self.send(f'TWIERDZA {empire.FORTS[fort][0]}. Gildia {stat["owner"]}, mury {stat["walls"]}, stabilność {stat["stability"]}/100. Garnizon: '+', '.join(f'{k} {stat["garrison"].get(k,0)}' for k in empire.TROOPS)+'.')
            await self.send(f'Produkcja: farmy {stat["farms"]}, targ {stat["targ"]}, kuźnia {stat["kuznia"]}. Dochód do odbioru: {currency_price_text(stat["reserve"])}. Przeżyte najazdy: {stat["raids"]}.')
            if action=='raport':
                for r in world.history(conn,fort):
                    await self.send(f'{r["attacker"]}: '+('obrona udana' if r['victory'] else 'mury ucierpiały')+f', straty {r["losses"]} oddziałów.')
            return
        if action in ('obsadz','wycofaj') and len(parts) in (4,5):
            fort,troop=parts[1:3]
            if fort not in empire.FORTS or troop not in empire.TROOPS:await self.send('Użycie: imperium obsadz <fort> <typ> <liczba> potwierdz.');return
            try:quantity=int(parts[3])
            except ValueError:await self.send('Podaj liczbę żołnierzy.');return
            if not 1<=quantity<=1000000:await self.send('Liczba jednostek: 1 do miliona na rozkaz.');return
            if len(parts)<5 or parts[4] not in ('potwierdz','tak','confirm'):
                await self.send(f'Przeniesienie {quantity} x {troop}: imperium {action} {fort} {troop} {quantity} potwierdz.');return
            leader=self._leader_v1320()
            if not leader:await self.send('Tylko lider gildii może zarządzać garnizonem.');return
            try:strength=world.move_garrison(conn,int(leader['clan_id']),fort,troop,quantity,return_to_army=(action=='wycofaj'))
            except ValueError as exc:await self.send(str(exc));return
            await self.send(f'Rozkaz wykonany. Siła garnizonu {strength}. Oddziały zachowują swój rzeczywisty stan.');return
        if action in ('rozbuduj','pobierz') and len(parts) in (2,3,4):
            fort=parts[1]
            if fort not in empire.FORTS:await self.send('Nieznana twierdza.');return
            leader=self._leader_v1320()
            if not leader:await self.send('Tylko lider gildii może rozliczać terytoria.');return
            confirm=parts[-1] in ('potwierdz','tak','confirm')
            if action=='pobierz':
                if not confirm:await self.send(f'Potwierdź: imperium pobierz {fort} potwierdz.');return
                try:coins=world.collect(conn,int(leader['clan_id']),fort)
                except ValueError as exc:await self.send(str(exc));return
                await self.send(f'Przeniesiono {currency_price_text(coins)} do skarbca gildii.');return
            if len(parts)<3 or parts[2] not in world.BUILDINGS:await self.send('Budynki: farmy, targ, kuznia.');return
            kind=parts[2]
            if not confirm:await self.send(f'Potwierdź: imperium rozbuduj {fort} {kind} potwierdz.');return
            try:level,price=world.upgrade(conn,int(leader['clan_id']),fort,kind)
            except ValueError as exc:await self.send(str(exc));return
            await self.send(f'Rozbudowano {kind} do poziomu {level}. Koszt: {currency_price_text(price)} ze skarbca.');return
        return await super().imperial_command_v1320(args)
