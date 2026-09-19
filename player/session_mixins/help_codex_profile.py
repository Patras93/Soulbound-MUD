# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: help_codex_profile."""

class SessionHelpCodexProfileMixin:
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
                "progress / postep - ogólny postęp; progress region - bieżący region",
                "historia / history / lifetime - trwała Historia postaci: walki, questy, kontrakty, profesje, zbiory, eksploracja i Bestiariusz",
                "bufor / bufory [xp|loot|quest|system|chat|party|tell|walka|all] [1-100] - sesyjne bufory ostatnich komunikatów; działa też historia xp / historia loot / historia quest",
                "eksploracja / exploration [all] - procent odkrycia stref i świata",
                "osiagniecia / achievements - Bronze, Silver, Gold i Platinum",
                "tytuly / titles; tytul <nazwa> - lista i aktywny tytuł; tytuły są prestiżowe i nie dają statystyk",
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
                "/ - sam znak ukośnika i Enter natychmiast teleportuje do Świątyni Odrodzenia",
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
                "professions / profesje - 8 profesji 1-400: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo, Jubilerstwo",
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
            "salvage / rozłóż <pełna nazwa EQ> - u Haldora rozkłada niezałożone EQ na materiały do Szkatułki i daje Kowalstwo XP; nie nabija użyć Młota Rzemieślniczego",
            "reforge / przekuj <pełna nazwa EQ> - u Haldora zmienia jeden affix EQ za Esencję Przekucia; próg Biegłości nie zmienia się",
            "runy - informacje, tworzenie i wyjmowanie run; runa <typ> <EQ> osadza runę w endgame EQ",
            "gildia - Gildia graczy: poziomy 1-100, Siedziba 1-10, budynki, kontrakty, bossowie, skarbiec, rangi, bank, trofea, osiągnięcia, log i czat",
            "znajomi - lista znajomych; dodaj/akceptuj/odrzuc/usun; szybkie zaproszenia party i gildia",
            "tell <gracz> <tekst>; reply <tekst> - prywatne wiadomości i szybka odpowiedź do ostatniego nadawcy",
            "osiagnieciaklasowe - osiągnięcia klas i profesji na progresji 1-400",
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
                    progress_text = f"Skill Level {level}, maksymalny"
                else:
                    progress_text = (
                        f"Skill Level {level}, XP {progress.get('xp', 0)} z "
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

    def format_item_description(self, item_id, item):
            parts = [f"{item['name']}. Typ: {item.get('type', 'przedmiot')}.", item.get("desc", "")]

            if item.get("type") == "armor":
                parts.append(
                    f"Slot: {EQUIPMENT_SLOT_NAMES.get(item.get('slot'), item.get('slot', 'brak'))}. "
                    f"Obrona fizyczna: +{item.get('defense', 0)}."
                )
                capacity = jewelry_socket_capacity(item)
                if capacity > 0:
                    parts.append(
                        f"Gniazda na klejnoty: {capacity}."
                    )
                if item.get("rarity_name"):
                    parts.append(
                        f"Rzadkość: {item['rarity_name']}."
                    )
                if item.get("required_class"):
                    req_level = max(1, int(item.get("required_character_level", item.get("required_mastery", 1)) or 1))
                    parts.append(
                        f"Wymagana aktywna klasa: {item['required_class']}. "
                        f"Wymagany Level postaci: {req_level}."
                    )
                elif int(item.get("required_character_level", item.get("required_mastery", 1)) or 1) > 1:
                    parts.append(
                        f"Wymagany Level postaci: {int(item.get('required_character_level', item.get('required_mastery', 1)) or 1)}."
                    )
                if item.get("class_shop_item") and item.get("required_class"):
                    class_name = item["required_class"]
                    parts.append(
                        f"Część zestawu klasowego {class_name}: "
                        f"Zestaw {item.get('class_set_name', class_name)}. "
                        "Progi zestawu: 2, 4, 6 i 8 części."
                    )
                if item.get("affix"):
                    affix_name = CRYPT_AFFIXES.get(
                        item["affix"], item["affix"]
                    )
                    parts.append(
                        f"Losowy bonus: {affix_name} "
                        f"+{item.get('affix_amount', 0)}."
                    )
                if item.get("stats"):
                    stats_text = ", ".join(
                        f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                        for stat, amount in item["stats"].items()
                    )
                    parts.append(f"Statystyki materiałowe: {stats_text}.")
                    if int(item["stats"].get("dexterity", 0)) > 0:
                        parts.append(
                            "Zręczność zwiększa szansę na trafienie krytyczne: "
                            "10 daje 5 procent, 40 daje 20 procent, 80 daje 30 procent, "
                            "a dalszy przyrost maleje do limitu 35 procent."
                        )
                if item.get("properties"):
                    properties_text = ", ".join(
                        f"{MATERIAL_PROPERTY_NAMES.get(prop, prop)} +{amount:g}%"
                        for prop, amount in item["properties"].items()
                    )
                    parts.append(f"Właściwości materiałowe: {properties_text}.")
                if item.get("corpse_material"):
                    parts.append(
                        f"Materiał łupu: {item.get('corpse_material')}."
                    )
                if item.get("crypt_set_tier"):
                    parts.append(
                        f"Zestaw Krypty Tier "
                        f"{item['crypt_set_tier']}."
                    )
            elif item.get("type") == "tool":
                tool = "Wędka" if item.get("tool_type") == "fishing" else "Kilof"
                parts.append(f"Narzędzie profesji: {tool}. Ma własny level 1-400 i osobny XP.")
            elif "heal" in item:
                parts.append(f"Leczenie: {item['heal']} HP.")
            elif "soul_xp" in item:
                parts.append(f"Po użyciu daje {item['soul_xp']} Soul XP.")

            if item.get("price") is not None:
                price_coins = self.shop_item_base_value_silver(item)
                parts.append("Cena kupna: " + currency_reading_text(price_coins, 0, 0) + ".")

            if item.get("sell_silver") or item.get("sell_gold") or item.get("sell_mithril"):
                parts.append(
                    "Wartość sprzedaży: "
                    + currency_reading_text(
                        item.get("sell_silver", 0),
                        item.get("sell_gold", 0),
                        item.get("sell_mithril", 0),
                    )
                    + "."
                )

            return " ".join(p for p in parts if p)

    def room_special_features(self, room_id):
            features = []
            if room_id in RIVER_FISHING_ROOMS:
                features.append("łowisko rzeczne")
            if room_id in LAKE_FISHING_ROOMS:
                features.append("łowisko jeziorowe")
            if room_id in SEA_FISHING_ROOMS:
                features.append("łowisko morskie")
            if room_id in OCEAN_FISHING_ROOMS:
                features.append("łowisko oceaniczne")
            if is_mining_room(room_id):
                features.append("miejsce wydobycia")
                floor = mine_floor_number(room_id)
                if floor is not None:
                    features.append(
                        f"Kopalnia Głębinowa poziom {floor}, bez górnego limitu"
                    )
            if room_id in SHOPS:
                features.append("sklep")
            if v0160_npcs_in_room(room_id):
                features.append("NPC")
            if any(spawn_room == room_id for spawn_room, _ in MOB_SPAWNS):
                features.append("przeciwnicy")
            return features

    def normalize_description_query(self, value):
            table = str.maketrans(
                "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
                "acelnoszzACELNOSZZ"
            )
            return value.strip().lower().translate(table)

    def find_description_entry(self, mapping, query, name_field="name"):
            q = self.normalize_description_query(query)
            if not q:
                return None
            exact = []
            partial = []
            for key, value in mapping.items():
                name = value[name_field] if isinstance(value, dict) else str(value)
                nk = self.normalize_description_query(str(key))
                nn = self.normalize_description_query(name)
                if q == nk or q == nn:
                    exact.append((key, value))
                elif q in nk or q in nn:
                    partial.append((key, value))
            if exact:
                return exact[0]
            if len(partial) == 1:
                return partial[0]
            return None

    def atlas_fish_min_level(self, item_id, habitat):
            """Najniższy level Wędki, przy którym gatunek realnie trafia do puli."""
            item = ITEMS.get(item_id, {})
            base_id = item.get("base_resource_id", item_id)
            for level in range(1, TOOL_MAX_LEVEL + 1):
                if base_id in self.fishing_available_pool(level, habitat):
                    return level
            return None

    def atlas_resource_requirement_rows(self, item_id):
            """Zwraca (miejsce, narzędzie, minimalny level) dla zasobu."""
            item = ITEMS.get(item_id, {})
            base_id = item.get("base_resource_id", item_id)
            rows = []

            # Specjalne miejsca są treścią świata; wymagany level zawsze pochodzi
            # z Generator Core przedmiotu, nigdy z osobnej tabeli liczb.
            field_places = {
                "field_grave_moss": ("Ogród Księżycowego Mchu, Stary Cmentarz", "Sierp"),
                "field_void_thorn": ("Ogród Cierni Pustki, Ruiny Kultystów", "Sierp"),
                "field_ironbark_root": ("Legowisko Bestii", "Piła"),
                "field_tomb_silver": ("Kopalnia Głębinowa", "Kilof"),
                "field_blind_sewer_eel": ("Czarny Kanał pod Miastem Dusz", "Wędka"),
                "field_frost_crystal_ore": ("Kopalnia Głębinowa", "Kilof"),
            }
            if base_id in field_places:
                place, tool = field_places[base_id]
                generated = int(ITEMS.get(base_id, {}).get("generator_level", 1) or 1)
                return [(place, tool, generated)]


            fish_groups = (
                ("river", "Rzeka", ("riverbank", "stone_bridge"), RIVER_FISH_ATLAS),
                ("lake", "Jezioro", ("lake_shore",), LAKE_FISH_ATLAS),
                ("sea", "Morze", ("sea_pier",), SEA_FISH_ATLAS),
                ("ocean", "Ocean", ("ocean_platform",), OCEAN_FISH_ATLAS),
            )
            if base_id in FISH_RESOURCE_IDS:
                for habitat, label, rooms, ids in fish_groups:
                    if base_id not in ids:
                        continue
                    level = self.atlas_fish_min_level(base_id, habitat)
                    if level is None:
                        continue
                    places = ", ".join(
                        ROOMS[room_id]["name"] for room_id in rooms if room_id in ROOMS
                    )
                    if places:
                        rows.append((f"{label}: {places}", "Wędka", int(level)))
                    # Profesyjny loch Wędkarstwa ma ograniczenie efektywnego levelu
                    # do 10 punktów na każdą głębokość.
                    if habitat == "sea":
                        grotto_floor = max(1, (int(level) + 9) // 10)
                        if grotto_floor <= 10:
                            rows.append((
                                f"Zatopiona Grota od głębokości {grotto_floor}",
                                "Wędka", int(level)
                            ))
                    elif habitat == "ocean":
                        grotto_floor = max(11, (int(level) + 9) // 10)
                        if grotto_floor <= 20:
                            rows.append((
                                f"Zatopiona Grota od głębokości {grotto_floor}",
                                "Wędka", int(level)
                            ))
                return rows

            if base_id in WOOD_RESOURCE_IDS:
                for room_id, level_map in WOOD_ATLAS_ROOM_MIN_LEVELS.items():
                    level = level_map.get(base_id)
                    if level is not None and room_id in ROOMS:
                        rows.append((ROOMS[room_id]["name"], "Piła", int(level)))
                deep_level = WOOD_ATLAS_ROOM_MIN_LEVELS.get("deep_grove", {}).get(base_id)
                if deep_level is not None:
                    forest_floor = max(1, (int(deep_level) + 9) // 10)
                    rows.append((
                        f"Pradawny Las od ostępu {forest_floor}",
                        "Piła", int(deep_level)
                    ))
                return sorted(rows, key=lambda row: (row[2], self.normalize_description_query(row[0])))

            if base_id in HERB_RESOURCE_IDS:
                for room_id, level_map in HERB_ATLAS_ROOM_MIN_LEVELS.items():
                    level = level_map.get(base_id)
                    if level is not None and room_id in ROOMS:
                        rows.append((ROOMS[room_id]["name"], "Sierp", int(level)))
                deep_level = HERB_ATLAS_ROOM_MIN_LEVELS.get("deep_grove", {}).get(base_id)
                if deep_level is not None:
                    garden_floor = max(1, (int(deep_level) + 9) // 10)
                    rows.append((
                        f"Ogród Alchemika od sektora {garden_floor}",
                        "Sierp", int(deep_level)
                    ))
                return sorted(rows, key=lambda row: (row[2], self.normalize_description_query(row[0])))

            if base_id in ORE_RESOURCE_IDS:
                level = int(ORE_ATLAS_LEVELS.get(base_id, 1))
                floor_min = int(ORE_MINE_FLOOR_MINIMUMS.get(base_id, 1))
                rows.append((f"Kopalnia Głębinowa od poziomu {floor_min}", "Kilof", level))
                return rows

            return rows

    def atlas_item_locations(self, item_id):
            result = []
            seen = set()
            for place, _tool, _level in self.atlas_resource_requirement_rows(item_id):
                if place not in seen:
                    seen.add(place)
                    result.append(place)
            return result

    def atlas_resource_min_level(self, item_id):
            rows = self.atlas_resource_requirement_rows(item_id)
            if not rows:
                return None, None
            tool = rows[0][1]
            level = min(row[2] for row in rows)
            return tool, level

    def atlas_group_level(self, item_id, kind, key):
            item = ITEMS.get(item_id, {})
            base_id = item.get("base_resource_id", item_id)
            if kind == "fish":
                return self.atlas_fish_min_level(base_id, key)
            if kind == "wood":
                rooms = {
                    "beginner": ("lumberjack_camp", "meadow"),
                    "forest": ("whisper_grove", "old_road"),
                    "deep": ("deep_grove",),
                }.get(key, ())
                levels = [
                    WOOD_ATLAS_ROOM_MIN_LEVELS.get(room_id, {}).get(base_id)
                    for room_id in rooms
                ]
            elif kind == "herb":
                rooms = {
                    "meadow": ("herbalist_hut", "meadow", "flower_meadow"),
                    "water": ("riverbank", "lake_shore", "lakeside_meadow"),
                    "forest": ("whisper_grove", "old_road"),
                    "deep": ("deep_grove",),
                }.get(key, ())
                levels = [
                    HERB_ATLAS_ROOM_MIN_LEVELS.get(room_id, {}).get(base_id)
                    for room_id in rooms
                ]
                # Tematyczne łąki należą do sekcji łąk; nie obniżają
                # wymagań tego samego zioła w lesie, nad wodą ani w Głębi Gaju.
                if key == "meadow":
                    for room_id, herb_id in HERB_SPECIFIC_MEADOWS.items():
                        if herb_id == base_id:
                            levels.append(1)
            else:
                return None
            levels = [int(value) for value in levels if value is not None]
            return min(levels) if levels else None

    async def send_atlas_group_with_levels(
            self, title, location_text, item_ids, kind, key, tool_name, chunk_size=12
        ):
            entries = []
            for item_id in sorted(
                item_ids,
                key=lambda value: self.normalize_description_query(ITEMS[value]["name"]),
            ):
                level = self.atlas_group_level(item_id, kind, key)
                if level is None:
                    entries.append(ITEMS[item_id]["name"])
                else:
                    entries.append(f"{ITEMS[item_id]['name']} [{tool_name} {level}+]")
            await self.send(f"{title}. Miejsce: {location_text}. Gatunków/surowców: {len(entries)}.")
            if not entries:
                await self.send("Brak pozycji.")
                return
            chunk_size = max(1, int(chunk_size))
            total = (len(entries) + chunk_size - 1) // chunk_size
            for index in range(0, len(entries), chunk_size):
                part = index // chunk_size + 1
                await self.send(
                    f"{title}, część {part} z {total}: "
                    + ", ".join(entries[index:index + chunk_size])
                    + "."
                )

    def atlas_names(self, item_ids):
            return ", ".join(
                sorted(
                    (ITEMS[item_id]["name"] for item_id in item_ids),
                    key=str.lower,
                )
            )

    async def send_complete_atlas_list(
            self, title, item_ids, chunk_size=20
        ):
            names = sorted(
                (ITEMS[item_id]["name"] for item_id in item_ids),
                key=self.normalize_description_query,
            )
            await self.send(
                f"{title}. Łącznie pozycji: {len(names)}."
            )
            if not names:
                await self.send("Brak pozycji.")
                return

            chunk_size = max(1, int(chunk_size))
            total_parts = (
                len(names) + chunk_size - 1
            ) // chunk_size

            for index in range(0, len(names), chunk_size):
                part = index // chunk_size + 1
                chunk = names[index:index + chunk_size]
                await self.send(
                    f"Część {part} z {total_parts}: "
                    + ", ".join(chunk)
                    + "."
                )

    async def show_atlas(self, query=""):
            q = self.normalize_description_query(query)

            if not q:
                await self.send("ATLAS SUROWCÓW")
                await self.send("Działy: ryby, drewno, rudy, geody, zioła.")
                await self.send(
                    "Atlas pokazuje teraz wymagany level profesji i prawdziwe miejsce występowania. "
                    "Użycie: atlas ryby, atlas rzeka, atlas drewno, atlas rudy, atlas geody, atlas zioła "
                    "albo atlas <nazwa surowca>."
                )
                return

            if q in ("ryby", "fish", "wedkarstwo"):
                await self.send(f"ATLAS RYB. Łącznie gatunków: {len(FISH_ATLAS_ALL)}.")
                groups = (
                    ("river", "RZEKA", ("riverbank", "stone_bridge"), RIVER_FISH_ATLAS),
                    ("lake", "JEZIORO", ("lake_shore",), LAKE_FISH_ATLAS),
                    ("sea", "MORZE", ("sea_pier",), SEA_FISH_ATLAS),
                    ("ocean", "OCEAN", ("ocean_platform",), OCEAN_FISH_ATLAS),
                )
                for habitat, title, rooms, items in groups:
                    places = ", ".join(ROOMS[r]["name"] for r in sorted(rooms))
                    await self.send_atlas_group_with_levels(
                        title, places, items, "fish", habitat, "Wędka", chunk_size=12
                    )
                if "field_blind_sewer_eel" in ITEMS:
                    await self.send("TERENOWA RYBA: Ślepy Węgorz Kanałowy [Wędka 30+; Czarny Kanał pod Miastem Dusz].")
                await self.send(
                    "Zatopiona Grota także zawiera ryby morskie i oceaniczne; dokładna minimalna głębokość jest podawana przy atlas <nazwa ryby>."
                )
                await self.send(
                    "Wpisz atlas <nazwa ryby>, aby usłyszeć dokładny minimalny level Wędki i wszystkie łowiska."
                )
                return

            fish_groups = {
                "rzeka": ("river", "RZEKA", ("riverbank", "stone_bridge"), RIVER_FISH_ATLAS),
                "river": ("river", "RZEKA", ("riverbank", "stone_bridge"), RIVER_FISH_ATLAS),
                "jezioro": ("lake", "JEZIORO", ("lake_shore",), LAKE_FISH_ATLAS),
                "lake": ("lake", "JEZIORO", ("lake_shore",), LAKE_FISH_ATLAS),
                "morze": ("sea", "MORZE", ("sea_pier",), SEA_FISH_ATLAS),
                "sea": ("sea", "MORZE", ("sea_pier",), SEA_FISH_ATLAS),
                "ocean": ("ocean", "OCEAN", ("ocean_platform",), OCEAN_FISH_ATLAS),
            }
            if q in fish_groups:
                habitat, title, rooms, items = fish_groups[q]
                places = ", ".join(ROOMS[r]["name"] for r in sorted(rooms))
                await self.send_atlas_group_with_levels(
                    title, places, items, "fish", habitat, "Wędka", chunk_size=12
                )
                return

            if q in ("drewno", "wood", "drwalstwo"):
                await self.send(f"ATLAS DREWNA. Łącznie rodzajów: {len(WOOD_ATLAS_ALL)}.")
                wood_groups = (
                    ("beginner", "OBÓZ DRWALA I SREBRNA ŁĄKA", ("lumberjack_camp", "meadow"), WOOD_BEGINNER_ATLAS),
                    ("forest", "GAJ SZEPTÓW I STARY TRAKT", ("whisper_grove", "old_road"), WOOD_FOREST_ATLAS),
                    ("deep", "GŁĘBIA GAJU", ("deep_grove",), WOOD_DEEP_ATLAS),
                )
                for key, title, rooms, items in wood_groups:
                    places = ", ".join(ROOMS[r]["name"] for r in rooms)
                    await self.send_atlas_group_with_levels(
                        title, places, items, "wood", key, "Piła", chunk_size=12
                    )
                if "field_ironbark_root" in ITEMS:
                    await self.send("TERENOWE DREWNO: Korzeń Żelaznokory [Piła 50+; Legowisko Bestii].")
                await self.send(
                    "Pradawny Las również korzysta z puli Głębi Gaju; wymagany ostęp zależy od levelu danego drewna."
                )
                await self.send(
                    "Wpisz atlas <nazwa drewna>, aby usłyszeć level Piły wymagany osobno w każdej lokacji."
                )
                return

            if q in ("rudy", "ruda", "ore", "gornictwo"):
                await self.send(f"ATLAS RUD. Łącznie rud i minerałów: {len(ORE_ATLAS_ALL)}.")
                entries = []
                for item_id in sorted(
                    ORE_ATLAS_ALL,
                    key=lambda value: (
                        ORE_ATLAS_LEVELS.get(value, 1),
                        self.normalize_description_query(ITEMS[value]["name"]),
                    ),
                ):
                    level = ORE_ATLAS_LEVELS.get(item_id, 1)
                    floor_min = ORE_MINE_FLOOR_MINIMUMS.get(item_id, 1)
                    where = f"Kopalnia Głębinowa {floor_min}+"
                    entries.append(
                        f"{ITEMS[item_id]['name']} [Kilof {level}+; {where}]"
                    )
                chunk_size = 8
                total = (len(entries) + chunk_size - 1) // chunk_size
                for index in range(0, len(entries), chunk_size):
                    part = index // chunk_size + 1
                    await self.send(
                        f"RUDY, część {part} z {total}: "
                        + "; ".join(entries[index:index + chunk_size])
                        + "."
                    )
                if "field_tomb_silver" in ITEMS:
                    await self.send("RUDY SPECJALNE W TEJ SAMEJ KOPALNI: Srebro Grobowe [Kilof 80+; poziom 80+]; Ruda Lodowego Kryształu [Kilof 100+; poziom 100+].")
                gem_rows = []
                for definition in GEM_DEFINITIONS:
                    raw_id = f"raw_gem_{definition['key']}"
                    if raw_id in ITEMS:
                        gem_rows.append(
                            f"{ITEMS[raw_id]['name']} [Kilof {definition['mining_level']}+; głębokość {definition['min_floor']}+]"
                        )
                if gem_rows:
                    await self.send("KLEJNOTY Z GÓRNICTWA: " + "; ".join(gem_rows) + ".")
                    await self.send(
                        "Jakość klejnotu może być Surowa, Czysta, Doskonała lub Perfekcyjna. "
                        "Lepszy Kilof i wyższe Górnictwo zwiększają szansę wyższej jakości."
                    )
                await self.send(
                    "Geody: Kamienna [Kilof 20+, głębokość 10+], Kryształowa [80+/60+], "
                    "Astralna [160+/150+]. Wpisz atlas geody."
                )
                await self.send(
                    "Czysty mithril nie jest rudą w Sakwie. To rzadka waluta możliwa "
                    "od efektywnej głębokości i levelu Kilofa 80."
                )
                return

            if q in ("geody", "geoda", "geode", "geodes"):
                await self.send("ATLAS GEOD.")
                for geode_id, cfg in GEODE_DEFINITIONS.items():
                    await self.send(
                        f"{cfg['name']} [Kilof {cfg['min_tool']}+; głębokość {cfg['min_floor']}+]. "
                        f"Może zawierać klejnoty do poziomu {cfg['max_gem_level']}."
                    )
                await self.send(
                    "Geody są dodatkowym rzutem Górnictwa i nie zastępują rudy ani zwykłego klejnotu. "
                    "Otwieranie: open geode / otwórz geodę."
                )
                return

            if q in ("ziola", "zioła", "herbs", "herb", "zielarstwo", "rosliny", "rośliny", "plants"):
                await self.send(f"ATLAS ZIÓŁ I ROŚLIN. Łącznie: {len(HERB_ATLAS_ALL)}.")
                herb_groups = (
                    ("meadow", "ŁĄKI I CHATA ZIELARKI", ("herbalist_hut", "meadow", "flower_meadow"), HERB_MEADOW_ATLAS),
                    ("water", "TERENY NAD WODĄ", ("riverbank", "lake_shore", "lakeside_meadow"), HERB_WATER_ATLAS),
                    ("forest", "GAJ SZEPTÓW I STARY TRAKT", ("whisper_grove", "old_road"), HERB_FOREST_ATLAS),
                    ("deep", "GŁĘBIA GAJU", ("deep_grove",), HERB_DEEP_ATLAS),
                )
                for key, title, rooms, items in herb_groups:
                    places = ", ".join(ROOMS[r]["name"] for r in rooms)
                    await self.send_atlas_group_with_levels(
                        title, places, items, "herb", key, "Sierp", chunk_size=12
                    )
                if "field_grave_moss" in ITEMS:
                    await self.send("TERENOWE ROŚLINY: Mech Nagrobny [Sierp 20+; Stary Cmentarz]; Cierń Pustki [Sierp 60+; Ruiny Kultystów].")
                dedicated = []
                for room_id, herb_id in HERB_SPECIFIC_MEADOWS.items():
                    if room_id in ROOMS and herb_id in ITEMS:
                        dedicated.append(f"{ITEMS[herb_id]['name']} — {ROOMS[room_id]['name']} [Sierp 1+]")
                if dedicated:
                    await self.send("ŁĄKI TEMATYCZNE: " + "; ".join(dedicated) + ".")
                await self.send(
                    "Ogród Alchemika również korzysta z puli Głębi Gaju; wymagany sektor zależy od levelu danego zioła."
                )
                await self.send(
                    "Wpisz atlas <nazwa zioła>, aby usłyszeć wszystkie lokacje i minimalny level Sierpa dla każdej z nich."
                )
                return

            resources = {
                item_id: ITEMS[item_id]
                for item_id in (
                    FISH_STORAGE_IDS
                    | ORE_STORAGE_IDS
                    | MINING_STORAGE_IDS
                    | WOOD_STORAGE_IDS
                    | HERB_STORAGE_IDS
                )
            }
            found = find_by_name(resources, query)
            if not found:
                # v0.8.75: prosta nazwa klejnotu (np. "diament") pasuje do kilku
                # jakości naraz. W takim wypadku atlas pokazuje wariant bazowy,
                # zamiast uznawać wyszukiwanie za niejednoznaczne. Konkretna jakość
                # nadal działa normalnie, np. "atlas czysty diament".
                q_lookup = normalize_lookup_text(query)
                gem_matches = []
                for definition in GEM_DEFINITIONS:
                    gem_names = (
                        definition["key"],
                        definition["raw_name"],
                        definition["cut_name"],
                        definition["raw_name"].replace("Surowy ", "", 1),
                        definition["cut_name"].replace("Szlifowany ", "", 1),
                    )
                    if any(
                        q_lookup == normalize_lookup_text(name)
                        for name in gem_names
                    ):
                        gem_matches.append(definition)
                if len(gem_matches) == 1:
                    base_gem_id = f"raw_gem_{gem_matches[0]['key']}"
                    found = (base_gem_id, ITEMS[base_gem_id])
            if not found:
                await self.send(
                    "Atlas nie rozpoznaje tego surowca. Wpisz atlas ryby, atlas drewno, atlas rudy, atlas geody albo atlas zioła."
                )
                return

            item_id, item = found
            base_id = item.get("base_resource_id", item_id)
            base_item = ITEMS.get(base_id, item)
            await self.send(f"ATLAS: {item['name']}.")
            if item.get("rare_resource_variant"):
                await self.send(f"Bazowy surowiec: {base_item['name']}.")
            if base_id in FISH_RESOURCE_IDS:
                await self.send("Typ: ryba. Trafia do Siatki na ryby.")
            elif base_id in WOOD_RESOURCE_IDS:
                await self.send("Typ: drewno. Trafia na Stos drewna.")
            elif base_id in HERB_RESOURCE_IDS:
                await self.send("Typ: zioło lub roślina. Trafia do Torby Zielarskiej.")
            elif item_id in RAW_GEM_IDS:
                await self.send("Typ: surowy klejnot Górnictwa. Trafia do Sakwy Górnika.")
            elif item_id in GEODE_IDS:
                await self.send("Typ: geoda Górnictwa. Trafia do Sakwy Górnika.")
            else:
                await self.send("Typ: ruda lub minerał. Trafia do Sakwy górniczej.")

            if item_id in RAW_GEM_IDS:
                gem_key = item.get("gem_key")
                definition = next((d for d in GEM_DEFINITIONS if d["key"] == gem_key), None)
                if definition:
                    quality = item.get("gem_quality", "raw")
                    await self.send(
                        f"Górnictwo: Kilof {definition['mining_level']}+; efektywna głębokość kopalni {definition['min_floor']}+. "
                        f"Jakość: {GEM_QUALITY_INFO.get(quality, GEM_QUALITY_INFO['raw'])['label']}. "
                        "Klejnot jest dodatkowym znaleziskiem obok normalnej rudy i trafia do Sakwy Górnika."
                    )
                    return
            if item_id in GEODE_IDS:
                cfg = GEODE_DEFINITIONS[item_id]
                await self.send(
                    f"Górnictwo: Kilof {cfg['min_tool']}+; efektywna głębokość {cfg['min_floor']}+. "
                    "Geoda jest dodatkowym znaleziskiem. Otwórz ją przez open geode / otwórz geodę."
                )
                return
            rows = self.atlas_resource_requirement_rows(base_id)
            if rows:
                tool, minimum = self.atlas_resource_min_level(base_id)
                await self.send(f"Minimalny wymagany level: {tool} {minimum}+.")
                for place, row_tool, level in rows:
                    await self.send(f"{place}: {row_tool} level {level}+.")
            else:
                await self.send("Brak danych o miejscu pozyskania tego surowca.")

    def codex_boss_ids(self):
            result = set()
            for mob_id, mob in MOB_TEMPLATES.items():
                if (
                    mob_id.startswith("crypt_boss_")
                    or mob_id.startswith("astral_boss_")
                    or mob_id.startswith("mythic_crypt_boss_")
                    or mob_id.startswith("mythic_astral_boss_")
                    or mob.get("world_boss")
                    or mob.get("boss_mechanic")
                ):
                    result.add(mob_id)
            return result

    def codex_relic_ids(self):
            result = set()
            for item_id, item in ITEMS.items():
                if (
                    item.get("boss_relic_floor") is not None
                    or item_id.startswith("astral_relic_")
                    or item.get("rarity") == "unique"
                ):
                    result.add(item_id)
            return result

    async def send_codex_name_list(
            self, title, names, chunk_size=20
        ):
            names = sorted(
                set(names),
                key=self.normalize_description_query,
            )
            await self.send(
                f"{title}. Łącznie: {len(names)}."
            )
            if not names:
                await self.send("Brak wpisów.")
                return

            chunk_size = max(1, int(chunk_size))
            total = (
                len(names) + chunk_size - 1
            ) // chunk_size
            for index in range(0, len(names), chunk_size):
                part = index // chunk_size + 1
                await self.send(
                    f"Część {part} z {total}: "
                    + ", ".join(
                        names[index:index + chunk_size]
                    )
                    + "."
                )

    def bestiary_spawn_room_ids(self, mob_template_id):
            base_id = canonical_bestiary_template_id(mob_template_id)
            return tuple(sorted(BESTIARY_SPAWN_ROOMS.get(base_id, ())))

    def bestiary_drop_lines(self, mob_template_id):
            base_id = canonical_bestiary_template_id(mob_template_id)
            template = MOB_TEMPLATES.get(base_id, {})
            result = []
            key_id = boss_key_for_template(template)
            if key_id and key_id in ITEMS:
                result.append(f"{ITEMS[key_id]['name']} — gwarantowany w ciele")
            for item_id, chance in sorted(
                (template.get("drops") or {}).items(),
                key=lambda row: normalize_lookup_text(ITEMS.get(row[0], {"name": row[0]}).get("name", row[0])),
            ):
                name = player_item_display_name_v0335(item_id)
                result.append(f"{name} — około {float(chance) * 100:.1f}%")
            return result

    async def show_bestiary(self, args=""):
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            rows = self.server.db.bestiary_rows(self.account_id)
            known_ids = {str(row["mob_template_id"]) for row in rows}
            total_kills = sum(int(row["kills"]) for row in rows)
            total_entries = len(BESTIARY_CATALOG)
            unlocked = len(known_ids.intersection(BESTIARY_CATALOG))
            pct = int(unlocked * 100 / max(1, total_entries))

            if not raw:
                await self.send(
                    f"BESTIARIUSZ: {unlocked} z {total_entries} gatunków, {pct}%. "
                    f"Łączne zaliczone zabicia: {total_kills}."
                )
                await self.send(
                    "Pierwsze zabicie odblokowuje wpis. Elite i proceduralne Rare liczą się do bazowego gatunku, więc Bestiariusz nie wymaga tysięcy kopii affixów."
                )
                await self.send(
                    "Komendy: bestiariusz lista / bestiary list; bestiariusz rekordy / bestiary records; bestiariusz <mob> / bestiary <mob>."
                )
                return

            if norm in ("lista", "list", "odkryte", "unlocked"):
                if not rows:
                    await self.send("Bestiariusz jest pusty. Pokonaj pierwszego przeciwnika, aby odblokować wpis.")
                    return
                entries = []
                for row in rows:
                    mob_id = str(row["mob_template_id"])
                    if mob_id not in BESTIARY_CATALOG:
                        continue
                    entries.append((BESTIARY_CATALOG[mob_id], int(row["kills"])))
                entries.sort(key=lambda x: normalize_lookup_text(x[0]))
                await self.send(f"ODKRYTE WPISY BESTIARIUSZA: {len(entries)}.")
                chunk = []
                for name, kills in entries:
                    chunk.append(f"{name} ({kills})")
                    if len(chunk) >= 18:
                        await self.send(", ".join(chunk) + ".")
                        chunk = []
                if chunk:
                    await self.send(", ".join(chunk) + ".")
                return

            if norm in ("rekordy", "records", "record", "czasy", "times"):
                timed = [row for row in rows if row["fastest_kill_ms"] is not None and str(row["mob_template_id"]) in BESTIARY_CATALOG]
                timed.sort(key=lambda row: int(row["fastest_kill_ms"]))
                if not timed:
                    await self.send("Nie masz jeszcze zapisanych rekordów czasu zabicia.")
                    return
                await self.send("NAJLEPSZE CZASY BESTIARIUSZA:")
                for index, row in enumerate(timed[:20], 1):
                    mob_id = str(row["mob_template_id"])
                    await self.send(
                        f"{index}. {BESTIARY_CATALOG[mob_id]}: {int(row['fastest_kill_ms']) / 1000.0:.2f} s; zabicia {int(row['kills'])}."
                    )
                return

            unlocked_mapping = {
                mob_id: MOB_TEMPLATES[mob_id]
                for mob_id in known_ids
                if mob_id in MOB_TEMPLATES
            }
            found = find_by_name(unlocked_mapping, raw)
            if not found:
                # Distinguish an unknown name from a real but not-yet-killed creature
                all_found = find_by_name(
                    {mob_id: MOB_TEMPLATES[mob_id] for mob_id in BESTIARY_CATALOG}, raw
                )
                if all_found:
                    await self.send("Ten wpis Bestiariusza jest jeszcze nieodkryty. Najpierw pokonaj tego przeciwnika.")
                else:
                    await self.send("Bestiariusz nie rozpoznaje takiego przeciwnika.")
                return

            mob_id, template = found
            row = self.server.db.bestiary_entry(self.account_id, mob_id)
            if not row:
                await self.send("Ten wpis Bestiariusza jest jeszcze nieodkryty.")
                return
            kind = "boss" if (mob_id in BOSS_COLLECTION_CATALOG or v0863_is_boss_template(template)) else ("mini-boss" if template.get("mini_boss") else "zwykły przeciwnik")
            await self.send(f"BESTIARIUSZ: {template['name']}. Typ: {kind}.")
            fastest = row["fastest_kill_ms"]
            fastest_text = f"{int(fastest) / 1000.0:.2f} s" if fastest is not None else "brak zapisanego czasu"
            await self.send(f"Zabicia: {int(row['kills'])}. Rekord pokonania: {fastest_text}.")
            dtype = "magiczne" if template.get("damage_type") == "magic" else "fizyczne"
            await self.send(
                f"HP: {int(template.get('max_hp', 0))}. Bazowe obrażenia: {int(template.get('damage', 0))}. "
                f"Typ ataku: {dtype}. Odporności: {bestiary_resistance_text(template)}."
            )
            room_ids = self.bestiary_spawn_room_ids(mob_id)
            if room_ids:
                zones = sorted({ROOMS[rid]["zone"] for rid in room_ids if rid in ROOMS}, key=normalize_lookup_text)
                names = sorted({ROOMS[rid]["name"] for rid in room_ids if rid in ROOMS}, key=normalize_lookup_text)
                await self.send("Regiony występowania: " + ", ".join(zones) + ".")
                if len(names) <= 12:
                    await self.send("Lokacje: " + ", ".join(names) + ".")
                else:
                    await self.send("Lokacje: " + ", ".join(names[:12]) + f"; oraz {len(names) - 12} dalszych.")
            drops = self.bestiary_drop_lines(mob_id)
            if drops:
                await self.send("Dropy: " + "; ".join(drops) + ".")
            else:
                await self.send("Dropy specjalne: brak stałych wpisów; nadal może wystąpić materiałowe EQ z ciała zgodnie z siłą przeciwnika.")
            if template.get("boss_mechanic_text"):
                await self.send("Mechanika: " + str(template["boss_mechanic_text"]))

    async def show_world_codex(self, query=""):
            q = self.normalize_description_query(query)
            bosses = self.codex_boss_ids()
            normal_mobs = set(MOB_TEMPLATES) - bosses
            relics = self.codex_relic_ids()

            if not q:
                await self.send("CODEX ŚWIATA")
                await self.send(
                    f"Ryby: {len(FISH_RESOURCE_IDS)} gatunków bazowych. "
                    f"Rzadkie warianty ryb: "
                    f"{len(RARE_FISH_VARIANT_IDS)}."
                )
                await self.send(
                    f"Rośliny i zioła: {len(HERB_RESOURCE_IDS)} bazowych. "
                    f"Rzadkie warianty roślin: "
                    f"{len(RARE_HERB_VARIANT_IDS)}."
                )
                await self.send(
                    f"Drewno: {len(WOOD_RESOURCE_IDS)} bazowych rodzajów. "
                    f"Rzadkie warianty drewna: "
                    f"{len(RARE_WOOD_VARIANT_IDS)}."
                )
                await self.send(
                    f"Rudy i minerały: {len(ORE_RESOURCE_IDS)}. "
                    f"Rodzaje żył: {len(MINING_VEINS)}."
                )
                await self.send(
                    f"Zwykłe moby: {len(normal_mobs)}. "
                    f"Bossowie: {len(bosses)}. "
                    f"Relikty i unikalne trofea: {len(relics)}."
                )
                await self.send(
                    "Działy: codex ryby, codex rośliny, codex drewno, "
                    "codex rudy, codex warianty, codex moby, "
                    "codex bossowie, codex relikty."
                )
                await self.send(
                    "Możesz też wpisać codex <nazwa>, aby wyszukać "
                    "konkretny zasób, mob, bossa albo relikt."
                )
                return

            if q in ("ryby", "ryba", "fish"):
                await self.send_complete_atlas_list(
                    "CODEX RYB - GATUNKI BAZOWE",
                    FISH_RESOURCE_IDS,
                    chunk_size=20,
                )
                await self.send(
                    "Rzadkie warianty każdego gatunku: "
                    "Albinos x2 wartości, Złoty okaz x4, "
                    "Olbrzymi okaz x3, Pradawny okaz x8."
                )
                await self.send(
                    "Szansa na rzadki wariant rośnie wraz z levelem "
                    "Wędki: około 8 do 12 procent."
                )
                return

            if q in (
                "rosliny", "rośliny", "ziola", "zioła",
                "herbs", "plants",
            ):
                await self.send_complete_atlas_list(
                    "CODEX ROŚLIN I ZIÓŁ - BAZOWE",
                    HERB_RESOURCE_IDS,
                    chunk_size=20,
                )
                await self.send(
                    "Rzadkie warianty: Bujna x2 wartości, "
                    "Lśniąca x4, Pradawna x6, Legendarna x10."
                )
                await self.send(
                    "Szansa na wariant rośnie z levelem Sierpa."
                )
                return

            if q in ("drewno", "wood", "drzewa", "drzewo"):
                await self.send_complete_atlas_list(
                    "CODEX DREWNA - BAZOWE",
                    WOOD_RESOURCE_IDS,
                    chunk_size=20,
                )
                await self.send(
                    "Rzadkie warianty drzew: Bujne x2 wartości, "
                    "Pradawne x4, Kryształowe x6, Legendarne x10."
                )
                await self.send(
                    "Szansa na wariant rośnie z levelem Piły."
                )
                return

            if q in ("rudy", "ruda", "ore", "mineral", "mineraly"):
                await self.send_complete_atlas_list(
                    "CODEX RUD I MINERAŁÓW",
                    ORE_RESOURCE_IDS,
                    chunk_size=20,
                )
                await self.send(
                    "Rodzaje żył: Zwykła x1, Bogata x2, "
                    "Kryształowa x3, Legendarna x5 urobku."
                )
                await self.send(
                    "Im wyższy level Kilofa, tym większa szansa na "
                    "Bogate, Kryształowe i Legendarne żyły."
                )
                return

            if q in ("warianty", "rare", "rzadkie"):
                await self.send("CODEX RZADKICH WARIANTÓW")
                await self.send(
                    "Ryby: Albinos, Złoty okaz, Olbrzymi okaz, "
                    "Pradawny okaz."
                )
                await self.send(
                    "Drzewa i drewno: Bujne, Pradawne, "
                    "Kryształowe, Legendarne."
                )
                await self.send(
                    "Rośliny: Bujna, Lśniąca, Pradawna, Legendarna."
                )
                await self.send(
                    "Górnictwo: Zwykła, Bogata, Kryształowa "
                    "i Legendarna żyła."
                )
                return

            if q in ("moby", "mob", "potwory", "przeciwnicy"):
                await self.send_codex_name_list(
                    "CODEX MOBÓW",
                    (
                        MOB_TEMPLATES[mob_id]["name"]
                        for mob_id in normal_mobs
                    ),
                    chunk_size=20,
                )
                return

            if q in ("bossowie", "boss", "bosses"):
                await self.send_codex_name_list(
                    "CODEX BOSSÓW",
                    (
                        MOB_TEMPLATES[mob_id]["name"]
                        for mob_id in bosses
                    ),
                    chunk_size=20,
                )
                return

            if q in ("relikty", "relikt", "relic", "relics"):
                await self.send_codex_name_list(
                    "CODEX RELIKTÓW I TROFEÓW",
                    (
                        ITEMS[item_id]["name"]
                        for item_id in relics
                    ),
                    chunk_size=20,
                )
                return

            searchable_items = {
                item_id: item
                for item_id, item in ITEMS.items()
                if (
                    item_id in FISH_STORAGE_IDS
                    or item_id in ORE_STORAGE_IDS
                    or item_id in WOOD_STORAGE_IDS
                    or item_id in HERB_STORAGE_IDS
                    or item_id in relics
                )
            }
            found = find_by_name(searchable_items, query)
            if found:
                item_id, item = found
                await self.send(f"CODEX: {item['name']}.")
                await self.send(item.get("desc", "Brak opisu."))
                if item.get("rare_resource_variant"):
                    base_id = item.get("base_resource_id")
                    base_name = ITEMS.get(
                        base_id, {"name": base_id}
                    )["name"]
                    await self.send(
                        f"Rzadki wariant: "
                        f"{item.get('rare_resource_label')}. "
                        f"Bazowy zasób: {base_name}. "
                        f"Mnożnik wartości: x"
                        f"{item.get('rare_value_multiplier', 1)}."
                    )
                places = self.atlas_item_locations(item_id)
                if places:
                    await self.send(
                        "Występowanie: "
                        + ", ".join(places)
                        + "."
                    )
                tool, minimum = self.atlas_resource_min_level(item_id)
                if tool is not None:
                    await self.send(
                        f"Minimalny wymagany level: {tool} {minimum}+. "
                        "Dokładne poziomy dla każdej lokacji: atlas "
                        f"{item['name']}."
                    )
                return

            found_mob = find_by_name(MOB_TEMPLATES, query)
            if found_mob:
                mob_id, mob = found_mob
                kind = (
                    "boss"
                    if mob_id in bosses
                    else "zwykły mob"
                )
                dtype = (
                    "magiczne"
                    if mob.get("damage_type") == "magic"
                    else "fizyczne"
                )
                await self.send(
                    f"CODEX: {mob['name']}. Typ: {kind}."
                )
                await self.send(
                    f"HP: {mob.get('max_hp', 0)}. "
                    f"Bazowe obrażenia: {mob.get('damage', 0)}. "
                    f"Typ obrażeń: {dtype}."
                )
                await self.send(
                    f"Nagrody: Soul XP {mob.get('soul_reward', 0)}, "
                    f"Class XP {mob.get('class_xp_reward', max(50, int(mob.get('stat_reward', 0)) * 10))}, "
                    f"Bazowy EXP każdej statystyki +{mob.get('stat_reward', 0)}."
                )
                rooms = sorted({
                    ROOMS[room_id]["name"]
                    for room_id, template_id in MOB_SPAWNS
                    if template_id == mob_id and room_id in ROOMS
                })
                if rooms:
                    await self.send("Występowanie: " + ", ".join(rooms) + ".")
                drops = [
                    f"{player_item_display_name_v0335(item_id)} około {int(chance * 100)} procent"
                    for item_id, chance in mob.get("drops", {}).items()
                ]
                if drops:
                    await self.send("Drop: " + ", ".join(drops) + ".")
                if mob.get("boss_mechanic_text"):
                    await self.send(
                        "Mechanika: "
                        + mob["boss_mechanic_text"]
                    )
                if kind == "boss":
                    await self.send(
                        "Boss ma fazy przy 75, 50 i 25 procent HP. "
                        "NVDA dostaje krótki komunikat przy każdej zmianie fazy."
                    )
                return

            await self.send(
                "Codex nie znalazł takiego wpisu. "
                "Wpisz codex bez argumentu, aby usłyszeć działy."
            )

    async def describe_target(self, query):
            q = query.strip()

            if not q:
                room = ROOMS[self.character.room_id]
                await self.send(f"{room['name']}. Strefa: {room['zone']}. {room['desc']}")
                features = self.room_special_features(self.character.room_id)
                if features:
                    await self.send("Funkcje lokacji: " + ", ".join(features) + ".")
                await self.show_exits()
                return

            normalized = self.normalize_description_query(q)

            normalized_systems = {
                self.normalize_description_query(k): v
                for k, v in SYSTEM_DESCRIPTIONS.items()
            }
            normalized_stats = {
                self.normalize_description_query(k): v
                for k, v in STAT_DESCRIPTIONS.items()
            }
            if normalized in normalized_stats:
                await self.send(normalized_stats[normalized])
                return
            if normalized in normalized_systems:
                await self.send(normalized_systems[normalized])
                return

            found = self.find_description_entry(ITEMS, q)
            if found:
                item_id, item = found
                await self.send(self.format_item_description(item_id, item))
                return

            found = self.find_description_entry(NPCS, q)
            if found:
                npc_id, npc = found
                room = ROOMS[npc["room"]]
                desc = NPC_DESCRIPTIONS.get(npc_id, npc.get("dialogue", ""))
                await self.send(f"{npc['name']}. {desc}")
                await self.send(f"Stała lokacja: {room['name']}.")
                if npc.get("quest"):
                    quest = QUESTS[npc["quest"]]
                    await self.send(f"Powiązane zadanie: {quest['name']}. {quest['description']}")
                return

            found = self.find_description_entry(MOB_TEMPLATES, q)
            if found:
                mob_id, mob = found
                dtype = "magiczne" if mob.get("damage_type") == "magic" else "fizyczne"
                await self.send(f"{mob['name']}. {MOB_DESCRIPTIONS.get(mob_id, '')}")
                await self.send(
                    f"HP: {mob['max_hp']}. Bazowe obrażenia: {mob['damage']}. Typ obrażeń: {dtype}."
                )
                await self.send(
                    "Nagroda podstawowa: "
                    + currency_reading_text(
                        mob.get("silver", 0), mob.get("gold", 0), mob.get("mithril", 0)
                    )
                    + f"; bazowy EXP każdej statystyki +{mob.get('stat_reward',0)}; "
                    + f"Soul XP +{mob.get('soul_reward',0)}."
                )
                drops = []
                for item_id, chance in mob.get("drops", {}).items():
                    drops.append(f"{player_item_display_name_v0335(item_id)} około {int(chance * 100)} procent")
                if drops:
                    await self.send("Możliwe dropy: " + ", ".join(drops) + ".")
                return

            found = self.find_description_entry(ROOMS, q)
            if found:
                room_id, room = found
                await self.send(f"{room['name']}. Strefa: {room['zone']}. {room['desc']}")
                exits = ", ".join(room["exits"].keys()) if room["exits"] else "brak"
                await self.send("Wyjścia: " + exits + ".")
                features = self.room_special_features(room_id)
                if features:
                    await self.send("Funkcje lokacji: " + ", ".join(features) + ".")
                return

            found = self.find_description_entry(QUESTS, q)
            if found:
                quest_id, quest = found
                await self.send(
                    f"Zadanie: {quest['name']}. Zleca: {quest['giver']}. {quest['description']}"
                )
                rewards = []
                if quest.get("reward_stat_progress"):
                    rewards.append(f"{quest['reward_stat_progress']} EXP każdej statystyki")
                if quest.get("reward_profession_xp"):
                    rewards.append(
                        f"{quest['reward_profession_xp']} XP profesji {quest.get('reward_profession','')}"
                    )
                if quest.get("reward_tool_xp"):
                    tool = "Wędki" if quest.get("reward_tool_type") == "fishing" else "Kilofa"
                    rewards.append(f"{quest['reward_tool_xp']} XP {tool}")
                if (
                    quest.get("reward_silver")
                    or quest.get("reward_gold")
                    or quest.get("reward_mithril")
                ):
                    rewards.append(
                        currency_reading_text(
                            quest.get("reward_silver", 0),
                            quest.get("reward_gold", 0),
                            quest.get("reward_mithril", 0),
                        )
                    )
                for item_id, qty in quest.get("reward_items", {}).items():
                    rewards.append(f"{player_item_display_name_v0335(item_id)} x{qty}")
                if rewards:
                    await self.send("Nagrody: " + ", ".join(rewards) + ".")
                return

            race_map = {
                race[0]: {
                    "name": race[0], "desc": race[1],
                    "strength": race[2], "dexterity": race[3],
                    "constitution": race[4], "intelligence": race[5],
                    "willpower": race[6], "charisma": 10,
                }
                for race in RACES
            }
            found = self.find_description_entry(race_map, q)
            if found:
                _, race = found
                await self.send(f"Rasa: {race['name']}. {race['desc']}")
                await self.send(
                    f"Startowe statystyki: Siła {race['strength']}, "
                    f"Zręczność {race['dexterity']}, Kondycja {race['constitution']}, "
                    f"Inteligencja {race['intelligence']}, Siła Woli {race['willpower']}, "
                    f"Charyzma {race['charisma']}."
                )
                await self.send(
                    race_class_recommendation_text(race['name']) +
                    " To rekomendacja, nie ograniczenie wyboru klasy."
                )
                return

            class_map = {
                cls[0]: {"name": cls[0], "type": cls[1], "weapon": cls[2], "base": cls[3]}
                for cls in CLASSES
            }
            found = self.find_description_entry(class_map, q)
            if found:
                _, cls = found
                kind = "fizyczna" if cls["type"] == "physical" else "magiczna"
                await self.send(
                    f"Klasa: {cls['name']}. Typ: {kind}. {CLASS_DESCRIPTIONS.get(cls['name'], '')}"
                )
                await self.send(
                    f"Broń Duszy: {cls['weapon']}. Bazowa moc Broni Duszy: {cls['base']}."
                )
                await self.send("Rozwój klasy: wszystkie sześć statystyk rośnie automatycznie.")
                skills = CLASS_SKILLS.get(cls["name"], [])
                if skills:
                    await self.send(
                        "Umiejętności: " + "; ".join(
                            f"{s['name']} do nauki od Biegłości klasy {s['unlock']}" for s in skills
                        ) + "."
                    )
                return

            help_key = HELP_TOPIC_ALIASES.get(normalized, normalized)
            if help_key in HELP_TOPICS:
                await self.show_help(help_key)
                return

            await self.send(
                "Nie znalazłem takiego opisu. Spróbuj dokładniejszej nazwy albo wpisz help opisy."
            )

    async def show_name_declension(self):
            await self.send(f"ODMIANA IMIENIA: {self.character.name_nom}")
            await self.send(f"Mianownik: {self.character.name_nom}.")
            await self.send(f"Dopełniacz: {self.character.name_gen}.")
            await self.send(f"Celownik: {self.character.name_dat}.")
            await self.send(f"Biernik: {self.character.name_acc}.")
            await self.send(f"Narzędnik: {self.character.name_ins}.")
            await self.send(f"Miejscownik: {self.character.name_loc}.")
            await self.send(f"Wołacz: {self.character.name_voc}.")

    async def show_hp(self):
            """Krótki stan zasobów bez podwójnego nagłówka HP pod NVDA."""
            await self.send(f"HP: {self.current_hp} z {self.max_hp()}.")
            await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")

    async def show_character_level(self):
            """Krótki Level postaci 1-400, niezależny od Soul Levelu."""
            c = self.character
            if c.character_level >= CHARACTER_MAX_LEVEL:
                await self.send(f"Level postaci: {CHARACTER_MAX_LEVEL}/{CHARACTER_MAX_LEVEL}. Maksymalny poziom.")
                return
            needed = character_xp_to_next(c.character_level)
            missing = max(0, int(needed) - int(c.character_xp))
            await self.send(
                f"Level postaci: {c.character_level}/{CHARACTER_MAX_LEVEL}. "
                f"EXP {c.character_xp} z {needed}. Brakuje {missing} EXP do Levelu {c.character_level + 1}."
            )

    async def show_character_xp(self):
            """Stan EXP postaci z dokładną liczbą brakującą do następnego Levelu."""
            c = self.character
            if c.character_level >= CHARACTER_MAX_LEVEL:
                await self.send(f"EXP postaci: maksimum. Level {CHARACTER_MAX_LEVEL}/{CHARACTER_MAX_LEVEL}.")
                return
            needed = character_xp_to_next(c.character_level)
            missing = max(0, int(needed) - int(c.character_xp))
            await self.send(
                f"EXP postaci: {c.character_xp} z {needed}. "
                f"Brakuje {missing} EXP do Levelu {c.character_level + 1}."
            )

    async def show_score(self):
            """Czytelne podsumowanie wszystkich osi Generator Core."""
            c = self.character
            active_classes = self.active_class_names()
            room = ROOMS.get(c.room_id, {})

            await self.send("SCORE")
            await self.send(f"Postać: {c.name}.")
            await self.send(f"Rasa: {c.race}.")
            await self.send(f"Klasa główna: {c.class_name}.")
            await self.send(f"Level postaci: {c.character_level}/400. EXP: {c.character_xp} z {character_xp_to_next(c.character_level) if c.character_level < 400 else 0}.")
            for class_name in active_classes:
                await self.send(
                    f"Biegłość {class_name}: {self.class_mastery_level(class_name)}/{CLASS_MASTERY_MAX_LEVEL}."
                )
            await self.send(f"Broń Duszy: {c.soul_weapon}.")
            await self.send(f"Soul Level: {c.soul_level}/{SOUL_MAX_LEVEL}.")
            await self.send(f"Soul Tier: {c.soul_tier}/{SOUL_MAX_TIER}.")
            await self.send(f"HP: {self.current_hp} z {self.max_hp()}.")
            await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
            await self.send(f"Siła: {self.effective_strength()}.")
            await self.send(f"Zręczność: {self.effective_dexterity()}.")
            await self.send(f"Kondycja: {self.effective_constitution()}.")
            await self.send(f"Inteligencja: {self.effective_intelligence()}.")
            await self.send(f"Siła Woli: {self.effective_willpower()}.")
            await self.send(f"Charyzma: {c.charisma}.")
            await self.send(
                "Portfel: "
                + currency_reading_text(
                    c.silver, c.gold, c.mithril,
                    full_names=True, include_zero=True,
                )
                + "."
            )
            await self.send(f"Lokacja: {room.get('name', c.room_id)}.")
            await self.send(f"Strefa: {room.get('zone', 'brak')}.")
            area = self.exp_area_for_room(c.room_id)
            if area:
                label, target, power = self.exp_area_dynamic_threat(area, room_id=c.room_id)
                await self.send(f"Ocena terenu dla tej postaci: {label}.")
                await self.send(
                    f"Orientacyjna siła progresji: {power}/400. Próg terenu: {target}/400."
                )
            else:
                await self.send(
                    f"Orientacyjna siła progresji: {self.character_progression_power()}/400."
                )
            await self.send("Wszystkie główne osie progresji 1-400 korzystają z Generator Core.")

    async def show_stats(self, mode=""):
            mode = self.normalize_description_query(mode)
            detailed = mode in (
                "info", "pelne", "pełne", "szczegoly", "szczegóły",
                "details", "mechanika",
            )
            c = self.character
            bonuses = self.equipment_bonus_totals()
            active_classes = self.active_class_names()

            if not detailed:
                await self.send("STATY")
                await self.send(f"Postać: {c.name}.")
                await self.send(f"Rasa: {c.race}.")
                await self.send(f"Klasa główna: {c.class_name}.")
                await self.send(f"Aktywne klasy: {', '.join(active_classes)}.")
                stat_values = (
                    ("strength", "Siła", c.strength, self.effective_strength()),
                    ("dexterity", "Zręczność", c.dexterity, self.effective_dexterity()),
                    ("constitution", "Kondycja", c.constitution, self.effective_constitution()),
                    ("intelligence", "Inteligencja", c.intelligence, self.effective_intelligence()),
                    ("willpower", "Siła Woli", c.willpower, self.effective_willpower()),
                    ("charisma", "Charyzma", c.charisma, c.charisma),
                )
                for stat_key, label, base_value, effective_value in stat_values:
                    effective_text = (
                        f" Efektywna {effective_value}."
                        if effective_value != base_value else ""
                    )
                    await self.send(
                        f"{label}: {base_value} — {stat_quality_label(base_value)}."
                        f"{effective_text} EXP {c.stat_progress_for(stat_key)} z "
                        f"{c.stat_growth_threshold_for(stat_key)}."
                    )
                await self.send(f"HP: {self.current_hp} z {self.max_hp()}.")
                await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                await self.send(f"Obrona fizyczna: {self.defense()}.")
                await self.send(f"Obrona magiczna: {self.magic_defense()}.")
                await self.send(f"Atak fizyczny: {self.physical_power()}.")
                await self.send(f"Moc czarów: {self.spell_power() if self.max_mana() > 0 else 0}.")
                await self.send(f"Unik: {int(self.dodge_chance() * 100)} procent.")
                await self.send(f"Krytyk: {int(round(self.critical_chance() * 100))} procent.")
                await self.send("Każda statystyka ma własny, niezależny licznik EXP.")
                await self.send("Wpisz staty info po pełne szczegóły albo help staty po pomoc.")
                return

            await self.send("STATY INFO")
            await self.send("Soulbound nie ma levelu ani XP postaci. Każda statystyka rozwija się osobno.")
            stat_rows = (
                ("strength", "Siła", c.strength, self.effective_strength(), bonuses["strength"]),
                ("dexterity", "Zręczność", c.dexterity, self.effective_dexterity(), bonuses["dexterity"]),
                ("constitution", "Kondycja", c.constitution, self.effective_constitution(), bonuses["constitution"]),
                ("intelligence", "Inteligencja", c.intelligence, self.effective_intelligence(), bonuses["intelligence"]),
                ("willpower", "Siła Woli", c.willpower, self.effective_willpower(), bonuses["willpower"]),
                ("charisma", "Charyzma", c.charisma, c.charisma, 0),
            )
            for stat_key, label, base, effective, gear_bonus in stat_rows:
                await self.send(f"{label}: baza {base} — {stat_quality_label(base)}.")
                if stat_key != "charisma":
                    await self.send(f"{label}: efektywna {effective}. Bonus EQ i klejnotów +{gear_bonus}.")
                else:
                    await self.send(f"{label}: efektywna {effective}.")
                await self.send(
                    f"{label}: EXP {c.stat_progress_for(stat_key)} z "
                    f"{c.stat_growth_threshold_for(stat_key)} do następnego wzrostu."
                )
            await self.send(f"HP: {self.current_hp} z {self.max_hp()}. Bonus EQ +{bonuses['hp']}.")
            await self.send(f"Mana: {self.current_mana} z {self.max_mana()}. Bonus EQ +{bonuses['mana']}.")
            await self.send(f"Obrona fizyczna: {self.defense()}.")
            await self.send(f"Obrona magiczna: {self.magic_defense()}.")
            await self.send(f"Szybkość: {self.speed()}.")
            await self.send(f"Krytyk: {int(round(self.critical_chance() * 100))} procent.")
            await self.send(f"Mnożnik krytyka: {int(self.critical_multiplier() * 100)} procent.")
            await self.send(f"Unik: {int(self.dodge_chance() * 100)} procent.")
            await self.send("Kondycja zwiększa maksymalne HP każdej klasy.")
            await self.send("Inteligencja zwiększa maksymalną Manę każdej klasy.")
            await self.send("Zręczność zwiększa szybkość, unik i krytyki każdej klasy.")
            await self.send(
                "Siła zwiększa obrażenia fizyczne i daje 25 procent swojego wpływu "
                "jako wtórne skalowanie magicznych skilli i spelli."
            )
            await self.send(f"Pasyw rasy {c.race}: {c.racial_passive_text()}.")
            for class_name in active_classes:
                await self.send(f"Pasyw klasy {class_name}: {c.class_passive_text_for(class_name)}.")
            await self.send(f"Bonus Broni Duszy klasy głównej: {c.soul_weapon_class_bonus_text()}.")
            await self.send(self.crypt_set_bonus_text())
            await self.send(self.astral_set_bonus_text())
            for line in self.class_set_status_lines():
                await self.send(line)
            await self.send(f"Rabat sklepowy z Charyzmy: {c.shop_discount_percent()} procent.")
            await self.send(f"Limit drużyny jako lider: {c.party_capacity()}.")

    def soul_milestone_text(self, tier):
            tier = int(tier)
            if tier not in SOUL_MILESTONE_TIERS:
                return ""
            name = SOUL_MILESTONE_NAMES[tier]
            c = self.character
            if c.class_name == "Łotrzyk":
                damage = c.soul_weapon_rogue_damage_bonus_percent()
                dodge = int(round(c.soul_weapon_dodge_bonus() * 100))
                effect = (
                    f"specjalizacja Łotrzyka: obrażenia fizyczne Broni Duszy "
                    f"+{damage} procent, unik z Broni Duszy +{dodge} pp"
                )
            elif c.class_name == "Strażnik":
                amount = SOUL_MILESTONE_GUARDIAN_REDUCTION[tier]
                effect = f"dodatkowa redukcja obrażeń +{amount} procent"
            else:
                amount = SOUL_MILESTONE_SPECIALIZATION_BONUS[tier]
                effect = f"dodatkowa specjalizacja Broni Duszy +{amount} procent"
            return f"{name}: {effect}."

    def soul_next_goal_text(self):
            c = self.character
            if c.soul_level >= SOUL_MAX_LEVEL and c.soul_tier >= SOUL_MAX_TIER:
                return "Soul Level i Tier są maksymalne."

            if c.soul_tier >= SOUL_MAX_TIER:
                return f"Tier jest maksymalny. Rozwijaj Soul do {SOUL_MAX_LEVEL}."

            next_tier = c.soul_tier + 1
            needed = SOUL_TIER_THRESHOLDS[next_tier - 1]
            if c.soul_level < needed:
                return f"Następny cel: Soul {needed} dla Tieru {next_tier}."

            quest_id = SOUL_TRIAL_QUEST_IDS.get(next_tier)
            if quest_id:
                if self.soul_tier_quest_completed(next_tier):
                    return f"Próba Tieru {next_tier} ukończona. Wpisz unlock."
                band = soul_trial_difficulty_band(next_tier)
                return (
                    f"Soul wymagany osiągnięty. Tier {next_tier} wymaga "
                    f"Próby Broni Duszy u Kapłana Elora. Pasmo: {band}."
                )
            return f"Tier {next_tier} jest gotowy. Wpisz unlock."

    async def show_guild(self, args=""):
            active = list(getattr(self.character, "classes", []) or [])
            if not active and getattr(self.character, "class_name", None):
                active = [self.character.class_name]
            query = (args or "").strip()
            if not query or query.lower() in ("info", "status", "stan"):
                lines = ["Gildia klasowa:"]
                for cls in active:
                    rep = self.character.guild_reputation(cls)
                    rank = self.character.guild_rep_rank(cls)
                    discount = int(round(self.character.guild_training_discount(cls) * 100))
                    exams = [str(t) for t in GUILD_EXAM_THRESHOLDS if self.character.guild_exam_done(cls, t)]
                    next_rank = next((r for r in GUILD_REPUTATION_RANKS if r[0] > rep), None)
                    next_text = f"następna ranga przy {next_rank[0]}" if next_rank else "maksymalna ranga"
                    lines.append(
                        f"{cls}: reputacja {rep}/{GUILD_REPUTATION_MAX}, ranga {rank[1]}, "
                        f"zniżka na naukę {discount}%, {next_text}, "
                        f"egzaminy: {', '.join(exams) if exams else 'brak'}."
                    )
                await self.send("\n".join(lines))
                return

            wanted = query.casefold()
            for cls in GUILD_CLASS_QUESTS:
                if cls.casefold() == wanted:
                    rep = self.character.guild_reputation(cls)
                    rank = self.character.guild_rep_rank(cls)
                    q = GUILD_CLASS_QUESTS[cls]
                    await self.send(
                        f"{cls}. Reputacja {rep}/{GUILD_REPUTATION_MAX}. Ranga: {rank[1]}. "
                        f"Zniżka na naukę: {int(rank[2]*100)}%. "
                        f"Zadanie klasowe: {q[0]}. {q[1]}"
                    )
                    return
            await self.send("Nie znam takiej klasy. Użyj: gildia info.")

    async def guild_class_quest(self, args=""):
            active = self.active_class_names()
            if not active:
                await self.send("Nie masz aktywnej klasy.")
                return
            cls = active[0]
            data = GUILD_CLASS_QUESTS.get(cls)
            if not data:
                await self.send("Ta klasa nie ma jeszcze zadania gildyjnego.")
                return

            states = self.character._guild_json("guild_class_quests_json")
            state = states.get(cls, {})
            if state is True:
                state = {"completed": True}
            if state.get("completed"):
                await self.send(f"Zadanie klasowe {cls} jest już ukończone.")
                return

            needed = int(data[4])
            if not state.get("accepted"):
                if self.character.soul_level < 25:
                    await self.send(f"{data[0]} wymaga Soul 25.")
                    return
                states[cls] = {"accepted": True, "progress": 0, "completed": False}
                self.character._set_guild_json("guild_class_quests_json", states)
                self.server.db.save_character(self.character)
                await self.send(f"Przyjęto zadanie: {data[0]}. {data[1]} Postęp 0 z {needed}.")
                return

            progress = int(state.get("progress", 0))
            if progress < needed:
                await self.send(f"{data[0]}. Postęp {progress} z {needed}. {data[1]}")
                return

            state["completed"] = True
            states[cls] = state
            self.character._set_guild_json("guild_class_quests_json", states)
            new_rep = self.character.add_guild_reputation(cls, data[2])
            self.character.silver += data[3]
            combat_quest = {
                "kind": "kill", "needed": needed, "required_soul_level": 25,
                "repeatable": False,
            }
            guild_stat_xp = v0914_combat_quest_stat_reward(combat_quest)
            await self.grant_combat_quest_stat_xp(
                guild_stat_xp, repeatable=False, source_label="Zadanie klasowe Gildii"
            )
            guild_soul_xp = v0914_combat_quest_soul_reward(combat_quest, self.character)
            await self.send(f"Zadanie klasowe Gildii: +{guild_soul_xp} Soul XP.")
            await self.grant_soul_xp(guild_soul_xp)
            self.server.db.save_character(self.character)
            await self.send(
                f"Ukończono zadanie klasowe: {data[0]}. "
                f"Reputacja {cls} +{data[2]}, waluta +" + currency_reading_text(data[3], 0, 0) + ". "
                f"Reputacja teraz {new_rep}/{GUILD_REPUTATION_MAX}."
            )

    async def guild_exam(self, args=""):
            raw = (args or "").strip()
            active = list(getattr(self.character, "classes", []) or [])
            if not active and getattr(self.character, "class_name", None):
                active = [self.character.class_name]
            if not active:
                await self.send("Nie masz aktywnej klasy.")
                return
            cls = active[0]

            if not raw:
                states = []
                for threshold in GUILD_EXAM_THRESHOLDS:
                    state = "zdany" if self.character.guild_exam_done(cls, threshold) else "niezdany"
                    states.append(
                        f"Soul {threshold}: {state}, wymagana reputacja {GUILD_EXAM_REPUTATION[threshold]}"
                    )
                await self.send(f"Egzaminy {cls}. " + ". ".join(states) + ".")
                return

            try:
                threshold = int(raw.split()[0])
            except Exception:
                await self.send("Użycie: egzamin 50, egzamin 100, egzamin 150 lub egzamin 200.")
                return
            if threshold not in GUILD_EXAM_THRESHOLDS:
                await self.send("Dostępne egzaminy: 50, 100, 150, 200.")
                return
            if self.character.guild_exam_done(cls, threshold):
                await self.send(f"Egzamin Soul {threshold} jest już zdany.")
                return
            if getattr(self.character, "soul_level", 1) < threshold:
                await self.send(f"Ten egzamin wymaga Soul {threshold}.")
                return

            if threshold == 50 and not self.character.guild_class_quest_done(cls):
                await self.send("Najpierw ukończ zadanie klasowe Gildii: zadanieklasowe.")
                return

            required_rep = GUILD_EXAM_REPUTATION[threshold]
            current_rep = self.character.guild_reputation(cls)
            if current_rep < required_rep:
                await self.send(
                    f"Egzamin Soul {threshold} wymaga reputacji {required_rep} w klasie {cls}. "
                    f"Masz {current_rep}. Wykonuj guildbounty i zadania Gildii."
                )
                return

            # Require previous exam except first.
            idx = GUILD_EXAM_THRESHOLDS.index(threshold)
            if idx > 0 and not self.character.guild_exam_done(cls, GUILD_EXAM_THRESHOLDS[idx-1]):
                await self.send(f"Najpierw zdaj egzamin Soul {GUILD_EXAM_THRESHOLDS[idx-1]}.")
                return

            # v0.8.61: koszt egzaminu skaluje się z nową ekonomią jednego salda.
            total_silver_cost = {
                50: 100_000,       # 100 złota
                100: 2_000_000,    # 2 000 złota
                150: 50_000_000,   # 50 000 złota
                200: 250_000_000,  # 250 000 złota
            }[threshold]
            if not self.pay_training_cost(total_silver_cost):
                await self.send(f"Egzamin Soul {threshold} kosztuje " + currency_reading_text(total_silver_cost, 0, 0) + ". Nie masz wystarczającej ilości pieniędzy.")
                return

            self.character.mark_guild_exam_done(cls, threshold)
            reward_rep = {50: 75, 100: 125, 150: 175, 200: 250}[threshold]
            rep = self.character.add_guild_reputation(cls, reward_rep)
            self.server.db.save_character(self.character)
            await self.send(
                f"Zdano egzamin {cls} Soul {threshold}. "
                "Koszt " + currency_reading_text(total_silver_cost, 0, 0) + f". Reputacja +{reward_rep}. "
                f"Reputacja teraz {rep}/{GUILD_REPUTATION_MAX}."
            )

    async def guild_bounty(self, args=""):
            arg = (args or "").strip().casefold()
            state = self.character.guild_bounty_state()
            current = state.get("target")

            if not arg or arg in ("info", "status"):
                if current:
                    target = next((x for x in GUILD_BOUNTY_TARGETS if x[0] == current), None)
                    if target:
                        await self.send(
                            f"Aktywne zlecenie: {target[1]}. "
                            f"Nagroda: reputacja +{target[2]}, waluta +" + currency_reading_text(target[3], 0, 0) + ". "
                            f"Po zabiciu celu użyj: guildbounty odbierz."
                        )
                        return
                lines = ["Tablica zleceń Gildii:"]
                for i, row in enumerate(GUILD_BOUNTY_TARGETS, 1):
                    lines.append(f"{i}. {row[1]} — reputacja +{row[2]}, waluta +" + currency_reading_text(row[3], 0, 0) + ".")
                lines.append("Użyj: guildbounty <numer>.")
                await self.send("\n".join(lines))
                return

            if arg in ("odbierz", "claim"):
                if not current:
                    await self.send("Nie masz aktywnego zlecenia.")
                    return
                # Track kill if generic kill history exists; otherwise allow claim only if marked externally.
                completed = bool(state.get("completed", False))
                if not completed:
                    await self.send("Cel zlecenia nie został jeszcze pokonany.")
                    return
                target = next((x for x in GUILD_BOUNTY_TARGETS if x[0] == current), None)
                if not target:
                    await self.send("To zlecenie jest nieprawidłowe.")
                    return
                active = list(getattr(self.character, "classes", []) or [])
                if not active and getattr(self.character, "class_name", None):
                    active = [self.character.class_name]
                cls = active[0] if active else "Wojownik"
                rep = self.character.add_guild_reputation(cls, target[2])
                self.character.silver += target[3]
                combat_quest = {
                    "kind": "kill", "target": target[0], "needed": 1,
                    "repeatable": True,
                }
                guild_stat_xp = v0914_combat_quest_stat_reward(combat_quest)
                await self.grant_combat_quest_stat_xp(
                    guild_stat_xp, repeatable=True, source_label="Zlecenie bojowe Gildii"
                )
                guild_soul_xp = v0914_combat_quest_soul_reward(combat_quest, self.character)
                await self.send(f"Zlecenie bojowe Gildii: +{guild_soul_xp} Soul XP.")
                await self.grant_soul_xp(guild_soul_xp)
                self.character.set_guild_bounty_state({})
                self.server.db.save_character(self.character)
                await self.send(
                    f"Odebrano nagrodę za {target[1]}. "
                    f"Reputacja {cls} +{target[2]}, waluta +" + currency_reading_text(target[3], 0, 0) + ". "
                    f"Reputacja teraz {rep}/{GUILD_REPUTATION_MAX}."
                )
                return

            try:
                idx = int(arg) - 1
            except Exception:
                await self.send("Użycie: guildbounty, guildbounty <numer>, guildbounty odbierz.")
                return
            if idx < 0 or idx >= len(GUILD_BOUNTY_TARGETS):
                await self.send("Nie ma takiego numeru zlecenia.")
                return
            target = GUILD_BOUNTY_TARGETS[idx]
            self.character.set_guild_bounty_state({
                "target": target[0],
                "completed": False,
            })
            self.server.db.save_character(self.character)
            await self.send(
                f"Przyjęto zlecenie: {target[1]}. "
                f"Nagroda: reputacja +{target[2]}, waluta +" + currency_reading_text(target[3], 0, 0) + "."
            )

    async def show_soul(self, mode=""):
            mode = self.normalize_description_query(mode)
            detailed = mode in (
                "info", "pelne", "pełne", "szczegoly", "szczegóły",
                "details", "progi", "tiers", "tiery", "proby", "próby",
            )
            c = self.character

            if not detailed:
                await self.send("DUSZA")
                await self.send(f"Broń Duszy: {c.soul_weapon}.")
                await self.send(f"Soul Level: {c.soul_level}/{SOUL_MAX_LEVEL}.")
                await self.send(f"Soul Tier: {c.soul_tier}/{SOUL_MAX_TIER}.")
                await self.send(f"Moc Broni Duszy: {c.soul_power()}.")
                if c.soul_level < SOUL_MAX_LEVEL:
                    if c.soul_progress_is_tier_locked():
                        await self.send(
                            f"Soul XP: ZABLOKOWANY na Soul Level {c.soul_level}. "
                            f"Najpierw odblokuj Tier {min(SOUL_MAX_TIER, c.soul_tier + 1)}."
                        )
                    else:
                        await self.send(f"Soul XP: {c.soul_xp} z {c.soul_xp_to_next()}.")
                        await self.send(f"Mnożnik wymaganego Soul XP: x{c.soul_xp_multiplier():.2f}.")
                else:
                    await self.send("Soul XP: maksimum.")
                await self.send(f"Bonus klasowy: {c.soul_weapon_class_bonus_text()}.")
                await self.send(self.soul_next_goal_text())
                await self.send("Wpisz dusza info po wszystkie progi, Próby i status następnego odblokowania.")
                return

            await self.send("DUSZA INFO")
            await self.send("Soul Level jest osobnym rozwojem Broni Duszy 1-400. Nie jest levelem postaci.")
            await self.send("Soul Level zatrzymuje się na progu następnego Tieru. Dalszy Soul XP rusza dopiero po ukończeniu Próby i użyciu unlock.")
            await self.send("Stare progi skilli do 200 odblokuje Biegłość właściwej klasy; sama Biegłość rozwija się do 400, nie Soul Level.")
            await self.send(f"Broń Duszy: {c.soul_weapon}.")
            await self.send(f"Soul Level: {c.soul_level}/{SOUL_MAX_LEVEL}.")
            await self.send(f"Soul Tier: {c.soul_tier}/{SOUL_MAX_TIER}.")
            await self.send(f"Moc Broni Duszy: {c.soul_power()}.")
            if c.soul_level < SOUL_MAX_LEVEL:
                if c.soul_progress_is_tier_locked():
                    await self.send(
                        f"Soul XP: ZABLOKOWANY na Soul Level {c.soul_level}. "
                        f"Najpierw odblokuj Tier {min(SOUL_MAX_TIER, c.soul_tier + 1)}."
                    )
                else:
                    await self.send(f"Soul XP: {c.soul_xp} z {c.soul_xp_to_next()}.")
                    await self.send(f"Mnożnik wymaganego Soul XP: x{c.soul_xp_multiplier():.2f}.")
            else:
                await self.send("Soul XP: maksimum. Soul Level 400.")
            await self.send(f"Bonus klasowy Broni Duszy: {c.soul_weapon_class_bonus_text()}.")
            await self.send(
                "Progi Tierów 1-10: T1 Soul 1; T2 10; T3 20; T4 25; T5 35; "
                "T6 45; T7 60; T8 70; T9 80; T10 90."
            )
            await self.send(
                "Progi Tierów 11-20: T11 Soul 100; T12 110; T13 120; T14 130; "
                "T15 140; T16 150; T17 160; T18 170; T19 180; T20 200."
            )
            await self.send("Każdy Tier od 2 do 40 wymaga własnej jednorazowej Próby Broni Duszy u Kapłana Elora.")
            await self.send("Po ukończeniu Próby wpisz unlock, aby odblokować przygotowany Tier.")

            for tier in range(2, SOUL_MAX_TIER + 1):
                quest_id = SOUL_TRIAL_QUEST_IDS.get(tier)
                quest = QUESTS.get(quest_id, {}) if quest_id else {}
                required_soul = SOUL_TIER_THRESHOLDS[tier - 1]
                row = self.server.db.quest(self.account_id, quest_id) if quest_id else None
                if c.soul_tier >= tier:
                    state = "Tier odblokowany"
                elif row and row["status"] == "completed":
                    state = "Próba ukończona; wpisz unlock"
                elif row and row["status"] == "active":
                    needed = int(quest.get("needed", 1))
                    progress = int(row["progress"])
                    state = f"Próba aktywna; postęp {progress} z {needed}"
                elif c.soul_level < required_soul:
                    state = f"zablokowana do Soul {required_soul}"
                elif c.soul_tier < tier - 1:
                    state = f"najpierw odblokuj Tier {tier - 1}"
                else:
                    state = "dostępna u Kapłana Elora"
                band = quest.get("trial_band", soul_trial_difficulty_band(tier))
                await self.send(f"Tier {tier}. Wymaga Soul {required_soul}. Próba: {band}. {state}.")

            await self.send("KAMIENIE MILOWE BRONI DUSZY")
            for milestone_tier in SOUL_MILESTONE_TIERS:
                state = "aktywne" if c.soul_tier >= milestone_tier else "zablokowane"
                await self.send(f"T{milestone_tier}: {self.soul_milestone_text(milestone_tier)} Stan: {state}.")
            await self.send(self.soul_next_goal_text())
            await self.send(
                "Mityczna Krypta jest dostępna bez progu Soul Level; Mityczna Wieża Astralna nadal wymaga Soul 100. "
                "Nie wymagają ukończenia zwykłej Krypty ani zwykłej Wieży."
            )
            await self.send("Wysokopoziomowe elity i bossowie mogą dawać bardzo duże ilości Soul XP.")
