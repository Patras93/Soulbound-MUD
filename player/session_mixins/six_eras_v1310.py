# -*- coding: utf-8 -*-
"""Short, NVDA-friendly, read-only six-eras travel guide."""
from __future__ import annotations

class SessionSixErasV1310Mixin:
    async def show_six_eras_v1310(self, args=''):
        key=str(args or '').strip().lower()
        sections={
          'imperia':(
            'ERA IMPERIÓW: z Domów Frakcji czterech krain idź na północ.',
            'Czekają twierdze, wojenne posterunki, cztery dowódcze bossy i kontrakty obrony.',
            'Wpisz quest list, by zobaczyć konkretne zadania.'),
          'wymiary':(
            'WOJNA WYMIARÓW: Podziemne Królestwo, Podniebny Archipelag, Valdoria — Wieża Obserwacyjna, północ.',
            'Trzy odrębne obszary: Cień, Żywioły, Astralna Pustka. Każdy ma kupca i własnego władcę.'),
          'odkrywcy':(
            'WIELKA ERA ODKRYWCÓW: z Portu Dusz dotrzyj do ocean_platform, potem góra.',
            'W Porcie Trzech Rejsów wybierz wschód, zachód albo północ. Na wyspach są kupcy i bossowie.',
            'Stare trasy statków Ocean 2.0 pozostają bez zmian.'),
          'gracze':(
            'ŚWIAT GRACZY: Zaginiony Kontynent, Gospoda Wędrowców, następnie północ.',
            'Dom: house. Gildia: gildia siedziba. Handel między graczami: handel.',
            'W Wolnej Dzielnicy dostępne są kontrakty, handlarze i strażnicy karawan.'),
          'starozytni':(
            'PRZEBUDZENIE STAROŻYTNYCH: z sal tronowych czterech krain idź na północ.',
            'Każdy z czterech bossów ma własny żywioł, kolejne fazy i rzadkie trofea.'),
          'dusze':(
            'DZIEDZICTWO DUSZ: w Podniebnym Archipelagu znajdź Dziki Gaj, następnie północ.',
            'Przyjmij pięć powiązanych zadań u Mistrzyni Pamięci Dusz.',
            'Finał: Relikt Dziedzictwa Dusz, bez resetu poziomów postaci.'),
        }
        aliases={'imperium':'imperia','imperiors':'imperia','wymiar':'wymiary',
                 'ocean':'odkrywcy','domy':'gracze','gildie':'gracze',
                 'bossowie':'starozytni','dziedzictwo':'dusze','dusza':'dusze'}
        key=aliases.get(key,key)
        if key in sections:
            for line in sections[key]: await self.send(line)
            return
        await self.send('SZEŚĆ ER v1.31.0. Wpisz: ery imperia, ery wymiary, ery odkrywcy, ery gracze, ery starozytni, ery dusze.')
        if key and key not in ('pomoc','help','info','lista',''):
            await self.send('Nie ma takiej części. Dostępne: imperia, wymiary, odkrywcy, gracze, starozytni, dusze.')
