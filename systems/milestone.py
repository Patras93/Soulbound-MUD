# -*- coding: utf-8 -*-
"""Soulbound v0.32.0 milestone constants/helpers."""
from data.rooms import ROOMS
from systems.dungeons_regions import (
    astral_floor_number, crypt_floor_number, mythic_astral_floor_number,
    mythic_crypt_floor_number, profession_dungeon_floor,
)

TECH_SET_UPGRADE_COSTS_V0320={
  2:{'magitek_alloy':2,'astral_alloy':1},
  3:{'eternium_alloy':2,'machine_warmech_core':1},
}

def room_is_dungeon_v0320(room_id):
    rid=str(room_id or '')
    if crypt_floor_number(rid) is not None or mythic_crypt_floor_number(rid) is not None: return True
    if astral_floor_number(rid) is not None or mythic_astral_floor_number(rid) is not None: return True
    d,f=profession_dungeon_floor(rid)
    if d and f is not None: return True
    room=ROOMS.get(rid,{})
    zone=str(room.get('zone','')).lower()
    return any(x in rid.lower() or x in zone for x in ('magitek','dungeon','fortress','gauntlet','mega_','ruin','crypt','astral'))

def dungeon_party_bonus_v0320(session):
    if not session or not getattr(session,'character',None) or not room_is_dungeon_v0320(session.character.room_id):
        return {'multiplier':1.0,'full':False,'diverse':0,'members':1}
    members=[s for s in session.server.party_sessions(session.account_id,same_room=session.character.room_id) if getattr(s,'character',None) and not s.closed and s.current_hp>0]
    if len(members)<=1: return {'multiplier':1.0,'full':False,'diverse':1,'members':len(members) or 1}
    leader=min(members,key=lambda s:s.account_id)
    try: capacity=max(1,int(leader.character.party_capacity()))
    except Exception: capacity=8
    full=len(members)>=capacity
    classes=set()
    for s in members:
        try:
            vals=s.active_class_names(); classes.update(str(v) for v in vals if v)
        except Exception:
            classes.add(str(s.character.class_name))
    bonus=0.03 if full else 0.0
    if len(classes)>=3: bonus+=0.02
    if len(classes)>=5: bonus+=0.02
    bonus=min(0.07,bonus)
    return {'multiplier':1.0+bonus,'full':full,'diverse':len(classes),'members':len(members),'bonus_pct':int(round(bonus*100))}
