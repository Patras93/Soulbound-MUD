SOULBOUND MUD v102.00.5 - INSTRUKCJA ADMIN LIVE (POLSKI)
=======================================================
Data: 24.10.2026. Pelna paczka Windows, kandydat do PREDEPLOY 60/60 PLUS.
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
W grze: admin live pomoc 57 ... admin live pomoc 76
Pomoc 57-59: taktyki UOSS 2.0, Quest Doctor, poprawki rozwoju.
Pomoc 60-64: kreator skilli, naprawy questow, rozszerzenia Admin Live.
Pomoc 65-69: wzorce skilli, audyt questow, postacie online, arena LAB, AI.
Pomoc 70-73: mechaniki i rozwój online (level/EXP, wpisy, symulacja).
Pomoc 74: prawdziwa arena UOSS przez izolowany tunel.
Pomoc 75: dodatkowe warunki aktywacji mechanik.
Pomoc 76: przeglad i audyt wszystkich modulow Admin Live.

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
