# -*- coding: utf-8 -*-
"""Soulbound v0.30.53 - handlers for extended crafting professions."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
from core.bootstrap_economy_professions import profession_max_rank, profession_rank, profession_rank_name, tool_tier, tool_tier_name
from core.classes_skills import ROOMS
from core.progression_600 import PROFESSION_MAX_LEVEL, TOOL_MAX_LEVEL, TOOL_MAX_TIER
from systems.crafting_quality import player_item_display_name_v0335
from systems.equipment_crafting import JEWELCRAFT_RECIPES
from systems.professions import V03053_CRAFT_RECIPES, V03053_ENCHANTS, V03053_PROFESSIONS, V1215_ENCHANT_RECIPES, V1215_ENCHANT_REQUIREMENTS, normalize_profession_name

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
        level=int(row['level'])
        await self.send(name.upper())
        await self.send(
            f"Poziom {level}/{PROFESSION_MAX_LEVEL}. "
            f"Ranga {profession_rank(level,name)}/{profession_max_rank(name)}: "
            f"{profession_rank_name(name,level)}. "
            f"XP: {self.profession_xp_status_text_v11343(name)}. "
            f"Akcje: {int(row['actions'])}."
        )
        await self.show_single_tool(cfg['tool_type'])
        await self.send(f"Warsztat: {ROOMS.get(cfg['station'],{}).get('name',cfg['station'])}.")
        await self.send(f"Receptury: receptury {name.lower()}. Wytwarzanie: {self.v03053_command_for(name)} <nazwa>.")

    def v03053_command_for(self,name):
        return {'Krawiectwo':'szyj / sew','Garbarstwo':'garbuj / tan','Stolarstwo':'stolarka / woodcraft','Zaklinanie':'zaklinaj / enchantitem'}.get(name,'craft')

    async def v03053_show_recipes(self, profession, filter_query=""):
        name=normalize_profession_name(profession)
        if name=='Zaklinanie':
            query=str(filter_query or '').strip().casefold()
            aliases={'str':'sila','strength':'sila','dex':'zrecznosc','dexterity':'zrecznosc',
                     'constitution':'kondycja','con':'kondycja','intelligence':'inteligencja',
                     'int':'inteligencja','will':'wola','willpower':'wola','health':'hp'}
            query=aliases.get(query,query)
            rows=[r for r in V1215_ENCHANT_RECIPES.values()
                  if not query or r['enchant_key']==query or str(r['min_profession_level'])==query]
            await self.send(f"RECEPTURY: ZAKLINANIE. Liczba: {len(rows)}. Komenda: zaklinaj <slot> <typ> [poziom].")
            if not query:
                await self.send('Typy: sila, zrecznosc, kondycja, inteligencja, wola, hp, mana. Wpisz receptury zaklinanie sila, aby zobaczyć wymagania i materiały konkretnego typu. Bez poziomu działa dotychczasowa wersja zaklęcia.')
                for typ, (label, _stat, _base, _mats) in V03053_ENCHANTS.items():
                    levels=sorted(r['min_profession_level'] for r in rows if r['enchant_key']==typ)
                    await self.send(f"{label}: poziomy {', '.join(map(str,levels))}.")
                return
            if not rows:
                await self.send('Nie znaleziono receptur tego typu. Dostępne: sila, zrecznosc, kondycja, inteligencja, wola, hp, mana.')
                return
            for r in sorted(rows,key=lambda x:(x['enchant_key'], x['min_profession_level'])):
                mats=', '.join(f"{player_item_display_name_v0335(i)} x{q}" for i,q in r['ingredients'].items())
                await self.send(f"{r['name']}. Zaklinanie poziom {r['min_profession_level']}. Fokus Runiczny. Składniki: {mats}. Wykonaj: zaklinaj <slot> {r['enchant_key']} {r['min_profession_level']}.")
            return
        if name=='Jubilerstwo':
            rows=[(k,v) for k,v in JEWELCRAFT_RECIPES.items() if str(k).startswith('v03053_')]
        else:
            rows=list(self.v03053_recipe_table(name).items())
        if not rows:
            await self.send('Brak receptur dla tej profesji.')
            return
        await self.send(f"RECEPTURY: {name.upper()}")
        for _rid,r in sorted(rows,key=lambda kv:int(kv[1].get('min_profession_level',1))):
            mats=', '.join(f"{player_item_display_name_v0335(i)} x{q}" for i,q in r.get('ingredients',{}).items())
            await self.send(f"{r['name']}. Poziom {r.get('min_profession_level',1)}. Składniki: {mats}.")

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
            await self.send('ZAKLINANIE: zaklinaj <slot> <sila|zrecznosc|kondycja|inteligencja|wola|hp|mana> [poziom]. Jedno zaklęcie na slot; nowe zastępuje stare. Lista: receptury zaklinanie, szczegóły: receptury zaklinanie sila.')
            await self.v03053_show_profession('Zaklinanie'); return False
        if len(parts)<2:
            await self.send('Użycie: zaklinaj <slot> <typ> [poziom].'); return False
        slot=parts[0].casefold(); key=parts[1].casefold().replace('ę','e').replace('ó','o').replace('ł','l').replace('ś','s').replace('ć','c').replace('ż','z').replace('ź','z').replace('ń','n').replace('ą','a')
        alias={'sila':'sila','strength':'sila','str':'sila','zrecznosc':'zrecznosc','dexterity':'zrecznosc','dex':'zrecznosc','kondycja':'kondycja','constitution':'kondycja','con':'kondycja','inteligencja':'inteligencja','intelligence':'inteligencja','int':'inteligencja','wola':'wola','will':'wola','willpower':'wola','hp':'hp','health':'hp','mana':'mana'}
        key=alias.get(key,key)
        ench=V03053_ENCHANTS.get(key)
        if not ench:
            await self.send('Nieznany typ zaklęcia. Wpisz receptury zaklinanie.'); return False
        if len(parts)>3 or (len(parts)==3 and not parts[2].isdigit()):
            await self.send('Użycie: zaklinaj <slot> <typ> [poziom]. Poziomy sprawdzisz: receptury zaklinanie <typ>.'); return False
        requested_level=int(parts[2]) if len(parts)==3 else V1215_ENCHANT_REQUIREMENTS[key]
        recipe=V1215_ENCHANT_RECIPES.get(f'{key}_{requested_level}')
        if recipe is None:
            await self.send('Brak takiej receptury. Wpisz receptury zaklinanie '+key+'.'); return False
        if self.combat_mob_key:
            await self.send('Nie możesz zaklinać podczas walki.'); return False
        eq={str(r['slot']).casefold():r for r in self.server.db.equipment(self.account_id)}
        if slot not in eq:
            await self.send('W tym slocie nie masz założonego przedmiotu.'); return False
        if self.character.room_id!='guild_arcane_chamber':
            await self.send('Zaklinać możesz w Komnacie Arkanów Gildii Dusz.'); return False
        if self.server.db.item_qty(self.account_id,'runic_focus')<=0:
            await self.send('Potrzebujesz Fokus Runiczny.'); return False
        prow=self.server.db.profession(self.account_id,'Zaklinanie'); level=int(prow['level'])
        req=recipe['min_profession_level']
        if level<req:
            await self.send(f"To zaklęcie wymaga Zaklinanie poziom {req}, masz {level}."); return False
        from core.bootstrap_economy_professions import required_tool_tier_for_level
        tool_level=int(self.server.db.tool(self.account_id,'enchanting')['level'])
        required_tier=required_tool_tier_for_level(req)
        if tool_tier(tool_level)<required_tier:
            await self.send(f"Receptura wymaga Fokus Runiczny Tier {required_tier}+, masz Tier {tool_tier(tool_level)}."); return False
        label,stat,base,_legacy_mats=ench
        mats=recipe['ingredients']
        missing=[f"{player_item_display_name_v0335(i)}: {self.available_recipe_item(i)}/{q}" for i,q in mats.items() if self.available_recipe_item(i)<q]
        if missing:
            await self.send('Brakuje składników: '+', '.join(missing)+'.'); return False
        # Wszystkie składniki sprawdzamy przed pobraniem; możliwe także zapasy magazynowe.
        for iid,q in mats.items():
            if not self.consume_recipe_item(iid,q):
                await self.send('Nie udało się pobrać składników. Zaklinanie przerwane.'); return False
        amt=self.v03053_enchant_amount(base,level)+recipe['tier_bonus']
        self.server.db.set_equipment_enchant_v03053(self.account_id,slot,key,stat,amt)
        await self.announce_profession_action_order_progress_v0713('enchanting', 1)
        messages,*_=self.grant_profession_progress(
            'Zaklinanie',max(25,req*2),'enchanting',max(20,req),content_level=req,
        )
        await self.send(f"Zaklinasz {player_item_display_name_v0335(eq[slot]['item_id'])}: {label} +{amt}. Receptura poziom {req}.")
        for m in messages: await self.send(m)
        return True

    async def v03053_enchants(self):
        rows=self.server.db.equipment_enchants_v03053(self.account_id)
        if not rows: await self.send('Nie masz aktywnych zaklęć na EQ.'); return
        await self.send('AKTYWNE ZAKLĘCIA')
        for r in rows: await self.send(f"{r['slot']}: {r['enchant_key']} +{r['amount']}.")
