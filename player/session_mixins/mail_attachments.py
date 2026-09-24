# -*- coding: utf-8 -*-
"""Soulbound v0.61.4 — player mail attachments with escrow."""

from player.session_mixins.inventory_equipment import CURRENCY_SQLITE_SAFE_TOTAL
from player.session_mixins.shops_teachers import currency_reading_text
from player.session_mixins.skill_learning import normalize_lookup_text


class SessionMailAttachmentsV0614Mixin:
    async def handle_mail_v03051(self, args=''):
        raw = str(args or '').strip()
        conn = self.server.db.conn
        parts = raw.split(maxsplit=2)
        action = normalize_lookup_text(parts[0]) if parts else 'lista'

        if action in ('lista', 'list', 'inbox'):
            rows = conn.execute(
                "SELECT id,sender_name,subject,is_read,created_at,attachment_kind,attachment_claimed "
                "FROM player_mail_v03051 WHERE recipient_account_id=? ORDER BY id DESC LIMIT 50",
                (self.account_id,),
            ).fetchall()
            await self.send("POCZTA:")
            for row in rows:
                kind = str(row['attachment_kind'] or '')
                attach = ''
                if kind:
                    attach = ' załącznik' if not int(row['attachment_claimed'] or 0) else ' załącznik odebrany'
                await self.send(
                    f"{row['id']}. {'nowa' if not row['is_read'] else 'przeczytana'}{attach} "
                    f"od {row['sender_name']}: {row['subject'] or '(bez tematu)'} ."
                )
            if not rows:
                await self.send("Skrzynka jest pusta.")
            return

        if action in ('wyslij', 'wyślij', 'send'):
            if len(parts) < 3:
                await self.send(
                    "Użycie: mail wyslij <gracz> <tekst>; mail wyslij <gracz> przedmiot <nazwa>; "
                    "mail wyslij <gracz> waluta <kwota> <nominał>."
                )
                return
            aid = self._social_target_id_v03051(parts[1])
            body = parts[2].strip()
            if aid is None:
                await self.send("Nie ma takiej postaci.")
                return
            if int(aid) == int(self.account_id):
                await self.send("Nie możesz wysłać poczty samemu sobie.")
                return

            body_parts = body.split(maxsplit=1)
            attach_mode = normalize_lookup_text(body_parts[0]) if body_parts else ''
            attach_payload = body_parts[1].strip() if len(body_parts) > 1 else ''

            if attach_mode in ('przedmiot', 'item', 'zalacznik', 'załącznik'):
                if not attach_payload:
                    await self.send("Użycie: mail wyslij <gracz> przedmiot <pełna nazwa przedmiotu>.")
                    return
                found = self.resolve_transferable_inventory_item(attach_payload)
                if not found:
                    await self.send(
                        "Nie rozpoznaję wolnego, przekazywalnego przedmiotu w twoim inventory. "
                        "Załącznik może zawierać jedną sztukę; przedmioty questowe, przypisane i założone są blokowane."
                    )
                    return
                item_id, item = found
                if self.free_transferable_quantity(item_id) < 1:
                    await self.send(f"Nie masz wolnej sztuki: {item['name']}.")
                    return
                mail_id = self.server.db.send_mail_attachment_v0614(
                    self.account_id, aid, self.character.name,
                    kind='item', item_id=item_id, item_name=item['name'],
                )
                if not mail_id:
                    await self.send("Nie udało się odłożyć przedmiotu w pocztowym escrow. Nic nie zostało wysłane.")
                    return
                await self.send(
                    f"Wysłano mail #{mail_id} do {self._social_name_v03051(aid)} z załącznikiem: {item['name']} x1. "
                    "Przedmiot został bezpiecznie zabrany od nadawcy i czeka na odbiór."
                )
                return

            if attach_mode in ('waluta', 'money', 'coins', 'monety'):
                if not attach_payload:
                    await self.send(
                        "Użycie: mail wyslij <gracz> waluta <kwota> <nominał>, "
                        "np. mail wyslij Arven waluta 5 złota."
                    )
                    return
                parsed = self.parse_player_currency_transfer(attach_payload)
                if parsed is None:
                    await self.send("Nie rozpoznaję kwoty. Przykład: mail wyslij Arven waluta 5 złota.")
                    return
                amount, description = parsed
                if amount <= 0 or amount > CURRENCY_SQLITE_SAFE_TOTAL:
                    await self.send("Kwota musi być dodatnia i mieścić się w limicie waluty.")
                    return
                sender_total = int(self.server.db.shared_wallet_for_character(self.account_id)[0])
                if sender_total < amount:
                    await self.send(
                        "Nie masz wystarczającej waluty. Masz: "
                        + currency_reading_text(sender_total, 0, 0, full_names=True) + "."
                    )
                    return
                mail_id = self.server.db.send_mail_attachment_v0614(
                    self.account_id, aid, self.character.name,
                    kind='currency', amount_silver=amount,
                )
                if not mail_id:
                    await self.send(
                        "Nie udało się wysłać waluty. Sprawdź odbiorcę, saldo i limit portfela; "
                        "nic nie zostało zmienione."
                    )
                    return
                self.server.db.apply_shared_wallet_to_character(self.character)
                await self.send(
                    f"Wysłano mail #{mail_id} do {self._social_name_v03051(aid)} z załącznikiem: {description}. "
                    "Waluta została odłożona w pocztowym escrow."
                )
                return

            conn.execute(
                "INSERT INTO player_mail_v03051(recipient_account_id,sender_account_id,sender_name,subject,body) "
                "VALUES(?,?,?,?,?)",
                (aid, self.account_id, self.character.name, 'Wiadomość od gracza', body[:2000]),
            )
            conn.commit()
            await self.send("Wiadomość wysłana.")
            return

        if action in ('czytaj', 'read') and len(parts) >= 2 and parts[1].isdigit():
            row = conn.execute(
                "SELECT * FROM player_mail_v03051 WHERE id=? AND recipient_account_id=?",
                (int(parts[1]), self.account_id),
            ).fetchone()
            if not row:
                await self.send("Nie ma takiej wiadomości.")
                return
            conn.execute("UPDATE player_mail_v03051 SET is_read=1 WHERE id=?", (row['id'],))
            conn.commit()
            await self.send(f"MAIL {row['id']} od {row['sender_name']}. {row['subject']}. {row['body']}")
            kind = str(row['attachment_kind'] or '')
            if kind and not int(row['attachment_claimed'] or 0):
                if kind == 'item':
                    await self.send(
                        f"ZAŁĄCZNIK DO ODBIORU: {row['attachment_item_name']} "
                        f"x{int(row['attachment_item_qty'] or 1)}. Wpisz mail odbierz {row['id']}."
                    )
                elif kind == 'currency':
                    await self.send(
                        "ZAŁĄCZNIK DO ODBIORU: "
                        + currency_reading_text(int(row['attachment_coins'] or 0), 0, 0, full_names=True)
                        + f". Wpisz mail odbierz {row['id']}."
                    )
            elif kind:
                await self.send("Załącznik został już odebrany.")
            return

        if action in ('odbierz', 'claim', 'take') and len(parts) >= 2 and parts[1].isdigit():
            mail_id = int(parts[1])
            row = conn.execute(
                "SELECT * FROM player_mail_v03051 WHERE id=? AND recipient_account_id=?",
                (mail_id, self.account_id),
            ).fetchone()
            if not row:
                await self.send("Nie ma takiej wiadomości.")
                return
            if not str(row['attachment_kind'] or ''):
                await self.send("Ta wiadomość nie ma załącznika.")
                return
            if int(row['attachment_claimed'] or 0):
                await self.send("Załącznik został już odebrany.")
                return
            result = self.server.db.claim_mail_attachment_v0614(self.account_id, mail_id)
            if not result or not result.get('ok'):
                if result and result.get('reason') == 'wallet_cap':
                    await self.send("Nie możesz jeszcze odebrać waluty: przekroczyłaby limit twojego wspólnego portfela.")
                else:
                    await self.send("Nie udało się odebrać załącznika; nic nie zostało oznaczone jako odebrane.")
                return
            if result['kind'] == 'item':
                await self.send(f"Odebrano załącznik: {result['item_name']} x{result['qty']}.")
            else:
                self.server.db.apply_shared_wallet_to_character(self.character)
                await self.send(
                    "Odebrano załącznik: "
                    + currency_reading_text(int(result['amount']), 0, 0, full_names=True) + "."
                )
            return

        if action in ('usun', 'usuń', 'delete') and len(parts) >= 2 and parts[1].isdigit():
            row = conn.execute(
                "SELECT attachment_kind,attachment_claimed FROM player_mail_v03051 "
                "WHERE id=? AND recipient_account_id=?",
                (int(parts[1]), self.account_id),
            ).fetchone()
            if row and str(row['attachment_kind'] or '') and not int(row['attachment_claimed'] or 0):
                await self.send("Ta wiadomość ma nieodebrany załącznik. Najpierw wpisz mail odbierz <id>.")
                return
            conn.execute(
                "DELETE FROM player_mail_v03051 WHERE id=? AND recipient_account_id=?",
                (int(parts[1]), self.account_id),
            )
            conn.commit()
            await self.send("Wiadomość usunięta.")
            return

        await self.send(
            "Mail: mail list, mail send <gracz> <tekst>, mail wyslij <gracz> przedmiot <nazwa>, "
            "mail wyslij <gracz> waluta <kwota> <nominał>, mail read <id>, mail odbierz <id>, mail delete <id>."
        )


__all__ = ["SessionMailAttachmentsV0614Mixin"]
