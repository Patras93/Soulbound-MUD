# -*- coding: utf-8 -*-
"""v115 content catalog: 30 authored regions and endless tier descriptors.

Read-only definitions. No world mutation until separately integrated and tested.
"""
from __future__ import annotations
from dataclasses import dataclass

REGION_NAMES = (
    'Bramy Wiecznego Świtu', 'Pustkowia Srebrnego Popiołu',
    'Lodowe Archiwum', 'Sanktuarium Złamanych Gwiazd',
    'Rubinowe Rozpadliny', 'Ogrody Pamięci', 'Cytadela Ostatniej Burzy',
    'Podziemne Morze', 'Żelazna Nekropolia', 'Dolina Płonących Liści',
    'Wieże Błękitnego Pioruna', 'Korona Północnych Olbrzymów',
    'Zatopione Obserwatorium', 'Księżycowy Bastion', 'Szkarłatna Otchłań',
    'Szlak Zapomnianych Karawan', 'Wrota Czarnego Słońca',
    'Szmaragdowe Labirynty', 'Piekielny Rozstaj', 'Kryształowe Katakumby',
    'Pola Echa', 'Kamienne Serce Świata', 'Bezkresny Przestwór',
    'Cmentarzysko Tytanów', 'Wieczny Las Widm', 'Marmurowy Tron',
    'Głębia Zegarów', 'Świątynie Gwiezdnego Pyłu',
    'Przepaść Milczących Bogów', 'Horyzont Bez Końca',
)

@dataclass(frozen=True)
class Region:
    key: str
    name: str
    suggested_level: int
    biome: str

BIOMES=('ruiny','pustynia','lodowiec','astral','kanion','las','twierdza','ocean','krypta','dolina')
REGIONS = tuple(Region(f'v115_region_{i:02d}', name, 800 + (i-1)*3500, BIOMES[(i-1)%len(BIOMES)])
                for i,name in enumerate(REGION_NAMES,1))
REGION_BY_KEY={r.key:r for r in REGIONS}

def dynamic_region(region_key: str, depth: int):
    """Return deterministic descriptors; does not impose entry level gates."""
    if region_key not in REGION_BY_KEY:
        raise ValueError('Nieznana kraina')
    if isinstance(depth,bool) or not isinstance(depth,int) or depth < 1 or depth > 1_000_000_000:
        raise ValueError('Nieprawidłowa głębokość')
    region=REGION_BY_KEY[region_key]
    level=region.suggested_level + (depth-1)*100
    return {'key':f'{region_key}:depth:{depth}', 'region':region_key,
            'name':f'{region.name} — głębokość {depth}', 'suggested_level':level,
            'biome':region.biome, 'entry_locked':False}
