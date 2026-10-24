# -*- coding: utf-8 -*-
"""Admin Guardian 7: private UOSS source-rule combat lab and atomic quest repairs.

Important security boundary: the lab is a deterministic approximation driven
by actual pure UOSS phase/ability/status rules, not the production combat loop.
No real Session, SQLite, live world mob or reward method is invoked by the lab.
Quest writes stage validated DRAFT only and require explicit confirmation.
"""
from __future__ import annotations
import copy
import re
from types import SimpleNamespace
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS
from systems.admin_guardian2_v3600 import resolve_mob, _audit
from systems.admin_guardian6_v4000 import _combined, _signals
from systems.live_quest_olc_v1209 import parse_quest_edit
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
from world.uoss_superboss_runtime import (
    SUPERBOSS_HELPER_ROLES_V11330, superboss_source_ability_v11162,
    superboss_source_summons_v11162, superboss_exact_ability_effect_v11160,
    superboss_source_status_v11162, superboss_source_round_event_v11160,
    superboss_phase_event_v11138, superboss_counterattack_multiplier_v11137,
    superboss_element_multiplier_v11173,
)

_HELP = {
    '1': ('GUARDIAN7 pomoc 1/3 ARENA: arena start BOSS_ID HP POSTACI OBRAZENIA [HELPER]; '
          'arena status [STRONA]; arena dziennik [STRONA]; arena atak [CEL]; arena magia ELEMENT [CEL]; '
          'arena obrona; arena wynik; arena wyjdz. CEL=boss lub numer pomocnika. '
          'Kazda komenda ataku wykonuje jedna ture. Bez prawdziwych nagrod.'),
    '2': ('GUARDIAN7 pomoc 2/3 QUESTY: questy plan ID | POLE | WARTOSC [| POLE | WARTOSC]; '
          'questy zmien ID | POLE | WARTOSC [| ...] | POTWIERDZAM; '
          'questy cofnij POTWIERDZAM; questy audyt ID; questy przeglad STRONA. '
          'Wszystko DRAFT, publikacja tylko przez admin live.'),
    '3': ('GUARDIAN7 pomoc 3/3: status; olc kontrola; pomoc 1/2/3. '
          'Arena wywoluje wybrane prawdziwe funkcje UOSS dla faz, zaklec, statusow i summonow '
          'NA KOPIACH danych. Nie uruchamia produkcyjnej petli walki, losowych unikow, '
          'pelnego AI ani skilli gracza; to laboratorium, nie wynik prawdziwego starcia. '
          'Zadne komendy labu nie modyfikuja HP, EXP, przedmiotow, questow i SQLite.'),
}

_MAX_HP=10**15
_MAX_DAMAGE=10**15
_MAX_ADDS=24  # only in private test; not a gameplay summon cap
_MAX_TURNS=250
_ALLOWED_REPAIR=frozenset(('target','giver','needed','requires_quest','requires_quests',
                            'reward_silver','reward_gold','reward_mithril','reward_items',
                            'olc_reward_xp','olc_reward_class_xp','olc_reward_soul_xp','olc_reward_stat_xp'))


def _number(value, low=1,high=_MAX_HP):
    if not re.fullmatch(r'[0-9]{1,16}',str(value)):
        raise ValueError('Oczekiwana dodatnia liczba calkowita.')
    n=int(value)
    if not low <= n <= high: raise ValueError(f'Dozwolony zakres {low}-{high}.')
    return n


def _id(value):
    if not re.fullmatch(r'[a-zA-Z0-9_\-]{1,100}',str(value)):
        raise ValueError('Niepoprawne ID.')
    return str(value)


def _template(service, identifier):
    ident=_id(identifier)
    if ident in UOSS_SUPERBOSS_ENCOUNTERS_V11134:
        ident='uoss_superboss_'+ident+'_v11136'
    base,origin=resolve_mob(service, ident)
    if base is None:raise ValueError('Nieznany boss. Uzyj ID moba lub klucza superbossa.')
    return ident,copy.deepcopy(base),origin


def _lab_start(s,service,identifier,hp,damage,helper='brak'):
    ident,t,origin=_template(service,identifier)
    mh=_number(t.get('max_hp',0));attack=_number(t.get('damage',0))
    hero_hp=_number(hp);hero_atk=_number(damage)
    key=t.get('uoss_unique_superboss_key')
    choice=str(helper).lower()
    eligible=[]
    if key in UOSS_SUPERBOSS_ENCOUNTERS_V11134:
        spec=UOSS_SUPERBOSS_ENCOUNTERS_V11134[key]
        eligible=list(spec.get('helpers') or ([spec['helper']] if spec.get('helper') else []))
    selected=next((x for x in eligible if x.lower()==choice),None)
    if choice!='brak' and not selected:
        raise ValueError('Nieznany pomocnik dla tego bossa. Dostepni: '+(', '.join(eligible) or 'brak'))
    mob=SimpleNamespace(template_id=ident, max_hp=mh, hp=mh, alive=True,
        combat_turn=0, phase_stage=0, room_id='__guardian7_private_lab__')
    s.guardian7_lab={'template':t,'boss':mob,'origin':origin,'key':key,'name':ident,
         'hero_hp':hero_hp,'hero_max':hero_hp,'hero_attack':hero_atk,
         'total_dealt':0,'total_taken':0,'round':0,'adds':[],
         'helper':selected,'statuses':set(),'notes':[], 'finished':False}
    return (f'ARENA7 START {ident} ({origin}); HP bossa {mh}, atak bossa {attack}; '
            f'HP testowej postaci {hero_hp}, atak {hero_atk}, pomocnik {selected or "brak"}. '
            'KOPIA W PAMIECI, bez nagrod i bez prawdziwej walki. arena atak [CEL].')


def _lab_status(s,page='1'):
    a=getattr(s,'guardian7_lab',None)
    if not a:return 'ARENA7: brak aktywnego testu. arena start ID HP ATAK.'
    boss=a['boss']; adds=a['adds']
    pn=_number(page,1,5)
    page_adds=adds[(pn-1)*6:pn*6]
    marker=', '.join(f'{i}: {entry["name"]} HP {entry["hp"]}/{entry["max"]}'
                      for i,entry in enumerate(page_adds,(pn-1)*6+1)) or 'brak'
    return (f'ARENA7 runda {a["round"]}, boss {a["name"]} HP {boss.hp}/{boss.max_hp}, '
            f'gracz HP {a["hero_hp"]}/{a["hero_max"]}, pomocnicy strona {pn} [{marker}], '
            f'statusy [{", ".join(sorted(a["statuses"])) or "brak"}], '
            f'{"KONIEC" if a["finished"] else "TRWA"}. '
            'Bez utraty prawdziwego HP ani nagrod.')


def _known_element_effect(template,element):
    """Use exact declared categories, never invent weakness/resist percentages."""
    normalized=str(element).strip().lower()
    if not normalized or len(normalized)>30 or not normalized.replace('_','').isalpha():
        raise ValueError('Zywioł: nazwa 1-30 liter.')
    def match(key):
        values=template.get(key) or ()
        if isinstance(values,str):values=(values,)
        return any(str(x).strip().lower()==normalized for x in values)
    if match('absorb'):return -1.0,'absorpcja z definicji bossa'
    if match('immune'):return 0.0,'immunitet z definicji bossa'
    mult,_=superboss_element_multiplier_v11173(template,element)
    if mult<0:return mult,'absorpcja UOSS'
    if mult==0:return mult,'immunitet UOSS'
    if match('resist') or match('weak'):
        return 1.0,'odpornosc/slabosc wymieniona w definicji, brak liczbowego mnoznika'
    return mult,''


def _lab_target(a,target):
    if not target or str(target).casefold() in ('boss','glowny'):
        return a['boss'],None
    value=_number(target,1,99)
    if value>len(a['adds']):raise ValueError('Nie ma pomocnika z tym numerem.')
    entry=a['adds'][value-1]
    if entry['hp']<=0:raise ValueError('Ten pomocnik jest juz pokonany.')
    return None,entry


def _lab_turn(s, element=None, target='boss', defend=False):
    a=getattr(s,'guardian7_lab',None)
    if not a:raise ValueError('Arena nieuruchomiona.')
    if a['finished']:raise ValueError('Arena skonczona. arena wynik lub arena wyjdz.')
    if a['round']>=_MAX_TURNS:
        a['finished']=True
        return 'ARENA7: zakonczono na limicie 250 tur LABORATORIUM. Nie ma tego limitu w zwyklej grze.'
    t=a['template']; boss=a['boss']; lines=[]
    mob,add=(None,None) if defend else _lab_target(a,target)
    if defend:
        lines.append('Obrona: w tej turze przyjete obrazenia zmniejszone o polowe (model testowy).')
    else:
        hit=a['hero_attack']
        if element:
            mult,note=_known_element_effect(t,element) if mob is not None else (1.0,'')
            if note:lines.append(note+'.')
            if mult<0:
                healed=min(boss.max_hp-boss.hp,hit)
                boss.hp+=healed
                hit=0; lines.append(f'{element}: absorpcja bossa, odzyskal {healed} HP.')
            else:
                hit=max(0,int(hit*mult))
                if not hit:lines.append(f'{element}: odpornosc — 0 obrazen.')
        if mob is not None:
            hit=min(hit,boss.hp);boss.hp-=hit
        else:
            hit=min(hit,add['hp']);add['hp']-=hit
        a['total_dealt']+=hit
        lines.append(f'Trafienie w {"boss" if mob is not None else add["name"]}: {hit}.')
    a['round']+=1
    boss.combat_turn=a['round']
    if boss.hp<=0:
        boss.alive=False;a['finished']=True
        result=f'ARENA7 tura {a["round"]}: '+ ' '.join(lines)+' Boss pokonany w symulacji, 0 EXP, 0 zlota, 0 dropow.'
        a['notes'].append(result[:550]);a['notes']=a['notes'][-24:]
        return result
    phase=superboss_phase_event_v11138(None,t,boss)
    if phase:lines.append(f'Faza {phase[0]} bossa: {str(phase[1])[:100]}.')
    ability=superboss_source_ability_v11162(t,boss)
    summoned=superboss_source_summons_v11162(None,t,boss,ability) if ability else ()
    if ability:lines.append(f'Zdolnosc UOSS: {ability}.')
    for ident in summoned:
        if len(a['adds'])>=_MAX_ADDS:
            lines.append('Limit bezpiecznego testu: kolejnych pomocnikow nie tworzono.')
            break
        summoned_template=MOB_TEMPLATES.get(ident)
        if summoned_template:
            health=_number(summoned_template.get('max_hp',1))
            dps=_number(summoned_template.get('damage',1))
            a['adds'].append({'id':ident,'name':str(summoned_template.get('name',ident)),
                              'hp':health,'max':health,'damage':dps})
            lines.append('Przywolano '+str(summoned_template.get('name',ident))[:60]+'.')
        else:
            lines.append('Brak szablonu przywolanego '+str(ident)[:50]+'.')
    source_effect=superboss_exact_ability_effect_v11160(
        SimpleNamespace(character=SimpleNamespace(gravityproof=False),gravityproof=False),t,boss,ability)
    event=superboss_source_round_event_v11160(None,t,boss)
    if event and event.get('instant_death'):
        a['hero_hp']=0;a['finished']=True
        lines.append(f'{event["name"]}: koniec proby w modelu; prawdziwa postac zyje.')
    else:
        phase_mult,_note=superboss_counterattack_multiplier_v11137(t,boss)
        hit=max(0,int(t.get('damage',0)*phase_mult))
        if ability:
            from world.uoss_superboss_runtime import superboss_source_attack_multiplier_v11162
            hit=int(hit*superboss_source_attack_multiplier_v11162(t,ability))
        if source_effect:
            if 'damage' in source_effect:hit=source_effect['damage']
            if 'current_hp_fraction' in source_effect:
                hit=int(a['hero_hp']*source_effect['current_hp_fraction'])
            if 'countdown_rounds' in source_effect:
                lines.append('Odliczanie: '+str(source_effect['countdown_rounds'])+' rund.')
        if defend:hit//=2
        if a['helper']:
            reduction=SUPERBOSS_HELPER_ROLES_V11330[a['helper']]['damage_reduction']
            hit=max(0,int(hit*(1-reduction)))
        extras=sum(add['damage'] for add in a['adds'] if add['hp']>0)
        if defend:extras//=2
        total=hit+extras
        a['hero_hp']=max(0,a['hero_hp']-total)
        a['total_taken']+=total
        lines.append(f'Cios bossa {hit}, pomocnicy {extras}, HP gracza {a["hero_hp"]}.')
        status=superboss_source_status_v11162(t,ability)
        if status:
            a['statuses'].add(status)
            lines.append('Nalozono status '+status+' (opis; brak symulacji czasu dzialania).')
        if a['hero_hp']<=0:a['finished']=True;lines.append('Postac testowa pokonana, prawdziwa zyje.')
    result=f'ARENA7 tura {a["round"]}: '+ ' '.join(lines)[:550]
    a['notes'].append(result);a['notes']=a['notes'][-24:]
    return result


def _lab_log(s,page='1'):
    a=getattr(s,'guardian7_lab',None)
    if not a:return 'ARENA7: brak aktywnego testu.'
    p=_number(page,1,8)
    rows=a['notes'][-24:]
    start=(p-1)*3
    return (f'ARENA7 DZIENNIK strona {p}/{max(1,(len(rows)+2)//3)}: '
            + (' '.join(rows[start:start+3]) if start<len(rows) else 'brak wpisow')+'.')


def _lab_report(s):
    a=getattr(s,'guardian7_lab',None)
    if not a:return 'ARENA7: brak raportu.'
    alive=sum(x['hp']>0 for x in a['adds'])
    return (f'ARENA7 RAPORT {a["name"]}: tur {a["round"]}, '
            f'zadane {a["total_dealt"]}, otrzymane {a["total_taken"]}, '
            f'HP bossa {a["boss"].hp}, postaci {a["hero_hp"]}, zywych summonow {alive}. '
            'Fazy, zdolnosci, summonowanie i efekty liczbowe UOSS uzywaja wybranych funkcji z silnika; '
            'brak pelnego AI i obrazen postaci z prawdziwego ekwipunku. Nie jest to test produkcyjnej walki. '
            '0 XP, 0 pieniedzy i 0 trwalych zapisow.')


def _repair_parse(spec):
    fields=[x.strip() for x in spec.split('|')]
    if len(fields)<3 or len(fields)%2!=1 or len(fields)>17:
        raise ValueError('Uzycie: ID | POLE | WARTOSC [| POLE | WARTOSC], maks. 8 pol.')
    qid=_id(fields[0]);changes={}
    for f,v in zip(fields[1::2],fields[2::2]):
        normalized, parsed=parse_quest_edit(f,v)
        if normalized not in _ALLOWED_REPAIR:raise ValueError('Pole niedostepne w bezpiecznej naprawie: '+f)
        if normalized in changes:raise ValueError('Powtorzone pole: '+normalized)
        changes[normalized]=parsed
    return qid,changes


def _repair_preview(service,spec):
    qid,changes=_repair_parse(spec)
    quests=_combined(service)
    if qid not in quests:raise ValueError('Nieznane ID questa.')
    before=copy.deepcopy(service.draft)
    after=copy.deepcopy(before)
    patch=after['quest_edits'].setdefault(qid,{})
    patch.update(changes)
    service.validate(after)
    rows=[]
    for field,value in changes.items():
        old=before['quest_edits'].get(qid,{}).get(field,quests[qid].get(field,'brak'))
        rows.append(f'{field} {str(old)[:55]} -> {str(value)[:55]}')
    return qid,before,after,'; '.join(rows)


def _repair(session,service,spec,confirm):
    qid,before,after,changes=_repair_preview(service,spec)
    if not confirm:
        return f'QUEST7 PLAN {qid}: {changes}. Brak zmian. Uzyj questy zmien ... | POTWIERDZAM.'
    service.draft=after
    stack=getattr(session,'guardian7_undo',[])
    stack.append((copy.deepcopy(before),copy.deepcopy(after),qid))
    session.guardian7_undo=stack[-8:]
    return (f'QUEST7 DRAFT {qid}: {changes}. Wylacznie robocza wersja; '
            'postepy i nagrody graczy pozostaja nietkniete. '
            'admin live sprawdz, porownaj, aktywuj POTWIERDZAM.')


def _undo(session,service):
    stack=getattr(session,'guardian7_undo',[])
    if not stack:raise ValueError('Nie ma operacji guardian7 do cofniecia.')
    before,after,qid=stack[-1]
    if service.draft!=after:raise ValueError('DRAFT zmienil sie od czasu naprawy — nie cofnie sie bezpiecznie.')
    service.validate(before)
    service.draft=copy.deepcopy(before)
    stack.pop()
    return f'QUEST7 COFNIETO robocza naprawe {qid}. Publikowane zmiany bez zmian.'


def _audit_one(service,qid):
    quests=_combined(service)
    if qid not in quests:raise ValueError('Nieznany quest.')
    base=quests[qid]
    issues=_signals(service,qid,base)
    new=copy.deepcopy(base)
    new.update(service.draft.get('quest_edits',{}).get(qid,{}))
    # Prevent false positives from author aliases; only signals, never auto-fix unknown IDs.
    checks=['nazwa','typ','cel','needed','nagrody','zaleznosci']
    if not new.get('name'):issues.append('brak nazwy')
    if new.get('kind') in ('kill','collect'):
        if new.get('needed') is None:issues.append('brak ilosci wymaganej')
    return (f'QUEST7 AUDYT {qid}: pola {", ".join(checks)}; '
           +('; '.join(issues[:12]) if issues else 'brak oczywistych bledow w kontrolowanych polach')
           +'. To sygnaly, nie dowod; bez zmian.')


def _audit_all(service):
    quests=_combined(service)
    counts={}
    samples=[]
    for qid,q in quests.items():
        issues=_signals(service,qid,q)
        if issues:
            for issue in issues:
                counts[issue.split(' ',1)[0]]=counts.get(issue.split(' ',1)[0],0)+1
            if len(samples)<12:samples.append(qid)
    return ('QUEST7 SKAN GLOBAL: sprawdzono '+str(len(quests))+' definicji, '
            'kategorie sygnalow: '+(', '.join(f'{k}={v}' for k,v in sorted(counts.items())) or 'brak')+'; '
            'przykladowe ID '+(', '.join(samples) or 'brak')+'. '
            'Statyczne kontrole, bez automatycznej zmiany i bez obietnicy 100% poprawnosci.')


def _audit_page(service,p):
    page=_number(p,1,10000)
    quests=sorted(_combined(service))
    from_=(page-1)*12
    if quests and from_>=len(quests):raise ValueError('Strona poza katalogiem.')
    hits=[]
    for qid in quests[from_:from_+12]:
        if _signals(service,qid,_combined(service)[qid]):hits.append(qid)
    return f'QUEST7 PRZEGLAD strona {page}/{max(1,(len(quests)+11)//12)}: 12 lub mniej questow; ID z sygnalami: '+(', '.join(hits) or 'brak')+'. Bez zmian.'


def _olc_guard(service):
    summary=service.validate(service.draft)
    ids=sorted(set(service.draft.get('quest_edits',{})) | set(service.draft.get('quests',{})))
    findings=[qid for qid in ids if _signals(service,qid,_combined(service)[qid])]
    return (f'OLC7 KONTROLA: {summary}; przygotowanych questow {len(ids)}, '
            f'sygnalow {len(findings)}; ID: '+(', '.join(findings[:12]) or 'brak')+'. '
            'Tylko odczyt; przed publikacja sprawdz takze admin live sprawdz i porownaj.')


async def handle_guardian7(s,raw):
    parts=str(raw or '').strip().split(maxsplit=1)
    if not parts or parts[0].casefold()!='guardian7':return False
    if not s.is_admin():
        await s.send('GUARDIAN7: tylko wlasciciel-administrator.');return True
    service=s.server.live_content_v1204
    rest=parts[1].strip() if len(parts)>1 else 'pomoc 1'
    tokens=rest.split();mode=tokens[0].casefold() if tokens else 'pomoc'
    try:
        if mode=='pomoc':
            msg=_HELP.get(tokens[1] if len(tokens)>1 else '1')
            if msg is None:raise ValueError('Pomoc ma strony 1, 2, 3.')
        elif mode=='status':
            msg='GUARDIAN7: laboratorium UOSS na kopiach i naprawy tylko w DRAFT. '+_lab_status(s)
        elif mode=='arena':
            action=tokens[1].casefold() if len(tokens)>1 else ''
            if (getattr(s,'guardian7_lab',None) and
                    'actor8' in s.guardian7_lab and action not in ('wyjdz','start')):
                raise ValueError('Aktywna arena8. Uzyj admin guardian8 arena ..., albo wyjdz.')
            if action=='start' and len(tokens) in (5,6):
                msg=_lab_start(s,service,tokens[2],tokens[3],tokens[4],tokens[5] if len(tokens)==6 else 'brak')
            elif action=='status' and len(tokens) in (2,3):msg=_lab_status(s,tokens[2] if len(tokens)==3 else '1')
            elif action=='dziennik' and len(tokens) in (2,3):msg=_lab_log(s,tokens[2] if len(tokens)==3 else '1')
            elif action=='atak' and len(tokens) in (2,3):msg=_lab_turn(s,target=tokens[2] if len(tokens)==3 else 'boss')
            elif action=='magia' and len(tokens) in (3,4):msg=_lab_turn(s,element=tokens[2],target=tokens[3] if len(tokens)==4 else 'boss')
            elif action=='obrona' and len(tokens)==2:msg=_lab_turn(s,defend=True)
            elif action=='wynik' and len(tokens)==2:msg=_lab_report(s)
            elif action=='wyjdz' and len(tokens)==2:
                s.guardian7_lab=None;msg='ARENA7: prywatny test usuniety. Postac i baza niezmienione.'
            else:raise ValueError(_HELP['1'])
        elif mode=='questy':
            action=tokens[1].casefold() if len(tokens)>1 else ''
            if action in ('plan','zmien'):
                bits=rest.split(None,2)
                if len(bits)<3:raise ValueError(_HELP['2'])
                spec=bits[2]
                if action=='zmien':
                    sections=spec.rsplit('|',1)
                    if len(sections)<2 or sections[-1].strip()!='POTWIERDZAM':
                        raise ValueError('Potrzebne POTWIERDZAM jako ostatni segment.')
                    spec=sections[0].strip()
                msg=_repair(s,service,spec,action=='zmien')
                if action=='zmien':_audit(s,'guardian7_quest_draft',spec.split('|',1)[0].strip())
            elif action=='cofnij' and len(tokens)==3 and tokens[2]=='POTWIERDZAM':
                msg=_undo(s,service);_audit(s,'guardian7_quest_undo','ostatnia')
            elif action=='audyt' and len(tokens)==3:msg=_audit_one(service,tokens[2])
            elif action=='przeglad' and len(tokens)==3:msg=_audit_page(service,tokens[2])
            elif action=='skan' and len(tokens)==2:msg=_audit_all(service)
            else:raise ValueError(_HELP['2'])
        elif mode=='olc' and len(tokens)==2 and tokens[1].casefold()=='kontrola':msg=_olc_guard(service)
        else:raise ValueError('Wpisz admin guardian7 pomoc 1, 2 lub 3.')
        await s.send(msg)
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        await s.send('GUARDIAN7: '+str(exc)[:350])
    return True
