"""Exercise the installed updater through a real CLI and Git clone, in an isolated home."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_update import ROOT, u


@unittest.skipUnless(shutil.which('git'),'Git is required for the clone integration test')
class GitIntegrationTests(unittest.TestCase):
    def test_installed_updater_clones_and_updates_itself(self):
        with tempfile.TemporaryDirectory(prefix='li-git-test-') as directory:
            temp=Path(directory).resolve();release=temp/'release';release.mkdir()
            home=temp/'home';home.mkdir()
            shutil.copytree(ROOT/'skills',release/'skills')
            for name in ['skills.json','distribution.json']:
                shutil.copy2(ROOT/name,release/name)
            u.apply_release(release,home,apply=True)
            env=dict(os.environ)
            env.update(HOME=str(home),USERPROFILE=str(home),XDG_CONFIG_HOME=str(home/'.config'),GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=str(temp/'gitconfig'),PYTHONDONTWRITEBYTECODE='1')
            # Force the fixed official URL to a local fixture only in this subprocess environment.
            # No real account or Git configuration is changed.
            env['GIT_CONFIG_COUNT']='1'
            env['GIT_CONFIG_KEY_0']='url.'+release.as_uri()+'.insteadOf'
            env['GIT_CONFIG_VALUE_0']=u.SOURCE
            for args in [['init','-b','main'],['add','.'],['-c','user.name=Li Test','-c','user.email=test@example.invalid','commit','-m','isolated release fixture']]:
                subprocess.run(['git',*args],cwd=release,env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            script=home/'.agents/skills/li-update/scripts/update.py'
            # Simulate a subsequent release, including an update to the running updater's own file.
            remote_script=release/'skills/li-update/scripts/update.py'
            remote_script.write_text(remote_script.read_text()+'\n# next fixture release\n')
            manifest=json.loads((release/'distribution.json').read_text())
            manifest['skills']['li-update']=u.fingerprint(remote_script.parent.parent)
            (release/'distribution.json').write_text(json.dumps(manifest))
            for args in [['add','.'],['-c','user.name=Li Test','-c','user.email=test@example.invalid','commit','-m','second fixture release']]:
                subprocess.run(['git',*args],cwd=release,env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            result=subprocess.run([sys.executable,'-B',str(script),'--check'],cwd=temp,env=env,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue(json.loads(result.stdout)['needs_update'])
            self.assertNotIn('next fixture release',script.read_text())
            result=subprocess.run([sys.executable,'-B',str(script),'--apply'],cwd=temp,env=env,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue(json.loads(result.stdout)['applied'])
            self.assertEqual(script.read_bytes(),remote_script.read_bytes())
            self.assertEqual(u.fingerprint(script.parent.parent),u.fingerprint(remote_script.parent.parent))


if __name__=='__main__':unittest.main()
