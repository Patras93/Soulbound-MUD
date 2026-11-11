"""Skalowanie EXP i waluty, niezalezne od zapisu SQLite."""
from .policy import gift_kind

def reward_plan(day, master, character):
    """Deterministic, varying gold/EXP; every advent gift > any normal daily."""
    kind = gift_kind(day)
    master = int(master)
    if master <= 0:
        raise ValueError('Missing master account')
    level = max(1, int(character.character_level))
    needed = max(0, int(character.character_xp_to_next()))
    variant = (day.toordinal() + master % 29) % 5
    if kind == 'daily':
        coin = 3500 + variant * 2600 + min(15000, level * 8)
        exp = min(10**15, max(10000, needed // (14-variant)))
    else:
        coin = 130000 + (day.day - 1) * 5500 + variant * 17000
        exp = min(3 * 10**15, max(120000, needed // (4 if variant < 3 else 3)))
        if day.day in (6, 24):
            coin *= 2
            exp = min(3 * 10**15, exp * 2)
    return dict(kind=kind, silver=int(coin), exp=int(exp), variant=variant)
