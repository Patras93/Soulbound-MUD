# -*- coding: utf-8 -*-
"""v105 — trwała, atomowa ewolucja posiadanego szablonu EQ.

Stare ID przedmiotów, runy, gniazda, przekucia i poziomy +1..+10
pozostają nietknięte. Tak jak istniejący system ulepszania, postęp
odnosi się do jednego typu przedmiotu danego konta, nie do osobnych
kopii o identycznym ID. Dlatego dopuszczamy tylko jedną posiadaną kopię.
"""
import sqlite3
from world.v10500_region_index import REGIONS

MAX_STAGE = 10
KEY_PREFIX = 'eq_evolution_v10500:'
LIVE_TUNING = {'v10500_ewolucja_eq': {'stat_pct': 100, 'defense_pct': 100}}


def record_key(item_id):
    item_id = str(item_id)
    if not item_id or len(item_id) > 150:
        raise ValueError('Nieprawidłowy identyfikator EQ.')
    return KEY_PREFIX + item_id


def is_evolved(conn, account_id, item_id):
    """True when this account owns a character-bound evolved equipment template.

    The v105 ledger stores one stage per (account,item ID), not per inventory
    copy. Until per-instance IDs exist, moving an evolved item could silently
    lose its bonus or let a later replacement inherit an unearned stage.
    """
    try:
        row = conn.execute(
            'SELECT value FROM player_records_v03051 WHERE account_id=? AND record_key=?',
            (account_id, record_key(item_id)),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        # Older import/test databases may omit the v0.30.51 records table.
        # Such databases cannot contain evolved gear. All other SQL errors
        # must propagate (do not silently bypass a damaged production table).
        if str(exc) == 'no such table: player_records_v03051':
            return False
        raise
    return bool(row and int(row[0]) > 0)


def current_stage(conn, account_id, item_id):
    row = conn.execute(
        'SELECT value FROM player_records_v03051 WHERE account_id=? AND record_key=?',
        (account_id, record_key(item_id)),
    ).fetchone()
    return max(0, min(MAX_STAGE, int(row[0]))) if row else 0


def required_materials(next_stage):
    stage = int(next_stage)
    if not 1 <= stage <= MAX_STAGE:
        raise ValueError('Nieprawidłowy etap ewolucji.')
    slug = REGIONS[(stage - 1) * 2][0]
    return {f'v10500_{slug}_alloy': 1 + stage, f'v10500_{slug}_material_3': 2 + stage}


def stage_stat_bonus(stage, item):
    """Rzeczywisty bonus KON założonego EQ, niezależny od run i przekucia."""
    stage = max(0, min(MAX_STAGE, int(stage)))
    return max(1, stage * max(1, int(item.get('affix_amount', 0) or 0) // 40) * LIVE_TUNING['v10500_ewolucja_eq']['stat_pct'] // 100) if stage else 0


def stage_defense_bonus(stage, item):
    stage = max(0, min(MAX_STAGE, int(stage)))
    return max(1, stage * max(1, int(item.get('defense', 0) or 0) // 80) * LIVE_TUNING['v10500_ewolucja_eq']['defense_pct'] // 100) if stage else 0


def evolve(conn, account_id, item_id, item):
    """Jedna nieprzerywalna operacja: zużycie dwóch materiałów + zapis etapu.

    Bez DDL i bez zmian inwentarza, parametrów szablonu ani run.
    Zwraca (success, message, stage) i nie zużywa surowców przy odmowie.
    """
    if not isinstance(item, dict) or item.get('type') != 'armor':
        return False, 'Ewolucja dotyczy wyłącznie istniejącego wyposażenia ochronnego.', 0
    key = record_key(item_id)
    outer = conn.in_transaction
    conn.execute('SAVEPOINT soulbound_eq_evolve_v10500')
    try:
        owned = conn.execute(
            'SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',
            (account_id, item_id),
        ).fetchone()
        count = int(owned[0]) if owned else 0
        if count != 1:
            detail = 'Brak przedmiotu.' if count == 0 else 'Masz kilka identycznych kopii. Zachowaj jedną przed ewolucją.'
            conn.execute('RELEASE SAVEPOINT soulbound_eq_evolve_v10500')
            return False, detail, 0
        old = current_stage(conn, account_id, item_id)
        if old >= MAX_STAGE:
            conn.execute('RELEASE SAVEPOINT soulbound_eq_evolve_v10500')
            return False, f'Osiągnięto maksymalny etap ewolucji {MAX_STAGE}.', old
        target = old + 1
        materials = required_materials(target)
        for material_id, qty in materials.items():
            row = conn.execute(
                'SELECT quantity FROM profession_storage WHERE account_id=? '
                'AND container=? AND item_id=?', (account_id, 'craftbox', material_id),
            ).fetchone()
            have = int(row[0]) if row else 0
            if have < qty:
                conn.execute('RELEASE SAVEPOINT soulbound_eq_evolve_v10500')
                return False, f'Za mało materiału {material_id}: masz {have}, potrzeba {qty}.', old
        for material_id, qty in materials.items():
            cursor = conn.execute(
                'UPDATE profession_storage SET quantity=quantity-? '
                'WHERE account_id=? AND container=? AND item_id=? AND quantity>=?',
                (qty, account_id, 'craftbox', material_id, qty),
            )
            if cursor.rowcount != 1:
                raise RuntimeError('Konflikt magazynu; materiały nie zostały zużyte.')
        conn.execute(
            'INSERT INTO player_records_v03051(account_id,record_key,value) VALUES(?,?,?) '
            'ON CONFLICT(account_id,record_key) DO UPDATE SET '
            'value=excluded.value,updated_at=CURRENT_TIMESTAMP',
            (account_id, key, target),
        )
        conn.execute('RELEASE SAVEPOINT soulbound_eq_evolve_v10500')
        if not outer:
            conn.commit()
        return True, f'Ewolucja EQ {target}/{MAX_STAGE} zapisana. Runa, przekucie i oryginalny przedmiot zachowane. Ewoluowane EQ jest przypisane do postaci (bez handlu).', target
    except Exception:
        conn.execute('ROLLBACK TO SAVEPOINT soulbound_eq_evolve_v10500')
        conn.execute('RELEASE SAVEPOINT soulbound_eq_evolve_v10500')
        raise


def reset_evolution(conn, account_id, item_id):
    """Explicitly unbind equipment by sacrificing all v105 evolution stages.

    No material refund (prevents reuse farming); all legacy runes and reforges
    are untouched. Designed for an intentional trade after player confirmation.
    Respects the caller's transaction boundary.
    """
    key = record_key(item_id)
    outer = conn.in_transaction
    conn.execute('SAVEPOINT sb105_eq_reset')
    try:
        row = conn.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',
                           (account_id, item_id)).fetchone()
        if row is None or int(row[0]) < 1:
            conn.execute('RELEASE SAVEPOINT sb105_eq_reset')
            return False, 'Aby zdjąć ewolucję, musisz posiadać ten przedmiot.'
        stage = current_stage(conn, account_id, item_id)
        if stage <= 0:
            conn.execute('RELEASE SAVEPOINT sb105_eq_reset')
            return False, 'Ten przedmiot nie ma etapów ewolucji.'
        conn.execute('DELETE FROM player_records_v03051 WHERE account_id=? AND record_key=?',
                     (account_id, key))
        conn.execute('RELEASE SAVEPOINT sb105_eq_reset')
        if not outer:
            conn.commit()
    except Exception:
        conn.execute('ROLLBACK TO SAVEPOINT sb105_eq_reset')
        conn.execute('RELEASE SAVEPOINT sb105_eq_reset')
        raise
    return True, f'Usunięto {stage} etapów ewolucji bez zwrotu materiałów. Przedmiot można teraz przekazać lub sprzedać.'
