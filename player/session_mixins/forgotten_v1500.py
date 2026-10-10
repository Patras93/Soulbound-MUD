# -*- coding: utf-8 -*-
"""NVDA-friendly discovery commands for 1.50.0 authored continent and infinite labyrinth."""
from systems.forgotten_world_v1500 import REGIONS, PROFESSIONS
from systems.echo_dungeon_v1500 import echo_identity


class SessionForgottenV1500Mixin:
    async def forgotten_continent_v1500(self, raw=''):
        arg=str(raw or '').strip().lower()
        if arg in ('profesje','profesja','rzemioslo','rzemiosło'):
            await self.send('PROFESJE 5.0: 14 profesji, każda ma 3 odnawialne próby po 12, 24 i 40 rzeczywistych akcjach.')
            await self.send('Specjaliści stoją w krainach: Szron, Żar, Korzenie i Gwiazdy. Wpisz quest list przy NPC.')
            for name,_,_ in PROFESSIONS:
                await self.send('Mistrz Ekspedycji ' + name)
            return
        if arg in ('saga','historia'):
            await self.send('SAGA ZAPOMNIANYCH ŚWIATÓW: 4 oddzielne historie po 10 etapów. Każdą prowadzi kronikarka przy wejściu do krainy.')
            await self.send('Etapy mają zapis w dotychczasowej bazie questów. Wpisz quest list, quest przyjmij 1 i oddaj quest 1.')
            return
        if arg in ('bossowie','boss','superbossowie'):
            await self.send('BOSSOWIE 5.0: 20 bossów czterech krain, 4 superbossów w ich sanktuariach oraz 1 wspólny w Tronie Czterech Wymiarów.')
            for data in REGIONS:
                await self.send(data[1] + ': ' + ', '.join(data[6]) + '; superboss: ' + data[7][0])
            return
        await self.send('ZAPOMNIANE ŚWIATY v1.50.0. Droga: Valdoria, Era Imperiów, Warownia — Sala Próby; stamtąd WSCHÓD.')
        await self.send('Z Bramy Zapomnianych Światów: PÓŁNOC Szron, WSCHÓD Żar, POŁUDNIE Las, DÓŁ Wrota Gwiazd.')
        await self.send('Na bramie: GÓRA Tron Czterech Wymiarów, w Gwiezdnych Wrotach DÓŁ do Nieskończonego Labiryntu Echa.')
        await self.send('Komendy: kontynent saga, kontynent profesje, kontynent bossowie, lochy50.')
        await self.send('Cztery krainy mają po 40 połączonych lokacji. Brak blokady poziomów i losowych pułapek.')

    async def forgotten_dungeons_v1500(self, raw=''):
        if self.character:
            found=echo_identity(self.character.room_id)
            if found:
                floor,role=found
                await self.send(f'NIESKOŃCZONY LABIRYNT ECHA: jesteś na piętrze {floor}, komora {role}.')
                await self.send('Wschód prowadzi przez komory. Z ostatniej komory DÓŁ — piętro dalej. Z pierwszej komory GÓRA — wyżej.')
                await self.send('Co 10 pięter boss; co 5 pięter elita. walk dol / walk dool prowadzi przed zejście. Użyj wyjscie, by wrócić do bramy.')
                return
        await self.send('NIESKOŃCZONY LABIRYNT ECHA: Valdoria -> Era Imperiów -> Sala Próby -> wschód, dół, dół.')
        await self.send('Każde piętro ma pięć komór. Co 5 pięter elita, co 10 pięter dodatkowy boss.')
        await self.send('Dalsze piętra tworzone są tylko przy wejściu. Nagrody skalują się z głębokością.')
        await self.send('Nie ma limitu pięter, blokady poziomu ani losowych pułapek. W lochu wpisz walk dol / walk dool, by dotrzeć przed zejście, albo wyjscie, by wrócić.')

    def dungeon_exit_destination(self, room_id=None):
        room_id=str(room_id or (self.character.room_id if self.character else ''))
        if echo_identity(room_id) is not None:
            return 'v1500_echo_entry', 'Nieskończony Labirynt Echa'
        return super().dungeon_exit_destination(room_id)
