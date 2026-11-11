# -*- coding: utf-8 -*-
"""v106: dokładne autorskie HP/obrażenia 390 rodzajów w rzeczywistym World().

Wcześniejsza kontrola badała tylko max_hp >= authored, przez co nie wykryła
ogromnych przeskalowań 10^16+ przez historyczne world/terrain v0362/v0384.
"""
from __future__ import annotations
import os
import socket
import re
from collections import defaultdict

def run():
    assert os.environ.get('SOULBOUND_V106_STAGING') == '1', 'tylko test staging'
    # Direct invocation must also be safe while production listens on 4000.
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as test_sock:
        test_sock.bind(('127.0.0.1',0))
        selected=test_sock.getsockname()[1]
    os.environ['SOULBOUND_HOST']='127.0.0.1'
    os.environ['SOULBOUND_PORT']=str(selected)
    os.environ.pop('SOULBOUND_DB',None)
    import server
    from world.dynamic_content import MOB_TEMPLATES, ROOMS
    from world.v10600_raids_26_35 import RAID_ROWS
    world=server.World()
    checks=0
    def check(cond,msg):
        nonlocal checks
        if not cond:raise AssertionError('V106 WORLD HP: '+msg)
        checks+=1
    real=defaultdict(list)
    for mob in world.mobs.values():
        tid=str(mob.template_id)
        if tid.startswith('v10600_') and ('_mob_' in tid or '_boss_' in tid):
            real[tid].append(mob)
    # World can legitimately add elite / legendary variants, including
    # their OWN HP/damage modifiers; do not mistake them for old terrain
    # world-overdrive clones.
    ordinary={k for k in real if '_mob_' in k}
    boss={k for k in real if '_boss_' in k}
    base_mob={str(MOB_TEMPLATES[k].get('base_template') or k).split('__')[0]
              for k in ordinary}
    base_boss={str(MOB_TEMPLATES[k].get('base_template') or k).split('__')[0]
               for k in boss}
    check(len(base_mob)==300,f'300 typów zwykłych, otrzymano {len(base_mob)}')
    check(len(base_boss)==90,f'90 bossów, otrzymano {len(base_boss)}')
    count=0
    for tid,entries in real.items():
        for mob in entries:
            meta=MOB_TEMPLATES[mob.template_id]
            check(mob.hp==int(meta['max_hp']) and mob.hp>0,
                  f'{tid}: złe HP rzeczywiste {mob.hp}/{meta["max_hp"]}')
            check(int(meta['damage'])>0,f'{tid}: niepoprawne obrażenia')
            check(not meta.get('world_threat_overdrive_v0384'),f'{tid}: stary v0384 aktywny')
            check(not meta.get('terrain_runtime_clone_v0362'),f'{tid}: stary v0362 aktywny')
            check(int(meta['generator_level'])>=30001,f'{tid}: zgubiony etap')
            count+=1
    check(count>=690,f'przynajmniej 690 rzeczywistych spawnów, jest {count}')
    for number,*_ in RAID_ROWS:
        for stage in range(1,4):
            mid=f'v10600_raid_{number}_boss_{stage}'
            check(len(real[mid])==1 and real[mid][0].room_id==f'v10600_raid_{number}_stage_{stage}',
                f'rajd {number}/{stage} spawn i sala')
    print(f'V106 WORLD AUTHOR HP: {checks} PASS, {count} rzeczywistych instancji, 390 typów',flush=True)
    return checks

if __name__=='__main__':run()
