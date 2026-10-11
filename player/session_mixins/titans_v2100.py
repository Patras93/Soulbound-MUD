# -*- coding: utf-8 -*-
"""NVDA-first Titan/secret discovery, clear status and timed guard command."""
from __future__ import annotations
from systems.titans_v2100 import (
    TITANS, TITAN_BY_SLUG, FAMILIES, chamber_identity, dungeon_identity,
    challenge_kind, titan_for_floor, titan_ability_v2100,
)


class SessionTitansV2100Mixin:
    def dungeon_exit_destination(self, room_id=None):
        rid=str(room_id or (self.character.room_id if self.character else ''))
        identity=chamber_identity(rid)
        if identity:
            from core.classes_skills import ROOMS
            origin=str(ROOMS.get(rid,{}).get('exits',{}).get('south') or '')
            if origin in ROOMS:
                return origin, 'Komnata Tytana lub Sekret Głębin'
        return super().dungeon_exit_destination(room_id)

    async def titan_command_v2100(self, raw=''):
        option = str(raw or '').strip().casefold()
        if not self.character:
            return
        current = str(self.character.room_id)
        chamber = chamber_identity(current)
        if option in ('obrona','bron','guard','oslona','osłona'):
            if not chamber or chamber[0]!='titan':
                await self.send('Osłona Tytana działa tylko podczas walki w jego legowisku.')
                return
            mob = self.server.world.mobs.get(str(self.combat_mob_key or ''))
            if mob is None or not mob.alive or mob.room_id != current:
                await self.send('Najpierw rozpocznij walkę z Tytanem.')
                return
            template = __import__('systems.content_registry',fromlist=['MOB_TEMPLATES']).MOB_TEMPLATES.get(mob.template_id,{})
            if not template.get('v2100_titan'):
                await self.send('Ten przeciwnik nie jest Tytanem.')
                return
            self.v2100_guard_mob = str(mob.key)
            await self.send('OSŁONA TYTANA: gotowa. Zmniejszy następny zapowiedziany potężny atak tego Tytana. Nie zużywa many ani nie blokuje automatycznej walki.')
            return
        if option in ('','lista','list'):
            known = {str(row['titan_slug']):int(row['defeats']) for row in self.server.db.titan_records_v2100(self.account_id)}
            await self.send('SUPERBOSSOWIE 9.0 — osiem Tytanów; legowiska co 50 pięter prawdziwych lochów, bez nowych blokad poziomów.')
            for idx, row in enumerate(TITANS,1):
                await self.send(f'{idx}. {row[1]}. Pierwsza głębokość {idx*50}. Zwycięstw: {known.get(row[0],0)}.')
            await self.send('Komendy: tytani info, tytani status, tytani obrona, lochy7. Legowiska są opcjonalnymi odnogami na wskazanych piętrach.')
            return
        if option in ('info','pomoc'):
            await self.send('TYTANI: stój na kanonicznej sali piętra 50, 100, 150 i kolejnych wielokrotnościach 50. Odszukaj wejście w kierunkach; z legowiska POWROT. Co cztery akcje zapowiedź i potężny cios; tytani obrona redukuje ten cios. Każdy członek obecnej drużyny otrzymuje osobiste zaliczenie. Pierwszy kill danego Tytana daje autorski artefakt, bonus Esencji odnawia się po 24 godzinach. Normalne nagrody EXP zostają bez zmian.')
            if chamber and chamber[0]=='titan':
                info = titan_for_floor(chamber[2])
                await self.send(f'Twój przeciwnik: {info[1]}. Umiejętność: {titan_ability_v2100(info[0])}. Powrót: poludnie albo wyjscie.')
            return
        if option in ('status','stan'):
            if chamber and chamber[0]=='titan':
                family,floor = chamber[1],chamber[2]
                info = titan_for_floor(floor)
                monsters = [m for m in self.server.world.room_mobs(current) if m.alive and __import__('systems.content_registry',fromlist=['MOB_TEMPLATES']).MOB_TEMPLATES.get(m.template_id,{}).get('v2100_titan')]
                if monsters:
                    mob = monsters[0]
                    await self.send(f'{info[1]}. HP {mob.hp}. Faza {int(getattr(mob,"v2100_phase",1) or 1)}. Umiejętność: {titan_ability_v2100(info[0])}.')
                else:
                    await self.send(f'{info[1]}: obecnie brak żywego Tytana w komnacie.')
                await self.send(f'Loch: {FAMILIES[family]}, piętro {floor}. Powrót: poludnie albo wyjscie.')
                return
            source = dungeon_identity(current)
            if source:
                family,floor=source
                kind=challenge_kind(floor)
                await self.send(f'{FAMILIES[family]} piętro {floor}: '+('możliwe legowisko Tytana.' if kind=='titan' else 'możliwa sekretna komnata.' if kind=='secret' else 'brak opcjonalnej komnaty na tym piętrze.'))
                return
            await self.send('Nie jesteś w legowisku Tytana ani na rozpoznanym progu lochu.')
            return
        await self.send('Komendy: tytani lista, tytani info, tytani status, tytani obrona.')

    async def dungeon_secrets_command_v2100(self, raw=''):
        arg = str(raw or '').strip().casefold()
        if not self.character:
            return
        chamber=chamber_identity(self.character.room_id)
        if arg in ('sekret','odbierz','zbadaj'):
            if not chamber or chamber[0]!='secret':
                await self.send('Aby zbadać sekret, wejdź do Sekretnej Komnaty co 25 pięter i wpisz lochy7 sekret.')
                return
            if self.combat_mob_key:
                await self.send('Najpierw zakończ walkę.')
                return
            _,family,floor=chamber
            first=self.server.db.claim_titan_secret_v2100(self.account_id,family,floor)
            if first:
                await self.send(f'ODKRYCIE: {FAMILIES[family]}, piętro {floor}. Esencja Pradawnego Tytana trafia do szkatułki. Sekret zapamiętany na stałe.')
            else:
                await self.send('Ten sekret został już odkryty przez tę postać. Nie możesz ponownie odebrać nagrody.')
            return
        source=dungeon_identity(self.character.room_id)
        await self.send('NIESKOŃCZONE LOCHY 7.0: na piętrach będących wielokrotnością 25 odkrywasz boczną komnatę. Co 50 pięter legowisko Tytana; pozostałe progi 25 — sekret z osobistą nagrodą. Żadnych pułapek, brak resetowania checkpointów. Portal i astralportal działają po staremu.')
        if source:
            family,floor=source
            await self.send(f'Tutaj: {FAMILIES[family]}, piętro {floor}. Rodzaj odnogi: {challenge_kind(floor) or "brak"}. Wpisz kierunki, aby znaleźć wejście.')
        if chamber and chamber[0]=='secret':
            _,family,floor=chamber
            known=self.server.db.titan_secret_known_v2100(self.account_id,family,floor)
            await self.send(f'Sekret piętra {floor}: '+('już odkryty.' if known else 'czeka na odkrycie. Wpisz lochy7 sekret.'))
