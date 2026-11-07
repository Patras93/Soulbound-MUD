# -*- coding: utf-8 -*-
"""One entry point for the full *local* v106 staging regression suite.

Safe by design: never opens or modifies production player data, never deploys.
The 12 local test groups are NOT the Windows release gate 12/12.
"""
from __future__ import annotations

import argparse
import os
import socket
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

# Each group is independently isolated in a Python child process.
# Explicit mode prevents accidental v106 flags contaminating v105 tests.
GROUPS = (
    ('01: zgodność wydanej v105', '', ('validation/v10500_first_integrity.py',
        'validation/v10600_one_package_guard_test.py',
        'validation/v10600_authored_hp_nonstaging_guard.py')),
    ('02: kompletność świata v106', '', ('validation/v10600_stage_catalog_audit.py',)),
    ('03: questy i integracja świata', '', (
        'validation/v10600_one_time_quest_offers.py',
        'validation/v10600_bootstrap_contracts_integration.py',
        'validation/v10600_tower_portal_regression.py',
        'validation/v10600_logout_announcement_regression.py')),
    ('04: Soul EXP od 1 do 60000', '1', (
        'validation/v10600_soul_early_curve_runtime.py',
        'validation/v10600_soul_bridge_runtime.py',
        'validation/v10600_soul_xp_curve_runtime.py')),
    ('05: Soul Tier i Admin Live', '1', (
        'validation/v10600_soul_progression_cap_and_fast_tiers.py',
        'validation/v10600_soul_tier_unlock_runtime.py',
        'validation/v10600_admin_live3_staging.py')),
    ('06: klasy i Broń Duszy', '', (
        'validation/v10600_skill_weapon_integration.py',
        'validation/v10600_weapon_regeneration_real.py')),
    ('07: poziomy zwykłych potworów', '1', (
        'validation/v10600_ordinary_mob_stage_runtime.py',)),
    ('08: bossowie i fazy rajdowe', '1', (
        'validation/v10600_boss_authored_stage_runtime.py',
        'validation/v10600_boss_adaptive_soul_level.py',
        'validation/v10600_raid_full_hp_phase_runtime.py',
        'validation/v10600_real_world_authored_hp.py',
        'validation/v10600_raid_combat_forecast.py',
        'validation/v10600_raid_six_survival.py',
        'validation/v10600_real_room_level_runtime.py')),
    ('09: ewolucja i migracja EQ', '', (
        'validation/test_v10600_equipment_migration_staging.py',
        'validation/v10600_manual_evolved_duplicates.py',
        'validation/v10600_equipment_cutover_gate.py',
        'validation/v10600_equipment_zero_stage_duplicates_gate.py',
        'validation/v10600_shadow_slots_integration.py',
        'validation/v10600_per_copy_evolution_stats.py',
        'validation/v10600_haldor_copy_evolution_command.py')),
    ('10: EQ, bank, magazyn i poczta', '', (
        'validation/v10600_inventory_instance_flow.py',
        'validation/v10600_bank_physical_flow.py',
        'validation/v10600_bank_legacy_migration.py',
        'validation/v10600_storage_physical_flow.py',
        'validation/v10600_mail_physical_flow.py')),
    ('11: crafting i materiały', '', (
        'validation/v10600_crafting_materials_atomic.py',
        'validation/v10600_full_recipe_atomic_flow.py',
        'validation/v10600_crafting_bonus_atomic.py',
        'validation/v10600_crafting_accounting_atomic.py',
        'validation/v10600_crafting_reward_journal.py',
        'validation/v10600_crafting_reward_manual_audit.py')),
    ('12: prawdziwy TCP i restart SQLite', '', (
        'validation/v10600_tcp_sqlite_close_contract.py',
        'validation/v10600_tcp_restart_snapshot_contract.py',
        'validation/v10600_tcp_world_smoke.py --story')),
)


def has_game_database(folder):
    # Detect old saves even if somebody placed the staging tree *inside*
    # a copied production directory. Never scan file contents or open the DB.
    extensions = {'.db', '.db3', '.sqlite', '.sqlite3'}
    return any(path.is_file() and path.suffix.lower() in extensions
               for path in folder.rglob('*'))


def guard_root():
    # Do not run in user's actual production directory or on a DB backup.
    if os.name == 'nt':
        production = Path('C:/Soulbound-MUD').resolve()
        candidate = ROOT.resolve()
        if candidate == production or production in candidate.parents:
            raise RuntimeError('ODMAWIAM: źródła lub podfolder produkcyjny C:\\Soulbound-MUD.')
    if not (ROOT / 'world/v10600_krainy_30001_60000.py').is_file():
        raise RuntimeError('Brak kompletnego kodu świata v106.')
    if (ROOT / 'VERSION').read_text(encoding='utf-8').strip() not in ('105.00.0','106.00.0'):
        raise RuntimeError('Niezweryfikowana wersja testowej paczki; przerwano.')
    if has_game_database(ROOT):
        raise RuntimeError('W folderze lub jego podfolderach jest baza SQLite; nie uruchamiaj testu na produkcji.')
    if not (ROOT / 'validation/v10600_tcp_world_child.py').is_file():
        raise RuntimeError('Brak izolowanego testu TCP.')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Lokalny test całej paczki v106; NIE WDRAŻAĆ')
    parser.add_argument('--bez-tcp', action='store_true', help='Skróć test, bez prawdziwego TCP')
    parser.add_argument('--rajd-tcp', action='store_true', help='Po 12 lokalnych grupach dodaj test 3 i 6 graczy TCP')
    parser.add_argument('--tylko-rajd-tcp', action='store_true', help='Tylko test 3 i 6 graczy TCP, bez pozostałych grup')
    parser.add_argument('--tylko-prognoza-rajd', action='store_true', help='Tylko bezpieczna prognoza DPS rajdów na kopii SQLite')
    parser.add_argument('--tylko-nagrody-rajd', action='store_true', help='Kontrakty 30 questów i nagród rajdów 26–35, bez sieci')
    parser.add_argument('--tylko-odbior-rajd-tcp', action='store_true', help='Prawdziwe oddawanie u NPC na osobnym localhost TCP i SQLite')
    parser.add_argument('--tylko-normalny-cios', action='store_true', help='Prawdziwy cios TCP bez admina w rajdzie 26; prywatna SQLite')
    parser.add_argument('--tylko-naturalny-rajd-6', action='store_true', help='Od 1 do 6 graczy TCP, prawdziwe ataki, pomiar rund bez admina')
    parser.add_argument('--tylko-pelny-naturalny-rajd-6', action='store_true', help='Od 1 do 6 graczy TCP, pełne naturalne pokonanie bossa i zapis postępu questów')
    parser.add_argument('--gracze', type=int, choices=range(1,7), default=6, help='Liczba graczy TCP dla testu naturalnego, domyślnie 6')
    parser.add_argument('--rajd', type=int, choices=range(26,36), default=26, help='Rajd 26–35 do testu naturalnego TCP')
    parser.add_argument('--etap', type=int, choices=range(1,4), default=1, help='Etap rajdu 1–3 do testu naturalnego TCP')
    parser.add_argument('--tylko', type=int, choices=range(1,13), help='Jeden zestaw 1..12')
    options = parser.parse_args(argv)
    extra_options=(options.tylko_nagrody_rajd,options.tylko_odbior_rajd_tcp)
    if sum(bool(v) for v in extra_options)>1:
        parser.error('Wybierz jedną kontrolę nagród.')
    natural_options=(options.tylko_naturalny_rajd_6,options.tylko_pelny_naturalny_rajd_6)
    if sum(bool(v) for v in natural_options)>1:
        parser.error('Wybierz tylko jeden tryb testu 6 graczy.')
    if any(natural_options) and (options.tylko or options.bez_tcp or options.rajd_tcp or
                                options.tylko_rajd_tcp or options.tylko_prognoza_rajd or options.tylko_normalny_cios):
        parser.error('Naturalnego rajdu 6 nie łączy się z innymi testami.')
    if options.tylko_normalny_cios and (options.tylko or options.bez_tcp or options.rajd_tcp or options.tylko_rajd_tcp or options.tylko_prognoza_rajd):
        parser.error('Testu zwykłego ciosu nie łączy się z innymi testami.')
    if options.tylko_prognoza_rajd and (options.tylko or options.bez_tcp or options.rajd_tcp or options.tylko_rajd_tcp):
        parser.error('Prognozy nie łączy się z innymi zestawami testów.')
    if options.bez_tcp and (options.rajd_tcp or options.tylko_rajd_tcp):
        parser.error('Nie można jednocześnie testować rajdu TCP i użyć --bez-tcp.')
    if options.etap!=1 and not any(natural_options):
        parser.error('--etap jest dostepny tylko w testach naturalnego rajdu TCP.')
    if any(extra_options) and (any(natural_options) or options.tylko or options.bez_tcp or
                               options.rajd_tcp or options.tylko_rajd_tcp or
                               options.tylko_prognoza_rajd or options.tylko_normalny_cios):
        parser.error('Kontroli nagród nie łączy się z pozostałymi testami.')
    guard_root()
    if any(extra_options):
        env=os.environ.copy()
        for key in ('SOULBOUND_DB','DATABASE_URL','SOULBOUND_ADMIN_ACCOUNTS',
                    'SOULBOUND_CONTROL_FILE','SOULBOUND_CONTROL_TOKEN'):
            env.pop(key,None)
        env.update(SOULBOUND_V106_STAGING='1' if options.tylko_nagrody_rajd else '0',
                   PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT))
        module=('validation.v10600_raid_rewards_contract' if options.tylko_nagrody_rajd
                else 'validation.v10600_tcp_raid_turnin_rewards')
        print('V106: audyt nagród – bez zmian w produkcji.',flush=True)
        try:
            result=subprocess.run([sys.executable,'-B','-m',module],cwd=ROOT,env=env,
                        stdin=subprocess.DEVNULL,timeout=240,check=False)
        except subprocess.TimeoutExpired:
            print('FAIL: audyt nagród przekroczył limit.',flush=True)
            return 1
        return result.returncode
    if any(natural_options):
        env=os.environ.copy()
        for key in ('SOULBOUND_DB','DATABASE_URL','SOULBOUND_ADMIN_ACCOUNTS',
                    'SOULBOUND_CONTROL_FILE','SOULBOUND_CONTROL_TOKEN'):
            env.pop(key,None)
        env['SOULBOUND_V106_STAGING']=''
        env['PYTHONUTF8']='1'
        env['PYTHONDONTWRITEBYTECODE']='1'
        env['PYTHONPATH']=str(ROOT)
        args=[sys.executable,'-B','-m','validation.v10600_tcp_raid_natural_six','--gracze',str(options.gracze),'--rajd',str(options.rajd),'--etap',str(options.etap)]
        if options.tylko_pelny_naturalny_rajd_6:
            args.append('--pelna-walka')
        print(f'V106: {options.gracze} PRAWDZIWYCH postaci, rajd {options.rajd} etap {options.etap}, zwykle ataki TCP; tylko tymczasowa SQLite.',flush=True)
        try:
            proc=subprocess.run(args,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                                timeout=360,check=False)
        except subprocess.TimeoutExpired:
            print('FAIL: naturalny rajd TCP przekroczył limit czasu.',flush=True)
            return 1
        print(f'NATURALNY RAID {options.gracze} TCP '+('PASS' if proc.returncode==0 else 'FAIL'),flush=True)
        return proc.returncode
    if options.tylko_normalny_cios:
        env=os.environ.copy()
        for key in ('SOULBOUND_DB','DATABASE_URL','SOULBOUND_ADMIN_ACCOUNTS',
                    'SOULBOUND_CONTROL_FILE','SOULBOUND_CONTROL_TOKEN'):
            env.pop(key,None)
        env['SOULBOUND_V106_STAGING']=''
        env['PYTHONUTF8']='1'
        env['PYTHONDONTWRITEBYTECODE']='1'
        env['PYTHONPATH']=str(ROOT)
        print('V106: prawdziwy, zwykły atak TCP, bez admin wyrok. To NIE jest pełny rajd.',flush=True)
        try:
            result=subprocess.run([sys.executable,'-B','-m','validation.v10600_raid_runtime_stage_tcp'],
                              cwd=ROOT,env=env,stdin=subprocess.DEVNULL,timeout=300,check=False)
        except subprocess.TimeoutExpired:
            print('FAIL: test TCP przekroczył limit.',flush=True)
            return 1
        print('NATURAL RAID TCP '+('PASS' if result.returncode==0 else 'FAIL'),flush=True)
        return result.returncode
    if options.tylko_prognoza_rajd:
        env=os.environ.copy()
        for key in ('SOULBOUND_DB','DATABASE_URL','SOULBOUND_ADMIN_ACCOUNTS',
                    'SOULBOUND_CONTROL_FILE','SOULBOUND_CONTROL_TOKEN'):
            env.pop(key,None)
        env['SOULBOUND_V106_STAGING']='1'
        env['PYTHONUTF8']='1'
        env['PYTHONDONTWRITEBYTECODE']='1'
        env['PYTHONPATH']=str(ROOT)
        print('V106: bezpieczny audyt wzorów, NIE walka TCP.',flush=True)
        result=subprocess.run([sys.executable,'-B','-m','validation.v10600_raid_combat_forecast'],
                              cwd=ROOT,env=env,stdin=subprocess.DEVNULL,timeout=180,check=False)
        print('AUDYT RAID DPS '+('PASS' if result.returncode==0 else 'FAIL'),flush=True)
        return result.returncode
    chosen = [] if options.tylko_rajd_tcp else list(enumerate(GROUPS,1))
    if options.tylko:
        chosen = [x for x in chosen if x[0] == options.tylko]
    if options.bez_tcp:
        chosen = [x for x in chosen if x[0] != 12]
    success=0
    print('SOULBOUND v106: JEDNA PACZKA, LOKALNE TESTY. PRODUKCJA BEZ ZMIAN.',flush=True)
    for number,(title,staging,tests) in chosen:
        print(f'\nZESTAW {number:02d}/12: {title}',flush=True)
        for command in tests:
            words=command.split(' ')
            filename=ROOT / words[0]
            if not filename.is_file():
                print(f'BŁĄD: brak testu {words[0]}',flush=True)
                return 1
            env=os.environ.copy()
            # Every validation importing server.py needs a private local
            # bootstrap port, never the user's actual C:\Soulbound-MUD:4000.
            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as test_socket:
                test_socket.bind(('127.0.0.1',0))
                selected_port=test_socket.getsockname()[1]
            for key in ('SOULBOUND_DB','DATABASE_URL','SOULBOUND_ADMIN_ACCOUNTS',
                        'SOULBOUND_CONTROL_FILE','SOULBOUND_CONTROL_TOKEN'):
                env.pop(key,None)
            env['SOULBOUND_HOST']='127.0.0.1'
            env['SOULBOUND_PORT']=str(selected_port)
            env['SOULBOUND_V106_STAGING']=staging
            env['PYTHONUTF8']='1'
            env['PYTHONDONTWRITEBYTECODE']='1'
            env['PYTHONPATH']=str(ROOT)
            print(f'  test: {words[0]}',flush=True)
            started=time.monotonic()
            try:
                module=Path(words[0]).with_suffix('').as_posix().replace('/', '.')
                p=subprocess.run([sys.executable,'-B','-m',module,*words[1:]],cwd=ROOT,
                                 env=env,stdin=subprocess.DEVNULL,
                                 timeout=600 if number == 12 else 480,check=False)
            except subprocess.TimeoutExpired:
                print('FAIL: test przekroczył limit; nie wolno wdrażać.',flush=True)
                return 1
            if p.returncode:
                print(f'FAIL: kod {p.returncode} po {int(time.monotonic()-started)} s.',flush=True)
                return 1
        success+=1
        print(f'ZESTAW {number:02d}/12 PASS',flush=True)
    if options.rajd_tcp or options.tylko_rajd_tcp:
        for players,raid in ((3,26),(6,35)):
            print(f'RAJD {raid}: {players} realnych klientów TCP, konto i SQLite tylko tymczasowe.',flush=True)
            env=os.environ.copy()
            env['SOULBOUND_V106_STAGING']=''
            env['PYTHONUTF8']='1'
            env['PYTHONDONTWRITEBYTECODE']='1'
            env['PYTHONPATH']=str(ROOT)
            command=[sys.executable,'-B','-m','validation.v10600_tcp_raid_party_real',
                     '--gracze',str(players),'--rajd',str(raid)]
            try:
                result=subprocess.run(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                                      timeout=900,check=False)
            except subprocess.TimeoutExpired:
                print('FAIL: rajd TCP przekroczył limit.',flush=True)
                return 1
            if result.returncode:
                print('FAIL: rajd TCP. Nie wdrażać.',flush=True)
                return 1
            print(f'RAJD {raid}: {players} klientów TCP i kill-credit PASS.',flush=True)
    print(f'\nKONIEC: {success}/{len(chosen)} LOKALNYCH ZESTAWÓW PASS.',flush=True)
    print('STAN WYDANIA: NIEZATWIERDZONE, NIE WDRAŻAĆ.',flush=True)
    print('Te 12 grup NIE są końcowym Windows PREDEPLOY 60/60 PLUS + v105 3/3 + v106 12/12.',flush=True)
    print('Nadal wymagane: migracja historycznie ulepszonego EQ na KOPII rzeczywistej bazy,')
    print('atomowe rozliczenie EXP/questów/osiągnięć craftingu i naturalne pełne walki rajdowe z DPS/HP 1–6 graczy.')
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError,RuntimeError) as exc:
        print('BŁĄD ZABEZPIECZEŃ: '+str(exc),file=sys.stderr,flush=True)
        raise SystemExit(2)
