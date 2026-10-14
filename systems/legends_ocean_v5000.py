# -*- coding: utf-8 -*-
"""Audible, per-fleet encounter rhythms for the five existing Imperial fleets.
No new ships, commands, currencies or SQLite tables. Legacy fleets unchanged.
"""
CYCLES = {
 'imperium_widm':(4, 148, 'Widmowe żagle zaciskają pierścień wokół floty.'),
 'imperium_lewiatanow':(5, 165, 'Lewiatan przygotowuje głębinowy wir.'),
 'imperium_koron':(6, 172, 'Zatopione działa tronu przygotowują salwę.'),
 'imperium_raf':(3, 138, 'Bursztynowe rafy kierują prąd pod kadłuby.'),
 'imperium_sztormow':(5, 181, 'Dziewięć sztormów łączy piorunowy front.'),
}

def ocean_hazard(enemy, turn, command):
    spec = CYCLES.get(enemy)
    if spec is None:
        return 100, ''
    period, strength, attack = spec
    if turn % period == 0:
        return strength, attack + ' Osłona i manewr ograniczają straty.'
    if (turn + 1) % period == 0:
        return 100, 'UWAGA: następna tura! ' + attack + ' Rozważ osłonę albo manewr.'
    return 100, ''
