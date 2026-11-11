# -*- coding: utf-8 -*-
"""v103 stage 3 — high-floor XP, saved Admin DRAFT, protected checkpoint titles."""
from __future__ import annotations

import asyncio
import json
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace


def run():
    import systems.admin_live_era_settings_v10300 as cfg
    import systems.era_dungeon_plus_v10300 as dl
    from systems.admin_live_era_v10300 import handle as handle_era
    from aktualizuj_soulbound import protected
    checks = 0

    def ok(value, text):
        nonlocal checks
        assert value, text
        checks += 1

    with tempfile.TemporaryDirectory(prefix='soul_era_dungeon_') as temp:
        old_path = cfg.CONFIG_PATH
        cfg.CONFIG_PATH = Path(temp) / 'era_v10300.json'
        cfg.reset_for_tests()
        try:
            for kind, field in dl.FLOOR_KEYS:
                for floor in (1, 25, 100, 799, 800):
                    t = {field: floor}
                    ok(dl.dungeon_identity(t) == (kind, floor), f'identity {kind}, {floor}')
                    ok(dl.reward_xp_v10300(t, 'class', 200000) == 200000, f'no change {kind}, {floor}')
                last = 0
                for floor in (801, 900, 901, 1000, 2000, 5000, 5001, 10000):
                    t = {field: floor}
                    value = dl.reward_xp_v10300(t, 'class', 200000)
                    ok(value >= 250000 and value >= last, f'progressive XP {kind}, {floor}')
                    ok(dl.reward_xp_v10300(t, 'soul', 200000) == value, f'soul {kind}, {floor}')
                    ok(dl.reward_xp_v10300(t, 'stat', 200000) == value, f'stat {kind}, {floor}')
                    ok(dl.reward_xp_v10300(t, 'character', 200000) == value, f'character {kind}, {floor}')
                    ok(dl.reward_xp_v10300(t, 'coins', 200000) == 200000, f'money {kind}, {floor}')
                    ok(dl.reward_xp_v10300(t, 'class', 0) == 0, f'no zero reward created {kind}, {floor}')
                    last = value
                for floor in (799, 801, 850, 899, 900, 999, 1000, 1500, 5000):
                    award = dl.checkpoint_title(kind, floor)
                    valid = (floor >= 800 and floor % 100 == 0)
                    ok(bool(award) == valid, f'clear milestone {kind}/{floor}')
                    if award:
                        ok(f'{kind}:{floor}' in award[0], 'stable award identity')
            ok(dl.dungeon_identity({'crypt_floor': 'wrong'}) == (None, 0), 'invalid metadata')
            ok(dl.dungeon_identity({}) == (None, 0), 'ordinary world unaffected')
            ok(dl.reward_xp_v10300({}, 'class', 999) == 999, 'ordinary world xp')
            ok(dl.reward_xp_v10300({'crypt_floor': 801}, 'class', -100) == -100, 'do not modify negative')
            ok(dl.reward_xp_v10300({'crypt_floor': 5000}, 'class', dl.V019_SAFE_INT) == dl.V019_SAFE_INT,
               'safe integer cap')
            ok(protected(Path('LIVE_CONTENT/era_v10300.json')), 'updater protects config')
            ok(cfg.active_bonus_pct('deep') == 100, 'default')
            ok('brak' in cfg.command('podglad').lower(), 'no initial draft')
            ok('100–200' in cfg.command('ustaw deep 999'), 'bound setting')
            ok('nieznany' in cfg.command('ustaw xyz 150'), 'reject unknown')
            ok(cfg.active_bonus_pct('deep') == 100, 'bad commands no side effects')
            ok('DRAFT' in cfg.command('ustaw deep 175'), 'draft accepted')
            ok('DRAFT poprawny' in cfg.command('sprawdz'), 'valid draft')
            ok('100% → 175%' in cfg.command('porownaj'), 'diff correct')
            ok(cfg.active_bonus_pct('deep') == 100, 'draft does not publish')
            ok(not cfg.CONFIG_PATH.exists(), 'draft does not write disk')
            ok('opublikowano' in cfg.command('aktywuj POTWIERDZAM'), 'publish explicit confirmation')
            ok(cfg.active_bonus_pct('deep') == 175, 'hot updated config')
            ok(json.loads(cfg.CONFIG_PATH.read_text('utf-8'))['bonus']['deep'] == 175, 'persistent file')
            prev_reward = dl.reward_xp_v10300({'uoss_deep_dungeon_floor': 1000}, 'class', 100000)
            cfg.reset_for_tests()
            ok(cfg.active_bonus_pct('deep') == 175, 'restart reloads config')
            ok(dl.reward_xp_v10300({'uoss_deep_dungeon_floor': 1000}, 'class', 100000) == prev_reward,
               'XP same after restart')
            ok('cofnięto' in cfg.command('cofnij POTWIERDZAM'), 'rollback active revision')
            ok(cfg.active_bonus_pct('deep') == 100, 'rollback effective immediately')
            ok('DRAFT' in cfg.command('ustaw krypta 150'), 'crypt settings staged')
            ok('anulowano' in cfg.command('anuluj'), 'cancel')
            ok(cfg.active_bonus_pct('crypt') == 100, 'cancel untouched')
            ok('brak' in cfg.command('aktywuj POTWIERDZAM'), 'cannot publish absent draft')
            ok('DRAFT' in cfg.command('ustaw wieza 125'), 'edit tower')
            obj=json.loads(cfg.CONFIG_PATH.read_text('utf-8'))
            obj['rev'] += 1
            cfg.CONFIG_PATH.write_text(json.dumps(obj), 'utf-8')
            ok('konflikt' in cfg.command('aktywuj POTWIERDZAM'), 'CAS protects concurrent editing')
            cfg.command('anuluj')
            cfg.reset_for_tests()
            ok('Błąd' not in cfg.command('podglad'), 'reload valid revision')
            cfg.CONFIG_PATH.write_text('{BROKEN', 'utf-8')
            cfg.reset_for_tests()
            ok('nie można wczytać' in cfg.command('podglad'), 'broken saved config detected')
            ok(not cfg.CONFIG_PATH.read_text('utf-8').startswith('{"schema"'),
               'corrupt config not overwritten')

            class Session:
                def __init__(self, admin):
                    self.admin = admin
                    self.messages = []
                def is_admin(self):
                    return self.admin
                async def send(self, message):
                    self.messages.append(message)
            guest = Session(False)
            asyncio.run(handle_era(guest, 'premie ustaw deep 200'))
            ok(guest.messages == ['Nieznana komenda. Wpisz help.'], 'guest cannot edit era')
        finally:
            cfg.CONFIG_PATH = old_path
            cfg.reset_for_tests()

    # Historical player saves: only cleared bosses / Apanda can grant new titles.
    from systems.era_dungeon_plus_v10300 import sync_checkpoint_titles_v10300
    from world.uoss_superboss_world import UOSS_DEEP_DUNGEON_APANDA_CLEARS_V11331
    conn=sqlite3.connect(':memory:')
    conn.executescript("""
        CREATE TABLE unlocked_titles(account_id INTEGER,title_id TEXT,title_name TEXT,
            PRIMARY KEY(account_id,title_id));
        CREATE TABLE boss_floor_clears(account_id INTEGER,dungeon_kind TEXT,floor INTEGER);
        CREATE TABLE characters(account_id INTEGER,crypt_checkpoint INTEGER);
        CREATE TABLE astral_progress(account_id INTEGER,checkpoint INTEGER);
        CREATE TABLE collection_codex(account_id INTEGER,category TEXT,entry_id TEXT);
    """)
    conn.executemany('INSERT INTO boss_floor_clears VALUES(?,?,?)',
        [(1,'mythic_crypt',1000),(1,'mythic_astral',1200),(1,'crypt',900),
         (2,'crypt',900)])
    conn.execute('INSERT INTO characters VALUES(?,?)',(1,1000))
    conn.execute('INSERT INTO astral_progress VALUES(?,?)',(1,900))
    conn.executemany('INSERT INTO collection_codex VALUES(?,?,?)',
        [(1,UOSS_DEEP_DUNGEON_APANDA_CLEARS_V11331,'800'),
         (1,UOSS_DEEP_DUNGEON_APANDA_CLEARS_V11331,'900'),
         (1,'uoss_deep_dungeon_floors_v11331','5000')])
    db=SimpleNamespace(conn=conn)
    got=sync_checkpoint_titles_v10300(db,1)
    ok(got==9,f'backfill should grant 9 titles: {got}, titles={list(conn.execute("SELECT title_id FROM unlocked_titles"))}')
    ok(sync_checkpoint_titles_v10300(db,1)==0,'backfill idempotent')
    titles={row[0] for row in conn.execute('SELECT title_id FROM unlocked_titles WHERE account_id=1')}
    ok('era103:mythic_crypt:1000' in titles,'mythic crypt title')
    ok('era103:mythic_tower:1200' in titles,'mythic tower alias title')
    ok('era103:tower:900' in titles,'legacy astral checkpoint title')
    ok('era103:deep:900' in titles,'Cleared Apanda granted')
    ok('era103:deep:5000' not in titles,'Deep visit alone never rewarded')
    ok(len(titles)==got,'no duplicate titles')
    ok(sync_checkpoint_titles_v10300(db,2)==1,'per-account isolation')
    ok(sync_checkpoint_titles_v10300(db,3)==0,'no invented achievements')
    conn.close()

    import ast
    combat = ast.parse(Path(__file__).resolve().parents[1].joinpath('player/session_mixins/combat_rewards.py').read_text('utf-8'))
    source = Path(__file__).resolve().parents[1].joinpath('player/session_mixins/combat_rewards.py').read_text('utf-8')
    ok('reward_xp_v10300(template, axis, result)' in source, 'real combat reward integration')
    ok(source.count('checkpoint_title(') == 2, 'Deep and dungeon boss hooks')
    ok('if first_clear:' in source and 'if session.server.db.add_collection_entry(' in source,
       'checkpoint titles guarded by real first clear')
    return checks

if __name__ == '__main__':
    print(f'ERA DUNGEON/ADMIN STAGE 3: {run()} checks PASS', flush=True)
