# Soulbound MUD v113.00.18 — LINUX, pełna gra

**Status: KANDYDAT. NIE WDRAŻAĆ bez PASS Linux PREDEPLOY 60/60 PLUS na komputerze kolegi.**

Jedna kompletna paczka Linux, bez BAT, CMD, VBS ani PowerShell.
Mechanika gry pochodzi z Windows v113.00.18: quest Upiór Krypty Velsal,
EXP Bank i Over Cap, Jammer automatyczny/Support/AoE, wiadomości dla drużyny
i wiadomość o zakończeniu Jammera. Autostart Windows nie jest funkcją Linux.

Linux potrzebuje Python 3.11+, bash, unzip. Serwer: TCP **4000**,
limit **6 rzeczywistych graczy**, bez wpływu na TeamTalk na innym porcie.

### Pierwsza instalacja

1. Przenieś tę pełną paczkę ZIP na Linux; rozpakuj ją bez zmiany nazwy folderu `Soulbound-MUD`.
2. Jeśli chcesz zachować dane, dostarcz **spójną kopię** `soulbound.db`
   do `Soulbound-MUD/IMPORT_BAZY/soulbound.db`. Nie dołączamy baz kont ani postaci.
   Jeżeli baza Windows korzysta z WAL, wykonaj backup przez API SQLite
   przy zatrzymanej grze; nie kopiuj samego pliku DB podczas zapisu.
3. W folderze `Soulbound-MUD` uruchom `PREDEPLOY_NOWEJ_WERSJI.sh`.
   Testy nie nadpisują źródłowej bazy; potrzebny jest PASS 60/60 PLUS,
   uniwersalne 20/20 i Linux, EQ i 6 graczy TCP.
4. Po PASS uruchom `WDROZ_PO_PREDEPLOY.sh` i wpisz `WDRAZAM`.
5. Do działania w tle: `INSTALUJ_USLUGE_LINUX.sh` (systemd --user).
   Do administracji: `START_Soulbound.sh`, `STOP_Soulbound.sh`, `STATUS_Soulbound.sh`.

### Aktualizacja istniejącego Linux Soulbound

Jeżeli poprzednia wersja była zainstalowana przez instalator Soulbound Linux
w `$HOME/Soulbound-Linux/current`, aktualizator wykryje jej bazę automatycznie.
Najpierw wykonaj kopię bezpieczeństwa i zakończ wszystkie sesje graczy.
Jeśli starsza wersja działa w innym miejscu, nie kasuj ani nie zastępuj jej
folderu: podaj do skryptów zmienną `SOULBOUND_IMPORT_DB` wskazującą
spójną kopię starej bazy, poza nowym folderem. Nie uruchamiaj obydwu
serwerów jednocześnie na tym samym porcie.

Oba etapy (PREDEPLOY, WDROŻENIE) wykorzystują **dokładnie ten sam ZIP**.
Wynik PASS dla Windows nie upoważnia do instalacji Linux.
Po instalacji można usunąć tymczasowy PREDEPLOY; gra od niego nie zależy.
Szczegóły w `CZYTAJ_LINUX_PL.txt`, historia w `CHANGELOG_PL.txt`.

Jeżeli TeamTalk już działa na serwerze, nie zmieniaj jego usługi, portów ani
konfiguracji. Program Linux nie zatrzymuje żadnych obcych procesów.
