# -*- coding: utf-8 -*-
"""Central numeric balance knobs extracted from gameplay logic in v0.43.0.

These values preserve v0.41.0 exactly. Change balance here; keep algorithms in core/systems.
"""

V019_CLASS_REQ = ((1,1000),(10,80000),(20,500000),(30,1200000),(40,2500000),(50,5000000),(75,18000000),(100,60000000),(150,600000000),(200,6000000000),(250,60000000000),(300,600000000000),(350,6000000000000),(399,60000000000000))
V019_SOUL_REQ = ((1,500),(10,12000),(20,100000),(30,250000),(40,500000),(50,1000000),(75,6000000),(100,25000000),(150,250000000),(200,2500000000),(250,25000000000),(300,250000000000),(350,2500000000000),(399,25000000000000))
V019_SKILL_REQ = ((1,100),(10,1000),(20,5000),(30,12000),(40,25000),(50,50000),(75,180000),(100,600000),(150,6000000),(200,60000000),(250,500000000),(300,4000000000),(350,25000000000),(399,150000000000))
V019_PROF_REQ = ((1,200),(10,2000),(20,10000),(30,25000),(40,60000),(50,120000),(75,600000),(100,3000000),(150,30000000),(200,300000000),(250,3000000000),(300,30000000000),(350,300000000000),(399,3000000000000))
V019_TOOL_REQ = ((1,200),(10,1000),(20,5000),(30,12000),(40,30000),(50,80000),(75,400000),(100,2000000),(150,20000000),(200,200000000),(250,2000000000),(300,20000000000),(350,200000000000),(399,2000000000000))
V019_STAT_REQ = ((1,100),(10,100),(20,1000),(30,10000),(40,25000),(50,60000),(75,400000),(100,2000000),(150,40000000),(200,800000000),(300,80000000000),(400,8000000000000))
V019_SKILL_GAIN = ((1,30),(10,75),(20,150),(50,800),(100,10000),(200,1000000),(300,50000000),(399,1000000000))
V019_PROF_GAIN = ((1,40),(10,100),(20,250),(50,1500),(100,15000),(150,120000),(200,1000000),(250,8000000),(300,60000000),(350,400000000),(399,6000000000))
V019_TOOL_GAIN = ((1,30),(10,75),(20,180),(50,900),(100,10000),(200,700000),(300,40000000),(399,4000000000))
V019_CLASS_KILL_NORMAL = ((1,100),(5,300),(10,1500),(20,10000),(30,25000),(40,60000),(50,120000),(75,500000),(100,2000000),(150,20000000),(200,200000000),(250,2000000000),(300,20000000000),(350,200000000000),(400,2000000000000))
V019_CLASS_KILL_BOSS = ((1,1500),(10,75000),(20,250000),(30,450000),(40,750000),(50,1250000),(75,4500000),(100,15000000),(150,150000000),(200,1500000000),(250,15000000000),(300,150000000000),(350,1500000000000),(400,15000000000000))
V019_SOUL_KILL_NORMAL = ((1,40),(10,300),(20,2000),(30,4500),(50,20000),(75,90000),(100,400000),(150,4000000),(200,40000000),(250,400000000),(300,4000000000),(350,40000000000),(400,400000000000))
V019_SOUL_KILL_BOSS = ((1,300),(10,6000),(20,50000),(30,90000),(50,250000),(75,1500000),(100,6000000),(150,60000000),(200,600000000),(250,6000000000),(300,60000000000),(350,600000000000),(400,6000000000000))
V019_STAT_KILL_NORMAL = ((1,2),(10,10),(20,50),(30,250),(40,700),(50,3000),(75,20000),(100,100000),(150,2000000),(200,40000000),(250,400000000),(300,4000000000),(350,40000000000),(400,400000000000))
V019_STAT_KILL_BOSS = ((1,20),(10,100),(20,250),(30,1500),(40,5000),(50,15000),(75,100000),(100,500000),(150,10000000),(200,200000000),(250,2000000000),(300,20000000000),(350,200000000000),(400,2000000000000))
V019_COIN_KILL_NORMAL = ((1,10),(10,200),(20,2000),(30,7500),(40,20000),(50,50000),(75,250000),(100,1000000),(150,25000000),(200,500000000),(250,10000000000),(300,200000000000),(350,4000000000000),(400,80000000000000))
V019_COIN_KILL_BOSS = ((1,100),(10,5000),(20,50000),(30,150000),(40,400000),(50,1000000),(75,6000000),(100,30000000),(150,600000000),(200,15000000000),(250,300000000000),(300,6000000000000),(350,120000000000000),(400,2400000000000000))
V019_HP_NORMAL = ((1,80),(10,300),(20,900),(30,1800),(50,5000),(75,12000),(100,25000),(150,100000),(200,500000),(250,2500000),(300,10000000),(350,50000000),(400,200000000))
V019_DAMAGE_NORMAL = ((1,5),(10,15),(20,35),(30,60),(50,120),(75,260),(100,500),(150,1600),(200,5000),(250,16000),(300,50000),(350,160000),(400,500000))
V019_QUEST_COIN = ((1,100),(10,2000),(20,20000),(30,60000),(50,500000),(75,3000000),(100,20000000),(150,500000000),(200,10000000000),(250,200000000000),(300,4000000000000),(350,80000000000000),(400,1600000000000000))
V019_ECONOMY_SINK = ((1,200),(10,5000),(20,20000),(30,70000),(50,500000),(75,3000000),(100,25000000),(150,500000000),(200,10000000000),(250,200000000000),(300,4000000000000),(350,80000000000000),(400,1600000000000000))
V019_RESOURCE_SALE = ((1,5),(10,50),(20,200),(30,500),(50,2500),(75,12000),(100,50000),(150,1000000),(200,20000000),(250,400000000),(300,8000000000),(350,160000000000),(400,3200000000000))
CHARACTER_MAX_LEVEL = 800
CLASS_MASTERY_MAX_LEVEL = 800
CLASS_MASTERY_XP_BASE = 1000
CLASS_MASTERY_XP_STEP = 250
MULTICLASS_MAX_ACTIVE = 3
SKILL_MAX_LEVEL = 800
SKILL_XP_BASE = 50
SKILL_XP_STEP = 8
SOUL_WEAPON_MASTERY_MAX_LEVEL = 800
PROFESSION_COOLDOWN = 2.0

# Quest timing belongs to configuration, not bootstrap/runtime logic.
QUEST_REPEAT_COOLDOWN_SECONDS = 60 * 60
BLACKSMITH_QUEST_COOLDOWN_SECONDS = 60 * 60
REST_TICK_SECONDS = 5.0
REST_REGEN_PERCENT = 10
V095_FISHING_BASE_SECONDS = 15
V095_FISHING_MIN_SECONDS = 5
PROFESSION_SPEED_CAP_LEVEL = 200
MINE_MIN_FLOOR = 1
MINE_PREGENERATED_MAX_FLOOR = 200
MINE_WALL_SCALING_START_FLOOR = 10

# v1.13.42: long-term progression pace. Rewards stay exciting, but the
# amount required for the next permanent level is deliberately much larger.
# Equal-stage, unbonused target pace:
# Character ~72 kills, Class Mastery ~48, Soul ~75,
# Soul Weapon Mastery ~54 basic hits, Stat ~60 kills per +1.
CHARACTER_XP_REQUIREMENT_MULTIPLIER = 4.0
CLASS_MASTERY_XP_REQUIREMENT_MULTIPLIER = 3.0
SOUL_XP_REQUIREMENT_MULTIPLIER = 3.0
SOUL_WEAPON_MASTERY_XP_REQUIREMENT_MULTIPLIER = 3.0

# Stats remain uncapped and keep the generous x4 source reward. The x4
# requirement restores a long-term ~60 equal-stage kills per permanent point
# instead of the previous ~15, without making loot/reward text feel smaller.
STAT_XP_REQUIREMENT_MULTIPLIER = 4.0
STAT_XP_REWARD_MULTIPLIER = 4.0
# v1.30.0: tylko podniesienie progow XP, bez zmiany sekund ani dropu.
# Szybkie lowienie (nawet 3s na polow) ma wyzszy prog, kazda inna
# profesja dostaje dluzsza sciezke rozwoju. Postepy sa zachowane.
PROFESSION_XP_REQUIREMENT_MULTIPLIERS = {
    "Wędkarstwo": 4.0,
    "Górnictwo": 2.0,
    "Drwalstwo": 2.5,
    "Zielarstwo": 2.5,
    "Kowalstwo": 2.0,
    "Gotowanie": 2.0,
    "Alchemia": 2.0,
    "Jubilerstwo": 2.0,
    "Krawiectwo": 2.0,
    "Garbarstwo": 2.0,
    "Stolarstwo": 2.0,
    "Zaklinanie": 2.0,
    "Archeologia": 2.0,
    "Kartografia": 2.0,
}
# v1.40.2: preserve historical per-tool difficulty (the pickaxe x2).
# Every tool now gets the SAME late-game requirement curve as its profession,
# but tool XP grants, actions, speeds and saved progression remain unchanged.
TOOL_XP_REQUIREMENT_MULTIPLIERS = {
    "mining": 2.0,
}

# v1.40.8: mocniejsza, lecz plynnna progresja od poziomu 50.
# Mnozniki sa CALKOWITE wzgledem starej (przed v1.40.1/v1.40.7)
# krzywej, NIE nakladaja sie ponownie na punkty z v1.40.7.
# Poziomy <=49 i zdobywane EXP pozostaja nietkniete.
# 10000 punktow = x1.00. Profesje i narzedzia maja wspolna krzywa.
PROFESSION_LATE_GAME_REQUIREMENT_POINTS_V1401 = (
    (49, 10000),
    (50, 10100),    # x1.01
    (75, 15000),    # x1.50
    (100, 20000),   # x2.00
    (150, 30000),   # x3.00
    (200, 40000),   # x4.00
    (300, 60000),   # x6.00
    (400, 80000),   # x8.00
    (500, 120000),  # x12.0
    (600, 160000),  # x16.0
    (700, 205000),  # x20.5
    (799, 250000),  # x25.0
)

# Poziom postaci, biegosc klasy, Dusza, Bron Duszy, skille, wzniesienie.
PLAYER_EXTRA_REQUIREMENT_POINTS_V1407 = (
    (49, 10000),
    (50, 10100),
    (75, 15000),
    (100, 20000),
    (150, 30000),
    (200, 40000),
    (300, 60000),
    (400, 80000),
    (500, 110000),
    (600, 140000),
    (700, 180000),
    (799, 220000),
)

# Kazda statystyka osobno: znacznie lzejsza krzywa, bez limitu wartosci.
# Zachowane wysokie progi statow w historycznej krzywej od 100+.
STAT_EXTRA_REQUIREMENT_POINTS_V1408 = (
    (49, 10000),
    (50, 10100),
    (75, 12500),
    (100, 15000),
    (150, 17500),
    (200, 20000),
    (300, 27000),
    (400, 35000),
    (500, 45000),
    (600, 55000),
    (700, 68000),
    (799, 80000),
)


def _interpolated_requirement_points_v1407(level: int, checkpoints) -> int:
    level = max(1, int(level))
    previous_level, previous_points = checkpoints[0]
    if level <= previous_level:
        return previous_points
    for next_level, next_points in checkpoints[1:]:
        if level <= next_level:
            return previous_points + ((level - previous_level) *
                (next_points - previous_points)) // (next_level - previous_level)
        previous_level, previous_points = next_level, next_points
    # Statystyki sa bez limitu: po 799 mnoznik rosnie powoli do x12.
    # Przy pozostalych osiach maksymalny poziom jest ograniczony.
    if checkpoints is STAT_EXTRA_REQUIREMENT_POINTS_V1408:
        return min(120000, previous_points + ((level - previous_level) * 20))
    return previous_points


def player_extra_requirement_points_v1407(level: int) -> int:
    return _interpolated_requirement_points_v1407(level, PLAYER_EXTRA_REQUIREMENT_POINTS_V1407)


def _scale_required_xp_by_points_v1408(required_xp: int, points: int) -> int:
    """Apply a requirement-only multiplier, never an XP award."""
    required_xp = max(1, int(required_xp))
    if points == 10000:
        return required_xp
    return min(9_000_000_000_000_000_000,
               max(required_xp, (required_xp * points + 5000) // 10000))


def scale_player_requirement_v1407(required_xp: int, level: int) -> int:
    """Legacy API: v1.40.8 player-axes requirement curve."""
    return _scale_required_xp_by_points_v1408(
        required_xp, player_extra_requirement_points_v1407(level))


def stat_extra_requirement_points_v1408(value: int) -> int:
    """Gentler curve for six individual unlimited statistics."""
    return _interpolated_requirement_points_v1407(
        value, STAT_EXTRA_REQUIREMENT_POINTS_V1408)


def scale_stat_requirement_v1408(required_xp: int, value: int) -> int:
    return _scale_required_xp_by_points_v1408(
        required_xp, stat_extra_requirement_points_v1408(value))


def profession_late_requirement_points_v1401(level: int) -> int:
    """Monotonic, continuous multiplier of required EXP, never earned EXP."""
    return _interpolated_requirement_points_v1407(
        level, PROFESSION_LATE_GAME_REQUIREMENT_POINTS_V1401
    )


def profession_xp_requirement_v1401(base: int, profession: str | None, level: int) -> int:
    """Canonical next-level EXP, preserving existing profession modifiers."""
    old_requirement = max(1, int(round(
        int(base) * float(PROFESSION_XP_REQUIREMENT_MULTIPLIERS.get(str(profession), 1.0))
    )))
    points = profession_late_requirement_points_v1401(level)
    # Exact historical value at <=49; round half-up for later progression.
    return old_requirement if points == 10000 else max(1, (old_requirement * points + 5000) // 10000)


# v1.40.2: synchronize TOOLS with the smooth late-game profession
# requirement curve introduced in v1.40.1. The formula only changes the
# amount needed for the NEXT tool level; it never edits character records.
# Keep exact historical rounding for levels <=49 and the pickaxe x2.
def tool_xp_requirement_v1402(base: int, tool_type: str | None, level: int) -> int:
    """Next-level required tool EXP, not an EXP reward calculation."""
    original = max(1, int(round(
        int(base) * float(TOOL_XP_REQUIREMENT_MULTIPLIERS.get(str(tool_type), 1.0))
    )))
    points = profession_late_requirement_points_v1401(level)
    return original if points == 10000 else max(1, (original * points + 5000) // 10000)


# v0.50.3: final combat pressure applied after all historical world/dungeon
# layers. Difficulty rises much more than rewards so tougher content does not
# undo the long-term progression pacing introduced in v0.50.1-v0.50.2.
# Values: HP, damage, EXP reward, coin reward.
V0503_DIFFICULTY_PRESSURE = {
    "world": {"hp": 1.30, "damage": 1.20, "reward": 1.08, "coin": 1.05},
    "instance": {"hp": 1.45, "damage": 1.30, "reward": 1.12, "coin": 1.08},
    "crypt": {"hp": 1.55, "damage": 1.38, "reward": 1.15, "coin": 1.10},
    "mythic_crypt": {"hp": 1.75, "damage": 1.50, "reward": 1.20, "coin": 1.12},
    "tower": {"hp": 1.55, "damage": 1.38, "reward": 1.15, "coin": 1.10},
    "mythic_tower": {"hp": 1.70, "damage": 1.48, "reward": 1.20, "coin": 1.12},
    "magitek": {"hp": 1.65, "damage": 1.45, "reward": 1.18, "coin": 1.12},
}

__all__ = [
    'CHARACTER_MAX_LEVEL',
    'CLASS_MASTERY_MAX_LEVEL',
    'CLASS_MASTERY_XP_BASE',
    'CLASS_MASTERY_XP_STEP',
    'MINE_MIN_FLOOR',
    'MINE_PREGENERATED_MAX_FLOOR',
    'MINE_WALL_SCALING_START_FLOOR',
    'MULTICLASS_MAX_ACTIVE',
    'PROFESSION_COOLDOWN',
    'QUEST_REPEAT_COOLDOWN_SECONDS',
    'BLACKSMITH_QUEST_COOLDOWN_SECONDS',
    'PROFESSION_SPEED_CAP_LEVEL',
    'REST_REGEN_PERCENT',
    'REST_TICK_SECONDS',
    'SKILL_MAX_LEVEL',
    'SKILL_XP_BASE',
    'SKILL_XP_STEP',
    'SOUL_WEAPON_MASTERY_MAX_LEVEL',
    'V019_CLASS_KILL_BOSS',
    'V019_CLASS_KILL_NORMAL',
    'V019_CLASS_REQ',
    'V019_COIN_KILL_BOSS',
    'V019_COIN_KILL_NORMAL',
    'V019_DAMAGE_NORMAL',
    'V019_ECONOMY_SINK',
    'V019_HP_NORMAL',
    'V019_PROF_GAIN',
    'V019_PROF_REQ',
    'V019_QUEST_COIN',
    'V019_RESOURCE_SALE',
    'V019_SKILL_GAIN',
    'V019_SKILL_REQ',
    'V019_SOUL_KILL_BOSS',
    'V019_SOUL_KILL_NORMAL',
    'V019_SOUL_REQ',
    'V019_STAT_KILL_BOSS',
    'V019_STAT_KILL_NORMAL',
    'V019_STAT_REQ',
    'V019_TOOL_GAIN',
    'V019_TOOL_REQ',
    'V095_FISHING_BASE_SECONDS',
    'V095_FISHING_MIN_SECONDS',
    'CHARACTER_XP_REQUIREMENT_MULTIPLIER',
    'CLASS_MASTERY_XP_REQUIREMENT_MULTIPLIER',
    'SOUL_XP_REQUIREMENT_MULTIPLIER',
    'SOUL_WEAPON_MASTERY_XP_REQUIREMENT_MULTIPLIER',
    'STAT_XP_REQUIREMENT_MULTIPLIER',
    'STAT_XP_REWARD_MULTIPLIER',
    'PROFESSION_XP_REQUIREMENT_MULTIPLIERS',
    'TOOL_XP_REQUIREMENT_MULTIPLIERS',
    'V0503_DIFFICULTY_PRESSURE',
]
