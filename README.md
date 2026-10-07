# liskill-members

> liskill 会员技能仓库（付费会员专用）。把真实的内容与经营问题交给 Agent，获得清晰判断和可以立即执行的下一步。

**支持：豆包 Agent、Codex、Claude Code，以及其他支持 Skills 的 Agent。**

## 快速安装

```bash
# GitHub（国外用户）
npx -y skills add Li-TongXue/liskill-members -g --all

# Gitee（国内用户，推荐）
npx -y skills add https://gitee.com/LTX12/liskill-members.git -g --all
```

安装完成后，直接在 Agent 中输入 `/Li-xxx` 或对应触发词即可使用。

## 技能清单

| 技能 | 触发方式（示例） | 作用 |
|---|---|---|
| Li-Eight-Audits 八大审核法 | `/Li-八大审核法`、「帮我审稿」「这条能不能发」「按八步流程审核」「为什么没流量」 | 用 8 步短视频审核流程诊断已写好的口播文案/脚本，指出最致命的 1-3 个缺口并给出可直接使用的改写 |
| Li-Public-Issues 公共问题升维 | `/Li-公共问题升维`、「这个现象值不值得讲」「帮我把这个问题讲大」「个体现象怎么变成公共话题」 | 把私人模糊的"我觉得不对劲"还原成可观察现象，检验公共性，找到底层机制，形成值得讨论的公共问题 |
| Li-Conflict-Topics 冲突性选题 | `/Li-冲突性选题`、「这个话题太平了」「帮我找冲突」「怎么往冲突里推」 | 判断普通话题是否适合走冲突，找到主冲突，推进成更有题感和传播张力的内容入口 |
| Li-Stasis-Topoi 修辞学选题法 | `/Li-Stasis-Topoi`、`/Li-修辞学选题法`、「Stasis」「修辞学四层」「四层争点」「Topos」「共同事实 + 不同解释」 | 用 Stasis 四层争点法 + Topos 切口法拆解争议性话题，给出最适合传播的"争点层级 + Topos + 题目"组合 |
| Li-City-Impressions 城市印象文案生成 | `/Li-城市印象文案生成`、「城市印象」「城市反转」 | 用"负面误解→真实小事反转→正面翻盘→情绪金句"结构，为城市/旅游/本地生活账号生成口播脚本 |
| Li-Agenda-Setting 议程设置内容定位 | `/Li-议程设置内容定位`、「议程设置」「内容印象诊断」「稳定印象」「账号印象」 | 判断一批内容会在观众脑子里形成什么稳定印象，并反推如何把这个印象做稳 |
| Li-Story-Vlog 故事、事件vlog写作 | `/Li-故事、事件vlog写作`、「故事vlog」「事件vlog」「vlog旁白」「把这件事写成vlog」 | 用"不经意的在场"叙事策略写故事/事件型 vlog 旁白：情感现实主义、克制抒情、容器隐喻，支持自然商业植入 |
| Li-Social-Currency 社交货币性选题内容判断 | `/Li-社交货币性选题内容判断`、「社交货币」「Social Currency」「转发性判断」「值不值得拍」「会不会有人转」 | 用《疯传》社交货币三机制判断选题/内容"观众愿不愿意转发"，不值得拍就用三机制改造或从零倒推易转发选题 |

## 目录名与 name 字段对照

仓库目录与各技能 `SKILL.md` 的 `name` 字段均采用「英文标识 + 中文名」命名。原因：安装器（skills CLI）会按 `name` 字段生成安装目录并把其中的中文丢弃——若 name 只有中文，8 个技能会被压成同一个目录互相覆盖。英文标识保证 slug 互不相同；中文名保留在 name / description 中，用于界面显示与 `/` 触发。

| 英文目录名 | name 字段（界面显示名） |
|---|---|
| `Li-Agenda-Setting` | Li-Agenda-Setting 议程设置内容定位 |
| `Li-City-Impressions` | Li-City-Impressions 城市印象文案生成 |
| `Li-Conflict-Topics` | Li-Conflict-Topics 冲突性选题 |
| `Li-Eight-Audits` | Li-Eight-Audits 八大审核法 |
| `Li-Public-Issues` | Li-Public-Issues 公共问题升维 |
| `Li-Social-Currency` | Li-Social-Currency 社交货币性选题内容判断 |
| `Li-Stasis-Topoi` | Li-Stasis-Topoi 修辞学选题法 |
| `Li-Story-Vlog` | Li-Story-Vlog 故事、事件vlog写作 |

## 更新

```bash
npx skills update -g
```

## 说明

- 本仓库为会员专用分发渠道，安装指令请勿公开发布。
- `name` 字段采用「英文标识 + 中文名」：英文标识保证安装器 slug 不撞车，中文名保留在 name / description 中供界面显示与 `/` 触发，安装后无需手动改名。
