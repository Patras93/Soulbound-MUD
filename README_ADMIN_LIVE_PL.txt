SOULBOUND MUD v102.00.12 - INSTRUKCJA ADMIN LIVE (POLSKI)
=======================================================
Data: 28.10.2026. Pelna paczka Windows, kandydat do PREDEPLOY 60/60 PLUS.
Ten plik zastępuje 8 historycznych README. Szczegoly dawnych aktualizacji
sa w CHANGELOG_PL.txt. Nie oznacza to, ze gra zostala wdrozona.

1. NAJWAZNIEJSZE PLIKI WINDOWS
- PREDEPLOY_NOWEJ_WERSJI.bat - testy przed wdrozeniem
- WDROZ_PO_PREDEPLOY.bat - wdrozenie DOPIERO po wyniku PASS 60/60 PLUS
- START_Soulbound.bat / STOP_Soulbound.bat - uruchomienie / zatrzymanie
- BACKUP_TERAZ_Soulbound.bat - kopia zapasowa
- CHANGELOG_PL.txt - historia wersji wymagana przez test identyfikatora
- VERSION - numer paczki i kontroli wydania

2. ADMIN LIVE - GDZIE JEST CO
W grze: admin live pomoc 57 ... admin live pomoc 77
Pomoc 57-59: taktyki UOSS 2.0, Quest Doctor, poprawki rozwoju.
Pomoc 60-64: kreator skilli, naprawy questow, rozszerzenia Admin Live.
Pomoc 65-69: wzorce skilli, audyt questow, postacie online, arena LAB, AI.
Pomoc 70-73: mechaniki i rozwój online (level/EXP, wpisy, symulacja).
Pomoc 74: prawdziwa arena UOSS przez izolowany tunel.
Pomoc 75: dodatkowe warunki aktywacji mechanik.
Pomoc 76: przeglad i audyt wszystkich modulow Admin Live.
Pomoc 77: globalne skalowanie potworow (Adaptive Combat).

3. PRZYKLADOWE KOMENDY
admin live audyt
admin live audyt raport
admin live audyt komendy
admin live audyt olc
admin live audyt arena
admin live questy doktor skan
admin live questy doktor analiza temple_rats
admin live skill kreator wzorce
admin live postacie online rozwoj karta Gracz
admin live postacie online wpisy plan Gracz | klasa:Wojownik=20,0
admin live mechaniki karta black_rabite
admin live boss uoss taktyka karta black_rabite

OLC: plan trafia do DRAFT. Dokonaj walidacji (admin live sprawdz),
a publikacje przeprowadz przez admin live aktywuj POTWIERDZAM.
Nie wolno publikowac zmian podczas ryzykownych dzialan lub aktywnej walki.

4. REALNA ARENA UOSS (POMOC 74)
admin live arena real start POTWIERDZAM
admin live arena real status
admin live arena real tunel POTWIERDZAM
[Zaloguj sie do izolowanej kopii gry w tym samym kliencie MUD.]
arena wyjdz
admin live arena real stop POTWIERDZAM

Tunel przeprowadza komendy do pelnego silnika w osobnym procesie na
127.0.0.1:4900, na kopii bazy, bez prawdziwych nagrod czy obrazen postaci.
W tunelu moze byc potrzebne osobne konto testowe. Nie otwieraj portu
areny publicznie. Arena LAB (pomoc 72) to symulacja, NIE walka 1:1.

5. SKILLE I MECHANIKI (POMOC 60, 65, 70, 75)
Mozliwe sa tylko sprawdzone przez silnik typy efektow: nie uruchamia
sie dowolnego kodu Python, eval ani skryptow przeslanych przez administratora.
Dla faz bossow dostepne sa planowane reguly celu, czasu, HP/many i drużyny.
Po zatwierdzeniu DRAFT i publikacji OLC zmiany dzialaja bez restartu.

6. POSTACIE I QUESTY (POMOC 61-67, 71, 73)
Poprawki online wymagaja postaci poza walka i wylaczonych automatyzacji.
Korekty w pamieci sesji i SQLite zabezpiecza kontrola konfliktow i rollback.
Ekwipunek zalozony, chronione przedmioty i nieistniejace wpisy sa blokowane.
Quest Doctor daje diagnozy; naprawy wymagaja planu i zatwierdzenia.

7. BEZPIECZNE WDROZENIE WINDOWS
1) Utworz kopie bazy i WAL (przez narzedzie BACKUP lub bezpieczny backup SQLite).
2) Umiesc pelny ZIP w NOWE_WERSJE bez recznego przepakowywania.
3) Uruchom PREDEPLOY_NOWEJ_WERSJI.bat, odczekaj na wynik wszystkich etapow.
4) Wymagane: WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS.
5) Jesli FAIL, NIE WDRAZAJ. Napraw przyczyne i ponow PREDEPLOY na nowym ZIP.
6) Po PASS wykonaj wdrozenie standardowym skryptem i test NVDA w kliencie.

8. ZAKRES TESTOW
Folder validation zawiera historyczne i aktualne regresje, wymagane przez
PREDEPLOY. Nie usuwaj plikow validation, Python, BAT ani CHANGELOG.
Testy nie zastępuja odbioru funkcji w zywej grze.

W v102.00.5 dodano bezpieczne sprzatanie historycznych README podczas instalacji.
Jesli aktualizujesz ze starego instalatora v96, porzadkowanie wykona sie
przy pierwszym uruchomieniu gry po aktualizacji. Osiem starych README
zniknie z glownego folderu; ich kopie beda w katalogu Soulbound_BACKUP_README_*
obok folderu gry, np. w C:\Soulbound_BACKUP_README_*. Zachowane sa aktualny
README, CHANGELOG, baza, konfiguracja, logi oraz prywatne dokumenty.
Nie usuwa sie calych katalogow ani innych README po wzorcu.
Wymagany nowy PREDEPLOY 60/60 PLUS; kod walki bez zmian.
Bez GitHuba.

9. WYLACZENIE AUTOMATYCZNEGO SKALOWANIA POTWOROW v102.00.6
admin live pomoc 77
admin live skalowanie status
admin live skalowanie off
admin live skalowanie on
Komendy dostepne tylko administratorowi. OFF dotyczy WSZYSTKICH graczy
od razu, rowniez przeciwnikow w trwajacych starciach. HP potworow wraca
do wartosci z szablonu, bez przywracania utraconego odsetka zdrowia.
Brak adaptacyjnego wzrostu obrazen zalezne od HP gracza lub druzyny;
zwykla potega bossow, poziomy regionow i pietra lochow zostaja.
Premia do EXP/waluty zwiazana WYLACZNIE z Adaptive Combat wraca do x1.
Wybor zapisuje sie w LIVE_CONTENT/adaptive_combat_global_v102006.json.
Nie usuwaj tego pliku po zmianie. Domyslny ON zachowuje historyczny
balans do chwili, gdy administrator uzyje admin live skalowanie off.
Po zmianie ZIP wymagane PREDEPLOY 60/60 PLUS.

10. EXP BIEGLOSCI I DUSZY ZA 3 ZLECENIA Z WALKI (v102.00.7)

Dostepne dokladne ID questow (NIE liczba 53 z listy):
  haldor_steel_recycling           Zlecenie Haldora: Stal do Przetopu
  haldor_broken_blades_v0929      Zlamane ostrza
  haldor_armor_recycling_v0929    Pancerz do przetopu

Przyklad ustawienia obu nagrod dla Pancerza do przetopu:
  admin live edytuj quest haldor_armor_recycling_v0929 xp_bieglosci | KWOTA
  admin live edytuj quest haldor_armor_recycling_v0929 xp_duszy | KWOTA
  admin live sprawdz
  admin live porownaj
  admin live aktywuj POTWIERDZAM

Przy innych dwoch questach zamien ID na odpowiednie z powyzszej listy.
KWOTA musi byc liczba calkowita >=0 wybrana przez administratora.
Sprawdz aktualne wartosci przed i po:
  admin live quest haldor_armor_recycling_v0929

Nie zmieniaj kind z collect na kill. Cele, loot, pochlanianie przedmiotow,
czas odnowienia oraz wszystkie istniejace nagrody pieniezne pozostaja bez zmian.
W trzech powyzszych questach EXP Bieglosci i Duszy sa wyplacane po oddaniu,
tylko jesli zostaly jawnie ustawione przez admina. W zwyklych questach
profesyjnych EXP Duszy pozostaje zerowy.

11. ADMIN LIVE EXPPROGI - HURTOWA KOREKTA DODATNICH NAGROD QUESTOW v102.00.8
Podglad nie zmienia niczego:
  admin live expprogi podglad xp_statystyk 1000
Przyklad przygotowania DRAFT (liczby wybierasz sam):
  admin live expprogi ustaw xp_statystyk 1000 25000
  admin live expprogi podglad xp_postaci 1000
  admin live expprogi ustaw xp_postaci 1000 12000
  admin live expprogi podglad wszystkie 1000
Pola: xp_postaci, xp_bieglosci, xp_duszy, xp_statystyk, xp_profesji,
xp_narzedzia, xp_sila, xp_zrecznosc, xp_kondycja, xp_inteligencja,
xp_wola, xp_charyzma, wszystkie.
Zmienia tylko bazowe dodatnie nagrody mniejsze od PROGU, niczego nie
narzuca z gory. Brak/zero EXP i nagrody >=PROGU pozostaja bez zmian.
W przypadku zwyklych questow profesji nie dopisuje bojowego EXP Bieglosci.
Trzy zlecenia Haldora na lupy z walki zachowuja wczesniejszy wyjatek.
Przyblednej komendzie poprzednie zmiany robocze pozostaja nietkniete.
Po zmianach: admin live sprawdz; admin live porownaj;
admin live aktywuj POTWIERDZAM. Przed publikacja mozna wpisac admin live anuluj.
Po publikacji nowe EXP sa nagrodami BAZOWYMI; dalsze modyfikatory EXP/CAP
pozostaja zgodne z zasadami silnika. Testuj na wybranych questach.

12. OPTYMALIZACJA DIAGNOSTYKI v102.00.9
admin komendy wolne - ostatnie 100 zapisanych wolnych pomiarow. Po wdrozeniu nowe wpisy craft i quit pomijaja celowe oczekiwanie na recepture lub menu, historyczne dane nie sa usuwane. Dodatkowy wpis [PERF QUESTACCEPT] pojawi sie w logach gdy przyjmowanie trwa ponad 250 ms. Nie rejestruje surowych argumentow komend.

13. NAPRAWA PRZYJMOWANIA QUESTOW v102.00.10
Naprawiono blad NameError _accept_db_v102009 w czasie przyjmowania questa, kiedy diagnostyka czasowa przekracza 250 ms.
Jesli poprzednio pojawil sie blad po komunikacie Quest przyjety, sprawdz aktywne questy: baza mogla juz zapisac zadanie.
Nie trzeba ponownie przyjmowac aktywnego questa. Nie zmieniono limitow ani wartosci nagrod.

14. CENTRUM NAPRAW ADMIN LIVE 1.0 (v102.00.11)
admin live bledy lista 20
admin live bledy pokaz SB-XXXXXXXX
admin live bledy diagnoza SB-XXXXXXXX
admin live napraw SB-XXXXXXXX
admin live napraw sprawdz SB-XXXXXXXX NICK QUEST_ID
admin live napraw zastosuj SB-XXXXXXXX NICK QUEST_ID POTWIERDZAM
admin live napraw cofnij NUMER_KOREKTY POTWIERDZAM

Odczyt i diagnoza nigdy nic nie zmieniaja. Automatyczna korekta jest dostepna
WYŁĄCZNIE dla ujemnego postepu aktywnego zadania gracza OFFLINE, z istniejacym
zapisem historii i kontrola konfliktow (CAS). Korekta podnosi ujemny postep
do zera. Numer korekty z odpowiedzi sluzy do cofniecia, jesli od tego czasu
postep sie nie zmienil i gracz nadal jest offline.

Numer SB NIE okresla, kto ma bledny quest, ani nie dowodzi przyczyny.
NameError, AttributeError, bledy importu i inne usterki samego kodu wymagaja
przetestowanej poprawki kodu i (zwykle) wdrozenia; Centrum Napraw nie wykonuje
arbitralnego Pythona, nie nadpisuje plikow i nie restartuje serwera.
Komenda naprawy NIE zamyka automatycznie zgloszenia SB. Po przetestowaniu
przyczyny: admin blad naprawiony SB-XXXXXXXX (osobna swiadoma decyzja).
Brak zmian EXP, balansu, zawartosci questow, danych innych graczy i DRAFT OLC.


15. LIMITY PO AKTUALIZACJI (v102.00.12)
- Zapis administratora: LIVE_CONTENT\admin_level_caps.json (chroniony przez aktualizator ZIP).
- Od v102.00.12 kazda przyszla wersja >= v52 automatycznie wczytuje zapisane limity przy starcie.
- admin live limity: sprawdza aktywne limity w RAM.
- admin live limity wczytaj POTWIERDZAM: odczytuje ponownie plik bez restartu.
- admin live limity wszystkie bezlimitu POTWIERDZAM: TRWALE ustawia 10 kategorii, jesli taka jest decyzja wlasciciela.
- Uwaga: ulepszenia_eq domyslnie +10, wiec uzycie 'wszystkie' zmienia rowniez ten limit.

16. EXP PONAD 800 (v102.00.12)
- Do poziomu 800 wartosci nagrod, wymagan, CAP i Bank EXP bez zmian.
- Poziom 801+ (gdy admin odblokuje limity) nadal ma rosnace wymagania EXP.
- Awaryjny per-award EXP CAP w testowych/starych bazach takze rosnie ponad 800.
- Produkcyjne Multi Cap pozostaje suma postepu postaci, Duszy, biegłości, statystyk, profesji, narzedzi i skilli.
- Half CAP, Overcap i bankowanie nadwyzek EXP pozostaja aktywne, nie kasujemy banku.
- SQLite nadal ogranicza pojedyncze wartosci liczbowe (int64); nie jest to limit poziomu 800.

17. NAGRODY EXP QUESTOW BEZ SYMBOLICZNYCH WARTOSCI (v102.00.12)
- Kazdy zwykly quest daje min. 200 000 bazowego EXP postaci i dla kazdej z szesciu statystyk. Prawdziwe uzyskane punkty podlegaja mechanice CAP, bankowania i premiom.
- Quest walki daje min. 200 000 bazowego EXP Bieglosci i Duszy; zadania profesji nie dostaja automatycznie EXP Duszy ani Bieglosci.
- Quest z kontekstem profesji/narzedzia daje min. 200 000 bazowego XP w tych osiach (nie w dowolnej profesji bez odpowiedniego narzedzia).
- Wyjatkowe trzy zlecenia Haldora z lupami nadal wymagaja osobnego uprawnienia OLC do EXP Bieglosci i Duszy; ustawiona wartosc dodatnia podlega nowemu minimum.
- Wyplata liczona w chwili oddania, wyswietlana przez quests na ekranie informacji. Zapisane w bazie nagrody OLC nie sa nadpisywane.
- admin live expprogi nadal edytuje zapisane surowe wartosci w DRAFT; wartosci ponizej minimum maja przy wyplacie podniesiona podstawe.

18. SWIAT, KRYPTY I WIEZE v102.00.12
- Dodatkowa stala presja: swiat +20% HP, +22% obrazen, +40% EXP walki. Inne instancje sa mocniejsze.
- Zwykle Krypty: dodatkowy mnoznik EXP x1.9, Mityczne Krypty x2.2.
- Wieza Astralna: dodatkowy mnoznik EXP x2.0, Mityczna x2.3.
- Zmiany dzialaja w statycznych i leniwie generowanych pietrach, takze bossach.
- Przelicznik EXP odbiorcy w kryptach/wiezach rowniez podniesiony; zabezpieczenie wczesnych poziomow (brak przeskakiwania wielu leveli jednym zabiciem) pozostaje.
- No adaptive: zapisane `admin live skalowanie off` NIE jest w zmienionych plikach ani automatycznie wlaczane.
- Wylacznie pliki wydania, bez danych graczy. Wymagany Windows PREDEPLOY 60/60 PLUS.
