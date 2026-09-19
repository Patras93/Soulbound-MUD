# -*- coding: utf-8 -*-
"""Soulbound v0.32.0 milestone player systems."""
class SessionMilestoneV0320Mixin:
    def tech_set_mark_bonus_v0320(self, item_id):
        mark=self.server.db.tech_set_mark_v0320(self.account_id,item_id)
        return max(0,mark-1)

    async def tech_set_upgrade_v0320(self,args=''):
        raw=str(args or '').strip()
        if not raw:
            await self.send('TECH SET UPGRADE: techupgrade <pełna nazwa części Tech Setu>. Mk-II i Mk-III są trwałe.')
            return
        found=self.resolve_owned_equipment_v0925(raw,free_only=False)
        if not found:
            await self.send('Nie rozpoznaję posiadanej części Tech EQ.')
            return
        item_id,item=found
        if item_id not in {x for rows in TECH_SET_ITEMS_V03114.values() for x in rows}:
            await self.send('Ten przedmiot nie należy do technologicznego setu Meca, Inżyniera ani Cyborga.')
            return
        current=self.server.db.tech_set_mark_v0320(self.account_id,item_id)
        if current>=3:
            await self.send(f"{item['name']} ma już Mk-III.")
            return
        target=current+1
        costs=TECH_SET_UPGRADE_COSTS_V0320[target]
        missing=[]
        for iid,qty in costs.items():
            have=self.available_recipe_item(iid)
            if have<qty: missing.append(f"{ITEMS[iid]['name']} {have}/{qty}")
        if missing:
            await self.send('Brakuje materiałów: '+', '.join(missing)+'.')
            return
        prow=self.server.db.profession(self.account_id,'Kowalstwo')
        req=240 if target==2 else 340
        if int(prow['level'])<req:
            await self.send(f"Mk-{['I','II','III'][target-1]} wymaga Kowalstwo {req}. Masz {int(prow['level'])}.")
            return
        for iid,qty in costs.items(): self.consume_recipe_item(iid,qty)
        self.server.db.set_tech_set_mark_v0320(self.account_id,item_id,target)
        await self.send(f"Tech Set Upgrade zakończony: {item['name']} -> Mk-{'II' if target==2 else 'III'}. Obrona tej części rośnie o {5 if target==2 else 10}; Mk-III daje też mocniejszy bonus całego Tech Setu.")
        msgs,_,_=self.grant_profession_progress('Kowalstwo',160 if target==2 else 260,'crafting',90 if target==2 else 140)
        for msg in msgs: await self.send(msg)

    def tech_set_equipped_mark_multiplier_v0320(self):
        marks=[]
        tech_ids={x for rows in TECH_SET_ITEMS_V03114.values() for x in rows}
        for row in self.server.db.equipment(self.account_id):
            iid=str(row['item_id'])
            if iid in tech_ids: marks.append(self.server.db.tech_set_mark_v0320(self.account_id,iid))
        if not marks: return 1.0
        mk2=sum(1 for x in marks if x>=2); mk3=sum(1 for x in marks if x>=3)
        return 1.0 + min(0.10,mk2*0.005+mk3*0.0075)

    async def party_quest_status_v0320(self):
        members=self.server.party_sessions(self.account_id,same_room=self.character.room_id)
        await self.send(f"POSTĘP ZADAŃ DRUŻYNY: obok {len(members)} członków. Kill questy i boss kill credit liczą się każdemu obok. Gather/craft pozostają wyłącznie osobiste.")

    async def dungeon_party_bonus_status_v0320(self):
        st=dungeon_party_bonus_v0320(self)
        if not room_is_dungeon_v0320(self.character.room_id):
            await self.send('Dungeon Party Bonus: ta lokacja nie jest lochem.')
            return
        await self.send(f"Dungeon Party Bonus: {st['members']} osób obok; różne klasy {st['diverse']}; pełna drużyna: {'tak' if st['full'] else 'nie'}; bonus EXP +{st.get('bonus_pct',0)} procent.")

    async def recap2_v0320(self,death=False):
        summary=self.server.db.recap_summary_v0320(self.account_id)
        if death:
            await SessionProgressionAccessibilityV03052Mixin.death_recap_v03052(self)
        else:
            await SessionProgressionAccessibilityV03052Mixin.combat_recap_v03052(self)
        if summary:
            await self.send(f"PODSUMOWANIE: finalny cios: {summary['final_blow'] or 'brak'}; przyczyna: {summary['cause'] or 'brak'}; leczenie uratowało {int(summary['healing_saved'])} HP; guard uratował {int(summary['guard_saved'])} obrażeń.")
        events=list(reversed(self.server.db.combat_events_v0320(self.account_id,10)))
        if events:
            await self.send(f"Ostatnie zdarzenia walki: {len(events)}.")
            for i,row in enumerate(events,1): await self.send(f"{i}. {row['event_text']}")

