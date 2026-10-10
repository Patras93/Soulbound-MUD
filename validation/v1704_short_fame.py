# -*- coding: utf-8 -*-
"""Fame is one local message; independent areas, aggregated dungeon floors."""
import sqlite3
from unittest.mock import patch
from systems.fame_v1702 import fame_report, fame_region, ensure_schema


def run_regression():
    conn = sqlite3.connect(':memory:')
    ensure_schema(conn)
    checks = 0
    # Use actual dungeon room-id conventions, without generating entire floors.
    mythic1 = 'mythic_astral_floor_15_gate'
    mythic2 = 'mythic_astral_floor_25_gate'
    crypt1 = 'crypt_floor_11_gate'
    crypt2 = 'crypt_floor_99_gate'
    mythic = fame_region(mythic1)
    crypt = fame_region(crypt1)
    assert fame_region(mythic2) == mythic
    assert fame_region(crypt2) == crypt
    assert mythic != crypt
    checks += 3
    targets = {mythic: ('boss_a','boss_b','boss_c','boss_d'), crypt: ('boss_e','boss_f','boss_g','boss_h')}
    labels = {mid: {'name': name} for mid, name in {'boss_a':'Rycerz Echa','boss_b':'Zimny Tytan','boss_c':'Strażnik Sfer','boss_d':'Król Mitycznej Wieży','boss_e':'Król Krypt','boss_f':'Widmo Krypt','boss_g':'Demon Krypt','boss_h':'Prastary Strażnik'}.items()}
    with patch('systems.fame_v1702.fame_catalog',return_value=targets), patch.dict('systems.fame_v1702.MOB_TEMPLATES', labels):
        # Nothing defeated: exactly one line, and separate regions.
        assert fame_report(conn,77,'',room_id=mythic1) == ['You have no fame in this area.']
        assert fame_report(conn,77,'',room_id=crypt1) == ['You have no fame in this area.']
        checks += 2
        def defeat(region, boss):
            conn.execute('INSERT INTO fame_bosses_v1702(account_id,region,boss_id) VALUES (77,?,?)',(region,boss))
            conn.commit()
        defeat(mythic,'boss_a')
        assert fame_report(conn,77,'',room_id=mythic1) == ['You have some fame in this area.']
        assert fame_report(conn,77,'',room_id=mythic2) == ['You have some fame in this area.']
        assert fame_report(conn,77,'',room_id=crypt1) == ['You have no fame in this area.']
        checks += 3
        defeat(mythic,'boss_b')
        assert fame_report(conn,77,'',room_id=mythic1) == ['You have most fame in this area.']
        checks += 1
        defeat(mythic,'boss_c')
        assert fame_report(conn,77,'',room_id=mythic1) == ['You have most fame in this area. Missing fame: Król Mitycznej Wieży.']
        assert fame_report(conn,77,'',room_id=mythic2) == ['You have most fame in this area. Missing fame: Król Mitycznej Wieży.']
        checks += 2
        defeat(mythic,'boss_d')
        assert fame_report(conn,77,'',room_id=mythic2) == ['You have all fame in this area.']
        assert fame_report(conn,77,'',room_id=crypt1) == ['You have no fame in this area.']
        checks += 2
        # Fame is credited on kill; only its EXP bonus waits for payout.
        defeat(crypt,'boss_e')
        conn.execute('INSERT INTO fame_pending_v1703(account_id,region,boss_id,boss_name,reward_xp,due_at,delivered) VALUES (77,?,?,?,123,0,0)',(crypt,'boss_e','Example'))
        conn.commit()
        assert fame_report(conn,77,'',room_id=crypt1) == ['You have some fame in this area.']
        conn.execute('UPDATE fame_pending_v1703 SET delivered=1 WHERE account_id=77 AND region=?',(crypt,));conn.commit()
        assert fame_report(conn,77,'',room_id=crypt2) == ['You have some fame in this area.']
        # The final killed boss still awaiting delayed Fame must not be
        # shown as un-killed or available to kill again.
        defeat(crypt,'boss_f'); defeat(crypt,'boss_g')
        assert fame_report(conn,77,'',room_id=crypt1) == ['You have most fame in this area. Missing fame: Prastary Strażnik.']
        defeat(crypt,'boss_h')
        conn.execute('INSERT INTO fame_pending_v1703(account_id,region,boss_id,boss_name,reward_xp,due_at,delivered) VALUES (77,?,?,?,123,0,0)',(crypt,'boss_h','Prastary Strażnik'))
        conn.commit()
        assert fame_report(conn,77,'',room_id=crypt2) == ['You have all fame in this area.']
        conn.execute('UPDATE fame_pending_v1703 SET delivered=1 WHERE account_id=77 AND region=? AND boss_id=?',(crypt,'boss_h'));conn.commit()
        assert fame_report(conn,77,'',room_id=crypt2) == ['You have all fame in this area.']
        checks += 3
        checks += 2
        # Keep non-local commands distinct: log and global summaries.
        assert fame_report(conn,77,'log',room_id=mythic1)[0].startswith('FAME LOG')
        assert 'PRZEGLĄD TERENÓW' in fame_report(conn,77,'regiony',room_id=mythic1)[0]
        assert fame_report(conn,77,'none',room_id=mythic1)
        assert fame_report(conn,77,'most',room_id=mythic1)
        checks += 4
        solo = 'Oddzielny teren'
        with patch('systems.fame_v1702.fame_catalog',return_value={solo: ('boss_a',)}), patch('systems.fame_v1702.fame_region',return_value=solo):
            assert fame_report(conn,77,'',room_id='solo_zone') == ['You have no fame in this area. Missing fame: Rycerz Echa.']
            checks += 1
    conn.close()
    return checks
