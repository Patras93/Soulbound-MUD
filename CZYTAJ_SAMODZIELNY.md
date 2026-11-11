# Soulbound v112 — samodzielny bieżący silnik

Ta wersja nie wymaga instalacji, aktywatorów ani plików wykonywalnych starszych wydań. Wszystkie 158 modułów startowych mają jawne zależności. Funkcje i metody są zwykłym kodem Python, bez klonowania FunctionType i wstrzykiwania wspólnych globali. Nazwy starych ID przedmiotów, questów, tabel i mechanik pozostają dla zachowania zawartości oraz zgodności danych.

## Nowa instalacja Windows

Uruchom `INSTALUJ_SAMODZIELNY.bat` w katalogu źródeł. Domyślnym celem jest nowy katalog `Soulbound-Samodzielny` obok źródeł. Możesz też podać nieistniejący katalog:

```powershell
python -m systems.current_install install --target "C:\Gry\Soulbound-Samodzielny"
```

Instalator wykonuje obowiązkowe testy bieżących źródeł, rzeczywisty test sześciu klientów i restartu, porównanie 33 katalogów z materiałem sprzed przebudowy oraz inicjalizację nowej pustej bazy. Kopiuje aktualny runtime wraz z zasobami binarnymi i bazą stref czasowych. Zapisuje manifest integralności SHA256 i wyników walidacji. Nie korzysta z zaświadczenia poprzedniej wersji, starego instalatora ani starej bazy. Istniejący katalog celu jest odrzucany przed wykonaniem instalacji.

Następnie w nowym katalogu uruchom `START_Soulbound.bat` lub `python server.py`. Zwykły port gry to 4000. Same źródła bez manifestu instalacji nie uzyskują automatycznej zgody na bazę produkcyjną. Flaga staging nie zastępuje instalacji.

## Istniejące zapisy

Nowy instalator tworzy wyłącznie pustą grę. Nie służy do nadpisywania serwera ani przenoszenia zapisów graczy. Historyczne narzędzia aktualizacji i ich zabezpieczenia pozostawiono w pełnych źródłach jako osobną ścieżkę. Bieżąca gra nie importuje dawnych aktywatorów ani dawnych binderów. Nie należy zastępować istniejącej bazy pustą bazą z nowej instalacji.

## Testy i architektura

`python -m systems.current_install validate` uruchamia bramki bez publikowania nowego katalogu. Instalacja powtarza walidację, sprawdza SHA256 przed i po testach i odmawia kontynuowania po zmianie źródeł.

Kolejność finalizacji świata jest jawna: specjalne połączenia aren są domykane po topologii, a końcowy balans waluty po wszystkich warstwach świata. HELP ma jawne katalogi fazy autorskiej i fazy gry. Trzynaście nadpisywanych reguł ma wąski interfejs kompozycji `core/runtime_rules.py`; żaden katalog ani dowolna zmienna nie trafiają do tej usługi.

Pełne źródła zawierają także historyczne testy offline. Do nowej instalacji nie są kopiowane aktywatory v107–v111 ani 74 pliki dawnego łączenia kodu. Ich obecność w archiwum źródeł nie jest wymogiem uruchomienia aktualnej gry.

Dockerfile przygotowuje samodzielną grę w osobnym etapie za pomocą tego samego instalatora, bez obrazu starszej wersji. Testy tej dostawy wykonano na Windows z Python 3.14; budowa obrazu Linux wymaga odrębnego sprawdzenia w środowisku Docker.

## Porządek w archiwum źródeł

Niewykorzystywane skrypty `sprawdz_v104_zbiorczo.py` i `_debug_boot_local.py` przeniesiono do osobnego archiwum `SOULBOUND_V112_ARCHIWUM_NARZEDZI_20261111.zip`. Nie są potrzebne grze ani instalacji. Pozostałe materiały regresyjne i narzędzia aktualizacji zachowano ze względu na ich odwołania w testach. Szczegóły: `PORZADEK_ZRODEL.md` na najwyższym poziomie ZIP-a.
