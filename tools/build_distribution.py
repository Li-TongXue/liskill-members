#!/usr/bin/env python3
"""Generate the file inventory used to verify complete downloads and installs."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def expected():
    registry = json.loads((ROOT / 'skills.json').read_text(encoding='utf-8'))
    skills = {}
    for entry in registry['skills']:
        folder = ROOT / 'skills' / entry['name']
        files = {}
        for path in sorted(folder.rglob('*')):
            if path.is_symlink():
                raise ValueError(f'分发包不能有链接：{path}')
            if path.is_file():
                if '__pycache__' in path.parts or path.suffix == '.pyc':
                    raise ValueError(f'请先移除生成的 Python 缓存：{path}')
                files[path.relative_to(folder).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        skills[entry['name']] = files
    return {'schema_version': 1, 'collection': 'liskill-members', 'skills': skills}


if __name__ == '__main__':
    (ROOT / 'distribution.json').write_text(json.dumps(expected(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
