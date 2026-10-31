# -*- coding: utf-8 -*-
"""v104 stage 12: explicit source audit of numeric routes, never edits files.

The presence of a route in this report does not mean it is fully converted.
Unlike a misleading 'all caps removed' check, this is a conservative blocker list.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# file, critical operation, axis, known blocker that still requires conversion
ROUTES = (
    ('storage/db_accounts.py', 'save_character', 'EXP / Soul XP / statystyki / waluty',
     'SQLite INTEGER, kontrola int64; brak aktywnego zapisu TEXT'),
    ('storage/db_accounts.py', 'shared_wallet_for_master', 'wspolny portfel',
     'SUM SQL usunieto w etapie 12; pozostaje INTEGER i brak odczytu TEXT'),
    ('storage/db_progression.py', 'add_class_mastery_xp', 'EXP i poziom klasy',
     'SQLite INTEGER, bez obslugi przekroczen int64'),
    ('storage/db_inventory.py', 'save_profession', 'profesja poziom / EXP',
     'SQLite INTEGER, poziomy i EXP do migracji'),
    ('storage/db_inventory.py', 'save_tool', 'narzedzie poziom / EXP',
     'SQLite INTEGER, poziomy i EXP do migracji'),
    ('storage/db_experience_bank_v2011.py', 'allocate_experience_bank_v2011',
     'bank nadwyzek EXP', 'TEXT juz istnieje; przeanalizowac atomowosc z zapisem postaci'),
    ('storage/big_number_ledger_v10400.py', 'add_exact_copy', 'ledger TEXT',
     'dziala na kopii i nie jest zintegrowany z gra'),
    ('storage/big_number_events_v10400.py', 'apply_event_copy', 'pokwitowania EXP / walut',
     'operacje idempotentne tylko na kopii; brak zintegrowanego runtime'),
    ('systems/world_invasions_v10400.py', 'create_schema', 'inwazje globalne',
     'oddzielna tabela wydarzen; nie jest migracja sald postaci'),
)


def inspect_sources(root: Path = ROOT) -> dict:
    results = []
    for path, marker, axis, issue in ROUTES:
        target = root / path
        exists = target.is_file()
        found = exists and marker in target.read_text(encoding='utf-8')
        results.append({'file': path, 'method': marker, 'axis': axis,
                        'issue': issue, 'found': bool(found)})
    return {'routes': results,
            'identified': sum(r['found'] for r in results),
            'expected': len(results),
            'converted_for_unlimited_live_progression': False}


def render_pl(report: dict) -> str:
    lines = [
        'AUDYT SCIEZEK LICZBOWYCH V104 – ETAP 12',
        'UWAGA: NIE JEST TO ZGODA NA WDROZENIE.',
        f"Znalezione sciezki: {report['identified']}/{report['expected']}",
        'Prawdziwy rozwoj ponad int64: NIEGOTOWY.',
        '',
    ]
    for r in report['routes']:
        lines.append(('ZNALEZIONO' if r['found'] else 'BRAK / ZMIANA KODU')
                     + ': ' + r['file'] + ' :: ' + r['method'])
        lines.append('  Dotyczy: ' + r['axis'])
        lines.append('  Blokada: ' + r['issue'])
    lines += ['',
        'Warunki odblokowania: zintegrowac odczyty i zapisy TEXT ze wszystkimi'
        ' trasami EXP, klas, profesji, narzedzi, walut, hp i obrazen;'
        ' naprawic SQL SUM / cast / porownania; wykonac migracje i rollback na'
        ' kopii bazy; testy TCP i Windows PREDEPLOY.',
        'Nie wlaczac migracji przez podmiane typu kolumny bez sprawdzenia wszystkich tras.'
    ]
    return '\n'.join(lines)+'\n'


def main():
    print(render_pl(inspect_sources()))


if __name__ == '__main__':
    main()
