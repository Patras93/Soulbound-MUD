# -*- coding: utf-8 -*-
"""v88: cross-domain atomic Admin Live DRAFT changes.

One plan can change quest, skill, mob, item, recipe, shop and *scripted UOSS*
without half-applying a bundle. All checks are performed against one complete
candidate in memory, with no live-world, currency, progression or SQLite writes.
The regular OLC publication workflow remains the sole activation path.
"""
from __future__ import annotations

import copy
import json
import re
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS
from data.crafting_recipes import CRAFT_RECIPES
from data.shops import SHOPS
from data.npcs import NPCS
from systems.live_content_v1204 import _integer
from systems.live_quest_olc_v1209 import QUEST_AUTO_FIELDS, parse_quest_edit
from systems.live_olc6_skill_editor import stage_existing_skill
from systems.live_olc17_quest_dependencies import validate_dependency_graph
from systems.admin_live_integrity_v4900 import _effective
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_v7500 import _boss, _integers
from systems.olc_level_bounds_v7003 import level_bound

SLOT = 'adminlive8800_all_plan'
UNDO = 'adminlive8800_all_undo'
MAX_CHANGES = 24
MAX_TEXT = 3500
IDENT = re.compile(r'[A-Za-z0-9_\-]{1,100}\Z', re.ASCII)
SAFE_NUMBERS = {
    'mob': {'max_hp','damage','class_xp_reward','soul_reward','stat_reward',
            'respawn_seconds','silver','gold','mithril'},
    'item': {'price','required_level','heal','defense','attack','magic_attack',
             'magic_defense','weapon_power','sell_silver','sell_gold'},
    'recipe': {'quantity','min_profession_level','min_tool_level','tool_xp','profession_xp'},
}
SECTIONS = {'mob':'mob_edits','item':'item_edits','recipe':'recipe_edits','shop':'shop_edits','npc':'npc_edits'}
CATALOGS = {'mob':MOB_TEMPLATES,'item':ITEMS,'recipe':CRAFT_RECIPES,'shop':SHOPS,'npc':NPCS}
HELP = (
    'ADMIN LIVE POMOC 46: aktualizacja plan TYP ID POLE | WARTOSC; TYP ID POLE | WARTOSC; ... '
    '(1-24 zmian: quest, skill, mob, item, recipe, shop, npc, uoss). '
    'Przyklady: quest temple_rats reward_gold | 100; mob temple_rat damage | 2; '
    'skill warrior_power_slash mana | 5; item leather_vest price | 200; '
    'shop market inventory | ["healing_potion","leather_vest"]; '
    'uoss black_rabite furia | 3:115:4; npc fisher_tomas dialogue | Witaj. '
    'Mozna uzyc AUTO dla pojedynczego nadpisania (dla zaleznosci questowych: BRAK). '
    'aktualizacja karta TYP ID POLE / status / zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
    'Wszystko jest walidowane razem. Zatwierdzenie zmienia WYŁĄCZNIE DRAFT, '
    'nie SQLite ani aktywnej gry. Publikacja nadal wymaga admin live sprawdz i aktywuj POTWIERDZAM.'
)


def _safe_id(value):
    if not IDENT.fullmatch(value):
        raise ValueError('ID musi zawierac 1-100 znakow ASCII: litery, cyfry, _ lub -.')
    return value


def _set_patch(candidate, section, ident, field, value):
    candidate.setdefault(section,{}).setdefault(ident,{})[field] = value


def _reset_patch(candidate, section, ident, field):
    record=candidate[section].get(ident)
    if not record:return
    record.pop(field,None)
    if not record:candidate[section].pop(ident,None)


def _uoss(candidate,boss,field,text):
    _boss(boss)  # validates that it is a real scripted UOSS boss
    fields={'fazy':'v32_rules','leczenie':'v33_rules','furia':'v34_rules','skala':'v24_rules'}
    if field not in fields:
        raise ValueError('UOSS: dozwolone pola fazy, leczenie, furia, skala.')
    dest=candidate[fields[field]]['uoss']
    if text.upper() in ('AUTO','BRAK'):
        if field=='skala':
            original=copy.deepcopy(dest.get(boss,{}))
            for key in ('max_hp_percent','damage_percent'):original.pop(key,None)
            if original:dest[boss]=original
            else:dest.pop(boss,None)
        else:dest.pop(boss,None)
        return
    if field=='fazy':
        phases=[]
        for entry in text.split(','):
            hp,every,power=_integers(entry.strip(),3,'fazy')
            phases.append({'below_hp':hp,'interval':every,'damage_percent':power})
        if not 1 <= len(phases) <= 5:
            raise ValueError('Fazy: 1-5 etapow.')
        dest[boss]={'phases':phases}
    elif field=='leczenie':
        hp,every,percent=_integers(text,3,'leczenie')
        dest[boss]={'below_hp':hp,'every':every,'restore_percent':percent}
    elif field=='furia':
        every,power,stacks=_integers(text,3,'furia')
        dest[boss]={'every':every,'stack_percent':power,'max_stacks':stacks}
    else:
        hp,damage=_integers(text,2,'skala')
        row=copy.deepcopy(dest.get(boss,{}))
        row.update(max_hp_percent=hp,damage_percent=damage)
        dest[boss]=row


def _stage(candidate,kind,ident,field,value):
    if kind in ('quest','zadanie'):
        if ident not in QUESTS and ident not in candidate.get('quests',{}):
            raise ValueError('Nieznany quest ID: '+ident)
        if field=='requires_quest' and value.upper()=='BRAK':
            _set_patch(candidate,'quest_edits',ident,field,None)
        elif field=='requires_quests' and value.upper()=='BRAK':
            _set_patch(candidate,'quest_edits',ident,field,[])
        else:
            canon=field
            from systems.live_quest_olc_v1209 import QUEST_XP_ALIASES
            canon=QUEST_XP_ALIASES.get(field,field)
            if value.upper()=='AUTO' and canon in QUEST_AUTO_FIELDS:
                _reset_patch(candidate,'quest_edits',ident,canon)
            else:
                canon,parsed=parse_quest_edit(field,value)
                _set_patch(candidate,'quest_edits',ident,canon,parsed)
    elif kind=='skill':
        stage_existing_skill(candidate,ident,field,value)
    elif kind=='uoss':
        _uoss(candidate,ident,field,value)
    elif kind=='npc':
        if ident not in NPCS and ident not in candidate.get('npcs',{}):
            raise ValueError('NPC: nieznany ID.')
        if field not in ('name','dialogue','room','quest','shopkeeper'):
            raise ValueError('NPC: pole musi byc name, dialogue, room, quest lub shopkeeper.')
        if value.upper()=='AUTO':
            _reset_patch(candidate,'npc_edits',ident,field)
        elif field=='shopkeeper':
            if value.casefold() not in ('true','false','tak','nie'):
                raise ValueError('shopkeeper: true/false lub tak/nie.')
            _set_patch(candidate,'npc_edits',ident,field,value.casefold() in ('true','tak'))
        else:
            from systems.live_content_v1204 import _text
            parsed=_text(value,100 if field=='name' else 1600,field)
            _set_patch(candidate,'npc_edits',ident,field,parsed)
    elif kind=='shop':
        if field!='inventory' or ident not in SHOPS and ident not in candidate['shops']:
            raise ValueError('Sklep: istniejący ID i pole inventory.')
        if value.upper()=='AUTO':
            _reset_patch(candidate,'shop_edits',ident,'inventory')
        else:
            try: inventory=json.loads(value)
            except json.JSONDecodeError as exc:raise ValueError('Sklep: lista JSON ID przedmiotow.') from exc
            if not isinstance(inventory,list) or len(inventory)>120 or any(type(k)!=str for k in inventory):
                raise ValueError('Sklep: lista JSON do 120 ID przedmiotow.')
            _set_patch(candidate,'shop_edits',ident,'inventory',inventory)
    elif kind in SECTIONS:
        section=SECTIONS[kind]
        definition=CATALOGS[kind].get(ident,candidate.get({'mob':'mobs','item':'items','recipe':'recipes'}[kind],{}).get(ident))
        if definition is None:
            raise ValueError('Nieznany '+kind+' ID: '+ident)
        if field not in SAFE_NUMBERS[kind]:
            raise ValueError(f'{kind}: pole {field} nie jest bezpiecznym polem liczbowym.')
        if kind in ('item','recipe') and field not in definition:
            raise ValueError(f'{kind} {ident} nie ma parametru {field}.')
        if value.upper()=='AUTO':
            _reset_patch(candidate,section,ident,field)
        else:
            level_axis={'required_level':'eq','min_profession_level':'profesje',
                        'min_tool_level':'narzedzia'}.get(field)
            limit=level_bound(level_axis) if level_axis else 365*86400 if field=='respawn_seconds' else 10000 if field=='quantity' else 10**15
            minimum=1 if field in ('required_level','min_profession_level','min_tool_level','quantity','max_hp') else 0
            result=_integer(value,minimum,limit,field)
            _set_patch(candidate,section,ident,field,result)
    else:
        raise ValueError('Typ: quest, skill, mob, item, recipe, shop, npc albo uoss.')


def plan(session,service,raw):
    setattr(session,SLOT,None)
    if not isinstance(raw,str) or not 1<=len(raw)<=MAX_TEXT:
        raise ValueError('Pusty lub zbyt dlugi plan (maksymalnie 3500 znakow).')
    entries=[x.strip() for x in raw.split(';')]
    if not 1<=len(entries)<=MAX_CHANGES or any(not x for x in entries):
        raise ValueError('Wymagane 1-24 niepuste operacje oddzielone srednikami.')
    before=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(before)
    labels=[];touched=set()
    for entry in entries:
        if entry.count('|')!=1:
            raise ValueError('Format: TYP ID POLE | WARTOSC.')
        lhs,value=(x.strip() for x in entry.split('|',1))
        parsed=lhs.split()
        if len(parsed)!=3 or not value or len(value)>600:
            raise ValueError('Format: TYP ID POLE | WARTOSC (wartosc do 600 znakow).')
        kind,ident,field=parsed
        kind=kind.casefold();kind='quest' if kind=='zadanie' else kind;_safe_id(ident)
        if not IDENT.fullmatch(field):raise ValueError('Niepoprawna nazwa pola.')
        section_key=(kind,ident,field)
        if section_key in touched:raise ValueError('Powtorzona zmiana w jednym planie: '+ident+'.'+field)
        touched.add(section_key)
        _stage(candidate,kind,ident,field,value)
        labels.append(f'{kind}/{ident}/{field}')
    # Check the entire quest chain after all edits are applied. This catches
    # cycles created by combining modifications from otherwise valid rows.
    full=_effective(service)
    full.update({qid:{**full[qid],**patch} for qid,patch in candidate['quest_edits'].items() if qid in full})
    validate_dependency_graph(full)
    service.validate(candidate)  # all production OLC validators, exactly once
    if candidate==before:raise ValueError('Brak zmian w DRAFT.')
    _plan(session,SLOT,before,service.active,candidate,'AKTUALIZACJA CALOSCIOWA')
    groups=sorted({x.split('/',1)[0] for x in labels})
    return (f'AKTUALIZACJA PLAN: {len(labels)} pol, {len(groups)} dziedzin: '
            +', '.join(groups)+'. '+ '; '.join(labels[:10])+
            (f'; i jeszcze {len(labels)-10} pol.' if len(labels)>10 else '.')+
            ' Walidacja pelnego DRAFT: OK. Nie zapisano zmian. '
            'aktualizacja zatwierdz POTWIERDZAM.')


def card(service,kind,ident,field):
    """One concise screen-reader-friendly current-value card, without guessing.

    Override absence is explicitly distinguishable from an authored default.
    """
    import json
    from core.classes_skills import CLASS_SKILLS
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    _safe_id(ident)
    kind=kind.casefold()
    if not IDENT.fullmatch(field):raise ValueError('Niepoprawne pole.')
    if kind=='uoss':
        if ident not in UOSS_SUPERBOSS_ENCOUNTERS_V11134:raise ValueError('Nieznany superboss.')
        section={'fazy':'v32_rules','leczenie':'v33_rules','furia':'v34_rules','skala':'v24_rules'}.get(field)
        if not section:raise ValueError('UOSS: fazy, leczenie, furia, skala.')
        def pull(snapshot):return snapshot[section]['uoss'].get(ident,'AUTO')
    else:
        if kind in ('quest','zadanie'):
            section='quest_edits'; base=QUESTS
        elif kind=='skill':
            section='skill_edits';base={str(row['id']):row for rows in CLASS_SKILLS.values() for row in rows}
        elif kind in SECTIONS:
            section=SECTIONS[kind];base=CATALOGS[kind]
        else:raise ValueError('Nieznany typ.')
        if ident not in base and ident not in service.draft.get({'quest_edits':'quests',
            'mob_edits':'mobs','item_edits':'items','recipe_edits':'recipes',
            'shop_edits':'shops','npc_edits':'npcs'}.get(section,'___'),{}):
            raise ValueError('Nieznany ID obiektu.')
        if section=='shop_edits' and field!='inventory':raise ValueError('Sklep ma pole inventory.')
        if section=='skill_edits' and field not in base[ident] and field not in ('olc_status','mechanic_cooldown'):
            raise ValueError('Brak tego pola skilla.')
        def pull(snapshot):
            edits=snapshot[section].get(ident,{})
            if field in edits:return edits[field]
            default=base.get(ident,{})
            return default.get(field,'BRAK') if isinstance(default,dict) else default if field=='inventory' else 'BRAK'
    a=pull(service.active); d=pull(service.draft)
    def short(value):
        output=json.dumps(value,ensure_ascii=False,separators=(',',':'))
        return output[:155]+('...' if len(output)>155 else '')
    return f'AKTUALIZACJA KARTA {kind} {ident} {field}: ACTIVE={short(a)}; DRAFT={short(d)}. Bez zmian.'


def status(session,service):
    pending=bool(getattr(session,SLOT,None))
    undo=bool(getattr(session,UNDO,None))
    altered=[key for key in ('quest_edits','skill_edits','mob_edits','item_edits',
                             'recipe_edits','shop_edits','npc_edits') if service.draft.get(key)!=service.active.get(key)]
    altered += [f'UOSS/{name}' for name in ('v24_rules','v32_rules','v33_rules','v34_rules')
                if service.draft[name]['uoss']!=service.active[name]['uoss']]
    return ('AKTUALIZACJA STATUS: plan='+('TAK' if pending else 'NIE')+
            '; cofniecie='+('TAK' if undo else 'NIE')+
            '; roznice DRAFT/ACTIVE='+(', '.join(altered) if altered else 'BRAK')+
            '. Niczego nie zapisano.')


async def dispatch_v8800(session,cmd,tail):
    args=str(tail or '').strip()
    parts=args.split()
    matched=(cmd=='pomoc' and args=='46') or (cmd=='aktualizacja' and parts and parts[0] in ('plan','status','anuluj','zatwierdz','cofnij','karta'))
    if not matched:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    try:
        service=session.server.live_content_v1204
        if cmd=='pomoc':out=HELP
        elif parts[0]=='plan':out=plan(session,service,args.partition('plan')[2].strip())
        elif parts==['zatwierdz','POTWIERDZAM']:out=_commit(session,service,SLOT,UNDO)
        elif parts==['cofnij','POTWIERDZAM']:out=_undo(session,service,SLOT,UNDO)
        elif len(parts)==4 and parts[0]=='karta':out=card(service,*parts[1:])
        elif parts==['anuluj']:
            setattr(session,SLOT,None)
            out='AKTUALIZACJA: plan anulowany; nic nie zmieniono.'
        elif parts==['status']:out=status(session,service)
        else:raise ValueError('Wymagane POTWIERDZAM. Pomoc 46.')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        out='ADMIN LIVE V88: '+str(exc)[:260]
    await session.send(out)
    return True
