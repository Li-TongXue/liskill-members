---
name: li-update
description: "检查或更新官方 liskill-members 的安装。用户要求更新、升级或检查 Li 安装状态时使用；仅询问版本或更新方式时先解释，只有明确要求更新才执行写入。"
metadata:
  collection: "liskill-members"
  kind: "system"
  completion_level: "internal"
  completion_reason: "系统维护入口，不直接生成业务文稿。"
---

# 更新 liskill

只维护官方 liskill-members 集合。先从当前对话分清用户要解释、检查还是执行更新。

## 使用条件

需要 Git、Python 3.10 或更新版本、官方仓库网络访问和目标目录写入权限。不能执行脚本的宿主只提供 README 所述终端操作，不假称已经更新。

## 执行

- 用户仅问更新方式：解释 `li-update` 的作用，不运行更新。
- 用户要求检查：运行本 Skill 目录下 `scripts/update.py --check`。
- 用户明确要求更新、升级或安装：直接运行 `scripts/update.py --apply`，无需再次文字确认；遵守宿主的权限机制。

用 `python3` 调用脚本；Windows 使用可用的 `py -3` 或 Python 解释器。路径必须以本 SKILL.md 的实际位置解析，不能假设当前工作目录。需要自定义客户端目录时，只有用户或客户端配置已经明确提供路径，才添加 `--skills-dir "实际目录"`；否则使用默认位置。

默认同步通用 Agents 目录、已存在的 Claude Code 用户目录，并迁移已识别的 Codex 旧专属入口。其他客户端通过明确的目标目录或其导入功能维护。更新来源固定为 Gitee 官方仓库，不切换到不明镜像。

## 结果与边界

脚本先检查来源、完整文件和本地修改，暂存与备份完成后才替换。具体行为见 [迁移说明](references/migration.md)。

- 退出成功且 `applied` 为 true：告知同步完成或文件已一致。按宿主需要新建对话或重新加载技能。
- 检查模式：根据 `needs_update` 说明是否有差异、将同步到哪些位置；不要把检查说成更新完成。
- 非零退出：说明网络、权限、来源冲突或用户改动等具体原因，保留材料，不自行删除冲突文件、不反复重试。
- 旧版首次升级没有本入口，指导用户通过官方仓库 README 的终端升级方式取得它。
- 不执行 `npx skills update`；不更新其他来源的 Skill，不创建后台任务，不读取或存储用户业务素材。

本 Skill 为系统工具，`completion_level: internal` 不表示会员业务内容的完成度。成功或失败说明完成后结束当前任务。
