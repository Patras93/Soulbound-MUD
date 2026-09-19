# -*- coding: utf-8 -*-
"""Soulbound v0.31.14 Full Crafting Audit 2.0 + HELP refresh."""
def full_crafting_audit_v03114():
    errors=[]; warnings=[]
    tables={"craft":CRAFT_RECIPES,"cook":COOK_RECIPES,"alchemy":ALCHEMY_RECIPES,"jewel":JEWELCRAFT_RECIPES}
    outputs=set(); ingredients=set()
    for tname,table in tables.items():
        for rid,r in table.items():
            out=r.get('output')
            if out not in ITEMS: errors.append(f"{tname}:{rid} missing output {out}")
            else: outputs.add(out)
            if not r.get('stations'): errors.append(f"{tname}:{rid} no station")
            for iid,q in (r.get('ingredients') or {}).items():
                ingredients.add(iid)
                if iid not in ITEMS: errors.append(f"{tname}:{rid} missing ingredient {iid}")
                if int(q or 0)<=0: errors.append(f"{tname}:{rid} bad qty {iid}:{q}")
    # Every direct blacksmith ore conversion must remain 1 -> 1.
    smelts=0
    for tier in BLACKSMITH_TIERS:
        r=CRAFT_RECIPES.get(tier['ingot'])
        if not r: continue
        smelts+=1
        if r.get('ingredients')!={tier['ore']:1} or int(r.get('quantity',1))!=1:
            errors.append(f"smelt not 1:1 {tier['ingot']}: {r.get('ingredients')} -> {r.get('quantity')}")
    # Salvage fallbacks must point to usable ingot outputs.
    for out,rid in SALVAGE_SMELT_FALLBACK_V03113.items():
        r=CRAFT_RECIPES.get(rid)
        if not r: errors.append(f"salvage fallback missing {out}:{rid}")
        elif r.get('output')!=out: errors.append(f"salvage fallback output mismatch {rid}")
    # New systems.
    if len(SALVAGE3_V03114)<8: errors.append('Salvage 3.0 too small')
    if len(_REFINED)<4: errors.append('Refining 2.0 incomplete')
    for sid,rows in TECH_SET_ITEMS_V03114.items():
        if len(rows)!=8: errors.append(f"tech set {sid} has {len(rows)}/8")
        for iid in rows:
            if iid not in ITEMS: errors.append(f"tech set item missing {iid}")
    for key in V0925_RUNES:
        if key not in RUNE_CRAFT_COSTS_V03114: warnings.append(f"rune has legacy dust-only recipe: {key}")
    # Find craft materials with no recipe input/output/salvage/rune use; warnings only, because quest-only materials can be valid.
    used=set(outputs)|ingredients|set(SALVAGE3_V03114)|set(TECH_SALVAGE_RECIPES)
    for outs in SALVAGE3_V03114.values(): used.update(outs)
    for outs in TECH_SALVAGE_RECIPES.values(): used.update(outs)
    used.update(iid for iid,_name in V0925_SALVAGE_MATERIALS.values())
    for costs in RUNE_CRAFT_COSTS_V03114.values(): used.update(costs)
    dead=[]
    for iid,item in ITEMS.items():
        if item.get('type')=='craft_material' and iid not in used and iid not in V0925_RUNE_BY_ID:
            dead.append(iid)
    return {"version":"0.31.14","error_count":len(errors),"warning_count":len(warnings),"errors":errors,"warnings":warnings,
            "recipes":sum(len(x) for x in tables.values()),"craft_recipes":len(CRAFT_RECIPES),"smelts_1to1_checked":smelts,
            "salvage3":len(SALVAGE3_V03114),"refining":len(_REFINED),"tech_sets":len(TECH_SET_ITEMS_V03114),
            "tech_set_pieces":sum(len(x) for x in TECH_SET_ITEMS_V03114.values()),"runes":len(V0925_RUNES),"dead_material_candidates":dead}

FULL_CRAFTING_AUDIT_V03114=full_crafting_audit_v03114()
if FULL_CRAFTING_AUDIT_V03114['error_count']:
    raise RuntimeError('Full Crafting Audit 2.0 failed: '+'; '.join(FULL_CRAFTING_AUDIT_V03114['errors'][:30]))

HELP_TOPICS['crafting_03114']=[
    'FORGE & MATERIALS 3.0: Salvage 3.0, Refining 2.0, Forge +1..+10, Tech EQ Sety, Socket Crafting, Rune Crafting i V-MAX Upgrade Path.',
    'Konwersje materiałów: konwersje / materialconversion.',
    'Przetop hurtowy: przetop max <metal>; przetop wszystko zużywa wyłącznie materiały Salvage z odpowiednikiem sztabki.',
    'Craft hurtowy: craft max <receptura>. Każda sztuka nadal jest osobną akcją craftingu i daje normalny progres.',
    'Refining: refine pokazuje Hartowaną Stal, Stop Magitek, Astralny Stop i Stop Eternium.',
    'Socket Crafting: najpierw wykuj Rdzeń Gniazda, potem socketcraft <EQ>. Maksymalnie +2 trwałe gniazda na dany przedmiot.',
    'Rune Crafting: runy stworz <typ> wykorzystuje Pył Runiczny oraz klejnot albo materiał technologiczny zależnie od runy.',
    'Tech sety: techsety. Mec, Inżynier i Cyborg mają po 8 części z progami 2/4/6/8.',
    'V-MAX: vmaxupgrade duration maks. 3 poziomy po +10 s; vmaxupgrade cooling maks. 2 poziomy po -8 s Overheat.',
]
for alias in ('forge3','salvage3','refining2','socketcraft','runecrafting','techsety','vmaxupgrade','konwersje','przetop max','craft max'):
    HELP_TOPIC_ALIASES[normalize_lookup_text(alias)]='crafting_03114'
