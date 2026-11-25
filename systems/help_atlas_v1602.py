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


def install_help_atlas_v1602(topics, aliases, tool_profession_map=None):
    names = sorted(set((tool_profession_map if tool_profession_map is not None else TOOL_PROFESSION_MAP).values()))
    caps = {CHARACTER_MAX_LEVEL, CLASS_MASTERY_MAX_LEVEL, PROFESSION_MAX_LEVEL,
            SKILL_MAX_LEVEL, SOUL_MAX_LEVEL, SOUL_WEAPON_MASTERY_MAX_LEVEL, TOOL_MAX_LEVEL}
    if caps != {800}:
        raise RuntimeError('HELP v1.60.2: oczekiwano wspólnego limitu poziomów 800, odczytano '+str(caps))
    if len(names) < 14:
        raise RuntimeError('HELP v1.60.2: brak kompletu historycznych 14 profesji')

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
        'Zawody podstawowe: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Kowalstwo, Gotowanie, Alchemia, Jubilerstwo, Krawiectwo, Garbarstwo, Stolarstwo, Zaklinanie, Archeologia i Kartografia. Nowe: Łowiectwo, Rolnictwo, Hodowla zwierząt, Okrętownictwo, Murarstwo, Inżynieria, Kupiectwo, Żeglarstwo.',
        'atlas profesje — katalog profesji; atlas profesje <nazwa> — NPC, narzędzia, zadania, receptury i komendy.',
        'profesje info / narzedzia info — poziomy, XP i rangi. Zamowienia — rotujące kontrakty; zamowienie porzuc — porzucenie.',
        'Receptury i koszty: receptury <profesja>, receptury mozliwe, braki receptura <nazwa>, gdzie zdobyc <przedmiot>.',
        'Tempo czynności sprawdzaj w help tempo_profesji; premie za dobre materiały i wyjątkowe zbiory nadal działają.',
    ]
    topics['profesje6'] = [
        'Nowe zawody — osobne narzędzia od poziomu 1 do 800.',
        'profesja lista — nazwy, narzędzia i czynności; profesja status <nazwa> — rozwój.',
        'profesja kup <nazwa> — zakup narzędzia tylko raz na postać; profesja czynnosci <nazwa> — możliwe prace.',
        'profesja praca <nazwa> <czynność> [próg] — wykonaj pracę i zdobądź EXP.',
        'profesja zamowienie <nazwa> oraz profesja oddaj <nazwa> — zlecenia i nagrody.',
    ]
    topics['atlas'] = [
        'atlas / atlas odkrycia — Globalny Atlas świata: regiony, miasta, wyspy, lochy, platformy, ruiny, superbossy i sekrety.',
        'atlas profesje — wszystkie profesje. atlas profesje <nazwa> — NPC, zadania, warsztat i aktualne receptury.',
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
        'lochy50 pokazuje opis systemu. walk dol prowadzi do zejścia i zatrzymuje przed przejściem piętra.',
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
        'walk dol — automatyczne dojście do zejścia w podziemiach i lochach, bez wykonania ostatniego kroku.',
        'walk gora / walk góra — dojście do wejścia wyżej w wieżach, z zatrzymaniem przed przejściem piętra.',
        'Przed wejściem na kolejne piętro użyj exits i wybierz właściwy kierunek.',
    ]
    topics['zamowienia'] = [
        'zamowienia / zamówienia — aktywne i rotujące kontrakty dawnych profesji i nowe zamówienia: profesja zamowienie <nazwa>.; nagrody zostały podniesione w v1.40.6.',
        'zamowienie porzuc — porzuca aktywny kontrakt bez usuwania posiadanych materiałów i bez kasowania historii.',
        'Nowa oferta ma własną wypłatę i EXP; wcześniej przyjęta zachowuje nagrodę zapisaną przy przyjęciu.',
    ]
    aliases.update({
        'górnictwo':'gornictwo', 'górnik':'gornictwo', 'kopanie':'gornictwo',
        'wędkarstwo':'wedkarstwo', 'żeglarstwo':'profesje6',
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



def refresh_current_help_v11320(topics, aliases):
    """Actual current command/help contracts, applied after every historical overlay.

    Pure in-place data repair; do not change class rules, equipment or database.
    Historical topic keys remain valid for old users and bookmarks.
    """
    # The early 1.60.2 installer still validates authored 800 defaults.
    # This final overlay runs *after* dawny edytor loads persisted limits and
    # after the v107 default-unlimited migration.  Never reject legitimate
    # production caps just because they differ from the authoring baseline.
    from core.live_level_caps_v5200 import current as current_live_caps
    live_caps = current_live_caps()
    axes = ('postac', 'bieglosc', 'dusza', 'bron_duszy',
            'skille', 'profesje', 'narzedzia')
    if not all((live_caps.get(axis) is None or
                (type(live_caps[axis]) is int and 1 <= live_caps[axis] <= 10_000_000))
               for axis in axes):
        raise RuntimeError('HELP: niepoprawne aktywne progi rozwoju')

    def cap_text(axis):
        value = live_caps[axis]
        return 'bez limitu' if value is None else str(value)
    from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP
    from core.classes_skills import CLASSES
    from systems.new_professions import PROFESSIONS as NEW_PROFESSIONS
    professions = sorted(set(TOOL_PROFESSION_MAP.values()))
    assert len(professions) >= 16 and len(NEW_PROFESSIONS) == 8
    assert len(CLASSES) >= 22
    topics['progresja800'] = [
        ('Aktualne progi rozwoju: postać '+cap_text('postac')+
         ', Biegłość klasy '+cap_text('bieglosc')+
         ', Soul '+cap_text('dusza')+
         ', Broń Duszy '+cap_text('bron_duszy')+
         ', skille '+cap_text('skille')+
         ', profesje '+cap_text('profesje')+
         ', narzędzia '+cap_text('narzedzia')+'.'),
        'Komenda admin live limity pokazuje bieżące wartości. Bez limitu oznacza brak twardego limitu poziomu, nie darmowe poziomy.',
        'Statystyki podstawowe nie mają twardego limitu. Postęp sprawdzisz w score, staty info, dusza info, profesje info i narzedzia info.',
    ]
    # Historical help keys remain valid, but show the current values.
    topics['progresja600'] = list(topics['progresja800'])
    topics['multiclass'] = [
        f'W aktualnej grze postać ma JEDNĄ klasę główną, wybraną przy tworzeniu. Dostępnych klas: {len(CLASSES)}.',
        f'multiclass lub klasy pokazuje klasę główną i Biegłość (limit: {cap_text("bieglosc")}).',
        'multiclass add/remove/switch są wyłączone. Nie da się dodać ani przełączyć drugiej aktywnej klasy.',
        'Historia starszych klas i ich poziomy pozostają w zapisie SQLite, ale nie dają dodatkowych skilli, pasywów ani EXP.',
        'Multi Cap klasy liczy tylko bieżącą klasę. Profesje i narzędzia rozwijają się niezależnie.',
        f'Nauczyciele i wyposażenie klasowe wymagają klasy głównej; help klasy — aktualny katalog {len(CLASSES)} klas.'
    ]
    topics['klasy'] = [
        f'Soulbound ma {len(CLASSES)} grywalnych klas. Jedną klasę główną wybiera się na stałe w kreatorze postaci.',
        'Do nowych klas należą: Paladyn, Samuraj, Korsarz, Gladiator, Chronomanta, Iluzjonista, Bard i Szaman.',
        f'Biegłość aktywnej klasy: limit {cap_text("bieglosc")}. Pomoc umiejętności: help skill <nazwa>; spis: kodeksklasowy wszystkie.',
        'multiclass pokazuje aktywną klasę. Dodawanie i przełączanie klas jest wyłączone; historyczny zapis innych klas pozostaje bez bonusów.',
        'classguild / guildquest — zadania i mistrzostwo klasowe. Nauczyciel uczy umiejętności tylko dla aktywnej klasy.',
        'W kreatorze możesz wrócić do wyboru rasy poleceniem 0, wroc lub rasy.'
    ]
    topics['atlas'] = [
        f'atlas — działy świata i surowców. atlas profesje — katalog wszystkich profesji ({len(professions)}).',
        'atlas profesje <nazwa> — aktualna specjalizacja, narzędzie, czynności i zadania (w tym osiem nowych profesji).',
        'atlas odkrycia [regiony|miasta|wyspy|lochy|platformy|ruiny|superbossy|sekrety] — postępy odkrywania.',
        'atlas ryby / atlas rzeka / atlas jezioro / atlas morze / atlas ocean — ryby według rodzaju wody.',
        'atlas rudy / atlas geody / atlas drewno / atlas zioła — wymagania narzędzi i surowce.',
        'atlas <nazwa surowca> — miejsca, progi narzędzia i dostępność w bieżącym katalogu.',
        'Komendy atlasu nie teleportują i nie zmieniają zapisów postaci.'
    ]
    topics['profesje'] = [
        f'W grze jest {len(professions)} profesji i {len(TOOL_PROFESSION_MAP)} narzędzi. Limit profesji: {cap_text("profesje")}; narzędzi: {cap_text("narzedzia")}.',
        'Osiem nowszych: Łowiectwo, Rolnictwo, Hodowla zwierząt, Okrętownictwo, Murarstwo, Inżynieria, Kupiectwo, Żeglarstwo.',
        'atlas profesje — kompletny katalog; atlas profesje <nazwa> — opis jednej profesji.',
        'profesje info i narzedzia info — poziomy i EXP. Nowe czynności: profesja czynnosci <nazwa>, pracuj <nazwa> <czynność> [próg].',
        'Każda profesja i odpowiadające narzędzie mają oddzielne EXP i poziomy; zadania i receptury zależą od konkretnych wymagań.'
    ]
    topics['kodeks_klasowy'] = [
        f'kodeksklasowy wszystkie / classcodex all — aktualny katalog {len(CLASSES)} klas i ich umiejętności.',
        'kodeksklasowy <klasa> — umiejętności, wymagana Biegłość, nauczyciel i koszty.',
        'kodeksklasowy moje — umiejętności bieżącej klasy głównej; inne klasy nie są aktywne.',
        'Przy tworzeniu postaci wybierasz jedną klasę, której nie można potem przełączać.'
    ]
    topics['bizuteria_klasowa'] = [
        'Klasowe pierścienie i naszyjniki istnieją dla klas, które mają je w aktualnym katalogu wyposażenia.',
        'Korzystanie z przedmiotu wymaga zgodności z JEDNĄ aktywną klasą postaci, nie z historyczną multiklasą.',
        'Załóż pierścień / załóż naszyjnik; szczegóły przedmiotu: opis <nazwa> i porownaj <nazwa>.',
        'Gniazda i klejnoty są osobne dla każdego noszonego elementu.'
    ]
    if 'sklepy_klasowe' in topics:
        topics['sklepy_klasowe'] = [s for s in topics['sklepy_klasowe']
                                  if 'Multiclass działa' not in s]
        topics['sklepy_klasowe'][0] = f'Klasowe sklepy wyposażenia: {len(CLASSES)} klas dostępnych w aktualnym świecie.'
        topics['sklepy_klasowe'].append(
            'Obecnie można używać wyłącznie wyposażenia JEDNEJ klasy głównej; archiwalne klasy nie odblokowują innych sklepów ani EQ.')
    topics['przypisane'] = [
        'Broń Duszy i poziomy narzędzi pozostają przypisane do konkretnej postaci.',
        f'W grze jest {len(TOOL_PROFESSION_MAP)} profesjonalnych narzędzi, po jednym na profesję.',
        f'Każde narzędzie kupuje się raz; rozwija własny level i EXP (limit: {cap_text("narzedzia")}).',
        'Nie można przekazywać poziomów narzędzi pomiędzy postaciami.'
    ]
    topics['tempo_profesji'] = [
        f'Wszystkie {len(professions)} profesje mają limit {cap_text("profesje")}.',
        'Czas konkretnej czynności i wymagania materiałowe zależą od jej profesji i poziomu.',
        'Nowe osiem profesji ma osobne czynności, koszty i progi; zobacz profesja czynnosci <nazwa>.',
        'Narzędzia rozwijają się niezależnie i mogą wpływać na jakość, zbiór i skuteczność działania.'
    ]
    for key in ('narzedzia200','wolniejszy_xp_narzedzi'):
        if key in topics:
            topics[key] = [
                f'Aktualny limit narzędzi: {cap_text("narzedzia")}. Nazwa tematu jest historyczna; stare progi pozostają etapami progresji.',
                'Poziom i aktualny wymagany EXP sprawdzaj przez narzedzia info / tools; progi i premie wynikają z rzeczywistego narzędzia.',
                'Atlas profesje oraz atlas <nazwa surowca> pokazują potrzebne narzędzia i wymagania.'
            ]
    topics['soul200'] = [
        f'Soul ma limit {cap_text("dusza")}, a Biegłość Broni Duszy {cap_text("bron_duszy")}; nazwa help soul200 pozostała dla kompatybilności.',
        'Próby Soul Tier i wymagania bossów pozostają w aktualnych systemach. Postęp: dusza info.',
        'Każdy awans Soul Level zapewnia rozwój Broni Duszy zgodnie z obecną progresją.'
    ]
    topics['endgame_profesje'] = [
        f'Limit profesji: {cap_text("profesje")}; narzędzi: {cap_text("narzedzia")}. Starsze surowce i receptury nadal mają swoje progi.',
        'Wędka: atlas ryby; Kilof: atlas rudy / atlas geody; Piła: atlas drewno; Sierp: atlas zioła.',
        'Receptury <profesja> pokazują aktualne wymagania profesji, narzędzia i materiałów.'
    ]
    if 'gotowanie_rozbudowane' in topics:
        topics['gotowanie_rozbudowane'] = [
            f'Gotowanie — limit: {cap_text("profesje")}; Nóż Kucharski — limit: {cap_text("narzedzia")}. Starsze progi receptur są zachowane.',
            'gotuj lista / receptury gotowanie — aktualne receptury i wymagania.',
            'Gotuj <nazwa> — przygotowanie potraw z właściwych magazynów i inventory.',
            'Poziom Gotowania wpływa na czas; Nóż rozwija się osobno i wpływa na wykonanie.'
        ]
    for key in ('nawigacja','krypta','druzyny','walk'):
        old = list(topics.get(key, ()))
        if key == 'krypta':
            old = [s for s in old if 'prowadz krypta prowadzi tylko' not in s]
            old.extend([
                'walk krypta dol prowadzi do następnego zejścia, z ochroną prowadzonej drużyny.',
                'Zabite moby znikają z listy żywych; ciało pozostaje do 10 minut, nieodebrane EQ leży potem na ziemi do 30 minut.',
                'ziemia — zobacz łup; podnies <nr|nazwa> / wez <nazwa> — podnieś przedmiot.',
                'Upiory Krypty z głębszych pięter także zaliczają zadanie wymagające upiorów.'
            ])
        else:
            old.append('Podczas szybkiego prowadzenia lider nie przechodzi dalej, gdy członek drużyny walczy lub pozostaje w poprzedniej lokacji.')
            old.append('Zgubiony członek drużyny: teleport to leader / tp lider — ręczny powrót do lidera, poza walką i bez omijania bram bossów.')
        topics[key] = old
    topics['teleport_to_leader'] = [
        'teleport to leader / tp lider — gracz w drużynie przenosi się do swojego lidera.',
        'Nie działa w walce ani przez niezaliczoną bramę bossa. Nie przemieszcza automatycznie pozostałych graczy.',
        'Przy szybkim marszu lider zatrzymuje się, gdy ktoś został z tyłu. Po zebraniu drużyny można wznowić prowadzenie.'
    ]
    topics['ziemia'] = [
        'Zabity mob znika z listy żywych. Jego ciało można przeszukać przez 10 minut.',
        'Po rozkładzie ciała nieodebrane przedmioty leżą na ziemi przez następne 30 minut.',
        'ziemia — lista; podnies <numer|nazwa>; wez <nazwa> lub wez wszystko — podnoszenie.',
        'przeszukaj <numer>.cialo — zawartość ciała; klucze bossów pozostają na ciele.'
    ]
    # Correct only present-tense claims. Historical 14-/22-class milestones
    # (quests from older eras, dated patch notes) retain their real history.
    from core.classes_skills import RACES
    replacements = {
        '14 klas': f'{len(CLASSES)} klas',
        '22 klas': f'{len(CLASSES)} klas',
        '14 grywalnych ras': f'{len(RACES)} grywalnych ras',
        '22 ras': f'{len(RACES)} ras',
        '22 profesji': f'{len(professions)} profesji',
    }
    for key in ('podstawy','rasy','umiejetnosci','skille','zadania klasowe',
                'zadanieklasowe','class quests','sety_klasowe','cyborg',
                'rasa_czlowiek','rasa_ogr','rasa_elf','rasa_krasnolud',
                'rasa_ork','rasa_niziolek','rasa_mroczny_elf','rasa_gnom',
                'rasa_smok','rasa_troll','rasa_diable','rasa_aasimar',
                'rasa_driada','rasa_cyborg','rasa_wampir','rasa_wilkolak',
                'rasa_minotaur','rasa_tryton','rasa_feniksjanin','rasa_dzin',
                'rasa_kitsune','rasa_krysztalowiec'):
        if key not in topics:
            continue
        fresh=[]
        for sentence in topics[key]:
            for old,new in replacements.items():
                sentence=sentence.replace(old,new)
            fresh.append(sentence)
        topics[key]=fresh
    if 'mana_stats_eq' in topics:
        topics['mana_stats_eq'] = [sentence.replace(
            'Klasa magiczna albo multiclass magiczny', 'Postać klasy magicznej')
            for sentence in topics['mana_stats_eq']]
    if 'naturalne_uzyj' in topics:
        topics['naturalne_uzyj'] = [sentence.replace(
            'w multiclassie', 'dla aktywnej klasy')
            for sentence in topics['naturalne_uzyj']]
    topics['tempo_profesji'] = [sentence.replace(
        f'Wszystkie {len(professions)} profesje',
        f'Wszystkie {len(professions)} profesji')
        for sentence in topics['tempo_profesji']]
    aliases.update({'multiklasa':'multiclass', 'multiklasowosc':'multiclass',
                    'teleport to leader':'teleport_to_leader', 'tp lider':'teleport_to_leader',
                    'tp leader':'teleport_to_leader', 'zagubiony':'teleport_to_leader',
                    'ziemia':'ziemia', 'podnies':'ziemia', 'podnieś':'ziemia',
                    'atlasy':'atlas'})
    return {'professions': len(professions), 'classes': len(CLASSES),
            'topics': len(topics)}
