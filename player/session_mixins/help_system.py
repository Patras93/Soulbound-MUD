# -*- coding: utf-8 -*-
"""HELP, changelog and skill help."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import os
from core.progression_600 import SKILL_MAX_LEVEL
from core.progression_resources import skill_xp_to_next
from player.session_mixins.exploration_progress import ALL_EXPLORATION_ROOMS, ROOMS, normalize_lookup_text
from player.session_mixins.io_auth_character import CLASS_SKILLS
from player.session_mixins.museum_bounty import BESTIARY_CATALOG
from storage.db_schema import FISH_RESOURCE_IDS
from systems.content_registry import LATEST_CHANGES, LATEST_CHANGES_TITLE
from world.equipment_help import HELP_TOPICS, HELP_TOPIC_ALIASES
from world.world_state import _FINAL_SKILL_HELP_EXACT_INDEX, _FINAL_SKILL_HELP_SEARCH_ROWS


class SessionHelpSystemMixin:

    async def show_lifetime_statistics(self):
            stats = self.server.db.lifetime_stats(self.account_id)
            # Pola, które mają już starsze trwałe źródło, są synchronizowane w górę
            # przy odczycie. Chroni to save'y po ręcznych migracjach i nie dubluje danych.
            deaths = max(stats.get("deaths", 0), int(self.character.deaths or 0))
            self.server.db.set_lifetime_stat_max(self.account_id, "deaths", deaths)
            explored = len(self.server.db.discovered_room_ids(self.account_id))
            self.server.db.set_lifetime_stat_max(self.account_id, "rooms_discovered", explored)
            bestiary_rows = self.server.db.bestiary_rows(self.account_id)
            unique_bestiary = len({str(row["mob_template_id"]) for row in bestiary_rows})
            self.server.db.set_lifetime_stat_max(self.account_id, "bestiary_unique", unique_bestiary)
            stats = self.server.db.lifetime_stats(self.account_id)

            await self.send(f"HISTORIA POSTACI: {self.character.name}.")
            await self.send(
                "Walka: zwycięstwa "
                f"{stats.get('combat_victories', 0)}, zabite moby {stats.get('kills_total', 0)}, "
                f"bossowie {stats.get('boss_kills', 0)}, rare moby {stats.get('rare_kills', 0)}, "
                f"śmierci {stats.get('deaths', 0)}."
            )
            await self.send(
                "Zadania: ukończone questy "
                f"{stats.get('quests_completed', 0)}, ukończone kontrakty {stats.get('bounties_completed', 0)}."
            )
            await self.send(
                "Profesje: akcje łącznie "
                f"{stats.get('profession_actions', 0)}, craftingi {stats.get('craft_actions', 0)}, "
                f"wytworzone przedmioty {stats.get('crafted_items', 0)}."
            )
            await self.send(
                "Zbiory od v0.9.4: ryby "
                f"{stats.get('fish_caught', 0)}, rudy i minerały {stats.get('ore_mined', 0)}, "
                f"drewno {stats.get('wood_gathered', 0)}, zioła {stats.get('herbs_gathered', 0)}, "
                f"klejnoty {stats.get('gems_found', 0)}."
            )
            await self.send(
                f"Świat: odkryte lokacje {stats.get('rooms_discovered', 0)} z {len(ALL_EXPLORATION_ROOMS)}, "
                f"Bestiariusz {stats.get('bestiary_unique', 0)} z {len(BESTIARY_CATALOG)}, "
                f"rzadkie ryby {stats.get('rare_fish_caught', 0)}."
            )
            await self.send(
                f"Wędkarstwo v0.9.5: odkryte gatunki {stats.get('fish_species_discovered', 0)} z {len(FISH_RESOURCE_IDS)}, "
                f"legendarne połowy {stats.get('legendary_fish_caught', 0)}, "
                f"nowe rekordy {stats.get('fish_record_updates', 0)}."
            )
            await self.send(
                "Starsze pewne dane zostały odtworzone z zapisów gry. Dokładne ilości sztuk "
                "ryb, rud, drewna, ziół i wytworzonych przedmiotów są liczone od v0.9.4."
            )

    async def show_where(self):
            room = ROOMS[self.character.room_id]
            await self.send(f"Jesteś tutaj: {room['name']}. Strefa: {room['zone']}.")

    def help_commands(self):
            lines = [
                "help / pomoc - kategorie pomocy; help [temat] / pomoc [temat] - wybrany temat; help tematy / topics - pełna lista",
                "changes / zmiany / changelog - pokaż najnowsze zmiany",
                "progress / postep - pełne podsumowanie: Level, Biegłość, Soul, profesje, reputacje, osiągnięcia, tytuły i eksploracja; progress region - bieżący region",
                "historia / history / lifetime - trwała Historia postaci: walki, questy, kontrakty, profesje, zbiory, eksploracja i Bestiariusz",
                "bufor / bufory [xp|loot|quest|system|chat|party|tell|walka|all] [1-100] - sesyjne bufory ostatnich komunikatów; działa też historia xp / historia loot / historia quest",
                "eksploracja / exploration [all] - procent odkrycia stref i świata",
                "osiagniecia / achievements - Bronze, Silver, Gold i Platinum",
                "tytuly / titles; tytul <nazwa> - lista i aktywny tytuł; Titles 2.0 dodaje tytuły za eksplorację, bossy, profesje, Kurierów i gildie; tytuły są prestiżowe i nie dają statystyk",
                "bounty / zlecenia / contracts - losowana Tablica Zleceń; kontrakty startują od 0/x i czytają postęp na żywo",
                "kolekcja / collection - Collection Codex; 2.0: kolekcja klasy, sety2, legendy, materialy eq, regiony, instancje",
                "rankingi / leaderboard - Top Krypty, Wieży, bossów, legend i kompletnych setów",
                "bosskodex / bosscodex [lista|nazwa] - kille, czas, solo/grupa, najwyższa wersja piętra i odkryte unikalne dropy",
                "historiadropow / drophistory - ostatnie wartościowe dropy",
                "loot rare+ / epic+ / legendary / all / off - filtr komunikatów lootu pod NVDA",
                "opis [nazwa] / describe [name] - szczegółowy opis elementu świata",
                "look lub l - opis aktualnej lokacji",
                "exits / ex - kierunki i nazwy lokacji, do których prowadzą; exits info dodaje strefę i poziom zagrożenia",
                "map / mapa - w świecie mapa regionu, w instancji mapa sektora 100 pięter z procentem, sekretami i checkpointami; mapa instancje - podsumowanie",
                "sekret / secret - zbadaj ukryty punkt na specjalnym piętrze instancji i zapisz go na mapie",
                "bestiariusz / bestiary - dziennik pokonanych mobów; bestiariusz <mob> - lokacje, dropy, odporności i rekord zabicia",
                "krypta / crypt - informacje o nieskończonej Krypcie, bossach co 10 pięter i checkpointach",
                "wieza / astral - informacje o nieskończonej Wieży Astralnej od piętra 100",
                "astralportal [poziom] - checkpointy Wieży Astralnej",
                "portal [piętro] - pokaż lub uruchom odblokowany Portal Krypty",
                "atlas [ryby|drewno|rudy|zioła|surowiec] - pełny atlas pozyskiwania surowców i klejnotów",
                "woda / łowisko - mówi typ bieżącego łowiska, np. rzeka, jezioro, morze, ocean, kanał lub Zatopiona Grota; pokazuje też znane i nieodkryte gatunki",
                "dziennikryb / fishjournal [lista|nazwa] - odkryte gatunki, rzadkość, liczba połowów oraz rekord długości i masy",
                "rekordyryb / fishrecords [gatunek] - Fishing Records 2.0: osobiste i serwerowe rekordy długości, masy oraz najrzadszy okaz",
                "projekty / worldprojects; projekt ... - wspólne długoterminowe odbudowy świata",
                "legendarnekontrakty / legendarycontracts - bardzo długie kontrakty z ogromnym Class XP, Soul XP i walutą",
                "geody / geodes - geody w Sakwie Górnika; open geode / otwórz geodę - otwórz jedną geodę",
                "unlock / odklucz / odblokuj - otwórz skrzynię bossową właściwym kluczem; poza skrzynią odblokuj kolejny Tier Broni Duszy",
                "where - aktualna lokacja",
                "teren info <nazwa> - Soul, NPC, questy, bossowie, profesje i dojście w regionie",
                "location / lokalizacja - lokacja, strefa i wyjścia",
                "north/south/east/west/up/down lub n/s/e/w/u/d - chodzenie; każdy krok najpierw rozpoczyna marsz, potem dopiero przenosi do sąsiedniej lokacji",
                "prowadz <cel> / walk <cel> - automatycznie prowadzi dokładnie do rozpoznanej lokalizacji lub NPC; działa też walk to <cel>",
                "walk krypta dół - będąc na piętrze zwykłej Krypty prowadzi przed zejście na następne piętro; samo zejście wykonujesz ręcznie",
                "/ - sam znak ukośnika i Enter natychmiast teleportuje do Świątyni Odrodzenia; w drużynie obejmuje tylko osoby stojące razem w tej samej lokacji",
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
                "multiclass / klasy - opcjonalne 1-3 aktywne klasy i Biegłość klas",
                "multiclass add klasa / remove klasa - dodaj lub wyłącz klasę dodatkową",
                "stats / staty - statystyki czytane osobno; staty info - baza, efektywne wartości, EQ i mechanika",
                "hp / zdrowie - szybkie bieżące i maksymalne HP oraz Mana",
                "score / wynik - podsumowanie postaci, klas, Biegłości, Duszy, statystyk, portfela i terenu",
                "odmiana / przypadki - pokaż 7 form imienia postaci",
                "skills / umiejetnosci - szczegółowa lista umiejętności aktywnych klas; skills all - nazwy skilli/spelli wszystkich 14 klas",
                "spells / spels / czary - czary aktywnych klas magicznych; spells all / spels all - czary wszystkich klas magicznych",
                "kodeksklasowy <klasa> / classcodex <class> - wszystkie skille, wymagana Biegłość, nauczyciel, koszt i status odblokowania",
                "skillnames / nazwyskilli - wszystkie nazwy skilli wszystkich klas",
                "skill / umiejetnosc / cast <nazwa lub numer> [cel] - użyj umiejętności",
                "help skill <nazwa> / help <nazwa skilla> / skill info <nazwa> - pełny help każdej umiejętności/spella w grze",
                "kolejka / kolejka lista - pokaż zapisane skille i czary; sloty są numerowane zwyczajnie jako Slot 1, Slot 2 itd. osobno dla fizycznych i magicznych; kolejka dodaj automatycznie włącza rotację",
                "użyj umiejętność <nazwa> [cel] / use skill <name> [target] - alternatywne użycie skilla",
                "learn / naucz / ucz <nazwa, numer lub naturalna kategoria> - np. naucz leczenie, tarcza, ciecie, pocisk, ogien",
                "soul / dusza - szybki stan Duszy; dusza info - Soul XP, Tiery, Próby i następny cel",
                "portfel / money / saldo - jedno wspólne saldo automatycznie pokazane jako mithril, złoto i srebro",
                "daj / przekaż <gracz> <przedmiot>; daj <gracz> <ilość> <przedmiot>; daj <gracz> <ilość> złota - przekazywanie graczowi w tej samej lokacji",
                "bank - Bank Dusz na Rynku; waluta i trwała skrytka przedmiotów",
                "portfel - pokazuje wspólną walutę wszystkich postaci na koncie oraz kurs nominałów",
                "professions / profesje - szybki stan profesji; profesje info - XP, rangi i zasady",
                "narzedzia / tools - szybki stan narzędzi; narzedzia info - XP, Tiery, bonusy i sprzedawcy",
                "professions / profesje - 12 profesji 1-600: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo, Jubilerstwo, Krawiectwo, Garbarstwo, Stolarstwo, Zaklinanie",
                "rangi / ranks - pełna lista rang profesji",
                "tools / narzedzia - skrót wszystkich 8 narzędzi",
                "wedka / kilof / pila / mlot / noz / sierp / mozdzierz / szczypce - pełne informacje o wybranym narzędziu",
                "tiers / tiery / nazwytierow - pełna lista Tierów wszystkich 8 narzędzi",
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
            "reforge / przekuj <pełna nazwa EQ> - u Haldora zmienia jeden affix EQ za Esencję Przekucia; próg Biegłości nie zmienia się",
            "runy - informacje, tworzenie i wyjmowanie run; runa <typ> <EQ> osadza runę w endgame EQ",
            "gildia - Gildia graczy: poziomy 1-600, Siedziba 1-10, budynki, kontrakty, bossowie, skarbiec, rangi, bank, trofea, osiągnięcia, log i czat",
            "znajomi - lista znajomych; dodaj/akceptuj/odrzuc/usun; szybkie zaproszenia party i gildia",
            "tell <gracz> <tekst>; reply <tekst> - prywatne wiadomości i szybka odpowiedź do ostatniego nadawcy",
            "osiagnieciaklasowe - osiągnięcia klas i profesji na progresji 1-600",
                "put fish net / wloz ryba siatka - przenieś ryby do Siatki",
                "put ore bag / wloz ruda sakwa - przenieś rudy do Sakwy",
                "take przedmiot net/bag / wyjmij przedmiot siatka/sakwa - wyjmij surowiec",
                "sell / sprzedaj - sell all / sprzedaj wszystko sprzedaje tylko niezałożone EQ; mikstury i zwykłe przedmioty są chronione. Surowce hurtowo: wszystko siatka/sakwa/stos/torba",
                "receptury / przepisy / recipes [craft|cook|alchemia|jubilerstwo] - lista receptur",
                "craft / stworz / wytworz receptura - rzemiosło z rud i drewna",
                "cook / gotuj receptura - przygotuj potrawę z ryb",
                "inventory / i - zwykły ekwipunek",
                "equipment / eq - szybkie EQ zawsze pokazuje też Broń Duszy; eq info - Soul XP, pełne bonusy, sockety i aktywne sety",
                "sety / sety info / sety <klasa> - zestawy klasowe 2/4/6/8 dla 14 klas",
                "help loot_krypty - rarity, losowe statystyki i sety Krypty",
                "equip / załóż przedmiot albo slot - m.in. hełm, zbroja, rękawice, nogi, buty, naramienniki, pas, peleryna, karwasze, kolczyki, relikt, pierścienie, talizmany, naszyjnik",
                "Biżuteria v0.30.21: załóż <nazwa pierścienia/talizmanu> wybiera wolny slot automatycznie, a gdy oba są zajęte zastępuje słabszy; ręczne sloty 1/2 nadal działają.",
                "Skróty EQ: zh hełm, zz zbroja, zr rękawice, zn nogi, zb buty, zp pierścienie auto, zt talizmany auto, zp1/zp2 i zt1/zt2 ręcznie, zna naszyjnik, zkol kolczyki auto, zkol1/zkol2 ręcznie, znar naramienniki, zpas pas, zpel peleryna, zkar karwasze, zrel relikt.",
                "use / użyj - przedmioty, skille i czary; np. użyj ciecie goblin albo użyj pocisk goblin",
                "shop / sklep / list / lista - krótka numerowana oferta: numer, nazwa i cena",
                "shop info <numer> / sklep info <numer> - pełny opis i porównanie EQ przed zakupem",
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

    def full_changelog_lines(self):
            module_dir = os.path.dirname(os.path.abspath(__file__))
            candidates = (
                os.path.join(module_dir, "CHANGELOG_PL.txt"),
                os.path.join(os.getcwd(), "CHANGELOG_PL.txt"),
            )

            for changelog_path in candidates:
                try:
                    if not os.path.exists(changelog_path):
                        continue
                    with open(changelog_path, "r", encoding="utf-8") as handle:
                        lines = [line.rstrip("\r\n") for line in handle]
                    if any(line.strip() for line in lines):
                        return lines
                except (OSError, UnicodeError):
                    continue

            lines = [LATEST_CHANGES_TITLE]
            lines.extend("- " + line for line in LATEST_CHANGES)
            return lines

    async def show_latest_changes(self):
            await self.send("PEŁNA HISTORIA ZMIAN SOULBOUND")
            await self.send(
                "Najnowsze wersje są na górze. Poniżej znajduje się "
                "cały dostępny CHANGELOG_PL.txt."
            )
            for line in self.full_changelog_lines():
                if line.strip():
                    await self.send(line)

    def all_skill_help_entries(self):
            entries = []
            for class_name, skills in CLASS_SKILLS.items():
                for skill in skills:
                    entries.append((class_name, skill))
            return entries

    def skill_help_query_text(self, query):
            normalized = normalize_lookup_text(query)
            prefixes = (
                "skill ", "spell ", "czar ", "umiejetnosc ", "zdolnosc ",
                "info ", "opis ", "help ", "pomoc ",
            )
            changed = True
            while normalized and changed:
                changed = False
                for prefix in prefixes:
                    if normalized.startswith(prefix):
                        normalized = normalized[len(prefix):].strip()
                        changed = True
                        break
            return normalized

    def find_global_skill_help_matches(self, query):
            wanted = self.skill_help_query_text(query)
            if not wanted:
                return []

            # Najczęstszy przypadek (pełna nazwa, ID lub alias) jest O(1).
            exact = _FINAL_SKILL_HELP_EXACT_INDEX.get(wanted, ())
            if exact:
                unique = {}
                for class_name, skill in exact:
                    unique[skill["id"]] = (class_name, skill)
                return list(unique.values())

            # Fragmenty nazw są celowo dopuszczone, ale nigdy nie zgadujemy przy
            # wielu trafieniach. Skan wykonuje się tylko dla niepełnego zapytania.
            unique = {}
            for class_name, skill, normalized_names in _FINAL_SKILL_HELP_SEARCH_ROWS:
                if any(wanted in value for value in normalized_names):
                    unique[skill["id"]] = (class_name, skill)
            return list(unique.values())

    def skill_help_kind_label(self, kind):
            return {
                "damage": "obrażenia pojedynczego celu",
                "aoe_damage": "obrażenia obszarowe",
                "execute": "finisher / egzekucja",
                "drain": "obrażenia i wysysanie życia",
                "boost": "buff / wzmocnienie",
                "guard": "obrona / guard",
                "evade": "unik",
                "heal": "leczenie",
                "group_heal": "leczenie drużynowe",
                "utility": "narzędzie użytkowe / trwałe ulepszenie",
            }.get(kind, str(kind or "nieznany"))

    def skill_help_scale_label(self, scale):
            return {
                "strength": "Siła",
                "dexterity": "Zręczność",
                "intelligence": "Inteligencja",
            }.get(scale, "brak bezpośredniego skalowania statystyką")

    def skill_help_effect_details(self, skill):
            parts = []
            kind = skill.get("kind")
            if skill.get("scale"):
                parts.append("Skalowanie: " + self.skill_help_scale_label(skill.get("scale")))
            if "mult" in skill:
                parts.append(f"Mnożnik mocy: x{float(skill['mult']):.2f}")
            if kind == "execute" and "execute_mult" in skill:
                parts.append(f"Mnożnik egzekucji: x{float(skill['execute_mult']):.2f}")
            if kind == "boost" and "boost" in skill:
                pct = int(round((float(skill.get("boost", 1.0)) - 1.0) * 100))
                duration = skill.get("duration")
                if duration:
                    parts.append(f"Bazowe wzmocnienie: +{pct} procent przez {int(duration)} sekund")
                else:
                    parts.append(f"Bazowe wzmocnienie: +{pct} procent; czas działania odpowiada efektywnemu cooldownowi")
            if kind == "guard" and "guard" in skill:
                parts.append(f"Bazowa redukcja następnego trafienia: {int(skill['guard'])}")
            if kind in ("heal", "group_heal") and "heal_pct" in skill:
                parts.append(f"Bazowe leczenie: {int(round(float(skill['heal_pct']) * 100))} procent maksymalnego HP")
            if kind == "drain" and "drain_pct" in skill:
                parts.append(f"Wysysanie życia: {int(round(float(skill['drain_pct']) * 100))} procent zadanych obrażeń")
            if skill.get("self_damage"):
                parts.append(f"Koszt własnego HP: {int(skill['self_damage'])}")
            if skill.get("self_damage_pct"):
                parts.append(f"Koszt własnego HP: {int(round(float(skill['self_damage_pct']) * 100))} procent")
            return parts

    async def show_skill_help(self, query):
            wanted = self.skill_help_query_text(query)
            if not wanted:
                await self.send(
                    "Użycie: help skill <nazwa>, help <nazwa skilla> albo skill info <nazwa>. "
                    "Wpisz skillnames, aby usłyszeć wszystkie nazwy."
                )
                return True

            matches = self.find_global_skill_help_matches(wanted)
            if not matches:
                return False
            if len(matches) > 1:
                await self.send(
                    "Nazwa jest niejednoznaczna. Pasujące umiejętności: "
                    + "; ".join(
                        f"{skill['name']} ({class_name}, ID: {skill['id']})"
                        for class_name, skill in matches[:20]
                    )
                    + ". Użyj help skill <ID>, aby wybrać dokładnie właściwą umiejętność."
                )
                return True

            class_name, skill = matches[0]
            kind = skill.get("kind")
            queue_type = self.skill_queue_type(skill)
            mastery_needed = self.skill_required_mastery(skill)
            mastery_current = self.class_mastery_level(class_name)
            learned = self.server.db.knows_skill(self.account_id, skill["id"])
            active = class_name in self.active_class_names()
            mana = int(skill.get("mana", 0) or 0)
            base_cd = int(skill.get("cooldown", 0) or 0)

            await self.send(f"HELP SKILL: {skill['name']}.")
            await self.send(
                f"Klasa: {class_name}. Typ: {self.skill_help_kind_label(kind)}. "
                f"Wymagana Biegłość klasy: {mastery_needed}. "
                f"Kolejka: {self.skill_queue_type_label(queue_type)}."
            )
            await self.send(
                f"Mana: {mana}. Bazowy cooldown: {base_cd} sekund. "
                f"Opis: {skill.get('desc', 'Brak opisu.')}"
            )
            effect_parts = self.skill_help_effect_details(skill)
            if effect_parts:
                await self.send("Mechanika: " + ". ".join(effect_parts) + ".")

            teacher_id, teacher = self.class_teacher(class_name)
            if teacher:
                room_name = ROOMS.get(teacher.get("room"), {}).get("name", "nieznana lokacja")
                base_cost, final_cost, discount = self.class_codex_training_cost(class_name, skill)
                cost_text = self.training_cost_text(final_cost)
                await self.send(
                    f"Nauczyciel: {teacher['name']}, {room_name}. "
                    f"Aktualny koszt nauki: {cost_text}."
                )

            if learned:
                progress = self.skill_progress_data(skill)
                level = max(1, int(progress.get("level", 1)))
                effective_cd = self.effective_skill_cooldown(skill, level)
                if level >= SKILL_MAX_LEVEL:
                    progress_text = f"Skill Poziom {level}, maksymalny"
                else:
                    progress_text = (
                        f"Skill Poziom {level}, XP {progress.get('xp', 0)} z "
                        f"{skill_xp_to_next(level)}, użycia {progress.get('uses', 0)}"
                    )
                await self.send(
                    f"Status: nauczona. {progress_text}. "
                    f"Aktualny cooldown przy tym Skill Level: {effective_cd} sekund."
                )
            elif not active:
                await self.send(
                    f"Status: klasa {class_name} nie jest aktywna. Twoja Biegłość tej klasy: {mastery_current}."
                )
            elif mastery_current < mastery_needed:
                await self.send(
                    f"Status: jeszcze zablokowana. Biegłość {class_name}: {mastery_current} z wymaganych {mastery_needed}."
                )
            else:
                await self.send(
                    f"Status: odblokowana do nauki. Biegłość {class_name}: {mastery_current}."
                )

            await self.send(
                f"Komendy: skill {skill['name']} [cel]; kolejka dodaj {skill['name']}."
            )
            return True

    async def show_help(self, topic=""):
            raw = topic.strip().lower()
            key = HELP_TOPIC_ALIASES.get(raw, raw)

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
            elif key not in HELP_TOPICS and key not in ("tematy", "komendy", "wszystko"):
                if await self.show_skill_help(raw):
                    return

            if not key or key == "kategorie":
                await self.send("POMOC — KATEGORIE")
                await self.send("START: help podstawy, help informacje, help komendy, help nawigacja.")
                await self.send("POSTAĆ: help statystyki, help hp, help score, help dusza, help ekwipunek, help klasy, help rasy, help multiclass.")
                await self.send("WALKA: help walka, help wimpy, help bossowie, help krytyki, help umiejetnosci, help druzyny, help skrzynie_bossow.")
                await self.send("ŚWIAT: help questy, help nawigacja, help event_exp, help eksploracja, help bestiariusz, help teren_info, help atlas, help krypta, help portale, help zwloki, help pojemniki, help sklepy.")
                await self.send("PROFESJE: help profesje, help wedkarstwo, help gornictwo, help geody, help drwalstwo, help zielarstwo, help alchemia, help rzemioslo, help gotowanie, help jubilerstwo2, help krawiectwo/tailoring, help garbarstwo/leatherworking, help stolarstwo/carpentry, help zaklinanie/enchanting, help craftmastery.")
                await self.send("SPOŁECZNE: help gracze, help druzyny, help przekazywanie, help social2, help mentor2, help housing2, help leaderboards2, help bufory, help pieniadze, help charyzma.")
                await self.send("SYSTEM: help logowanie, help smierc, help recaps, help loothistory2, help accessibility_presets, help audyt_v03055, help opisy, help zmiany.")
                if self.is_admin():
                    await self.send("ADMINISTRATOR: help admin.")
                await self.send("help tematy / help topics — pełna lista tematów.")
                await self.send("help wszystko / help all — pełny przewodnik.")
                await self.send("help <temat> albo pomoc <temat> — otwiera wybraną pomoc.")
                await self.send("help skill <nazwa> — pełna pomoc konkretnego skilla lub spella.")
                await self.send("Samo help albo pomoc zawsze wraca do tego indeksu kategorii.")
                return

            if key == "tematy":
                await self.send("TEMATY POMOCY")
                for name in HELP_TOPICS:
                    if name == "admin_owner" and not self.is_admin():
                        continue
                    await self.send(name)
                await self.send("Dodatkowo: komendy, wszystko.")
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
                await self.send("Nie znam takiego tematu pomocy. Wpisz help tematy albo help komendy.")
                return

            await self.send("POMOC: " + key.upper())
            for line in lines:
                await self.send(line)
