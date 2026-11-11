# -*- coding: utf-8 -*-
"""Fail-closed v108 release contract. No access to player data or running game.

The v108 version keeps only v107 physical equipment. New EQ 2.0 was cancelled.
Existing v107 checks and the 60/60 Windows contract remain mandatory; no
v108 EQ migration, new cutover, or automatic reconciliation is authorized.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def release_at_least_108(version):
    try:
        parts = str(version).strip().split('.')
        if len(parts) != 3 or any(not part.isascii() or not part.isdigit() for part in parts):
            raise ValueError('Wymagany format wersji X.Y.Z')
        return tuple(int(part) for part in parts) >= (108, 0, 0)
    except (TypeError, ValueError) as exc:
        raise ValueError('Nieprawidlowy numer wersji kandydata') from exc


def unmet_requirements(root=ROOT):
    """Static source preflight is necessary, but never production approval."""
    root=Path(root)
    problems=[]
    activation=root/'systems/v10800_activation.py'
    compat=root/'validation/v10800_v107_equipment_compat_gate.py'
    server=root/'server/mud_server.py'
    updater=root/'aktualizuj_soulbound.py'
    tester=root/'testuj_soulbound_windows.py'
    bridge=root/'wdroz_v108_z_zewnatrz.py'
    predeploy=root/'predeploy_nowej_wersji.py'
    external_predeploy=root/'predeploy_v108_z_zewnatrz.py'
    for path,label in ((activation,'autoryzacja startu v108'),
                       (compat,'zgodnosc dotychczasowego EQ v107'),
                       (bridge,'pomost instalatora v107 do v108')):
        if not path.is_file():
            problems.append('Brak '+label)
    def has(path,*tokens):
        return path.is_file() and all(t in path.read_text(encoding='utf-8') for t in tokens)
    if not (has(activation,'v108_release_activation.json','v108_release_gates_pass',
                'REQUIRED','activation_manifest') and
            has(server,'activate_production_ledger','v107_eq_production_cutover','v10800_activation') and
            has(updater,'v108_release_activation.json','v108_release_gates_pass',
                'commit_verified_copy','restore_sqlite_from_backup') and
            has(predeploy,'verified_staged_pass','V108 RELEASE GATES PASS',
                'v108_eq_rebuild_trial_pass','prepare_from_snapshot') and
            has(external_predeploy,'preflight','pd.main')):
        problems.append('Brak autoryzacji startu v108 wspolnej dla serwera i instalatora')
    if not (has(compat,'v107_eq_production_cutover','query_only','v108_eq_production_cutover') and
            has(root/'systems/v10700_live_equipment.py','activate_production_ledger',
                '_check_all_accounts') and
            'activate_v108_production_ledger' not in server.read_text(encoding='utf-8')):
        problems.append('Nie zamrozono migracji EQ v108 lub brak ochrony v107')
    if not (has(tester,'V108 RELEASE GATES PASS',
                'validation/v10800_offline_suite.py',
                'validation/v10800_v107_equipment_compat_gate.py') and
            compat.is_file()):
        problems.append('Brak obowiazkowego Windows PREDEPLOY v108')
    if not has(root/'systems/v10800_eq_cutover_bridge.py',
               'prepare_from_snapshot','commit_verified_copy','restore_sqlite_from_backup'):
        problems.append('Brak bezpiecznej przebudowy i wycofania EQ na zatrzymanej bazie')
    if not (root/'VERSION').is_file() or (root/'VERSION').read_text(encoding='utf-8-sig').strip()!='108.00.0':
        problems.append('Kandydat nie ma numeru 108.00.0')
    return tuple(problems)


def main():
    missing = unmet_requirements()
    if missing:
        print('V108: KOD ROBOCZY, NIE WDRAZAC. NIESPELNIONE BRAMKI:')
        for index, message in enumerate(missing, 1):
            print(f'{index}. {message}')
        print('WYNIK: FAIL; 60/60 v107 nie uprawnia do wdrozenia v108.')
        return 3
    print('Bramki kodu v108 obecne; nadal wymagany niezalezny Windows PREDEPLOY i rzeczywista kopia danych.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
