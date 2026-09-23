# -*- coding: utf-8 -*-
"""Soulbound v0.37.0 - Public Server Records, Hall of Fame and Profession Records."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
from core.mines_threat import COMMAND_ALIASES
from player.session import (
    SessionAdminGatheringSalesMixin,
    SessionCoreProgressionMixin,
    SessionCraftingExpansionV03114Mixin,
    SessionCraftingInventoryEquipmentMixin,
    SessionProfessionsStorageGuideMixin,
    SessionSocialExpansionMixin,
    SessionWorldProgressionMixin,
)
from player.session_mixins.crafting import crafting_output_is_quality_equipment_v03054
from player.session_mixins.crafting_expansion import (
    BLACKSMITH_TIERS,
    CRAFT_RECIPES,
    ITEMS,
    SALVAGE_SMELT_FALLBACK_V03113,
    find_by_name,
    normalize_lookup_text,
    player_item_display_name_v0335,
    required_tool_tier_for_level,
    tool_tier,
)
from player.session_mixins.gathering_actions import format_fish_weight
from player.session_mixins.inventory_equipment import GEM_QUALITY_ORDER
from player.session_mixins.skill_learning import MOB_TEMPLATES
from storage.database import Database
from systems.crafting_quality import CRAFT_QUALITY_ORDER_V03054
from world.equipment_help import HELP_TOPICS, HELP_TOPIC_ALIASES


V0370_VERSION = "0.37.0"

# ----------------------------- Database ---------------------------------
_V0370_DB_INIT_BEFORE = Database.__init__

def _v0370_db_init(self, path):
    _V0370_DB_INIT_BEFORE(self, path)
    self.conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS server_profession_records_v0370 (
            record_key TEXT PRIMARY KEY,
            value INTEGER NOT NULL DEFAULT 0,
            holder_account_id INTEGER NOT NULL DEFAULT 0,
            holder_name TEXT NOT NULL DEFAULT '',
            text_value TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS hall_of_fame_v0370 (
            achievement_key TEXT PRIMARY KEY,
            category TEXT NOT NULL DEFAULT '',
            holder_account_id INTEGER NOT NULL DEFAULT 0,
            holder_name TEXT NOT NULL DEFAULT '',
            detail TEXT NOT NULL DEFAULT '',
            achieved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    self.conn.commit()

Database.__init__ = _v0370_db_init

def _db_v0370_record_max(self, key, value, account_id, holder_name, text_value=""):
    key=str(key); value=max(0,int(value or 0)); account_id=int(account_id or 0)
    old=self.conn.execute("SELECT value FROM server_profession_records_v0370 WHERE record_key=?",(key,)).fetchone()
    if old is not None and int(old["value"] or 0) >= value:
        return False
    self.conn.execute(
        "INSERT INTO server_profession_records_v0370(record_key,value,holder_account_id,holder_name,text_value) VALUES(?,?,?,?,?) "
        "ON CONFLICT(record_key) DO UPDATE SET value=excluded.value,holder_account_id=excluded.holder_account_id,holder_name=excluded.holder_name,text_value=excluded.text_value,updated_at=CURRENT_TIMESTAMP",
        (key,value,account_id,str(holder_name or "Nieznany"),str(text_value or "")),
    )
    self.conn.commit(); return True

Database.v0370_record_max = _db_v0370_record_max

def _db_v0370_record_row(self,key):
    return self.conn.execute("SELECT * FROM server_profession_records_v0370 WHERE record_key=?",(str(key),)).fetchone()
Database.v0370_record_row = _db_v0370_record_row

def _db_v0370_hof_first(self,key,category,account_id,holder_name,detail="",achieved_at=None):
    if self.conn.execute("SELECT 1 FROM hall_of_fame_v0370 WHERE achievement_key=?",(str(key),)).fetchone():
        return False
    if achieved_at:
        self.conn.execute(
            "INSERT OR IGNORE INTO hall_of_fame_v0370(achievement_key,category,holder_account_id,holder_name,detail,achieved_at) VALUES(?,?,?,?,?,?)",
            (str(key),str(category),int(account_id or 0),str(holder_name or "Nieznany"),str(detail or ""),str(achieved_at)),
        )
    else:
        self.conn.execute(
            "INSERT OR IGNORE INTO hall_of_fame_v0370(achievement_key,category,holder_account_id,holder_name,detail) VALUES(?,?,?,?,?)",
            (str(key),str(category),int(account_id or 0),str(holder_name or "Nieznany"),str(detail or "")),
        )
    self.conn.commit()
    return self.conn.execute("SELECT changes() AS n").fetchone()["n"] > 0
Database.v0370_hof_first = _db_v0370_hof_first

# ----------------------------- Helpers ----------------------------------
def _v0370_character_name(db, account_id):
    row=db.conn.execute("SELECT name FROM characters WHERE account_id=?",(int(account_id),)).fetchone()
    return str(row["name"]) if row else "Nieznany"

def _v0370_gem_score(item_id):
    item=ITEMS.get(item_id,{})
    q=str(item.get("gem_quality") or "raw")
    try: qidx=GEM_QUALITY_ORDER.index(q)
    except Exception: qidx=0
    level=max(0,int(item.get("gem_level",0) or 0))
    return qidx*1_000_000 + level

def _v0370_craft_score(item_id):
    item=ITEMS.get(item_id,{})
    q=str(item.get("craft_quality_v03054") or "normal")
    try: qidx=CRAFT_QUALITY_ORDER_V03054.index(q)
    except Exception: qidx=0
    crit=1 if item.get("craft_critical_v03054") else 0
    lvl=max(0,int(item.get("required_character_level", item.get("required_mastery", item.get("generator_level",1))) or 1))
    return qidx*1_000_000 + crit*100_000 + lvl

def _v0370_seed_hall(db):
    # Existing level 600: historical order cannot be reconstructed perfectly from legacy saves.
    if not db.conn.execute("SELECT 1 FROM hall_of_fame_v0370 WHERE achievement_key='first_level_600'").fetchone():
        row=db.conn.execute("SELECT account_id,name,character_level FROM characters WHERE character_level>=600 ORDER BY account_id LIMIT 1").fetchone()
        if row: db.v0370_hof_first("first_level_600","Level",row["account_id"],row["name"],"Pierwszy zarejestrowany Level 600; stan zastany przy v0.37.0")
    if not db.conn.execute("SELECT 1 FROM hall_of_fame_v0370 WHERE achievement_key='first_mastery_600'").fetchone():
        row=db.conn.execute("SELECT cp.account_id,c.name,cp.class_name FROM class_progress cp JOIN characters c ON c.account_id=cp.account_id WHERE cp.level>=600 ORDER BY cp.account_id,cp.class_name LIMIT 1").fetchone()
        if row: db.v0370_hof_first("first_mastery_600","Biegłość",row["account_id"],row["name"],f"Biegłość 600: {row['class_name']}; stan zastany przy v0.37.0")
    # Per-class first registered 600.
    rows=db.conn.execute("SELECT cp.account_id,c.name,cp.class_name FROM class_progress cp JOIN characters c ON c.account_id=cp.account_id WHERE cp.level>=600 ORDER BY cp.account_id,cp.class_name").fetchall()
    for row in rows:
        db.v0370_hof_first(f"first_mastery_600:{row['class_name']}","Biegłość",row["account_id"],row["name"],f"Pierwszy zarejestrowany {row['class_name']} z Biegłością 600; stan zastany przy v0.37.0")
    # Existing UOSS superboss first kills can use Bestiary's first_killed_at timestamp.
    superboss_ids=[mid for mid,t in MOB_TEMPLATES.items() if t.get("uoss_superboss")]
    by_name={}
    for mid in superboss_ids:
        name=str(MOB_TEMPLATES[mid].get("uoss_superboss_name") or MOB_TEMPLATES[mid].get("name") or mid)
        by_name.setdefault(name,[]).append(mid)
    for name,ids in by_name.items():
        placeholders=",".join("?" for _ in ids)
        row=db.conn.execute(
            f"SELECT b.account_id,c.name,b.first_killed_at FROM bestiary_stats b JOIN characters c ON c.account_id=b.account_id WHERE b.mob_template_id IN ({placeholders}) AND b.kills>0 ORDER BY b.first_killed_at,b.account_id LIMIT 1",
            tuple(ids),
        ).fetchone()
        if row:
            db.v0370_hof_first(f"superboss:{normalize_lookup_text(name)}","Superboss",row["account_id"],row["name"],f"Pierwszy zabójca: {name}",row["first_killed_at"])

# -------------------------- Session records ------------------------------
_V0370_RECORDS_BEFORE = SessionSocialExpansionMixin.records_v03051

async def _v0370_records(self,args='',compact=False):
    raw=str(args or '').strip(); norm=normalize_lookup_text(raw)
    _v0370_seed_hall(self.server.db)
    if norm in ("hall","hof","hall of fame","halloffame","slawa","sława","galeria slawy","galeria sławy"):
        rows=self.server.db.conn.execute("SELECT * FROM hall_of_fame_v0370 ORDER BY achieved_at,achievement_key LIMIT 200").fetchall()
        await self.send("HALL OF FAME — PIERWSI NA SERWERZE")
        if not rows:
            await self.send("Hall of Fame jest jeszcze pusty."); return
        for row in rows:
            await self.send(f"{row['holder_name']}: {row['detail']}. Data: {row['achieved_at']}.")
        return
    if norm in ("profesje","professions","profession","rzemioslo","rzemiosło"):
        await self.send("PUBLICZNE REKORDY PROFESJI")
        labels=(
            ("largest_smelt","Największy przetop"),
            ("mining_session_ore","Najwięcej rudy w jednej sesji kopania"),
            ("rarest_gem","Najrzadszy klejnot"),
            ("best_craft","Najlepszy craft"),
        )
        for key,label in labels:
            row=self.server.db.v0370_record_row(key)
            if not row:
                await self.send(f"{label}: brak rekordu.")
            elif key in ("rarest_gem","best_craft"):
                await self.send(f"{label}: {row['text_value']} — {row['holder_name']}.")
            else:
                await self.send(f"{label}: {row['value']} — {row['holder_name']}." + (f" {row['text_value']}." if row['text_value'] else ""))
        return
    if raw:
        return await _V0370_RECORDS_BEFORE(self,args,compact)

    db=self.server.db
    await self.send("PUBLICZNE REKORDY SERWERA")
    row=db.conn.execute("SELECT name,character_level FROM characters ORDER BY character_level DESC,account_id ASC LIMIT 1").fetchone()
    await self.send(f"Najwyższy Level: {int(row['character_level'])} — {row['name']}." if row else "Najwyższy Level: brak.")
    row=db.conn.execute("SELECT b.account_id,c.name,MAX(b.floor) floor FROM boss_floor_clears b JOIN characters c ON c.account_id=b.account_id WHERE b.dungeon_kind='crypt' GROUP BY b.account_id ORDER BY floor DESC,b.account_id LIMIT 1").fetchone()
    await self.send(f"Najgłębsza Krypta: piętro {int(row['floor'])} — {row['name']}." if row else "Najgłębsza Krypta: brak rekordu.")
    row=db.conn.execute("SELECT l.account_id,c.name,l.value FROM lifetime_statistics l JOIN characters c ON c.account_id=l.account_id WHERE l.stat_key='boss_kills' ORDER BY l.value DESC,l.account_id LIMIT 1").fetchone()
    await self.send(f"Najwięcej bossów: {int(row['value'])} — {row['name']}." if row else "Najwięcej bossów: brak rekordu.")
    row=db.conn.execute("SELECT best_weight_g,weight_holder,fish_id FROM fish_global_records_v022 ORDER BY best_weight_g DESC,best_length_mm DESC LIMIT 1").fetchone()
    await self.send(f"Największa ryba: {format_fish_weight(row['best_weight_g'])}, {player_item_display_name_v0335(row['fish_id'])} — {row['weight_holder']}." if row else "Największa ryba: brak rekordu.")
    row=db.conn.execute("SELECT l.account_id,c.name,l.value FROM lifetime_statistics l JOIN characters c ON c.account_id=l.account_id WHERE l.stat_key='craft_actions' ORDER BY l.value DESC,l.account_id LIMIT 1").fetchone()
    await self.send(f"Najwięcej craftów: {int(row['value'])} — {row['name']}." if row else "Najwięcej craftów: brak rekordu.")
    row=db.v0370_record_row("largest_smelt")
    await self.send(f"Największy przetop: {int(row['value'])} przetopów naraz — {row['holder_name']}." if row else "Największy przetop: brak rekordu.")
    await self.send("Szczegóły: rekordy profesje; rekordy hall; rekordy <gracz>.")

SessionSocialExpansionMixin.records_v03051 = _v0370_records
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.

# --------------------------- Hall hooks ----------------------------------
_V0370_CHAR_XP_BEFORE = SessionCoreProgressionMixin.add_character_xp_with_event
def _v0370_char_xp(self,amount):
    result=_V0370_CHAR_XP_BEFORE(self,amount)
    if self.character and int(self.character.character_level)>=600:
        self.server.db.v0370_hof_first("first_level_600","Level",self.account_id,self.character.name,"Pierwszy gracz z Levelem 600")
    return result
SessionCoreProgressionMixin.add_character_xp_with_event = _v0370_char_xp

_V0370_CLASS_XP_BEFORE = SessionCoreProgressionMixin.grant_class_xp
async def _v0370_class_xp(self,total_xp):
    result=await _V0370_CLASS_XP_BEFORE(self,total_xp)
    if self.character:
        rows=self.server.db.conn.execute("SELECT class_name,level FROM class_progress WHERE account_id=? AND level>=600",(self.account_id,)).fetchall()
        for row in rows:
            self.server.db.v0370_hof_first("first_mastery_600","Biegłość",self.account_id,self.character.name,f"Pierwszy gracz z Biegłością 600: {row['class_name']}")
            self.server.db.v0370_hof_first(f"first_mastery_600:{row['class_name']}","Biegłość",self.account_id,self.character.name,f"Pierwszy {row['class_name']} z Biegłością 600")
    return result
SessionCoreProgressionMixin.grant_class_xp = _v0370_class_xp

_V0370_MOB_PROGRESS_BEFORE = SessionWorldProgressionMixin.record_mob_progress
async def _v0370_mob_progress(self,mob):
    result=await _V0370_MOB_PROGRESS_BEFORE(self,mob)
    if self.character:
        t=MOB_TEMPLATES.get(mob.template_id,{})
        if t.get("uoss_superboss"):
            name=str(t.get("uoss_superboss_name") or t.get("name") or mob.template_id)
            self.server.db.v0370_hof_first(f"superboss:{normalize_lookup_text(name)}","Superboss",self.account_id,self.character.name,f"Pierwszy zabójca: {name}")
    return result
SessionWorldProgressionMixin.record_mob_progress = _v0370_mob_progress

# ------------------------ Profession hooks -------------------------------
_V0370_GEM_DROP_BEFORE = SessionProfessionsStorageGuideMixin.mining_gem_drop
def _v0370_gem_drop(self,*args,**kwargs):
    result=_V0370_GEM_DROP_BEFORE(self,*args,**kwargs)
    self._v0370_last_gem_id=result
    return result
SessionProfessionsStorageGuideMixin.mining_gem_drop = _v0370_gem_drop

_V0370_SET_AUTO_MINING_BEFORE = SessionProfessionsStorageGuideMixin.set_auto_mining
async def _v0370_set_auto_mining(self,enabled):
    if enabled:
        self._v0370_mining_session_ore=0
    return await _V0370_SET_AUTO_MINING_BEFORE(self,enabled)
SessionProfessionsStorageGuideMixin.set_auto_mining = _v0370_set_auto_mining

_V0370_MINE_BEFORE = SessionAdminGatheringSalesMixin.mine
async def _v0370_mine(self,from_auto=False):
    before=self.server.db.lifetime_stat(self.account_id,"ore_mined") if self.account_id else 0
    self._v0370_last_gem_id=None
    result=await _V0370_MINE_BEFORE(self,from_auto=from_auto)
    after=self.server.db.lifetime_stat(self.account_id,"ore_mined") if self.account_id else before
    gained=max(0,int(after)-int(before))
    if gained and self.character:
        if from_auto:
            self._v0370_mining_session_ore=int(getattr(self,"_v0370_mining_session_ore",0) or 0)+gained
            session_total=self._v0370_mining_session_ore
        else:
            session_total=gained
        self.server.db.v0370_record_max("mining_session_ore",session_total,self.account_id,self.character.name,"ciągła sesja kopania")
    gem_id=getattr(self,"_v0370_last_gem_id",None)
    if gem_id and self.character:
        self.server.db.v0370_record_max("rarest_gem",_v0370_gem_score(gem_id),self.account_id,self.character.name,player_item_display_name_v0335(gem_id))
    return result
SessionAdminGatheringSalesMixin.mine = _v0370_mine

_V0370_PERFORM_RECIPE_BEFORE = SessionCraftingInventoryEquipmentMixin.perform_recipe
async def _v0370_perform_recipe(self,query,recipes,action_name):
    found=find_by_name(recipes,query)
    base_output=None; candidates=[]; before={}
    if found:
        _rid,rec=found; base_output=rec.get("output")
        if base_output and crafting_output_is_quality_equipment_v03054(base_output):
            candidates=[iid for iid,item in ITEMS.items() if item.get("crafted_base_id_v03054")==base_output]
            before={iid:self.server.db.item_qty(self.account_id,iid) for iid in candidates}
    result=await _V0370_PERFORM_RECIPE_BEFORE(self,query,recipes,action_name)
    if result and base_output and self.character:
        candidates=[iid for iid,item in ITEMS.items() if item.get("crafted_base_id_v03054")==base_output]
        gained=[iid for iid in candidates if self.server.db.item_qty(self.account_id,iid)>before.get(iid,0)]
        if gained:
            best=max(gained,key=_v0370_craft_score)
            item=ITEMS.get(best,{})
            label=player_item_display_name_v0335(best)
            self.server.db.v0370_record_max("best_craft",_v0370_craft_score(best),self.account_id,self.character.name,label)
    return result
SessionCraftingInventoryEquipmentMixin.perform_recipe = _v0370_perform_recipe

_V0370_SMELT_BEFORE = SessionCraftingExpansionV03114Mixin.smelt_item_v03114
async def _v0370_smelt(self,query):
    raw=str(query or '').strip(); norm=normalize_lookup_text(raw); count=0
    if norm in ("wszystko","all"):
        profession_level=int(self.server.db.profession(self.account_id,"Kowalstwo")["level"])
        old_tool_level=int(self.server.db.tool(self.account_id,"crafting")["level"])
        current_tool_tier=tool_tier(old_tool_level)
        recipe_ids=[tier["ingot"] for tier in BLACKSMITH_TIERS]+["recycled_steel_ingot"]+list(SALVAGE_SMELT_FALLBACK_V03113.values())
        for rid in dict.fromkeys(recipe_ids):
            rec=CRAFT_RECIPES.get(rid)
            if not rec: continue
            n=self.max_recipe_crafts_v03114(rec)
            req=max(1,int(rec.get("min_profession_level",rec.get("min_tool_level",1)) or 1))
            if n>0 and profession_level>=req and current_tool_tier>=required_tool_tier_for_level(req) and self.character.room_id in rec.get("stations",()): count+=n
    elif norm.startswith("max "):
        found=self.resolve_smelt_recipe(raw.split(maxsplit=1)[1]); count=self.max_recipe_crafts_v03114(found[1]) if found else 0
    else:
        count=1
    result=await _V0370_SMELT_BEFORE(self,query)
    if result and count>0 and self.character:
        self.server.db.v0370_record_max("largest_smelt",count,self.account_id,self.character.name,"jedna akcja przetapiania")
    return result
SessionCraftingExpansionV03114Mixin.smelt_item_v03114 = _v0370_smelt

# ------------------------ Boss-key cleanup -------------------------------
def _v0370_key_salvage_outputs(item):
    floor=max(1,int(item.get("boss_chest_floor",1) or 1))
    dust=max(1,min(8,1+floor//100))
    essence=1 if floor>=200 else 0
    return dust,essence

_V0370_SALVAGE_BEFORE = SessionCraftingExpansionV03114Mixin.salvage_equipment_v0925
async def _v0370_salvage(self,args=""):
    raw=str(args or '').strip(); norm=normalize_lookup_text(raw)
    owned=[]
    for row in self.server.db.inventory(self.account_id):
        iid=str(row["item_id"]); item=ITEMS.get(iid,{})
        if item.get("boss_chest_key") and int(row["quantity"] or 0)>0:
            owned.append((iid,item,int(row["quantity"] or 0)))
    if norm in ("klucze","keys","klucze bossow","klucze bossów"):
        if not owned:
            await self.send("Nie masz nadmiarowych kluczy bossowych do rozłożenia."); return False
        total_keys=total_dust=total_ess=0
        for iid,item,qty in owned:
            if not self.server.db.remove_item(self.account_id,iid,qty): continue
            dust,ess=_v0370_key_salvage_outputs(item)
            self.server.db.add_storage_item(self.account_id,"craftbox","rune_dust",dust*qty); total_dust+=dust*qty
            if ess:
                self.server.db.add_storage_item(self.account_id,"craftbox","reforge_essence",ess*qty); total_ess+=ess*qty
            total_keys+=qty
        await self.send(f"ROZŁÓŻ KLUCZE: rozłożono {total_keys} kluczy bossowych. Pył Runiczny x{total_dust}" + (f", Esencja Przekucia x{total_ess}." if total_ess else "."))
        return total_keys>0
    if raw and norm not in ("wszystko","all","everything"):
        pool={iid:item for iid,item,_qty in owned}
        found=find_by_name(pool,raw)
        if found:
            iid,item=found
            if not self.server.db.remove_item(self.account_id,iid,1):
                await self.send("Nie udało się pobrać klucza do Salvage."); return False
            dust,ess=_v0370_key_salvage_outputs(item)
            self.server.db.add_storage_item(self.account_id,"craftbox","rune_dust",dust)
            if ess: self.server.db.add_storage_item(self.account_id,"craftbox","reforge_essence",ess)
            await self.send(f"SALVAGE KLUCZA: {item['name']} -> Pył Runiczny x{dust}" + (f", Esencja Przekucia x{ess}." if ess else "."))
            return True
    return await _V0370_SALVAGE_BEFORE(self,args)
SessionCraftingExpansionV03114Mixin.salvage_equipment_v0925 = _v0370_salvage

for _iid,_item in ITEMS.items():
    if _item.get("boss_chest_key"):
        _item["desc"] = str(_item.get("desc","")).rstrip() + " Po otwarciu skrzyni klucz jest zużywany; nadmiarowy klucz można rozłożyć komendą rozłóż <nazwa klucza> albo rozłóż klucze."
        _item["salvageable_key_v0370"] = True

HELP_TOPICS["rekordy_serwera"] = [
    "rekordy — publiczne rekordy całego serwera: najwyższy Level, najgłębsza Krypta, najwięcej bossów, największa ryba, najwięcej craftów i największy przetop.",
    "rekordy profesje — największy przetop, najwięcej rudy w jednej ciągłej sesji kopania, najrzadszy klejnot i najlepszy craft.",
    "rekordy hall — Hall of Fame: pierwsi gracze z Level 600, Biegłością 600 i pierwsi zabójcy konkretnych Superbossów.",
    "rekordy <gracz> — zachowuje wcześniejszy widok osobistych rekordów wskazanej postaci.",
]
HELP_TOPIC_ALIASES.update({"rekordy":"rekordy_serwera","records":"rekordy_serwera","halloffame":"rekordy_serwera","hall of fame":"rekordy_serwera"})
HELP_TOPICS.setdefault("salvage",[]).append("Klucze bossowe są zużywane przy otwarciu skrzyni. Nadmiarowe klucze można rozłożyć pojedynczo lub przez `rozłóż klucze`; `salvage wszystko` nadal ich automatycznie nie niszczy.")

# ----------------------------- Audit ------------------------------------
def public_records_audit_v0370():
    errors=[]
    if COMMAND_ALIASES.get("rekordy")!="records": errors.append("missing rekordy alias")
    keys=[iid for iid,item in ITEMS.items() if item.get("boss_chest_key")]
    if not keys: errors.append("no boss chest keys registered")
    if any(not ITEMS[i].get("salvageable_key_v0370") for i in keys): errors.append("boss key not salvageable")
    if not hasattr(SessionSocialExpansionMixin,"records_v03051"): errors.append("records command missing")
    if not hasattr(Database,"v0370_record_max"): errors.append("records database API missing")
    return {"version":V0370_VERSION,"boss_keys":len(keys),"error_count":len(errors),"errors":errors}

PUBLIC_RECORDS_AUDIT_V0370=public_records_audit_v0370()
if PUBLIC_RECORDS_AUDIT_V0370["error_count"]:
    raise RuntimeError("Public Records Audit v0.37.0 failed: "+"; ".join(PUBLIC_RECORDS_AUDIT_V0370["errors"]))

LATEST_CHANGES_TITLE = "Soulbound v0.37.0 - Public Records + Hall of Fame"
LATEST_CHANGES = [
    "Dodano publiczne rekordy serwera: Level, Krypta, bossowie, największa ryba, crafty i największy przetop.",
    "Dodano Hall of Fame oraz publiczne rekordy profesji.",
    "Klucze bossowe nadal są zużywane przy skrzyni, a nadmiarowe można bezpiecznie rozłożyć pojedynczo lub przez rozłóż klucze.",
]
