# -*- coding: utf-8 -*-
"""HELP, changelog and skill help."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import os
from difflib import get_close_matches
from core.classes_skills import effective_skill_mana_cost
from core.progression_600 import SKILL_MAX_LEVEL
from core.progression_resources import skill_xp_to_next
from player.session_mixins.exploration_progress import ALL_EXPLORATION_ROOMS, ROOMS, normalize_lookup_text
from player.session_mixins.io_auth_character import CLASS_SKILLS
from player.session_mixins.museum_bounty import BESTIARY_CATALOG
from storage.db_schema import FISH_RESOURCE_IDS
from systems.content_registry import LATEST_CHANGES, LATEST_CHANGES_TITLE
from systems.content_registry import HELP_TOPICS, HELP_TOPIC_ALIASES
from world.world_state import _FINAL_SKILL_HELP_EXACT_INDEX, _FINAL_SKILL_HELP_SEARCH_ROWS


from .help_parts_v109 import HelpHistoryV109Mixin, HelpSkillsV109Mixin

class SessionHelpSystemMixin(HelpHistoryV109Mixin, HelpSkillsV109Mixin):


    async def show_where(self, args=""):
            action = normalize_lookup_text(args or "")
            if action in ("ep", "punkty", "eksploracja"):
                await self.show_exploration("")
                return
            if action in ("fame", "fama"):
                # Region-based Fame also supports lazily generated dungeon floors.
                await self.fame_v1702("tutaj")
                return
            room = ROOMS.get(self.character.room_id)
            if not room:
                await self.send("Nie mogę ustalić bieżącej lokacji. Użyj look.")
                return
            await self.send(f"Jesteś tutaj: {room['name']}. Strefa: {room['zone']}.")
            if action in ("cele", "miasto", "walk"):
                await self.show_current_city_walk_destinations()
                return
            if action in ("pomoc", "help", "?"):
                await self.send("gdzie — aktualna lokacja i wyjścia; gdzie fame / where fame — none, some, most lub all w bieżącym terenie; gdzie cele — cele prowadzenia w mieście; trasa <cel> — zaplanuj drogę; walk <cel> — rozpocznij prowadzenie.")
                return
            await self.show_exits()
            await self.send("Szukasz miejsca? gdzie cele, trasa <cel>, walk <cel>.")

    def help_commands(self):
            lines = [
                "KRÓTKIE KOMENDY: help proste komendy — wszystkie nowe i stare aliasy; help <temat> otwiera opis, nie używa umiejętności.",
                "help / pomoc - kategorie pomocy; help [temat] / pomoc [temat] - wybrany temat; help tematy / topics - pełna lista",
                "changes / zmiany / changelog - ostatnie zmiany (do 20 linii); zmiany 50 / 100; zmiany wszystkie - pełna historia",
                "progress / postep - pełne podsumowanie: Level, Biegłość, Soul, profesje, reputacje, osiągnięcia, tytuły i eksploracja; progress region - bieżący region",
                "braki / gaps / missing - konkretne liczby brakujące do następnego Levelu, Soul Tieru, poziomów profesji, rozbudowy Gildii i pełnych kolekcji; pokazuje też aktywne cele",
                "historia / history / lifetime - trwała Historia postaci: walki, questy, kontrakty, profesje, zbiory, eksploracja i Bestiariusz",
                "bufor / bufory [xp|loot|quest|system|chat|party|tell|walka|all] [1-100] - sesyjne bufory ostatnich komunikatów; działa też historia xp / historia loot / historia quest",
                "eksploracja / exploration [all] - procent odkrycia stref i świata",
                "ep - całkowita liczba zdobytych Exploration Points; ep region - bieżąca strefa; ep all - pełne zestawienie",
                "osiagniecia / achievements - Bronze, Silver, Gold i Platinum",
                "najemnik rozwoj [imię] - poziom równy twojemu; najemnik taktyka <imię> <automatyczna|szturm|obrona|wsparcie> - dowolna zmiana bez grindu i kosztu",
                "kryzysy / kryzys start|status|ratuj|odbierz - wielkie wydarzenia świata w 4 krainach",
                "kariera [status|walka|profesje|rekordy|postep] — odczyt trwałych statystyk; osiagniecia postep — kolejne progi informacyjne",
                "nawigacja [status|krok|okolica|cel <nazwa>|druzyna] — Nawigacja 2.0 dla NVDA",
                "druzyna raport / zbiorka / trasa <cel|krok|off> — Party 4.0, koordynacja bez teleportacji",
                "tytuly / titles; tytul <nazwa> - lista i aktywny tytuł; Titles 2.0 dodaje tytuły za eksplorację, bossy, profesje, Kurierów i gildie; tytuły są prestiżowe i nie dają statystyk",
                "bounty / zlecenia / contracts - losowana Tablica Zleceń; kontrakty startują od 0/x i czytają postęp na żywo",
                "kolekcja / collection - Collection Codex; 2.0: kolekcja klasy, sety2, legendy, materialy eq, regiony, instancje",
                "rankingi / leaderboard - Top Krypty, Wieży, bossów, legend i kompletnych setów",
                "bosskodex / bosscodex [lista|nazwa] - kille, czas, solo/grupa, najwyższa wersja piętra i odkryte unikalne dropy",
                "historiadropow / drophistory - ostatnie wartościowe dropy",
                "zdobycze [legendarne|epickie|rzadkie|wszystkie] [1-30] / zdobycze szukaj <nazwa> — czytelna lista zapisanych dropów",
                "loot rare+ / epic+ / legendary / all / off - filtr komunikatów lootu pod NVDA",
                "opis [nazwa] / describe [name] - szczegółowy opis elementu świata",
                "najemnicy (w tawernie) - 22 postacie do wyboru: po jednym najemniku dla każdej z 22 klas; najemnik skille [imię] - podgląd zdolności; najemnik specjalizacje [imię] - automatyczne specjalizacje 4.0; najemnik wynajmij <imię>; najemnik status; najemnik odeslij <imię|wszyscy> - do 3 NPC na stałe, niezależnie od pomocników UOSS",
                "look lub l - opis aktualnej lokacji",
                "exits / ex - kierunki i nazwy lokacji, do których prowadzą; exits info dodaje strefę i poziom zagrożenia",
                "map / mapa - w świecie mapa regionu, w instancji mapa sektora 100 pięter z procentem, sekretami i checkpointami; mapa instancje - podsumowanie",
                "sekret / secret - zbadaj ukryty punkt na specjalnym piętrze instancji i zapisz go na mapie",
                "bestiariusz / bestiary - dziennik pokonanych mobów; bestiariusz <mob> - lokacje, dropy, odporności i rekord zabicia",
                "krypta / crypt - informacje o nieskończonej Krypcie, bossach co 10 pięter i checkpointach",
                "wieza / astral - informacje o nieskończonej Wieży Astralnej od piętra 100",
                "astralportal [poziom] - zwykła i Mityczna Wieża: checkpoint co 10 poziomów; z Bramy LUB z odblokowanego checkpointu przeskok na dowolny inny odblokowany checkpoint; astralportal wyjdz wraca do Bramy",
                "portal [piętro] - zwykła i Mityczna Krypta: checkpoint co 10 pięter; z wejścia LUB odblokowanego checkpointu przeskok na inny odblokowany checkpoint; portal wyjdz wraca do Bramy/Sali",
                "W Katakumbach pod Świątynią: portal 1/2/3 - przejście na już odwiedzone piętro; portal - lista; portal wyjdz - wyjście.",
                "deepdungeon - status nieskończonego UOSS Deep Dungeon; deepelevator <piętro> - winda do odwiedzonego piętra; deepelevator 0 - Floor 0 po dotarciu do 100",
                "atlas / atlas odkrycia [regiony|miasta|wyspy|lochy|superbossy] - atlas świata; atlas profesje [nazwa] - wszystkie 14 profesji; atlas ryby|drewno|rudy|geody|zioła|surowiec - surowce",
                "woda / łowisko - mówi typ bieżącego łowiska, np. rzeka, jezioro, morze, ocean, kanał lub Zatopiona Grota; pokazuje też znane i nieodkryte gatunki",
                "dziennikryb / fishjournal [lista|nazwa] - odkryte gatunki, rzadkość, liczba połowów oraz rekord długości i masy",
                "rekordyryb / fishrecords [gatunek] - Fishing Records 2.0: osobiste i serwerowe rekordy długości, masy oraz najrzadszy okaz",
                "projekty / worldprojects; projekt ... - wspólne długoterminowe odbudowy świata",
                "legendarnekontrakty / legendarycontracts - bardzo długie kontrakty z ogromnym Class XP, Soul XP i walutą",
                "geody / geodes - geody w Sakwie Górnika; open geode / otwórz geodę - otwórz jedną geodę",
                "unlock / odklucz / odblokuj - otwórz skrzynię bossową właściwym kluczem; poza skrzynią odblokuj kolejny Tier Broni Duszy",
                "gdzie / where — lokacja i wyjścia; gdzie fame / where fame — status Fame terenu none/some/most/all; gdzie cele — lokalne cele walk; trasa <cel> — zaplanuj przejście",
                "prace — status przetopu, automatycznego zbierania i kolejki skilli; działa także podczas przetapiania",
                "combat concise / normal / full; combat ostatnie [liczba] — tryb i historia komunikatów walki",
                "teren info <nazwa> - Soul, NPC, questy, bossowie, profesje i dojście w regionie",
                "location / lokalizacja - lokacja, strefa i wyjścia",
                "north/south/east/west/up/down lub n/s/e/w/u/d - chodzenie; każdy krok najpierw rozpoczyna marsz, potem dopiero przenosi do sąsiedniej lokacji",
                "prowadz <cel> / walk <cel> - automatycznie prowadzi dokładnie do rozpoznanej lokalizacji lub NPC; działa też walk to <cel>",
                "walk dol / walk dool - na piętrze lochu prowadzi do przejścia na kolejne piętro; ostatni krok wykonujesz ręcznie (również w Labiryncie Echa, Deep Dungeon, Magitek i lochach profesji)",
                "walk gora / walk góra - na piętrze zwykłej i Mitycznej Wieży Astralnej lub Twierdzy Gigantów prowadzi przed wejście na kolejne piętro; ostatni krok w górę ręcznie",
                "walk krypta dół - będąc na piętrze zwykłej Krypty prowadzi przed zejście na następne piętro; samo zejście wykonujesz ręcznie",
                "/ - sam znak ukośnika i Enter natychmiast teleportuje do Świątyni Odrodzenia; w drużynie obejmuje tylko osoby stojące razem w tej samej lokacji",
                "hp - HP, Mana i aktywne czasowe efekty; score pokazuje tę samą linię efektów w pełnym profilu",
                "buffs / effects / efekty - szybka lista aktywnych buffów i stanów bojowych z pozostałym czasem; obejmuje wszystkie klasy, V-MAX, Guard, Evade i Overheat",
                "wimpy set <1-99> - automatyczna ucieczka przy wskazanym procencie HP; wimpy off wyłącza; wimpy pokazuje status",
                "eventxp / xpevent - status godzinnego eventu x2 EXP; aktywne okno trwa pierwsze 15 minut każdej godziny",
                "prowadz status - bieżący cel, pozostała droga i następny krok; prowadz stop - natychmiast przerwij prowadzenie",
                "trasa <cel> / route <cel> - zaplanuj drogę bez ruchu; trasa pełna <cel> - wszystkie kroki; trasa krok - następny kierunek",
                "prowadz lista / walk list - kategorie: miasto, gildia, profesje, tereny, lochy, npc, wszystko",
                "who - gracze online",
                "say tekst - rozmowa lokalna",
                "tell gracz tekst - wiadomość prywatna",
                "załóż drużynę; zaproś <gracz>; dołącz; odrzuć; opuść; wyrzuć <gracz>; rozwiąż; lider <gracz> - bezpośrednie komendy drużynowe; działa też druzyna / party",
                "zasłoń / zaslon [off] - Strażnik chroni drużynę w tej samej lokacji, przejmując aggro wspólnego przeciwnika",
                "pc tekst - czat drużyny",
                "charyzma / charisma - szósta statystyka; rabat sklepowy i limit drużyny",
                "multiclass / klasy - jedna stała klasa na postać, zapis poprzednich klas zachowany",
                "multiclass add/remove - wyłączone; klasa wybierana przy tworzeniu postaci",
                "stats / staty - statystyki czytane osobno; staty info - baza, efektywne wartości, EQ i mechanika",
                "hp / zdrowie - szybkie bieżące i maksymalne HP oraz Mana",
                "score / wynik - podsumowanie postaci, klas, Biegłości, Duszy (Soul XP: obecny / wymagany / brakujący), statystyk, portfela i terenu",
                "odmiana / przypadki - pokaż 7 form imienia postaci",
                "skills / umiejetnosci - lista umiejętności aktywnych klas; skills all - nazwy skilli/spelli wszystkich 22 klas",
                "spells / spels / czary - czary aktywnych klas magicznych; spells all / spels all - czary wszystkich klas magicznych",
                "kodeksklasowy <klasa> / classcodex <class> - wszystkie skille, wymagana Biegłość, nauczyciel, koszt i status odblokowania",
                "skillnames / nazwyskilli - wszystkie nazwy skilli wszystkich klas",
                "skill / umiejetnosc / cast <nazwa lub numer> [cel] - użyj umiejętności",
                "help skill <nazwa> / skill info <nazwa> - pomoc konkretnej umiejętności; help <temat> zawsze wyświetla temat pomocy",
                "kolejka / kolejka lista - pokaż zapisane skille i czary; każda kolejka ma 40 aktywnych slotów na Levelu 1 i +1 slot co 10 Leveli, do 120 na Levelu 800; kolejka dodaj automatycznie włącza rotację",
                "kolejka usuń <nr>, kolejka wyczyść [typ], kolejka góra/dół i kolejka on/off - pełne zarządzanie rotacją; pasywki nie zajmują slotów",
                "aoe on / aoe off - globalnie włącza lub ogranicza ofensywne efekty wielocelowe; help aoe pokazuje zasady targetowania i party",
                "użyj umiejętność <nazwa> [cel] / use skill <name> [target] - alternatywne użycie skilla",
                "learn / naucz / ucz - przy nauczycielu aktywnej klasy pokazuje tylko odblokowane, jeszcze nienauczone skille i ceny; learn <numer lub nazwa> uczy; pelny katalog: kodeksklasowy",
                "soul / dusza - szybki stan Duszy; dusza info - Soul XP, Tiery, Próby i następny cel",
                "forma lista / forma wybierz <nazwa lub nr> / forma auto - formy Broni Duszy; relic / relikt pozostają zgodnymi aliasami",
                "portfel / money / saldo - jedno wspólne saldo automatycznie pokazane jako mithril, złoto i srebro",
                "daj / przekaż <gracz> <przedmiot>; daj <gracz> <ilość> <przedmiot>; daj <gracz> <ilość> złota - przekazywanie graczowi w tej samej lokacji",
                "bank - Bank Dusz na Rynku; waluta i trwała skrytka przedmiotów",
                "portfel - pokazuje wspólną walutę wszystkich postaci na koncie oraz kurs nominałów",
                "professions / profesje - szybki stan profesji; profesje info - XP, rangi i zasady",
                "narzedzia / tools - szybki stan narzędzi; narzedzia info - XP, Tiery, bonusy i sprzedawcy",
                "profesje - 22 profesje do poziomu 800; starsze 14: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo, Jubilerstwo, Krawiectwo, Garbarstwo, Stolarstwo, Zaklinanie, Archeologia, Kartografia. Do tego 8 nowych. Komendy: profesja kup <nazwa>; pracuj Kupiectwo pakuj",
                "archeologia / wykop - profesja eksploracyjna 1-600; kartografia / mapuj - profesja eksploracyjna 1-600",
                "statek / zegluj / skarby / handel morski - Ocean 2.0; help ocean pokazuje pełną składnię",
                "handel morski wez <nr> / oddaj / porzuc - kontrakt morski; objazd lub zmiana wód nie zeruje aktywnego kontraktu",
                "superbosses - lista unikalnych Super Bossów i wymagania; Serpentarius wymaga osobistego dotarcia do Deep Dungeon 100; superboss <nazwa> - wejście do odblokowanego wyzwania; help superbossy - zasady",
                "relic / relikt - zgodne aliasy systemu form Broni Duszy; pełne zarządzanie: forma lista / wybierz / auto",
                "rangi / ranks - pełna lista rang profesji",
                "tools / narzedzia - skrót wszystkich 14 narzędzi",
                "wedka / kilof / pila / mlot / noz / sierp / mozdzierz / szczypce / zestawkrawiecki / nozgarbarski / ciesielskie / fokus / pedzel / kompas - pełne informacje o wybranym narzędziu",
                "tiers / tiery / nazwytierow - pełna lista Tierów wszystkich 14 narzędzi",
                "fish / wedkuj / low - pojedynczy połów",
                "low on / fish on - auto-łowienie",
                "low off / fish off - wyłącz auto-łowienie",
                "mine / kop - pojedyncze wydobycie",
                "kop on / mine on - auto-kopanie",
                "kop off / mine off - wyłącz auto-kopanie",
                "tnij / drwal / woodcut - pojedyncze pozyskanie drewna",
                "tnij on / woodcut on - auto-Drwalstwo",
                "tnij off / woodcut off - wyłącz auto-Drwalstwo",
                "zbieraj / zielarstwo - pojedynczy zbiór ziół",
                "zbieraj on / zbieraj off - auto-Zielarstwo",
                "ziola / herbs - Torba Zielarska; pokazuje ilość ziół i szacowany zarobek",
                "alchemia / warz receptura - warzenie mikstur",
                "net / siatka - Siatka na ryby; pokazuje liczbę ryb i szacowany zarobek ze sprzedaży",
                "bag / sakwa - Sakwa górnicza; pokazuje ilość rud i szacowany zarobek",
                "drewno / stos / woodpile - Stos drewna; pokazuje ilość drewna i szacowany zarobek",
                "szkatułka / craftbox - Szkatułka Rzemieślnicza podzielona na kategorie: Kowalstwo, Jubilerstwo, Alchemia, Runy, Salvage i pozostałe",
            "salvage / rozłóż <pełna nazwa EQ> - u Haldora rozkłada pojedyncze niezałożone EQ; salvage wszystko / rozłóż wszystko hurtowo rozkłada wszystkie wolne przedmioty obsługiwane przez Salvage, pomijając założone EQ i chroniony Moogle Board; materiały trafiają do Szkatułki, a operacja daje Kowalstwo XP bez nabijania użyć Młota Rzemieślniczego",
            "gdzie zdobyc <przedmiot> [pelne], do czego <przedmiot>, braki receptura <nazwa> i receptury mozliwe - aktualne planowanie źródeł/craftingu z danych runtime",
            "przetop stop - zatrzymuje aktywną serię przetapiania bez kasowania reszty ekwipunku",
            "reforge / przekuj <pełna nazwa EQ> - u Haldora zmienia jeden affix EQ za Esencję Przekucia; próg Biegłości nie zmienia się",
            "runy - informacje, tworzenie i wyjmowanie run; runa <typ> <EQ> osadza runę w endgame EQ; tworzenie run od v0.59.2 zużywa też Odłamki Duszy",
            "gildia - Gildia graczy: poziomy 1-800, Siedziba 1-10, budynki, kontrakty, bossowie, skarbiec, rangi, bank, trofea, osiągnięcia, log i czat",
            "znajomi - lista wszystkich postaci zaakceptowanych znajomych (takze nowych); dodaj/akceptuj/odrzuc/usun; zaproszenia party i gildia",
            "tell <gracz> <tekst>; reply <tekst> - prywatne wiadomości i szybka odpowiedź do ostatniego nadawcy",
            "osiagnieciaklasowe - osiągnięcia klas i profesji na progresji 1-600",
                "put fish net / wloz ryba siatka - przenieś ryby do Siatki",
                "put ore bag / wloz ruda sakwa - przenieś rudy do Sakwy",
                "take przedmiot net/bag / wyjmij przedmiot siatka/sakwa - wyjmij surowiec",
                "sell / sprzedaj - sell all / sprzedaj wszystko sprzedaje tylko niezałożone EQ; mikstury i zwykłe przedmioty są chronione. Surowce hurtowo: wszystko siatka/sakwa/stos/torba",
                "receptury / przepisy / recipes <profesja> - receptury osobno dla: kowalstwo, gotowanie, alchemia, jubilerstwo, krawiectwo, garbarstwo, stolarstwo, zaklinanie; `receptury mozliwe` grupuje możliwe receptury według profesji",
                "zamowienia / zamówienia - rotujące zamówienia wszystkich 14 profesji; wez <nr>, status, oddaj, porzuc",
                "porownaj / porównaj <przedmiot> - porównanie posiadanego EQ z aktualnie założonym; pokazuje też Tożsamość EQ i Etap źródła EQ, jeśli są dostępne",
                "craft / stworz / wytworz receptura - rzemiosło z rud i drewna",
                "cook / gotuj receptura - przygotuj potrawę z ryb",
                "inventory / i - zwykły ekwipunek",
                "equipment / eq - szybkie EQ zawsze pokazuje też Broń Duszy; eq info - Soul XP, pełne bonusy, sockety i aktywne sety; eq info 1 lub eq info glowa - opis konkretnej założonej części",
                "sety / sety info / sety <klasa> - zestawy klasowe 2/4/6/8 dla 14 klas",
                "help loot_krypty - rarity, losowe statystyki i sety Krypty; help loot - globalne dropy; help zrodla_eq - role źródeł EQ; help gamefeel - rzadkie momenty nagród",
                "equip / załóż przedmiot albo slot - m.in. hełm, zbroja, rękawice, nogi, buty, tarcza, naramienniki, pas, peleryna, karwasze, bransoleta, kolczyki, relikt, pierścienie, talizmany, akcesoria i naszyjnik",
                "Biżuteria: załóż <nazwa pierścienia/talizmanu/kolczyka/akcesorium> wybiera wolny lub słabszy podwójny slot; ręczne sloty 1/2 nadal działają.",
                "Skróty EQ: zh hełm, zz zbroja, zr rękawice, zn nogi, zb buty, ztar tarcza, zp pierścienie auto, zt talizmany auto, zp1/zp2 i zt1/zt2 ręcznie, zna naszyjnik, zkol kolczyki auto, zkol1/zkol2 ręcznie, zakc akcesoria auto, znar naramienniki, zpas pas, zpel peleryna, zkar karwasze, zbra bransoleta, zrel relikt.",
                "use / użyj - przedmioty, skille i czary; np. użyj ciecie goblin albo użyj pocisk goblin",
                "shop / sklep / list / lista - krótka numerowana oferta: numer, nazwa i cena",
                "shop info <numer> / sklep info <numer> - pełny opis, wymagania, Tożsamość EQ, Etap źródła i porównanie; shop/list/kup używają tej samej ceny",
                "Brak price=None/0 nie robi przedmiotu darmowym; prawdziwe token-only pokazuje koszt tokenu bez mylącego 0 srebra",
                "buy / kup przedmiot - kup po nazwie lub numerze z listy; np. kup 9 albo kup 9 3",
                "talk npc - rozmowa, zadania i lekcje nauczycieli klasowych",
                "teachers / nauczyciele - lista nauczycieli w Sali Gildii",
                "help quest - pełna pomoc dziennika; quest - aktywne; quest godzinne - wszystkie zlecenia godzinne; każde odnawia się niezależnie po 60 minutach; questy ukończone; quest list <NPC>; accept quest <numer>; oddaj quest <numer>; quest info/porzuć <numer>",
                "consider / con / ocen <mob> - oceń dowolnego zabijalnego moba bez rozpoczynania walki; działa też np. con 2 goblin",
                "k <mob> / attack / atakuj / zabij / kill <mob> - szybki atak na wskazanego przeciwnika",
                "ciało / zwloki / corpse - pokaż ciała i ich ekwipunek",
                "przeszukaj ciało / loot - zabierz ekwipunek z ciała moba",
                "flee / uciekaj - ucieczka",
                "unlock / odklucz / odblokuj - skrzynia bossowa z kluczem; unlock soul / odklucz dusza - odblokuj gotowy Soul Tier",
                "save / zapisz - zapis",
                "quit / wyjdz - zapisz bieżącą postać i wróć do MENU POSTACI",
            ]
            if self.is_admin():
                lines.extend([
                    "admin help / administrator pomoc - ukryte opcje właściciela",
                    "wipe / wyczyść moje postacie POTWIERDZAM - reset Twoich postaci bez kasowania konta",
                    "wipe / wyczyść wszystkie postacie POTWIERDZAM - serwerowy reset postaci bez kasowania kont",
                ])
            return lines


    async def show_latest_changes(self, args=""):
            """NVDA: bounded default output; the complete history stays opt-in."""
            argument = normalize_lookup_text(str(args or "").strip())
            full = argument in ("wszystkie", "calosc", "całość", "all", "pelne", "pełne", "full")
            if argument.isdigit() and len(argument) <= 4:
                limit = max(1, min(100, int(argument)))
            else:
                limit = 20
            lines = self.full_changelog_lines()
            if full:
                await self.send("PEŁNA HISTORIA ZMIAN SOULBOUND")
                await self.send("Wysyłam całą historię na Twoje życzenie. Może być bardzo długa.")
                selected = lines
            else:
                await self.send(f"OSTATNIE ZMIANY SOULBOUND — {limit} pierwszych wierszy")
                selected = lines[:limit]
            for line in selected:
                if line.strip():
                    await self.send(line)
            if not full and len(lines) > len(selected):
                await self.send("Więcej: zmiany 50 lub zmiany 100. Pełna historia: zmiany wszystkie.")








    async def show_help(self, topic=""):
            # v11.00.3: canonical topic takes priority over historical aliases.
            # Historically an alias "klasy" -> "multiclass" hid the real help
            # for "klasy", and topics like "Kupiectwo" were absent altogether.
            raw = str(topic or "").strip().lower()
            folded = normalize_lookup_text(raw)
            if not raw:
                key = ""
            elif raw in HELP_TOPICS:
                key = raw
            elif folded in HELP_TOPICS:
                key = folded
            else:
                searchable = {}
                # One canonical normalization handles Polish accents, spaces,
                # underscores and hyphens without losing original topic names.
                for name in HELP_TOPICS:
                    searchable.setdefault(normalize_lookup_text(name), name)
                for alias, destination in HELP_TOPIC_ALIASES.items():
                    if destination in HELP_TOPICS:
                        searchable.setdefault(normalize_lookup_text(alias), destination)
                key = searchable.get(folded)
                if key is None:
                    key = searchable.get(folded.replace(" ", ""), raw)
                if key not in HELP_TOPICS and folded.replace(" ", ""):
                    # Only a unique compact spelling may auto-resolve. For
                    # ambiguous input provide suggestions, not the wrong help.
                    compact = folded.replace(" ", "")
                    compact_hits = {dest for alias, dest in searchable.items()
                                    if alias.replace(" ", "") == compact}
                    if len(compact_hits) == 1:
                        key = next(iter(compact_hits))

            # v0.8.72: temat administratora jest całkowicie ukryty przed zwykłymi kontami.
            if key == "admin_owner" and not self.is_admin():
                await self.send("Nieznany temat pomocy. Wpisz help tematy.")
                return

            # v0.8.52: pełny help dla wszystkich 253 skilli/spelli, także klas
            # nieaktywnych. Działa `help skill <nazwa>` oraz bezpośrednio
            # `help <nazwa skilla>`. Zwykłe tematy help zachowują pierwszeństwo.
            raw_normalized = normalize_lookup_text(raw)
            explicit_skill_help = any(
                raw_normalized.startswith(prefix)
                for prefix in (
                    "skill ", "spell ", "czar ", "umiejetnosc ", "zdolnosc "
                )
            )
            if explicit_skill_help:
                if await self.show_skill_help(raw):
                    return
                await self.send('Nie ma takiej umiejętności. Wpisz help umiejetnosci albo help tematy.')
                return
            if folded in ('skill', 'spell', 'czar', 'umiejetnosc', 'zdolnosc'):
                await self.send('POMOC: UMIEJĘTNOŚCI')
                await self.send('Spis: umiejetnosci lub nazwyskilli. Opis konkretnej umiejętności: help skill <nazwa>.')
                return

            if not key or key == "kategorie":
                await self.send("POMOC — KATEGORIE")
                await self.send("START: help podstawy, help proste komendy, help progresja800, help informacje, help komendy, help nawigacja.")
                await self.send("POSTAĆ: help statystyki, help hp, help score, help level, help dusza, help ekwipunek, help klasy, help rasy, help multiclass, help wzniesienie, help worldtier, help moogle board.")
                await self.send("WALKA: help walka, help statusy, help wimpy, help bossowie, help superbossy, help krytyki, help umiejetnosci, help druzyny, help skrzynie_bossow.")
                await self.send("ŚWIAT: help questy, help nawigacja, help ocean, help era60, help kontynent, help labirynt echa, help podziemia, help eksploracja, help bestiariusz, help atlas, help krypta, help portale, help sklepy.")
                await self.send("NOWE PROFESJE: help lowiectwo, help rolnictwo, help hodowla, help okretownictwo, help murarstwo, help inzynieria, help kupiectwo, help zeglarstwo, help karawana.")
                await self.send("PROFESJE: help profesje, help wedkarstwo, help gornictwo, help geody, help drwalstwo, help zielarstwo, help alchemia, help rzemioslo, help gotowanie, help jubilerstwo2, help krawiectwo/tailoring, help garbarstwo/leatherworking, help stolarstwo/carpentry, help zaklinanie/enchanting, help archeologia, help kartografia, help craftmastery.")
                await self.send("SPOŁECZNE: help gracze, help druzyny, help najemnicy, help przekazywanie, help reputacja, help social2, help mentor2, help housing2, help leaderboards2, help bufory, help pieniadze, help charyzma.")
                await self.send("SYSTEM: help logowanie, help smierc, help recaps, help loothistory2, help accessibility_presets, help audyt_v03055, help opisy, help zmiany.")
                if self.is_admin():
                    await self.send("ADMINISTRATOR: help admin.")
                await self.send("help tematy — lista tematów stronami; help tematy 2 — następna strona; help tematy wszystkie — komplet.")
                await self.send("help szukaj <fraza> — wyszukanie tematu i informacji.")
                await self.send("help wszystko / help all — pełny przewodnik.")
                await self.send("help <temat> albo pomoc <temat> — zawsze otwiera pomoc, nigdy nie wykonuje komendy ani skilla.")
                await self.send("help skill <nazwa> — opis konkretnego skilla lub spella (nie wykonuje go).")
                await self.send("Samo help albo pomoc zawsze wraca do tego indeksu kategorii.")
                return

            if folded.startswith(("szukaj ", "search ")):
                phrase = folded.split(" ", 1)[1].strip()
                if not phrase:
                    await self.send("Użycie: help szukaj <fraza>.")
                    return
                found = []
                for name, content in HELP_TOPICS.items():
                    if name == "admin_owner" and not self.is_admin():
                        continue
                    lines = content if isinstance(content, (list, tuple)) else [content]
                    if phrase in normalize_lookup_text(name) or any(
                        phrase in normalize_lookup_text(row) for row in lines
                    ):
                        found.append(name)
                await self.send(f"HELP SZUKAJ: {phrase}. Wyniki {len(found)}.")
                if found:
                    await self.send("Tematy: " + ", ".join(found[:15]) + ".")
                    if len(found) > 15:
                        await self.send("Więcej wyników: doprecyzuj szukaną frazę.")
                else:
                    await self.send("Brak wyników. Wpisz help tematy.")
                return

            if key == "tematy" or folded.startswith("tematy "):
                tail = folded[6:].strip() if folded.startswith("tematy ") else ""
                names = sorted(name for name in HELP_TOPICS
                               if name != "admin_owner" or self.is_admin())
                if tail in ("wszystkie", "all"):
                    await self.send(f"TEMATY POMOCY: {len(names)} wszystkich tematów.")
                    for name in names:
                        await self.send(name)
                    return
                if tail and not tail.isdecimal():
                    await self.send("Użycie: help tematy [numer strony], albo help tematy wszystkie.")
                    return
                page = max(1, int(tail or "1"))
                per_page = 25
                total_pages = max(1, (len(names) + per_page - 1) // per_page)
                if page > total_pages:
                    await self.send(f"Nie ma strony {page}. Dostępne strony 1-{total_pages}.")
                    return
                await self.send(f"TEMATY POMOCY: strona {page}/{total_pages}, łącznie {len(names)} tematów.")
                for name in names[(page-1)*per_page:page*per_page]:
                    await self.send(name)
                await self.send(f"help tematy {page+1} — następna strona." if page < total_pages
                                else "Koniec listy. help tematy wszystkie — całość.")
                await self.send("help szukaj <fraza> — szukanie we wszystkich tematach.")
                return

            if key == "komendy":
                await self.send("WSZYSTKIE KOMENDY")
                for line in self.help_commands():
                    await self.send(line)
                return

            if key == "wszystko":
                await self.send("PEŁNY PRZEWODNIK SOULBOUND")
                for name, lines in HELP_TOPICS.items():
                    if name == "admin_owner" and not self.is_admin():
                        continue
                    await self.send(name.upper())
                    for line in lines:
                        await self.send(line)
                await self.send("KOMENDY")
                for line in self.help_commands():
                    await self.send(line)
                return

            lines = HELP_TOPICS.get(key)
            if not lines:
                # `help <komenda>` should show actual help, not ask the player
                # to activate a skill. Covers all remaining registered commands
                # and aliases without touching gameplay or swallowing typos.
                from core.command_catalog import COMMAND_CATALOG
                from player.session_mixins.command_registry import COMMAND_REGISTRY
                resolved = COMMAND_CATALOG.resolve(raw)
                if resolved in COMMAND_REGISTRY and resolved not in ('admin', 'wipe'):
                    definition = COMMAND_CATALOG.definition(resolved)
                    aliases = sorted(a for a in (definition.aliases if definition else ())
                                     if not any(ch.isdigit() for ch in a))
                    await self.send('POMOC: ' + resolved.upper())
                    await self.send('Komenda: ' + (aliases[0] if aliases else resolved) +
                                    ' [argumenty].')
                    if aliases:
                        await self.send('Inne nazwy: ' + ', '.join(aliases[:8]) + '.')
                    await self.send('Opis i składnia: help komendy; help szukaj ' + resolved + '.')
                    return
                # v11.00.11: "help <pełna nazwa skilla>" musi rzeczywiście
                # korzystać z tego samego indeksu co "help skill <nazwa>".
                # Tematy i zarejestrowane komendy mają pierwszeństwo;
                # rozpoznana umiejętność otwiera wyłącznie opis (bez wykonania).
                # Indeks obsługuje polskie znaki, dawne aliasy i niezmienne ID.
                if self.find_global_skill_help_matches(raw):
                    await self.show_skill_help(raw)
                    return
                available = {}
                for name in HELP_TOPICS:
                    if name != "admin_owner" or self.is_admin():
                        available[normalize_lookup_text(name)] = name
                for alias, destination in HELP_TOPIC_ALIASES.items():
                    if destination in HELP_TOPICS and destination != "admin_owner":
                        available.setdefault(normalize_lookup_text(alias), destination)
                suggestions = []
                for match in get_close_matches(folded, available, n=8, cutoff=0.52):
                    value = available[match]
                    if value not in suggestions:
                        suggestions.append(value)
                    if len(suggestions) == 3:
                        break
                await self.send(f"Nie ma tematu pomocy: {raw}." +
                    (" Podobne: " + ", ".join("help " + x for x in suggestions) + "." if suggestions else ""))
                await self.send("help szukaj <fraza> — szukaj tematu; help tematy — lista stronami.")
                return

            await self.send("POMOC: " + key.upper())
            for line in lines:
                await self.send(line)
