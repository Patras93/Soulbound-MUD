# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def _make_soul_grid_skill(class_name, soul_level, name, kind):
    profile = _SOUL_GRID_CLASS_PROFILES[class_name]
    magic = bool(profile["magic"])
    skill = {
        "id": f"{profile['prefix']}_{int(soul_level)}",
        "name": name,
        "aliases": [name.lower()],
        "natural_tags": [word.lower() for word in name.split()],
        "unlock": int(soul_level),
        "kind": kind,
        "cooldown": 4,
        "mana": 0,
        "desc": (
            f"Umiejętność klasy {class_name} odblokowywana przez "
            f"Soul Level {int(soul_level)} Broni Duszy."
        ),
    }

    # Mana rośnie wraz z siłą czaru, ale fizyczne klasy pozostają bez many.
    if magic:
        skill["mana"] = max(4, 5 + int(soul_level) // 7)

    if kind == "damage":
        skill["scale"] = profile["scale"]
        skill["mult"] = round(1.18 + int(soul_level) * 0.0082, 2)
        skill["cooldown"] = min(12, 4 + int(soul_level) // 35)
    elif kind == "execute":
        skill["scale"] = profile["scale"]
        skill["mult"] = round(1.22 + int(soul_level) * 0.0078, 2)
        skill["execute_mult"] = round(min(2.0, 1.45 + int(soul_level) / float(SOUL_MAX_LEVEL)), 2)
        skill["cooldown"] = min(17, 9 + int(soul_level) // 30)
    elif kind == "drain":
        skill["scale"] = profile["scale"]
        skill["mult"] = round(1.16 + int(soul_level) * 0.0074, 2)
        skill["drain_pct"] = round(min(0.48, 0.24 + int(soul_level) / 800.0), 2)
        skill["cooldown"] = min(15, 8 + int(soul_level) // 35)
    elif kind == "boost":
        skill["boost"] = round(min(1.70, 1.20 + int(soul_level) / float(SOUL_MAX_LEVEL)), 2)
        skill["cooldown"] = min(16, 10 + int(soul_level) // 45)
        skill["duration"] = skill["cooldown"]
        skill["desc"] = (
            f"Czasowo wzmacnia wszystkie skille i spelle. Wymaga Biegłości klasy {int(soul_level)}."
        )
    elif kind == "guard":
        skill["guard"] = 10 + int(soul_level) // 3
        skill["cooldown"] = min(18, 10 + int(soul_level) // 35)
    elif kind == "evade":
        skill["cooldown"] = min(16, 9 + int(soul_level) // 40)
    elif kind == "heal":
        skill["heal_pct"] = round(min(0.52, 0.14 + int(soul_level) / 520.0), 3)
        skill["cooldown"] = min(18, 9 + int(soul_level) // 35)
    else:
        raise ValueError(f"Nieobsługiwany typ skilla progresji Soul: {kind}")

    return skill


def _v0922_alt_skill(class_name, level, variant_index, base_name, kind):
    profile = _SOUL_GRID_CLASS_PROFILES[class_name]
    magic = bool(profile["magic"])
    level = int(level)
    # Nazwa ma być jednoznaczna dla NVDA i komendy learn, ale nie może
    # udawać nowego skilla przez samo dopisanie numeru poziomu.
    name = None
    if class_name == "Wojownik":
        name = _v0244_warrior_alt_name(level, kind)
    if not name:
        name = f"{base_name} {level}"
    skill = {
        "id": f"v0922_{profile['prefix']}_{level}_{variant_index}",
        "name": name,
        "aliases": [name.lower()],
        "natural_tags": [w.lower() for w in base_name.split()],
        "unlock": level,
        "kind": kind,
        "cooldown": 10,
        "mana": (max(4, 5 + level // 12) if magic else 0),
        "desc": (
            f"Alternatywna umiejętność progu Biegłości {level} klasy {class_name}. "
            "Umiejętności z tego samego progu współdzielą cooldown wyboru."
        ),
        "mastery_choice_group": f"{class_name}:{level}",
    }
    progress = min(1.0, max(0.0, (level - 1) / float(max(1, CLASS_MASTERY_MAX_LEVEL - 1))))
    if kind in ("damage", "aoe_damage", "execute", "drain"):
        skill["scale"] = profile["scale"]
        # Alternatywy są trochę słabsze od najmocniejszego głównego skilla progu;
        # ich wartością jest inny typ działania, nie power creep.
        skill["mult"] = round(1.16 + progress * 1.75, 2)
        skill["cooldown"] = 8 if kind == "damage" else 12
    if kind == "aoe_damage":
        skill["mult"] = round(1.02 + progress * 1.40, 2)
        skill["cooldown"] = 14
    elif kind == "execute":
        skill["execute_mult"] = round(1.45 + progress * 0.35, 2)
        skill["cooldown"] = 15
    elif kind == "drain":
        skill["drain_pct"] = round(0.24 + progress * 0.14, 2)
        skill["cooldown"] = 13
    elif kind == "guard":
        skill["guard"] = 10 + int(round(progress * 110))
        skill["cooldown"] = 13
    elif kind == "evade":
        skill["cooldown"] = 13
    elif kind == "boost":
        skill["boost"] = round(1.18 + progress * 0.42, 2)
        skill["duration"] = 12
        skill["cooldown"] = 15
    elif kind == "heal":
        skill["heal_pct"] = round(0.14 + progress * 0.36, 3)
        skill["cooldown"] = 13
    elif kind == "group_heal":
        skill["heal_pct"] = round(0.10 + progress * 0.28, 3)
        skill["cooldown"] = 16
    return skill


def _v0310_build_tech_class_skills():
    levels = (1, *range(10, CLASS_MASTERY_MAX_LEVEL + 1, 10))
    mec_special = {
        1: [("Fire Beam", "damage"), ("TekShield", "guard"), ("Vent Heat", "heal")],
        10: [("Ice Beam", "damage"), ("Bolt Beam", "damage"), ("Target Lock", "boost")],
        20: [("Gravity Bomb", "aoe_damage"), ("TekBarrier", "guard"), ("Overdrive", "boost")],
        30: [("Bio Blast", "aoe_damage"), ("TekMissile", "execute"), ("Heal Force", "heal")],
        40: [("Diffuser", "aoe_damage"), ("Runic Weapon", "boost"), ("Core Meltdown", "execute")],
    }
    eng_special = {
        1: [("Auto Crossbow", "aoe_damage"), ("Mako Gun", "damage"), ("Scanner", "boost")],
        10: [("Bio Blaster", "aoe_damage"), ("Flash", "aoe_damage"), ("Debilitator", "boost")],
        20: [("Drill", "damage"), ("Napalm", "aoe_damage"), ("Launcher", "execute")],
        30: [("Noise Blaster", "aoe_damage"), ("Chainsaw", "execute"), ("Mega Bomb", "aoe_damage")],
        40: [("Air Anchor", "damage"), ("Field Repair", "heal"), ("Tool Upgrade", "boost")],
    }
    generic_mec = (("Salwa Rdzenia", "damage"), ("Pancerz Reaktywny", "guard"), ("Przeciążenie Systemów", "boost"))
    generic_eng = (("Wieżyczka Szturmowa", "damage"), ("Ładunek Taktyczny", "aoe_damage"), ("Kalibracja", "boost"))
    # v0.33.1: nie używamy już sztucznych nazw Mk-13A, Mk-14A itd.
    # Każdy próg technologiczny dostaje własny, czytelny tytuł bez cyfr.
    tech_stage_titles = (
        "Pierwszy Zapłon", "Miedziany Impuls", "Żelazny Obwód", "Stalowy Rezonans",
        "Kobaltowy Sygnał", "Srebrna Matryca", "Złoty Przekaźnik", "Runiczny Układ",
        "Kryształowy Rdzeń", "Astralna Iskra", "Próżniowy Napęd", "Eteryczna Sieć",
        "Reaktywny Pancerz", "Puls Plazmowy", "Jonowy Horyzont", "Kwantowa Brama",
        "Neuralny Splot", "Magitekowy Węzeł", "Tytanowy Obwód", "Gwiezdny Reaktor",
        "Fazowy Przekaźnik", "Chronalny Impuls", "Burzowy Kondensator", "Słoneczny Rdzeń",
        "Lunarny Moduł", "Grawitonowa Matryca", "Widmowy Układ", "Harmoniczny Napęd",
        "Pustkowy Rezonator", "Kosmiczny Obwód", "Niebiański Reaktor", "Pierwotny Węzeł",
        "Wieczny Przekaźnik", "Nieskończona Matryca", "Transcendentny Rdzeń", "Korona Maszyny",
        "Horyzont Absolutu", "Ponadczasowy Układ", "Ostateczny Rezonans", "Szczyt Techniki",
        "Absolutny Rdzeń", "Przekroczenie Obwodu", "Gwiezdny Tron Maszyny",
        "Wieczne Echo Rdzenia", "Serce Otchłani Techniki", "Korona Gwiezdnej Maszyny",
        "Sąd Horyzontu Techniki", "Nieskończony Puls Systemu", "Kosmiczna Matryca",
        "Pradawny Rezonator", "Świt Absolutnego Rdzenia", "Moduł Przeznaczenia",
        "Oko Wszechsystemu", "Wieczna Iskra Maszyny", "Transcendentny Obwód",
        "Głos Nieskończonej Sieci", "Ostateczny Horyzont Techniki", "Dusza Kosmicznej Maszyny",
        "Korona Wiecznego Rdzenia", "Apogeum Techniki", "Absolut Maszyny",
    )
    tech_stage_titles += (
        "Przebudzenie Maszyny", "Niebiański Układ", "Płomień Syntezy", "Gwiezdne Odrodzenie",
        "Wieczny Mechanizm", "Kosmiczny Pulsator", "Rdzeń Świetlistych Bram", "Astralny Przekaźnik",
        "Złote Przebudzenie", "Maszyna Przeznaczenia", "Prąd Wiecznej Ery",
        "Nieskończone Sploty", "Sąd Gigantów", "Serce Nowej Techniki",
        "Niebiański Rezonator", "Pamięć Tysiąca Światów", "Korona Nowego Nieba",
        "Pradawny Puls", "Absolutna Synteza", "Tron Żywej Maszyny",
    )
    stage_title_by_level = {level: tech_stage_titles[idx] for idx, level in enumerate(levels)}
    for cname,prefix,special,generic in (("Mec","mec",mec_special,generic_mec),("Inżynier","engineer",eng_special,generic_eng)):
        rows=[]
        for level in levels:
            specs=special.get(level)
            if specs is None:
                title = stage_title_by_level[level]
                specs=[(f"{n}: {title}", k) for n,k in generic]
            for idx,(name,kind) in enumerate(specs,1):
                rows.append(_v0310_tech_skill(cname,prefix,level,idx,name,kind))
        CLASS_SKILLS[cname]=rows


def _v03014_unique_generated_skill_names():
    renamed = 0
    old_aliases_added = 0
    level_to_title = {
        int(level): _V03014_SKILL_TITLES[idx]
        for idx, level in enumerate(_V0922_MASTERY_LEVELS)
    }
    for class_name, skills in CLASS_SKILLS.items():
        if class_name == "Wojownik":
            # v0.24.4 already gave the Warrior authored, non-numbered names.
            continue
        families = _V03014_SKILL_FAMILIES.get(class_name, {})
        for skill in skills:
            sid = str(skill.get("id", ""))
            if not sid.startswith("v0922_"):
                continue
            match = re.search(r"_(\d+)_(\d+)$", sid)
            if not match:
                continue
            original_level = int(match.group(1))
            variant_index = int(match.group(2))
            title = level_to_title.get(original_level, f"Próg {original_level}")
            kind = str(skill.get("kind", "damage"))
            family_options = families.get(kind) or families.get("damage") or (class_name,)
            family = family_options[(variant_index + original_level) % len(family_options)]
            old_name = str(skill.get("name", "")).strip()
            new_name = f"{family}: {title}"
            aliases = [str(a).strip() for a in (skill.get("aliases") or []) if str(a).strip()]
            if old_name and old_name.casefold() not in {a.casefold() for a in aliases}:
                aliases.append(old_name)
                old_aliases_added += 1
            if new_name.casefold() not in {a.casefold() for a in aliases}:
                aliases.append(new_name)
            skill["legacy_display_name_v03013"] = old_name
            skill["name"] = new_name
            skill["aliases"] = aliases
            skill["natural_tags"] = list(dict.fromkeys(
                list(skill.get("natural_tags") or []) +
                [w.lower().strip(":,—") for w in (family + " " + title).split() if w.strip(":,—")]
            ))
            renamed += 1
    return renamed, old_aliases_added


def _v03014_skill_name_audit():
    errors = []
    warnings = []
    seen_names = {}
    seen_ids = {}
    valid_kinds = {
        "damage", "aoe_damage", "execute", "drain", "boost", "guard", "evade",
        "heal", "group_heal", "passive", "utility",
    }
    per_class = {}
    numeric_names = []
    for class_name, skills in CLASS_SKILLS.items():
        per_class[class_name] = len(skills)
        for skill in skills:
            sid = str(skill.get("id", "")).strip()
            name = str(skill.get("name", "")).strip()
            kind = str(skill.get("kind", "")).strip()
            if not sid or not name:
                errors.append(f"{class_name}: skill bez id/nazwy")
                continue
            id_key = sid.casefold()
            if id_key in seen_ids:
                errors.append(f"Powtórzone ID {sid}: {seen_ids[id_key]} / {class_name}")
            else:
                seen_ids[id_key] = class_name
            name_key = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").casefold()
            name_key = re.sub(r"[^a-z0-9]+", " ", name_key).strip()
            if name_key in seen_names:
                errors.append(f"Powtórzona nazwa {name}: {seen_names[name_key]} / {class_name}")
            else:
                seen_names[name_key] = class_name
            # v0.33.1: cyfry w nazwie wyświetlanej skilla/spella są zabronione.
            # Progi i warianty należą do pól unlock/id, nie do nazwy dla gracza.
            if re.search(r"\d", name):
                numeric_names.append((class_name, name))
            if kind not in valid_kinds:
                warnings.append(f"{class_name}/{name}: nieznany kind={kind}")
            unlock = int(skill.get("unlock", 1) or 1)
            if not (1 <= unlock <= CLASS_MASTERY_MAX_LEVEL):
                errors.append(f"{class_name}/{name}: unlock poza zakresem: {unlock}")
    if numeric_names:
        errors.append(f"Pozostały numerowane nazwy: {len(numeric_names)}")
    return {
        "version": "0.35.6",
        "classes": len(CLASS_SKILLS),
        "skills": sum(per_class.values()),
        "renamed": V03014_SKILLS_RENAMED,
        "legacy_aliases_added": V03014_OLD_NAME_ALIASES,
        "legacy_aliases_preserved": sum(
            1 for _skills in CLASS_SKILLS.values() for _skill in _skills
            if _skill.get("legacy_display_name_v03013") and
            str(_skill.get("legacy_display_name_v03013")).casefold() in
            {str(_a).casefold() for _a in (_skill.get("aliases") or [])}
        ),
        "per_class": per_class,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def _all_class_skill_target_audit_v11196():
    """Target-role audit for every skill in every playable Soulbound class."""
    errors=[]
    expected_classes={
        "Wojownik","Berserker","Łotrzyk","Łowca","Mnich","Strażnik",
        "Mag","Nekromanta","Kapłan","Czarownik","Druid","Psionik",
        "Inżynier","Mec",
    }
    actual_classes=set(CLASS_SKILLS)
    if actual_classes!=expected_classes:
        errors.append(
            "playable class set mismatch: "
            f"missing={sorted(expected_classes-actual_classes)} "
            f"extra={sorted(actual_classes-expected_classes)}"
        )
    per_class={}
    total=0
    for class_name,skills in CLASS_SKILLS.items():
        per_class[class_name]=len(skills)
        total+=len(skills)
        for skill in skills:
            sid=str(skill.get("id","") or skill.get("name","?"))
            kind=str(skill.get("kind","") or "")
            expected=_TARGET_SCOPE_BY_KIND_V11196.get(kind)
            actual=str(skill.get("soulbound_kind_target_scope_v11196","") or "")
            if expected is None:
                errors.append(f"{class_name}:{sid}: unknown kind={kind}")
                continue
            if actual!=expected:
                errors.append(
                    f"{class_name}:{sid}: kind target scope={actual} expected={expected}"
                )

            # Harmful effects may never point at self/allies even when the skill
            # also deals damage or has a custom authored runtime.
            if bool(skill.get("soulbound_harmful_debuff")):
                if str(skill.get("soulbound_target_scope",""))!="enemy_only":
                    errors.append(
                        f"{class_name}:{sid}: harmful debuff must be enemy_only"
                    )

            # Healing is the inverse invariant: never heal a hostile mob.
            if kind in {"heal","group_heal","regen"}:
                if bool(skill.get("soulbound_harmful_debuff")):
                    errors.append(
                        f"{class_name}:{sid}: healing skill cannot be harmful debuff"
                    )
                if str(skill.get("soulbound_target_scope",""))=="enemy_only":
                    errors.append(
                        f"{class_name}:{sid}: healing skill cannot be enemy_only"
                    )

    return {
        "version":"1.11.96",
        "classes":len(CLASS_SKILLS),
        "skills":total,
        "per_class":per_class,
        "error_count":len(errors),
        "errors":errors,
    }


def _priest_healing_contract_audit_v11196():
    rows = {
        str(skill.get("id", "")): skill
        for skill in CLASS_SKILLS.get("Kapłan", ())
        if str(skill.get("kind", "")) in {"heal", "group_heal", "regen"}
    }
    errors = []

    regen = rows.get("priest_regen")
    if not regen:
        errors.append("priest_regen: missing")
    else:
        if int(regen.get("unlock", 0) or 0) != 1:
            errors.append("priest_regen: Reqs None must map to Biegłość Kapłana 1")
        if int(regen.get("source_ap_cost", 0) or 0) != 300:
            errors.append("priest_regen: Base AP 300 must remain learning points")
        if str(regen.get("source_ap_semantics", "")) != "learning_points":
            errors.append("priest_regen: AP semantics must be learning_points")
        if list(regen.get("source_target_mode") or []) != ["self", "one_ally"]:
            errors.append("priest_regen: target must remain Self/One Ally")
        if list(regen.get("source_stat_influence") or []) != ["will"]:
            errors.append("priest_regen: Stat Influence must remain Will")
        if list(regen.get("source_properties") or []) != [
            "dispelable", "extendable", "reflectable", "silenceable"
        ]:
            errors.append("priest_regen: source Properties mismatch")
        if str(regen.get("level_effect", "")) != "increases_duration":
            errors.append("priest_regen: Level Effect must increase Duration")

    wind = rows.get("priest_healing_wind")
    if not wind:
        errors.append("priest_healing_wind: missing")
    else:
        if int(wind.get("unlock", 0) or 0) != 1:
            errors.append("priest_healing_wind: Reqs None must map to Biegłość Kapłana 1")
        if int(wind.get("source_ap_cost", 0) or 0) != 1500:
            errors.append("priest_healing_wind: Base AP 1500 must remain learning points")
        if str(wind.get("source_ap_semantics", "")) != "learning_points":
            errors.append("priest_healing_wind: AP semantics must be learning_points")
        if int(wind.get("mana", 0) or 0) != 60:
            errors.append("priest_healing_wind: MP cost must remain 60")
        if str(wind.get("source_target_mode", "")) != "all_allies":
            errors.append("priest_healing_wind: target must remain All Allies")
        if list(wind.get("source_stat_influence") or []) != ["will"]:
            errors.append("priest_healing_wind: Stat Influence must remain Will")
        if list(wind.get("source_properties") or []) != ["multicastable", "silenceable"]:
            errors.append("priest_healing_wind: source Properties mismatch")
        if str(wind.get("level_effect", "")) != "increases_healing_power":
            errors.append("priest_healing_wind: Level Effect must increase Healing Power")
        if wind.get("heal_pct") is not None:
            errors.append("priest_healing_wind: no invented source healing percentage allowed")

    for sid, row in rows.items():
        kind = str(row.get("kind", ""))
        if kind == "heal":
            if str(row.get("target_mode", "")) != "self_or_one_ally":
                errors.append(f"{sid}: single heal target must be self_or_one_ally")
            if not bool(row.get("soulbound_enemy_heal_disabled")):
                errors.append(f"{sid}: enemy healing must remain disabled")
        elif kind == "group_heal":
            if str(row.get("target_mode", "")) != "local_party":
                errors.append(f"{sid}: group heal target must be local_party")
            if not bool(row.get("soulbound_enemy_heal_disabled")):
                errors.append(f"{sid}: enemy healing must remain disabled")

    return {
        "version": "1.11.96",
        "checked": len(rows),
        "ids": sorted(rows),
        "error_count": len(errors),
        "errors": errors,
    }


def _all_class_endgame_damage_audit_v11196():
    errors = []
    report = {}
    endgame_unlock = min(180, CLASS_MASTERY_MAX_LEVEL)
    for class_name, allowed_scales in _CLASS_OFFENSIVE_SCALES_V11196.items():
        skills = tuple(CLASS_SKILLS.get(class_name, ()))
        offensive = [
            skill for skill in skills
            if str(skill.get("kind", "")) in _ENDGAME_OFFENSIVE_KINDS_V11196
        ]
        endgame = [
            skill for skill in offensive
            if int(skill.get("unlock", 1) or 1) >= endgame_unlock
        ]
        if not offensive:
            errors.append(f"{class_name}: brak ofensywnych umiejętności")
        if not endgame:
            errors.append(
                f"{class_name}: brak ofensywnej umiejętności endgame od Biegłości {endgame_unlock}"
            )
        bad = []
        for skill in endgame:
            scale = str(skill.get("scale", "") or "").strip().lower()
            if not scale:
                bad.append(f"{skill.get('name', skill.get('id', '?'))}: brak scale")
                continue
            if scale not in allowed_scales:
                bad.append(
                    f"{skill.get('name', skill.get('id', '?'))}: scale={scale}, "
                    f"dozwolone={sorted(allowed_scales)}"
                )
        if bad:
            errors.extend(f"{class_name}: {row}" for row in bad)
        report[class_name] = {
            "offensive": len(offensive),
            "endgame": len(endgame),
            "allowed_scales": tuple(sorted(allowed_scales)),
            "top_unlock": max((int(skill.get("unlock", 1) or 1) for skill in offensive), default=0),
        }
    return {
        "version": "1.11.96",
        "classes": len(_CLASS_OFFENSIVE_SCALES_V11196),
        "report": report,
        "error_count": len(errors),
        "errors": errors,
    }


def all_class_gamefeel_audit_v11330():
    """One final mechanical report over every active class and every skill.

    This audit is diagnostic and consumed by predeploy. It intentionally does
    not raise at module import, so a report-format regression cannot take the
    production server down after deployment.
    """
    errors = []
    report = {}
    expected_classes = {str(row[0]) for row in CLASSES}
    actual_classes = set(CLASS_SKILLS)
    if actual_classes != expected_classes:
        errors.append(
            "class roster mismatch: "
            f"expected={sorted(expected_classes)}, actual={sorted(actual_classes)}"
        )

    known_kinds = {
        "damage", "aoe_damage", "execute", "drain", "boost", "guard", "evade",
        "heal", "group_heal", "regen", "passive", "utility", "support",
    }
    offensive_kinds = {"damage", "aoe_damage", "execute", "drain"}
    technology_classes = {"Mec", "Inżynier"}

    for class_name in sorted(expected_classes):
        rows = list(CLASS_SKILLS.get(class_name, ()))
        class_errors = []
        ids = set()
        offensive = []
        endgame = []
        signatures = []
        passive_count = 0
        heal_count = 0
        harmful_count = 0

        for skill in rows:
            sid = str(skill.get("id", "") or "").strip()
            name = str(skill.get("name", sid) or sid)
            kind = str(skill.get("kind", "") or "").strip().lower()
            if not sid:
                class_errors.append("skill without id")
                continue
            if sid in ids:
                class_errors.append(f"{sid}: duplicate id")
            ids.add(sid)
            if kind not in known_kinds:
                class_errors.append(f"{sid}: unknown kind={kind}")

            try:
                unlock = int(skill.get("unlock", 1) or 1)
            except (TypeError, ValueError, OverflowError):
                unlock = 0
            if not 1 <= unlock <= CLASS_MASTERY_MAX_LEVEL:
                class_errors.append(f"{sid}: unlock out of range={unlock}")

            try:
                cooldown = int(skill.get("cooldown", 0) or 0)
            except (TypeError, ValueError, OverflowError):
                cooldown = -1
            if not 0 <= cooldown <= 60:
                class_errors.append(f"{sid}: cooldown out of 0..60={cooldown}")

            try:
                mana = int(effective_skill_mana_cost(skill, class_name))
            except Exception:
                mana = -1
            if mana < 0:
                class_errors.append(f"{sid}: negative/invalid mana={mana}")

            if kind == "passive":
                passive_count += 1
                if cooldown != 0:
                    class_errors.append(f"{sid}: passive has cooldown={cooldown}")
                if not bool(skill.get("automatic")):
                    class_errors.append(f"{sid}: passive is not automatic")

            if kind in {"heal", "group_heal", "regen"}:
                heal_count += 1
                if str(skill.get("soulbound_target_scope", "")) == "enemy_only":
                    class_errors.append(f"{sid}: heal targets enemy")

            if bool(skill.get("soulbound_harmful_debuff")):
                harmful_count += 1
                if str(skill.get("soulbound_target_scope", "")) != "enemy_only":
                    class_errors.append(f"{sid}: harmful debuff is not enemy_only")

            if kind in offensive_kinds:
                offensive.append(skill)
                if unlock >= min(180, CLASS_MASTERY_MAX_LEVEL):
                    endgame.append(skill)
                scale = str(skill.get("scale", "") or "").strip().lower()
                # Mec/Engineer have several exact-source custom branches whose
                # runtime power can be defined by base_power/source contracts.
                if class_name not in technology_classes and not scale:
                    class_errors.append(f"{sid}: offensive skill without scale")
                try:
                    mult = float(skill.get("mult", 0.0) or 0.0)
                except (TypeError, ValueError, OverflowError):
                    mult = 0.0
                try:
                    execute = float(skill.get("execute_mult", 1.0) or 1.0)
                except (TypeError, ValueError, OverflowError):
                    execute = 1.0
                impact = mult * max(1.0, execute)
                if (
                    (class_name in technology_classes and unlock >= 180)
                    or impact >= 2.20
                ):
                    signatures.append(sid)

        if not rows:
            class_errors.append("no skills")
        if not offensive:
            class_errors.append("no offensive skills")
        if not endgame:
            class_errors.append("no offensive endgame skill >= mastery 180")
        if not signatures:
            class_errors.append("no signature o-kurde offensive skill")

        report[class_name] = {
            "skills": len(rows),
            "offensive": len(offensive),
            "endgame_offensive": len(endgame),
            "signature_offensive": len(signatures),
            "passives": passive_count,
            "heals": heal_count,
            "harmful_debuffs": harmful_count,
            "errors": tuple(class_errors),
        }
        errors.extend(f"{class_name}: {row}" for row in class_errors)

    # Reuse the detailed specialist audits rather than duplicating their
    # source-specific knowledge here.
    for label, result in (
        ("targets", ALL_CLASS_SKILL_TARGET_AUDIT_V11196),
        ("healing", CLASS_HEALING_SCALE_AUDIT_V11196),
        ("harmful_debuffs", HARMFUL_DEBUFF_TARGET_AUDIT_V11196),
        ("endgame_damage", ALL_CLASS_ENDGAME_DAMAGE_AUDIT_V11196),
        ("mec", MEC_CONTRACT_AUDIT_V11149),
        ("engineer", ENGINEER_AP_SEMANTICS_AUDIT_V11196),
    ):
        for error in result.get("errors", ()):
            errors.append(f"{label}: {error}")

    return {
        "version": "1.13.30",
        "class_count": len(expected_classes),
        "skill_count": sum(len(v) for v in CLASS_SKILLS.values()),
        "automatic_passives_normalized": V11330_AUTOMATIC_PASSIVES_NORMALIZED,
        "report": report,
        "error_count": len(errors),
        "errors": errors,
    }

