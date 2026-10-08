"""v1.17.6 profession XP, tools, timers and bulk-smelt regression checks.

Synthetic character/database; never touches a real player, account or server.
All fourteen live profession->tool pairs go through the real XP grant method.
"""
from __future__ import annotations

from types import SimpleNamespace


def audit_profession_balance_v1176(*, runtime=False):
    from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES, TOOL_PROFESSION_MAP
    from core.profession_timing import (TOOL_ACTION_BASE_SECONDS,
                                        TOOL_ACTION_MIN_SECONDS,
                                        profession_action_seconds)
    from core.profession_batch_v1176 import (
        profession_batch_content_level_v1176, profession_batch_effort_v1176)

    checks, errors = 0, []
    def verify(ok, message):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(message)

    all_professions = set(PROFESSION_RANK_NAMES)
    all_tools = set(TOOL_PROFESSION_MAP)
    verify(len(all_professions) == (14 if runtime else 8), f"incorrect professions count: {len(all_professions)}")
    verify(len(all_tools) == (14 if runtime else 8), f"incorrect tools count: {len(all_tools)}")
    verify(set(TOOL_PROFESSION_MAP.values()) == all_professions, "missing profession tool mapping")
    verify(len(set(TOOL_PROFESSION_MAP.values())) == len(all_professions), "multiple tools mapped to one profession")
    verify(all_tools <= set(TOOL_ACTION_BASE_SECONDS) and all_tools <= set(TOOL_ACTION_MIN_SECONDS), "timing catalogue mismatch")

    for tool, profession in sorted(TOOL_PROFESSION_MAP.items()):
        for level in (1, 100, 200, 400, 600):
            seconds = profession_action_seconds(tool, level)
            verify(TOOL_ACTION_MIN_SECONDS[tool] <= seconds <= TOOL_ACTION_BASE_SECONDS[tool],
                   f"{profession}: incorrect timing at {level}")
        verify(profession_action_seconds(tool, 1) == TOOL_ACTION_BASE_SECONDS[tool],
               f"{profession}: incorrect base duration")
        verify(profession_action_seconds(tool, 600) == TOOL_ACTION_MIN_SECONDS[tool],
               f"{profession}: minimum duration not achieved")
        verify(profession_action_seconds(tool, 100) >= profession_action_seconds(tool, 200) >=
               profession_action_seconds(tool, 400), f"{profession}: timer goes backwards")

    ordered = [(1, 100), (500, 900)]
    a = profession_batch_content_level_v1176(ordered)
    verify(a == profession_batch_content_level_v1176(list(reversed(ordered))),
           "batch content level depends on catalogue order")
    verify(a > 400, "high-grade batch treated as first cheap recipe")
    verify(profession_batch_content_level_v1176([(600, 1000)]) == 600,
           "single-tier smelting is not preserved")
    verify(profession_batch_content_level_v1176([]) == 1, "empty batch is not safe")

    previous = 0
    for batch_count in (1, 2, 8, 64, 512, 4096):
        multiplier = profession_batch_effort_v1176(batch_count)
        verify(multiplier > previous, f"smelting batch reward plateaus at {batch_count}")
        previous = multiplier
    verify(profession_batch_effort_v1176(1) == 1.0, "single craft changed")
    verify(profession_batch_effort_v1176(8) == 2.0, "eight-craft effort changed")

    if not runtime:
        return {'checks': checks, 'errors': errors, 'error_count': len(errors),
                'professions': len(all_professions), 'tools': len(all_tools)}

    from player.session_mixins.profession_storage import SessionProfessionStorageMixin
    from player.session_mixins.crafting_orders import CRAFTING_ORDER_NPCS_V0600
    from systems.profession_quest_expansion import (
        PROFESSION_QUEST_IDS_BY_PROFESSION_V0700, PROFESSION_QUEST_STAGES_V0700)
    from data.quests import QUESTS

    orders = list(CRAFTING_ORDER_NPCS_V0600.values())
    verify(len(orders) == 14, "not all professions have rotating orders")
    verify({spec['profession'] for spec in orders} == all_professions,
           "missing profession rotating order")
    for spec in orders:
        verify(TOOL_PROFESSION_MAP.get(spec['tool_type']) == spec['profession'],
               f"{spec['profession']}: order tool mismatch")
        verify(spec.get('source') in ('gather', 'craft', 'cook', 'alchemy', 'jewel', 'extended', 'action'),
               f"{spec['profession']}: order source missing")
    verify(set(PROFESSION_QUEST_IDS_BY_PROFESSION_V0700) == all_professions,
           "missing four-stage mastery quest coverage")
    for profession in sorted(all_professions):
        quests = PROFESSION_QUEST_IDS_BY_PROFESSION_V0700.get(profession, ())
        verify(len(quests) == len(PROFESSION_QUEST_STAGES_V0700),
               f"{profession}: mastery quest stages missing")
        for quest_id in quests:
            quest = QUESTS.get(quest_id, {})
            verify(quest.get('required_profession') == profession,
                   f"{profession}: missing/misassigned mastery quest {quest_id}")
            verify(int(quest.get('reward_profession_xp', 0)) > 0 and
                   int(quest.get('reward_tool_xp', 0)) > 0,
                   f"{profession}: missing profession/tool quest XP {quest_id}")
            verify(quest.get('repeatable') and int(quest.get('repeat_cooldown', 0)) > 0,
                   f"{profession}: nonrepeatable profession quest {quest_id}")

    class MemoryDb:
        def __init__(self, profession, tool):
            self.profs = {profession: {"level": 100, "xp": 0, "actions": 0}}
            self.tools = {tool: {"level": 100, "xp": 0, "uses": 0}}
        def profession(self, account, profession):
            return self.profs[profession]
        def tool(self, account, tool):
            return self.tools[tool]
        def save_profession(self, account, profession, level, xp, actions):
            self.profs[profession] = {"level": level, "xp": xp, "actions": actions}
        def save_tool(self, account, tool, level, xp, uses):
            self.tools[tool] = {"level": level, "xp": xp, "uses": uses}
        def increment_profession_action_quests_v0700(self, *args):
            return []
        def save_character(self, character):
            return None

    class Practice(SessionProfessionStorageMixin):
        def __init__(self, profession, tool):
            self.server = SimpleNamespace(db=MemoryDb(profession, tool))
            self.account_id = 1
            self.character = SimpleNamespace()
        def guild_bonus_percent_v0926(self): return 0
        def v0260_profession_xp_bonus_percent(self, *args): return 0
        def mentor_bonus_percent_v03050(self): return 0
        def apply_double_xp(self, xp): return xp
        def session_summary_add(self, *args): return None
        def add_character_xp_with_event(self, *args, **kwargs): return []

    for tool, profession in sorted(TOOL_PROFESSION_MAP.items()):
        prev_prof, prev_tool = -1, -1
        for material_level in (1, 30, 100, 200, 400, 600):
            tester = Practice(profession, tool)
            messages, *_ = tester.grant_profession_progress(
                profession, 15, tool, 12, content_level=material_level)
            earned = tester._last_profession_progress_gain_v11343
            xp, tool_xp = earned['profession_xp'], earned['tool_xp']
            verify(xp > prev_prof, f"{profession}: XP did not increase with content {material_level}")
            verify(tool_xp > prev_tool, f"{profession}: tool XP did not increase at {material_level}")
            verify(any('XP' in x for x in messages), f"{profession}: no readable XP message")
            verify(tester.server.db.profs[profession]['actions'] == 1,
                   f"{profession}: real action not counted")
            prev_prof, prev_tool = xp, tool_xp

    for count in (1, 8, 64, 512):
        tester = Practice('Kowalstwo', 'crafting')
        tester.grant_profession_progress('Kowalstwo', 8000, 'crafting', 8000,
                                         content_level=300, batch_count=count)
        gains = tester._last_profession_progress_gain_v11343
        verify(gains['batch_count'] == count, 'batch count missing from XP record')
        if count > 1:
            verify(gains['profession_xp'] > base_gains[0], f"batch prof XP flat at {count}")
            verify(gains['tool_xp'] > base_gains[1], f"batch tool XP flat at {count}")
        else:
            base_gains = (gains['profession_xp'], gains['tool_xp'])

    return {'checks': checks, 'errors': errors, 'error_count': len(errors),
            'professions': len(all_professions), 'tools': len(all_tools)}


if __name__ == '__main__':
    result = audit_profession_balance_v1176()
    print(result)
    raise SystemExit(1 if result['errors'] else 0)
