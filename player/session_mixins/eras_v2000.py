# -*- coding: utf-8 -*-
"""Accessible v2.00.0 navigation, persistent PvE faction and arena commands."""
from __future__ import annotations
from systems import eras_pve_v2000 as era
from systems.parallel_worlds_v2000 import REALMS, ISLANDS, ARENAS
from data.catalogs import ROOMS

class SessionErasV2000Mixin:
    def _eras_v2000(self):
        db=self.server.db
        conn=self._econ_v1321()
        if not getattr(db,'_eras_v2000_initialized',False):
            era.init(conn)
            db._eras_v2000_initialized=True
        return conn

    async def dimensions_v2000(self,args=''):
        if not self.character:return
        query=str(args or '').strip().casefold()
        await self.send('WYMIARY 2.00.0: wejście z Wymiarów Chaosu w GÓRĘ; Węzeł Światów. Kierunki: północ Sny, wschód Smoki, południe Duchy, zachód Pustka.')
        for slug,title,_element,level,*_ in REALMS:
            if not query or query in ('lista','pomoc') or query==slug:
                await self.send(f'{slug}: {title}, zalecany poziom {level}, 18 pomieszczeń, boss, 3 polowania. Powrót do Węzła Światów.')
        if query in ('droga','trasa'):
            path=self.shortest_path(self.character.room_id,'v2000_nexus')
            if path is None:await self.send('Brak trasy z bieżącego miejsca.')
            elif path:await self.send(f'Trasa do Węzła Światów: {len(path)} przejść. Pierwszy krok: {self.route_direction_name(path[0][0])}.')
            else:await self.send('Stoisz już w Węźle Światów.')

    async def ocean5_v2000(self,args=''):
        if not self.character:return
        await self.send('OCEAN 5.0: Port Nieznanych Mórz. Z Węzła Światów w GÓRĘ; północ Perły, wschód Otchłań, zachód Burze. Bitwy flot nadal obsługuje ocean4.')
        for slug,title,_element,level,*_ in ISLANDS:
            await self.send(f'{slug}: {title}; zalecany poziom {level}; 8 pomieszczeń, 5 typów mobów i boss Fame.')
        await self.send('Nowe cele flot: ocean4 cele, ocean4 atak perlowaflota / czarnaarmada / sztormowcy. Dotychczasowe statki i ulepszenia pozostają.')

    async def factions_v2000(self,args=''):
        if not self.character:return
        parts=str(args or '').strip().casefold().split()
        action=parts[0] if parts else 'status'
        conn=self._eras_v2000();account=int(self.account_id)
        if action in ('status','lista','pomoc'):
            await self.send('FRAKCJE 5.0: frakcje kontrakt <kod>; frakcje odbierz <kod>; frakcje status; frakcje odznaka <kod>. Kontrakty raz na godzinę, nagrody za rzeczywiste zabicia. Reputacja bez resetu.')
            earned=era.fame_status(conn,account)
            for key,(name,target,level) in era.FACTIONS.items():
                row=conn.execute('SELECT active,progress,ready_at,completions FROM v2000_faction_hunts WHERE account_id=? AND faction=?',(account,key)).fetchone()
                status=('gotowy do odbioru' if row and row['active'] and row['progress']
                        else 'aktywny' if row and row['active'] else 'dostępny')
                await self.send(f'{key}: {name}. Reputacja {earned.get(key,0)}. Kontrakt {status}; cel {target}.')
            return
        if len(parts)!=2 or parts[1] not in era.FACTIONS:
            await self.send('Podaj kod frakcji z: frakcje lista. Komendy: frakcje kontrakt <kod>, frakcje odbierz <kod>.');return
        key=parts[1]
        if action in ('kontrakt','przyjmij'):
            try:target=era.faction_start(conn,account,key)
            except ValueError as exc:await self.send(str(exc));return
            await self.send(f'Przyjęto kontrakt frakcji {era.FACTIONS[key][0]}. Pokonaj {target} w odpowiednim świecie. Zaliczenie drużynowe; frakcje odbierz {key}.')
            return
        if action in ('odznaka','ranga'):
            try:rank,item,renown=era.claim_rank(conn,account,key)
            except ValueError as exc:await self.send(str(exc));return
            await self.send(f'Otrzymujesz {item}. Ranga {rank}; reputacja {renown}. Przedmiot w ekwipunku.')
            return
        if action in ('odbierz','nagroda'):
            try:coins,renown,balance=era.claim_faction(conn,account,key)
            except ValueError as exc:await self.send(str(exc));return
            self.character.silver=balance;self.character.gold=0;self.character.mithril=0
            await self.send(f'Kontrakt ukończony. {coins} srebra, +25 reputacji. {era.FACTIONS[key][0]}: {renown}. Kolejny za godzinę.')
            return
        await self.send('Użycie: frakcje status / kontrakt <kod> / odbierz <kod>.')

    async def arena_v2000(self,args=''):
        if not self.character:return
        parts=str(args or '').strip().casefold().split()
        action=parts[0] if parts else 'lista'
        conn=self._eras_v2000();account=int(self.account_id)
        if action in ('lista','pomoc','status'):
            await self.send('ARENA LEGEND 3.0: z Portu Nieznanych Mórz w GÓRĘ. Arena podejmij <kod>; arena status; arena odbierz <kod>. Walka solo lub z drużyną. Próby są trwałe w SQLite.')
            for key,(title,level,boss_id) in era.ARENA.items():
                row=conn.execute('SELECT state,progress,victories,ready_at FROM v2000_arena_trials WHERE account_id=? AND challenge=?',(account,key)).fetchone()
                state=('w toku' if row and row['state']==1 else 'gotowa do odbioru' if row and row['state']==2 else 'wolna')
                await self.send(f'{key}: {title}; zalecany poziom {level}, {state}, zwycięstwa {int(row["victories"]) if row else 0}; fale {((int(row['progress']) & 7).bit_count() if row else 0)}/3. Przeciwnik: {boss_id}.')
            return
        if len(parts)!=2 or parts[1] not in era.ARENA:
            await self.send('Wpisz arena lista, arena podejmij <kod> lub arena odbierz <kod>.');return
        key=parts[1]
        if action in ('podejmij','start'):
            if self.character.room_id!='v2000_arena_hall':
                await self.send('Wyzwanie można podjąć tylko w Hali Areny Legend. Z Portu Nieznanych Mórz idź w GÓRĘ.');return
            try:boss_id=era.arena_start(conn,account,key)
            except ValueError as exc:await self.send(str(exc));return
            await self.send(f'Próba {key} rozpoczęta. Pokonaj trzy rodzaje strażników fal i {boss_id} w prawdziwej walce PvE. Kolejność nie ma znaczenia, także przy AoE. Zaliczają się członkowie drużyny z aktywną próbą.')
            return
        if action in ('odbierz','nagroda'):
            try:coins,wins,balance=era.claim_arena(conn,account,key)
            except ValueError as exc:await self.send(str(exc));return
            self.character.silver=balance;self.character.gold=0;self.character.mithril=0
            await self.send(f'Nagroda Areny {key}: {coins} srebra. Łączne zwycięstwa {wins}. Odnowienie 90 minut.')
            return
        await self.send('Nieznana akcja Areny. Wpisz arena lista.')
