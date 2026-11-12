# Soulbound v113.00.8 — poprawka aktywacji po PREDEPLOY

Wersja pelna. NIE WDRAZAC przed nowym pelnym Windows PREDEPLOY 60/60 PLUS,
dodatkowymi bramkami i testami uniwersalnymi dla TEGO ZIP-a.
Wersja v113.00.7 przerwala wdrozenie przed automatycznym STOP i backupem,
poniewaz kod aktywacji kandydata zawieral SyntaxError. Poprawiono
aktywacje i dodano rzeczywisty test procesu. Zachowano automatyczny STOP,
bezpieczny backup SQLite i wybrane dwie stale komendy BAT.
Szczegoly i wyniki w CHANGELOG_PL.txt.

---

# Soulbound v113.00.5 — pełne źródła, paczka robocza

**NIE WDRAŻAĆ** przed Windows PREDEPLOY 60/60 PLUS wraz z bramkami dodatkowymi. 
Poprawka izoluje historyczny test NPC/Elora w osobnym procesie i nie wymaga
żadnych poprzednich wersji gry ani aktywatorów. Szczegóły: `CHANGELOG_PL.txt`.
Po pełnym PASS używać wyłącznie stałych `PREDEPLOY_NOWEJ_WERSJI.bat`
i `WDROZ_PO_PREDEPLOY.bat`, z potwierdzeniem `WDRAZAM`.
Po wdrożeniu gra musi być samowystarczalna bez katalogu PREDEPLOY.

---

# Soulbound MUD v113.00.1 — pełne źródła

Paczka robocza. **NIE WDRAŻAĆ** bez wyniku Windows PREDEPLOY 60/60 PLUS na izolowanej kopii zapisów.

Gra i instalator korzystają z jednego pliku `VERSION`. Główne mechaniki używają wspólnego `systems/runtime_activation.py`. Aktualizacje nowych wydań korzystają z dwóch stałych BAT: `PREDEPLOY_NOWEJ_WERSJI.bat` i `WDROZ_PO_PREDEPLOY.bat`.

Nie kopiować starych modułów gry do nowej wersji. Postacie i ekwipunek są przenoszone wyłącznie z zatwierdzonej kopii danych SQLite/WAL i ustawień. Istniejąca instalacja pozostaje bez zmian.

Pełny opis zmian i faktycznie wykonanych testów: `CHANGELOG_PL.txt`.

Kontynuacja audytu: naprawiono konflikt backupu z katalogiem logs oraz wykonano testy 14/14 PASS i dwa cykle TCP sześciu graczy. Bieżący ZIP jest pełną paczką źródeł, nie aktualizacją produkcyjną. Po stronie użytkownika nie należy jeszcze uruchamiać WDROZ_PO_PREDEPLOY.bat bez zatwierdzonego Windows 60/60 PLUS.


## Kontrola po logu Windows v113 — ważne

Oryginalna paczka v113 miała wynik Windows **49/60 PASS** i **11 FAIL**.
Niniejsza paczka zawiera poprawki. Na odizolowanej **syntetycznej** bazie
poprawione etapy 9/19/24/25/26/31/49/50/60 przeszły 9/9 PASS; dodatkowe
bramki v105 zostały przetestowane osobno. Nie jest to dowód certyfikacji
Windows na prawdziwych zapisach. **Nie wdrażaj** przed nowym PREDEPLOY.

Stałe dwa BAT pozostają uniwersalne. Nie kopiuj ani nie uruchamiaj
historycznych instalatorów, nie usuwaj katalogu PREDEPLOY przed wdrożeniem.


## Poprawka 113.00.1
Poprzedni Windows PREDEPLOY v113.00.0: 58/60 PASS, 2 FAIL. Naprawiono kwalifikację Over Cap bossa powyżej poziomu 800 oraz bezpieczną autoryzację dodatkowej izolowanej areny TCP. Pakiet nadal **NIE WDRAŻAĆ** do czasu nowego 60/60 PLUS PASS. Szczegóły i wyniki w `CHANGELOG_PL.txt`.


## Poprawka 113.00.2
Poprzedni Windows PREDEPLOY: 58/60 PASS; niedozwolony wyjątek w Over Cap
oraz przycinanie tool_tier do poziomu 800. Te dwa problemy poprawiono.
NIE WDRAŻAĆ do czasu nowego rzeczywistego Windows 60/60 PLUS PASS.
