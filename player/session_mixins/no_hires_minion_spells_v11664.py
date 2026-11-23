# -*- coding: utf-8 -*-
"""v116.00.64: Retire hirelings; skeletons are paid-MP spells, not pets.

Do not delete the historic contracts or other player records. This mixin is
first in Session MRO, so legacy implementations remain for isolated fixtures.
"""
from __future__ import annotations
from network.protocol_gameplay_utils import normalize_lookup_text


class SessionNoHiresMinionSpellsV11664Mixin:
    def class_teacher(self,class_name=None):
        if self.character:
            from systems.current_class_schools_v11664 import school_teacher
            from data.npcs import NPCS
            wanted=class_name or self.character.class_name
            teacher=NPCS.get(school_teacher(wanted))
            if (teacher and self.character.room_id.startswith('v11664_class_school_')
                    and self.character.room_id.startswith('v11664_class_school_' + school_teacher(wanted).split('v11664_school_teacher_')[-1] + '_')):
                return school_teacher(wanted),teacher
        return super().class_teacher(class_name)

    async def show_teachers(self):
        if self.character:
            from systems.current_class_schools_v11664 import school_teacher,school_room
            from data.npcs import NPCS
            wanted=self.character.class_name
            teacher=NPCS.get(school_teacher(wanted))
            if teacher:
                await self.send(f'Szkoła klasy {wanted}: {teacher["name"]}, Sala Nauczyciela. '
                                'W szkole wpisz learn lub talk <nauczyciel>. '
                                'Po wyjściu z niej nadal możesz uczyć się w Gildii Dusz. '
                                'Portal do miasta znajduje się na krańcu szkoły.')
                return
        return await super().show_teachers()

    async def move(self,direction,preserve_auto_mining=False):
        if self.character:
            from data.rooms import ROOMS
            here=ROOMS.get(self.character.room_id,{})
            pending=getattr(self,'_v11664_school_exit_pending',None)
            if here.get('v11664_school_city_portal') and direction=='up':
                if pending!=(self.character.room_id,direction):
                    self._v11664_school_exit_pending=(self.character.room_id,direction)
                    level=int(getattr(self.character,'character_level',1))
                    await self.send('UWAGA: portal opuszcza twoją szkołę i prowadzi do Miasta Dusz. '
                                    + ('Zalecany poziom 10, twój jest niższy. ' if level<10 else '')
                                    + 'Wpisz up ponownie, aby potwierdzić, albo inny kierunek, aby anulować.')
                    return
                self._v11664_school_exit_pending=None
            else:
                self._v11664_school_exit_pending=None
        return await super().move(direction,preserve_auto_mining=preserve_auto_mining)

    def _v11664_live_hires_retired(self):
        return bool(getattr(self.server.db, '_retired_mercenaries_v11664', False))

    def nearby_mercenaries_v1226(self):
        return [] if self._v11664_live_hires_retired() else super().nearby_mercenaries_v1226()

    def visible_mercenary_for_look_v1226(self, query):
        return None if self._v11664_live_hires_retired() else super().visible_mercenary_for_look_v1226(query)

    def adaptive_member_mercenary_dps_v1261(self, member):
        return 0 if self._v11664_live_hires_retired() else super().adaptive_member_mercenary_dps_v1261(member)

    async def mercenary_combat_turn_v1170(self, mob):
        if self._v11664_live_hires_retired():
            return None
        return await super().mercenary_combat_turn_v1170(mob)

    async def handle_mercenaries_v1170(self, args=''):
        if self._v11664_live_hires_retired():
            await self.send('Najemnicy zostali wycofani z gry. Nie można ich wynajmować ani przywoływać. Dawne kontrakty zachowano w archiwum zapisów.')
            return
        return await super().handle_mercenaries_v1170(args)

    async def summons_v1700(self, raw=''):
        """Old chowaniec/nekro controls cannot create skeleton spell minions."""
        if self._v11664_live_hires_retired():
            from player.session_mixins.sky_parts_v109.dependencies import ascii_fold, summon_key
            parts = ascii_fold(raw).split()
            action = parts[0] if parts else ''
            kind = summon_key(' '.join(parts[1:])) if len(parts)>1 else ''
            if kind in ('mag','wojownik') and action in ('przywolaj','stworz','aktywuj','schowaj','ulepsz','odwolaj'):
                await self.send('Szkielety są zaklęciami minionów. Użyj: cast skeletal mage albo cast skeletal warrior (skrót c). Każde przywołanie kosztuje MP.')
                return
            if not parts or action in ('lista','status','info','pomoc'):
                conn = self._v1700_conn()
                self._v1702_prepare_summon_lives(conn)
                rows = conn.execute('SELECT summon_type, active, hp, max_hp FROM summons_v1700 WHERE account_id=? ORDER BY summon_type', (self.account_id,)).fetchall()
                await self.send('CHOWAŃCE: zwierzęta i inne przywołania klasowe. Szkieletowy Mag i Wojownik to zaklęcia: cast skeletal mage/warrior. Limit 3 aktywne przywołania.')
                from player.session_mixins.sky_parts_v109.dependencies import SUMMONS
                for row in rows:
                    kind = str(row['summon_type'])
                    if kind in ('mag','wojownik') or kind not in SUMMONS:
                        continue
                    await self.send(f"{SUMMONS[kind][0]}: {'aktywny' if row['active'] else 'nieaktywny'}, HP {row['hp']}/{row['max_hp']}.")
                await self.send('Przywołania: call list (Druid), mag lista (Mag), nekro lista (Nekromanta).')
                return
        return await super().summons_v1700(raw)

    def v11664_can_use_summon(self, kind, required_class):
        classes = set(self.active_class_names()) if self.character else set()
        return (required_class in classes or
                (kind in ('mag','wojownik') and self._v11664_live_hires_retired()
                 and 'Mag' in classes))

    async def cast_minion_spell_v11664(self, raw=''):
        """Cast skeletal mage/warrior, 10% max-MP spell, no material bypass.

        Skeleton spell minions reuse the existing durable summon health and
        combat system. A cast is explicit, never an automatic free respawn.
        """
        if not self.character or self.account_id is None:
            return
        text = normalize_lookup_text(raw or '').strip().casefold()
        spell = ' '.join(text.replace('_',' ').split())
        translations = {
            'skeletal mage':'mag', 'skeleton mage':'mag',
            'szkieletowy mag':'mag', 'szkielet maga':'mag',
            'skeletal warrior':'wojownik', 'skeleton warrior':'wojownik',
            'szkieletowy wojownik':'wojownik', 'szkielet wojownika':'wojownik',
        }
        kind = translations.get(spell)
        if kind is None:
            await self.send('Zaklęcia minionów: cast skeletal mage albo cast skeletal warrior. Skrót: c. Każde przywołanie kosztuje 10% maksymalnej many (minimum 120 lub 90 MP).')
            return
        classes = set(self.active_class_names())
        if not ('Mag' in classes or 'Nekromanta' in classes):
            await self.send('Szkieletowe zaklęcia są dostępne tylko dla aktywnego Maga lub Nekromanty, nie dla Druida.')
            return
        if self.current_hp <= 0 or self.is_downed_v0371():
            await self.send('Nie możesz rzucać zaklęć po śmierci.')
            return
        if self.combat_mob_key:
            await self.send('Przywołaj miniona przed rozpoczęciem walki.')
            return
        from player.session_mixins.sky_parts_v109.dependencies import SUMMONS
        mana_cost = max(120 if kind == 'mag' else 90, (max(1,int(self.max_mana()))+9)//10)
        conn = self._v1700_conn()
        self._v1702_prepare_summon_lives(conn)
        self._v1710_refresh_summon_health(conn)
        row = conn.execute('SELECT active FROM summons_v1700 WHERE account_id=? AND summon_type=?', (self.account_id,kind)).fetchone()
        if row is not None and int(row['active']):
            await self.send(f'{SUMMONS[kind][0]} jest już aktywny. Nie pobrano many.')
            return
        active = conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=? AND active=1 AND hp>0', (self.account_id,)).fetchone()[0]
        if int(active) >= 3:
            await self.send('Masz już trzy aktywne przywołania. Zwolnij jedno miejsce.')
            return
        if not await self._v1701_need_mana(mana_cost):
            return
        level = self._v1806_owner_summon_level(kind)
        hp = self._v1702_summon_max_hp(kind,level)
        conn.execute('SAVEPOINT v11664_skeletal_cast')
        try:
            if row is None:
                conn.execute('INSERT INTO summons_v1700(account_id,summon_type,level,active,hp,max_hp,xp) VALUES(?,?,?,1,?,?,0)',(self.account_id,kind,level,hp,hp))
            else:
                conn.execute('UPDATE summons_v1700 SET active=1,level=?,hp=?,max_hp=? WHERE account_id=? AND summon_type=?',(level,hp,hp,self.account_id,kind))
            conn.execute('RELEASE SAVEPOINT v11664_skeletal_cast')
            conn.commit()
        except BaseException:
            conn.execute('ROLLBACK TO SAVEPOINT v11664_skeletal_cast')
            conn.execute('RELEASE SAVEPOINT v11664_skeletal_cast')
            raise
        self.current_mana -= mana_cost
        await self.send(f'{SUMMONS[kind][0]} przywołany zaklęciem. Mana -{mana_cost} MP, zostało {self.current_mana} MP. Minion walczy automatycznie.')
