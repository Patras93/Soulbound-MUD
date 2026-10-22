# -*- coding: utf-8 -*-
"""OLC17 pure rules + on-hit runtime tests; run without live server/DB."""
from types import SimpleNamespace
from systems.live_olc20_phase_tactics import (
    validate_stage_map, boss_stage_cycle, ELEMENTS, ROLES,
)
from systems.live_olc19_status_skills import parse_status, apply_skill_status_v1900
from systems.summon_status_v1808 import summon_status_enemy_turn_v1808


def run():
    n = 0
    def ck(x, msg=''):
        nonlocal n
        assert x, msg
        n += 1
    def fail(fn):
        try: fn()
        except (ValueError, TypeError): ck(True)
        else: raise AssertionError('Accepted forbidden editor value')

    # Defaults unchanged: existing 19.00.0 schema still maps identically.
    for kind in ('poison','burn','freeze','shock'):
        ck(parse_status({'kind':kind,'chance':.4}) == {'kind':kind,'chance':.4})
    ck(parse_status('auto') is None)
    ck(parse_status({'kind':'poison','chance':1.,'power_percent':200,'ticks':5}) ==
       {'kind':'poison','chance':1.,'power_percent':200,'ticks':5})
    ck(parse_status({'kind':'burn','chance':1.,'power_percent':1,'ticks':1})['ticks'] == 1)
    for d in ({'kind':'freeze','chance':1.,'ticks':2},
              {'kind':'shock','chance':1.,'power_percent':50},
              {'kind':'poison','chance':.5,'ticks':0},
              {'kind':'poison','chance':.5,'ticks':6},
              {'kind':'poison','chance':.5,'ticks':1.0},
              {'kind':'poison','chance':.5,'power_percent':0},
              {'kind':'burn','chance':.5,'power_percent':201},
              {'kind':'burn','chance':.5,'power_percent':True},
              {'kind':'burn','chance':.5,'power_percent':float('nan')},
              {'kind':'burn','chance':.5,'ticks':2,'script':'bad'}):
        fail(lambda d=d: parse_status(d))

    def target(hp=10**20):
        return SimpleNamespace(hp=hp,alive=True)
    # A high-level character has no global artificial DOT damage ceiling.
    victim = target(hp=10**80)
    hit = 10**45
    ck(bool(apply_skill_status_v1900(victim,{'kind':'poison','chance':1.,'power_percent':180,'ticks':5},
                                     hit, now=10, roll=0)))
    status = victim.v1808_summon_statuses['poison']
    ck(status['power'] == hit * 180 // 100)
    ck(status['ticks_left'] == 5)
    ck(status['until'] == 31.)
    for second in (13,16,19,22,25):
        lines, skip, dead = summon_status_enemy_turn_v1808(victim,now=second)
        ck(len(lines) == 1 and not skip and not dead)
    ck(victim.hp == 10**80 - 5*(hit*180//100))
    # Per-kind cooldown still stops refreshing DoTs indefinitely.
    ck(not apply_skill_status_v1900(victim,{'kind':'poison','chance':1.,'power_percent':200,'ticks':5},
                                    hit, now=26,roll=0))
    # Other controls still skip no more than one action.
    victim = target()
    ck(bool(apply_skill_status_v1900(victim,{'kind':'freeze','chance':1.},100,now=10,roll=0)))
    lines,skip,killed = summon_status_enemy_turn_v1808(victim,now=11)
    ck(skip and not killed)
    _lines,skip,_dead = summon_status_enemy_turn_v1808(victim,now=11.1)
    ck(not skip)

    elements={'0':['fire','ice'],'2':['lightning'],'5':['holy','shadow']}
    roles={'0':['obronca','zbrojny'],'1':['uzdrowiciel'],'3':['furia','arkaniczny']}
    ck(validate_stage_map(elements, ELEMENTS, 'elementy') == elements)
    ck(validate_stage_map(roles, ROLES, 'role') == roles)
    ck(boss_stage_cycle({'x':3},2,'x',ELEMENTS) is None)
    ck(boss_stage_cycle({'x':elements},0,'x',ELEMENTS)==['fire','ice'])
    ck(boss_stage_cycle({'x':elements},2,'x',ELEMENTS)==['lightning'])
    ck(boss_stage_cycle({'x':elements},3,'x',ELEMENTS) is None)
    ck(boss_stage_cycle({'x':roles},3,'x',ROLES)==['furia','arkaniczny'])
    for bad in ({},{'6':['fire']},{'-1':['fire']},{0:['fire']},
                {'0':[]},{'0':['fire','python']},{'0':['fire']*13},
                {'0':'fire'},{'0':['fire'],'1':['bad']},
                {'0':['fire'],'1':['ice'],'2':['fire'],'3':['ice'],'4':['holy'],'5':['shadow'],'6':['dark']}):
        fail(lambda bad=bad: validate_stage_map(bad,ELEMENTS,'elementy'))
    ck(boss_stage_cycle({'x':{'0':['bogus']}},0,'x',ELEMENTS) is None)
    return n

if __name__=='__main__':
    print('Soulbound v20.00.0 / OLC17:',run(),'PASS')
