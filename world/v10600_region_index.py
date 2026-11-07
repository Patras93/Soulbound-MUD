# -*- coding: utf-8 -*-
"""v106 — unikalne krainy 30001–60000, bez modyfikacji zakresu v105."""
REGION_ROWS = (
    ('przedmurze','Przedmurze Pękniętych Gwiazd','Strażnik Zerwanej Granicy','Władca Pęknięcia'),
    ('eter','Dolina Wypalonego Eteru','Wędrowiec Żaru','Wypalony Archont'),
    ('kometa','Kuźnie Białej Komety','Żelazny Meteor','Kowal Białej Komety'),
    ('czas','Ogrody Utraconego Czasu','Strażnik Klepsydry','Ogrodnik Wieków'),
    ('firmament','Brama Rozdartego Firmamentu','Herold Rozdarcia','Sędzia Nieba'),
    ('wyspy','Wyspy Milczących Pływów','Sternik Ciszy','Pan Pustych Fal'),
    ('ksiezyce','Zatoka Martwych Księżyców','Księżycowy Rozbitek','Admirał Zmierzchu'),
    ('latarnia','Latarnia Zapomnianych Żeglarzy','Strażnik Latarni','Wieczny Nawigator'),
    ('szklo','Głębie Szklanej Burzy','Szklany Łowca','Serce Sztormu'),
    ('wir','Tron Błękitnego Wiru','Podwodny Herold','Władca Błękitnego Wiru'),
    ('schody','Schody Bez Imion','Archiwista Schodów','Bezimienny Strażnik'),
    ('biblioteka','Biblioteka Żywych Run','Żywa Księga','Mistrz Żywych Run'),
    ('krypta','Krypta Wiecznych Szeptów','Milczący Skryba','Władca Szeptów'),
    ('przysiegi','Miasto Utraconych Przysiąg','Strażnik Przysięgi','Sędzia Zapomnienia'),
    ('pamiec','Sanktuarium Pękniętej Pamięci','Cień Wspomnień','Strażniczka Pamięci'),
    ('lustra','Pustynia Czarnych Luster','Pustynny Odbity','Władca Czarnych Luster'),
    ('korony','Twierdza Pustych Koron','Żołnierz Bez Króla','Pusty Monarcha'),
    ('swit','Katedra Zatrzymanego Świtu','Kapłan Zmierzchu','Wieczny Świt'),
    ('most','Most Wygasłych Konstelacji','Gwiezdny Strażnik','Kartograf Pustki'),
    ('palac','Pałac Nienazwanych Władców','Dworski Cień','Władca Bez Imienia'),
    ('mroz','Ścieżka Mroźnej Fali','Lodowy Pielgrzym','Matka Mroźnej Fali'),
    ('jezioro','Pęknięte Jezioro Dusz','Utopiona Dusza','Strażnik Dusz'),
    ('kuznie','Tysiąc Kuźni Zorzy','Kowal Zorzy','Przedwieczny Hutnik'),
    ('korzenie','Szklisty Las Korzeni','Szklisty Druid','Korzeń Zorzy'),
    ('krag','Krąg Zaginionych Prób','Strażnik Kręgu','Mistrz Ostatecznej Próby'),
    ('echa','Miasto Ostatnich Ech','Ostatnie Echo','Królewna Echa'),
    ('czelusc','Czeluść Obcych Gwiazd','Obcy Posłaniec','Serce Obcej Gwiazdy'),
    ('cisza','Wysoki Ogród Ciszy','Ogrody Milczenia','Niemowa Niebios'),
    ('cytadela','Żywa Cytadela Wielu Światów','Żywy Bastion','Władca Wielu Światów'),
    ('serce','Serce Astralnego Przebudzenia','Zwiastun Przebudzenia','Astralny Przebudzony'),
)
REGIONS = tuple((slug,name,30001+i*1000,31000+i*1000,b1,b2)
                for i,(slug,name,b1,b2) in enumerate(REGION_ROWS))
assert len(REGIONS)==30 and REGIONS[0][2]==30001 and REGIONS[-1][3]==60000
assert len({x[0] for x in REGIONS})==len({x[1] for x in REGIONS})==30
