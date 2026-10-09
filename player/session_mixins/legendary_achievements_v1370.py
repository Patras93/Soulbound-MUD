# -*- coding: utf-8 -*-
"""Accessible, paged, durable player achievements for Soulbound v1.37.0."""
from systems.legendary_achievements_v1370 import (
    CATALOG_V1370, CATEGORIES_V1370, snapshot_v1370, sync_v1370, records_v1370,
)
from network.protocol_gameplay_utils import normalize_lookup_text


def legendary_page_v1370(items, page, size=15):
    page = max(1, int(page))
    pages = max(1, (len(items) + size - 1) // size)
    page = min(page, pages)
    return items[(page - 1) * size:page * size], page, pages


class SessionLegendaryAchievementsV1370Mixin:
    async def legendary_achievements_v1370(self, args=''):
        raw = normalize_lookup_text(args)
        if raw in ('pomoc', 'help', '?'):
            await self.send(
                'LEGENDARNE OSIĄGNIĘCIA. Komendy: medale, medale rozwoj, medale klasy, '
                'medale profesje, medale wyczyny, medale brakujace, medale kronika, '
                'medale rekordy. Możesz dodać numer strony, np. medale profesje 2.'
            )
            return
        db = self.server.db
        unlocked_now = sync_v1370(db, self.account_id)
        snapshot = snapshot_v1370(db, self.account_id)
        owned = {row['achievement_id'] for row in db.conn.execute(
            'SELECT achievement_id FROM achievements WHERE account_id=? AND achievement_id LIKE ?',
            (self.account_id, 'legend:v1370:%'))}
        if raw in ('kronika', 'postaci', 'moja', 'historia'):
            await self.send(f'KRONIKA POSTACI: {self.character.name}. Legendarne osiągnięcia: {len(owned)} z {len(CATALOG_V1370)}.')
            rows = db.conn.execute(
                'SELECT name,unlocked_at FROM achievements WHERE account_id=? AND achievement_id LIKE ? '
                'ORDER BY unlocked_at DESC,achievement_id DESC LIMIT 15',
                (self.account_id, 'legend:v1370:%')).fetchall()
            if not rows:
                await self.send('Brak zapisanych legendarnych osiągnięć. Wpisz medale brakujace.')
            for row in rows:
                await self.send(f"{row['unlocked_at']}: {row['name']}.")
            await self.send('Pełna historia świata: kronika. Kronika postaci: kronika postaci.')
            return
        if raw in ('rekordy', 'rekord', 'records'):
            await self.send('LEGENDARNE REKORDY — POSTACIE NA SERWERZE')
            for index, row in enumerate(records_v1370(db), 1):
                await self.send(f"{index}. {row['name']}: poziom {row['character_level']}, "
                                f"Dusza {row['soul_level']}, Broń Duszy {row['soul_weapon_mastery_level']}.")
            await self.send('Pozostałe rekordy: rekordy, rekordy profesje, rekordy hall.')
            return
        parts = raw.split()
        page = 1
        if parts and parts[-1].isdigit():
            page = max(1, int(parts.pop()))
        category = ' '.join(parts)
        categories = {
            'rozwoj':'Rozwój', 'rozwoj postaci':'Rozwój',
            'klasy':'Klasy', 'klasa':'Klasy',
            'profesje':'Profesje', 'profesja':'Profesje',
            'wyczyny':'Wyczyny', 'walka':'Wyczyny', 'eksploracja':'Wyczyny',
        }
        show_missing = category in ('brakujace','braki','nastepne','cele')
        if category and category not in categories and not show_missing:
            await self.send('Nieznana kategoria. Wpisz medale pomoc.')
            return
        definitions = [a for a in CATALOG_V1370 if not category or
                       a.category == categories.get(category) or show_missing]
        if show_missing:
            next_by_track = {}
            for a in definitions:
                if a.identifier not in owned:
                    next_by_track.setdefault((a.source, a.key), a)
            definitions = list(next_by_track.values())
        else:
            definitions = [a for a in definitions if a.identifier in owned]
        display, page, pages = legendary_page_v1370(definitions, page)
        await self.send(f'LEGENDARNE OSIĄGNIĘCIA: {len(owned)} z {len(CATALOG_V1370)}. '
                        f'Nowo zapisane: {unlocked_now}. '
                        f'{category or "Odblokowane"}: strona {page} z {pages}.')
        if not display:
            await self.send('Brak wpisów w tej kategorii. Wpisz medale brakujace.')
        for a in display:
            value = snapshot.get((a.source, a.key), 0)
            if show_missing:
                await self.send(f'{a.name}. Postęp {value} z {a.threshold}.')
            else:
                await self.send(a.name + (f'. Nagroda: tytuł {a.reward_title}.' if a.reward_title else '.'))
        await self.send('Kategorie: medale rozwoj, medale klasy, medale profesje, medale wyczyny. '
                        'Strona: dodaj numer. Historia: kronika postaci.')

    async def achievements_plus_v1192(self, args=''):
        if normalize_lookup_text(args) in ('legendarne', 'medale'):
            await self.legendary_achievements_v1370()
            return
        return await super().achievements_plus_v1192(args)
