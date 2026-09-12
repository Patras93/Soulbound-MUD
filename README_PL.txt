WDROŻENIE RAILWAY: przeczytaj RAILWAY_PL.txt.

SOULBOUND v0.5 RAILWAY READY
=============================

To jest pierwsza prawdziwa wieloosobowa wersja Soulbound.

NAJWAŻNIEJSZE
--------------
- Serwer TCP/Telnet.
- Domyślny port: 4000.
- Działa z MUSHclientem, Mudletem i podobnymi klientami MUD.
- Wielu graczy może być online jednocześnie.
- Domyślny limit programu: 100 jednoczesnych połączeń.
- Konta i postacie są przechowywane po stronie serwera w SQLite.
- Hasła nie są zapisywane jako zwykły tekst. Są hashowane PBKDF2-SHA256.
- Nie potrzeba żadnej zewnętrznej biblioteki Pythona.

WAŻNE O HASŁACH
---------------
Klasyczne połączenie Telnet nie szyfruje ruchu sieciowego.
Serwer bezpiecznie hashuje hasła w bazie, ale przy zwykłym Telnecie samo wpisanie
hasła może przechodzić przez sieć bez szyfrowania. Na publiczny duży serwer
docelowo dodamy TLS lub bezpieczną bramę.

SYSTEM POSTACI
--------------
Postać NIE ma levelu i NIE ma XP postaci.

Klasy fizyczne automatycznie rozwijają:
- Siłę,
- Zręczność,
- Kondycję.

Inteligencja i Siła Woli klasom fizycznym nie rosną.

Klasy magiczne automatycznie rozwijają:
- Inteligencję,
- Siłę Woli.

Nie ma ręcznego rozdawania punktów.

BROŃ DUSZY
----------
Broń Duszy ma własny, niezależny system:
- Soul Level 1-100,
- osobne Soul XP,
- Tier 1 od początku,
- Tier 2 do odblokowania od Soul Level 25,
- Tier 3 do odblokowania od Soul Level 60.

Tier nie odblokowuje się sam. Używa się komendy:
unlock

URUCHOMIENIE NA WINDOWS
-----------------------
W katalogu gry:
python server.py

Następnie MUSHclient:
adres: 127.0.0.1
port: 4000

URUCHOMIENIE NA LINUX / ORACLE CLOUD
------------------------------------
1. Zainstaluj Python 3:
sudo apt update
sudo apt install -y python3

2. Skopiuj katalog Soulbound na serwer.

3. Wejdź do katalogu:
cd Soulbound_v0.4_Online_Server

4. Uruchom:
python3 server.py

Serwer nasłuchuje na:
0.0.0.0:4000

5. W Oracle Cloud trzeba zezwolić na ruch przychodzący TCP 4000
w regułach sieciowych instancji.

6. Jeżeli Ubuntu ma aktywny UFW:
sudo ufw allow 4000/tcp

7. Gracze wpisują w MUSHclient:
adres: publiczny adres IP instancji
port: 4000

PRACA 24/7 PRZEZ SYSTEMD
------------------------
W paczce jest plik:
soulbound.service.example

Skopiuj go do:
/etc/systemd/system/soulbound.service

Przed użyciem popraw ścieżki User, WorkingDirectory i ExecStart.

Następnie:
sudo systemctl daemon-reload
sudo systemctl enable --now soulbound
sudo systemctl status soulbound

Logi:
journalctl -u soulbound -f

AKTUALIZACJE GRY
----------------
Baza danych soulbound.db jest oddzielona od kodu.
Przy przyszłych aktualizacjach nie usuwaj pliku soulbound.db.

Typowa aktualizacja:
1. Zatrzymaj serwer:
sudo systemctl stop soulbound

2. Zrób kopię:
cp soulbound.db soulbound.db.backup

3. Wgraj nowe pliki kodu.

4. Uruchom:
sudo systemctl start soulbound

KOMENDY W GRZE
--------------
help
look
north / south / east / west
n / s / e / w
who
say tekst
tell gracz tekst
stats
soul
fight
unlock
save
quit

PIERWSZY ŚWIAT
--------------
- Plac Dusz
- Dziedziniec Treningowy
- Kuźnia Dusz
- Gaj Szeptów
- Północna Brama

Walka treningowa jest dostępna na Dziedzińcu Treningowym.

PLIKI
-----
server.py
  Główny serwer MUD.

soulbound.service.example
  Przykładowa usługa systemd dla Linux/Oracle Cloud.

start_linux.sh
  Prosty start na Linux.

start_windows.bat
  Prosty start na Windows.

README_PL.txt
  Ten dokument.

CHANGELOG_PL.txt
  Historia wersji.
