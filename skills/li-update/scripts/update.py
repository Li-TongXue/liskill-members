#!/usr/bin/env python3
"""Update only the official Li collection; standard library + Git, no global skills update."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

SOURCE = 'https://gitee.com/LTX12/liskill-members.git'
COLLECTION = 'liskill-members'


class UpdateError(Exception):
    pass


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise UpdateError(f'无法读取有效配置：{path}') from exc


def exists(path):
    return path.exists() or path.is_symlink()


def fingerprint(directory):
    """No hidden extras are ignored: user additions and edits must cause a conflict."""
    if not directory.is_dir():
        raise UpdateError(f'不是可读取的技能目录：{directory}')
    result = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise UpdateError(f'技能内部含额外链接，需要人工检查：{path}')
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def release_info(source):
    manifest = read_json(source / 'distribution.json')
    registry = read_json(source / 'skills.json')
    if manifest.get('schema_version') != 1 or registry.get('schema_version') != 1:
        raise UpdateError('分发清单版本不受支持，请使用新版更新器。')
    if manifest.get('collection') != COLLECTION or registry.get('repository') != SOURCE:
        raise UpdateError('分发来源标识不匹配。')
    names = [entry['name'] for entry in registry['skills']]
    if len(names) != len(set(names)) or set(names) != set(manifest['skills']):
        raise UpdateError('技能目录与分发清单不一致。')
    for name in names:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name) > 64:
            raise UpdateError(f'无效技能名：{name}')
        folder = source / 'skills' / name
        if folder.is_symlink() or fingerprint(folder) != manifest['skills'][name]:
            raise UpdateError(f'分发文件缺失、带链接或校验失败：{name}')
    if 'li-update' not in names:
        raise UpdateError('分发包缺少更新入口。')
    return manifest, names


def load_state(home):
    path = home / '.liskill/install-state.json'
    if not path.exists():
        return {'schema_version': 1, 'installs': {}}
    state = read_json(path)
    if state.get('schema_version') != 1 or not isinstance(state.get('installs'), dict):
        raise UpdateError('本地安装记录无效；已保留原安装，请先修复记录。')
    return state


def install_plan(source, home, targets=None):
    manifest, names = release_info(source)
    legacy = read_json(source / 'skills/li-update/references/legacy-installations.json')['skills']
    old = {entry['name']: entry for entry in legacy}
    aliases = {name: set(old.get(name, {}).get('aliases', [])) | {name} for name in names}
    alias_owner = {alias.casefold(): name for name, values in aliases.items() for alias in values}
    state = load_state(home)
    if targets is None:
        destinations = [home / '.agents/skills']
        if (home / '.claude').is_dir():
            destinations.append(home / '.claude/skills')
        cleanup = [home / '.codex/skills'] if (home / '.codex/skills').is_dir() else []
    else:
        destinations = [Path(p).expanduser().absolute() for p in targets]
        cleanup = []
    destinations = list(dict.fromkeys(p.resolve() for p in destinations))
    cleanup = [p.resolve() for p in cleanup if p.resolve() not in destinations]
    roots = destinations + cleanup
    for root in roots:
        if root == home or root == Path(root.anchor) or root == source or root == source / 'skills':
            raise UpdateError(f'不能将此目录作为安装位置：{root}')
        if any(root != other and root.is_relative_to(other) for other in roots):
            raise UpdateError('安装目录不能互相嵌套。')
    recognized = []
    conflicts = []
    for root in roots:
        if exists(root) and not root.is_dir():
            raise UpdateError(f'安装位置不是目录：{root}')
        for path in sorted(root.iterdir()) if root.is_dir() else []:
            name = alias_owner.get(path.name.casefold())
            if not name:
                continue
            try:
                files = fingerprint(path)
            except (UpdateError, OSError) as exc:
                conflicts.append(f'{path}（{exc}）')
                continue
            accepted = [manifest['skills'][name]]
            if name in old:
                accepted.append(old[name]['files'])
            record = state['installs'].get(str(path.absolute()))
            if record and record.get('name') == name and record.get('source') == SOURCE:
                accepted.append(record.get('files'))
            if files not in accepted:
                conflicts.append(str(path))
            else:
                recognized.append({'path': path, 'name': name, 'files': files})
    if conflicts:
        raise UpdateError('发现同名的未知来源、用户改动或额外文件；未覆盖任何技能：\n'+'\n'.join(conflicts))
    return {'manifest': manifest, 'names': names, 'destinations': destinations,
            'old': recognized, 'state': state, 'cleanup': cleanup}


def _apply_release(source, home, targets=None, *, apply=False):
    """Source is a validated local checkout; the CLI obtains it only from SOURCE."""
    source, home = Path(source).resolve(), Path(home).resolve()
    plan = install_plan(source, home, targets)
    wanted = {root / name for root in plan['destinations'] for name in plan['names']}
    existing = {entry['path']: entry for entry in plan['old']}
    changes = any(path not in existing or existing[path]['files'] != plan['manifest']['skills'][path.name]
                  for path in wanted) or any(path not in wanted for path in existing)
    result = {'source': SOURCE, 'skill_count': len(plan['names']), 'needs_update': changes,
              'destinations': [str(p) for p in plan['destinations']], 'applied': False}
    if not apply:
        return result
    if not changes:
        state = plan['state']
        for path in wanted:
            state['installs'][str(path.absolute())] = {'name': path.name, 'files': plan['manifest']['skills'][path.name], 'source': SOURCE}
        write_state(home / '.liskill/install-state.json', state)
        result['applied'] = True
        result['message'] = '文件已经与官方仓库一致。'
        return result
    run_id = uuid.uuid4().hex
    state_dir = home / '.liskill'
    backup = state_dir / 'backups' / run_id
    state_path = state_dir / 'install-state.json'
    old_state = state_path.read_bytes() if state_path.exists() else None
    staged = []
    parked = []
    installed = []
    temps = []
    old_records = []
    safe_to_clean = True
    try:
        # Prepare all new files and complete old content backups before replacing anything.
        for root in plan['destinations']:
            root.mkdir(parents=True, exist_ok=True)
            stage = Path(tempfile.mkdtemp(prefix='.li-stage-', dir=root.parent))
            temps.append(stage)
            for name in plan['names']:
                incoming = stage / name
                shutil.copytree(source / 'skills' / name, incoming)
                if fingerprint(incoming) != plan['manifest']['skills'][name]:
                    raise UpdateError(f'暂存文件校验失败：{name}')
                staged.append((incoming, root / name))
        backup.mkdir(parents=True)
        for index, entry in enumerate(plan['old']):
            path = entry['path']
            if fingerprint(path) != entry['files']:
                raise UpdateError(f'安装在检查后发生变化，已停止：{path}')
            snapshot = backup / f'{index:03d}'
            shutil.copytree(path, snapshot)  # Copies link targets; backups survive canonical replacement.
            old_records.append({'path': str(path), 'backup': snapshot.name, 'name': entry['name']})
        (backup / 'locations.json').write_text(json.dumps(old_records, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        # Move every old alias aside before installing canonical lowercase names (also on macOS).
        for entry in plan['old']:
            path = entry['path']
            parking = Path(tempfile.mkdtemp(prefix='.li-old-', dir=path.parent.parent))
            temps.append(parking)
            target = parking / path.name
            path.rename(target)
            parked.append((target, path))
        for incoming, target in staged:
            if exists(target):
                raise UpdateError(f'安装目标在检查后被占用：{target}')
            incoming.rename(target)
            installed.append(target)
        for target in installed:
            if fingerprint(target) != plan['manifest']['skills'][target.name]:
                raise UpdateError(f'安装后校验失败：{target}')
        state = plan['state']
        for entry in plan['old']:
            state['installs'].pop(str(entry['path'].absolute()), None)
        for target in installed:
            state['installs'][str(target.absolute())] = {
                'name': target.name, 'files': plan['manifest']['skills'][target.name], 'source': SOURCE}
        write_state(state_path, state)
    except Exception as error:
        rollback_errors = []
        for target in reversed(installed):
            try:
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                elif exists(target):
                    target.unlink()
            except OSError as exc:
                rollback_errors.append(str(exc))
        for parked_path, original in reversed(parked):
            try:
                if exists(parked_path):
                    if exists(original):
                        raise OSError(f'恢复目标被占用：{original}')
                    parked_path.rename(original)
            except OSError as exc:
                rollback_errors.append(str(exc))
        try:
            if old_state is None:
                state_path.unlink(missing_ok=True)
            else:
                state_path.write_bytes(old_state)
        except OSError as exc:
            rollback_errors.append(str(exc))
        if rollback_errors:
            safe_to_clean = False
            raise UpdateError(f'更新失败且部分恢复受阻；完整备份位于 {backup}，原目录的暂存副本已保留：'+'；'.join(rollback_errors)) from error
        raise
    finally:
        if safe_to_clean:
            for directory in temps:
                shutil.rmtree(directory, ignore_errors=True)
    result.update(applied=True, backup=str(backup), message='Li 技能已更新并通过文件校验。')
    return result


def write_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f'.state-{uuid.uuid4().hex}.json'
    try:
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def apply_release(source, home, targets=None, *, apply=False):
    source, home = Path(source).resolve(), Path(home).resolve()
    if not apply:
        return _apply_release(source, home, targets, apply=False)
    install_plan(source, home, targets)  # Reject conflicts before creating local maintenance data.
    lock = home / '.liskill/update.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = lock.open('x', encoding='utf-8')
    except FileExistsError as exc:
        raise UpdateError(f'另一次更新尚未结束，或上次被中断；确认没有更新进程后再处理 {lock}。') from exc
    try:
        with handle:
            handle.write(str(os.getpid()))
        # Recheck after acquiring the lock; never apply a stale preflight plan.
        return _apply_release(source, home, targets, apply=True)
    finally:
        lock.unlink(missing_ok=True)


def fetch_release(destination):
    try:
        subprocess.run(['git', 'clone', '--quiet', '--depth', '1', '--', SOURCE, str(destination)],
                       check=True, timeout=120, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as exc:
        raise UpdateError('找不到 Git；安装 Git 后重试。') from exc
    except subprocess.TimeoutExpired as exc:
        raise UpdateError('读取官方仓库超时；本地技能未修改。') from exc
    except subprocess.CalledProcessError as exc:
        raise UpdateError('无法读取官方仓库；检查网络和仓库访问权限后重试。') from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true', help='只检查差异，不修改安装')
    mode.add_argument('--apply', action='store_true', help='同步官方 Li 技能并迁移已识别旧安装')
    parser.add_argument('--skills-dir', action='append', type=Path, help='明确指定安装目录，可重复；覆盖默认目录选择')
    args = parser.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix='liskill-fetch-') as tmp:
            source = Path(tmp) / 'repository'
            fetch_release(source)
            result = apply_release(source, Path.home(), args.skills_dir, apply=args.apply)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (UpdateError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f'liskill 没有更新完成：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
