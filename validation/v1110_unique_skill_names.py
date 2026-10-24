# -*- coding: utf-8 -*-
"""v11.00.10: skill-name authoring and exact v11.00.9 mechanical invariants."""
from validation.release_contracts import release_valid
import hashlib
import json
import re
from collections import Counter
from core.classes_skills import CLASS_SKILLS, V1110_UNIQUE_SKILL_NAMES
from core.unique_skill_names_v1110 import _canonical, _generated, _KIND_GROUP
from core.bootstrap_economy_professions import VERSION

_EXPECTED_MECHANIC_SHA256 = {'Bard': 'a84b5f333db955ddbf1199b61b7ef01c5171ff7ba674234a19e313f3aff05465', 'Berserker': '8a3f5806b3a25eb7209ebcb832b3531f304dc408b34e777c389639b11f51a45f', 'Chronomanta': '305fb2637b0bed003c5696c2c5618e42d6222ed3407d7d3defee747e7cdd2806', 'Czarownik': '288b73dc0518eb2c70c01cb2bdfe5a94d299e261b4f58aef696d35cbdcb9b7ab', 'Druid': '1b733c35f449bc114ef21306fa591f59d8156bd1676b9ca8f2471b81764d7288', 'Gladiator': '1867f36dcc50fee0d1d14da649baece9e90f4313ccd8328d7225a7c976e54f02', 'Iluzjonista': '17d25ba796475bb8d77651c715b97ad181335e0be6aec49d834ad40a9cf8fc28', 'Inżynier': 'f160c1b4302d0b2b728c5a7bcc5db5eeaaa722f09a9c5bf005f22e51e9d1d972', 'Kapłan': '82f8fbd9d0110ef58cd46663270297f156712b67446f01496f40fd7c06daea55', 'Korsarz': '52446aca808069d943c4a07e265fa0d13bf031b162105b016f5011db08e3b876', 'Mag': '53a35a44f5aeb1fbdef043411eb98f58890e72c5f70711fd2fa39d10e6a82b77', 'Mec': '20d4af90132876edf36eb9fb3e41d2650c21d3f3418952f1b4daa307bd8437e5', 'Mnich': 'e47d3173a0748a60c6a011836bc2a9a9ac87f90203bbfa9c10eba9dd8a7629ae', 'Nekromanta': '6e2fed51432758724ae1f117e39de88f150cbc421d34acabde8c069f7141cfc0', 'Paladyn': 'cf4b7910ea6919696322f43590aea3c6a4a8c0f1bfa9a4cbca19dade31cc5526', 'Psionik': '078b399a5cc3a2e1dbe15aa828e6ab9a774414f37c910f475ff15f54eac4a025', 'Samuraj': '474c1b5550faf0e800f25536d27dd631a637be4a6c8faa2a4ae196986bf475b1', 'Strażnik': '0a4c37158046a858a32598c1c9e799051fa32500a54584f8bc382094f643b7dc', 'Szaman': '84c7ee326c27febf8f447781d06406f40b320d5427431cab6fadc9c08c32e765', 'Wojownik': 'a1c6dc8bcbfcf6a4d1d543147efab98a2e42f6ac945114cf0260a840424cc99b', 'Łotrzyk': '85c00f7f7ef20e40854063ceba145903c832d7379a9f439b6ab82841109e48d7', 'Łowca': '52546b7c2677070b8f76aba6a19aeb1d6a29513a3110b31882605ab8a3e5f551'}
_NON_MECHANICAL = {'name','aliases','desc','natural_tags','pre_v1110_skill_name','legacy_display_name_v03013'}


def run_regression():
    checks = 0
    def ck(value, message):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError('NAZWY SKILLI v11.00.10: ' + message)
    ck(release_valid(VERSION, '11.00.10'), 'candidate version')
    ck(len(CLASS_SKILLS) == 22, 'all playable classes')
    ck(sum(len(rows) for rows in CLASS_SKILLS.values()) == 5461,'all skill IDs retained')
    ck(V1110_UNIQUE_SKILL_NAMES['renamed'] == 4659,'all generic mastery names replaced')
    ck(set(CLASS_SKILLS) == set(_EXPECTED_MECHANIC_SHA256),'22 unchanged class identities')
    seen_names = set()
    seen_ids = set()
    remapped = 0
    for class_name, rows in sorted(CLASS_SKILLS.items()):
        baseline = {str(s['id']):{k:v for k,v in s.items() if k not in _NON_MECHANICAL} for s in rows}
        digest = hashlib.sha256(json.dumps(baseline,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        ck(digest == _EXPECTED_MECHANIC_SHA256[class_name], class_name+' mechanics/IDs/XP/unlocks changed')
        ck(len(baseline) == len(rows), class_name+' repeated ID')
        ck(len(rows) >= 245, class_name+' lost learned skills')
        for skill in rows:
            sid = str(skill['id'])
            name = str(skill['name'])
            normalized = _canonical(name)
            ck(sid not in seen_ids, sid+' duplicate ID')
            ck(normalized not in seen_names, sid+' duplicate name '+name)
            ck(bool(normalized) and not re.search(r'\d', name), sid+' numeric/empty display')
            seen_ids.add(sid)
            seen_names.add(normalized)
            prev = skill.get('pre_v1110_skill_name')
            if prev is not None:
                remapped+=1
                aliases = {_canonical(value) for value in skill.get('aliases', [])}
                ck(_canonical(prev) in aliases, sid+' old command not retained')
                ck(normalized in aliases, sid+' new name is not a command alias')
                ck(normalized != _canonical(prev), sid+' displayed old placeholder')
                ck(not any(suffix in name for suffix in ('Żelazny Próg', 'Stalowy Szlak', 'Północny Zew', 'Pierwszy Świt')),
                   sid+' generic shared level-title remains')
                ck(bool(skill.get('kind')) and len(str(name).split())>=2, sid+' not an authored descriptive name')
                if _generated(skill):
                    kind = skill['kind']
                    if kind in ('heal','group_heal'):
                        ck(not name.startswith(('Salwa','Tarcza','Cios','Wir')), sid+' healing mislabelled as attack/guard')
                    if kind=='guard':
                        ck(not name.startswith(('Salwa','Strzał','Wir','Uderzenie')), sid+' defence mislabelled as attack')
                    if kind=='aoe_damage':
                        ck(not name.startswith(('Tarcza','Opatrunek','Medytacja')), sid+' AoE mislabelled as guard/heal')
    ck(len(seen_ids)==5461 and len(seen_names)==5461, 'full catalogue integrity')
    ck(remapped==4659,'renamed skill coverage')
    # Special Mec/UOSS authored tech IDs and IDs for early 22-class skills persist.
    for class_name, ids in (
        ('Mec', ('v0319_mec_strength_protocol','v0319_mec_magic_protocol')),
        ('Paladyn', ('v900_paladyn_1','v900_paladyn_10')),
        ('Bard', ('v900_bard_1','v900_bard_10')),
        ('Szaman', ('v900_szaman_1','v900_szaman_10')),
    ):
        real_ids = {s['id'] for s in CLASS_SKILLS[class_name]}
        for sid in ids:
            ck(sid in real_ids, class_name+' canonical authored skill '+sid)
    print(f'UNIKALNE NAZWY SKILLI v11.00.10: {checks} checks PASS; 22 klasy, 5461 skilli, 4659 nowych nazw, zachowane ID i parametry')
    return checks

if __name__ == '__main__':
    run_regression()
