"""Walidacja statycznego wpisu nowej krainy."""

def entry(slug, name, lore, boss1, boss2, enemies, materials):
    creatures = tuple(part.strip() for part in enemies.split('|'))
    loot = tuple(part.strip() for part in materials.split('|'))
    if len(creatures) != 12 or len(set(creatures)) != 12:
        raise ValueError('v109: wymaga 12 unikalnych potworów: '+slug)
    if len(loot) != 4 or len(set(loot)) != 4:
        raise ValueError('v109: wymaga 4 unikalnych materiałów: '+slug)
    return (slug, name, lore, boss1, boss2, creatures, loot)
