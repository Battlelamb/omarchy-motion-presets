"""Motion v0.3.0 offline behavioral slices."""
import json
import os
import pathlib
import signal
import subprocess
import time
import unittest
from unittest.mock import patch
import test_backend as base

backend = base.backend
RUNTIME = base.RUNTIME


class AdvancedTests(unittest.TestCase):
    home: pathlib.Path
    env: dict[str, str]
    setUp = base.BackendTests.setUp
    cli = base.BackendTests.cli
    values = base.BackendTests.values

    def test_every_runtime_and_test_python_source_compiles_without_bytecode_writes(self):
        files=[*RUNTIME.rglob('*.py'),*(base.ROOT/'tests').glob('*.py')]
        self.assertTrue(files)
        for path in files:
            with self.subTest(path=path.name):
                compile(path.read_bytes(),str(path),'exec')

    def test_recent_storage_failure_does_not_fabricate_apply_failure(self):
        ident=backend.load_rows()[0]['id']
        with patch.dict(os.environ,self.env,clear=True),patch.object(backend.preferences,'remember',side_effect=OSError('fixture write refusal')):
            result=backend.action(ident,'apply')
        self.assertTrue(result['ok'])
        self.assertIn('warning',result['message'].lower())
        self.assertNotEqual(self.values(),self.original)
        self.assertEqual(self.cli('action','--id','restore:last','--verb','restore','--apply')[0],0)
        self.assertEqual(self.values(),self.original)

    def test_large_valid_preferences_cannot_overflow_catalog_or_hide_confirmed_action(self):
        ids=[str(i).zfill(3)+'x'*200 for i in range(512)]
        with patch.dict(os.environ,self.env,clear=True):
            prefs=backend.preferences.change(backend.SLUG,backend.PREFERENCE_SCHEMA,{})
        prefs['collections']={'group-'+str(i):ids for i in range(16)}
        # Seed a validated legacy store; normal new writes correctly reject this size.
        path=self.home/'.config/omarchy/lego'/backend.SLUG/'preferences.json'
        path.write_text(json.dumps(prefs))
        self.assertGreater(path.stat().st_size,1048576)
        with patch.dict(os.environ,self.env,clear=True):
            self.assertEqual(backend.preferences.read(backend.SLUG,backend.PREFERENCE_SCHEMA),prefs)
        code,result=self.cli('catalog')
        self.assertNotEqual(code,0)
        self.assertFalse(result['ok'])
        self.assertIn('limit',result['message'].lower())
        ident=backend.load_rows()[0]['id']
        code,result=self.cli('action','--id',ident,'--verb','apply','--apply')
        self.assertEqual(code,0,result)
        self.assertTrue(result['ok'])
        self.assertIn('warning',result['message'].lower())
        self.assertNotEqual(self.values(),self.original)
        self.assertEqual(self.cli('action','--id','restore:last','--verb','restore','--apply')[0],0)
        self.assertEqual(self.values(),self.original)

    def test_hardlinked_custom_store_is_rejected_without_modifying_other_link(self):
        code, result = self.cli('action', '--id', 'capture:current', '--verb', 'capture', '--apply', '--payload', '{"name":"Owned"}')
        self.assertEqual(code, 0, result)
        path = next((self.home / '.config').rglob('custom-presets.json'))
        other = self.home / 'other.json'
        os.link(path, other)
        saved = other.read_bytes()
        code, result = self.cli('catalog')
        self.assertNotEqual(code, 0)
        self.assertFalse(result['ok'])
        self.assertEqual(other.read_bytes(), saved)
        self.assertEqual(path.read_bytes(), saved)

    def test_json_file_reads_reject_symlinks_duplicates_and_special_files(self):
        data = self.home / 'source.json'
        data.write_text('{"valid":true}')
        link = self.home / 'link.json'
        link.symlink_to(data)
        with self.assertRaises(ValueError):
            backend.bounded_json(link)
        data.write_text('{"key":1,"key":2}')
        with self.assertRaises(ValueError):
            backend.bounded_json(data)
        fifo = self.home / 'pipe.json'
        os.mkfifo(fifo)
        with self.assertRaises(ValueError):
            backend.bounded_json(fifo)
        self.assertTrue(link.is_symlink())
        self.assertEqual(data.read_text(), '{"key":1,"key":2}')

    def test_unexpected_cli_options_fail_as_json_without_side_effects(self):
        for args in [('catalog', '--bogus'), ('catalog', '--payload', '{}'),
                     ('catalog', '--apply'), ('preferences', '--id', 'unknown'),
                     ('preferences', '--payload', '{"options":{}}'),
                     ('preferences', '--apply', '--payload', '{"recent":[]}')]:
            with self.subTest(args=args):
                code, result = self.cli(*args)
                self.assertNotEqual(code, 0)
                self.assertFalse(result['ok'])
        self.assertFalse((self.home / 'calls.jsonl').exists())
        self.assertFalse((self.home / 'state').exists())
        self.assertFalse((self.home / '.config').exists())

    def test_off_row_disables_motion_without_touching_unrelated_keys(self):
        rows={r['id']:r for r in backend.load_rows()}
        self.assertIn('off',rows)
        self.assertEqual(rows['off']['settings'],{'animations.enabled':False,'animations.workspace_wraparound':False})
        self.assertEqual(self.cli('action','--id','off','--verb','apply','--apply')[0],0)
        self.assertIs(self.values()['animations.enabled'],False)
        self.assertEqual(self.values()['unrelated'],'keep')
        self.assertEqual(self.cli('action','--id','restore:last','--verb','restore','--apply')[0],0)
        self.assertEqual(self.values(),self.original)

    def test_scalar_export_import_roundtrip_has_no_fabricated_defaults_or_ipc(self):
        code, exported = self.cli('action', '--id', 'reduced', '--verb', 'export-preset', '--apply')
        self.assertEqual(code, 0, exported)
        self.assertEqual(exported['preset']['settings'], {'animations.enabled':False})
        preset = dict(exported['preset'], name='Imported reduced')
        code, imported = self.cli('action', '--id', 'import:preset', '--verb', 'import', '--apply', '--payload', json.dumps(preset))
        self.assertEqual(code, 0, imported)
        self.assertFalse((self.home / 'calls.jsonl').exists())
        self.assertEqual(self.cli('action', '--id', imported['id'], '--verb', 'apply', '--apply')[0], 0)
        self.assertIs(self.values()['animations.enabled'], False)
        self.assertEqual(self.cli('action', '--id', 'restore:last', '--verb', 'restore', '--apply')[0], 0)
        self.assertEqual(self.values(), self.original)

    def test_timed_motion_preview_survives_killed_caller_then_keep_and_restore(self):
        script = "import runpy,json,time; b=runpy.run_path(" + repr(str(RUNTIME/'backend.py')) + "); b['action'].__globals__['TRIAL_SECONDS']=0.8; print(json.dumps(b['action']('reduced','preview')),flush=True); time.sleep(30)"
        caller = subprocess.Popen(['/usr/bin/python3','-c',script],env=self.env,stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,start_new_session=True)
        try:
            line = caller.stdout.readline()
            self.assertTrue(line, caller.stderr.read() if caller.poll() is not None else b'no result')
            self.assertTrue(json.loads(line)['ok'])
            path = next((self.home / 'state').rglob('transaction.json'))
            record = json.loads(path.read_text())
            self.assertNotEqual(os.getsid(record['watchdog_pid']), caller.pid)
            self.assertIs(self.values()['animations.enabled'], False)
            os.killpg(caller.pid, signal.SIGKILL)
            caller.communicate(timeout=2)
            limit = record['deadline'] + 3
            while path.exists() and time.monotonic() < limit:
                time.sleep(0.03)
            self.assertFalse(path.exists(), 'independent Motion watchdog did not restore')
            self.assertEqual(self.values(), self.original)
        finally:
            if caller.poll() is None:
                os.killpg(caller.pid, signal.SIGKILL)
                caller.wait(timeout=2)
            caller.stdout.close()
            caller.stderr.close()
        self.assertEqual(self.cli('action', '--id', 'reduced', '--verb', 'preview', '--apply')[0], 0)
        self.assertEqual(self.cli('action', '--id', 'reduced', '--verb', 'confirm', '--apply')[0], 0)
        path = next((self.home / 'state').rglob('transaction.json'))
        self.assertNotIn('token', json.loads(path.read_text()))
        self.assertEqual(self.cli('action', '--id', 'restore:last', '--verb', 'restore', '--apply')[0], 0)
        self.assertEqual(self.values(), self.original)

    def test_motion_capture_preserves_disabled_intent_and_preferences_reset_keeps_receipt(self):
        code, result = self.cli('preferences')
        self.assertEqual(code, 0, result)
        self.assertFalse((self.home / '.config').exists())
        self.assertEqual(result['settingsSchema'], backend.PREFERENCE_SCHEMA)
        code, captured = self.cli('action', '--id', 'capture:current', '--verb', 'capture', '--apply', '--payload', '{"name":"Normal motion"}')
        self.assertEqual(code, 0, captured)
        current = dict(self.original, **{'animations.enabled':False})
        (self.home / 'compositor.json').write_text(json.dumps(current))
        code, comparison = self.cli('action', '--id', captured['id'], '--verb', 'compare', '--apply')
        self.assertEqual(code, 0, comparison)
        self.assertFalse(any(d['key']=='animations.enabled' and d['after'] is True for d in comparison['diff']))
        code, applied = self.cli('action', '--id', captured['id'], '--verb', 'apply', '--apply')
        self.assertEqual(code, 0, applied)
        self.assertIs(self.values()['animations.enabled'], False)
        path = next((self.home / 'state').rglob('transaction.json'))
        receipt = path.read_bytes()
        self.assertEqual(self.cli('preferences', '--apply', '--payload', '{"reset":true}')[0], 0)
        self.assertEqual(path.read_bytes(), receipt)
        self.assertIn(captured['id'], [r['id'] for r in self.cli('catalog')[1]['rows']])
        self.assertEqual(self.cli('action', '--id', 'restore:last', '--verb', 'restore', '--apply')[0], 0)
        self.assertEqual(self.values(), current)
