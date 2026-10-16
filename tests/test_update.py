from pathlib import Path
import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('li_updater', ROOT/'skills/li-update/scripts/update.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='li-test-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.home = self.base/'home'; self.home.mkdir()
        self.source = self.base/'release'; self.source.mkdir()
        shutil.copytree(ROOT/'skills', self.source/'skills')
        for name in ['skills.json','distribution.json']:
            shutil.copy2(ROOT/name,self.source/name)
        self.canonical = self.home/'.agents/skills'

    def legacy(self, root=None, name='Li'):
        folder=(root or self.canonical)/name
        folder.mkdir(parents=True)
        shutil.copy2(ROOT/'tests/fixtures/legacy/li.SKILL.txt',folder/'SKILL.md')
        return folder

    def run_update(self, apply=True, targets=None):
        return u.apply_release(self.source,self.home,targets,apply=apply)

    def alter_release(self, name='li', suffix='\n新版本内容。\n'):
        p=self.source/'skills'/name/'SKILL.md'
        p.write_text(p.read_text()+suffix)
        manifest=json.loads((self.source/'distribution.json').read_text())
        manifest['skills'][name]=u.fingerprint(p.parent)
        (self.source/'distribution.json').write_text(json.dumps(manifest))

    def test_check_is_read_only(self):
        result=self.run_update(apply=False)
        self.assertTrue(result['needs_update']); self.assertFalse(result['applied'])
        self.assertEqual(list(self.home.iterdir()),[])

    def test_fresh_install_complete_and_idempotent(self):
        result=self.run_update()
        self.assertEqual(result['skill_count'],11)
        for p in (self.source/'skills').iterdir():
            self.assertEqual(u.fingerprint(p),u.fingerprint(self.canonical/p.name))
        self.assertFalse(self.run_update(apply=False)['needs_update'])
        self.assertTrue(self.run_update()['applied'])
        self.assertFalse((self.home/'.claude').exists())

    def test_standalone_material_package_has_all_runtime_references(self):
        import re
        folder=self.base/'standalone'
        shutil.copytree(self.source/'skills/li-material-mining',folder)
        self.assertFalse((folder.parent/'li-stasis-topos').exists())
        for p in folder.rglob('*.md'):
            for ref in re.findall(r'\]\(([^)]+)\)',p.read_text()):
                if ref.startswith(('http','#')):continue
                target=(p.parent/ref.split('#')[0]).resolve()
                self.assertTrue(target.is_relative_to(folder.resolve()),str(p))
                self.assertTrue(target.is_file(),str(target))

    def test_migrate_manual_case_alias(self):
        old=self.legacy(); before=u.fingerprint(old)
        result=self.run_update()
        self.assertIn('li',[p.name for p in self.canonical.iterdir()])
        self.assertNotIn('Li',[p.name for p in self.canonical.iterdir()])
        backup=Path(result['backup'])
        locations=json.loads((backup/'locations.json').read_text())
        saved=next(x for x in locations if x['path']==str(old.parent.resolve()/old.name))
        self.assertEqual(before,u.fingerprint(backup/saved['backup']))

    def test_migrate_cli_sanitized_directory(self):
        self.legacy(name='li')
        self.run_update()
        self.assertIn('name: li\n',(self.canonical/'li/SKILL.md').read_text())

    def test_migrate_links_preserves_source_and_deduplicates_codex(self):
        external=self.base/'source-skill'
        external.mkdir()
        shutil.copy2(ROOT/'tests/fixtures/legacy/li.SKILL.txt',external/'SKILL.md')
        before=u.fingerprint(external)
        self.canonical.mkdir(parents=True)
        (self.canonical/'li').symlink_to(external,target_is_directory=True)
        for host in ['.claude','.codex']:
            root=self.home/host/'skills';root.mkdir(parents=True)
            (root/'Li').symlink_to(self.canonical/'li',target_is_directory=True)
        self.run_update()
        self.assertEqual(before,u.fingerprint(external))
        self.assertEqual(list((self.home/'.codex/skills').iterdir()),[])
        self.assertEqual(u.fingerprint(self.canonical/'li'),u.fingerprint(self.home/'.claude/skills/li'))

    def test_unknown_same_name_blocks_all_writes(self):
        target=self.canonical/'li';target.mkdir(parents=True)
        (target/'SKILL.md').write_text('user-created content')
        before=u.fingerprint(target)
        with self.assertRaisesRegex(u.UpdateError,'未覆盖'):
            self.run_update()
        self.assertEqual(before,u.fingerprint(target))
        self.assertEqual([p.name for p in self.canonical.iterdir()],['li'])
        self.assertFalse((self.home/'.liskill').exists())

    def test_legacy_user_edit_is_preserved(self):
        old=self.legacy();p=old/'SKILL.md';p.write_text(p.read_text()+'\n个人规则\n')
        before=u.fingerprint(old)
        with self.assertRaises(u.UpdateError):self.run_update()
        self.assertEqual(before,u.fingerprint(old))

    def test_extra_user_file_is_preserved(self):
        old=self.legacy();(old/'我的素材.txt').write_text('不能丢失')
        with self.assertRaises(u.UpdateError):self.run_update()
        self.assertEqual((old/'我的素材.txt').read_text(),'不能丢失')

    def test_other_skills_and_business_files_untouched(self):
        other=self.canonical/'other-skill';other.mkdir(parents=True)
        (other/'SKILL.md').write_text('another provider')
        content=self.home/'我的文稿';content.mkdir();(content/'稿件.md').write_text('用户内容')
        self.run_update()
        self.assertEqual((other/'SKILL.md').read_text(),'another provider')
        self.assertEqual((content/'稿件.md').read_text(),'用户内容')

    def test_edited_modern_install_is_preserved(self):
        self.run_update();p=self.canonical/'li/SKILL.md';p.write_text(p.read_text()+'\n私人修改\n')
        before=u.fingerprint(p.parent)
        with self.assertRaises(u.UpdateError):self.run_update()
        self.assertEqual(before,u.fingerprint(p.parent))

    def test_previous_managed_release_updates_and_new_skill_is_installed(self):
        self.run_update();self.alter_release()
        new=self.source/'skills/li-new';new.mkdir();(new/'SKILL.md').write_text('---\nname: li-new\ndescription: Example.\n---\n')
        registry=json.loads((self.source/'skills.json').read_text());registry['skills'].append({'name':'li-new'})
        (self.source/'skills.json').write_text(json.dumps(registry))
        manifest=json.loads((self.source/'distribution.json').read_text());manifest['skills']['li-new']=u.fingerprint(new)
        (self.source/'distribution.json').write_text(json.dumps(manifest))
        result=self.run_update()
        self.assertEqual(result['skill_count'],12)
        self.assertEqual(u.fingerprint(self.canonical/'li'),u.fingerprint(self.source/'skills/li'))
        self.assertEqual(u.fingerprint(self.canonical/'li-new'),u.fingerprint(new))

    def test_already_current_cli_install_records_ownership_for_next_update(self):
        shutil.copytree(self.source/'skills',self.canonical)
        self.assertFalse(self.run_update()['needs_update'])
        self.assertTrue((self.home/'.liskill/install-state.json').exists())
        self.alter_release()
        self.run_update()
        self.assertEqual(u.fingerprint(self.canonical/'li'),u.fingerprint(self.source/'skills/li'))

    def test_active_update_lock_preserves_installation(self):
        self.legacy();folder=self.home/'.liskill';folder.mkdir();(folder/'update.lock').write_text('other process')
        before=u.fingerprint(self.canonical/'Li')
        with self.assertRaisesRegex(u.UpdateError,'另一次更新'):self.run_update()
        self.assertEqual(before,u.fingerprint(self.canonical/'Li'))
        self.assertEqual((folder/'update.lock').read_text(),'other process')

    def test_custom_directory_does_not_expand_scope(self):
        custom=self.base/'custom/skills';self.run_update(targets=[custom])
        self.assertTrue((custom/'li-update/SKILL.md').exists())
        self.assertFalse(self.canonical.exists())

    def test_duplicate_resolved_targets_are_not_repeated(self):
        custom=self.base/'custom';custom.mkdir();link=self.base/'link';link.symlink_to(custom,target_is_directory=True)
        result=self.run_update(targets=[custom,link])
        self.assertEqual(len(result['destinations']),1)

    def test_nested_and_home_targets_are_rejected(self):
        for targets in [[self.home],[self.base/'a',self.base/'a/b'],[self.source/'skills']]:
            with self.assertRaises(u.UpdateError):self.run_update(targets=targets)

    def test_corrupt_or_extra_distribution_files_rejected_before_install(self):
        for action in ['remove','extra']:
            with self.subTest(action=action):
                p=self.source/'skills/li/SKILL.md'
                original=p.read_bytes()
                extra=p.parent/'extra.txt'
                if action=='remove':p.unlink()
                else:extra.write_text('not in manifest')
                with self.assertRaises(u.UpdateError):self.run_update()
                self.assertFalse(self.canonical.exists())
                p.write_bytes(original);extra.unlink(missing_ok=True)

    def test_failure_during_replacement_restores_original(self):
        old=self.legacy();before=u.fingerprint(old)
        rename=Path.rename
        def fail_one(path,target):
            if path.parent.name.startswith('.li-stage-') and path.name=='li-update':
                raise OSError('simulated disk failure')
            return rename(path,target)
        with patch.object(Path,'rename',fail_one):
            with self.assertRaises(OSError):self.run_update()
        self.assertEqual(before,u.fingerprint(old))
        self.assertEqual([p.name for p in self.canonical.iterdir()],['Li'])
        self.assertFalse((self.home/'.liskill/install-state.json').exists())

    def test_state_write_failure_rolls_back_all_roots(self):
        self.legacy();(self.home/'.claude').mkdir()
        before=u.fingerprint(self.canonical/'Li')
        with patch.object(u.os,'replace',side_effect=OSError('state write failure')):
            with self.assertRaises(OSError):self.run_update()
        self.assertEqual(before,u.fingerprint(self.canonical/'Li'))
        self.assertEqual(list((self.home/'.claude/skills').iterdir()),[])

    def test_cli_network_failure_does_not_touch_installation(self):
        self.legacy();before=u.fingerprint(self.canonical/'Li')
        with patch.object(u,'fetch_release',side_effect=u.UpdateError('网络失败')),patch.object(Path,'home',return_value=self.home),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(u.main(['--apply']),1)
        self.assertEqual(before,u.fingerprint(self.canonical/'Li'))

    def test_cli_check_and_apply_report_real_result(self):
        def fetch(destination):shutil.copytree(self.source,destination)
        for flag in ['--check','--apply']:
            output=io.StringIO()
            with patch.object(u,'fetch_release',side_effect=fetch),patch.object(Path,'home',return_value=self.home),contextlib.redirect_stdout(output):
                self.assertEqual(u.main([flag]),0)
            result=json.loads(output.getvalue())
            self.assertEqual(result['applied'],flag=='--apply')


if __name__=='__main__':unittest.main()
