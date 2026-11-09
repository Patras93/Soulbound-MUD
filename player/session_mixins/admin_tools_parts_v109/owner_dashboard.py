# -*- coding: utf-8 -*-
"""Admin Tools 2.0: identyczny dispatcher właściciela, bez zmian uprawnień.

Historyczne globalne symbole importujemy z ich oryginalnych źródeł.
Brak zmian w SQL, logach admina, uprawnieniach, potwierdzaniu i NVDA.
"""
from __future__ import annotations
import os
import time
import sqlite3
from pathlib import Path
from contextlib import closing
from datetime import datetime, timezone
from data.npcs import NPCS
from data.mobs import MOB_TEMPLATES
from core.classes_skills import ROOMS

class AdminOwnerDashboardV109Mixin:
    async def admin_tools_v1224(self, raw):
        """NVDA-first owner controls. Returns False for older admin commands."""
        parts = str(raw or "").strip().split()
        if not parts:
            return False
        action = parts[0].casefold()
        if action not in {
            "pomoc", "online", "gracz", "przywolaj", "ulecz", "wskrzes", "odbuguj",
            "wyrzuc", "serwer", "blad", "log", "komendy", "backup", "baza",
            "oglos", "historia", "lokacja", "moby", "boss", "npc", "profesje",
            "zamowienia", "prace", "najemnicy", "questy", "eq", "napraw", "goto"
        }:
            return False
        if action == "goto" and (len(parts) < 2 or parts[1].casefold() != "gracz"):
            return False
        db = self.server.db
        login = db.account_name(self.master_account_id)
        conn = db.conn
        def audit(cmd, target=""):
            db.record_admin_action_v1224(login, cmd, target)
        def target_row(nick):
            return conn.execute("SELECT account_id,name,room_id,character_level,race,class_name "
                                "FROM characters WHERE name=? COLLATE NOCASE", (nick,)).fetchone()
        def session_for(nick):
            return self.server.find_character_session(nick)
        def check_confirm():
            return len(parts) >= 2 and parts[-1].casefold() == "potwierdzam"
        def room_name(rid):
            return ROOMS.get(rid, {}).get("name", str(rid))
        if action == "pomoc":
            category = parts[1].casefold() if len(parts)>1 else ""
            menus = {
                "gracze": "admin god on/off/status; admin cios grom/nawalnica/wyrok [cel]; admin online; gracz NICK; goto gracz NICK; przywolaj NICK POTWIERDZAM; ulecz NICK POTWIERDZAM; wskrzes NICK POTWIERDZAM; odbuguj NICK POTWIERDZAM; wyrzuc NICK POTWIERDZAM",
                "serwer": "admin serwer; admin blad lista 20; admin blad diagnoza NUMER; admin blad questy NICK; admin blad napraw NUMER NICK QUEST_ID POTWIERDZAM; admin blad SB-XXXXXXXX; admin blad naprawiony SB-XXXXXXXX; admin blad otworz SB-XXXXXXXX; admin log ostatnie 20; admin log aktywne; admin log naprawione; admin log podglad; admin log wyczysc naprawione POTWIERDZAM; wyczysc naprawione POTWIERDZAM; komendy wolne; backup; baza sprawdz; oglos TEKST; historia 20",
                "swiat": "admin lokacja ID; npc NAZWA; moby ID; boss NAZWA",
                "postacie": "admin profesje NICK; zamowienia NICK; prace NICK; najemnicy NICK; questy NICK; eq NICK; napraw postac NICK (diagnoza) / ... POTWIERDZAM (tylko błędna lokacja)",
            }
            if category in menus:
                await self.send("ADMIN " + category.upper() + ": " + menus[category] + ".")
            else:
                await self.send("ADMIN TOOLS 2.0: admin pomoc gracze / serwer / swiat / postacie. Stare polecenia: admin help.")
            return True
        if action == "online":
            clients = sorted((s for s in self.server.sessions if not s.closed and s.character),
                             key=lambda s:s.character.name.casefold())
            await self.send(f"ONLINE: {len(clients)} postaci, {len(self.server.sessions)} połączeń.")
            for s in clients[:100]:
                await self.send(f"{s.character.name}: poziom {s.character.character_level}, {room_name(s.character.room_id)}.")
            return True
        if action == "serwer":
            online = sum(bool(s.character) for s in self.server.sessions if not s.closed)
            mobs = len(self.server.world.mobs)
            size = os.path.getsize(db.path) if os.path.isfile(db.path) else 0
            uptime = int(time.time() - getattr(self.server,"start_time_v1224",time.time()))
            ram_kib = 0
            status_file = Path("/proc/self/status")
            if status_file.exists():
                for line in status_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("VmRSS:"):
                        ram_kib = int(line.split()[1])
                        break
            ram_text = f"{ram_kib // 1024} MiB" if ram_kib else "niedostępne"
            await self.send(f"SERWER: online {online}; połączeń {len(self.server.sessions)}; lokacji {len(ROOMS)}; mobów {mobs}; czas działania {uptime}s; baza {size//1024} KiB; RAM {ram_text}; CPU procesu {time.process_time():.1f}s.")
            return True
        if action == "blad":
            from systems.admin_error_quest_v36001 import handle_error_quest_command
            if await handle_error_quest_command(self, parts):
                return True
            import re
            error_id = parts[-1].upper() if len(parts) >= 2 else ""
            if len(parts) not in (2, 3) or not re.fullmatch(r"SB-[0-9A-F]{8}", error_id):
                await self.send("Użycie: admin blad SB-XXXXXXXX / admin blad naprawiony SB-XXXXXXXX / admin blad otworz SB-XXXXXXXX.")
                return True
            if len(parts) == 3:
                status_action = parts[1].casefold()
                if status_action not in ("naprawiony", "otworz", "otwórz"):
                    await self.send("Użycie: admin blad naprawiony SB-XXXXXXXX / admin blad otworz SB-XXXXXXXX.")
                    return True
                resolved = status_action == "naprawiony"
                if db.set_admin_error_resolved_v1371(error_id, login, resolved):
                    await self.send(f"ADMIN: {error_id} — {'oznaczony jako naprawiony' if resolved else 'ponownie otwarty'}. Wpis pozostaje w rejestrze do ręcznego czyszczenia.")
                else:
                    await self.send("Nie znaleziono podanego identyfikatora błędu.")
                return True
            row = conn.execute("SELECT * FROM admin_errors_v1224 WHERE id=?", (error_id,)).fetchone()
            if row is None:
                await self.send("Nie znaleziono w wewnętrznym rejestrze. Starsze błędy sprzed v1.22.4 są tylko w logach Railway.")
            else:
                status = ("naprawiony przez " + row['resolved_by'] + " dnia " + row['resolved_at']) if row['resolved_at'] else "aktywny / nieoznaczony"
                await self.send(f"{row['id']}: {row['created_at']}; {row['exception']}; {row['file']}:{row['line']}; moduł {row['subsystem']}; obsługa {row['handler']}; status {status}. Szczegóły traceback w logach serwera.")
            return True
        if action == "log":
            sub = parts[1].casefold() if len(parts) >= 2 else ""
            if sub in ("wyczysc", "wyczyść", "czysc", "czyść"):
                if len(parts) != 4 or parts[2].casefold() != "naprawione" or parts[3].casefold() != "potwierdzam":
                    await self.send("Użycie: admin log wyczysc naprawione POTWIERDZAM. Usuwa WYŁĄCZNIE ręcznie oznaczone błędy z wewnętrznej bazy. Zalecane: admin backup.")
                    return True
                removed = db.purge_resolved_admin_errors_v1371(login)
                await self.send(f"ADMIN: wyczyszczono {removed} naprawionych zgłoszeń SB. Aktywne błędy pozostają. Operację zapisano w admin historia. Logi Railway nie są zmieniane.")
                return True
            if sub in ("podglad", "podgląd"):
                active = conn.execute("SELECT COUNT(*) FROM admin_errors_v1224 WHERE resolved_at = ''").fetchone()[0]
                fixed = conn.execute("SELECT COUNT(*) FROM admin_errors_v1224 WHERE resolved_at != ''").fetchone()[0]
                await self.send(f"REJESTR BŁĘDÓW: aktywne lub nieoznaczone {active}; ręcznie naprawione {fixed}. Do wyczyszczenia: {fixed}. Niczego nie usunięto.")
                return True
            if sub not in ("ostatnie", "last", "aktywne", "naprawione"):
                await self.send("Użycie: admin log ostatnie 20 / aktywne 20 / naprawione 20 / podglad / wyczysc naprawione POTWIERDZAM.")
                return True
            if len(parts) > 3 or (len(parts) == 3 and not parts[2].isdigit()):
                await self.send("Podaj liczbę wpisów od 1 do 50, np. admin log aktywne 20.")
                return True
            limit = min(50, max(1, int(parts[2]) if len(parts) == 3 else 20))
            condition = {"aktywne": "WHERE resolved_at = ''", "naprawione": "WHERE resolved_at != ''"}.get(sub, "")
            rows = conn.execute(f"SELECT * FROM admin_errors_v1224 {condition} ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,)).fetchall()
            await self.send(f"BŁĘDY {sub.upper()}: {len(rows)} wpisów.")
            for row in rows:
                status = "NAPRAWIONY" if row['resolved_at'] else "AKTYWNY"
                await self.send(f"{row['id']}: {row['exception']}, {row['file']}:{row['line']}; {status}.")
            return True
        if action == "komendy":
            if len(parts)<2 or parts[1].casefold() not in ("wolne","slow"):
                await self.send("Użycie: admin komendy wolne.")
                return True
            rows = conn.execute("SELECT command,COUNT(*) n,MAX(duration_ms) max_ms FROM admin_slow_commands_v1224 GROUP BY command ORDER BY max_ms DESC LIMIT 20").fetchall()
            await self.send(f"WOLNE KOMENDY: {len(rows)} typów (ostatnie 100 wolnych pomiarów, także z poprzednich wersji; od v102.00.9 bez celowego oczekiwania craft/menu quit).")
            for row in rows:
                await self.send(f"{row['command']}: {row['n']} razy; najwolniej {row['max_ms']} ms.")
            return True
        if action == "baza":
            if len(parts)<2 or parts[1].casefold() != "sprawdz":
                await self.send("Użycie: admin baza sprawdz.")
                return True
            row = conn.execute("PRAGMA quick_check").fetchone()
            await self.send(f"Baza danych: {'OK' if row[0]=='ok' else 'WYKRYTO PROBLEM: ' + str(row[0])[:150]}.")
            audit("baza_sprawdz")
            return True
        if action == "backup":
            folder = Path(db.path).resolve().parent / "backups"
            folder.mkdir(parents=True,exist_ok=True,mode=0o700)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            destination = folder / ("soulbound_backup_" + stamp + ".db")
            with closing(sqlite3.connect(str(destination))) as backup_db, backup_db:
                # Consistent SQLite online backup; works with WAL mode.
                db.conn.backup(backup_db)
                result = backup_db.execute("PRAGMA quick_check").fetchone()[0]
            if result != "ok":
                destination.unlink(missing_ok=True)
                await self.send("Kopia nie przeszła kontroli integralności.")
                return True
            os.chmod(destination,0o600)
            old_backups = sorted(folder.glob("soulbound_backup_*.db"), reverse=True)
            for stale in old_backups[10:]:
                stale.unlink(missing_ok=True)
            audit("backup",destination.name)
            await self.send(f"BACKUP OK: {destination.name}. Folder: {folder}. Skopiuj go również poza serwer.")
            return True
        if action == "historia":
            limit = min(50,max(1,int(parts[1]) if len(parts)>1 and parts[1].isdigit() else 20))
            rows = conn.execute("SELECT created_at,admin_login,action,target FROM admin_actions_v1224 ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
            await self.send(f"HISTORIA ADMIN: {len(rows)} wpisów.")
            for row in rows:
                await self.send(f"{row['created_at']}: {row['admin_login']} {row['action']} {row['target']}.")
            return True
        if action == "oglos":
            announcement = " ".join(ch for ch in str(raw).partition(" ")[2].strip() if ch.isprintable())
            if not 1<=len(announcement)<=240:
                await self.send("Użycie: admin oglos TEKST (1-240 znaków).")
                return True
            audit("oglos", f"{len(announcement)} znaków")
            await self.server.broadcast_all(f"OGŁOSZENIE ADMINISTRATORA: {announcement}")
            return True
        if action == "npc":
            needle = " ".join(parts[1:]).casefold()
            matches=[(k,v) for k,v in NPCS.items() if needle and (needle in str(v.get('name','')).casefold() or needle==str(k).casefold())]
            await self.send(f"NPC: znaleziono {len(matches)}. Podaj nazwę lub identyfikator.")
            for key,npc in matches[:20]:
                await self.send(f"{npc.get('name',key)} ({key}): {room_name(npc.get('room','?'))}; pokój {npc.get('room','?')}.")
            return True
        if action == "lokacja":
            rid = " ".join(parts[1:]) or self.character.room_id
            if rid not in ROOMS:
                await self.send("Nie znaleziono lokacji (użyj ID pokoju).")
                return True
            room = ROOMS[rid]
            await self.send(f"LOKACJA: {room_name(rid)}; ID {rid}; strefa {room.get('zone','?')}; wyjścia {', '.join(sorted(room.get('exits',{}))) or 'brak'}. NPC {sum(n.get('room')==rid for n in NPCS.values())}; żywe moby {sum(m.room_id==rid and m.alive for m in self.server.world.mobs.values())}.")
            return True
        if action == "moby":
            rid = " ".join(parts[1:]) or self.character.room_id
            if rid not in ROOMS:
                await self.send("Nie znaleziono lokacji.")
                return True
            mobs=[m for m in self.server.world.mobs.values() if m.room_id==rid]
            await self.send(f"MOBY: {room_name(rid)}, {len(mobs)} wpisów.")
            for mob in mobs[:30]:
                await self.send(f"{MOB_TEMPLATES.get(mob.template_id,{}).get('name',mob.template_id)}: HP {mob.hp}; {'żywy' if mob.alive else 'pokonany'}; klucz {mob.key}.")
            return True
        if action == "boss":
            q = " ".join(parts[1:]).casefold()
            if not q:
                await self.send("Użycie: admin boss NAZWA.")
                return True
            matches=[m for m in self.server.world.mobs.values() if q in str(MOB_TEMPLATES.get(m.template_id,{}).get('name',m.template_id)).casefold()]
            await self.send(f"BOSS / POTWÓR: znaleziono {len(matches)} aktywnych instancji pasujących do nazwy.")
            for m in matches[:20]:
                await self.send(f"{MOB_TEMPLATES.get(m.template_id,{}).get('name',m.template_id)}: {room_name(m.room_id)}, HP {m.hp}, {'żywy' if m.alive else 'pokonany'}, respawn {max(0,int(m.respawn_at-time.time()))}s.")
            return True
        if action == "goto":
            if len(parts)<3:
                await self.send("Użycie: admin goto gracz NICK.")
                return True
            target = session_for(" ".join(parts[2:]))
            if not target:
                await self.send("Gracz nie jest online.")
                return True
            self.character.room_id=target.character.room_id
            db.save_character(self.character)
            audit("goto_gracz",target.character.name)
            await self.send(f"Przeniesiono do {room_name(self.character.room_id)}.")
            await self.look()
            return True
        if action == "gracz":
            row=target_row(" ".join(parts[1:]))
            if not row:
                await self.send("Nie znaleziono postaci o tej nazwie.")
                return True
            online = session_for(row['name'])
            await self.send(f"GRACZ: {row['name']}; poziom {row['character_level']}; {row['race']} / {row['class_name']}; {room_name(row['room_id'])}; {'online' if online else 'offline'}." +
                            (f" HP {online.current_hp}/{online.max_hp()}." if online else ""))
            return True
        if action in ("przywolaj","ulecz","wskrzes","odbuguj","wyrzuc"):
            nick = " ".join(parts[1:-1] if check_confirm() else parts[1:])
            target = session_for(nick)
            if not target:
                await self.send("Ta postać musi być online i mieć dokładną nazwę.")
                return True
            if not check_confirm():
                await self.send(f"Potwierdź: admin {action} {target.character.name} POTWIERDZAM.")
                return True
            if target is self and action in ("wyrzuc","przywolaj"):
                await self.send("Nie możesz wykonać tej operacji na sobie.")
                return True
            if target.is_admin() and target is not self:
                await self.send("Operacje na innym administratorze są zablokowane.")
                return True
            if action in ("przywolaj","odbuguj"):
                if (target.combat_mob_key or target.is_downed_v0371()
                        or any(bool(getattr(target, flag, False)) for flag in
                        ("auto_mining", "auto_fishing", "auto_woodcutting", "auto_herbalism", "resting"))
                        or target.guide_task_active() or target.smelt_task_active_v1124()):
                    await self.send("Gracz walczy albo ma aktywną pracę. Najpierw zakończ walkę, prowadzenie lub pracę.")
                    return True
                dest = self.character.room_id if action=="przywolaj" else "temple"
                if dest not in ROOMS:
                    await self.send("Brak bezpiecznej lokacji docelowej.")
                    return True
                target.character.room_id=dest
                db.save_character(target.character)
                await target.send(f"ADMIN: przeniesiono cię do {room_name(dest)}.")
            elif action in ("ulecz","wskrzes"):
                if action=="wskrzes" and target.current_hp>0 and not target.is_downed_v0371():
                    await self.send("Gracz nie potrzebuje wskrzeszenia.")
                    return True
                if action=="wskrzes":
                    target.clear_downed_v0371(cancel_task=True)
                    target.server.release_all_engagements_for_session(target)
                    target.combat_mob_key=None
                    await target.stop_realtime_combat()
                    target.skill_guard=0
                    target.skill_evade=False
                    target.skill_evade_lockout_until=0.0
                target.current_hp=target.max_hp()
                target.current_mana=target.max_mana()
                await target.send("ADMIN: przywrócono HP i Manę.")
            else:
                audit("wyrzuc",target.character.name)
                await target.send("ADMIN: sesja została rozłączona.")
                target.closed=True
                target.writer.close()
                await self.send("Gracz został rozłączony.")
                return True
            audit(action,target.character.name)
            await self.send(f"ADMIN: {action} zakończone dla {target.character.name}.")
            return True
        # Other-player diagnostics: read-only by default.
        if action in ("profesje","zamowienia","prace","najemnicy","questy","eq","napraw"):
            offset=2 if action=="napraw" else 1
            if action=="napraw" and (len(parts)<2 or parts[1].casefold()!="postac"):
                await self.send("Użycie: admin napraw postac NICK [POTWIERDZAM].")
                return True
            nick=" ".join(parts[offset:-1] if check_confirm() else parts[offset:])
            row=target_row(nick)
            if not row:
                await self.send("Nie znaleziono postaci.")
                return True
            cid=int(row['account_id'])
            if action=="napraw":
                if row['room_id'] in ROOMS:
                    await self.send("Diagnostyka: lokacja prawidłowa. Brak automatycznych zmian. Pozostałe problemy wymagają ręcznej diagnozy.")
                elif not check_confirm():
                    await self.send(f"Nieistniejąca lokacja {row['room_id']}. Aby przenieść postać do świątyni: admin napraw postac {row['name']} POTWIERDZAM.")
                elif session_for(row['name']):
                    await self.send("Postać musi być offline przed naprawą zapisu.")
                else:
                    conn.execute("UPDATE characters SET room_id='temple' WHERE account_id=?",(cid,))
                    conn.commit()
                    audit("napraw_lokacja",row['name'])
                    await self.send("Naprawiono wyłącznie identyfikator lokacji. Inne dane nietknięte.")
                return True
            if action=="profesje":
                prows=conn.execute("SELECT profession,level,xp FROM professions WHERE account_id=? ORDER BY profession",(cid,)).fetchall()
                await self.send(f"PROFESJE {row['name']}: {len(prows)}.")
                for entry in prows[:25]:
                    await self.send(f"{entry['profession']}: poziom {entry['level']}, EXP {entry['xp']}.")
            elif action=="zamowienia":
                order=db.crafting_order_v0600(cid)
                await self.send(f"ZAMÓWIENIA {row['name']}: " +
                                (f"{order['item_name']}, {order['progress']}/{order['needed']}" if order and order['needed'] else "brak aktywnego"))
            elif action=="najemnicy":
                active=db.mercenary_contracts(cid)
                await self.send(f"NAJEMNICY {row['name']}: {len(active)} aktywnych; " + ", ".join(x['role'] for x in active))
            elif action=="prace":
                live=session_for(row['name'])
                if live:
                    states=[name for name,flag in (("ryby",live.auto_fishing),("ruda",live.auto_mining),
                           ("drewno",live.auto_woodcutting),("zioła",live.auto_herbalism)) if flag]
                    await self.send("PRACE: " + (", ".join(states) if states else "brak aktywnych prac automatycznych") + ".")
                else:
                    await self.send("Postać offline; aktywności sesyjne nie działają.")
            elif action=="questy":
                quests=db.quest_rows(cid)
                await self.send(f"QUESTY {row['name']}: {len(quests)} zapisów; pokazuję do 15.")
                for q in quests[:15]:
                    await self.send(str(dict(q))[:180])
            elif action=="eq":
                entries=db.equipment(cid)
                await self.send(f"EQ {row['name']}: {len(entries)} slotów.")
                for entry in list(entries)[:25]:
                    await self.send(str(dict(entry))[:180])
            return True
        return False
