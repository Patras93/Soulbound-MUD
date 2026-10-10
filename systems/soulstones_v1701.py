# -*- coding: utf-8 -*-
"""Soulbound colored soulstone definitions. Inspired by Alter Aeon, separately balanced."""
SOULSTONE_TIERS = (
    ('czerwony', 'Czerwony Kamień Duszy', 'v1700_soul_stone', 1.00, 1),
    ('zolty', 'Żółty Kamień Duszy', 'v1701_soul_yellow', 1.04, 100),
    ('zielony', 'Zielony Kamień Duszy', 'v1701_soul_green', 1.09, 180),
    ('jasnoniebieski', 'Jasnoniebieski Kamień Duszy', 'v1701_soul_pale_blue', 1.15, 270),
    ('ciemnoniebieski', 'Ciemnoniebieski Kamień Duszy', 'v1701_soul_deep_blue', 1.24, 350),
    ('fioletowy', 'Fioletowy Kamień Duszy', 'v1701_soul_purple', 1.36, 450),
    ('przezroczysty', 'Przezroczysty Kamień Duszy', 'v1701_soul_clear', 1.52, 570),
    ('bialy', 'Biały Kamień Duszy', 'v1701_soul_white', 1.73, 670),
    ('czarny', 'Czarny Kamień Duszy', 'v1701_soul_black', 2.00, 780),
)
STONE_ALIASES = {'red':'czerwony','yellow':'zolty','green':'zielony',
    'paleblue':'jasnoniebieski','pale':'jasnoniebieski',
    'deepblue':'ciemnoniebieski','deep':'ciemnoniebieski',
    'purple':'fioletowy','clear':'przezroczysty',
    'white':'bialy','black':'czarny',
    'jasny':'jasnoniebieski','ciemny':'ciemnoniebieski',
    'bezbarwny':'przezroczysty'}
STONE_BY_KEY = {tier[0]: (i, tier) for i, tier in enumerate(SOULSTONE_TIERS)}
