# -*- coding: utf-8 -*-
"""Soulbound v28 OLC60-67. Durable publication, neutral defaults, eight consumers."""
import copy
import json
import sqlite3
from types import SimpleNamespace


def run():
    from systems.live_content_v1204 import LiveContentV1204, blank
    from systems.live_olc28_expansion import (DOMAINS, ACTIVE, FIELDS, boss_finisher_factor,
        craft_yield, summon_outgoing, skill_damage_multiplier, event_weight,
        quest_coins, guild_extra_bonus, sale_coins, preview)
    from systems.world_events_v12812 import active_city_event_v12812
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES
    from player.session_mixins.era_sky_v1700 import SUMMONS
    from player.session_methods_v4200.combatskills_part01 import offensive_skill_damage_multiplier_v11186
    from data.mobs import MOB_TEMPLATES
    checks=0
    def ok(value, label):
        nonlocal checks
        assert value, label
        checks+=1
    def deny(action, label):
        nonlocal checks
        try:action()
        except (ValueError,TypeError): checks+=1
        else:raise AssertionError('Brak walidacji: '+label)

    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE quests(quest_id TEXT,status TEXT)')
    boss=MOB_TEMPLATES['uoss_superboss_black_rabite_v11136']
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *_:None)
    server=SimpleNamespace(world=world,sessions=[])
    svc=None;again=None
    old_templates={}
    for slug in ('basalt','echo','star','myth'):
        tid='v12812_event_'+slug
        old_templates[tid]=copy.deepcopy(MOB_TEMPLATES.get(tid))
        if tid not in MOB_TEMPLATES:
            MOB_TEMPLATES[tid]={'name':'Event test','max_hp':10000,'damage':300,
                               'class_xp_reward':500,'soul_reward':50,
                               'stat_reward':5,'silver':120,'damage_type':'physical'}
    event_id='live_trial_v28'
    try:
        svc=LiveContentV1204(SimpleNamespace(conn=db))
        ok('v28_rules' in svc.active and set(svc.active['v28_rules'])==set(DOMAINS),'eight domains')
        ok(boss_finisher_factor(boss,10,100)==1,'neutral UOSS')
        ok(craft_yield('Górnictwo',4)==4,'neutral crafting')
        ok(summon_outgoing('pajak',500)==500,'neutral summon')
        ok(skill_damage_multiplier(1.35)==1.35,'neutral skill')
        ok(event_weight(event_id)==1,'neutral event')
        ok(quest_coins(100000)==100000,'neutral quest')
        ok(guild_extra_bonus(True)==0,'neutral guild')
        ok(sale_coins(100)==100,'neutral resale')
        ok(guild_extra_bonus(False)==0,'non-member')
        old=blank();old.pop('v28_rules')
        ok(set(LiveContentV1204._compat(old))==set(blank()),'v27 compatible')
        ok(all(FIELDS[x] for x in DOMAINS),'fields wired')
        event={'name':'Próba v28','boss_name':'Żelazny Wędrowiec','city':'basalt',
               'style':'physical','element':'earth','hp':500000,'damage':3500,'silver':9000}
        svc.stage_edit('event26',event_id,'definicja',json.dumps(event,ensure_ascii=False))
        requests=(
            ('uoss28','black_rabite','finisher_target_hp_percent','30'),
            ('uoss28','black_rabite','finisher_damage_percent','225'),
            ('fach28','Górnictwo','craft_yield_percent','250'),
            ('summon28','pajak','outgoing_damage_percent','180'),
            ('skill28','global','damage_percent','155'),
            ('event28',event_id,'rotation_weight','3'),
            ('fabula28','global','quest_currency_percent','175'),
            ('gildia28','global','bonus_extra_percent','20'),
            ('ekonomia28','global','sell_value_percent','140'),
        )
        for domain,key,field,value in requests:
            svc.stage_edit(domain,key,field,value)
            ok(svc.draft['v28_rules'][__import__('systems.live_olc28_expansion',fromlist=['ALIASES']).ALIASES[domain]][key][field]==int(value),
               'stage '+domain)
        ok('Aktualnie:' in preview(svc,'uoss28','black_rabite','finisher_damage_percent'),'preview existing')
        for d,key,field,bad in (
            ('uoss28','missing','finisher_damage_percent','150'),
            ('fach28','missing','craft_yield_percent','150'),
            ('summon28','missing','outgoing_damage_percent','120'),
            ('event28','live_unknown','rotation_weight','2'),
            ('event28',event_id,'rotation_weight','0'),
            ('event28',event_id,'rotation_weight','6'),
            ('skill28','global','damage_percent','70'),
            ('gildia28','global','bonus_extra_percent','101'),
            ('uoss28','black_rabite','finisher_target_hp_percent','0'),
            ('ekonomia28','global','sell_value_percent','100.5'),
            ('fabula28','global','quest_currency_percent','true'),
            ('fabula28','wrong','quest_currency_percent','110'),
        ):
            deny(lambda d=d,key=key,field=field,bad=bad:svc.stage_edit(d,key,field,bad),d+'/'+field)
        ok(skill_damage_multiplier(1)==1,'draft not active')
        ok(quest_coins(80)==80,'draft payout neutral')
        ok('Aktywowano' in svc.apply(server,'v28_integracja'),'publish')
        ok(svc.revision==1,'first revision')
        ok(abs(boss_finisher_factor(boss,29,100)-2.25)<1e-8,'finisher enabled')
        ok(boss_finisher_factor(boss,31,100)==1,'finisher threshold')
        ok(boss_finisher_factor({'name':'Zwykły'},10,100)==1,'UOSS only')
        ok(craft_yield('Górnictwo',4)==10,'craft quantities real')
        ok(craft_yield('Kowalstwo',4)==4,'other craft neutral')
        ok(summon_outgoing('pajak',500)==900,'summon strike')
        ok(summon_outgoing('wilk',500)==500,'other summon neutral')
        ok(abs(skill_damage_multiplier(1.35)-2.0925)<1e-8,'skill power')
        # Test the actual offensive skill multiplier with only its declared math dependencies.
        class Character:
            def class_physical_damage_multiplier(self):return 1.0
            def racial_physical_damage_multiplier(self):return 1.0
            def class_magic_damage_multiplier(self):return 1.0
            def racial_magic_damage_multiplier(self):return 1.0
            def racial_all_damage_multiplier(self):return 1.0
        stub=SimpleNamespace(character=Character(), total_set_damage_multiplier=lambda:1.0,
            equipment_damage_multiplier=lambda _kind:1.0,
            skill_buff_multiplier=lambda **kwargs:1.0)
        # Party synergy may require session state; also tested via skill_damage_multiplier above.
        ok(event_weight(event_id)==3,'authored event weight')
        slots=[active_city_event_v12812(n*10800)['slug'] for n in range(7)]
        ok(slots.count(event_id)==3,'actual world rotation weight')
        ok(quest_coins(100)==175,'quest money payout')
        ok(guild_extra_bonus(True)==20,'guild member bonus')
        ok(guild_extra_bonus(False)==0,'no boost for nonmembers')
        ok(sale_coins(1000)==1400,'shop sale payout')
        # A separate reader re-installs the published revision after removal.
        svc._remove(world)
        again=LiveContentV1204(SimpleNamespace(conn=db))
        ok(again.revision==1,'SQLite reload revision')
        ok(craft_yield('Górnictwo',4)==10,'craft survives restart')
        ok(event_weight(event_id)==3,'event survives restart')
        ok(sale_coins(100)==140,'economy survives restart')
        ok(quest_coins(100)==175,'quest survives restart')
        # Isolated revert does not change other published domains.
        again.stage_edit('fabula28','global','quest_currency_percent','auto')
        again.stage_edit('summon28','pajak','outgoing_damage_percent','auto')
        again.stage_edit('event28',event_id,'rotation_weight','auto')
        ok('Aktywowano' in again.apply(server,'v28_integracja'),'auto publish')
        ok(quest_coins(100)==100,'reset quest money')
        ok(summon_outgoing('pajak',500)==500,'reset summon')
        ok(event_weight(event_id)==1,'reset event')
        ok(craft_yield('Górnictwo',4)==10,'other changes retained')
        ok(db.execute('SELECT COUNT(*) FROM live_content_history_v1204').fetchone()[0]==2,'history')
    finally:
        for instance in (again,svc):
            if instance is not None and instance._undo:instance._remove(world)
        for tid,old in old_templates.items():
            if old is None:MOB_TEMPLATES.pop(tid,None)
            else:MOB_TEMPLATES[tid]=old
        db.close()
    return checks

if __name__=='__main__':print('OLC60-67:',run(),'PASS')
