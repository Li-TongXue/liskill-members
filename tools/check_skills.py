#!/usr/bin/env python3
"""Read-only validation of portable skills, packaged methods and generated inventories."""
from pathlib import Path
import hashlib
import json
import re
import sys
import yaml

from build_docs import rendered
from build_distribution import expected as expected_distribution
from build_references import expected as expected_references

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}


def frontmatter(path):
    text = path.read_text(encoding='utf-8')
    match = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
    if not match:
        raise ValueError(f'缺少 YAML frontmatter：{path}')
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError(f'frontmatter 必须是映射：{path}')
    return data, text[match.end():]


def check(root=ROOT):
    errors = []
    def require(condition, message):
        if not condition:
            errors.append(message)
    registry = json.loads((root/'skills.json').read_text(encoding='utf-8'))
    entries = registry['skills']
    names = [e['name'] for e in entries]
    require(len(names)==len(set(names)), '清单有重复名称')
    require(set(names)=={p.name for p in (root/'skills').iterdir() if p.is_dir()}, '正式清单与目录不一致')
    for entry in entries:
        name = entry['name']; folder=root/'skills'/name
        require(bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name)) and len(name)<=64, f'{name}: 非法名称')
        try:
            meta,body=frontmatter(folder/'SKILL.md')
            require(not (set(meta)-FIELDS), f'{name}: 未知顶层字段')
            require(meta.get('name')==name, f'{name}: name 与目录不同')
            desc=meta.get('description')
            require(isinstance(desc,str) and 1<=len(desc)<=1024, f'{name}: description 类型或长度错误')
            require(desc==entry['description'], f'{name}: description 与清单不同')
            md=meta.get('metadata',{})
            require(isinstance(md,dict) and all(isinstance(v,str) for v in md.values()),f'{name}: metadata 必须为字符串映射')
            for key in ['kind','completion_level','completion_reason']:
                require(md.get(key)==entry[key],f'{name}: {key} 与清单不同')
            require(md.get('collection')=='liskill-members',f'{name}: 集合标识错误')
            level=md.get('completion_level')
            require(level in {'1','2','internal'},f'{name}: 未知完成度')
            if entry['kind']=='business':
                require(level!='internal', f'{name}: 会员业务不能标为内部工具')
            if level=='1':
                require('这个 skill 目前是结构型，填充物需要我们一起补充，不会自动产出完整文稿' in body, f'{name}: 缺少结构型告知')
            if level=='2':
                require(bool(md.get('completion_upgrade_status')) and md['completion_upgrade_status']==entry.get('completion_upgrade_status'), f'{name}: 升级状态缺失或不一致')
            require(len((folder/'SKILL.md').read_text().splitlines())<500, f'{name}: 请拆分长篇参考')
            ui=yaml.safe_load((folder/'agents/openai.yaml').read_text(encoding='utf-8'))['interface']
            require(ui['display_name']==f"{name}（{entry['display_name']}）", f'{name}: 显示名错误')
            require(25<=len(ui['short_description'])<=64, f'{name}: 界面简介长度错误')
            require('$'+name in ui['default_prompt'], f'{name}: 默认提示词缺少正式调用')
            for p in folder.rglob('*'):
                require(not p.is_symlink(), f'{name}: 分发文件不能为软链接 {p}')
                if p.suffix!='.md': continue
                text=p.read_text(encoding='utf-8')
                require(not re.search(r'/Users/|[A-Z]:\\Users\\',text), f'{p}: 作者绝对路径')
                require(not re.search(r'/[Ll]i-[\u4e00-\u9fff]',text),f'{p}: 把中文别名当成命令')
                links = re.findall(r'\]\(([^)]+)\)',text)
                links += re.findall(r'`((?:references|scripts|assets|agents)/[^`]+)`',text)
                for ref in links:
                    ref = ref.split(' --', 1)[0]
                    if re.match(r'https?://|mailto:|#',ref): continue
                    target=(p.parent/ref.split('#')[0]).resolve()
                    # Convention: bare references/ paths in prose are relative to the skill root.
                    if ref.startswith(('references/','scripts/','assets/','agents/')): target=(folder/ref.split('#')[0]).resolve()
                    require(target.is_relative_to(folder.resolve()) and target.is_file(),f'{p}: 缺失或越界引用 {ref}')
        except (OSError,KeyError,TypeError,ValueError,yaml.YAMLError) as exc:
            errors.append(f'{name}: {exc}')
    router=(root/'skills/li/SKILL.md').read_text(encoding='utf-8')
    for name in names:
        if name!='li': require('`'+name+'`' in router,f'主入口未覆盖 {name}')
    readme=(root/'README.md').read_text(encoding='utf-8')
    require(readme==rendered(readme),'README 清单未重新生成')
    refs=root/'skills/li-material-mining/references'
    for name,expected in expected_references().items():
        require((refs/name).read_text(encoding='utf-8')==expected,f'随包参考过期：{name}')
    for row in json.loads((refs/'li-method-sources.json').read_text(encoding='utf-8')):
        for source in row['sources']:
            require(hashlib.sha256((root/source['path']).read_bytes()).hexdigest()==source['sha256'],f'方法来源哈希过期：{source["path"]}')
    for row in json.loads((refs/'external-method-sources.json').read_text(encoding='utf-8')):
        require(hashlib.sha256((refs/row['file']).read_bytes()).hexdigest()==row['bundled_sha256'],f'外部方法副本发生未记录改动：{row["file"]}')
    require((root/'docs/installation.md').read_bytes()==(root/'skills/li-update/references/migration.md').read_bytes(),'更新器内的迁移说明与文档不同')
    require(json.loads((root/'distribution.json').read_text(encoding='utf-8'))==expected_distribution(),'分发清单过期')
    return errors


if __name__=='__main__':
    try:
        errors=check()
    except (OSError,ValueError,KeyError) as exc:
        errors=[str(exc)]
    if errors:
        print('\n'.join(errors),file=sys.stderr)
        sys.exit(1)
    print('所有 Skill 定义、引用、清单和分发文件校验通过。')
