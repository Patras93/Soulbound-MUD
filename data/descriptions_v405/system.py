"""Katalog opisow system w wersji 4.00.5."""

def make_system_descriptions_v405():
    """Build the original v4.00.4 SYSTEM_DESCRIPTIONS data as a fresh dictionary."""
    return {
        "wędkarstwo": (
            "Wędkarstwo ma własny poziom profesji. Do połowu potrzebna jest Wędka, która ma "
            "osobny level od 1 bez stałego końca i osobny XP. Podstawową Wędkę kupisz u Rybaka Borysa na Targu Rybnym. "
            "Użyj fish albo low. Auto-łowienie: low on i low off. "
            "Czas połowu zależy od Wędkarstwa: 16 sekund na poziomie 1 i minimum 3 sekundy na poziomie 200."
        ),
        "wedkarstwo": (
            "Wędkarstwo ma własny poziom profesji. Do połowu potrzebna jest Wędka, która ma "
            "osobny level od 1 bez stałego końca i osobny XP. Podstawową Wędkę kupisz u Rybaka Borysa na Targu Rybnym. "
            "Użyj fish albo low. Auto-łowienie: low on i low off. "
            "Czas połowu zależy od Wędkarstwa: 16 sekund na poziomie 1 i minimum 3 sekundy na poziomie 200."
        ),
        "fishing": "Wędkarstwo ma własny poziom profesji od 1 bez stałego końca, a Wędka własny niezależny level od 1 bez stałego końca. Podstawową Wędkę sprzedaje Rybak Borys. Czas połowu spada z 16 do minimum 3 sekund wraz z poziomem Wędkarstwa.",
        "górnictwo": (
            "Górnictwo ma własny poziom od 1 bez stałego końca. Kilof ma osobny level od 1 bez stałego końca. "
            "Użyj mine albo kop. Auto-kopanie: kop on i kop off. "
            "Mithril jest walutą i może wypaść jako dodatkowy bonus od Kilofa 80, Górnictwa 80 i poziomu kopalni 80. "
            "Od Kilofa 20 mogą wypadać geody; open geode / otwórz geodę otwiera je na klejnoty."
        ),
        "gornictwo": (
            "Górnictwo ma własny poziom od 1 bez stałego końca. Kilof ma osobny level od 1 bez stałego końca. "
            "Mithril jest walutą i może wypaść jako dodatkowy bonus od Kilofa 80, Górnictwa 80 i poziomu kopalni 80."
        ),
        "mining": "Górnictwo ma własny poziom od 1 bez stałego końca i do 200 skraca czas wydobycia; Kilof ma niezależny level od 1 bez stałego końca i odblokowuje lepsze rudy/żyły.",
        "jubilerstwo": (
            "Jubilerstwo ma własny level od 1 bez stałego końca. "
            "Szczypce Jubilerskie mają niezależny level od 1 bez stałego końca i kolejne Tiery bez stałego końca. "
            "Biżuterię wykonujesz w Pracowni Jubilerskiej u Mirelli."
        ),
        "jewelcrafting": (
            "Jubilerstwo od 1 bez stałego końca. Narzędzie: Szczypce Jubilerskie od 1 bez stałego końca. "
            "Receptury tworzą pierścienie i naszyjniki."
        ),
        "broń duszy": (
            "Broń Duszy jest na stałe związana z klasą. Ma Soul XP, katalog 1000 Tierów i progi Soul Level do 10000 (Soul Level rozwija się także powyżej 800). "
            "Od v0.9.0 bazowa Moc startowa klas mieści się w zakresie 7-8, a dalsza przewaga wynika z Soul Levelu, Tieru i specjalizacji klasy. "
            "Łotrzyk otrzymuje z Broni Duszy mieszany bonus: umiarkowany unik oraz obrażenia fizyczne, żeby progres nie był marnowany na limicie 35 procent uniku. "
            "Każdy awans Soul Tieru 2–1000 wymaga jednorazowej Próby Broni Duszy u Kapłana Elora. "
            "Trudność rośnie pasmami: T2-4 Początkująca, T5-7 Poszukiwacza, T8-12 Weterana, T13-20 Mistrzowska, T21-40 endgame."
        ),
        "bron duszy": "Broń Duszy ma 1000 Tierów, progi Soul Level do 10000 i Soul Level rozwija się powyżej 800.",
        "soul weapon": "Broń Duszy ma 1000 Tierów, progi Soul Level do 10000 i Soul Level rozwija się powyżej 800.",
        "próby duszy": (
            "Próby Broni Duszy odblokowują Tiery 2–1000 u Kapłana Elora. "
            "Pasma trudności: T2-4 Początkująca, T5-7 Poszukiwacza, T8-12 Weterana, "
            "T13-20 Mistrzowska, T21-30 Endgame, T31-40 Ekstremalna. "
            "Pierwsze siedem Tierów nie wymagają bossów Krypty; od T8 pojawiają się bossowie regionalni, "
            "a ciężkie Próby Krypty zaczynają się od T13. Użyj dusza info, aby sprawdzić stan każdej Próby."
        ),
        "proby duszy": "Próby Broni Duszy: Tiery 2–1000 u Elora. Dalsze strony: quest list Elor 801. Użyj dusza info.",
        "soul trials": "Próby Broni Duszy: Tiery 2–1000 u Elora. Dalsze strony: quest list Elor 801. Użyj dusza info.",
        "srebro": "Srebro jest najmniejszym nominałem wspólnej waluty. 100 srebra = 1 złoto.",
        "silver": "Srebro jest najmniejszym nominałem wspólnej waluty. 100 srebra = 1 złoto.",
        "złoto": "Złoto jest wyższym nominałem tego samego salda. 1 złoto = 100 srebra.",
        "zloto": "Złoto jest wyższym nominałem tego samego salda. 1 złoto = 100 srebra.",
        "gold": "Złoto jest wyższym nominałem tego samego salda. 1 złoto = 100 srebra.",
        "mithril": (
            "Mithril jest najwyższym nominałem tego samego wspólnego salda. "
            "1 mithril = 1 000 000 złota = 100 000 000 srebra. "
            "Może być nagrodą lub bardzo rzadkim bezpośrednim wydobyciem wysokopoziomowym Kilofem."
        ),
        "siatka": "Siatka na ryby jest osobnym trwałym magazynem profesji. Komenda siatka/net pokazuje też łączną liczbę ryb, liczbę gatunków i szacowany zarobek ze sprzedaży całej zawartości. Sprzedaż ryb właściwym rybakom daje dodatkowy EXP Wędkarstwa.",
        "net": "Siatka na ryby przechowuje wszystkie złowione ryby i pokazuje łączną liczbę ryb oraz wartość sprzedaży całej siatki.",
        "sakwa": "Sakwa Górnika przechowuje cały urobek Górnictwa: rudy, minerały, klejnoty wszystkich jakości oraz geody. Całą zawartość skupuje wyłącznie Dagna na Górskim Targu Minerałów. Sprzedaż Dagnie daje dodatkowy EXP Górnictwa; geody możesz zamiast tego otwierać.",
        "bag": "Sakwa Górnika przechowuje rudy, minerały, surowe klejnoty i geody. Dagna jest jedynym skupującym zawartość sakwy; geody otwierasz przez open geode / otwórz geodę.",
        "śmierć": (
            "Po śmierci postać odradza się w Świątyni Odrodzenia i traci 10 procent "
            "wartości wspólnego salda."
        ),
        "smierc": "Po śmierci postać odradza się w Świątyni Odrodzenia i traci 10 procent wartości wspólnego salda.",
        "death": "Po śmierci postać odradza się w Świątyni Odrodzenia i traci część waluty.",
    }
