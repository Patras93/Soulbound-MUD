# -*- coding: utf-8 -*-
"""Quest stages for a real, cross-world, solo-or-party grand journey."""
STAGES = (
    ('city','Miasto: odwiedź targ, rynek lub port.'),
    ('ocean','Ocean: odwiedź szlak morski, wyspę albo podwodne ruiny.'),
    ('dungeon','Loch: odwiedź kryptę, wieżę, fortecę albo Deep Dungeon.'),
    ('mine','Kopalnia: wejdź na dowolne piętro Kopalni Głębinowej.'),
)

def expedition_region_v1260(room_id, room=None):
    room_id=str(room_id or '').casefold()
    room=room or {}
    zone=str(room.get('zone','')).casefold()
    if room_id.startswith('mine_floor_'):
        return 'mine'
    if (room_id.startswith(('crypt_floor_','astral_floor_','mythic_crypt_','mythic_astral_',
                            'uoss_deep_','giant_fortress_','deep_dungeon_')) or
            'loch' in zone or 'katakumb' in zone or 'krypt' in zone):
        return 'dungeon'
    if (room_id.startswith(('ocean_','sea_','ocean_sector_','v0180_archipelago_')) or
            room.get('requires_ship') or room.get('underwater') or
            'ocean' in zone or 'archipelag' in zone or 'morze' in zone):
        return 'ocean'
    if room_id in ('market','square','harbor') or 'miasto' in zone or 'port' in zone:
        return 'city'
    return ''
