#!/usr/bin/env python3
"""
liskill-members 技能发布器
用法：
  python3 publish.py check <skill_dir>          # 检查技能规范
  python3 publish.py push <skill_dir> <skill_name>  # 推送单个技能到 Gitee
"""

import json
import base64
import sys
import os
import re
import urllib.request
import urllib.error

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "references", "config.json")


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def gitee_api(method, path, data=None):
    config = load_config()
    token = config["gitee"]["access_token"]
    owner = config["gitee"]["owner"]
    repo = config["gitee"]["repo"]
    url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/{path}"

    if data is not None:
        data["access_token"] = token
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
    else:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}access_token={token}"
        req = urllib.request.Request(url, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode("utf-8")}


def check_skill(skill_dir):
    issues = []
    dir_name = os.path.basename(skill_dir.rstrip("/"))
    if not re.match(r"^li-[a-z0-9-]+$", dir_name):
        issues.append(f"目录名 '{dir_name}' 不符合 kebab-case 规范")

    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_md):
        issues.append("缺少 SKILL.md 文件")
        return issues

    with open(skill_md, "r") as f:
        content = f.read()

    if not content.startswith("---\n"):
        issues.append("SKILL.md 缺少 frontmatter")
        return issues

    if not issues:
        print("✅ 技能规范检查通过")
    else:
        print("❌ 发现以下问题：")
        for i in issues:
            print(f"  - {i}")
    return issues


def push_file_to_gitee(file_path, repo_path, commit_msg):
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")

    existing = gitee_api("GET", f"contents/{repo_path}")
    data = {
        "content": content,
        "message": commit_msg,
        "branch": load_config()["gitee"]["branch"]
    }

    if "sha" in existing:
        data["sha"] = existing["sha"]
        result = gitee_api("PUT", f"contents/{repo_path}", data)
    else:
        result = gitee_api("POST", f"contents/{repo_path}", data)

    if "content" in result:
        print(f"✅ Gitee 推送成功: {repo_path}")
        return True
    else:
        print(f"❌ Gitee 推送失败: {result}")
        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "check":
        check_skill(sys.argv[2])
    elif cmd == "push":
        skill_dir = sys.argv[2]
        skill_name = sys.argv[3]
        skill_md = os.path.join(skill_dir, "SKILL.md")
        push_file_to_gitee(skill_md, f"skills/{skill_name}/SKILL.md", f"feat: 新增 {skill_name}")
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
