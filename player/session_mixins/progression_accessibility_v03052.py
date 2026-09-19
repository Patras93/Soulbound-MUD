# -*- coding: utf-8 -*-
"""Soulbound v0.30.52 progression, rankings, housing, recap and accessibility expansion."""
import json, math, time

class SessionProgressionAccessibilityV03052Mixin:
    def _pct52(self,a,b):
        return int(round(100.0*max(0,int(a))/max(1,int(b))))

    async def collection_codex_v03052(self,args=''):
        q=normalize_lookup_text(args or '')
        db=self.server.db; aid=self.account_id
        fish=set(COLLECTION_CATALOGS.get('fish',{})); ores=set(COLLECTION_CATALOGS.get('minerals',{})); bosses=set(COLLECTION_CATALOGS.get('bosses',{})); rare=set(COLLECTION_CATALOGS.get('rare',{}))
        fish_seen=db.collection_entry_ids(aid,'fish'); ore_seen=db.collection_entry_ids(aid,'minerals'); boss_seen=db.collection_entry_ids(aid,'bosses'); rare_seen=db.collection_entry_ids(aid,'rare')
        await self.v0260_sync_museum()
        set_catalog=set(V0260_MUSEUM_CATALOGS.get('sets',()))
        set_seen=self.v0260_museum_found_ids('sets')
        secret_catalog=set(V0260_MUSEUM_CATALOGS.get('secrets',()))
        secrets=self.v0260_museum_found_ids('secrets')
        categories=[('Ryby',len(fish_seen&fish),len(fish)),('Rudy',len(ore_seen&ores),len(ores)),('Sety',len(set_seen&set_catalog),len(set_catalog)),('Bossowie',len(boss_seen&bosses),len(bosses)),('Rare moby',len(rare_seen&rare),len(rare)),('Sekrety',len(secrets&secret_catalog),len(secret_catalog))]
        await self.send('COLLECTION CODEX 2.0 — PODSUMOWANIE')
        for name,c,t in categories: await self.send(f'{name}: {c} z {t}, {self._pct52(c,t)}%.')
        if q in ('braki','missing','brakujace','brakujące'):
            miss_f=[ITEMS.get(x,{}).get('name',x) for x in sorted(fish-fish_seen,key=str)][:30]
            miss_o=[ITEMS.get(x,{}).get('name',x) for x in sorted(ores-ore_seen,key=str)][:30]
            miss_b=[MOB_TEMPLATES.get(x,{}).get('name',x) for x in sorted(bosses-boss_seen,key=str)][:30]
            await self.send('Brakujące ryby: '+(', '.join(miss_f) if miss_f else 'brak')+'.')
            await self.send('Brakujące rudy: '+(', '.join(miss_o) if miss_o else 'brak')+'.')
            await self.send('Brakujący bossowie: '+(', '.join(miss_b) if miss_b else 'brak')+'.')

    async def completion_v03052(self):
        db=self.server.db; aid=self.account_id
        discovered=db.discovered_room_ids(aid); world_total=len(ROOMS); world=len(discovered.intersection(ROOMS.keys()))
        prof_rows=db.conn.execute("SELECT level FROM professions WHERE account_id=?",(aid,)).fetchall()
        prof_score=sum(min(400,int(r['level'] or 1)) for r in prof_rows); prof_total=max(1,len(prof_rows)*400)
        bosses=set(self.codex_boss_ids()); br=db.conn.execute("SELECT mob_template_id FROM bestiary_stats WHERE account_id=? AND kills>0",(aid,)).fetchall(); boss_score=len({str(r['mob_template_id']) for r in br}&bosses)
        coll_c=coll_t=0
        for cat,catalog in COLLECTION_CATALOGS.items():
            found=db.collection_entry_ids(aid,cat); coll_c+=len(set(catalog)&found); coll_t+=len(catalog)
        parts=[('Świat',world,world_total),('Profesje',prof_score,prof_total),('Bossowie',boss_score,len(bosses)),('Kolekcje',coll_c,coll_t)]
        vals=[]
        await self.send('COMPLETION % 2.0')
        for n,c,t in parts:
            p=self._pct52(c,t); vals.append(p); await self.send(f'{n}: {p}% ({c}/{t}).')
        await self.send(f'Cała gra: {int(round(sum(vals)/len(vals)))}%.')

    async def leaderboards_v03052(self,args=''):
        q=normalize_lookup_text(args or '')
        db=self.server.db
        async def rows(title,sql,params=()):
            rr=db.conn.execute(sql,params).fetchall(); await self.send(title+':')
            if not rr: await self.send('Brak wyników.'); return
            for i,r in enumerate(rr,1): await self.send(f"{i}. {r['name']} — {r['score']}.")
        if q in ('mentor','mentorzy'):
            await rows('Ranking mentorów',"SELECT c.name name, COALESCE(SUM(mp.activity_points),0) score FROM mentor_progress_v03051 mp JOIN characters c ON c.account_id=mp.mentor_account_id GROUP BY mp.mentor_account_id,c.name ORDER BY score DESC,c.name COLLATE NOCASE LIMIT 20")
            return
        if q in ('profesje','profession','professions'):
            await rows('Ranking profesji',"SELECT c.name name, SUM(p.level) score FROM professions p JOIN characters c ON c.account_id=p.account_id GROUP BY p.account_id,c.name ORDER BY score DESC,c.name COLLATE NOCASE LIMIT 20")
            return
        if q in ('bossowie','bosses'):
            await rows('Ranking bossów',"SELECT c.name name, COUNT(DISTINCT b.mob_template_id) score FROM bestiary_stats b JOIN characters c ON c.account_id=b.account_id WHERE b.kills>0 GROUP BY b.account_id,c.name ORDER BY score DESC,c.name COLLATE NOCASE LIMIT 20")
            return
        if q in ('kolekcje','collection'):
            await rows('Ranking kolekcji',"SELECT c.name name, COUNT(cc.entry_id) score FROM collection_codex cc JOIN characters c ON c.account_id=cc.account_id GROUP BY cc.account_id,c.name ORDER BY score DESC,c.name COLLATE NOCASE LIMIT 20")
            return
        if q in ('gildie','guilds'):
            await rows('Ranking gildii',"SELECT pc.name name, COALESCE(SUM(CASE WHEN pcm.metric IN ('contracts_completed','guild_boss_kills','hall_upgrades') THEN pcm.value ELSE 0 END),0) score FROM player_clans pc LEFT JOIN player_clan_metrics pcm ON pcm.clan_id=pc.id GROUP BY pc.id,pc.name ORDER BY score DESC,pc.name COLLATE NOCASE LIMIT 20")
            return
        if q in ('rekordy','records'):
            await rows('Ranking największego krytyka',"SELECT c.name name, pr.value score FROM player_records_v03051 pr JOIN characters c ON c.account_id=pr.account_id WHERE pr.record_key='biggest_crit' ORDER BY score DESC,c.name COLLATE NOCASE LIMIT 20")
            return
        await self.send('LEADERBOARDS 2.0: leaderboards profesje, bossowie, kolekcje, rekordy, gildie, mentorzy. Klasyczne rankingi lochów nadal działają przez leaderboards krypta/astral itd.')

    async def mentor_v03052(self,args=''):
        raw=str(args or '').strip(); q=normalize_lookup_text(raw)
        if q in ('ranking','rank','mentorzy'): return await self.leaderboards_v03052('mentorzy')
        if q in ('graduation','graduate','absolutorium','ukoncz','ukończ'):
            row=self.mentor_link_v03050()
            if not row: await self.send('Nie masz aktywnej relacji mentor-uczeń.'); return
            mid,sid=int(row['mentor_account_id']),int(row['student_account_id'])
            pr=self.server.db.conn.execute("SELECT activity_points FROM mentor_progress_v03051 WHERE mentor_account_id=? AND student_account_id=?",(mid,sid)).fetchone(); pts=int(pr['activity_points'] if pr else 0)
            sm,ss=self.mentor_progress_v03050(sid)
            if pts<100 or sm<50 or ss<50:
                await self.send(f'Graduation wymaga 100 wspólnych aktywności oraz ucznia z Biegłością 50 i Soul Level 50. Teraz: aktywności {pts}, Biegłość {sm}, Soul Level {ss}.'); return
            conn=self.server.db.conn
            conn.execute("INSERT OR IGNORE INTO mentor_graduation_v03052(mentor_account_id,student_account_id,activity_points) VALUES(?,?,?)",(mid,sid,pts))
            conn.execute("DELETE FROM mentor_links_v03050 WHERE mentor_account_id=? AND student_account_id=?",(mid,sid)); conn.commit()
            reward=10000
            for aid in (mid,sid):
                w=int(self.server.db.shared_wallet_for_character(aid)[0]); self.server.db.set_shared_wallet_for_character(aid,min(CURRENCY_SQLITE_SAFE_TOTAL,w+reward),0,0,commit=False)
            conn.commit(); await self.send(f'Apprentice Graduation zakończone. Mentor i uczeń dostają po {currency_reading_text(reward,0,0)}.')
            return
        await self.handle_mentor_v03050(args)

    async def housing_v03052(self,args=''):
        raw=str(args or '').strip(); parts=raw.split(maxsplit=2); act=normalize_lookup_text(parts[0]) if parts else ''
        conn=self.server.db.conn; aid=self.account_id
        if act in ('rooms','pokoje'):
            rows=conn.execute("SELECT room_key,room_name,decor,station FROM housing_rooms_v03052 WHERE account_id=? ORDER BY room_key",(aid,)).fetchall()
            await self.send('HOUSING 2.0 — POKOJE:')
            if not rows: await self.send('Brak dodatkowych pokoi. Użyj: house room add <nazwa>.'); return
            for r in rows: await self.send(f"{r['room_key']}: {r['room_name']}. Stacja: {r['station'] or 'brak'}. Dekoracja: {r['decor'] or 'brak'}.")
            return
        if act=='room' and len(parts)>1:
            sub=parts[1].split(maxsplit=1); op=normalize_lookup_text(sub[0]); tail=sub[1] if len(sub)>1 else ''
            if op in ('add','dodaj'):
                count=conn.execute("SELECT COUNT(*) n FROM housing_rooms_v03052 WHERE account_id=?",(aid,)).fetchone()['n']; base=conn.execute("SELECT level FROM player_housing_v03051 WHERE account_id=?",(aid,)).fetchone(); lim=max(1,int(base['level'] if base else 1))
                if count>=lim: await self.send(f'Limit dodatkowych pokoi: {lim}. Ulepsz dom.'); return
                name=tail.strip()[:60] or f'Pokój {count+1}'; key=f'room{count+1}'; conn.execute("INSERT INTO housing_rooms_v03052(account_id,room_key,room_name) VALUES(?,?,?)",(aid,key,name)); conn.commit(); await self.send(f'Dodano pokój: {name}.'); return
            await self.send('Użycie: house room add <nazwa>.'); return
        if act in ('station','stacja') and len(parts)>1:
            seg=parts[1].split(maxsplit=1)
            if len(seg)<2: await self.send('Użycie: house station <roomN> <forge|alchemy|cooking|jewelcrafting>.'); return
            key,station=seg[0],normalize_lookup_text(seg[1]); allowed={'forge','alchemy','cooking','jewelcrafting'}
            if station not in allowed: await self.send('Stacje: forge, alchemy, cooking, jewelcrafting.'); return
            cur=conn.execute("UPDATE housing_rooms_v03052 SET station=? WHERE account_id=? AND room_key=?",(station,aid,key)); conn.commit()
            await self.send('Stacja ustawiona.' if cur.rowcount else 'Nie ma takiego pokoju.'); return
        if act in ('gallery','gabloty','trophies2'):
            rows=conn.execute("SELECT display_name FROM housing_trophies_v03052 WHERE account_id=? ORDER BY display_name",(aid,)).fetchall(); await self.send('GABLOTY: '+(', '.join(r['display_name'] for r in rows) if rows else 'puste')+'.'); return
        await self.housing_v03051(args)

    async def transport_v03052(self,args=''):
        q=normalize_lookup_text(args or '')
        # Existing world transport remains authoritative; this adds named categories/help.
        if not q:
            await self.send('TRANSPORT 2.0: łodzie łączą porty i wybrzeża; wozy — miasta/osady; windy — kopalnie; portale — odblokowane punkty lochów. Następnie wybierz cel przez transport <cel>.')
        return await self.handle_transport_v018(args)

    async def death_recap_v03052(self):
        r=self.server.db.conn.execute("SELECT killer,room_id,damage_taken,duration_ms,created_at FROM death_recaps_v03052 WHERE account_id=? ORDER BY id DESC LIMIT 1",(self.account_id,)).fetchone()
        if not r: await self.send('Brak zapisanego Death Recap.'); return
        room=ROOMS.get(r['room_id'],{}).get('name',r['room_id']); await self.send(f"DEATH RECAP: pokonał cię {r['killer']}; miejsce {room}; otrzymane obrażenia {r['damage_taken']}; czas walki {int(r['duration_ms'])/1000:.1f} s.")

    async def combat_recap_v03052(self):
        r=self.server.db.conn.execute("SELECT * FROM combat_recaps_v03052 WHERE account_id=? ORDER BY id DESC LIMIT 1",(self.account_id,)).fetchone()
        if not r: await self.send('Brak zapisanego Combat Recap.'); return
        await self.send(f"COMBAT RECAP: {r['opponent']}; wynik {r['result'] or 'brak'}; czas {int(r['duration_ms'])/1000:.1f} s; damage {r['damage_dealt']}; otrzymane {r['damage_taken']}; leczenie {r['healing']}; crit {r['crits']}; skille {r['skills_used']}.")

    async def loot_history_v03052(self,args=''):
        raw=str(args or '').strip(); q=normalize_lookup_text(raw); rows=self.server.db.conn.execute("SELECT item_name,rarity,source,zone,created_at FROM drop_history WHERE account_id=? ORDER BY id DESC LIMIT 100",(self.account_id,)).fetchall()
        if q:
            rows=[r for r in rows if q in normalize_lookup_text(' '.join(str(r[k] or '') for k in ('item_name','rarity','source','zone')))]
        await self.send(f'LOOT HISTORY 2.0: wyników {len(rows)}.')
        for i,r in enumerate(rows[:30],1): await self.send(f"{i}. {r['item_name']}; {r['rarity']}; {r['source'] or 'źródło nieznane'}; {r['zone'] or 'strefa nieznana'}.")
        if not rows: await self.send('Brak pasujących dropów.')

    async def accessibility_v03052(self,args=''):
        raw=str(args or '').strip(); parts=raw.split(); conn=self.server.db.conn; aid=self.account_id
        conn.execute("INSERT OR IGNORE INTO accessibility_presets_v03052(account_id) VALUES(?)",(aid,)); conn.commit()
        if not parts:
            r=conn.execute("SELECT * FROM accessibility_presets_v03052 WHERE account_id=?",(aid,)).fetchone(); await self.send(f"NVDA presets: combat {r['combat']}, social {r['social']}, system {r['system']}. Użycie: nvda <combat|social|system|all> <concise|normal|full>."); return
        if len(parts)!=2 or normalize_lookup_text(parts[0]) not in ('combat','social','system','all') or normalize_lookup_text(parts[1]) not in ('concise','normal','full'):
            await self.send('Użycie: nvda <combat|social|system|all> <concise|normal|full>.'); return
        area=normalize_lookup_text(parts[0]); mode=normalize_lookup_text(parts[1]); cols=('combat','social','system') if area=='all' else (area,)
        for col in cols: conn.execute(f"UPDATE accessibility_presets_v03052 SET {col}=? WHERE account_id=?",(mode,aid))
        conn.commit(); await self.send(f'NVDA preset ustawiony: {area} = {mode}.')
