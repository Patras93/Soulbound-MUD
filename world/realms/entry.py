# -*- coding: utf-8 -*-
"""Wspólny kontrakt wejścia danych krainy; nie dotyka świata."""
def entry(slug,name,lore,bosses,enemies,materials):
    b=tuple(x.strip() for x in bosses.split('|'))
    m=tuple(x.strip() for x in enemies.split('|'))
    i=tuple(x.strip() for x in materials.split('|'))
    if not slug.isascii() or not slug.replace('_','').isalnum():raise ValueError('zły slug')
    for label,rows,count in (('boss',b,3),('mob',m,12),('surowiec',i,4)):
        if len(rows)!=count or len(set(rows))!=count or not all(rows):
            raise ValueError('v110: '+label+' wymaga '+str(count)+' unikalnych nazw w '+slug)
    return (slug,name,lore,b,m,i)
