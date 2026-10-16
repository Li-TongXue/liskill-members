#!/usr/bin/env python3
"""Build the four Li method snapshots used by a standalone material-mining install."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'skills/li-material-mining/references'
SOURCES = {
    'stasis-topos.md': ['skills/li-stasis-topos/SKILL.md', 'skills/li-stasis-topos/references/method.md'],
    'conflict.md': ['skills/li-conflict-topics/SKILL.md'],
    'public-issues.md': ['skills/li-public-issues/SKILL.md', 'skills/li-public-issues/references/case-study.md'],
    'social-currency.md': ['skills/li-social-currency/SKILL.md'],
}


def expected():
    result = {}
    for target, sources in SOURCES.items():
        parts = ['# 素材挖掘的方法参考\n\n由仓库内方法正文生成，用于独立安装。这里的输出模板供判断参考，最终交付服从素材挖掘的格式。\n']
        for source in sources:
            text = (ROOT / source).read_text(encoding='utf-8')
            if text.startswith('---\n'):
                text = text.split('---', 2)[2].lstrip()
            text = text.replace('(references/method.md)', '(#争点与切口参考)').replace('`references/case-study.md`', '下方的完整案例')
            parts.append(f'\n<!-- source: {source} -->\n\n{text}')
        result[target] = '\n'.join(parts).rstrip() + '\n'
    return result


if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, content in expected().items():
        (DEST / name).write_text(content, encoding='utf-8')
        manifest.append({'file': name, 'sources': [
            {'path': s, 'sha256': hashlib.sha256((ROOT / s).read_bytes()).hexdigest()}
            for s in SOURCES[name]]})
    (DEST / 'li-method-sources.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
