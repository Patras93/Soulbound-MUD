# -*- coding: utf-8 -*-
import builtins
import os
import unittest
from unittest.mock import patch
from systems.v115 import optional_sound


class SoundpackOptionalTests(unittest.TestCase):
    def test_disabled_is_noop(self):
        with patch.dict(os.environ, {'SOULBOUND_SOUND_EVENTS': '0'}):
            self.assertIsNone(optional_sound._event('LEVEL_UP'))
            self.assertIsNone(optional_sound.record_paid_exp_event_v11329(None, 1, 9, 10))
            self.assertIsNone(optional_sound.sound_reward_queue_checkpoint_v11329(None, 1))
            optional_sound.sound_reward_queue_rollback_v11329(None, 1, None)
            class Session: pass
            optional_sound.install_sound_hooks_v1208(Session)
            self.assertFalse(hasattr(Session, '_sound_hooks_installed_v1208'))

    def test_missing_audio_module_is_noop(self):
        original = builtins.__import__
        def deny(name, *args, **kwargs):
            if name == 'systems.sound_events_v1208' or (name == 'systems' and args and 'sound_events_v1208' in args[2]):
                raise ModuleNotFoundError("No module named 'systems.sound_events_v1208'", name='systems.sound_events_v1208')
            return original(name, *args, **kwargs)
        with patch.dict(os.environ, {'SOULBOUND_SOUND_EVENTS':'1'}), patch('builtins.__import__', side_effect=deny):
            self.assertIsNone(optional_sound._event('LEVEL_UP'))
            self.assertIsNone(optional_sound.record_paid_exp_event_v11329(None, 1, 9, 10))
            self.assertIsNone(optional_sound.sound_reward_queue_checkpoint_v11329(None, 1))
            class Session: pass
            optional_sound.install_sound_hooks_v1208(Session)

    def test_default_preserves_existing_transport(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(optional_sound._event('LEVEL_UP'), 'SOUND_EVENT LEVEL_UP')

    def test_core_imports_go_through_adapter(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        for name in ('player/session.py','systems/experience_bank_v2011.py',
                     'systems/manual_exp_bank_v11325.py','systems/atomic_progression_rewards_v10400.py',
                     'systems/atomic_character_experience_v10400.py',
                     'player/session_mixins/achievement_xp_v11331.py',
                     'player/session_mixins/social_expansion.py'):
            self.assertNotIn('from systems.sound_events_v1208 import', (root/name).read_text(encoding='utf8'), name)

if __name__ == '__main__': unittest.main()
