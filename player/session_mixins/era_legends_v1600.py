# -*- coding: utf-8 -*-
"""Accessible 1.60 discovery and existing-system guidance."""
import time
from systems.era_legends_v1600 import UNDERGROUND,FRONTS,HUNTS,active_invasion_v1600

class SessionEraLegendsV1600Mixin:
    async def era_legends_v1600(self, raw=''):
        arg=str(raw or '').strip().lower()
        if arg in ('orki','orkowie','droga','trasa'):
            await self.send('DO ORKÓW: ze Świątyni idź na Plac Dusz, potem do Rozdroża Czterech Wiatrów. Stamtąd na północny wschód i traktem do Valdorii. Dalej przez Osadę Wędrowców na północ do Gor-Khaz.')
            await self.send('Automatyczna trasa: walk orki, walk orkowie lub walk gor khaz. Trasa nie wymaga wejścia do Krypty.')
        elif arg in ('podziemia','krolestwa','królestwa'):
            await self.send('PODZIEMNE KRÓLESTWA: z Rozdroża Czterech Wiatrów idź traktem do Warty Północnych Rubieży, potem DÓŁ.')
            for slug,name,*_ in UNDERGROUND: await self.send(name+': wejście z Wielkiej Bramy Podziemnych Królestw.')
        elif arg in ('wojny','frakcje','fronty'):
            await self.send('FRAKCJE I WOJNY PvE 5.0: cztery fronty, prawdziwe walki i dwu-godzinne zlecenia u dowódców.')
            for _,name,_,_,_ in FRONTS: await self.send(name+'.')
        elif arg in ('twierdza','gildie','gildia'):
            await self.send('GILDIE I TWIERDZE 5.0: w gildia siedziba rozbuduj rozwijasz prawdziwą siedzibę ze wspólnego skarbca.')
            await self.send('Poziom 3 odblokowuje Salę Wojenną i Wieżę Obserwacyjną; poziom 6 — Archiwum Reliktów. Kontrakty, bossowie i trofea zachowują dawny zapis.')
        elif arg in ('najemnicy','najemnik'):
            await self.send('NAJEMNICY 6.0: strażnik automatycznie osłania podczas walki z potężnym bossem i w tej samej turze nadal atakuje pełną mocą. Reszta najemników zachowuje inteligentne skille, leczenie i taktykę.')
        elif arg in ('ocean','glebiny','głębiny'):
            await self.send('OCEAN 5.0: od Przystani Latarników droga DÓŁ prowadzi do ośmiu nowych ruin i dwóch bossów.')
            await self.send('Bitwy flot: ocean4 cele, ocean4 atak glebiny, ocean4 atak meduzy, ocean4 atak cesarz. Trzy nowe przeciwniki flot NPC.')
        elif arg in ('inwazje','inwazja','eventy'):
            event=active_invasion_v1600()
            await self.send('INWAZJE ŚWIATOWE: jeden aktywny front rotuje co cztery godziny. Prawdziwy boss pojawia się przy wejściu gracza w region wydarzenia.')
            await self.send('Teraz: '+event['title']+'. Strefa: '+event['room_id']+'.')
        elif arg in ('bestia','bestie','bestia r iusz','bestiariusz','lowcy','łowcy'):
            await self.send('ŁOWCY LEGEND: dziesięć polowań na rzeczywistych bossów, zlecanych przez Mistrzów Łowów na Trakcie, w Podziemiach i w Głębinach.')
            await self.send('Zabicia zapisują się w istniejącym bestiariuszu. Użyj: bestiariusz, quest list, quest przyjmij.')
            for _,_,name in HUNTS: await self.send(name+'.')
        else:
            await self.send('SOULBOUND 1.60.0 — WIELKA ERA LEGEND: 7 aktualizacji PvE. Bez resetu postaci, bez Generator Core.')
            await self.send('Podkomendy: era60 orki, era60 podziemia, era60 wojny, era60 twierdza, era60 najemnicy, era60 ocean, era60 inwazje, era60 lowcy.')
