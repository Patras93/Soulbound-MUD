# -*- coding: utf-8 -*-
"""v1.60.2: final, current public HELP overlay and navigational contracts.

Installs after the 1.50/1.60 expansions and old help refresh hooks.
Does not touch character/account data, economy or progression mathematics.
"""
from core.progression_600 import (
    CHARACTER_MAX_LEVEL, CLASS_MASTERY_MAX_LEVEL, PROFESSION_MAX_LEVEL,
    SKILL_MAX_LEVEL, SOUL_MAX_LEVEL, SOUL_WEAPON_MASTERY_MAX_LEVEL,
    TOOL_MAX_LEVEL,
)
from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP


def install_help_atlas_v1602(topics, aliases):
    names = sorted(set(TOOL_PROFESSION_MAP.values()))
    caps = {CHARACTER_MAX_LEVEL, CLASS_MASTERY_MAX_LEVEL, PROFESSION_MAX_LEVEL,
            SKILL_MAX_LEVEL, SOUL_MAX_LEVEL, SOUL_WEAPON_MASTERY_MAX_LEVEL, TOOL_MAX_LEVEL}
    if caps != {800}:
        raise RuntimeError('HELP v1.60.2: oczekiwano wspólnego limitu poziomów 800, odczytano '+str(caps))
    if len(names) != 14:
        raise RuntimeError('HELP v1.60.2: brak kompletu 14 profesji')

    # Many old public topics claimed cap 600. Preserve genuinely historical notes,
    # but do not advertise 600 as the LIVE cap for the core progression axes.
    replaced = 0
    for key, lines in list(topics.items()):
        updated = []
        for line in lines:
            phrase = str(line)
            if ('1-600' in phrase or '1–600' in phrase) and not any(
                x in phrase.casefold() for x in ('historycznie', 'w poprzedniej wersji', 'dawniej')
            ):
                phrase = phrase.replace('1-600', '1-800').replace('1–600', '1–800')
                replaced += 1
            updated.append(phrase)
        topics[key] = updated

    topics['podstawy'] = [s.replace('1-600', '1-800') for s in topics.get('podstawy', ())]
    topics['progresja800'] = [
        'Aktualne maksymalne poziomy: postać, Biegłość klasowa, Soul, Broń Duszy, skille, wszystkie profesje i wszystkie narzędzia: 800.',
        'Statystyki Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma nie mają twardego limitu.',
        'Od poziomu 50 wymagana ilość EXP wzrasta stopniowo. Nagrody EXP za akcje, walki i zadania pozostają bez zmniejszania.',
        'Dokładny postęp: score, staty info, dusza info, profesje info, narzedzia info.',
    ]
    topics['progresja600'] = list(topics['progresja800'])
    aliases.update({'progresja800':'progresja800', 'progresja600':'progresja800',
                    'progresja':'progresja800'})

    topics['profesje'] = [
        f'W Soulbound jest {len(names)} profesji, każda od poziomu 1 do {PROFESSION_MAX_LEVEL}; każde narzędzie rozwija się osobno do {TOOL_MAX_LEVEL}.',
        'Od poziomu 50 rośnie wymagany EXP, ale nagrody, doświadczenie zdobyte wcześniej i poziomy postaci pozostają bez zmian.',
        'Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo; Kowalstwo, Gotowanie, Alchemia, Jubilerstwo, Krawiectwo, Garbarstwo, Stolarstwo, Zaklinanie; Archeologia i Kartografia.',
        'atlas profesje — katalog wszystkich 14; atlas profesje <nazwa> — NPC, narzędzia, zadania, receptury i komendy.',
        'profesje info / narzedzia info — poziomy, XP i rangi. Zamowienia — rotujące kontrakty; zamowienie porzuc — porzucenie.',
        'Receptury i koszty: receptury <profesja>, receptury mozliwe, braki receptura <nazwa>, gdzie zdobyc <przedmiot>.',
        'Tempo czynności sprawdzaj w help tempo_profesji; premie za dobre materiały i wyjątkowe zbiory nadal działają.',
    ]
    topics['atlas'] = [
        'atlas / atlas odkrycia — Globalny Atlas świata: regiony, miasta, wyspy, lochy, platformy, ruiny, superbossy i sekrety.',
        'atlas profesje — wszystkie 14 profesji. atlas profesje <nazwa> — NPC, zadania, warsztat i aktualne receptury.',
        'atlas ryby, atlas rzeka, atlas jezioro, atlas morze, atlas ocean — poziomy Wędki i łowiska.',
        'atlas rudy / atlas geody — poziom Kilofa i głębokość; atlas drewno — poziom Piły; atlas zioła — poziom Sierpa.',
        'atlas <nazwa surowca> — konkretne miejsca i wymagania. Atlas odkryć pokazuje także nowe Krainy 1.50/1.60 i Labirynt Echa.',
    ]
    topics['gornictwo'] = [
        'Górnictwo i Kilof rozwijają się od poziomu 1 do 800. Wymagane EXP wyraźniej rośnie od poziomu 50, zdobywane EXP pozostaje bez zmian.',
        'kop — pojedyncze wydobycie; kop kierunki — lista 10 kierunków; wybierz sam numer 1-10, kop <numer> lub kop <kierunek> — rozpocznij automatyczne drążenie; kop off — zatrzymaj; kopalnia / mineinfo — postęp kopalni.',
        'Kopanie tuneli: kop north, south, east, west, northeast, northwest, southeast, southwest, up, down. Polskie odpowiedniki też działają.',
        'kop on <kierunek> także działa. Po otwarciu chodnika postać przechodzi dalej i drąży kolejną ścianę. Wykopane tunele zapisują się na stałe dla postaci. Zatrzymaj: kop off.',
        'Zwykłe i rzadkie żyły, geody i klejnoty mają własne wymagania i nagrody. Nowe rudy zależą od Kilofa i poziomu kopalni.',
        'atlas rudy — wszystkie rudy z wymaganiami. atlas geody — geody. atlas <nazwa rudy> — dokładny poziom Kilofa i minimalna głębokość.',
        'Wpisz atlas profesje gornictwo, żeby poznać specjalistę, zadania i komendy. Poziom i EXP: profesje info / narzedzia info.',
    ]
    topics['era60'] = [
        'Wielka Era Legend 1.60: Podziemne Królestwa, Frakcje i Wojny PvE, Gildie i Twierdze, Najemnicy 6.0, Ocean 5.0, Inwazje, Bestiariusz i Łowcy Legend.',
        'Komenda główna: era60. Działy: era60 orki / podziemia / wojny / twierdza / najemnicy / ocean / inwazje / lowcy.',
        'walk orki / walk gor khaz prowadzi zwykłą drogą z głównego świata.',
        'Atlasy regionów: atlas odkrycia regiony. Nowy bestiariusz: bestiariusz, help bestiariusz.',
    ]
    topics['kontynent'] = [
        'Zapomniane Światy 1.50: cztery krainy, Saga Duszy, nazwani bossowie i zadania 14 profesji.',
        'kontynent; kontynent saga; kontynent profesje; kontynent bossowie.',
        'Nowe tereny: atlas odkrycia regiony. Labirynt: lochy50 i help labirynt_echa.',
    ]
    topics['labirynt_echa'] = [
        'Nieskończony Labirynt Echa: pięć komór na piętro, boss co 10 pięter, bez sztucznego końca.',
        'lochy50 pokazuje opis systemu. walk dol lub walk dool prowadzi do zejścia i zatrzymuje przed przejściem piętra.',
        'Schodząc na następny poziom wpisz kierunek wskazany przez exits; zwykły walk nie omija bossa.',
        'Odkrycia: atlas odkrycia lochy.',
    ]
    topics['podziemia'] = [
        'Podziemne Królestwa v1.60: Bazaltowe Serce, Świetliste Grzyby, Kryształowa Monarchia, Imperium Bezdennych Żył.',
        'era60 podziemia — informacje o wejściach. atlas odkrycia regiony — odkrycie każdej krainy.',
        'Zadania i bossowie działają w PvE solo i drużynie.',
    ]
    topics['walk'] = [
        'walk <cel> prowadzi postać po dostępnych drogach. walk orki — dojście do Krainy Orków.',
        'walk dol / walk dool — automatyczne dojście do zejścia w podziemiach i lochach, bez wykonania ostatniego kroku.',
        'walk gora / walk góra — dojście do wejścia wyżej w wieżach, z zatrzymaniem przed przejściem piętra.',
        'Przed wejściem na kolejne piętro użyj exits i wybierz właściwy kierunek.',
    ]
    topics['zamowienia'] = [
        'zamowienia / zamówienia — aktywne i rotujące kontrakty wszystkich 14 profesji; nagrody zostały podniesione w v1.40.6.',
        'zamowienie porzuc — porzuca aktywny kontrakt bez usuwania posiadanych materiałów i bez kasowania historii.',
        'Nowa oferta ma własną wypłatę i EXP; wcześniej przyjęta zachowuje nagrodę zapisaną przy przyjęciu.',
    ]
    aliases.update({
        'górnictwo':'gornictwo', 'górnik':'gornictwo', 'kopanie':'gornictwo',
        'wędkarstwo':'wedkarstwo', 'żeglarstwo':'ocean',
        'ziół':'zielarstwo', 'zielarstwo':'zielarstwo',
        'labirynt echa':'labirynt_echa', 'labirynt':'labirynt_echa',
        'lochy50':'labirynt_echa', 'era 60':'era60',
        'atlas odkrycia':'atlas', 'atlas profesje':'atlas',
        'gora':'walk', 'dół':'walk', 'nawigacja lochy':'walk',
        'zapomniane światy':'kontynent', 'kraina orków':'era60',
        'podziemne królestwa':'podziemia',
        'zamówienia':'zamowienia', 'zamówienie':'zamowienia',
    })
    return {'version':'1.60.2','topics':len(topics),'profession_count':len(names),
            'old_cap_lines_replaced':replaced}
