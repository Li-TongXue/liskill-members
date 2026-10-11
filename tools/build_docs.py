#!/usr/bin/env python3
"""Render the skill directory table from skills.json; leave prose outside markers untouched."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
START, END = '<!-- skills:start -->', '<!-- skills:end -->'


def table():
    entries = json.loads((ROOT/'skills.json').read_text(encoding='utf-8'))['skills']
    lines = ['| 机器名称 | 中文名称 | 类型 | 完成度 | 用途 |', '|---|---|---|---|---|']
    for e in entries:
        level = '系统工具' if e['completion_level']=='internal' else 'Level '+e['completion_level']
        lines.append(f"| `{e['name']}` | {e['display_name']} | {e['kind']} | {level} | {e['description']} |")
    return '\n'.join(lines)


def rendered(text):
    a,b = text.split(START); _,c = b.split(END)
    return a+START+'\n'+table()+'\n'+END+c


if __name__ == '__main__':
    path = ROOT/'README.md'
    path.write_text(rendered(path.read_text(encoding='utf-8')), encoding='utf-8')
