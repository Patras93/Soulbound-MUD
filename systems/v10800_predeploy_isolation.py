# -*- coding: utf-8 -*-
"""Explicit fail-closed permissions for local v108 PREDEPLOY TCP test servers.

All conditions are required: a copied candidate tree in TEMP, a known private
SQLite fixture in TEMP, loopback-only networking, and an explicit test flag.
No production approval is granted; production still requires v108 activation.
"""
from __future__ import annotations
import os
from pathlib import Path
import re
import tempfile


def authorized_predeploy_test(root, db_path, env=None, temp_root=None):
    env = os.environ if env is None else env
    if env.get('SOULBOUND_V108_PREDEPLOY') != '1':
        return False
    if env.get('SOULBOUND_HOST') != '127.0.0.1':
        return False
    try:
        port = int(env.get('SOULBOUND_PORT', ''))
        if not (1025 <= port <= 65535) or port == 4000:
            return False
        temporary = Path(temp_root or tempfile.gettempdir()).resolve()
        source = Path(root).resolve()
        database = Path(db_path).resolve()
        parts = source.relative_to(temporary).parts
        db_parts = database.relative_to(temporary).parts
    except (ValueError, TypeError, OSError):
        return False
    if not parts or not db_parts or len(db_parts) < 2:
        return False

    # The worker is a copy of the candidate, not the original C:\Soulbound-MUD.
    worker = (len(parts) == 2 and
              parts[0].lower().startswith('soulbound-predeploy-workers-') and
              re.fullmatch(r'candidate-[0-9]+', parts[1].lower()) is not None)
    initial_stage = (len(parts) == 2 and
                     parts[0].lower().startswith('soulbound_predeploy_') and
                     parts[1].lower() == 'soulbound-mud')
    legacy_nested = (len(parts) == 2 and parts[0].lower().startswith((
        'sb103-real-tcp-', 'sb103-other-raids-', 'sb103-tcp-raid-real-'))
        and parts[1].lower() in ('server_source', 'private_game'))
    # v85 UOSS full-TCP audit starts a second, fully disposable game tree:
    # TEMP/Soulbound_UOSS_REAL_<random>/gra/soulbound.db. The outer launcher
    # snapshots a *synthetic* DB and strips credentials before running it.
    # This exemption is for that single private copy ONLY; it never permits a
    # normal install folder, remote listener, port 4000 or arbitrary DB path.
    uoss_private = (len(parts) == 2 and
                    parts[0].lower().startswith('soulbound_uoss_real_') and
                    parts[1].lower() == 'gra' and
                    database == source / 'soulbound.db')
    if not (worker or initial_stage or legacy_nested or uoss_private):
        return False

    name = database.name.lower()
    if uoss_private:
        return name == 'soulbound.db'
    folder = database.parent.name.lower()
    if name == 'audit.sqlite' and folder.startswith('soulbound-predeploy-stage-'):
        return True
    if name == 'five_players.sqlite' and (
        folder.startswith('soulbound-tcp5-') or
        (legacy_nested and database.parent == source)):
        return True
    if name == 'stress.db' and folder.startswith('sb-ultra-5-tcp-'):
        return True
    if name == 'wave.sqlite' and folder.startswith('sb-ultimate-tcp-waves-'):
        return True
    if name == 'tcp_test.sqlite' and folder.startswith('sb104_tcp_lab_'):
        return True
    return False
