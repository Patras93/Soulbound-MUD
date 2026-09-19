# -*- coding: utf-8 -*-
"""Soulbound v0.30.53 - handlers for extended crafting professions."""
class SessionProfessionsV03053Mixin:
    def v03053_recipe_table(self, profession):
        name=normalize_profession_name(profession)
        return {k:v for k,v in V03053_CRAFT_RECIPES.items() if v.get('profession')==name}

    async def v03053_show_profession(self, profession):
        name=normalize_profession_name(profession)
        cfg=V03053_PROFESSIONS.get(name)
        if not cfg:
            await self.send('Nie rozpoznaję tej profesji.')
            return
        row=self.server.db.profession(self.account_id,name)
        level=int(row['level']); tool=self.server.db.tool(self.account_id,cfg['tool_type'])
        await self.send(name.upper())
        await self.send(f"Level {level}/400. Ranga {profession_rank(level,name)}/{profession_max_rank(name)}: {profession_rank_name(name,level)}. XP {row['xp']}. Akcje {row['actions']}.")
        await self.send(f"Narzędzie: {cfg['tool_name']}, level {tool['level']}/400, Tier {tool_tier(tool['level'])}/40: {tool_tier_name(cfg['tool_type'],tool['level'])}.")
        await self.send(f"Warsztat: {ROOMS.get(cfg['station'],{}).get('name',cfg['station'])}.")
        await self.send(f"Receptury: receptury {name.lower()}. Wytwarzanie: {self.v03053_command_for(name)} <nazwa>.")

    def v03053_command_for(self,name):
        return {'Krawiectwo':'szyj / sew','Garbarstwo':'garbuj / tan','Stolarstwo':'stolarka / woodcraft','Zaklinanie':'zaklinaj / enchantitem'}.get(name,'craft')

    async def v03053_show_recipes(self, profession):
        name=normalize_profession_name(profession)
        if name=='Jubilerstwo':
            rows=[(k,v) for k,v in JEWELCRAFT_RECIPES.items() if str(k).startswith('v03053_')]
        else:
            rows=list(self.v03053_recipe_table(name).items())
        if not rows:
            await self.send('Brak receptur dla tej profesji.')
            return
        await self.send(f"RECEPTURY: {name.upper()}")
        for _rid,r in sorted(rows,key=lambda kv:int(kv[1].get('min_profession_level',1))):
            mats=', '.join(f"{ITEMS.get(i,{}).get('name',i)} x{q}" for i,q in r.get('ingredients',{}).items())
            await self.send(f"{r['name']}. Level {r.get('min_profession_level',1)}. Składniki: {mats}.")

    async def v03053_craft(self, profession, query):
        name=normalize_profession_name(profession)
        if not str(query or '').strip():
            await self.v03053_show_recipes(name); return False
        return await self.perform_recipe(query,self.v03053_recipe_table(name),name.lower())

    def v03053_enchant_amount(self, base, profession_level):
        return int(base + max(0,int(profession_level)-1)//40)

    async def v03053_enchant(self,args):
        parts=str(args or '').split()
        if not parts or parts[0].casefold() in ('lista','list','info'):
            await self.send('ZAKLINANIE / ENCHANTING: zaklinaj / enchantitem <slot> <sila|strength|zrecznosc|dexterity|kondycja|constitution|inteligencja|intelligence|wola|will|hp|mana>. Jedno zaklęcie na slot; nowe zastępuje stare.')
            await self.v03053_show_profession('Zaklinanie'); return False
        if len(parts)<2:
            await self.send('Użycie: zaklinaj / enchantitem <slot> <typ>.'); return False
        slot=parts[0].casefold(); key=parts[1].casefold().replace('ę','e').replace('ó','o').replace('ł','l').replace('ś','s').replace('ć','c').replace('ż','z').replace('ź','z').replace('ń','n').replace('ą','a')
        alias={'sila':'sila','strength':'sila','str':'sila','zrecznosc':'zrecznosc','dexterity':'zrecznosc','dex':'zrecznosc','kondycja':'kondycja','constitution':'kondycja','con':'kondycja','inteligencja':'inteligencja','intelligence':'inteligencja','int':'inteligencja','wola':'wola','will':'wola','willpower':'wola','hp':'hp','health':'hp','mana':'mana'}
        key=alias.get(key,key)
        ench=V03053_ENCHANTS.get(key)
        eq={str(r['slot']).casefold():r for r in self.server.db.equipment(self.account_id)}
        if slot not in eq:
            await self.send('W tym slocie nie masz założonego przedmiotu.'); return False
        if not ench:
            await self.send('Nieznany typ zaklęcia. Wpisz zaklinaj lista albo enchantitem list.'); return False
        if self.character.room_id!='guild_arcane_chamber':
            await self.send('Zaklinać możesz w Komnacie Arkanów Gildii Dusz.'); return False
        tool_item='runic_focus'
        if self.server.db.item_qty(self.account_id,tool_item)<=0:
            await self.send('Potrzebujesz Fokus Runiczny.'); return False
        prow=self.server.db.profession(self.account_id,'Zaklinanie'); level=int(prow['level'])
        req=max(1, {'sila':1,'zrecznosc':1,'kondycja':30,'inteligencja':60,'wola':100,'hp':160,'mana':220}.get(key,1))
        if level<req:
            await self.send(f"To zaklęcie wymaga Zaklinanie level {req}, masz {level}."); return False
        label,stat,base,mats=ench
        missing=[f"{ITEMS.get(i,{}).get('name',i)}: {self.server.db.item_qty(self.account_id,i)}/{q}" for i,q in mats.items() if self.server.db.item_qty(self.account_id,i)<q]
        if missing:
            await self.send('Brakuje składników: '+', '.join(missing)+'.'); return False
        for iid,q in mats.items(): self.server.db.remove_item(self.account_id,iid,q)
        amt=self.v03053_enchant_amount(base,level)
        self.server.db.set_equipment_enchant_v03053(self.account_id,slot,key,stat,amt)
        messages,*_=self.grant_profession_progress('Zaklinanie',max(25,level*2),'enchanting',max(20,level))
        await self.send(f"Zaklinasz {ITEMS.get(eq[slot]['item_id'],{}).get('name',eq[slot]['item_id'])}: {label} +{amt}.")
        for m in messages: await self.send(m)
        return True

    async def v03053_enchants(self):
        rows=self.server.db.equipment_enchants_v03053(self.account_id)
        if not rows: await self.send('Nie masz aktywnych zaklęć na EQ.'); return
        await self.send('AKTYWNE ZAKLĘCIA')
        for r in rows: await self.send(f"{r['slot']}: {r['enchant_key']} +{r['amount']}.")
