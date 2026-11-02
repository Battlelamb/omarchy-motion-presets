"""Preference-only motion defaults; no host IPC is admitted by configuration."""
import json
import os
import pathlib
import unittest
from unittest.mock import patch
import test_backend as base
backend=base.backend


class ConfigurationTests(unittest.TestCase):
    home: pathlib.Path
    env: dict
    original: dict
    setUp=base.BackendTests.setUp
    cli=base.BackendTests.cli
    values=base.BackendTests.values

    def test_preview_primary_is_saved_without_setters_and_default_remains_apply(self):
        with patch.dict(os.environ,self.env,clear=True), patch.object(backend,'run_hypr',side_effect=AssertionError('configuration must not call IPC')):
            initial=backend.catalog()
            self.assertEqual(initial['preferences']['options']['primaryAction'],'apply')
            self.assertIn('preview',initial['actions'])
            result=backend.preference_command({'options':{'primaryAction':'preview'}},True)
            self.assertEqual(result['preferences']['options']['primaryAction'],'preview')
            current=backend.catalog()
            self.assertIn(current['preferences']['options']['primaryAction'],current['actions'])
            self.assertEqual(current['actions'],initial['actions'])
            backend.preference_command({'reset':True},True)
            self.assertEqual(backend.catalog()['preferences']['options']['primaryAction'],'apply')
        self.assertEqual(self.values(),self.original)
        self.assertFalse((self.home/'state').exists())
        self.assertFalse((self.home/'calls.jsonl').exists())

    def test_invalid_primary_values_preserve_preferences_without_ipc(self):
        with patch.dict(os.environ,self.env,clear=True),patch.object(backend,'run_hypr',side_effect=AssertionError('configuration must not call IPC')):
            backend.preference_command({'options':{'primaryAction':'preview'}},True)
            path=self.home/'.config/omarchy/lego/motion-presets/preferences.json'
            saved=path.read_bytes()
            for value in [True,0,None,[],{},'confirm','preview\n']:
                with self.assertRaises(ValueError):
                    backend.preference_command({'options':{'primaryAction':value}},True)
                self.assertEqual(path.read_bytes(),saved)
            legacy=json.loads(saved)
            del legacy['options']['primaryAction']
            path.write_text(json.dumps(legacy))
            self.assertEqual(backend.catalog()['preferences']['options']['primaryAction'],'apply')
        self.assertFalse((self.home/'calls.jsonl').exists())
        self.assertFalse((self.home/'state').exists())
