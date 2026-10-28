"""Real-process resilience probes. No production code is changed."""
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EDITORIAL = BASE


def subprocess_environment():
    env = os.environ.copy()
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(EDITORIAL) + (os.pathsep + current if current else "")
    )
    return env


class OperationalResilience(unittest.TestCase):
    def test_real_concurrent_noreplace(self):
        with tempfile.TemporaryDirectory(prefix='xientia-r2-race-') as td:
            root=Path(td); destination=root/'published'; workers=[]
            script='''import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from atomic_publish import publish_noreplace
root=Path(sys.argv[2]); idx=sys.argv[3]
source=root/('stage-'+idx);source.mkdir()
(source/'owner').write_text(idx)
ready=root/('ready-'+idx);ready.touch()
while not (root/'go').exists():time.sleep(.01)
try:
 publish_noreplace(source,root/'published')
 print('WIN',flush=True)
except FileExistsError:
 print('LOSE',flush=True)
'''
            try:
                for i in ('a','b'):
                    workers.append(subprocess.Popen([sys.executable,'-c',script,str(EDITORIAL),td,i],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=subprocess_environment()))
                deadline=time.monotonic()+10
                while not all((root/('ready-'+i)).exists() for i in ('a','b')):
                    self.assertLess(time.monotonic(),deadline,'Workers did not become ready')
                    time.sleep(.02)
                (root/'go').touch()
                results=[p.communicate(timeout=10) for p in workers]
                self.assertEqual([p.returncode for p in workers],[0,0],results)
                self.assertEqual(sorted(x.strip() for x,_ in results),['LOSE','WIN'])
                self.assertIn((destination/'owner').read_text(),('a','b'))
                self.assertEqual(len(list(destination.iterdir())),1)
            finally:
                for p in workers:
                    if p.poll() is None:p.kill();p.wait()

    def test_real_renderer_failure_does_not_publish(self):
        with tempfile.TemporaryDirectory(prefix='xientia-r2-fail-') as td:
            root=Path(td)
            script='''import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from validated_publish import run_supervised
run_supervised([sys.executable,'-c',"import sys;sys.exit(17)"])
'''
            p=subprocess.run([sys.executable,'-c',script,str(EDITORIAL)],capture_output=True,text=True,timeout=10,env=subprocess_environment())
            self.assertNotEqual(p.returncode,0)
            self.assertIn('CalledProcessError',p.stderr)
            self.assertFalse((root/'published').exists())

    def test_real_interrupt_kills_owned_descendant(self):
        with tempfile.TemporaryDirectory(prefix='xientia-r2-signal-') as td:
            root=Path(td); marker=root/'descendant.pid'
            parent='''import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from validated_publish import run_supervised
run_supervised([sys.executable,'-c',"import os,time,sys;from pathlib import Path;Path(sys.argv[1]).write_text(str(os.getpid()));time.sleep(120)",sys.argv[2]])
'''
            p=subprocess.Popen([sys.executable,'-c',parent,str(EDITORIAL),str(marker)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=subprocess_environment())
            try:
                deadline=time.monotonic()+10
                while not marker.exists():
                    self.assertIsNone(p.poll(),'Parent exited prematurely')
                    self.assertLess(time.monotonic(),deadline,'Child never started')
                    time.sleep(.02)
                child_pid=int(marker.read_text())
                p.send_signal(signal.SIGINT)
                p.communicate(timeout=12)
                self.assertNotEqual(p.returncode,0)
                # Linux may retain a zombie briefly; check that it is not running.
                def active():
                    try:
                        stat=Path(f'/proc/{child_pid}/stat').read_text()
                        return stat.split(') ',1)[1][0] not in 'ZX'
                    except FileNotFoundError:
                        return False
                deadline=time.monotonic()+4
                while active() and time.monotonic()<deadline:time.sleep(.05)
                self.assertFalse(active(),'Owned child survived interruption')
                self.assertFalse((root/'published').exists())
            finally:
                if p.poll() is None:p.kill();p.wait()

if __name__=='__main__':unittest.main()
