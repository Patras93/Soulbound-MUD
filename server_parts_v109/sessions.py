# -*- coding: utf-8 -*-
"""v109: wydzielone metody serwera — sessions; bez zmiany zachowania."""
class MudSessionsV109Mixin:
    def account_online(self, account_id):
        return self.session_by_master_account(account_id) is not None

    def session_by_master_account(self, account_id, exclude=None):
        for session in list(self.sessions):
            if session is exclude or session.closed:
                continue
            if getattr(session, "master_account_id", None) == int(account_id):
                return session
        return None

    def find_character_session(self, name):
        for s in self.sessions:
            if s.closed or not s.character:
                continue
            if s.character.name.lower() == str(name or "").lower():
                return s
        return None

    def session_by_account(self, account_id):
        for session in self.sessions:
            if session.account_id == account_id and session.character:
                return session
        return None
