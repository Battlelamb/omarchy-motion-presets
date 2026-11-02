"""Recovery controls for the new scalar-motion preview path; no live IPC."""
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


class MotionControls(unittest.TestCase):
    setUp = base.BackendTests.setUp
    cli = base.BackendTests.cli
    values = base.BackendTests.values

    def test_preview_external_edit_is_not_overwritten_after_timeout(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(backend, 'TRIAL_SECONDS', 0.6):
            backend.action('reduced', 'preview')
        path = next((self.home / 'state').rglob('transaction.json'))
        saved = path.read_bytes()
        edited = dict(self.values(), **{'animations.workspace_wraparound':True})
        (self.home / 'compositor.json').write_text(json.dumps(edited))
        time.sleep(1.8)
        self.assertEqual(self.values(), edited)
        self.assertEqual(path.read_bytes(), saved)
        self.assertNotEqual(self.cli('action', '--id', 'restore:last', '--verb', 'restore', '--apply')[0], 0)
        edited['animations.workspace_wraparound'] = False
        (self.home / 'compositor.json').write_text(json.dumps(edited))
        self.assertEqual(self.cli('action', '--id', 'restore:last', '--verb', 'restore', '--apply')[0], 0)
        self.assertEqual(self.values(), self.original)

    def test_group_kill_at_pending_switch_preserves_original_preview_authority(self):
        script = '''import runpy,json,os,time
from pathlib import Path
b=runpy.run_path(SOURCE)
g=b['action'].__globals__
g['TRIAL_SECONDS']=1.0
b['action']('reduced','preview')
p=next(Path(os.environ['XDG_STATE_HOME']).rglob('transaction.json'))
original=json.loads(p.read_text())
real=g['save']
def save(directory,record):
    real(directory,record)
    if record['phase']=='pending':
        Path(os.environ['HOME'],'paused.json').write_text(json.dumps({'original':original,'pending':record}))
        time.sleep(30)
g['save']=save
b['action']('wraparound','preview')
'''.replace('SOURCE', repr(str(RUNTIME/'backend.py')))
        caller = subprocess.Popen(['/usr/bin/python3','-c',script],env=self.env,
                                  stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:
            marker = self.home/'paused.json'
            limit=time.monotonic()+4
            while not marker.exists() and caller.poll() is None and time.monotonic()<limit:
                time.sleep(.01)
            self.assertTrue(marker.exists())
            evidence=json.loads(marker.read_text())
            for key in ('token','deadline','watchdog_pid'):
                self.assertEqual(evidence['pending'][key], evidence['original'][key])
            os.killpg(caller.pid, signal.SIGKILL)
            out,err=caller.communicate(timeout=2)
            self.assertEqual((caller.returncode,out,err),(-9,b'',b''))
            path=next((self.home/'state').rglob('transaction.json'))
            limit=evidence['original']['deadline']+3
            while path.exists() and time.monotonic()<limit:
                time.sleep(.02)
            self.assertFalse(path.exists())
            self.assertEqual(self.values(),self.original)
        finally:
            if caller.poll() is None:
                os.killpg(caller.pid,signal.SIGKILL)
                caller.wait(timeout=2)
            caller.stdout.close()
            caller.stderr.close()

    def test_lost_compensation_ack_preserves_durable_pending_and_timed_recovery(self):
        for after_replace in (False, True):
            with self.subTest(after_replace=after_replace):
                self.setUp()
                with patch.dict(os.environ,self.env,clear=True),patch.object(backend,'TRIAL_SECONDS',1.0):
                    backend.action('reduced','preview')
                    path=next((self.home/'state').rglob('transaction.json'))
                    old=json.loads(path.read_text())
                    real_save,real_write=backend.save,backend.write_value
                    compensating=[False]
                    def save(directory,record):
                        if record['phase']=='active' and not compensating[0]:
                            compensating[0]=True
                            if after_replace:
                                real_save(directory,record)
                            raise OSError('active publication failure')
                        return real_save(directory,record)
                    def write(key,value,expected):
                        result=real_write(key,value,expected)
                        if compensating[0]:
                            raise ValueError('acknowledgement lost after compensation')
                        return result
                    with patch.object(backend,'save',save),patch.object(backend,'write_value',write):
                        with self.assertRaisesRegex(ValueError,'retained'):
                            backend.action('wraparound','preview')
                pending=json.loads(path.read_text())
                self.assertEqual(pending['phase'],'pending')
                self.assertEqual(pending['previous'],old['expected'])
                self.assertEqual(pending['before'],old['before'])
                self.assertNotEqual(pending['token'],old['token'])
                limit=pending['deadline']+3
                while path.exists() and time.monotonic()<limit:
                    time.sleep(.02)
                self.assertFalse(path.exists())
                self.assertEqual(self.values(),self.original)
