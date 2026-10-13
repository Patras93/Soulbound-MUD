# -*- coding: utf-8 -*-
"""Cross-class EQ regressions, read-only, no player DB required."""
from systems.equipment_multiclass_v3001 import crossover_bonus_v3001, crossover_text_v3001


def run_regression():
    checks = 0
    def check(condition, message):
        nonlocal checks
        assert condition, message
        checks += 1
    physical = {'name':'Pancerz','type':'armor','slot':'body','required_class':'Wojownik','stats':{'strength':100,'dexterity':50},'attack':60,'defense':20}
    magical = {'name':'Szata','type':'armor','slot':'body','required_class':'Mag','stats':{'intelligence':90,'willpower':60},'magic_attack':50,'defense':20}
    xstat,xpower=crossover_bonus_v3001(physical)
    check(xstat=={'intelligence':30,'willpower':30},'physical stats')
    check(xpower=={'magic_attack':18},'physical magic attack')
    check('Siła Woli +30' in crossover_text_v3001(physical),'NVDA physical')
    xstat,xpower=crossover_bonus_v3001(magical)
    check(xstat=={'strength':30,'dexterity':30},'magical stats')
    check(xpower=={'attack':15},'magical attack')
    check('Zręczność +30' in crossover_text_v3001(magical),'NVDA magical')
    hybrid = {'name':'Hybrid','type':'armor','slot':'charm','stats':{'strength':10,'intelligence':10},'attack':10,'magic_attack':10}
    check(crossover_bonus_v3001(hybrid)==({},{}),'no double hybrid')
    for obj in ({'type':'tool','slot':'hands','attack':50}, {'type':'loot'}, {}, {'type':'armor'}):
        check(crossover_bonus_v3001(obj)==({},{}),'no non-equipment boosts')
    low={'type':'armor','slot':'head','defense':2}
    check(crossover_bonus_v3001(low)==({'intelligence':1,'willpower':1},{'magic_attack':1}),'starter')
    check(physical['stats']=={'strength':100,'dexterity':50},'no mutation')
    check(magical['magic_attack']==50,'no mutation power')
    check(crossover_bonus_v3001(physical)==crossover_bonus_v3001(physical),'idempotent')
    # Verify that registered class-shop items, including late-generated items,
    # use the identical crossover arithmetic without relying on hardcoded ids.
    import sys
    running_server = sys.modules.get("server")
    items = getattr(running_server, "ITEMS", {}) if running_server else {}
    phys_item=next((it for it in items.values() if it.get('class_shop_item') and it.get('required_class')=='Wojownik'),None)
    magic_item=next((it for it in items.values() if it.get('class_shop_item') and it.get('required_class')=='Mag'),None)
    if phys_item and magic_item:
        s,p=crossover_bonus_v3001(phys_item)
        check('intelligence' in s and 'willpower' in s and 'magic_attack' in p,'real warrior shop gear')
        s,p=crossover_bonus_v3001(magic_item)
        check('strength' in s and 'dexterity' in s and 'attack' in p,'real mage shop gear')
        # End-to-end live aggregators and equipment comparison, without real player SQL.
        from types import SimpleNamespace
        from player.session_mixins.equipment_stats import SessionEquipmentStatsMixin
        from player.session_mixins.equipment_compare import SessionEquipmentCompareV0600Mixin
        class FakeDB:
            def equipment_reforge(self, *args): return None
            def equipment_runes_v0925(self, *args): return ()
            def equipment_upgrade_level_v03042(self, *args): return 0
            def equipment_enchants_v03053(self, *args): return ()
        class Wearer(SessionEquipmentStatsMixin, SessionEquipmentCompareV0600Mixin):
            account_id=100
            server=SimpleNamespace(db=FakeDB())
            def equipped_item_rows(self): return self.rows
            def equipment_total_socket_capacity_v03114(self, *args): return 0
            def active_soul_weapon_relic_v11176(self): return ('',None)
            def class_set_stat_bonus_totals(self): return {}
        phys_id=next(k for k,it in items.items() if it is phys_item)
        magic_id=next(k for k,it in items.items() if it is magic_item)
        wearer=Wearer()
        wearer.rows=({'item_id':phys_id}, {'item_id':magic_id})
        bs=wearer.equipment_bonus_totals()
        pf=wearer.equipment_flat_power_totals_v11187()
        e1,e2=crossover_bonus_v3001(phys_item)[0],crossover_bonus_v3001(magic_item)[0]
        check(bs['intelligence']>=e1['intelligence'], 'actual int agg')
        check(bs['willpower']>=e1['willpower'], 'actual will agg')
        check(bs['strength']>=e2['strength'], 'actual str agg')
        check(bs['dexterity']>=e2['dexterity'], 'actual dex agg')
        check(pf['attack']>=crossover_bonus_v3001(magic_item)[1]['attack'], 'actual attack agg')
        check(pf['magic_attack']>=crossover_bonus_v3001(phys_item)[1]['magic_attack'], 'actual magic attack agg')
        snap=wearer._comparison_snapshot_v0600(phys_id,phys_item)
        check(snap['stats']['intelligence']>=e1['intelligence'], 'compare int')
        check(snap['power']['magic_attack']>=crossover_bonus_v3001(phys_item)[1]['magic_attack'], 'compare magic attack')
    return checks

if __name__ == '__main__':
    print(f'EQ MULTICLASS 14 v3.00.1: {run_regression()} checks PASS')
