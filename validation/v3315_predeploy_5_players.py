# -*- coding: utf-8 -*-
"""v3.31.5: fail-closed coverage of a private five-player release gate.

Actual five-account TCP, sixth-connection refusal, one kill, NPC dialogue,
quest sharing and restart are carried out by mandatory stage 9. This check
prevents that stage and the two banner-only stages from drifting back to
larger client counts; it checks the new gates, it does not fake gameplay.
"""
from __future__ import annotations
import ast
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))



def five_account_profession_events():
    """All 200 new profession actions: five private accounts, wrong target and
    restart durability. Uses the game's real SQLite event method, NOT fake XP
    credits, a live server or a real crafting/item payout.
    """
    from contextlib import closing
    import sqlite3
    import tempfile
    import server  # register the exact current quests via game bootstrap
    from validation.v2400_real_quest_events import QuestEventDB
    from systems.profession_apprenticeship_v3313 import ADDED_IDS, QUEST_IDS_BY_PROFESSION
    from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700

    accounts=(101,102,103,104,105)
    if len(ADDED_IDS)!=200 or len(QUEST_IDS_BY_PROFESSION)!=14:
        raise AssertionError('200 questow profesji albo 14 profesji zniknelo')
    checks=2
    db=QuestEventDB()
    try:
        with db.conn:
            db.conn.executemany(
                'INSERT INTO quests(account_id,quest_id,status,progress) VALUES (?,?,?,0)',
                ((account,qid,'active') for account in accounts for qid in ADDED_IDS),
            )
        for ix,(prof,tool,_npc,_desc) in enumerate(PROFESSION_QUEST_SPECS_V0700):
            selected=accounts[ix%len(accounts)]
            expected=set(QUEST_IDS_BY_PROFESSION[prof])
            result=db.increment_profession_action_quests_v0700(selected,prof,tool,1)
            if {row[0] for row in result} != expected:
                raise AssertionError(f'{prof}: nie zaliczono prawdziwych akcji')
            checks+=1
            # Invalid profession/tool and zero actions must not grant progress.
            assert db.increment_profession_action_quests_v0700(selected,'bad-test-profession',tool,1)==[]
            assert db.increment_profession_action_quests_v0700(selected,prof,tool,0)==[]
            checks+=2
            for aid in accounts:
                for qid in expected:
                    row=db.conn.execute('SELECT progress FROM quests WHERE account_id=? AND quest_id=?',
                                        (aid,qid)).fetchone()
                    if int(row['progress']) != int(aid==selected):
                        raise AssertionError(f'{prof}/{qid}: wyciek progresu miedzy kontami {aid}')
                    checks+=1
        # sqlite3.backup simulates an independent read after persist; no live DB.
        with tempfile.TemporaryDirectory(prefix='sb-3315-5prof-') as td:
            snapshot=Path(td)/'five_accounts.sqlite'
            with closing(sqlite3.connect(snapshot)) as target:
                db.conn.backup(target)
            with closing(sqlite3.connect(snapshot)) as reopened:
                assert reopened.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                checks+=1
                for ix,(prof,_tool,_npc,_desc) in enumerate(PROFESSION_QUEST_SPECS_V0700):
                    chosen=accounts[ix%len(accounts)]
                    for qid in QUEST_IDS_BY_PROFESSION[prof]:
                        saved=reopened.execute('SELECT progress FROM quests WHERE account_id=? AND quest_id=?',
                                               (chosen,qid)).fetchone()
                        if saved is None or int(saved[0])!=1:
                            raise AssertionError(f'{qid}: zapis postepu po restarcie bazy')
                        checks+=1
        return checks
    finally:
        db.close()

def run_regression():
    import testuj_soulbound_windows as gate
    from validation import v2102_tcp_six_players as tcp
    from validation import v2302_exhaustive_game_coverage as registry
    from core.bootstrap_economy_professions import VERSION
    from config.balance import ALL_PROGRESS_XP_REQUIREMENT_MULTIPLIER_V3310
    from validation.v2102_tcp_six_players import run_contract

    checks = run_contract()
    def check(ok, message):
        nonlocal checks
        if not ok: raise AssertionError('PREDEPLOY 5P: '+message)
        checks += 1

    check(VERSION in ('3.31.5', '4.00.0', '4.00.1','4.00.2','4.00.3','4.00.4','4.00.5','4.00.6','4.00.7','4.10.0','4.20.0','4.21.0','4.21.1','5.00.0','5.00.1','6.00.0','6.00.1','7.00.0'), 'runtime version mismatch')
    check(ALL_PROGRESS_XP_REQUIREMENT_MULTIPLIER_V3310 == 10, 'EXP multiplier changed')
    check(tcp.PLAYERS == 5, 'stage 9 must use five clients')
    check(len(gate.STAGES) == 60, '60-stage legacy gate must stay complete')
    check('5 KLIENTOW' in gate.STAGES[8][0], 'stage 9 label must be accessible')
    check('5 SESJI' in gate.STAGES[23][0], 'stage 24 label must be accessible')
    check('3 FALE PO 5' in gate.STAGES[49][0], 'stage 50 label must be accessible')
    check(len(registry.READ_TCP_CASES)==25, '25 distinct read-only commands on each client')
    check(len(registry.ADDITIONAL_TCP_CASES)==14, '14 extra scenarios still present')

    # Verify the actual function bodies, not just expected config in one fixture.
    funcs = {'validation/predeploy_ultra_v2327.py': 'case_twenty_tcp',
             'validation/predeploy_ultimate_v2328.py': 'repeated_tcp_waves'}
    for filename, fn in funcs.items():
        tree=ast.parse((ROOT/filename).read_text(encoding='utf-8'))
        function=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==fn),None)
        check(function is not None,f'{filename}: missing stage implementation')
        calls=[]; settings=[]
        for node in ast.walk(function):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='range':
                if len(node.args)==1 and isinstance(node.args[0],ast.Constant):
                    calls.append(node.args[0].value)
            if isinstance(node,ast.keyword) and node.arg=='SOULBOUND_MAX_CLIENTS':
                if isinstance(node.value,ast.Constant): settings.append(node.value.value)
        check(5 in calls and not any(n in (6, 20, 24, 30, 35) for n in calls),
              f'{filename}: TCP wave exceeds 5')
        check(settings==['5'],f'{filename}: private server client cap not five')

    # Mandatory versioned regression suites and real TCP scenario must remain.
    source=(ROOT/'validation/v2320_autonomous_tcp.py').read_text(encoding='utf-8')
    check('assert len(clients) == 5' in source,'real party size guard')
    check('run_actual_npc_journey' in source and 'run_actual_delivery' in source,
          'NPC kill and courier test must remain')
    source=(ROOT/'validation/v2102_tcp_six_players.py').read_text(encoding='utf-8')
    check('Sixth connection not rejected' in source,'must test extra socket rejection')
    check('TCP QUEST DURABILITY: kill committed before restart PASS' in source,
          'must wait for independent SQLite durable proof')
    check('run_sqlite_cleanup_regression' in source,'cleanup handles must remain')
    for mod in ('v3312_all_world_events','v3313_profession_paths','v3314_required_xp'):
        check((ROOT/'validation'/f'{mod}.py').is_file(),f'missing regression {mod}')
    actions=five_account_profession_events()
    print(f'PREDEPLOY 5 KONT PROFESJE SQLite: {actions} checks PASS', flush=True)
    return checks+actions

if __name__=='__main__':
    print('PREDEPLOY 5 GRACZY v3.31.5:',run_regression(),'checks PASS',flush=True)
