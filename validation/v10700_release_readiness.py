# -*- coding: utf-8 -*-
"""Fail-closed production-readiness check for v107 (never self-certifies).

A catalogue PASS or old 60/60 alone must not be mistaken for a release PASS:
the new features have staging-only gameplay and require a live-safe EQ migration.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
_EQ_DIAGNOSTICS=[]

def eq_readiness_diagnostics():
    return tuple(_EQ_DIAGNOSTICS)


def unmet_requirements():
    _EQ_DIAGNOSTICS.clear()
    reasons=[]
    sources={rel:(ROOT/rel).read_text(encoding='utf-8-sig') for rel in (
        'server.py','world/dynamic_content.py','core/progression_600.py','core/live_level_caps_v5200.py',
        'systems/equipment_inventory_flow_v10600.py',
        'systems/equipment_evolution_command_v10600.py',
        'systems/v10700_equipment_write_barrier.py',
        'systems/v10700_eq_runtime_gate.py',
        'systems/v10700_live_equipment.py','server/mud_server.py',
        'storage/database.py',
        'aktualizuj_soulbound.py', 'wdroz_po_predeploy.py',
        'world/v10700_saga_760_quests.py',
        'world/v10700_saga_events_calendar.py',
        'player/session_mixins/quest_offers.py',
        'player/session_mixins/command_registry.py',
        'wdroz_v107_z_zewnatrz.py', 'systems/v10700_activation.py')}
    # These blockers are independently derived from actual v107 code; never
    # silently remove one to pass a release. A real audited implementation
    # must remove the limitation and pass its own clone/TCP tests.
    # v107 content is authorised on normal startup only when the updater has
    # installed a matching 60/60 PLUS activation marker, with the exact ZIP
    # and critical source files still intact. Independent regression exercises
    # both rejection and authorised bootstrap without staging environment.
    approval_source=sources['systems/v10700_activation.py']
    production_path=(
        'v107_release_activation.json' in approval_source
        and "state.get('status') != 'PASS'" in approval_source
        and "state.get('completed_stages') != 60" in approval_source
        and 'archive.read(entry)' in approval_source
        and "'v107_release_activation.json'" in sources['aktualizuj_soulbound.py'])
    if not (production_path and '_sb107_runtime_enabled()' in sources['server.py']):
        reasons.append('nowe klasy v107 uruchamia wyłącznie ręczna flaga robocza')
    if not (production_path and sources['world/dynamic_content.py'].count('_sb107_runtime_enabled()') >= 5):
        reasons.append('30 krain / 2000 questów działa wyłącznie w stagingu')
    # Check actual production DB bootstrap, not a staging *string* in one module.
    # Refactoring a flag into an imported helper MUST NOT remove a blocker.
    db_runtime=sources['storage/database.py']
    guard=sources['systems/v10700_equipment_write_barrier.py']
    live=sources['systems/v10700_live_equipment.py']
    runtime=sources['server/mud_server.py']
    eq_live=(
        '_v107_eq_live_active = False' in db_runtime
        and 'def activate_production_ledger' in live
        and 'def _backup_and_check' in live
        and 'def _check_all_accounts' in live
        and "'v107_eq_production_cutover'" in live
        and '_require_approved()' in live
        and 'install_on_migrated_connection' in live
        and 'activate_production_ledger(self.db, ITEMS)' in runtime
        and "'systems/v10700_live_equipment.py'" in approval_source
        and 'def approved_instance_operation' in guard
        and 'v107_eq_instance_mutation_allowed' in guard
        and "'equipment_reforges'" in guard
    )
    evolution=sources['systems/equipment_evolution_command_v10600.py']
    evolution_live=(eq_live and 'def production_copy_evolution' in live
                    and 'production_copy_evolution(db,session.account_id,slot,uid)' in evolution
                    and 'def _evolve_equipped_copy_transaction' in (
                        ROOT/'systems/equipment_evolution_stats_v10600.py').read_text(encoding='utf-8-sig'))
    # Do not trust only source-code token checks. Execute real SQLite migration,
    # restart, rollback snapshot and evolution checks on disposable fixtures.
    if eq_live and evolution_live:
        try:
            from validation.v10700_production_eq_cutover_regression import run as _rehearse_eq
            result=_rehearse_eq()
            if result != 24:
                _EQ_DIAGNOSTICS.append('Proba 24 operacji EQ: niepelny wynik ('+str(result)+'/24).')
                eq_live=False; evolution_live=False
        except Exception as exc:
            # Report the safe exception type and Windows OS error code only.
            # Never record actual player details, paths, item IDs or database rows.
            code=getattr(exc,'winerror',None) or getattr(exc,'errno',None)
            _EQ_DIAGNOSTICS.append('Proba EQ: '+type(exc).__name__+
                                   (' kod OS '+str(code) if code is not None else ''))
            eq_live=False; evolution_live=False
    if not eq_live:
        reasons.append('fizyczne EQ 2.0 nie ma produkcyjnego ledgeru z migracją i ochroną handlu')
    if not evolution_live:
        reasons.append('ewolucja fizycznych kopii EQ nadal wymaga stagingu v106')
    # Authoring tests require a frozen 1..800 baseline. Runtime after an
    # approved v107 cutover can use unlimited caps without changing it.
    caps=sources['core/live_level_caps_v5200.py']
    runtime_caps=('activate_v107_uncapped_defaults' in caps
                  and 'if disk!=DEFAULTS:' in caps
                  and 'for key in OLD_KEYS_V52:' in caps
                  and "next_values['eq']=None" in caps
                  and '_v107_uncap()' in sources['server.py'])
    if not runtime_caps:
        reasons.append('podstawowe poziomy/profesje/narzędzia mają limit 800 (nie bez końca)')
    # Assert the real end-to-end event wiring, not just a removed TODO text.
    event_wiring=(
        "v10700_event_rotation=True" in sources['world/v10700_saga_760_quests.py']
        and 'active_quest_ids' in sources['world/v10700_saga_events_calendar.py']
        and "if quest.get('v10700_event_rotation')" in sources['player/session_mixins/quest_offers.py']
        and "'wydarzenia107': ('show_v107_chaos_events'" in sources['player/session_mixins/command_registry.py']
    )
    if event_wiring:
        from world.v10700_saga_events_calendar import active_quest_ids,is_active
        windows=[set(active_quest_ids(n*3600)) for n in range(6)]
        event_wiring=(all(len(x)==10 for x in windows)
                      and len(set().union(*windows))==60
                      and all(not windows[i]&windows[j] for i in range(6) for j in range(i+1,6))
                      and is_active('v10700_saga_events_001',0))
    if not event_wiring:
        reasons.append('nowe zadania wydarzeń nie mają zweryfikowanego harmonogramu v107')
    # The approved candidate has its own external bridge, since the old
    # installed v106 scripts cannot be replaced before an authorized upgrade.
    updater=sources['aktualizuj_soulbound.py']
    if ("V106 KOD ROBOCZY: AKTUALIZACJA ZABLOKOWANA" in updater
            or updater.count('require_v104_official_predeploy(root, archive_path, new_version)')<2
            or 'run_update(live, approved, version' not in sources['wdroz_v107_z_zewnatrz.py']
            or 'check_candidate_matches_zip' not in sources['wdroz_v107_z_zewnatrz.py']):
        reasons.append('bezpieczny instalator v106→v107 nadal niedokończony')
    deploy=sources['wdroz_po_predeploy.py']
    if ('v106_work_in_progress_deploy_blocked' in deploy
            or "s.get('status')!='PASS'" not in deploy
            or 'sha256(z)' not in deploy
            or "input('Aby wdrozyc, wpisz dokladnie WDRAZAM: ')" not in deploy):
        reasons.append('WDROZ_PO_PREDEPLOY wymaga naprawy autoryzacji PASS i zgody gracza')
    return tuple(reasons)


def main():
    reasons=unmet_requirements()
    if reasons:
        print('V107 NIE JEST GOTOWE DO WDROŻENIA. TESTY 60/60 NIE MOGĄ NADPISAĆ TYCH BLOKAD:')
        for i,reason in enumerate(reasons,1):print(f'{i}. {reason}')
        print('WYNIK: FAIL; działający serwer v106 i bazy pozostają bez zmian.')
        return 3
    # Absence of code-level blockers is not itself a pass. Each required
    # production migration/TCP/rollback gate must be independently verified.
    print('Brak jawnych blokad w kodzie; pełne testy na kopii bazy i TCP wciąż obowiązkowe.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
