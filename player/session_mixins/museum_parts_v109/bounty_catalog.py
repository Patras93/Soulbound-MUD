# -*- coding: utf-8 -*-
"""v109: muzeum, osiągnięcia i zlecenia — bounty_catalog. Historyczne metody bez zmian."""
from .dependencies import *

class MuseumBountyCatalogV109Mixin:
    def bounty_kill_candidates(self):
            result = []
            for mob_id in sorted(BESTIARY_CATALOG):
                template = MOB_TEMPLATES.get(mob_id, {})
                if not BESTIARY_SPAWN_ROOMS.get(mob_id):
                    continue
                if mob_id in BOSS_COLLECTION_CATALOG or template.get("mini_boss"):
                    continue
                if template.get("rare_mob") or template.get("rare_base_template") or template.get("elite_base_template"):
                    continue
                # v0.38.7: warianty zagęszczające lochy są techniczne. Ich
                # nazwy mogą mieć formę „Grobowy Upiór — Kościany Rycerz” i
                # nigdy nie mogą być osobnym celem Tablicy Zleceń.
                if template.get("dense_dungeon_variant"):
                    continue
                if v0863_is_boss_template(template):
                    continue
                result.append((mob_id, template.get("name") or "Nieznany przeciwnik"))
            # Pick only reachable, level-appropriate ordinary mobs.
            # If an exact band has no mobs, prefer the closest lower-level
            # targets. Never assign a wildly over-level target.
            char_level = max(1, min(800, int(getattr(
                getattr(self, 'character', None), 'character_level', 1) or 1)))
            ceiling = max(10, int(char_level * 1.20) + 5)
            lower = max(1, int(char_level * 0.65))
            eligible = [(mob_id, name, v0190_mob_stage(MOB_TEMPLATES[mob_id]))
                        for mob_id, name in result
                        if v0190_mob_stage(MOB_TEMPLATES[mob_id]) <= ceiling]
            close = [(mob_id, name) for mob_id, name, level in eligible
                     if lower <= level <= ceiling]
            if close:
                return close
            if eligible:
                best = max(level for _, _, level in eligible)
                return [(mob_id, name) for mob_id, name, level in eligible
                        if level >= max(1, best - 10)]
            return []

    def generate_bounty_offers(self):
            offers = []
            char_level = max(1, min(800, int(getattr(
                getattr(self, 'character', None), 'character_level', 1) or 1)))
            board_band = (char_level - 1) // 10
            kinds = list(BOUNTY_KINDS)
            random.shuffle(kinds)
            # Trzy różne typy na planszy zwiększają szansę, że gracz może wykonać
            # kontrakt bez zmiany aktualnej aktywności/profesji.
            for kind in kinds[:BOUNTY_OFFER_COUNT]:
                if kind == "kill":
                    candidates = self.bounty_kill_candidates()
                    if not candidates:
                        continue
                    target, name = random.choice(candidates)
                    needed = random.choice((8, 10, 12, 15))
                    base_needed = needed
                    label = f"Pokonaj {needed} razy: {name}"
                elif kind in ("mine", "fish", "wood", "herb"):
                    target = kind
                    base_needed = random.choice(BOUNTY_RESOURCE_NEEDS[kind])
                    needed = base_needed
                    if kind == "fish":
                        fish_level = self.profession_level_for_tool("fishing")
                        needed = max(
                            base_needed,
                            int(math.ceil(base_needed * v096_fishing_workload_scale(fish_level))),
                        )
                    label = f"{BOUNTY_RESOURCE_LABELS[kind]}: {needed} sztuk"
                else:
                    target = "any"
                    base_needed = random.choice(BOUNTY_RESOURCE_NEEDS.get(kind, (1, 2, 3)))
                    needed = base_needed
                    unit = {
                        "explore": "nowych sektorów", "event": "wydarzeń", "secret": "sekretów", "mini": "mini-lochów",
                    }.get(kind, "celów")
                    label = f"{BOUNTY_RESOURCE_LABELS.get(kind, kind)}: {needed} {unit}"
                reward_needed = base_needed
                if kind == "kill" and target in MOB_TEMPLATES:
                    reward_stage=v0190_mob_stage(MOB_TEMPLATES[target])
                elif kind in ("mine","fish","wood","herb"):
                    resource_level=max(1,self.profession_level_for_tool({"mine":"mining","fish":"fishing","wood":"woodcutting","herb":"herbalism"}[kind]))
                    reward_stage=max(resource_level, int(math.sqrt(char_level*resource_level)))
                else:
                    _char = getattr(self, "character", None)
                    _soul = int(getattr(_char, "soul_level", 1) or 1) if _char is not None else 1
                    try:
                        _mastery = int(self.highest_active_class_mastery())
                    except Exception:
                        _mastery = 1
                    reward_stage=max(1, _soul, _mastery)
                soul_xp=max(1,int(round(v0190_log_curve(reward_stage,V019_SOUL_KILL_NORMAL)*max(2.0,math.sqrt(reward_needed)))))
                reward_coins=max(1,int(round(v0190_log_curve(reward_stage,V019_QUEST_COIN)*0.75)))
                gold=max(1,reward_coins//SILVER_PER_GOLD)
                if reward_stage >= 300: gold=max(gold,500_000)
                elif reward_stage >= 200: gold=max(gold,250_000)
                elif reward_stage >= 150: gold=max(gold,100_000)
                elif reward_stage >= 100: gold=max(gold,25_000)
                offers.append({
                    "kind": kind,
                    "target": target,
                    "label": label,
                    "needed": int(needed),
                    "stage": int(reward_stage),
                    "board_band": int(board_band),
                    "reward_soul_xp": int(soul_xp),
                    "reward_gold": int(gold),
                })
            while len(offers) < BOUNTY_OFFER_COUNT:
                kind = random.choice(("mine", "fish", "wood", "herb"))
                target = kind
                base_needed = random.choice(BOUNTY_RESOURCE_NEEDS[kind])
                needed = base_needed
                if kind == "fish":
                    fish_level = self.profession_level_for_tool("fishing")
                    needed = max(
                        base_needed,
                        int(math.ceil(base_needed * v096_fishing_workload_scale(fish_level))),
                    )
                resource_level=max(1,self.profession_level_for_tool({"mine":"mining","fish":"fishing","wood":"woodcutting","herb":"herbalism"}[kind]))
                reward_stage=max(resource_level, int(math.sqrt(char_level*resource_level)))
                soul_xp=max(1,int(round(v0190_log_curve(reward_stage,V019_SOUL_KILL_NORMAL)*max(2.0,math.sqrt(base_needed)))))
                reward_coins=max(1,int(round(v0190_log_curve(reward_stage,V019_QUEST_COIN)*0.75)))
                gold=max(1,reward_coins//SILVER_PER_GOLD)
                offers.append({
                    "kind": kind,
                    "target": target,
                    "label": f"{BOUNTY_RESOURCE_LABELS[kind]}: {needed} sztuk",
                    "needed": int(needed),
                    "stage": int(reward_stage),
                    "board_band": int(board_band),
                    "reward_soul_xp": int(soul_xp),
                    "reward_gold": int(gold),
                })
            return offers[:BOUNTY_OFFER_COUNT]

    def bounty_content_stage_v11342(self, entry):
            row=dict(entry or {})
            stored=max(0,int(row.get("stage",0) or 0))
            if stored>0:
                return max(1,min(800,stored))
            kind=str(row.get("kind") or "")
            target=str(row.get("target") or "")
            if kind=="kill" and target in MOB_TEMPLATES:
                return max(1,min(800,v0190_mob_stage(MOB_TEMPLATES[target])))
            if kind in ("mine","fish","wood","herb"):
                tool_type={
                    "mine":"mining","fish":"fishing",
                    "wood":"woodcutting","herb":"herbalism",
                }[kind]
                return max(1,min(800,self.profession_level_for_tool(tool_type)))
            fallback=max(
                int(getattr(self.character,"soul_level",1) or 1),
                int(self.highest_active_class_mastery() or 1),
            )
            return max(1,min(800,fallback))

    def normalize_bounty_kill_entry_v0387(self, entry):
            """Return one clean, canonical bounty entry without technical mob names."""
            row = dict(entry or {})
            if str(row.get("kind") or "") != "kill":
                return row, False
            old_target = str(row.get("target") or "")
            canonical = canonical_bestiary_template_id(old_target)
            if canonical not in MOB_TEMPLATES:
                return row, False
            needed = max(1, int(row.get("needed", 1) or 1))
            clean_name = str(MOB_TEMPLATES[canonical].get("name") or canonical)
            clean_label = f"Pokonaj {needed} razy: {clean_name}"
            changed = old_target != canonical or str(row.get("label") or "") != clean_label
            row["target"] = canonical
            row["label"] = clean_label
            return row, changed

    def ensure_bounty_board(self):
            state = self.server.db.bounty_board_state(self.account_id)
            if not state.get("offers"):
                state["offers"] = self.generate_bounty_offers()
                self.server.db.save_bounty_board_state(
                    self.account_id,
                    offers=state["offers"],
                    active=state.get("active", {}),
                    completed_count=state.get("completed_count", 0),
                )
                return state

            active_contract = state.get('active') or {}
            board_level = max(1, min(800, int(getattr(
                getattr(self, 'character', None), 'character_level', 1) or 1)))
            board_band = (board_level - 1) // 10
            offers = state.get('offers') or []
            if (not active_contract and offers and
                    any(int(offer.get('board_band', -1)) != board_band
                        for offer in offers)):
                state['offers'] = self.generate_bounty_offers()
                self.server.db.save_bounty_board_state(
                    self.account_id, offers=state['offers'],
                    active={}, completed_count=state.get('completed_count', 0))
                return state

            # v0.38.7: napraw również już zapisane oferty/aktywny kontrakt
            # z wcześniejszej wersji, bez zerowania postępu gracza.
            changed = False
            clean_offers = []
            for offer in state.get("offers") or []:
                clean, was_changed = self.normalize_bounty_kill_entry_v0387(offer)
                clean_offers.append(clean)
                changed = changed or was_changed
            clean_active, active_changed = self.normalize_bounty_kill_entry_v0387(state.get("active") or {})
            changed = changed or active_changed
            state["offers"] = clean_offers
            state["active"] = clean_active
            if changed:
                self.server.db.save_bounty_board_state(
                    self.account_id, offers=clean_offers, active=clean_active,
                    completed_count=state.get("completed_count", 0),
                )
            return state
