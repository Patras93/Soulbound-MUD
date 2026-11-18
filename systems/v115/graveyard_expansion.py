# -*- coding: utf-8 -*-
"""v115: rzeczywista rozbudowa Starego Cmentarza bez zamiany starych pokoi.

Stale 64 identyfikatory; ruch w siatce oraz droga powrotna do graveyard.
"""

WIDTH = HEIGHT = 8
ANCHOR = "graveyard"
PREFIX = "v115_graveyard_"


def room_id(x, y):
    return f"{PREFIX}{x:02d}_{y:02d}"


def build_rooms(existing):
    anchor = existing.get(ANCHOR)
    if not anchor:
        raise ValueError("Brakuje oryginalnego Starego Cmentarza")
    if "up" in anchor.get("exits", {}):
        raise ValueError("Górne wyjście Starego Cmentarza jest zajęte")
    created = {}
    names = ("Aleja Nagrobków", "Stary Kwaterunek", "Grobowy Trakt", "Złamany Mur",
             "Zarośnięte Mogiły", "Kamienny Krąg", "Ogród Ciszy", "Zapomniane Groby")
    for y in range(HEIGHT):
        for x in range(WIDTH):
            rid = room_id(x,y)
            if rid in existing:
                raise ValueError("Kolizja lokacji: " + rid)
            exits = {}
            if x: exits["west"] = room_id(x-1,y)
            if x < WIDTH-1: exits["east"] = room_id(x+1,y)
            if y: exits["south"] = room_id(x,y-1)
            if y < HEIGHT-1: exits["north"] = room_id(x,y+1)
            if (x,y)==(0,0): exits["down"] = ANCHOR
            created[rid] = {
                "zone": "Stary Cmentarz", "name": names[(x+3*y)%len(names)],
                "desc": "Rozległa część Starego Cmentarza. Nagrobki i boczne ścieżki prowadzą w głąb nekropolii.",
                "exits": exits, "generator_level": 12 + (x+y)//3,
                "exploration_ep": 12 + (x+y)//2 if (x+y)%2==0 else 0,
                "v115_legacy_expansion": "graveyard", 
            }
    return created


def build_spawns():
    # W istniejącym katalogu oba typy istnieją; brak wymyślonych mobów.
    return [(room_id(x,y), "skeleton") for y in range(HEIGHT) for x in range(WIDTH)
            if (x+y)%2==0]
