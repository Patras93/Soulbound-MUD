# -*- coding: utf-8 -*-
"""Dalsze stopnie po 800 — stateless, no save migrations, no level cap.
Historical ranks 1..800 remain owned by the original catalogue.
"""
from __future__ import annotations


def profession_rank_v10300(level, historical_count):
    level = max(1, int(level or 1))
    return historical_count + max(0, (level - 800) // 20)


def next_profession_rank_level_v10300(rank, historical_count):
    rank=int(rank)
    if rank <= historical_count:
        raise ValueError('Progi historyczne musza pochodzić z oryginalnej tabeli.')
    return 800 + 20*(rank-historical_count)


def profession_rank_name_v10300(profession, rank, historical_count):
    if rank <= historical_count:
        raise ValueError('Nie zmieniaj historycznych nazw rang.')
    return f'Arcymistrz Nowej Ery {rank-historical_count} — {profession}'


def tool_tier_v10300(level, historical_count):
    level=max(1,int(level or 1))
    return historical_count + max(0,(level-800)//10)


def tool_tier_level_v10300(tier, historical_count):
    tier=int(tier)
    if tier<=historical_count:
        raise ValueError('Historyczne progi narzedzi trzeba odczytac z tabeli.')
    return 800 + 10*(tier-historical_count)


def tool_tier_bonus_v10300(tier, historical_count, historical_bonus):
    tier=int(tier)
    if tier<=historical_count:
        return historical_bonus[tier-1]
    return min(0.95,round(float(historical_bonus[-1]) + (tier-historical_count)*0.0005,4))
