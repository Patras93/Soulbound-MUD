# -*- coding: utf-8 -*-
"""Admin Guardian 5.0: bounded, read-only quest and boss diagnostics.

Edits go ONLY through the existing atomic `admin live` pipeline. This module
never grants rewards, changes player progress or spawns combat instances.
"""
from data.quests import QUESTS
from data.mobs import MOB_TEMPLATES
from data.items import ITEMS
from data.npcs import NPCS
from systems.admin_guardian2_v3600 import resolve_mob
from systems.admin_guardian4_v3800 import _area_report
from systems.live_olc4_browse import find_catalog
from systems.live_quest_olc_v1209 import STAT_XP_FIELDS_V3900, FIELD_TITLES
from core.progression_resources import (v0190_quest_stat_reward,
    v0270_quest_character_reward, v0522_combat_quest_class_reward,
    v0190_quest_soul_reward, v0522_is_profession_quest)

HELP = (
    'GUARDIAN5: questy szukaj FRAZA [STRONA]; questy nagrody ID; '
    'questy diagnoza ID; questy porownaj ID; arena boss MOB_ID; '
    'kraina audyt ID; olc status; status; pomoc. '
    'Wszystko tylko odczyt. Zmieniaj EXP komenda admin live edytuj quest ID '
    'reward_stat_xp | LICZBA (wszystkie) lub reward_stat_strength / dexterity / '
    'constitution / intelligence / willpower / charisma | LICZBA (osobne). '
    'Po zmianach: admin live sprawdz, porownaj, aktywuj POTWIERDZAM. '
    'Wpisz auto jako LICZBA, zeby usunac nadpisanie jednej statystyki.'
)
STAT_LABELS = {
    'strength':'Sila','dexterity':'Zrecznosc','constitution':'Kondycja',
    'intelligence':'Inteligencja','willpower':'Sila Woli','charisma':'Charyzma',
}

def _quest(service, qid):
    if not 1 <= len(qid) <= 100 or any(ord(c) < 33 for c in qid):
        raise ValueError('Podaj dokladne ID questa bez spacji.')
    base = QUESTS.get(qid) or service.draft.get('quests',{}).get(qid)
    if base is None: raise ValueError('Nieznany QUEST_ID. Uzyj questy szukaj FRAGMENT.')
    return base


def _effective_reward(base, settings):
    common = settings.get('olc_reward_stat_xp', base.get('olc_reward_stat_xp', v0190_quest_stat_reward(base)))
    individual = {name: settings.get(field,base.get(field,common)) for name,field in STAT_XP_FIELDS_V3900.items()}
    return common,individual


def _quest_rewards(service, qid):
    base=_quest(service,qid)
    active=service.active.get('quest_edits',{}).get(qid,{})
    draft=service.draft.get('quest_edits',{}).get(qid,{})
    common, values=_effective_reward(base, active)
    lines=[f'QUEST NAGRODY {qid} ({base.get("name",qid)}):',
           f'EXP wspolny statystyk (bazowy): {common}'+(' [ustawiony]' if 'olc_reward_stat_xp' in active else ' [automatyczny]'),
           'EXP indywidualne, 6 statystyk: '+'; '.join(
               f'{STAT_LABELS[n]}={v}'+(' [osobny]' if field in active else ' [wspolny]')
               for n,field in STAT_XP_FIELDS_V3900.items() for v in (values[n],)),
           f'EXP postaci: {active.get("olc_reward_xp",base.get("olc_reward_xp",v0270_quest_character_reward(base)))}; '
           f'Bieglosci: {active.get("olc_reward_class_xp",base.get("olc_reward_class_xp",v0522_combat_quest_class_reward(base)))}; '
           f'Duszy: {0 if v0522_is_profession_quest(base) else active.get("olc_reward_soul_xp",base.get("olc_reward_soul_xp",v0190_quest_soul_reward(base)))}.',
           f'Waluta bazowa: srebro {active.get("reward_silver",base.get("reward_silver",0))}, '
           f'zloto {active.get("reward_gold",base.get("reward_gold",0))}, '
           f'mithril {active.get("reward_mithril",base.get("reward_mithril",0))}.',
           f'DRAFT: {len(draft)} przygotowanych pol: '+(', '.join(sorted(draft)) or 'brak')+'.',
           f'Edytuj wszystkie: admin live edytuj quest {qid} reward_stat_xp | {common}',
           f'Edytuj jedna: admin live edytuj quest {qid} reward_stat_strength | {values["strength"]}',
           'Kwoty sa bazowe: skalowanie, premie i EXP Bank pozostaja aktywne. '
           'Ta komenda niczego nie zmienia.']
    return ' '.join(lines)


def _quest_compare(service,qid):
    base=_quest(service,qid)
    active=service.active.get('quest_edits',{}).get(qid,{})
    draft=service.draft.get('quest_edits',{}).get(qid,{})
    a, avalues=_effective_reward(base,active)
    # draft is independent full DRAFT snapshot, NOT a delta to active
    b, bvalues=_effective_reward(base,draft)
    items=[]
    if a!=b:items.append(f'wspolny {a}->{b}')
    for name in STAT_XP_FIELDS_V3900:
        if avalues[name]!=bvalues[name]:items.append(f'{STAT_LABELS[name]} {avalues[name]}->{bvalues[name]}')
    for field in ('olc_reward_xp','olc_reward_class_xp','olc_reward_soul_xp','reward_profession_xp',
                  'reward_tool_xp','reward_silver','reward_gold','reward_mithril','reward_items'):
        old=active.get(field,base.get(field,'auto'))
        new=draft.get(field,base.get(field,'auto'))
        if old!=new: items.append(f'{FIELD_TITLES.get(field,field)} {str(old)[:30]}->{str(new)[:30]}')
    return (f'QUEST POROWNAJ {qid}: '+('; '.join(items[:20]) if items else 'brak zmian nagrod miedzy aktywne i DRAFT.')+
            ' Zmiany nieaktywne do admin live aktywuj POTWIERDZAM.')


def _quest_diag(service,qid):
    base=dict(_quest(service,qid))
    base.update(service.draft.get('quest_edits',{}).get(qid,{}))
    issues=[]
    kind=base.get('kind','?')
    target=base.get('target')
    if kind=='kill' and target not in MOB_TEMPLATES and target not in service.draft.get('mobs',{}) and target!='*':
        issues.append('nieznany cel moba (sprawdz aliasy / quest_target)')
    if kind=='collect' and target not in ITEMS and target not in service.draft.get('items',{}):
        issues.append('nieznany przedmiot')
    if kind in ('kill','collect') and int(base.get('needed') or 0)<1:
        issues.append('wymagana liczba <= 0')
    giver=base.get('giver')
    names={str(n.get('name','')).casefold() for n in NPCS.values()}
    names.update(str(n.get('name','')).casefold() for n in service.draft.get('npcs',{}).values())
    if giver and str(giver).casefold() not in names:
        issues.append('dawca nie wystepuje pod dokladna nazwa; moze byc aliasem/serwisem')
    dependency=base.get('requires_quest')
    if dependency and dependency not in QUESTS and dependency not in service.draft.get('quests',{}):
        issues.append('brak ID wymaganej misji')
    for need in base.get('requires_quests',[]) or []:
        if need not in QUESTS and need not in service.draft.get('quests',{}):
            issues.append('brak w liscie wymaganych misji: '+str(need)[:35])
    return (f'QUEST DIAGNOZA {qid}: typ {kind}, cel {target}, dawca {giver or "brak"}; '+
            (f'{len(issues)} sygnalow: '+('; '.join(issues[:12])) if issues else 'brak oczywistych anomalii w sprawdzanych polach.')+
            ' Nie oznacza to gwarancji poprawnosci scenariusza. Bez zmian postepu i nagrod.')


def _boss_metadata(service,mid):
    meta,origin=resolve_mob(service,mid)
    if meta is None: raise ValueError('Nieznany mob / boss ID.')
    if not (meta.get('boss') or meta.get('olc_boss_phases') or meta.get('olc_ancient_phases')
            or meta.get('olc_boss_phase_element_cycles')):
        return f'ARENA BOSS {mid}: brak jawnych metadanych bossa. To moze byc zwykly mob.'
    bits=[]
    for field in ('olc_boss_phases','olc_ancient_phases','olc_boss_phase_element_cycles',
                  'olc_boss_guardian_phase_roles','olc_boss_guardian_roles',
                  'olc_boss_support_interval','olc_boss_guardian_interval',
                  'olc_boss_tactic_interval','olc_boss_tactic_element',
                  'olc_boss_guard_threshold','olc_boss_guardian_hp_threshold'):
        if field in meta:
            value=meta[field]
            description=(f'{len(value)} rekordow' if isinstance(value,(list,dict)) else str(value)[:60])
            bits.append(f'{field}={description}')
    return (f'ARENA BOSS {mid} ({origin}): HP {meta.get("max_hp", "?")}, '
            f'obrazenia {meta.get("damage", "?")}; metadane '+('; '.join(bits[:15]) or 'brak faz w OLC')+'. '
            'Odczyt definicji, NIE symulacja prawdziwego UOSS, odporności, AI, summonow ani dropow. Brak nagrod.')


def _olc_status(service):
    active=service.active
    draft=service.draft
    sections=['quest_edits','quests','mob_edits','mobs','rooms','links','npcs']
    differences=[f'{k}: {len(draft.get(k,{})) if k!="links" else len(draft.get(k,[]))}'
                 for k in sections if draft.get(k)!=active.get(k)]
    return ('OLC GUARDIAN5: DRAFT/aktywne: '+('; '.join(differences) if differences else 'brak roznic')+'. '
            'Odczyt; przed publikacja: admin live sprawdz / porownaj. Bez zmian.')


async def handle_guardian5(s,raw):
    """Handle owner-only v39 namespace; all operations are read-only."""
    parts=str(raw).strip().split()
    if not parts or parts[0].casefold()!='guardian5':return False
    if not s.is_admin():
        await s.send('GUARDIAN5: tylko wlasciciel-administrator.')
        return True
    args=parts[1:]
    service=s.server.live_content_v1204
    try:
        if not args or args[0].casefold() in ('pomoc','help'):msg=HELP
        elif args==['status']:msg='GUARDIAN5 v39: nagrody szesciu statystyk i diagnostyka, bez zmian w bazie; arena boss tylko metadane.'
        elif args[0].casefold()=='questy':
            if len(args)>=3 and args[1].casefold()=='szukaj':
                page=int(args[-1]) if len(args)>=4 and args[-1].isdigit() else 1
                phrase=' '.join(args[2:-1] if len(args)>=4 and args[-1].isdigit() else args[2:]).strip()
                if not 1<=len(phrase)<=70: raise ValueError('Fraza 1-70 znakow.')
                msg=find_catalog(service,'quest',phrase,page)
            elif len(args)==3 and args[1].casefold()=='nagrody':msg=_quest_rewards(service,args[2])
            elif len(args)==3 and args[1].casefold()=='diagnoza':msg=_quest_diag(service,args[2])
            elif len(args)==3 and args[1].casefold()=='porownaj':msg=_quest_compare(service,args[2])
            else:raise ValueError('questy szukaj FRAZA [STRONA] / nagrody ID / diagnoza ID / porownaj ID')
        elif len(args)==3 and args[:2]==['arena','boss']:msg=_boss_metadata(service,args[2])
        elif len(args)==3 and args[:2]==['kraina','audyt']:msg=_area_report(service,args[2])
        elif args==['olc','status']:msg=_olc_status(service)
        else:raise ValueError(HELP)
        await s.send(msg)
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        await s.send('GUARDIAN5: '+str(exc)[:400])
    return True
