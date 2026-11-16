# -*- coding: utf-8 -*-
"""Account-owned durable command shortcuts, without eval or nested expansion."""
from __future__ import annotations
import re

_NAME = re.compile(r"[a-zA-Z0-9_]{1,24}\Z")


def _connection(session):
    return session.server.db.conn


def _init(conn):
    if getattr(conn, '_player_alias_table_ready_v11325', False):
        return
    conn.execute("""CREATE TABLE IF NOT EXISTS player_command_aliases_v11325 (
        account_id INTEGER NOT NULL, alias_name TEXT NOT NULL,
        command_text TEXT NOT NULL,
        PRIMARY KEY(account_id, alias_name),
        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
    )""")
    # SQLite connections do not support arbitrary attributes. CREATE TABLE
    # IF NOT EXISTS is safe to repeat; no silent exception is required.


def _safe_name(name):
    from player.session_mixins.command_registry import resolve_session_command
    from core.command_catalog import COMMAND_CATALOG
    from core.mines_threat import DIRECTION_ALIASES
    name = name.casefold()
    if not _NAME.fullmatch(name) or name in ('alias', 'aliases', 'aliasy'):
        return False
    # Unknown command tokens fall through unchanged in the command parser.
    # Only a real registered command counts as a collision.
    resolved = resolve_session_command(name)
    return COMMAND_CATALOG.definition(resolved) is None and name not in DIRECTION_ALIASES


async def process_alias_input(session, raw):
    """Return (handled, input). Only expand one command; numeric menu has priority."""
    if session.account_id is None or session.character is None:
        return False, raw
    parts = raw.strip().split(maxsplit=2)
    if not parts:
        return False, raw
    head = parts[0].casefold()
    conn = _connection(session)
    if head in ('alias', 'aliasy', 'aliases'):
        _init(conn)
        if len(parts) == 1 or parts[1].casefold() in ('lista', 'list'):
            rows = conn.execute('SELECT alias_name, command_text FROM player_command_aliases_v11325 WHERE account_id=? ORDER BY alias_name', (session.account_id,)).fetchall()
            await session.send('Aliasy: ' + ('; '.join(f'{n} = {c}' for n,c in rows) if rows else 'brak') + '.')
            await session.send('Dodaj: alias 1 use cosmic rave. Usuń: alias usuń 1.')
            return True, raw
        if parts[1].casefold() in ('usun', 'usuń', 'delete', 'remove'):
            name = parts[2].strip().casefold() if len(parts)>2 else ''
            if not _NAME.fullmatch(name):
                await session.send('Podaj nazwę aliasu do usunięcia.')
            else:
                conn.execute('DELETE FROM player_command_aliases_v11325 WHERE account_id=? AND alias_name=?', (session.account_id,name))
                conn.commit()
                await session.send('Alias usunięty: ' + name + '.')
            return True, raw
        if len(parts)<3 or not _safe_name(parts[1]):
            await session.send('Podaj wolną nazwę aliasu oraz komendę. Nie można nadpisywać komend gry.')
            return True, raw
        name, command = parts[1].casefold(), parts[2].strip()
        if not command or len(command)>300 or command.split()[0].casefold() in ('alias', 'aliasy', 'aliases') or '\n' in command or '\r' in command:
            await session.send('Nieprawidłowe polecenie aliasu.')
            return True, raw
        conn.execute('INSERT INTO player_command_aliases_v11325(account_id,alias_name,command_text) VALUES(?,?,?) ON CONFLICT(account_id,alias_name) DO UPDATE SET command_text=excluded.command_text',(session.account_id,name,command))
        conn.commit()
        await session.send('Alias zapisany: '+name+'.')
        return True, raw
    name = head
    if not _NAME.fullmatch(name):
        return False, raw
    _init(conn)
    row = conn.execute('SELECT command_text FROM player_command_aliases_v11325 WHERE account_id=? AND alias_name=?',(session.account_id,name)).fetchone()
    if row is None:
        return False, raw
    # Remaining parameters may supplement a stored command; never re-expand.
    rest = raw.strip().split(maxsplit=1)
    suffix = rest[1] if len(rest)>1 else ''
    expanded = row[0] + (' ' + suffix if suffix else '')
    if expanded.strip().split()[0].casefold() in ('alias','aliases','aliasy'):
        await session.send('Alias nie może uruchamiać administracji aliasami.')
        return True, raw
    return False, expanded
