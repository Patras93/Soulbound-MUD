# -*- coding: utf-8 -*-
"""v29.10: rekomendacje bez cache, awans, 800, NVDA, nagrody XP."""
import asyncio
from types import SimpleNamespace
from unittest.mock import patch
from player.session_mixins.exp_terrain import SessionExpTerrainMixin
from player.session_mixins.session_runtime_state import SessionRuntimeStateMixin
from core.progression_600 import CHARACTER_MAX_LEVEL


class FakeCharacter:
    def __init__(self, level=1, soul_level=1):
        self.character_level = level
        self.soul_level = soul_level

    def add_soul_xp(self, amount, single_level_cap=False):
        if amount > 0:
            self.soul_level += 1
        return [f'Soul XP +{amount}']

    def add_character_xp(self, amount, single_level_cap=False):
        # Kontrolowany awans, niezalezny od kosztu XP prawdziwej postaci.
        before = self.character_level
        self.character_level = min(CHARACTER_MAX_LEVEL, before + amount)
        return [f'EXP postaci +{amount}'] + (
            [f'Level postaci wzrasta do {self.character_level}.']
            if self.character_level > before else []
        )


class FakeSession(SessionExpTerrainMixin, SessionRuntimeStateMixin):
    def __init__(self, level=1, soul=1):
        self.character = FakeCharacter(level, soul)
        self.server = SimpleNamespace(db=object())
        self.account_id = 7
        self.sent = []

    def find_room_matches(self, guide):
        return []  # Obowiazuja bezpieczne statyczne progi katalogu.

    def normalize_description_query(self, query):
        return str(query).lower().strip()

    def character_progression_power(self):
        return self.character.character_level

    def exp_area_category_text(self, area):
        return 'Teren testowy'

    def scale_progression_xp_v11342(self, amount, content_level, content_scaled=False):
        return amount

    def apply_double_xp(self, amount, now=None):
        return amount

    def session_summary_add(self, category, amount):
        pass

    def mentor_bonus_percent_v03050(self):
        return 0

    def max_hp(self):
        return 500

    async def set_achievement_progress(self, key, value):
        return None

    async def send(self, message, **kwargs):
        self.sent.append(str(message))


def run():
    count = 0

    def ok(condition, label):
        nonlocal count
        assert condition, label
        count += 1

    session = FakeSession(level=1)
    first = session.recommended_exp_areas_v2910()
    ok(bool(first), 'polecane na starcie')
    ok(any(a['id'] == 'trening' for a in first), 'plac treningowy na starcie')
    ok(all(session.exp_area_recommended(a) for a in first), 'spojnosc filtrow')
    ok(bool(session.recommended_exp_areas_v2910(level=13)), 'polecane 13')
    ok(not any(a['id'] == 'trening' for a in session.recommended_exp_areas_v2910(13)), 'trening znika po 12')
    ok(session.exp_area_level_up_hint_v2910(1, 13) is not None, 'powiadomienie gdy zmienia sie lista')
    ok(session.exp_area_level_up_hint_v2910(13, 13) is None, 'bez awansu brak powiadomienia')
    ok(session.exp_area_level_up_hint_v2910(13, 14) is None, 'brak spamu gdy polecane takie same')
    ok(session.exp_area_level_up_hint_v2910(14, 13) is None, 'spadek levelu bez powiadomienia')
    ok([a['id'] for a in session.recommended_exp_areas_v2910(13)] == [a['id'] for a in session.recommended_exp_areas_v2910(13)], 'deterministyczne rekomendacje')
    ok(any(a['id'] == 'ashen_wastes' for a in session.recommended_exp_areas_v2910(300)), 'region 300+')
    ok(any(a['id'] == 'world_crown' for a in session.recommended_exp_areas_v2910(400)), 'region 390-400')
    ok(not any(a['id'] == 'world_crown' for a in session.recommended_exp_areas_v2910(401)), 'region 390-400 nie na 401')
    ok(not any(a['id'] == 'world_crown' for a in session.recommended_exp_areas_v2910(450)), 'nie polecaj starej krainy 450')
    high = session.recommended_exp_areas_v2910(450)
    ok(any(a['id'] == 'krypta' for a in high), 'lochy skalowane ponad 400')
    ok(not any(a['id'] in {'astral', 'mythic_astral'} for a in high), 'astral wymaga Duszy 100')
    ok(not any(a['id'] == 'astral' for a in session.recommended_exp_areas_v2910(110)), 'astral zabroniony przy Soul 1')
    ok(session.exp_area_soul_level_up_hint_v2910(99, 100) is None, 'Soul 100 nie wystarcza gdy Level postaci 1')
    session.character.soul_level = 100
    high_soul = session.recommended_exp_areas_v2910(800)
    ok(any(a['id'] == 'astral' for a in high_soul), 'astral z Dusza 100')
    ok(any(a['id'] == 'mythic_astral' for a in high_soul), 'mityczny astral z Dusza 100')
    session.character.character_level = 250
    ok(session.exp_area_soul_level_up_hint_v2910(99, 100) is not None, 'powiadomienie o Soul 100 dla wysokich Leveli')
    ok(any(a['id'] == 'v3000_eternal' for a in high_soul), 'v30 nowe otwarte regiony powyzej 400')

    session.character.character_level = 13
    session.character.soul_level = 1
    session.sent.clear()
    asyncio.run(session.show_exp_areas('polecane 2'))
    ok(session.sent[0].startswith('POLECANE EXPOWISKA'), 'naglowek nvda')
    ok(sum(line.startswith(('1. ', '2. ', '3. ')) for line in session.sent) == 2, 'tylko 2 pozycje')
    ok(any('Pokazano' in line for line in session.sent), 'wskazowka rozwijania listy')
    ok(any('Prowadzenie: prowadz' in line for line in session.sent), 'nawigacja w kazdej pozycji')
    session.sent.clear()
    asyncio.run(session.show_exp_areas('polecane wszystkie'))
    ok(sum(line.startswith(tuple(f'{i}. ' for i in range(1, 30))) for line in session.sent) == len(session.recommended_exp_areas_v2910()), 'pelna lista')
    session.sent.clear()
    asyncio.run(session.show_exp_areas('polecane pomylka'))
    ok('Użycie:' in session.sent[-1], 'walidacja komendy')
    session.character.character_level = 800
    session.sent.clear()
    asyncio.run(session.show_exp_areas('polecane'))
    ok(any('dobierz odblokowane piętro' in msg for msg in session.sent), 'komunikat o glebokosci')
    ok(not any('Korona Świata' in msg for msg in session.sent), 'stary region 390-400 nie jest polecany dla 800')

    session.character.character_level = 1
    with patch('systems.experience_bank_v2011.banked_experience_v2011', side_effect=lambda db, account_id, amount, *args, **kwargs: amount):
        result = session.add_character_xp_with_event(12, content_level=session.character.character_level)
        ok(session.character.character_level == 13, 'realne wejscie przyznawania XP')
        ok(sum('Polecane expowiska odświeżone' in msg for msg in result) == 1, 'jeden komunikat po wielokrotnym awansie')
        ok('expowiska polecane' in result[-1], 'komenda w komunikacie')
        result = session.add_character_xp_with_event(0, content_level=session.character.character_level)
        ok(not any('Polecane expowiska odświeżone' in msg for msg in result), 'brak spamu bez XP')
        result = session.add_character_xp_with_event(1, content_level=session.character.character_level)
        ok(sum('Polecane expowiska odświeżone' in msg for msg in result) <= 1, 'nie spamuj w tej samej nagrodzie')
    # Rzeczywista bramka przyznawania Soul XP: awans 99->100 odblokowuje
    # Astral przy odpowiednim Levelu postaci i informuje tylko raz.
    from player.session_methods_v4200.dungeonprogression_part02 import grant_soul_xp
    session.character.character_level = 250
    session.character.soul_level = 99
    session.sent.clear()
    with patch('systems.experience_bank_v2011.banked_experience_v2011', side_effect=lambda db, account_id, amount, *args, **kwargs: amount):
        advanced = asyncio.run(grant_soul_xp(session, 1, content_level=session.character.soul_level))
    ok(advanced and session.character.soul_level == 100, 'realna bramka Soul XP')
    ok(sum('Polecane expowiska odświeżone po awansie Soul Level' in message for message in session.sent) == 1, 'Soul awans generuje jedna wskazowke')
    ok(any('Awans Soul Level odnawia' in message for message in session.sent), 'zachowane leczenie na Soul awans')
    return count


if __name__ == '__main__':
    print(f'V29.10.0 DYNAMICZNE EXPOWISKA: {run()} checks PASS')
