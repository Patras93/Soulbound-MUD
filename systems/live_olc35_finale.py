# -*- coding: utf-8 -*-
"""v35.00.0 — four data-driven systems; no administrator Python execution."""
import copy
import json
import re

CATEGORIES = ('bosses', 'activities', 'wars', 'cities')
ACTIVE = {key: {} for key in CATEGORIES}
ALIASES = {'boss35': 'bosses', 'uoss35': 'bosses',
           'czyn35': 'activities', 'fach35': 'activities',
           'wojna35': 'wars', 'gildia35': 'wars',
           'miasto35': 'cities', 'osada35': 'cities'}
CUSTOM = re.compile(r'^live_[a-z0-9_]{3,45}$')
DEFAULT_WAR = {'bosses_needed': 5, 'reward_silver': 50000, 'cooldown_minutes': 60}
DEFAULT_CITY = {'max_level': 10, 'base_cost_silver': 10000, 'bonus_per_level': 1}


def number(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name}: liczba calkowita {low}-{high}.')


def validate(rules, *, payload=None):
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from data.crafting_recipes import CRAFT_RECIPES
    from data.items import ITEMS
    if type(rules) is not dict or set(rules) != set(CATEGORIES):
        raise ValueError('OLC35: wymagane cztery dzialy.')
    payload = payload or {}
    recipes = {**CRAFT_RECIPES, **payload.get('recipes', {})}
    for category, entries in rules.items():
        if type(entries) is not dict or len(entries) > 150:
            raise ValueError('OLC35: maksymalnie 150 wpisow na dzial.')
        for key, row in entries.items():
            if type(key) is not str or type(row) is not dict:
                raise ValueError('OLC35: wymagane identyfikatory i definicje JSON.')
            if category == 'bosses':
                if key not in UOSS_SUPERBOSS_ENCOUNTERS_V11134 or set(row) != {'phases'}:
                    raise ValueError('Boss35: znany UOSS i lista phases.')
                phases = row['phases']
                if type(phases) is not list or not 1 <= len(phases) <= 5:
                    raise ValueError('Boss35: od jednej do pieciu faz.')
                previous = 101
                for phase in phases:
                    if type(phase) is not dict or set(phase) != {'below_hp', 'every', 'action', 'power'}:
                        raise ValueError('Boss35: below_hp, every, action, power.')
                    number(phase['below_hp'], 1, 99, 'Prog HP')
                    number(phase['every'], 1, 30, 'Rytm')
                    if phase['action'] not in ('strike', 'heal'):
                        raise ValueError('Boss35: dozwolone strike albo heal.')
                    number(phase['power'], 101 if phase['action'] == 'strike' else 1,
                           300 if phase['action'] == 'strike' else 5, 'Moc')
                    if phase['below_hp'] >= previous:
                        raise ValueError('Boss35: progi HP musza malec.')
                    previous = phase['below_hp']
            elif category == 'activities':
                if not CUSTOM.fullmatch(key) or set(row) != {'name', 'recipe'}:
                    raise ValueError('Czynnosc35: live_id, name i recipe.')
                if not isinstance(row['name'], str) or not 3 <= len(row['name'].strip()) <= 100 or any(ord(c) < 32 for c in row['name']):
                    raise ValueError('Czynnosc35: nazwa 3-100 znakow.')
                recipe = recipes.get(row['recipe'])
                if not recipe or not recipe.get('ingredients') or not recipe.get('tool_type') or not recipe.get('tool_item_id'):
                    raise ValueError('Czynnosc35: istniejąca pelna receptura z narzedziem i materialami.')
                if recipe.get('output') not in set(ITEMS) | set(payload.get('items', {})):
                    raise ValueError('Czynnosc35: nieznany produkt.')
            elif category == 'wars':
                if key != 'global' or set(row) != set(DEFAULT_WAR):
                    raise ValueError('Wojna35 global: bosses_needed, reward_silver, cooldown_minutes.')
                number(row['bosses_needed'], 1, 50, 'Wymagane bossy')
                number(row['reward_silver'], 0, 100_000_000, 'Nagroda skarbca w srebrze')
                number(row['cooldown_minutes'], 1, 10080, 'Cooldown w minutach')
            elif category == 'cities':
                if key != 'global' or set(row) != set(DEFAULT_CITY):
                    raise ValueError('Miasto35 global: max_level, base_cost_silver, bonus_per_level.')
                number(row['max_level'], 1, 30, 'Maksymalny poziom')
                number(row['base_cost_silver'], 100, 100_000_000, 'Koszt bazowy w srebrze')
                number(row['bonus_per_level'], 0, 5, 'Bonus za poziom')
    return True


def sync(rules):
    for cat in CATEGORIES:
        ACTIVE[cat].clear()
        ACTIVE[cat].update(copy.deepcopy(rules[cat]))


def stage(service, category, key, field, value):
    domain = ALIASES.get(category)
    if domain is None:
        return False
    if field != 'definicja':
        raise ValueError('OLC35: pole definicja.')
    draft = copy.deepcopy(service.draft)
    if str(value).strip().casefold() in ('auto', 'automatyczny'):
        draft['v35_rules'][domain].pop(key, None)
    else:
        try:
            draft['v35_rules'][domain][key] = json.loads(value)
        except (TypeError, ValueError) as exc:
            raise ValueError('OLC35: niepoprawny JSON.') from exc
    service.validate(draft)
    service.draft = draft
    return True


def preview(service, category, key, field):
    domain = ALIASES.get(category)
    if domain is None:
        return None
    if field != 'definicja':
        raise ValueError('OLC35: tylko pole definicja.')
    old = service.active['v35_rules'][domain].get(key, 'auto')
    new = service.draft['v35_rules'][domain].get(key, 'auto')
    return (f'OLC35 {domain}/{key}: aktualnie {json.dumps(old, ensure_ascii=False)}. '
            f'Roboczo {json.dumps(new, ensure_ascii=False)}. Zmiana: definicja | JSON; cofniecie: auto.')


def package(service, raw):
    try:
        records = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError('Pakiet35: bledny JSON.') from exc
    if type(records) is not dict or not records or set(records) - set(CATEGORIES):
        raise ValueError('Pakiet35: slownik z dzialami bosses/activities/wars/cities.')
    draft = copy.deepcopy(service.draft)
    for domain, entries in records.items():
        if type(entries) is not dict:
            raise ValueError('Pakiet35: ID -> definicja.')
        for key, row in entries.items():
            if row is None:
                draft['v35_rules'][domain].pop(key, None)
            else:
                draft['v35_rules'][domain][key] = row
    service.validate(draft)
    service.draft = draft
    return 'Pakiet35 DRAFT: '+', '.join(f'{d}: {len(v)}' for d, v in records.items())+'. Sprawdz i opublikuj.'


def help_text():
    return ('OLC35: boss35 ID definicja | {"phases":[{"below_hp":50,"every":2,"action":"strike","power":140}]} ; '
            'czyn35 live_ID definicja | {"name":"Obrobka","recipe":"ID_RECEPTURY"}; '
            'wojna35 global definicja | {"bosses_needed":5,"reward_silver":50000,"cooldown_minutes":60}; '
            'miasto35 global definicja | {"max_level":10,"base_cost_silver":10000,"bonus_per_level":1}. '
            'Dostep: czynnosci; gildia wojna; gildia miasto. Publikacja admin live aktywuj POTWIERDZAM.')


def boss_action(mob, template):
    """Bounded, deterministic phase action on a real UOSS attack."""
    record = ACTIVE['bosses'].get(template.get('uoss_unique_superboss_key', ''))
    if not record or int(getattr(mob, 'hp', 0)) <= 0:
        return 1.0
    tick = int(getattr(mob, '_olc35_turn', 0)) + 1
    mob._olc35_turn = tick
    percent = 100 * int(mob.hp) / max(1, int(getattr(mob, 'max_hp', 1)))
    # Most urgent active phase wins; this is not cumulative or free healing each turn.
    active = [p for p in record['phases'] if percent <= p['below_hp']]
    if not active:
        return 1.0
    phase = active[-1]
    if tick % phase['every']:
        return 1.0
    if phase['action'] == 'heal':
        healed = max(1, int(mob.max_hp) * phase['power'] // 100)
        mob.hp = min(int(mob.max_hp), int(mob.hp) + healed)
        return 1.0
    return phase['power'] / 100.0


def war_config():
    return ACTIVE['wars'].get('global', DEFAULT_WAR).copy()


def city_config():
    return ACTIVE['cities'].get('global', DEFAULT_CITY).copy()


def ensure_guild_tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS guild_wars_v3500 (
      clan_id INTEGER PRIMARY KEY, target INTEGER NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
      reward INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 0, ready_at INTEGER NOT NULL DEFAULT 0)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS guild_city_v3500 (
      clan_id INTEGER NOT NULL, building TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(clan_id,building))''')


def war_status(conn, clan_id):
    ensure_guild_tables(conn)
    return conn.execute('SELECT * FROM guild_wars_v3500 WHERE clan_id=?', (clan_id,)).fetchone()


def start_war(conn, clan_id, now):
    conf = war_config()
    ensure_guild_tables(conn)
    previous = war_status(conn, clan_id)
    if previous and (int(previous['active']) or int(previous['ready_at']) > now):
        return False
    # The guild's watchtower helps prepare the campaign, never grants free wins.
    guard = city_level(conn, clan_id, 'straznica')
    required = max(1, conf['bosses_needed'] - guard // 3)
    # One current war row per guild; completed war is retained until next start.
    conn.execute('''INSERT INTO guild_wars_v3500(clan_id,target,progress,reward,active,ready_at)
      VALUES(?,?,0,?,1,0) ON CONFLICT(clan_id) DO UPDATE
      SET target=excluded.target, progress=0, reward=excluded.reward, active=1, ready_at=0''',
      (clan_id, required, conf['reward_silver']))
    conn.commit()
    return True


def war_boss_kill(conn, clan_id, now, valid_boss):
    """One guild boss credit per completed encounter; returns completed reward once."""
    if not valid_boss:
        return None
    try:
        row = conn.execute('SELECT * FROM guild_wars_v3500 WHERE clan_id=?', (clan_id,)).fetchone()
    except __import__('sqlite3').OperationalError:
        return None
    if not row or not int(row['active']):
        return None
    progress = min(int(row['target']), int(row['progress']) + 1)
    if progress < int(row['target']):
        conn.execute('UPDATE guild_wars_v3500 SET progress=? WHERE clan_id=? AND active=1', (progress, clan_id))
        conn.commit()
        return progress, int(row['target']), 0
    granary = city_level(conn, clan_id, 'spichlerz')
    cooldown = max(60, war_config()['cooldown_minutes'] * 60 * (100-min(50,granary*5)) // 100)
    # The conditional UPDATE prevents duplicate last-hit awards.
    result = conn.execute('''UPDATE guild_wars_v3500 SET progress=?,active=0,ready_at=?
      WHERE clan_id=? AND active=1''', (progress, now+cooldown, clan_id))
    if result.rowcount != 1:
        return None
    reward = int(row['reward'])
    conn.execute('UPDATE player_clans SET treasury=treasury+? WHERE id=?', (reward, clan_id))
    conn.commit()
    return progress, int(row['target']), reward


def city_level(conn, clan_id, building):
    try:
        row = conn.execute('SELECT level FROM guild_city_v3500 WHERE clan_id=? AND building=?',
                           (clan_id, building)).fetchone()
    except __import__('sqlite3').OperationalError:
        return 0
    return int(row['level']) if row else 0


def city_upgrade(conn, clan_id, building):
    if building not in ('warsztat', 'spichlerz', 'straznica'):
        raise ValueError('Miasto: warsztat, spichlerz albo straznica.')
    ensure_guild_tables(conn)
    level = city_level(conn, clan_id, building)
    cfg = city_config()
    if level >= cfg['max_level']:
        return False, level, 0
    cost = cfg['base_cost_silver'] * (level + 1) ** 2
    # Conditional cost deduction, then upgrade in one SQLite transaction.
    try:
        with conn:
            cursor = conn.execute('UPDATE player_clans SET treasury=treasury-? WHERE id=? AND treasury>=?',
                                  (cost, clan_id, cost))
            if cursor.rowcount != 1:
                raise ValueError('Brak srebra w skarbcu gildii.')
            conn.execute('''INSERT INTO guild_city_v3500(clan_id,building,level) VALUES(?,?,1)
              ON CONFLICT(clan_id,building) DO UPDATE SET level=level+1''', (clan_id, building))
    except ValueError:
        raise
    return True, level+1, cost


def city_bonus(conn, clan_id):
    """Small, bounded guild XP bonus from tangible city development."""
    # Called for joined players only.  No schema write on every XP query.
    try:
        values = conn.execute('SELECT COALESCE(SUM(level),0) FROM guild_city_v3500 WHERE clan_id=?',
                              (clan_id,)).fetchone()
    except __import__('sqlite3').OperationalError:
        return 0
    return min(90, int(values[0]) * city_config()['bonus_per_level']) if values else 0


def city_craft_bonus(conn, clan_id, quantity):
    """Workshop adds earned output, not free materials or tools; cap +3."""
    if not clan_id:
        return quantity
    level=city_level(conn,clan_id,'warsztat')
    return int(quantity)+min(3,level//3)
