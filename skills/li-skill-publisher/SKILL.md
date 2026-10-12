---
name: li-skill-publisher
description: "把新技能包发布到 liskill-members 仓库（GitHub + Gitee 双端同步），并自动更新主路由和 README。用户说「发布新技能」「加个技能」「上传 skill」「把这个技能推到仓库」时使用；只更新已有技能内容、删除技能或审核技能质量时不使用。"
metadata:
  collection: "liskill-members"
  kind: "tool"
  completion_level: "2"
  completion_reason: "内置规范检查脚本、双端推送流程、主路由和 README 更新模板。"
  completion_upgrade_status: "已满足：内置规范检查脚本、双端推送流程、主路由和 README 更新模板。"
---

# li-skill-publisher｜技能发布器

把一个新技能包发布到 liskill-members 仓库，自动完成：命名检查 → 双端推送 → 主路由更新 → README 更新。

---

## 工作流程

### 第 1 步：接收技能包

用户提供技能包（zip 文件或目录路径）。解压后确认结构：
- 目录名是什么
- 有没有 SKILL.md
- SKILL.md 里的 frontmatter 是否完整

### 第 2 步：规范检查

按以下规则检查，不符合的先修正：

| 检查项 | 规范 | 不通过时怎么办 |
|---|---|---|
| 目录名 | 小写英文 kebab-case，如 `li-example-skill` | 改成符合规则的英文名，中文名保留在标题里 |
| name 字段 | 与目录名完全一致 | 同步修改 |
| description | 包含：用途 + 触发场景 + 不适用边界 | 补全三要素 |
| metadata | 包含 collection、kind、completion_level | 补全默认值 |

**命名参考**：按功能起英文名，如素材挖掘 = material-mining，发布适配 = publish-pack。不要用中文或 PascalCase。

### 第 3 步：推送双端

**Gitee**（用 API，token 已配置在 `references/config.json`）：
```bash
python3 skills/li-skill-publisher/scripts/publish.py push <skill_dir> <skill_name>
```

**GitHub**（用 gh CLI 或 git）：
```bash
cd <repo_dir>
git add skills/<skill_name>/
git commit -m "feat: 新增 <skill_name>"
git push origin main
```

### 第 4 步：更新主路由

打开 `skills/li/SKILL.md`，在路由总表里加一行：
- 按短视频制作流程选阶段：素材 / 选题 / 用户共鸣 / 文案脚本 / 审核 / 发布 / 工具
- 编号按顺序排
- 典型说法写 3-5 个用户常说的话

同时在"判定要点"里加一条容易混淆的区分。

### 第 5 步：更新 README

打开 `README.md`，在技能清单表格里加一行：
- 阶段列填对应阶段
- 调用名 = 机器名
- 中文名称 = 显示名
- 用途 = description 的精简版

---

## 配置文件

`references/config.json` 存了双端仓库信息和 Gitee token。其他对话框加载这个技能时会自动读到配置，不需要重新登录。

---

## 边界

- 只负责发布新技能，不审核技能内容写得好不好
- 已有技能的内容更新，直接改文件后 git push 即可，不用走这个流程
- 删除技能、调整技能顺序、重构路由结构，属于维护操作，需要人工确认后再做
