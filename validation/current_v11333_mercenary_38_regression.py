# -*- coding: utf-8 -*-
"""v113.00.33: 38 real playable classes, contracts, tactics and account isolation.

Runs in a fresh interpreter against in-memory SQLite; no production DB or TCP.
"""
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.classes_skills import CLASSES
from core.archetypes.chaos import CLASS_SPECS as CHAOS
from core.archetypes.expansion import CLASS_SPECS as EXPANSION
from core.magitek.catalogue import CLASS_NAME as MAGITEK
from storage.db_mercenaries import DatabaseMercenariesMixin
from systems.mercenary_taverns import MERCENARIES, mercenary_role, mercenary_skill_lines_v12211
from systems.mercenary_specialists_v1240 import (
    SPECIALISTS, _MERC_VOICES_V1270, specialist_attack_v1240,
    specialist_support_on_strike_v1240, mercenary_preferred_combo_v1270,
    mercenary_voice_v1270,
)
from systems.companion_tactics_v4000 import FINISHERS, BREAKERS, GUARDIANS, tactical_response
from systems.mercenary_memory_v1250 import memory_choice_v1250, memory_learn_v1250


def run_regression():
    checks = 0
    def ck(value, message):
        nonlocal checks
        assert value, '38 najemnikow: ' + message
        checks += 1

    historical = {c[0] for c in CLASSES}
    additions = {MAGITEK} | {c[0] for c in CHAOS} | {c[0] for c in EXPANSION}
    complete = historical | additions
    ck(len(historical) == 22 and len(additions) == 16 and len(complete) == 38,
       'true authored playable class coverage')
    ck(len(MERCENARIES) == len(SPECIALISTS) == len(complete) == 38,
       'every playable class has one hireable NPC and specialty')
    ck(set(MERCENARIES) == set(SPECIALISTS) == set(_MERC_VOICES_V1270),
       'each hire has specialty and distinct speech')
    ck({s['class'] for s in MERCENARIES.values()} == complete,
       'no duplicate/missing playable class')
    ck(len({s['name'].casefold() for s in MERCENARIES.values()}) == 38,
       'unique NPC names')
    ck(set(MERCENARIES) == FINISHERS | BREAKERS | GUARDIANS and
       not (FINISHERS & BREAKERS or FINISHERS & GUARDIANS or BREAKERS & GUARDIANS),
       'every role has exactly one class tactic')
    ck(MERCENARIES['paladyn']['name'] == 'Seren' and
       MERCENARIES['lucznik']['name'] == 'Riven' and
       mercenary_role('Łucznik') == 'lucznik', 'historical contracts preserved')

    natural_abilities = {row[0]: row[6][0] for row in CHAOS}
    natural_abilities.update({row[0]: row[6] for row in EXPANSION})
    natural_abilities[MAGITEK] = 'Impuls Rdzenia Magiteka'
    new_roles = [r for r, spec in MERCENARIES.items() if spec['class'] in additions]
    ck(len(new_roles) == 16, '16 genuinely new hires')
    for role, spec in MERCENARIES.items():
        ck(mercenary_role(spec['name']) == mercenary_role(spec['class']) == role,
           'hire by NPC name and playable class: '+role)
        ck(spec['attack_type'] in ('physical', 'magic') and spec['cost'] > 0 and spec['power'] > 0,
           'valid battle type and one-time cost: '+role)
        profile = SPECIALISTS[role]
        ck(len(profile) == 5 and len(set(profile[2:])) == 3 and
           profile[2] == spec['ability'], 'three unique usable techniques: '+role)
        ck(bool(mercenary_skill_lines_v12211(role)) and
           spec['ability'] in ' '.join(mercenary_skill_lines_v12211(role)),
           'skill list can be read through NVDA: '+role)
        ck(bool(mercenary_voice_v1270(role, 4, boss=True)),
           'boss speech available: '+role)
        buff, technique, reaction = specialist_attack_v1240(
            SimpleNamespace(hp=150, max_hp=500), 101, role,
            spec['attack_type'], 300, 10.0, boss=True)
        ck(buff >= 1.0 and bool(technique) and isinstance(reaction, str),
           'real offensive specialist during boss battle: '+role)
        ck(tactical_response(role, True, 200, 1000, 1)[0] >= 1.0,
           'boss tactics do not reduce owner-powered damage: '+role)
        if role in new_roles:
            ck(spec['ability'] == natural_abilities[spec['class']],
               'offensive ability matches playable class: '+role)
            session = SimpleNamespace(server=None, account_id=100)
            move, index, key = memory_choice_v1250(session, role, 'test_species', profile[2], 0)
            ck(move in profile[2:] and 0 <= index < 3 and key[0] == role,
               'real tactical memory selects class skill: '+role)
            memory_learn_v1250(session, key, index, 100, 100, 200)
            ck(sum(session._mercenary_memory_v1250[key]['attempts']) == 1,
               'tactical memory persisted in isolated session: '+role)

    for role in ('tkacz_dusz', 'szeptacz_bestii', 'paladyn_zmierzchu'):
        ally = SimpleNamespace(current_hp=600, max_hp=lambda: 1000, skill_guard=0,
                               character=SimpleNamespace(name='Wojownik'))
        result = specialist_support_on_strike_v1240(role, ally, 100, True, False)
        ck(ally.current_hp > 600 and result.startswith('Regeneracja'),
           'healing companion heals real ally '+role)
        noheal = SimpleNamespace(current_hp=600, max_hp=lambda: 1000, skill_guard=0,
                                 character=SimpleNamespace(name='Wojownik'))
        result2 = specialist_support_on_strike_v1240(role, noheal, 100, True, True)
        ck(noheal.current_hp == 600 and 'Regeneracja' not in result2,
           'healing respects anti-heal '+role)
    for role in ('runiczny_obronca','straznik_przyplywow'):
        ally = SimpleNamespace(current_hp=700, max_hp=lambda: 1000, skill_guard=0,
                               character=SimpleNamespace(name='Wojownik'))
        result = specialist_support_on_strike_v1240(role, ally, 100, True, False)
        ck(ally.skill_guard > 0 and 'osłona' in result,
           'guardian actually shields party '+role)
    for role in new_roles:
        partner = next((other for other in MERCENARIES if other != role and
                        mercenary_preferred_combo_v1270(role, (other,))[0]), None)
        ck(partner is not None and mercenary_preferred_combo_v1270(role,(partner,))[1] > 1,
           'unique effective two-hire synergy: '+role)

    class DB(DatabaseMercenariesMixin):
        def __init__(self):
            self.conn = sqlite3.connect(':memory:')
            self.conn.row_factory = sqlite3.Row
            self.conn.execute('CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY,silver INTEGER)')
            self.conn.executemany('INSERT INTO account_wallet VALUES(?,?)',
                                  [(i, 200000) for i in range(1, 40)])
            # A historical contract exists before the new class catalog boots.
            self.conn.execute('CREATE TABLE mercenary_contracts '
                              '(character_account_id INTEGER NOT NULL,role TEXT NOT NULL,'
                              'expires_at REAL NOT NULL,PRIMARY KEY(character_account_id,role))')
            self.conn.execute('INSERT INTO mercenary_contracts VALUES(1,?,0)', ('paladyn',))
            self.create_mercenary_schema()
        def master_account_for_character(self, account_id):
            return int(account_id)
        def shared_wallet_for_master(self, master):
            return (self.conn.execute('SELECT silver FROM account_wallet WHERE master_account_id=?',
                                      (master,)).fetchone()['silver'],0,0)
        def set_shared_wallet_for_master(self, master, silver, gold, mithril, *, commit=True):
            self.conn.execute('UPDATE account_wallet SET silver=? WHERE master_account_id=?',
                              (silver,master))
            if commit:self.conn.commit()
    db = DB()
    ck(db.mercenary_contracts(1) == [{'role':'paladyn','expires_at':0}],
       'old permanent contract survives current schema boot')
    for i,role in enumerate(new_roles,2):
        amount = MERCENARIES[role]['cost']*100
        before=db.shared_wallet_for_master(i)[0]
        ck(db.hire_mercenary(i,role,amount) == 'ok',
           'new class can sign permanent contract: '+role)
        ck(db.hire_mercenary(i,role,amount) == 'duplicate',
           'same hire does not charge again: '+role)
        ck(db.shared_wallet_for_master(i)[0] == before-amount,
           'contract charges only one time: '+role)
        ck(db.mercenary_contracts(i)[0] == {'role':role,'expires_at':0},
           'contract persists separately per account: '+role)
        ck(db.mercenary_set_tactic_v1229(i,role,'obrona') == 'ok' and
           db.mercenary_progress_v1220(i,role)['specialization'] == 'obrona',
           'new class tactic saved without schema change: '+role)
    ck(db.hire_mercenary(1, new_roles[0], 100) == 'ok' and
       db.hire_mercenary(1,new_roles[1],100) == 'ok' and
       db.hire_mercenary(1,new_roles[2],100) == 'full',
       'three total hires including historical contract; fourth rejected')
    ck(len(db.mercenary_contracts(1)) == 3 and
       len(db.mercenary_contracts(2)) == 1, 'no cross-account hire mixing')
    old_balance = db.shared_wallet_for_master(1)[0]
    db.create_mercenary_schema()
    ck(len(db.mercenary_contracts(1)) == 3 and
       db.shared_wallet_for_master(1)[0] == old_balance,
       'schema restart preserves old/new hires and wallet')
    db.conn.close()
    return checks

if __name__ == '__main__':
    print('CURRENT 38 MERCENARIES: '+str(run_regression())+' PASS')
