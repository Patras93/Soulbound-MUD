# -*- coding: utf-8 -*-
"""Modul v109: artifacts; oryginalne metody bez zmian AST."""
from .dependencies import *

class ArtifactsV109Mixin:

    async def artifact_upgrade_v020(self,args=""):
            query=normalize_lookup_text(args)
            candidates=[]
            for fid,data in V017_ARTIFACTS.items():
                tier,item_id=v0200_artifact_owned_tier(self.server.db,self.account_id,fid)
                if tier:
                    candidates.append((fid,data,tier,item_id))
            if not query:
                await self.send("ROZWÓJ ARTEFAKTÓW")
                if not candidates: await self.send("Nie posiadasz jeszcze artefaktu frakcyjnego."); return
                for fid,data,tier,item_id in candidates:
                    await self.send(f"{data['name']}: poziom {tier}/{V020_ARTIFACT_MAX_TIER}. " + ("Maksymalny." if tier>=V020_ARTIFACT_MAX_TIER else "Użyj ulepszartefakt <nazwa>."))
                return
            chosen=None
            for row in candidates:
                fid,data,tier,item_id=row
                if query in normalize_lookup_text(data['name']) or query in normalize_lookup_text(fid): chosen=row; break
            if not chosen:
                await self.send("Nie znajduję posiadanego artefaktu o tej nazwie."); return
            fid,data,tier,item_id=chosen
            if tier>=V020_ARTIFACT_MAX_TIER: await self.send(f"Ten artefakt ma już maksymalny poziom {V020_ARTIFACT_MAX_TIER}."); return
            if any(row["item_id"] == item_id for row in self.equipped_item_rows()):
                await self.send("Najpierw zdejmij artefakt. Ulepszanie nie zmienia założonego przedmiotu w locie."); return
            next_tier=tier+1; req=V020_ARTIFACT_UPGRADE_COSTS[next_tier]; missing=[]
            for iid,qty in req.items():
                if iid=="coins": continue
                have=self.server.db.item_qty(self.account_id,iid)
                if have<qty: missing.append(f"{ITEMS[iid]['name']} {have}/{qty}")
            coins=int(req.get("coins",0)); wallet=self.character_wallet_silver_value()
            if wallet<coins: missing.append(f"waluta {currency_reading_text(wallet,0,0)} / {currency_price_text(coins)}")
            if missing:
                await self.send("Brakuje: "+"; ".join(missing)+"."); return
            # Nie ma RNG/faila: dopiero po pełnej walidacji pobieramy koszt i zamieniamy przedmiot.
            for iid,qty in req.items():
                if iid!="coins": self.server.db.remove_item(self.account_id,iid,qty)
            self.character.silver=wallet-coins; self.character.gold=0; self.character.mithril=0
            self.server.db.remove_item(self.account_id,item_id,1)
            new_item=V020_ARTIFACT_VARIANTS[fid][next_tier-1]; self.server.db.add_item(self.account_id,new_item,1); self.server.db.save_character(self.character)
            await self.record_item_collection(new_item,source="Rozwój artefaktu",announce=True)
            await self.send(f"Artefakt rozwinięty bez ryzyka: {ITEMS[new_item]['name']}. Koszt waluty: {currency_price_text(coins)}.")

    async def show_artifacts_v017(self):
            await self.send("ARTEFAKTY FRAKCYJNE")
            discovered = self.server.db.collection_entry_ids(self.account_id, "unique")
            for faction_id, data in V017_ARTIFACTS.items():
                item_id = data["item_id"]
                owned = self.server.db.item_qty(self.account_id, item_id) > 0 or item_id in discovered
                equipped = any(row["item_id"] == item_id for row in self.equipped_item_rows())
                state = "założony" if equipped else ("odkryty" if owned else "nieodkryty")
                await self.send(f"{data['name']} — {V016_FACTIONS[faction_id]['name']}. {state}. {data['effect']}")

    async def show_biome_sets_v017(self, args=""):
            query = normalize_lookup_text(args)
            counts = self.regional_set_counts()
            await self.send("ZESTAWY BIOMOWE")
            shown = 0
            for kind, name in V017_BIOME_SET_NAMES.items():
                if query and query not in normalize_lookup_text(kind) and query not in normalize_lookup_text(name) and query not in normalize_lookup_text(V013_FRONTIER_SPECS[kind]["zone"]):
                    continue
                sid = f"v017_{kind}"
                count = int(counts.get(sid, 0))
                cfg = REGIONAL_SET_BONUSES[sid]
                await self.send(
                    f"{name}: {count}/6 założonych. Biom: {V013_FRONTIER_SPECS[kind]['zone']}. "
                    f"2/6 HP/Mana +{int(round((cfg['hp']-1)*100))}%, "
                    f"4/6 obrażenia +{int(round((cfg['damage']-1)*100))}%, "
                    f"6/6 obrona +{int(round((cfg['defense']-1)*100))}%."
                )
                shown += 1
            if not shown:
                await self.send("Nie rozpoznaję takiego zestawu biomowego.")
