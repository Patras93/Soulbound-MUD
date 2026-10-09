# -*- coding: utf-8 -*-
"""Ultra-rare ordinary-monster variants; reuse existing elite reward pipeline."""
import copy
import random
from systems.elite_variants import elite_eligible_template_v11338, elite_source_template_id_v11338

TIERS = {'legendary': ('Legendarny', 2.65, 2.2, 1.65, 1.16),
         'mythic': ('Mityczny', 4.10, 3.5, 2.2, 1.30)}

def legendary_roll_v1250(template, rng=None):
    if not elite_eligible_template_v11338(template): return ''
    rng = rng or random
    chance = rng.random()
    # Harder variants stay rare and do not replace manually-authored bosses.
    if chance < .003: return 'mythic'
    if chance < .018: return 'legendary'
    return ''

def legend_variant_id_v1250(source_id, rank):
    return f'{source_id}__v1250_{rank}'

def build_legendary_v1250(source_id, template, rank):
    if rank not in TIERS or not elite_eligible_template_v11338(template):
        raise ValueError('Invalid legendary monster')
    label, reward, drop, hp, dmg = TIERS[rank]
    clone = copy.deepcopy(template)
    clone['name'] = f"{label} {template.get('name', source_id)}"
    clone['rank'] = 'rare' if rank == 'legendary' else 'elite'
    clone['elite'] = True
    # Different existing monster AI techniques, not merely larger damage numbers.
    affixes = ('storm','vampiric','cursed')
    clone['elite_affix'] = affixes[sum(str(source_id).encode('utf-8')) % len(affixes)] if rank == 'mythic' else 'armored'
    clone['attack_elements_v11339'] = ('dark',) if rank == 'mythic' else ('lightning',)
    clone['elite_legend_rank_v1250'] = rank
    clone['elite_source_template_v11338'] = str(source_id)
    clone['elite_base_template'] = str(template.get('elite_base_template') or template.get('base_template') or source_id)
    clone['elite_reward_multiplier_v11338'] = reward
    clone['elite_drop_multiplier_v11338'] = drop
    clone['elite_hp_multiplier_v11338'] = hp
    clone['elite_damage_multiplier_v11338'] = dmg
    # Rare material drop is handled by the normal corpse loot pipeline.
    drops = dict(clone.get('drops') or {})
    drops['v12812_mythic_heart' if rank == 'mythic' else 'v12812_legendary_seal'] = (0.27 if rank == 'mythic' else 0.12)
    clone['drops'] = drops
    return clone
