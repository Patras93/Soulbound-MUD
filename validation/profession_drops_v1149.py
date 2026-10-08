"""Drop-rate contract for v1.14.9; never touches player state or SQLite."""


def audit_profession_drops_v1149():
    from core.profession_drop_rates_v1149 import (
        resource_variant_chances_v1149, mining_vein_chances_v1149,
        mined_gem_quality_chances_v1149, mining_geode_chances_v1149,
    )
    errors = []
    checks = 0
    for category, premium in (("fish", "ancient"), ("wood", "legendary"), ("herb", "legendary")):
        early = resource_variant_chances_v1149(category, 1, 1, 1)
        advanced = resource_variant_chances_v1149(category, 600, 600, 600)
        wrong_prof = resource_variant_chances_v1149(category, 600, 1, 600)
        wrong_material = resource_variant_chances_v1149(category, 600, 600, 1)
        checks += 5
        if early.get(premium, 0) or wrong_prof.get(premium, 0) or wrong_material.get(premium, 0):
            errors.append(f"{category}: premium before unlock")
        if not (0 < advanced.get(premium, 0) < 0.002):
            errors.append(f"{category}: premium probability too high / missing")
        if not (0 < sum(advanced.values()) < 0.10):
            errors.append(f"{category}: total variants exceed 10%")
    for level in (1, 100, 200, 400, 600):
        for cat in ("fish", "wood", "herb"):
            rates = resource_variant_chances_v1149(cat, level, level, level)
            checks += 1
            if sum(rates.values()) >= 0.15 or any(not 0 <= v <= 1 for v in rates.values()):
                errors.append(f"{cat}/{level}: impossible rates")
    mine_low = mining_vein_chances_v1149(1, 1, 1)
    mine_weak_prof = mining_vein_chances_v1149(600, 1, 600)
    mine_shallow = mining_vein_chances_v1149(600, 600, 1)
    mine_no_floor = mining_vein_chances_v1149(600, 600, None)
    mine_high = mining_vein_chances_v1149(600, 600, 600)
    checks += 5
    if any(r['legendary'] for r in (mine_low, mine_weak_prof, mine_shallow, mine_no_floor)):
        errors.append("legendary mine without eligibility")
    if not (0.005 < mine_high['legendary'] < 0.008):
        errors.append("legendary mining chance should be under 0.8%")
    if abs(sum(mine_high.values()) - 1.0) > 1e-9:
        errors.append("mining probabilities do not sum to one")
    for tool, prof in ((1, 600), (600, 1), (600, 600)):
        rates = mined_gem_quality_chances_v1149(tool, prof)
        checks += 1
        if abs(sum(rates.values()) - 1.0) > 1e-9:
            errors.append("gem quality probabilities do not sum to one")
        if min(tool, prof) == 1 and rates['perfect']:
            errors.append("perfect gem without both levels")
    if mined_gem_quality_chances_v1149(600, 600)['perfect'] >= 0.01:
        errors.append("perfect gem too common")
    checks += 1
    for stage, floor in ((1, 1), (80, 60), (600, 600)):
        rates = mining_geode_chances_v1149(stage, stage, floor)
        checks += 1
        if sum(rates.values()) > 0.04:
            errors.append("too many geodes")
        if stage == 1 and rates:
            errors.append("beginner geodes")
        if stage == 80 and 'astral_geode' in rates:
            errors.append("early astral geode")
    if mining_geode_chances_v1149(600, 600, 600).get('astral_geode', 1) >= 0.002:
        errors.append("astral geode too common")
    checks += 1
    return {"checks": checks, "errors": errors, "error_count": len(errors)}


if __name__ == "__main__":
    result = audit_profession_drops_v1149()
    print(f"PROFESSION DROP AUDIT v1.14.9: {result['checks']} checks; {result['error_count']} errors")
    for error in result['errors']:
        print("DROP ERROR:", error)
    raise SystemExit(1 if result['error_count'] else 0)
