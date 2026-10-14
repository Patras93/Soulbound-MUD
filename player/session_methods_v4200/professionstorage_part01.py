# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
def valid_tool_type(self, tool_type):
        return tool_type in (
            "fishing",
            "mining",
            "woodcutting",
            "crafting",
            "cooking",
            "herbalism",
            "alchemy",
            "jewelcrafting",
            "tailoring",
            "leatherworking",
            "carpentry",
            "enchanting",
            "archaeology",
            "cartography_profession",
        )


def tool_display_name_v11343(self, tool_type):
        return {
            "fishing": "Wędka",
            "mining": "Kilof",
            "woodcutting": "Piła",
            "crafting": "Młot Rzemieślniczy",
            "cooking": "Nóż Kucharski",
            "herbalism": "Sierp Zielarski",
            "alchemy": "Moździerz Alchemiczny",
            "jewelcrafting": "Szczypce Jubilerskie",
            "tailoring": "Zestaw Krawiecki",
            "leatherworking": "Nóż Garbarski",
            "carpentry": "Narzędzia Ciesielskie",
            "enchanting": "Fokus Runiczny",
            "archaeology": "Pędzel Archeologa",
            "cartography_profession": "Kompas Mierniczy",
        }.get(str(tool_type),str(tool_type))


def tool_progress_state(self):
        result = {}
        for tool_type in (
            "fishing",
            "mining",
            "woodcutting",
            "crafting",
            "cooking",
            "herbalism",
            "alchemy",
            "jewelcrafting",
            "tailoring",
            "leatherworking",
            "carpentry",
            "enchanting",
            "archaeology",
            "cartography_profession",
        ):
            row = self.server.db.tool(self.account_id, tool_type)
            result[tool_type] = (
                int(row["level"]),
                int(row["xp"]),
                int(row["uses"]),
            )
        return result


def profession_content_level_v11342(
    self, item_id=None, item=None, recipe=None, explicit_level=None
):
        """Kanoniczny poziom trudności materiału/przedmiotu/receptury.

        Nie skaluje po levelu gracza. XP ma rosnąć dlatego, że praca jest
        trudniejsza: lepsza ruda, ryba, zioło, receptura, EQ do salvage itd.
        """
        levels = []
        if explicit_level is not None:
            try:
                explicit_value=int(explicit_level)
            except (TypeError, ValueError):
                explicit_value=0
            if explicit_value>0:
                levels.append(explicit_value)
        if item is None and item_id:
            item = ITEMS.get(str(item_id), {})
        for source in (item or {}, recipe or {}):
            for key in (
                "generator_level",
                "min_tool_level",
                "min_profession_level",
                "required_character_level",
                "required_mastery",
                "source_progression_stage",
            ):
                try:
                    value = int(source.get(key, 0) or 0)
                except (TypeError, ValueError):
                    value = 0
                if value > 0:
                    levels.append(value)
        return max(1, min(PROFESSION_MAX_LEVEL, max(levels or [1])))


def profession_content_xp_floor_v11342(
    self, profession_xp, tool_xp, content_level, tool_type
):
        """Usuń płaskie XP bez podwójnego pompowania dobrych receptur.

        Stare niskie/stałe nagrody są podciągane do rosnącego minimum.
        Receptury, które już mają większe authored XP, zachowują je.
        Młot Rzemieślniczy ma wyższe minimum, bo wcześniej odstawał.
        """
        stage = max(1, min(PROFESSION_MAX_LEVEL, int(content_level or 1)))
        profession_floor = 12 + stage // 4
        tool_floor = 10 + stage // 5
        if str(tool_type) == "crafting":
            tool_floor = max(tool_floor, 15 + stage // 3)
        return (
            max(max(0, int(profession_xp or 0)), profession_floor),
            max(max(0, int(tool_xp or 0)), tool_floor),
        )


def profession_content_xp_multiplier_v11342(self, content_level, tool_type=""):
        """Realny mnożnik jakości treści nakładany PO Generator Core.

        v0190_scaled_gain celowo ignoruje wielkość starego raw XP, więc
        sam authored tool_xp/profession_xp nie różnicował materiałów.
        Poziom 1 daje ~x1, a poziom 600 ~x2. Młot ma dodatkowo x1.35.
        """
        stage=max(1,min(PROFESSION_MAX_LEVEL,int(content_level or 1)))
        # v1.13.58: a 1->2x spread across 600 levels was technically
        # dynamic but felt almost flat.  Difficulty/material quality now
        # matters strongly while remaining smooth: ~x1 at level 1, ~x2
        # near 100, ~x3.5 near 300 and ~x6 near 600.
        progress=(stage-1)/float(max(1,PROFESSION_MAX_LEVEL-1))
        material_mult=1.0 + 5.0*(progress ** 0.78)
        tool_mult=material_mult
        if str(tool_type)=="crafting":
            tool_mult*=1.35
        return material_mult,tool_mult


def grant_profession_progress(
    self, profession, prof_xp, tool_type, tool_xp,
    tool_progress=True, content_level=None, batch_count=1
):
        if not self.valid_tool_type(tool_type):
            raise ValueError(f"Nieznany typ narzędzia: {tool_type}")

        raw_prof_xp=max(0,int(prof_xp or 0))
        raw_tool_xp=max(0,int(tool_xp or 0))
        content_stage=max(
            1,
            min(
                PROFESSION_MAX_LEVEL,
                int(content_level or 1),
            ),
        )
        base_prof_floor,base_tool_floor=self.profession_content_xp_floor_v11342(
            0,0,content_stage,tool_type
        )
        if content_level is not None:
            prof_xp, tool_xp = self.profession_content_xp_floor_v11342(
                raw_prof_xp, raw_tool_xp, content_stage, tool_type
            )
        else:
            prof_xp,tool_xp=raw_prof_xp,raw_tool_xp

        authored_prof_mult=self.profession_authored_xp_multiplier_v11343(
            prof_xp,base_prof_floor
        )
        authored_tool_mult=self.profession_authored_xp_multiplier_v11343(
            tool_xp,base_tool_floor
        )

        _guild_pct=self.guild_bonus_percent_v0926()
        prow = self.server.db.profession(
            self.account_id, profession
        )
        profession_cap = profession_max_level(profession)
        plevel = int(prow["level"])
        trow_preview = self.server.db.tool(self.account_id, tool_type)
        tlevel_preview = int(trow_preview["level"])
        legacy_prof_xp = max(0, int(prof_xp)) * PROFESSION_XP_GAIN_MULTIPLIER
        actual_prof_xp = v0190_scaled_gain(
            legacy_prof_xp, plevel, "profession", 40
        )
        tool_xp = v0190_scaled_gain(
            tool_xp, tlevel_preview, "tool", 12
        )

        # v1.13.42: Generator Core daje bazę zależną od bieżącego levelu,
        # a jakość wykonywanej pracy różnicuje realny przyrost. Wcześniej
        # raw XP był ignorowany przez v0190_scaled_gain, więc miedź i
        # Eternium mogły dawać ten sam realny postęp.
        if content_level is None:
            content_stage=max(
                1,
                min(PROFESSION_MAX_LEVEL,max(plevel,tlevel_preview,1)),
            )
        content_prof_mult,content_tool_mult=(
            self.profession_content_xp_multiplier_v11342(
                content_stage,tool_type
            )
        )
        # Historyczne x2 było punktem odniesienia. v1.13.42 ustawia x4,
        # czyli realnie około 2x szybsze profession leveling niż wcześniej.
        profession_speed_mult=max(
            0.25,float(PROFESSION_XP_GAIN_MULTIPLIER)/2.0
        )
        actual_prof_xp=max(
            0,
            int(round(
                actual_prof_xp
                * profession_speed_mult
                * content_prof_mult
                * authored_prof_mult
            )),
        )
        tool_xp=max(
            0,
            int(round(
                tool_xp
                * content_tool_mult
                * authored_tool_mult
            )),
        )

        # v1.17.6: a batch is still a single action, but its XP must not
        # plateau merely because the authored XP ratio was capped. Apply
        # effort after the generated baseline, with diminishing returns.
        batch_effort = profession_batch_effort_v1176(batch_count)
        if batch_effort > 1.0:
            actual_prof_xp = max(0, int(round(actual_prof_xp * batch_effort)))
            tool_xp = max(0, int(round(tool_xp * batch_effort)))

        actual_prof_xp=max(0,int(round(actual_prof_xp*(1.0+_guild_pct/100.0))))
        tool_xp=max(0,int(round(tool_xp*(1.0+_guild_pct/100.0))))
        _title_pct = self.v0260_profession_xp_bonus_percent(profession, tool_type)
        if _title_pct:
            actual_prof_xp=max(0,int(round(actual_prof_xp*(1.0+_title_pct/100.0))))
            tool_xp=max(0,int(round(tool_xp*(1.0+_title_pct/100.0))))
        _mentor_pct = self.mentor_bonus_percent_v03050()
        if _mentor_pct:
            actual_prof_xp=max(0,int(round(actual_prof_xp*(1.0+_mentor_pct/100.0))))
            tool_xp=max(0,int(round(tool_xp*(1.0+_mentor_pct/100.0))))
            self.mentor_record_activity_v03051()
        actual_prof_xp = self.apply_double_xp(actual_prof_xp)
        tool_xp = self.apply_double_xp(tool_xp)
        # v2.32.19: the ordinary gather/craft route MUST obey the same
        # independent full Multi Cap as class, quest, order and skill XP.
        # Preserve all surplus in separate SQLite profession/tool ledgers.
        from systems.experience_bank_v2011 import banked_experience_v2011
        actual_prof_xp = banked_experience_v2011(
            self.server.db, self.account_id, actual_prof_xp,
            'profession', plevel, source_key=profession)
        if tool_progress:
            tool_xp = banked_experience_v2011(
                self.server.db, self.account_id, tool_xp,
                'tool', tlevel_preview, source_key=tool_type)
        self.session_summary_add("profession_xp", actual_prof_xp, profession)
        if tool_progress:
            self.session_summary_add("tool_xp", tool_xp, tool_type)
        old_profession_rank = profession_rank(
            plevel, profession
        )
        pxp = int(prow["xp"]) + actual_prof_xp
        actions = int(prow["actions"]) + 1
        messages = [f"{profession}: +{actual_prof_xp} XP."]

        while plevel < profession_cap:
            needed = self.profession_xp_to_next(
                plevel, profession
            )
            if pxp < needed:
                break
            pxp -= needed
            plevel += 1
            messages.append(f"AWANS PROFESJI: {profession} osiąga poziom {plevel}.")
        if plevel >= profession_cap:
            plevel = profession_cap
            pxp = 0
        self.server.db.save_profession(
            self.account_id, profession, plevel, pxp, actions
        )
        if plevel>=profession_cap:
            messages.append(
                f"{profession}: poziom {plevel}, XP maksimum."
            )
        else:
            messages.append(
                f"{profession}: poziom {plevel}, XP {pxp} z "
                f"{self.profession_xp_to_next(plevel,profession)}."
            )
        # v0.70.0: mastery contracts count only real profession actions.
        # Reward XP uses grant_profession_reward_xp(), so it cannot recurse.
        for quest_id, quest_progress, quest_needed in self.server.db.increment_profession_action_quests_v0700(
            self.account_id, profession, tool_type, 1
        ):
            quest_name = QUESTS.get(quest_id, {}).get("name", quest_id)
            if int(quest_progress) >= int(quest_needed):
                messages.append(
                    f"Postęp questa: {quest_name}. Postęp {quest_progress} z {quest_needed}. GOTOWE DO ODDANIA."
                )
            else:
                messages.append(
                    f"Postęp questa: {quest_name}. Postęp {quest_progress} z {quest_needed}."
                )

        new_profession_rank = profession_rank(
            plevel, profession
        )
        max_profession_rank = profession_max_rank(
            profession
        )
        if new_profession_rank > old_profession_rank:
            messages.append(
                f"{profession}: awansujesz na Rangę {new_profession_rank} "
                f"z {max_profession_rank}: "
                f"{profession_rank_name(profession, plevel)}."
            )

        trow = self.server.db.tool(self.account_id, tool_type)
        tlevel = int(trow["level"])
        if tool_progress:
            old_tool_tier = tool_tier(tlevel)
            txp = int(trow["xp"]) + tool_xp
            uses = int(trow["uses"]) + 1
            tool_name = {
                "fishing": "Wędka",
                "mining": "Kilof",
                "woodcutting": "Piła",
                "crafting": "Młot Rzemieślniczy",
                "cooking": "Nóż Kucharski",
                "herbalism": "Sierp Zielarski",
                "alchemy": "Moździerz Alchemiczny",
                "jewelcrafting": "Szczypce Jubilerskie",
                "tailoring": "Zestaw Krawiecki",
                "leatherworking": "Nóż Garbarski",
                "carpentry": "Narzędzia Ciesielskie",
                "enchanting": "Fokus Runiczny",
                "archaeology": "Pędzel Archeologa",
                "cartography_profession": "Kompas Mierniczy",
            }.get(tool_type, tool_type)
            messages.append(f"{tool_name}: +{tool_xp} XP narzędzia.")

            tool_level_cap = tool_max_level(tool_type)
            while tlevel < tool_level_cap:
                needed = self.tool_xp_to_next(tlevel, tool_type)
                if txp < needed:
                    break
                txp -= needed
                tlevel += 1
                messages.append(f"{tool_name} osiąga poziom {tlevel}.")
            if tlevel >= tool_level_cap:
                tlevel = tool_level_cap
                txp = 0
            self.server.db.save_tool(
                self.account_id, tool_type, tlevel, txp, uses
            )
            if tlevel>=tool_level_cap:
                messages.append(
                    f"{tool_name}: poziom {tlevel}, XP maksimum."
                )
            else:
                messages.append(
                    f"{tool_name}: poziom {tlevel}, XP {txp} z "
                    f"{self.tool_xp_to_next(tlevel,tool_type)}."
                )

            new_tool_tier = tool_tier(tlevel)
            if new_tool_tier > old_tool_tier:
                messages.append(
                    f"{tool_name} awansuje na Tier {new_tool_tier} z {TOOL_MAX_TIER}: "
                    f"{tool_tier_name(tool_type, tlevel)}. "
                    f"Szansa na dodatkowy urobek: "
                    f"{int(tool_tier_bonus_chance(tlevel) * 100)} procent."
                )

        _char_stage=max(1,min(CHARACTER_MAX_LEVEL,max(plevel,tlevel)))
        _char_gain=balance_math.axis_gain("character",_char_stage,0.35)
        messages.extend(
            self.add_character_xp_with_event(
                _char_gain,
                content_level=_char_stage,
                content_scaled=True,
            )
        )
        self.server.db.save_character(self.character)
        self._last_profession_progress_gain_v11343 = {
            "profession": str(profession),
            "profession_xp": int(actual_prof_xp),
            "profession_level": int(plevel),
            "profession_progress": int(pxp),
            "tool_type": str(tool_type),
            "tool_xp": int(tool_xp if tool_progress else 0),
            "tool_level": int(tlevel),
            "tool_progress": int(txp) if tool_progress else int(trow["xp"]),
            "content_level": int(content_stage),
            "batch_count": max(1, int(batch_count)),
        }
        return messages, plevel, tlevel


def grant_tool_progress(
    self, tool_type, tool_xp, *, content_level=None
):
        if not self.valid_tool_type(tool_type):
            raise ValueError(f"Nieznany typ narzędzia: {tool_type}")
        row = self.server.db.tool(self.account_id, tool_type)
        level = int(row["level"])
        old_tier = tool_tier(level)
        raw_tool_xp=max(0,int(tool_xp or 0))
        stage=max(
            1,
            min(PROFESSION_MAX_LEVEL,int(content_level or level or 1)),
        )
        _base_prof,_base_tool=self.profession_content_xp_floor_v11342(
            0,0,stage,tool_type
        )
        authored_tool_mult=self.profession_authored_xp_multiplier_v11343(
            max(raw_tool_xp,_base_tool),_base_tool
        )
        tool_xp = v0190_scaled_gain(raw_tool_xp, level, "tool", 12)
        if content_level is not None:
            _prof_mult,_tool_mult=self.profession_content_xp_multiplier_v11342(
                stage,tool_type
            )
            tool_xp=max(
                0,
                int(round(tool_xp*_tool_mult*authored_tool_mult)),
            )
        else:
            tool_xp=max(0,int(round(tool_xp*authored_tool_mult)))
        tool_xp = self.apply_double_xp(tool_xp)
        from systems.experience_bank_v2011 import banked_experience_v2011
        tool_xp = banked_experience_v2011(
            self.server.db, self.account_id, tool_xp, 'tool', level,
            source_key=tool_type)
        self.session_summary_add("tool_xp", tool_xp, tool_type)
        xp = int(row["xp"]) + max(0, int(tool_xp))
        uses = int(row["uses"]) + 1

        tool_name = {
            "fishing": "Wędka",
            "mining": "Kilof",
            "woodcutting": "Piła",
            "crafting": "Młot Rzemieślniczy",
            "cooking": "Nóż Kucharski",
            "herbalism": "Sierp Zielarski",
            "alchemy": "Moździerz Alchemiczny",
            "jewelcrafting": "Szczypce Jubilerskie",
            "tailoring": "Zestaw Krawiecki",
            "leatherworking": "Nóż Garbarski",
            "carpentry": "Narzędzia Ciesielskie",
            "enchanting": "Fokus Runiczny",
            "archaeology": "Pędzel Archeologa",
            "cartography_profession": "Kompas Mierniczy",
        }.get(tool_type, tool_type)

        messages = [f"{tool_name}: +{tool_xp} XP narzędzia."]

        tool_level_cap = tool_max_level(tool_type)
        while level < tool_level_cap:
            needed = self.tool_xp_to_next(level, tool_type)
            if xp < needed:
                break
            xp -= needed
            level += 1
            messages.append(f"{tool_name} osiąga poziom {level}.")

        if level >= tool_level_cap:
            level = tool_level_cap
            xp = 0

        self.server.db.save_tool(
            self.account_id, tool_type, level, xp, uses
        )
        if level>=tool_level_cap:
            messages.append(f"{tool_name}: poziom {level}, XP maksimum.")
        else:
            messages.append(
                f"{tool_name}: poziom {level}, XP {xp} z "
                f"{self.tool_xp_to_next(level,tool_type)}."
            )

        new_tier = tool_tier(level)
        if new_tier > old_tier:
            if tool_type == "cooking":
                bonus_name = "dodatkową potrawę"
            elif tool_type == "crafting":
                bonus_name = "dodatkowy produkt receptury"
            else:
                bonus_name = "dodatkowy urobek"
            messages.append(
                f"{tool_name} awansuje na Tier {new_tier} z {TOOL_MAX_TIER}: "
                f"{tool_tier_name(tool_type, level)}. "
                f"Szansa na {bonus_name}: "
                f"{int(tool_tier_bonus_chance(level) * 100)} procent."
            )

        _char_stage=max(1,min(CHARACTER_MAX_LEVEL,level))
        _char_gain=balance_math.axis_gain("character",_char_stage,0.25)
        messages.extend(
            self.add_character_xp_with_event(
                _char_gain,
                content_level=_char_stage,
                content_scaled=True,
            )
        )
        self.server.db.save_character(self.character)
        return messages, level

