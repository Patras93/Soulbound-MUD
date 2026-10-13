# -*- coding: utf-8 -*-
"""v3.10.1 - No two authored NPCs share a room, including legacy content.

Add reachable PRIVATE rooms. Never delete/move old rooms, overwrite an exit,
change quest IDs, write SQLite, or mutate unrelated NPC fields.
"""
from __future__ import annotations
from collections import defaultdict

OPPOSITE = {
    'north':'south', 'south':'north', 'east':'west', 'west':'east',
    'northeast':'southwest', 'southwest':'northeast',
    'northwest':'southeast', 'southeast':'northwest',
    'up':'down', 'down':'up',
}
# Prefer lateral exits, using stairs only as a last resort.
PREFERRED = (
    'west','east','north','south','northwest','northeast',
    'southwest','southeast','up','down',
)


def _unused_direction(room):
    current = room.setdefault('exits', {})
    for direction in PREFERRED:
        if direction not in current:
            return direction
    raise AssertionError('Brak wolnego kierunku dla oddzielnego NPC: '+str(room.get('name')))


def _add_room(rooms, room_id, name, zone, desc):
    if room_id in rooms:
        raise AssertionError('Kolizja pokoju NPC: '+room_id)
    rooms[room_id] = {'name':name,'zone':zone, 'desc':desc,'exits':{}}


def _join(rooms, origin, target):
    direction = _unused_direction(rooms[origin])
    reverse = OPPOSITE[direction]
    if reverse in rooms[target]['exits']:
        raise AssertionError('Niebezpieczna kolizja drogi powrotnej NPC: '+target)
    rooms[origin]['exits'][direction]=target
    rooms[target]['exits'][reverse]=origin
    return direction


def install(rooms, npcs, shop_sellers=None):
    """Return number of original collisions and created rooms, deterministic/idempotent."""
    shop_sellers = shop_sellers or {}
    occupied = defaultdict(list)
    for npc_id,npc in npcs.items():
        rid = npc.get('room')
        if rid in rooms:
            occupied[rid].append(npc_id)
    # Keep the actual seller in the old shop: SHOPS, SHOP_SELLERS, class EQ
    # and shop-specific mechanics are already bound to that room. Move the
    # teacher into a private classroom instead; never strand a shopkeeper.
    original = {}
    for rid,members in occupied.items():
        if len(members)<=1:
            continue
        seller=shop_sellers.get(rid)
        if seller in members:
            members=[seller]+[npc_id for npc_id in members if npc_id!=seller]
        original[rid]=members
    reserved_names={str(room.get('name') or '') for room in rooms.values()}
    added=[]
    relocated=[]

    def unique_name(base):
        if base not in reserved_names:
            reserved_names.add(base)
            return base
        index=2
        while f'{base} ({index})' in reserved_names:
            index+=1
        result=f'{base} ({index})'
        reserved_names.add(result)
        return result

    for room_id,members in original.items():
        parent=rooms[room_id]
        zone=parent.get('zone','')
        extras=members[1:]
        # Just two NPCs: direct annex with one return exit.
        if len(extras)==1:
            attachments=[(room_id,extras[0])]
        else:
            # One navigable vestibule; each adjacent room belongs to ONE NPC.
            # More than nine NPCs: two small wings, all reachable in 3 steps.
            hub_id='npc_v3101_hub_'+room_id
            _add_room(rooms, hub_id,unique_name('Galeria rozmów — '+str(parent.get('name') or room_id)),zone,
                      'Korytarz prowadzi do osobnych pomieszczeń mieszkańców. Każdy NPC przyjmuje w swojej izbie.')
            _join(rooms, room_id, hub_id)
            added.append(hub_id)
            if len(extras)<=9:
                attachments=[(hub_id,npc_id) for npc_id in extras]
            else:
                attachments=[]
                chunks=[extras[i:i+8] for i in range(0,len(extras),8)]
                if len(chunks)>9:
                    raise AssertionError('Zbyt wielu NPC w jednym pokoju: '+room_id)
                for wing_index,chunk in enumerate(chunks,1):
                    wing_id=f'npc_v3101_wing_{room_id}_{wing_index}'
                    _add_room(rooms,wing_id,unique_name(f'Skrzydło {wing_index} — '+str(parent.get('name') or room_id)),zone,
                              'Osobne pracownie i gabinety mieszkańców; przejścia prowadzą do konkretnych NPC.')
                    _join(rooms,hub_id,wing_id)
                    added.append(wing_id)
                    attachments.extend((wing_id,npc_id) for npc_id in chunk)
        for attachment,npc_id in attachments:
            npc=npcs[npc_id]
            new_room='npc_v3101_private_'+npc_id
            title=unique_name('Gabinet — '+str(npc.get('name') or npc_id))
            _add_room(rooms,new_room,title,zone,
                      str(npc.get('name') or npc_id)+' przyjmuje tutaj gości. Możesz porozmawiać, obejrzeć ofertę, uczyć się lub przyjąć zadanie. Powrót prowadzi do głównej drogi.')
            direction=_join(rooms,attachment,new_room)
            if attachment==room_id and npc.get('teacher_class'):
                parent['desc']=str(parent.get('desc') or '') + (' Nauczyciel ma teraz własny gabinet; wejdź: '+direction+'.')
            npc['room']=new_room
            relocated.append(npc_id)
            added.append(new_room)

    final_occupied=defaultdict(list)
    for npc_id,npc in npcs.items():
        rid=npc.get('room')
        if rid in rooms:
            final_occupied[rid].append(npc_id)
    invalid={rid:ids for rid,ids in final_occupied.items() if len(ids)>1}
    if invalid:
        raise AssertionError('NPC po przebudowie nadal współdzielą pokoje: '+str(invalid)[:900])
    return {'shared_rooms_fixed':len(original), 'npcs_moved':len(relocated),
            'rooms_added':len(added),'total_npcs':len(npcs), 'relocated_npc_ids':tuple(relocated)}
