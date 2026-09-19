# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Social Suite 2.0 and player services."""

class SessionSocialExpansionMixin:
    def _social_target_id_v03051(self, name):
        return self.server.db.character_account_id_by_name_v0928(str(name or '').strip())

    def _social_name_v03051(self, aid):
        return self.server.db.character_name_by_account_v0928(int(aid)) or f"konto {aid}"

    def is_ignored_v03051(self, owner_id, other_id):
        return bool(self.server.db.conn.execute("SELECT 1 FROM social_ignores_v03051 WHERE account_id=? AND ignored_account_id=?",(int(owner_id),int(other_id))).fetchone())

    async def handle_ignore_v03051(self, args='', remove=False):
        raw=str(args or '').strip(); conn=self.server.db.conn
        if not raw:
            rows=conn.execute("SELECT ignored_account_id FROM social_ignores_v03051 WHERE account_id=? ORDER BY ignored_account_id",(self.account_id,)).fetchall()
            await self.send("IGNOROWANI: " + (", ".join(self._social_name_v03051(r['ignored_account_id']) for r in rows) if rows else "brak.")); return
        aid=self._social_target_id_v03051(raw)
        if aid is None: await self.send("Nie ma takiej postaci."); return
        if int(aid)==int(self.account_id): await self.send("Nie możesz ignorować samego siebie."); return
        if remove:
            conn.execute("DELETE FROM social_ignores_v03051 WHERE account_id=? AND ignored_account_id=?",(self.account_id,aid)); conn.commit(); await self.send(f"Przestajesz ignorować: {self._social_name_v03051(aid)}.")
        else:
            conn.execute("INSERT OR IGNORE INTO social_ignores_v03051(account_id,ignored_account_id) VALUES(?,?)",(self.account_id,aid)); conn.commit(); await self.send(f"Ignorujesz: {self._social_name_v03051(aid)}.")

    def channel_enabled_v03051(self, channel):
        row=self.server.db.conn.execute("SELECT enabled FROM social_channel_settings_v03051 WHERE account_id=? AND channel=?",(self.account_id,str(channel))).fetchone()
        return True if row is None else bool(row['enabled'])

    async def channel_broadcast_v03050(self, channel, message):
        channel=str(channel); raw=str(message or '').strip(); norm=normalize_lookup_text(raw)
        if norm in ('on','wlacz','włącz'):
            self.server.db.conn.execute("INSERT INTO social_channel_settings_v03051(account_id,channel,enabled) VALUES(?,?,1) ON CONFLICT(account_id,channel) DO UPDATE SET enabled=1",(self.account_id,channel)); self.server.db.conn.commit(); await self.send(f"Kanał {channel}: włączony."); return
        if norm in ('off','wylacz','wyłącz'):
            self.server.db.conn.execute("INSERT INTO social_channel_settings_v03051(account_id,channel,enabled) VALUES(?,?,0) ON CONFLICT(account_id,channel) DO UPDATE SET enabled=0",(self.account_id,channel)); self.server.db.conn.commit(); await self.send(f"Kanał {channel}: wyciszony."); return
        if not raw: await self.send(f"Użycie: {channel} <tekst> albo {channel} on/off."); return
        if not self.channel_enabled_v03051(channel): await self.send(f"Kanał {channel} jest wyciszony. Użyj: {channel} on."); return
        now=time.time(); state=getattr(self,'_channel_rate_v03051',[]); state=[x for x in state if now-x<10]
        last=getattr(self,'_channel_last_v03051',0.0)
        if now-last<1.5 or len(state)>=5: await self.send("Pisz trochę wolniej. Ochrona kanałów ogranicza spam."); return
        self._channel_last_v03051=now; state.append(now); self._channel_rate_v03051=state
        if len(raw)>500: raw=raw[:500]
        labels={'gossip':'GOSSIP','newbie':'NEWBIE','trade':'TRADE'}; text=f"[{labels.get(channel,channel.upper())}] {self.character.name}: {raw}"
        self.server.db.conn.execute("INSERT INTO social_channel_history_v03051(channel,sender_account_id,sender_name,message) VALUES(?,?,?,?)",(channel,self.account_id,self.character.name,raw)); self.server.db.conn.execute("DELETE FROM social_channel_history_v03051 WHERE id NOT IN (SELECT id FROM social_channel_history_v03051 ORDER BY id DESC LIMIT 500)"); self.server.db.conn.commit()
        for session in list(self.server.sessions):
            if session.closed or not session.character or not session.channel_enabled_v03051(channel): continue
            if session.is_ignored_v03051(session.account_id,self.account_id): continue
            await session.send(text,history_category='chat')

    async def show_channels_v03050(self):
        states=', '.join(f"{c}={'on' if self.channel_enabled_v03051(c) else 'off'}" for c in ('gossip','newbie','trade'))
        await self.send(f"KANAŁY: {states}. Użycie: gossip/newbie/trade <tekst> albo on/off. channels history [gossip|newbie|trade].")

    async def show_channel_history_v03051(self, channel='gossip', limit=20):
        channel=normalize_lookup_text(channel or 'gossip'); channel={'plotki':'gossip','handel':'trade','nowi':'newbie'}.get(channel,channel)
        if channel not in ('gossip','newbie','trade'): await self.send("Kanał historii: gossip, newbie albo trade."); return
        rows=self.server.db.conn.execute("SELECT sender_account_id,sender_name,message,created_at FROM social_channel_history_v03051 WHERE channel=? ORDER BY id DESC LIMIT ?",(channel,max(1,min(20,int(limit))))).fetchall()[::-1]
        await self.send(f"HISTORIA {channel.upper()}:")
        for r in rows:
            if not self.is_ignored_v03051(self.account_id,r['sender_account_id']): await self.send(f"{r['created_at']} {r['sender_name']}: {r['message']}")
        if not rows: await self.send("Brak wiadomości.")

    async def handle_afk_v03051(self,args=''):
        raw=str(args or '').strip(); conn=self.server.db.conn
        row=conn.execute("SELECT message,since_ts FROM social_afk_v03051 WHERE account_id=?",(self.account_id,)).fetchone()
        if normalize_lookup_text(raw) in ('off','wylacz','wyłącz','back','wracam') or (not raw and row):
            conn.execute("DELETE FROM social_afk_v03051 WHERE account_id=?",(self.account_id,)); conn.commit(); await self.send("AFK wyłączone."); return
        msg=raw or 'AFK'
        conn.execute("INSERT INTO social_afk_v03051(account_id,message,since_ts) VALUES(?,?,?) ON CONFLICT(account_id) DO UPDATE SET message=excluded.message,since_ts=excluded.since_ts",(self.account_id,msg,int(time.time()))); conn.commit(); await self.send(f"AFK: {msg}")

    async def tell(self,args):
        parts=str(args or '').split(maxsplit=1)
        if len(parts)!=2: await self.send("Użycie: tell <gracz> <tekst>."); return
        name,msg=parts[0],parts[1].strip(); target=self.server.find_character_session(name)
        if not target or target.closed or not target.character: await self.send("Ten gracz nie jest online."); return
        if target is self: await self.send("Nie musisz pisać do siebie."); return
        if target.is_ignored_v03051(target.account_id,self.account_id): await self.send("Ta osoba nie przyjmuje od ciebie wiadomości."); return
        if self.is_ignored_v03051(self.account_id,target.account_id): await self.send("Najpierw użyj unignore dla tej osoby."); return
        msg=msg[:500]; target.last_private_sender_account_id=self.account_id; target.last_private_sender_name=self.character.name
        await target.send(f"[TELL] {self.character.name}: {msg}",history_category='tell'); await self.send(f"[TELL do {target.character.name}] {msg}",history_category='tell')
        afk=self.server.db.conn.execute("SELECT message FROM social_afk_v03051 WHERE account_id=?",(target.account_id,)).fetchone()
        if afk: await self.send(f"{target.character.name} jest AFK: {afk['message']}")

    def _guild_name_v03051(self, aid):
        row=self.server.db.conn.execute("SELECT c.name FROM player_clan_members m JOIN player_clans c ON c.id=m.clan_id WHERE m.account_id=?",(int(aid),)).fetchone(); return row['name'] if row else ''

    def _mentor_role_v03051(self, aid):
        row=self.server.db.conn.execute("SELECT mentor_account_id,student_account_id FROM mentor_links_v03050 WHERE mentor_account_id=? OR student_account_id=?",(int(aid),int(aid))).fetchone()
        if not row: return ''
        return 'mentor' if int(row['mentor_account_id'])==int(aid) else 'uczeń'

    async def who(self):
        online=[x for x in self.server.sessions if x.character and not x.closed]; online.sort(key=lambda x:x.character.name.lower()); await self.send(f"Gracze online: {len(online)}.")
        for s in online:
            c=s.character; classes=', '.join(c.active_class_names()) or c.class_name; title=f", tytuł {c.active_title}" if c.active_title else ''; guild=self._guild_name_v03051(s.account_id); role=self._mentor_role_v03051(s.account_id); afk=self.server.db.conn.execute("SELECT 1 FROM social_afk_v03051 WHERE account_id=?",(s.account_id,)).fetchone(); party='party' if self.server.party_key_for_account(s.account_id) is not None else ''
            extras=', '.join(x for x in (guild and f"gildia {guild}",role,afk and 'AFK',party) if x)
            await self.send(f"{c.name}: {classes}, Soul {c.soul_level}{title}" + (f", {extras}" if extras else '') + '.')

    async def whois_v03051(self,args=''):
        aid=self._social_target_id_v03051(args)
        if aid is None: await self.send("Użycie: whois <gracz>."); return
        row=self.server.db.conn.execute("SELECT * FROM characters WHERE account_id=?",(aid,)).fetchone()
        if not row: await self.send("Brak profilu."); return
        name=row['name']; title=row['active_title'] or 'brak'; guild=self._guild_name_v03051(aid) or 'brak'; mastery=self.server.db.conn.execute("SELECT COALESCE(MAX(level),1) mx FROM class_progress WHERE account_id=?",(aid,)).fetchone()['mx']; ach=self.server.db.conn.execute("SELECT COUNT(*) n FROM achievements WHERE account_id=?",(aid,)).fetchone()['n']; prows=self.server.db.conn.execute("SELECT profession,level FROM professions WHERE account_id=? ORDER BY level DESC,profession LIMIT 8",(aid,)).fetchall(); prof=', '.join(f"{r['profession']} {r['level']}" for r in prows) or 'brak'; bosses=self.server.db.conn.execute("SELECT COALESCE(SUM(kills),0) n FROM bestiary WHERE account_id=?",(aid,)).fetchone() if self.server.db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bestiary'").fetchone() else None
        await self.send(f"PROFIL {name}. Tytuł: {title}. Klasa: {row['class_name']}. Biegłość max {mastery}. Soul Level {row['soul_level']}. Gildia: {guild}. Osiągnięcia: {ach}. Profesje: {prof}.")
        await self.records_v03051(str(name), compact=True)

    async def handle_mail_v03051(self,args=''):
        raw=str(args or '').strip(); conn=self.server.db.conn; parts=raw.split(maxsplit=2); action=normalize_lookup_text(parts[0]) if parts else 'lista'
        if action in ('lista','list','inbox'):
            rows=conn.execute("SELECT id,sender_name,subject,is_read,created_at FROM player_mail_v03051 WHERE recipient_account_id=? ORDER BY id DESC LIMIT 50",(self.account_id,)).fetchall(); await self.send("POCZTA:");
            for r in rows: await self.send(f"{r['id']}. {'nowa' if not r['is_read'] else 'przeczytana'} od {r['sender_name']}: {r['subject'] or '(bez tematu)'}.")
            if not rows: await self.send("Skrzynka jest pusta."); return
        elif action in ('wyslij','wyślij','send'):
            if len(parts)<3: await self.send("Użycie: mail send <gracz> <tekst>."); return
            aid=self._social_target_id_v03051(parts[1]); body=parts[2].strip()
            if aid is None: await self.send("Nie ma takiej postaci."); return
            conn.execute("INSERT INTO player_mail_v03051(recipient_account_id,sender_account_id,sender_name,subject,body) VALUES(?,?,?,?,?)",(aid,self.account_id,self.character.name,'Wiadomość od gracza',body[:2000])); conn.commit(); await self.send("Wiadomość wysłana."); return
        elif action in ('czytaj','read') and len(parts)>=2 and parts[1].isdigit():
            r=conn.execute("SELECT * FROM player_mail_v03051 WHERE id=? AND recipient_account_id=?",(int(parts[1]),self.account_id)).fetchone()
            if not r: await self.send("Nie ma takiej wiadomości."); return
            conn.execute("UPDATE player_mail_v03051 SET is_read=1 WHERE id=?",(r['id'],)); conn.commit(); await self.send(f"MAIL {r['id']} od {r['sender_name']}. {r['subject']}. {r['body']}"); return
        elif action in ('usun','usuń','delete') and len(parts)>=2 and parts[1].isdigit():
            conn.execute("DELETE FROM player_mail_v03051 WHERE id=? AND recipient_account_id=?",(int(parts[1]),self.account_id)); conn.commit(); await self.send("Wiadomość usunięta."); return
        else: await self.send("Mail: mail list, mail send <gracz> <tekst>, mail read <id>, mail delete <id>.")

    async def handle_board_v03051(self,args=''):
        raw=str(args or '').strip(); conn=self.server.db.conn; parts=raw.split(maxsplit=2); action=normalize_lookup_text(parts[0]) if parts else 'list'
        if action in ('list','lista'):
            cat=normalize_lookup_text(parts[1]) if len(parts)>1 else ''; q="SELECT id,author_name,category,body,created_at FROM bulletin_posts_v03051"; par=()
            if cat in ('trade','handel','guild','gildia','help','pomoc'): cat={'handel':'trade','gildia':'guild','pomoc':'help'}.get(cat,cat); q+=' WHERE category=?'; par=(cat,)
            rows=conn.execute(q+' ORDER BY id DESC LIMIT 30',par).fetchall(); await self.send("TABLICA OGŁOSZEŃ:");
            for r in rows: await self.send(f"{r['id']}. [{r['category']}] {r['author_name']}: {r['body']}")
            if not rows: await self.send("Brak ogłoszeń."); return
        if action in ('dodaj','post','add'):
            if len(parts)<3: await self.send("Użycie: board post <trade|guild|help> <tekst>."); return
            cat=normalize_lookup_text(parts[1]); cat={'handel':'trade','gildia':'guild','pomoc':'help'}.get(cat,cat)
            if cat not in ('trade','guild','help'): await self.send("Kategorie: trade, guild, help."); return
            body=parts[2].strip()[:500]; conn.execute("INSERT INTO bulletin_posts_v03051(author_account_id,author_name,category,body) VALUES(?,?,?,?)",(self.account_id,self.character.name,cat,body)); conn.commit(); await self.send("Ogłoszenie dodane."); return
        if action in ('usun','usuń','delete') and len(parts)>=2 and parts[1].isdigit(): conn.execute("DELETE FROM bulletin_posts_v03051 WHERE id=? AND author_account_id=?",(int(parts[1]),self.account_id)); conn.commit(); await self.send("Ogłoszenie usunięte."); return
        await self.send("Board: board list [trade|guild|help], board post <kategoria> <tekst>, board delete <id>.")

    async def handle_lfg_v03051(self,args=''):
        raw=str(args or '').strip(); conn=self.server.db.conn; now=int(time.time()); conn.execute("DELETE FROM lfg_entries_v03051 WHERE expires_ts<?",(now,)); conn.commit()
        if not raw or normalize_lookup_text(raw) in ('list','lista'):
            rows=conn.execute("SELECT character_name,category,note FROM lfg_entries_v03051 ORDER BY created_ts DESC").fetchall(); await self.send("LFG:");
            for r in rows: await self.send(f"{r['character_name']}: {r['category']}. {r['note']}")
            if not rows: await self.send("Nikt teraz nie szuka grupy."); return
        if normalize_lookup_text(raw) in ('off','usun','usuń','cancel'): conn.execute("DELETE FROM lfg_entries_v03051 WHERE account_id=?",(self.account_id,)); conn.commit(); await self.send("LFG wyłączone."); return
        parts=raw.split(maxsplit=1); cat=normalize_lookup_text(parts[0]); aliases={'krypta':'crypt','boss':'boss','profesja':'profession','profession':'profession','crypt':'crypt'}; cat=aliases.get(cat,cat)
        if cat not in ('crypt','boss','profession'): await self.send("Użycie: lfg crypt [opis], lfg boss [opis], lfg profession [opis], lfg list, lfg off."); return
        note=(parts[1] if len(parts)>1 else '')[:200]; conn.execute("INSERT INTO lfg_entries_v03051(account_id,character_name,category,note,created_ts,expires_ts) VALUES(?,?,?,?,?,?) ON CONFLICT(account_id) DO UPDATE SET character_name=excluded.character_name,category=excluded.category,note=excluded.note,created_ts=excluded.created_ts,expires_ts=excluded.expires_ts",(self.account_id,self.character.name,cat,note,now,now+7200)); conn.commit(); await self.send("LFG ustawione na 2 godziny.")

    def mentor_record_activity_v03051(self):
        row=self.mentor_link_v03050()
        if not row or not self.mentor_bonus_percent_v03050(): return
        mid,sid=int(row['mentor_account_id']),int(row['student_account_id']); now=int(time.time()); conn=self.server.db.conn
        pr=conn.execute("SELECT last_point_ts FROM mentor_progress_v03051 WHERE mentor_account_id=? AND student_account_id=?",(mid,sid)).fetchone()
        if pr and now-int(pr['last_point_ts'] or 0)<60: return
        conn.execute("INSERT INTO mentor_progress_v03051(mentor_account_id,student_account_id,activity_points,last_point_ts) VALUES(?,?,1,?) ON CONFLICT(mentor_account_id,student_account_id) DO UPDATE SET activity_points=activity_points+1,last_point_ts=excluded.last_point_ts",(mid,sid,now)); conn.commit()

    async def mentor_tasks_v03051(self, claim=False):
        row=self.mentor_link_v03050()
        if not row: await self.send("Nie masz relacji mentor-uczeń."); return
        mid,sid=int(row['mentor_account_id']),int(row['student_account_id']); conn=self.server.db.conn; pr=conn.execute("SELECT activity_points,rewards_claimed FROM mentor_progress_v03051 WHERE mentor_account_id=? AND student_account_id=?",(mid,sid)).fetchone(); pts=int(pr['activity_points'] if pr else 0); claimed=int(pr['rewards_claimed'] if pr else 0); available=pts//20
        if not claim: await self.send(f"MENTOR 2.0: wspólne aktywności {pts}. Nagroda co 20 punktów. Odebrane pakiety: {claimed}. Dostępne do odbioru: {max(0,available-claimed)}."); return
        if available<=claimed: await self.send("Nie ma jeszcze nowej nagrody mentorskiej."); return
        reward=2500
        for _aid in (mid,sid):
            _wallet=int(self.server.db.shared_wallet_for_character(_aid)[0])
            self.server.db.set_shared_wallet_for_character(_aid,min(CURRENCY_SQLITE_SAFE_TOTAL,_wallet+reward),0,0,commit=False)
            _sess=self.server.session_by_account(_aid)
            if _sess and _sess.character:
                self.server.db.apply_shared_wallet_to_character(_sess.character)
        conn.execute("UPDATE mentor_progress_v03051 SET rewards_claimed=rewards_claimed+1 WHERE mentor_account_id=? AND student_account_id=?",(mid,sid)); conn.commit()
        await self.send(f"Nagroda Mentor 2.0 trafia do mentora i ucznia: po {currency_reading_text(reward,0,0)}.")

    async def newbie_protection_v03051(self,args=''):
        norm=normalize_lookup_text(args or 'status'); conn=self.server.db.conn; row=conn.execute("SELECT enabled FROM newbie_protection_v03051 WHERE account_id=?",(self.account_id,)).fetchone(); enabled=True if row is None else bool(row['enabled'])
        if norm in ('off','wylacz','wyłącz'): enabled=False
        elif norm in ('on','wlacz','włącz'): enabled=True
        elif norm not in ('status','info',''): await self.send("Użycie: newbieprotect on/off."); return
        if norm not in ('status','info',''): conn.execute("INSERT INTO newbie_protection_v03051(account_id,enabled) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET enabled=excluded.enabled",(self.account_id,1 if enabled else 0)); conn.commit()
        await self.send(f"Newbie Protection: {'włączone' if enabled else 'wyłączone'}. Chroni początkujących przed wejściem na skrajnie za trudne zwykłe tereny.")

    def newbie_entry_block_v03051(self,target):
        row=self.server.db.conn.execute("SELECT enabled FROM newbie_protection_v03051 WHERE account_id=?",(self.account_id,)).fetchone(); enabled=True if row is None else bool(row['enabled'])
        if not enabled or int(getattr(self.character,'character_level',1) or 1)>=30: return ''
        req=int(ROOMS.get(target,{}).get('recommended_mastery',0) or 0); lvl=int(getattr(self.character,'character_level',1) or 1)
        if req>=lvl+25: return f"Newbie Protection blokuje ten teren: zalecany Level {req}, masz {lvl}. Użyj newbieprotect off, jeśli świadomie chcesz wejść."
        return ''

    async def daily_login_v03051(self):
        import datetime as _dt
        conn=self.server.db.conn; today=_dt.date.today(); row=conn.execute("SELECT last_day,streak,best_streak FROM daily_login_v03051 WHERE account_id=?",(self.account_id,)).fetchone()
        if row and row['last_day']==today.isoformat(): return
        streak=1; best=1
        if row:
            try:
                prev=_dt.date.fromisoformat(row['last_day']); streak=int(row['streak'])+1 if (today-prev).days==1 else 1; best=max(int(row['best_streak']),streak)
            except Exception: best=max(1,int(row['best_streak'] or 0))
        reward=min(3500,500*streak); self.character.silver=min(CURRENCY_SQLITE_SAFE_TOTAL,self.character_wallet_silver_value()+reward); self.character.gold=0; self.character.mithril=0; self.server.db.save_character(self.character)
        conn.execute("INSERT INTO daily_login_v03051(account_id,last_day,streak,best_streak) VALUES(?,?,?,?) ON CONFLICT(account_id) DO UPDATE SET last_day=excluded.last_day,streak=excluded.streak,best_streak=excluded.best_streak",(self.account_id,today.isoformat(),streak,best)); conn.execute("INSERT INTO player_mail_v03051(recipient_account_id,sender_name,subject,body,is_read) VALUES(?,?,?,?,0)",(self.account_id,'Soulbound','Daily login',f'Dzień serii: {streak}. Nagroda: {currency_reading_text(reward,0,0)}.')); conn.commit(); await self.send(f"Daily login: dzień {streak}. Nagroda {currency_reading_text(reward,0,0)}.")

    async def housing_v03051(self,args=''):
        raw=str(args or '').strip(); conn=self.server.db.conn
        conn.execute("INSERT OR IGNORE INTO player_housing_v03051(account_id) VALUES(?)",(self.account_id,)); conn.commit()
        row=conn.execute("SELECT * FROM player_housing_v03051 WHERE account_id=?",(self.account_id,)).fetchone()
        parts=raw.split(maxsplit=2); action=normalize_lookup_text(parts[0]) if parts else 'status'
        if action in ('status','info',''):
            await self.send(f"DOM: {row['name']}, poziom {row['level']}/10. Dekoracja: {row['decor'] or 'brak'}. Komendy: house name <tekst>, house decor <tekst>, house upgrade, house chest, house store <przedmiot> [ilość], house take <przedmiot> [ilość], house trophies."); return
        if action in ('nazwa','name') and len(parts)>1:
            name=' '.join(parts[1:])[:60]; conn.execute("UPDATE player_housing_v03051 SET name=? WHERE account_id=?",(name,self.account_id)); conn.commit(); await self.send("Nazwa domu zmieniona."); return
        if action in ('dekoracja','decor') and len(parts)>1:
            decor=' '.join(parts[1:])[:200]; conn.execute("UPDATE player_housing_v03051 SET decor=? WHERE account_id=?",(decor,self.account_id)); conn.commit(); await self.send("Dekoracja ustawiona."); return
        if action in ('ulepsz','upgrade'):
            lvl=int(row['level'])
            if lvl>=10: await self.send("Dom ma maksymalny poziom 10."); return
            cost=2000*lvl; wallet=self.character_wallet_silver_value()
            if wallet<cost: await self.send(f"Koszt: {currency_reading_text(cost,0,0)}."); return
            self.character.silver=wallet-cost; self.character.gold=0; self.character.mithril=0; self.server.db.save_character(self.character)
            conn.execute("UPDATE player_housing_v03051 SET level=level+1 WHERE account_id=?",(self.account_id,)); conn.commit(); await self.send(f"Dom osiąga poziom {lvl+1}."); return
        if action in ('chest','skrzynia'):
            import json as _json
            box=_json.loads(row['storage_json'] or '{}'); await self.send("SKRZYNIA DOMOWA:")
            if not box: await self.send("Pusta."); return
            for iid,qty in sorted(box.items(), key=lambda kv: normalize_lookup_text(player_item_display_name_v0335(kv[0]))):
                await self.send(f"{player_item_display_name_v0335(iid)}: {qty}.")
            return
        if action in ('trophies','trofea'):
            rows=conn.execute("SELECT name,tier FROM achievements WHERE account_id=? ORDER BY unlocked_at DESC LIMIT 20",(self.account_id,)).fetchall(); await self.send("TROFEA DOMOWE:")
            if not rows: await self.send("Brak zdobytych trofeów."); return
            for r in rows: await self.send(f"{r['name']} — {r['tier']}.")
            return
        if action in ('store','schowaj','wloz','włóż','take','wyjmij'):
            if len(parts)<2: await self.send("Użycie: house store/take <przedmiot> [ilość]."); return
            tail=' '.join(parts[1:]).strip(); qty=1
            seg=tail.rsplit(maxsplit=1)
            if len(seg)==2 and seg[1].isdigit(): tail=seg[0]; qty=max(1,int(seg[1]))
            norm=normalize_lookup_text(tail); candidates=[]
            for inv in self.server.db.inventory(self.account_id):
                iid=str(inv['item_id']); name=player_item_display_name_v0335(iid)
                if normalize_lookup_text(name)==norm or normalize_lookup_text(iid)==norm: candidates.append((iid,name,int(inv['quantity'])))
            import json as _json
            box=_json.loads(row['storage_json'] or '{}')
            if action in ('store','schowaj','wloz','włóż'):
                if not candidates: await self.send("Nie masz takiego przedmiotu w inventory."); return
                iid,name,have=candidates[0]; qty=min(qty,have)
                if qty<=0: await self.send("Brak przedmiotu."); return
                self.server.db.remove_item(self.account_id,iid,qty); box[iid]=int(box.get(iid,0))+qty
                conn.execute("UPDATE player_housing_v03051 SET storage_json=? WHERE account_id=?",(_json.dumps(box,ensure_ascii=False),self.account_id)); conn.commit(); await self.send(f"Do skrzyni: {name} x{qty}."); return
            # take: match storage by id or visible name
            found=None
            for iid,have in box.items():
                if normalize_lookup_text(iid)==norm or normalize_lookup_text(player_item_display_name_v0335(iid))==norm: found=(iid,int(have)); break
            if not found: await self.send("Nie ma tego w skrzyni."); return
            iid,have=found; qty=min(qty,have); self.server.db.add_item(self.account_id,iid,qty); left=have-qty
            if left>0: box[iid]=left
            else: box.pop(iid,None)
            conn.execute("UPDATE player_housing_v03051 SET storage_json=? WHERE account_id=?",(_json.dumps(box,ensure_ascii=False),self.account_id)); conn.commit(); await self.send(f"Ze skrzyni: {player_item_display_name_v0335(iid)} x{qty}."); return
        await self.send("Dom: status, name <tekst>, decor <tekst>, upgrade, chest, store, take, trophies.")

    def record_social_record_v03051(self,key,value,text=''):
        try:
            value=int(value or 0); self.server.db.conn.execute("INSERT INTO player_records_v03051(account_id,record_key,value,text_value) VALUES(?,?,?,?) ON CONFLICT(account_id,record_key) DO UPDATE SET value=MAX(value,excluded.value),text_value=CASE WHEN excluded.value>value THEN excluded.text_value ELSE text_value END,updated_at=CURRENT_TIMESTAMP",(self.account_id,str(key),value,str(text or ''))); self.server.db.conn.commit()
        except Exception: pass

    async def records_v03051(self,args='',compact=False):
        aid=self._social_target_id_v03051(args) if str(args or '').strip() else self.account_id
        if aid is None: await self.send("Nie ma takiej postaci."); return
        name=self._social_name_v03051(aid); crit=self.server.db.conn.execute("SELECT value FROM player_records_v03051 WHERE account_id=? AND record_key='biggest_crit'",(aid,)).fetchone(); deepest=self.server.db.conn.execute("SELECT COALESCE(MAX(floor),0) v FROM boss_floor_clears WHERE account_id=?",(aid,)).fetchone()['v']; kills=self.server.db.conn.execute("SELECT COALESCE(SUM(kills),0) v FROM bestiary_stats WHERE account_id=?",(aid,)).fetchone()['v']; fish=self.server.db.conn.execute("SELECT COALESCE(MAX(best_weight_g),0) v FROM fish_journal WHERE account_id=?",(aid,)).fetchone()['v']
        await self.send(f"REKORDY {name}: najgłębszy boss/loch {deepest}; największy krytyk {int(crit['value']) if crit else 0}; najcięższa ryba {fish} g; zabicia Bestiariusza {kills}.")

    async def inspect_v03051(self,args=''):
        target=self.server.find_character_session(str(args or '').strip())
        if not target or target.closed or not target.character: await self.send("Inspect działa na graczu online."); return
        row=self.server.db.conn.execute("SELECT inspect_enabled FROM player_profile_privacy_v03051 WHERE account_id=?",(target.account_id,)).fetchone(); enabled=True if row is None else bool(row['inspect_enabled'])
        if not enabled and target is not self: await self.send("Ten gracz ukrywa swoje EQ."); return
        await self.send(f"INSPECT {target.character.name}:")
        eq=target.equipped_item_rows()
        for r in eq:
            await self.send(f"{r['slot']}: {player_item_display_name_v0335(r['item_id'])}.")
        if not eq: await self.send("Brak założonego EQ.")

    async def inspect_privacy_v03051(self,args=''):
        norm=normalize_lookup_text(args or 'status'); conn=self.server.db.conn; row=conn.execute("SELECT inspect_enabled FROM player_profile_privacy_v03051 WHERE account_id=?",(self.account_id,)).fetchone(); enabled=True if row is None else bool(row['inspect_enabled'])
        if norm in ('on','wlacz','włącz'): enabled=True
        elif norm in ('off','wylacz','wyłącz'): enabled=False
        elif norm not in ('status','info',''): await self.send("Użycie: inspectprivacy on/off."); return
        if norm not in ('status','info',''): conn.execute("INSERT INTO player_profile_privacy_v03051(account_id,inspect_enabled) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET inspect_enabled=excluded.inspect_enabled",(self.account_id,1 if enabled else 0)); conn.commit()
        await self.send(f"Inspect innych graczy: {'dozwolony' if enabled else 'ukryty'}.")

    async def emote_v03051(self,kind,args=''):
        custom=str(args or '').strip(); verbs={'smile':'uśmiecha się.','wave':'macha.','cheer':'wiwatuje.'}
        if kind=='emote':
            if not custom: await self.send("Użycie: emote <tekst>."); return
            text=f"{self.character.name} {custom[:300]}"
        else: text=f"{self.character.name} {verbs[kind]}"
        await self.server.broadcast_room(self.character.room_id,text,exclude=None,history_category='chat')
