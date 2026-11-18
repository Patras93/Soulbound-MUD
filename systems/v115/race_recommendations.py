# -*- coding: utf-8 -*-
"""v115: recommendations for v110 races left with empty lists.

Recommendations guide creation only; they never grant a class or change a saved build.
"""
RECOMMENDED = {
    'Rezonanci': (('Mag','Psionik','Wirtuoz Echa'), 'Inteligencja i bonus do magii wspierają ataki magiczne i rezonans.'),
    'Lustrzanie': (('Łotrzyk','Iluzjonista','Fantomowy Szermierz'), 'Zręczność i unik sprzyjają szybkim, zwodniczym stylom walki.'),
    'Zarodnikowcy': (('Druid','Kapłan','Szeptacz Bestii'), 'Wysoka Siła Woli i bonus leczenia wspierają naturę oraz wsparcie drużyny.'),
    'Zaranie': (('Strażnik','Paladyn','Runiczny Obrońca'), 'Kondycja i redukcja obrażeń pozwalają skuteczniej osłaniać drużynę.'),
    'Selenici': (('Mag','Chronomanta','Szaman'), 'Inteligencja i dodatkowa Mana wspierają klasy korzystające z zaklęć.'),
    'Głębinowcy': (('Strażnik','Korsarz','Strażnik Przypływów'), 'Odporność fizyczna i Kondycja pomagają przetrwać trudne starcia.'),
    'Miedzianie': (('Inżynier','Runiczny Obrońca','Strażnik'), 'Obrona magiczna sprzyja technicznym i defensywnym klasom; '),
    'Żarborny': (('Berserker','Gladiator','Żarowy Żniwiarz'), 'Siła i bonus obrażeń fizycznych wspierają ofensywę.'),
}

def recommendation_for(race_name, available_classes):
    entry = RECOMMENDED.get(str(race_name))
    if entry is None:
        return None
    names, reason = entry
    visible = [name for name in names if name in available_classes]
    return {'classes': visible, 'reason': reason} if visible else None
