# -*- coding: utf-8 -*-
"""Autorskie poziomy 300 zwykłych mobów v106 przez prawdziwy normalizator.

Nie dotyka HP, obrażeń, dropu ani v105. Obejmuje klony terenu/elite.
"""
from __future__ import annotations
import os,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

def run():
    from validation.v10600_stage_catalog_audit import registries
    from world.v10600_krainy_30001_60000 import install
    from core.progression_resources import v0190_apply_combat_template
    from validation.v10600_boss_authored_stage_runtime import real_restore
    assert os.getenv('SOULBOUND_V106_STAGING')=='1','Only staging.'
    state=registries(); rooms,mobs,spawns,*_=state
    install(*state)
    restore=real_restore(rooms,mobs)
    checks=0
    def ck(ok,label):
        nonlocal checks
        if not ok:raise AssertionError('V106 MOB NORMALIZER: '+label)
        checks+=1
    targets=[(room,mid) for room,mid in spawns if mid.startswith('v10600_') and '_mob_' in mid]
    ck(len(targets)==600,'300 ordinary mobs in two spawn rooms each')
    ck(len(set(mid for _,mid in targets))==300,'unique 300 normal mobs')
    for room,mid in targets:
        original=mobs[mid]
        stage=original['v106_authored_mob_stage'];hp=original['max_hp'];damage=original['damage']
        ck(stage==original['generator_level'] and 30001<=stage<=60000,'authored marker '+mid)
        v0190_apply_combat_template(original)
        ck(original['generator_level']==800,'legacy cap actually applied '+mid)
        restore(room,mid)
        ck(original['generator_level']==stage and original['v019_stage']==stage,'restored stage '+mid)
        ck(original['max_hp']==hp and original['damage']==damage,'HP and damage unchanged '+mid)
        # Real-world terrain and elite variants may have their own HP/attack,
        # and must retain the authored stage marker without copying base HP.
        clone=copy.deepcopy(original)
        cid=mid+'__terrain_v0362_800';clone.update(base_template=mid,
            terrain_runtime_clone_v0362=True,max_hp=hp*2,damage=damage*3,
            generator_level=800,v019_stage=800)
        mobs[cid]=clone
        restore(room,cid)
        ck(clone['generator_level']==stage and clone['v019_stage']==stage,'clone stage '+mid)
        ck(clone['max_hp']==hp*2 and clone['damage']==damage*3,'clone HP/damage unaffected '+mid)
        del mobs[cid]
        # Repeat normalization and restore to prove stable respawn.
        v0190_apply_combat_template(original);restore(room,mid)
        ck(original['generator_level']==stage and original['max_hp']==hp,'respawn '+mid)
    room,mid=targets[0];original=mobs[mid]
    os.environ.pop('SOULBOUND_V106_STAGING',None)
    try:
        v0190_apply_combat_template(original)
        restore(room,mid)
        ck(original['generator_level']==800,'production non-staging preserves historical normalization')
    finally:os.environ['SOULBOUND_V106_STAGING']='1'
    fake=mid+'__badmarker';mobs[fake]={'generator_level':800,'v106_authored_mob_stage':True,'max_hp':300}
    restore(room,fake)
    ck(mobs[fake]['generator_level']==800,'rejects bool marker')
    mobs[fake]['v106_authored_mob_stage']='60000';restore(room,fake)
    ck(mobs[fake]['generator_level']==800,'rejects str marker')
    del mobs[fake]
    print(f'V106 300 AUTHORED ORDINARY MOBS + CLONES: {checks} PASS',flush=True)
    return checks
if __name__=='__main__':run()
