# -*- coding: utf-8 -*-
"""Strict, source-derived additional quest counts; never relax old audits."""
def expected_quest_total_v1100():
    from systems.eternal_glory_world_v1100 import QUEST_IDS as REGIONAL
    from systems.eternal_glory_depths_v1100 import DUNGEON_QUEST_IDS
    from systems.eternal_glory_crafting_v1100 import PROFESSION_QUEST_IDS
    from systems.eternal_glory_class_guild_v1100 import CLASS_QUEST_IDS,TEAM_CONTRACT_IDS
    from systems.eternal_glory_story_v1100 import CHAPTER_IDS
    extensions = [set(REGIONAL), set(DUNGEON_QUEST_IDS), set(PROFESSION_QUEST_IDS),
                  set(CLASS_QUEST_IDS), set(TEAM_CONTRACT_IDS), set(CHAPTER_IDS)]
    all_ids = set().union(*extensions)
    assert len(all_ids)==sum(map(len,extensions)),'v11 quest ID collision'
    assert [len(s) for s in extensions]==[24,24,22,66,12,12], 'v11 missing quest modules'
    from core.bootstrap_economy_professions import VERSION
    if VERSION in ('11.00.12', '11.00.13', '11.00.14', '11.00.15', '11.00.16','11.00.17','11.00.18'):
        from systems.class_legend_paths_v900 import TEACHER_QUEST_IDS
        assert len(TEACHER_QUEST_IDS) == 24 and not (TEACHER_QUEST_IDS & all_ids)
        return 6585 + len(all_ids) + len(TEACHER_QUEST_IDS)
    return 6585 + len(all_ids)
