# 开发与验收

## 真源与生成物

- `skills.json`：正式技能清单、机器名称、描述和完成度依据。
- `skills/<name>/SKILL.md`：执行正文。frontmatter 必须与清单一致；自定义字段放在 `metadata` 中。
- `agents/openai.yaml`：Codex 可选界面信息，中文显示名与机器名称分开。
- 素材挖掘的四份 Li 方法参考由现有业务 Skill 生成；dbs 争点方法为注明来源的随包副本。
- `distribution.json`：全部 Skill 文件的校验清单，供检查完整下载与安装使用；不是数字签名或自动版本发布系统。

原文缺失的扩展不能用模型常识补成“原版方法”。对完成度的修改需要写清输入来源、已具备流程及尚未满足的条件。Level 1 必须在业务开始前明确说明，Level 2 必须有升级条件已满足的说明。

## 生成与校验

```bash
python3 -B tools/build_references.py
python3 -B tools/build_docs.py
python3 -B tools/build_distribution.py
python3 -B tools/check_skills.py
python3 -B -m unittest discover -s tests -v
```

开发校验需要 `requirements-dev.txt` 中的 PyYAML；运行更新器只需要 Python 标准库和 Git。可在项目外创建虚拟环境后安装开发依赖，不把环境打入分发目录。

校验包含名称、description、元数据、相对引用、方法副本、README 清单与分发文件一致性。测试使用临时 home 和本地发布副本，不改开发者真实技能目录；覆盖安装、旧目录及软链接迁移、同名冲突、用户修改、损坏分发、更新失败回滚和再次升级。

首次升级由 README 中的终端命令取得 `li-update`。本地变更未发布前，仅在隔离环境验证本地包；不运行正式命令覆盖开发者全局安装。
