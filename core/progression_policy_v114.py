"""Apply release-owned, immutable progression caps after the static catalog builds."""
from core import live_level_caps_v5200 as policy
PROGRESSION_KEYS=policy.PROGRESSION_KEYS
ENHANCEMENT_CAP=10

def install_deploy_policy():
    if policy.current()!={**dict.fromkeys(PROGRESSION_KEYS,None),'ulepszenia_eq':10}:
        raise RuntimeError('Rozwoj jest ustalany w kodzie wydania, nie w sesji.')
    policy._apply_to_runtime()
    return policy.current()
