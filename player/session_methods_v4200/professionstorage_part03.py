# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def grant_profession_reward_xp(
    self, profession, profession_xp, tool_type, tool_xp, *,
    content_level=None, quest=None
):
        if not self.valid_tool_type(tool_type):
            raise ValueError(f"Nieznany typ narzędzia: {tool_type}")

        _guild_pct=self.guild_bonus_percent_v0926()
        prow = self.server.db.profession(
            self.account_id, profession
        )
        profession_cap = profession_max_level(profession)
        plevel = int(prow["level"])
        trow_preview = self.server.db.tool(self.account_id, tool_type)
        tlevel_preview = int(trow_preview["level"])
        raw_profession_xp=max(0,int(profession_xp or 0))
        raw_tool_xp=max(0,int(tool_xp or 0))
        stage=max(
            1,
            min(
                PROFESSION_MAX_LEVEL,
                int(content_level or max(plevel,tlevel_preview,1)),
            ),
        )
        base_prof_floor,base_tool_floor=self.profession_content_xp_floor_v11342(
            0,0,stage,tool_type
        )
        authored_prof_mult=self.profession_authored_xp_multiplier_v11343(
            max(raw_profession_xp,base_prof_floor),base_prof_floor
        )
        authored_tool_mult=self.profession_authored_xp_multiplier_v11343(
            max(raw_tool_xp,base_tool_floor),base_tool_floor
        )
        legacy_profession_xp = raw_profession_xp * PROFESSION_XP_GAIN_MULTIPLIER
        actual_profession_xp = v0190_scaled_gain(
            legacy_profession_xp, plevel, "profession", 40
        )
        tool_xp = v0190_scaled_gain(
            raw_tool_xp, tlevel_preview, "tool", 12
        )
        # Quest/order rewards do not point at one material, but the global
        # v1.13.42 profession-speed boost must still be real.
        actual_profession_xp=max(
            0,
            int(round(
                actual_profession_xp
                * max(0.25,float(PROFESSION_XP_GAIN_MULTIPLIER)/2.0)
            )),
        )
        if content_level is not None:
            _prof_mult,_tool_mult=self.profession_content_xp_multiplier_v11342(
                stage,tool_type
            )
            actual_profession_xp=max(
                0,
                int(round(
                    actual_profession_xp
                    * _prof_mult
                    * authored_prof_mult
                )),
            )
            tool_xp=max(
                0,
                int(round(tool_xp*_tool_mult*authored_tool_mult)),
            )
        else:
            actual_profession_xp=max(
                0,int(round(actual_profession_xp*authored_prof_mult))
            )
            tool_xp=max(0,int(round(tool_xp*authored_tool_mult)))
        from systems.profession_exp_pacing_v1201 import improved_work_xp
        actual_profession_xp = improved_work_xp(
            actual_profession_xp,
            self.profession_xp_to_next(plevel, profession),
            plevel, content_level, tool=False)
        tool_xp = improved_work_xp(
            tool_xp, self.tool_xp_to_next(tlevel_preview, tool_type),
            tlevel_preview, content_level, tool=True)
        from systems.profession_xp_v1203 import reward_xp_v1203
        actual_profession_xp = reward_xp_v1203(
            actual_profession_xp, self.profession_xp_to_next(plevel, profession),
            plevel, content_level)
        tool_xp = reward_xp_v1203(
            tool_xp, self.tool_xp_to_next(tlevel_preview, tool_type),
            tlevel_preview, content_level, tool=True)
        if quest is not None:
            from systems.profession_xp_v1203 import quest_reward_floor_v1203
            actual_profession_xp = quest_reward_floor_v1203(
                actual_profession_xp,
                self.profession_xp_to_next(plevel, profession),plevel,quest)
            tool_xp = quest_reward_floor_v1203(
                tool_xp,self.tool_xp_to_next(tlevel_preview,tool_type),
                tlevel_preview,quest,tool=True)
        from systems.live_progression_v1206 import xp_with_live_bonus
        actual_profession_xp = xp_with_live_bonus(actual_profession_xp, profession)
        tool_xp = xp_with_live_bonus(tool_xp, tool_type, tool=True)
        actual_profession_xp=max(0,int(round(actual_profession_xp*(1.0+_guild_pct/100.0))))
        tool_xp=max(0,int(round(tool_xp*(1.0+_guild_pct/100.0))))
        _title_pct = self.v0260_profession_xp_bonus_percent(profession, tool_type)
        if _title_pct:
            actual_profession_xp=max(0,int(round(actual_profession_xp*(1.0+_title_pct/100.0))))
            tool_xp=max(0,int(round(tool_xp*(1.0+_title_pct/100.0))))
        actual_profession_xp = self.apply_double_xp(actual_profession_xp)
        tool_xp = self.apply_double_xp(tool_xp)
        from systems.experience_bank_v2011 import banked_experience_v2011
        actual_profession_xp = banked_experience_v2011(
            self.server.db, self.account_id, actual_profession_xp,
            'profession', plevel, source_key=profession)
        tool_xp = banked_experience_v2011(
            self.server.db, self.account_id, tool_xp, 'tool',
            tlevel_preview, source_key=tool_type)
        self.session_summary_add("profession_xp", actual_profession_xp, profession)
        self.session_summary_add("tool_xp", tool_xp, tool_type)
        pxp = int(prow["xp"]) + actual_profession_xp
        actions = int(prow["actions"])

        await self.send(
            f"{profession}: nagroda +{actual_profession_xp} XP."
        )

        while plevel < profession_cap:
            needed = self.profession_xp_to_next(
                plevel, profession
            )
            if pxp < needed:
                break
            pxp -= needed
            plevel += 1
            await self.send(f"AWANS PROFESJI: {profession} osiąga poziom {plevel}.")

        if plevel >= profession_cap:
            plevel = profession_cap
            pxp = 0

        self.server.db.save_profession(
            self.account_id, profession, plevel, pxp, actions
        )
        if plevel>=profession_cap:
            await self.send(
                f"{profession}: poziom {plevel}, XP maksimum."
            )
        else:
            await self.send(
                f"{profession}: poziom {plevel}, XP {pxp} z "
                f"{self.profession_xp_to_next(plevel,profession)}."
            )

        trow = self.server.db.tool(self.account_id, tool_type)
        tlevel = int(trow["level"])
        txp = int(trow["xp"]) + tool_xp
        uses = int(trow["uses"])
        tool_name = self.tool_display_name_v11343(tool_type)

        await self.send(f"{tool_name}: nagroda +{tool_xp} XP.")

        tool_level_cap = tool_max_level(tool_type)
        while tlevel < tool_level_cap:
            needed = self.tool_xp_to_next(tlevel, tool_type)
            if txp < needed:
                break
            txp -= needed
            tlevel += 1
            await self.send(f"{tool_name} osiąga poziom {tlevel}.")

        if tlevel >= tool_level_cap:
            tlevel = tool_level_cap
            txp = 0

        self.server.db.save_tool(
            self.account_id, tool_type, tlevel, txp, uses
        )
        self._last_profession_reward_gain_v11343 = {
            "profession": str(profession),
            "profession_xp": int(actual_profession_xp),
            "profession_level": int(plevel),
            "profession_progress": int(pxp),
            "tool_type": str(tool_type),
            "tool_xp": int(tool_xp),
            "tool_level": int(tlevel),
            "tool_progress": int(txp),
            "content_level": int(stage),
        }
        if tlevel>=tool_level_cap:
            await self.send(
                f"{tool_name}: poziom {tlevel}, XP maksimum."
            )
        else:
            await self.send(
                f"{tool_name}: poziom {tlevel}, XP {txp} z "
                f"{self.tool_xp_to_next(tlevel,tool_type)}."
            )

