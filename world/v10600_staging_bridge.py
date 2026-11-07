# -*- coding: utf-8 -*-
"""Opcjonalne wpięcie katalogów v106 do REALNEGO bootstrapu świata.

Tylko SOULBOUND_V106_STAGING=1; domyślnie aktywna pozostaje v105.
Brak migracji bazy oraz brak zapisu do serwera produkcyjnego.
Próby 3010+ są katalogiem v106, nie są jeszcze odblokowywane przez core.
"""
from __future__ import annotations


def install(rooms, mobs, spawns, npcs, quests, items, recipes,
            areas, zone_ids, categories, guides, power):
    from world.v10600_krainy_30001_60000 import install as regions_install
    from world.v10600_raids_26_35 import install as raids_install
    from world.v10600_soul_trials import register as register_trials
    from world.v10600_calendar_contracts import install as contracts_install

    original_quests = len(quests)
    original_rooms = len(rooms)
    original_mobs = len(mobs)
    regions = regions_install(rooms,mobs,spawns,npcs,quests,items,recipes,
                              areas,zone_ids,categories,guides,power)
    raids = raids_install(rooms,mobs,spawns,npcs,quests,items,recipes)
    trials = register_trials(quests,mobs)
    contracts = contracts_install(quests,npcs,mobs,items)
    expected_quests = regions['quests'] + raids['quests'] + trials + contracts['contracts']
    if len(quests)-original_quests != expected_quests:
        raise RuntimeError('v106: niepełna integracja questów do świata')
    if (len(rooms)-original_rooms != regions['rooms']+raids['rooms'] or
            len(mobs)-original_mobs != regions['mobs']+raids['bosses']):
        raise RuntimeError('v106: niepełna integracja pokoi i przeciwników')
    # Próby T3010–6000 powstają wcześniej w world.equipment_help,
    # który importowany jest jeszcze przed world.dynamic_content. Nie liczymy
    # ich dwa razy do delty instalatora, ale raportujemy całość v106.
    from world.v10600_soul_trials import trial_ids
    return {'regions':regions,'raids':raids,'trials':trials,
            'trials_catalogued':len(trial_ids()),
            'contracts':contracts,'new_quests':expected_quests+len(trial_ids())-trials,
            'world_install_quests':expected_quests,
            'areas':regions['areas']}
