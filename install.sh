#!/usr/bin/env bash
# liskill-members 一键安装/更新脚本
# 作用：把仓库 skills/ 下的全部技能同步到豆包技能目录 ~/.agents/skills
# 用法：curl -sL https://gitee.com/LTX12/liskill-members/raw/main/install.sh | bash
#       或  bash install.sh（已克隆仓库时）
# 说明：仓库新增/更新技能后，重跑本脚本即可全量同步；本地多余旧目录需手动删除。

set -e

REPO_URL="https://gitee.com/LTX12/liskill-members.git"
DEST="${HOME}/.agents/skills"

echo "▶ 拉取技能仓库（${REPO_URL}）..."
TMP="$(mktemp -d)/liskill-tmp"
if git clone --depth 1 "$REPO_URL" "$TMP" 2>/dev/null; then
    :
else
    echo "✗ 拉取失败，请检查网络连接（GitHub 用户可改用镜像仓库）。"
    rm -rf "$TMP"
    exit 1
fi

SKILL_COUNT="$(find "$TMP/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
if [ -z "$SKILL_COUNT" ] || [ "$SKILL_COUNT" = "0" ]; then
    echo "✗ 仓库中未发现技能目录，请检查仓库结构。"
    rm -rf "$TMP"
    exit 1
fi

mkdir -p "$DEST"
echo "▶ 同步 ${SKILL_COUNT} 个技能到 ${DEST} ..."
cp -R "$TMP/skills/." "$DEST/"
rm -rf "$TMP"

echo "✅ ${SKILL_COUNT} 个技能已同步完成。"
echo "   在豆包中输入 /Li-xxx 或对应触发词即可使用；更新时重跑本脚本。"
