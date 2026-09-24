# -*- coding: utf-8 -*-
"""Soulbound v0.55.0 - courier prestige packages and expanded courier achievements."""

POSTAL_REFRESH_SECONDS_V0522 = 15 * 60
POSTAL_OFFERS_PER_CITY_V0522 = 5

POSTAL_CITY_HUBS_V0522 = {
    "Miasto Dusz": "courier_office",
    "Brzozowy Trakt": "birch_square",
    "Żelazne Bramy": "iron_square",
    "Twierdza Popiołu": "ash_square",
    "Port Mglistych Wysp": "fog_square",
    "Srebrna Korona": "silver_crown_square",
    "Zielony Brzeg": "green_shore_square",
    "Kamienna Straż": "stone_watch_square",
    "Cicha Przystań": "quiet_haven_square",
}

GUIDE_CITY_HUBS_V0522 = dict(POSTAL_CITY_HUBS_V0522)
GUIDE_CITY_HUBS_V0522["Miasto Dusz"] = "square"

# v0.53.0+: Courier Guild progression. Reputation is deliberately capped at 400,
# matching the classic long progression bands used elsewhere in Soulbound.
COURIER_REPUTATION_MIN_V0530 = 1
COURIER_REPUTATION_MAX_V0530 = 400

COURIER_RANKS_V0530 = (
    # reputation, rank/title, payout bonus
    (1,   "Posłaniec",          0.00),
    (40,  "Kurier",             0.05),
    (80,  "Kurier Gildyjny",    0.10),
    (140, "Starszy Kurier",     0.16),
    (220, "Kurier Królewski",   0.23),
    (300, "Naczelny Kurier",    0.31),
    (360, "Strażnik Szlaków",   0.40),
    (400, "Mistrz Szlaków",     0.50),
)

# v0.54.0: package classes are completely risk-free. They differ by unlock
# reputation, payout and Courier Guild reputation gain only. No package can be
# damaged, stolen, intercepted or lose its reward because of a random event.
COURIER_PACKAGE_CLASSES_V0530 = {
    "zwykla": {
        "name": "Zwykła paczka",
        "unlock_rep": 1,
        "reward_mult": 1.00,
        "rep_bonus": 0,
        "description": "standardowa przesyłka z podstawową wypłatą",
    },
    "pilna": {
        "name": "Pilna paczka",
        "unlock_rep": 40,
        "reward_mult": 1.45,
        "rep_bonus": 1,
        "description": "priorytetowa przesyłka z podwyższoną wypłatą",
    },
    "ciezka": {
        "name": "Ciężka paczka",
        "unlock_rep": 80,
        "reward_mult": 1.35,
        "rep_bonus": 2,
        "description": "cięższy transport premiowany wyższą reputacją",
    },
    "delikatna": {
        "name": "Delikatna paczka",
        "unlock_rep": 140,
        "reward_mult": 1.55,
        "rep_bonus": 3,
        "description": "starannie oznaczona przesyłka z lepszą wypłatą",
    },
    "tajna": {
        "name": "Tajna paczka",
        "unlock_rep": 220,
        "reward_mult": 1.75,
        "rep_bonus": 4,
        "description": "poufne zlecenie dla doświadczonych kurierów",
    },
    "wartosciowa": {
        "name": "Wartościowa paczka",
        "unlock_rep": 300,
        "reward_mult": 2.10,
        "rep_bonus": 5,
        "description": "bardzo dobrze opłacana klasa przesyłki",
    },
    "prestizowa": {
        "name": "Prestiżowa paczka",
        "unlock_rep": 360,
        "reward_mult": 5.00,
        "rep_bonus": 10,
        "description": (
            "elitarne zlecenie Gildii Kurierów dla Strażników Szlaków i Mistrzów; "
            "wymaga reputacji 360 i daje bardzo wysoką wypłatę, bez losowego ryzyka"
        ),
    },
}

# v0.54.0: dedicated Courier achievements use the global achievements table.
COURIER_DELIVERY_ACHIEVEMENTS_V0540 = (
    (10, "courier_deliveries_10", "Kurier: 10 dostaw", "Bronze"),
    (100, "courier_deliveries_100", "Kurier: 100 dostaw", "Silver"),
    (1000, "courier_deliveries_1000", "Kurier: 1000 dostaw", "Gold"),
    (10000, "courier_deliveries_10000", "Kurier: 10 000 dostaw", "Platinum"),
)
COURIER_ALL_CITIES_ACHIEVEMENT_V0540 = (
    "courier_all_cities", "Kurier: Wszystkie miasta", "Gold"
)
COURIER_ALL_PACKAGE_TYPES_ACHIEVEMENT_V0540 = (
    "courier_all_package_types", "Kurier: Wszystkie typy paczek", "Platinum"
)

# v0.55.0: 100-delivery achievements for every destination and every package class.
COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550 = {
    "Miasto Dusz": ("courier_city_miasto_dusz_100", "Kurier: 100 dostaw do Miasta Dusz", "Gold"),
    "Brzozowy Trakt": ("courier_city_brzozowy_trakt_100", "Kurier: 100 dostaw do Brzozowego Traktu", "Gold"),
    "Żelazne Bramy": ("courier_city_zelazne_bramy_100", "Kurier: 100 dostaw do Żelaznych Bram", "Gold"),
    "Twierdza Popiołu": ("courier_city_twierdza_popiolu_100", "Kurier: 100 dostaw do Twierdzy Popiołu", "Gold"),
    "Port Mglistych Wysp": ("courier_city_port_mglistych_wysp_100", "Kurier: 100 dostaw do Portu Mglistych Wysp", "Gold"),
    "Srebrna Korona": ("courier_city_srebrna_korona_100", "Kurier: 100 dostaw do Srebrnej Korony", "Gold"),
    "Zielony Brzeg": ("courier_city_zielony_brzeg_100", "Kurier: 100 dostaw do Zielonego Brzegu", "Gold"),
    "Kamienna Straż": ("courier_city_kamienna_straz_100", "Kurier: 100 dostaw do Kamiennej Straży", "Gold"),
    "Cicha Przystań": ("courier_city_cicha_przystan_100", "Kurier: 100 dostaw do Cichej Przystani", "Gold"),
}

COURIER_PACKAGE_TYPE_ACHIEVEMENTS_V0550 = {
    key: (
        f"courier_type_{key}_100",
        f"Kurier: 100 — {spec['name']}",
        "Gold" if key != "prestizowa" else "Platinum",
    )
    for key, spec in COURIER_PACKAGE_CLASSES_V0530.items()
}


# Backward-compatible label table retained for older code/tests that import it.
POSTAL_PACKAGE_TYPES_V0522 = tuple(
    (spec["name"], spec["reward_mult"])
    for spec in COURIER_PACKAGE_CLASSES_V0530.values()
)


def courier_rank_for_reputation_v0530(reputation):
    reputation = max(COURIER_REPUTATION_MIN_V0530, min(COURIER_REPUTATION_MAX_V0530, int(reputation or 1)))
    current = COURIER_RANKS_V0530[0]
    for rank in COURIER_RANKS_V0530:
        if reputation < rank[0]:
            break
        current = rank
    return {
        "threshold": current[0],
        "name": current[1],
        "payout_bonus": current[2],
    }


def courier_next_rank_v0530(reputation):
    reputation = max(COURIER_REPUTATION_MIN_V0530, int(reputation or 1))
    for threshold, name, payout_bonus in COURIER_RANKS_V0530:
        if threshold > reputation:
            return {
                "threshold": threshold,
                "name": name,
                "payout_bonus": payout_bonus,
            }
    return None


def courier_unlocked_package_keys_v0530(reputation):
    reputation = max(COURIER_REPUTATION_MIN_V0530, int(reputation or 1))
    return tuple(
        key for key, spec in COURIER_PACKAGE_CLASSES_V0530.items()
        if reputation >= int(spec["unlock_rep"])
    )


# Both the public city hub and the postal counter count as a city visit.
COURIER_CITY_ROOM_TO_NAME_V0530 = {
    **{room_id: city for city, room_id in GUIDE_CITY_HUBS_V0522.items()},
    **{room_id: city for city, room_id in POSTAL_CITY_HUBS_V0522.items()},
}

# v0.71.0: reputacja poszczególnych miast. Dostawy i lokalne questy budują
# zaufanie 1-400 niezależnie od reputacji Gildii Kurierów.
CITY_REPUTATION_MIN_V0710 = 1
CITY_REPUTATION_MAX_V0710 = 400
CITY_REPUTATION_RANKS_V0710 = (
    (1, "Przybysz", 0.00),
    (40, "Znajomy Miasta", 0.02),
    (100, "Zaufany Mieszkaniec", 0.04),
    (180, "Przyjaciel Miasta", 0.06),
    (260, "Opiekun Miasta", 0.08),
    (340, "Bohater Miasta", 0.10),
    (400, "Legenda Miasta", 0.12),
)


def city_rank_for_reputation_v0710(reputation):
    reputation = max(CITY_REPUTATION_MIN_V0710, min(CITY_REPUTATION_MAX_V0710, int(reputation or 1)))
    current = CITY_REPUTATION_RANKS_V0710[0]
    for rank in CITY_REPUTATION_RANKS_V0710:
        if reputation < rank[0]:
            break
        current = rank
    return {
        "threshold": current[0],
        "name": current[1],
        "courier_bonus": current[2],
    }
