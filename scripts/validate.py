#!/usr/bin/env python3
"""prd-craft 技能校验工具。

用法:
    python scripts/validate.py                        # 校验技能包自身结构
    python scripts/validate.py <skill_dir>            # 校验指定技能目录
    python scripts/validate.py --body <prd.md>        # 扫描产出的 PRD 正文，检查杂项泄漏
    python scripts/validate.py --body <prd.md> --companion <sup.md>
                                                      # 同时校验正文与补充说明的对应关系

检查项（技能自检）:
    1. SKILL.md 的 YAML frontmatter（name / description 单行 / agent_created）
    2. SKILL.md 中 `references/...` 引用路径是否存在
    3. 全部 .md 文件内的相对链接是否可解析
    4. mermaid 代码块是否含可识别的图类型
    5. 必备文件（含 companion-doc.md）是否存在

检查项（正文杂项泄漏扫描）:
    G9 逐项：元信息行、版本号、日期、作者、名词解释、角色读者、需求背景、
    目标用户、需求目标、成功标准、待确认清单、篇幅说明、配套索引、未决标记

退出码: 0 = 无错误, 1 = 存在错误
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------- 杂项泄漏规则

LEAK_RULES = [
    ("元信息行", r"^>\s*(文档类型|版本|日期|作者)\s*[:：]", 1),
    ("版本号", r"v\d+\.\d+", 1),
    ("日期", r"20\d\d-\d\d-\d\d", 1),
    ("需求背景", r"需求背景|业务现状|痛点|触发因素", 1),
    ("目标用户", r"目标用户|用户画像|使用角色", 1),
    ("需求目标", r"需求目标|成功标准|北极星", 1),
    ("待确认清单", r"待确认清单|待定事项|待确认事项", 1),
    ("篇幅说明", r"篇幅对照|篇幅变化|压缩说明|本次变更", 1),
    ("配套索引", r"配套文档索引|补充说明文档索引", 1),
    ("版本记录", r"版本记录|变更明细|变更摘要", 1),
    ("角色与读者", r"角色与读者|读者指引", 1),
    ("未决标记", r"\[待补充[:：]|待定|TBD|TODO", 1),
    ("变体标记", r"精简版|完整版|终版|草稿版|讨论稿", 1),
]

ALLOW_MARK = "PRD-LEAK-SCAN-ALLOW"

BUF = io.StringIO()
errors = []
warns = []


def out(s=""):
    BUF.write(str(s) + "\n")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def finish():
    text = BUF.getvalue()
    sys.stdout.write(text)
    sys.stdout.flush()
    return 1 if errors else 0


# ---------------------------------------------------------------- 正文扫描


def scan_body(path, companion=None):
    txt = load(path)
    lines = txt.splitlines()
    hits = []
    for i, line in enumerate(lines, 1):
        if ALLOW_MARK in line:
            continue
        for name, pat, _ in LEAK_RULES:
            if re.search(pat, line):
                hits.append((i, name, line.strip()[:90]))
                break

    out("=== 正文杂项泄漏扫描 (G9) ===")
    out("文件: " + path)
    out("行数: %d" % len(lines))
    if hits:
        out("命中 %d 处：" % len(hits))
        for ln, name, snippet in hits:
            out("  L%-5d [%s] %s" % (ln, name, snippet))
        errors.append("正文存在 %d 处杂项泄漏" % len(hits))
    else:
        out("命中 0 处 —— G9 通过")
    out("")

    # 结构检查：首行必须是标题，其后不得紧跟元信息
    out("=== 正文形态检查 ===")
    if not lines or not lines[0].startswith("# "):
        errors.append("正文首行不是一级标题")
        out("首行: %r  <<< 违规" % (lines[0] if lines else ""))
    else:
        out("首行: %s  OK" % lines[0])
    out("")

    # 待补充占位符必须为 0
    n = len(re.findall(r"\[待补充", txt))
    out("正文 [待补充] 出现次数: %d %s" % (n, "OK" if n == 0 else "<<< 违规"))
    if n:
        errors.append("正文出现 %d 处 [待补充]" % n)
    out("")

    # 补充说明对应检查
    if companion:
        if not os.path.isfile(companion):
            errors.append("补充说明文档不存在: " + companion)
        else:
            ct = load(companion)
            out("=== 补充说明检查 ===")
            out("文件: " + companion)
            secs = ["1 文档信息", "2 需求背景", "3 待确认事项", "4 版本变更", "6 配套文档"]
            for s in secs:
                ok = s.split(" ", 1)[1] in ct
                out("  缺少 %s" % s if not ok else "  %s OK" % s)
                if not ok:
                    errors.append("补充说明缺少章节: " + s)
            cplace = len(re.findall(r"\[待补充", ct))
            out("补充说明 [待补充] 出现次数: %d" % cplace)
            if cplace == 0:
                warns.append("补充说明未使用 [待补充]，请确认确无待确认项")
            if "正文留空位置对照" not in ct:
                errors.append("补充说明缺少「正文留空位置对照」")
            else:
                out("  正文留空位置对照 OK")
    out("")


# ---------------------------------------------------------------- 技能自检


def scan_skill(root):
    skill_md = os.path.join(root, "SKILL.md")
    if not os.path.isfile(skill_md):
        errors.append("未找到 SKILL.md: " + skill_md)
        return

    raw = load(skill_md)
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", raw, re.S)
    if not m:
        errors.append("SKILL.md 缺少 YAML frontmatter")
    else:
        fm = m.group(1)
        if not re.search(r"^name:\s*[\w-]+\s*$", fm, re.M):
            errors.append("frontmatter 的 name 缺失或不合法")
        if not re.search(r"^agent_created:\s*true\s*$", fm, re.M):
            errors.append("frontmatter 缺少 agent_created: true")
        d = re.search(r"^description:\s*(.+)$", fm, re.M)
        if not d:
            errors.append("frontmatter 缺少 description")
        else:
            out("[desc] %d chars, single-line OK" % len(d.group(1)))
        if ">-" in fm or re.search(r"^description:\s*\|", fm, re.M):
            errors.append("description 使用了 YAML 折叠块，必须写成单行")

    refs = sorted(
        r for r in set(re.findall(r"`(references/[^`]+\.md)`", raw))
        if "<" not in r and ">" not in r
    )
    for r in refs:
        if not os.path.isfile(os.path.join(root, r.replace("/", os.sep))):
            errors.append("SKILL.md 引用了不存在的文件: " + r)
    out("[refs] SKILL.md 引用 %d 个文件" % len(refs))

    required = [
        "references/shared/conventions.md",
        "references/shared/companion-doc.md",
        "references/shared/quality-gate.md",
        "references/shared/metrics-spec.md",
        "references/shared/exception-handling.md",
        "references/discovery.md",
        "references/software-system/template.md",
        "references/software-system/page-structure.md",
        "references/agent-system/template.md",
        "references/agent-system/capability-spec.md",
    ]
    missing = [p for p in required if not os.path.isfile(os.path.join(root, p.replace("/", os.sep)))]
    for p in missing:
        errors.append("必备文件缺失: " + p)
    out("[required] 必备文件 %d/%d" % (len(required) - len(missing), len(required)))

    allmd = []
    for dirpath, _, filenames in os.walk(root):
        if os.sep + "scripts" in dirpath:
            continue
        for fn in filenames:
            if fn.endswith(".md"):
                allmd.append(os.path.join(dirpath, fn))

    linkcount = 0
    for f in allmd:
        txt = load(f)
        for link in sorted(set(re.findall(r"`((?:\.\./)*[A-Za-z0-9_\-/]+\.md)`", txt))):
            if link.startswith("references/"):
                target = os.path.join(root, link.replace("/", os.sep))
            else:
                target = os.path.join(os.path.dirname(f), link.replace("/", os.sep))
            linkcount += 1
            if not os.path.isfile(os.path.normpath(target)):
                errors.append("%s -> 断链: %s" % (os.path.relpath(f, root), link))
    out("[links] 校验 %d 条内部相对链接" % linkcount)

    mermaid = 0
    for f in allmd:
        txt = load(f)
        blocks = re.findall(r"```mermaid\r?\n(.*?)```", txt, re.S)
        mermaid += len(blocks)
        for b in blocks:
            if not re.search(r"^\s*(flowchart|graph|sequenceDiagram|erDiagram|stateDiagram|classDiagram)", b):
                warns.append("%s 存在未识别图类型的 mermaid 块" % os.path.relpath(f, root))
    out("[mermaid] %d 个流程图代码块" % mermaid)

    # 占位符双轨制自检：模板不得引导在正文写 [待补充]
    for tpl in ("references/software-system/template.md", "references/agent-system/template.md"):
        p = os.path.join(root, tpl.replace("/", os.sep))
        if os.path.isfile(p):
            t = load(p)
            if "正文净化约束" not in t:
                errors.append("%s 缺少「正文净化约束」段落" % tpl)
            if "companion-doc.md" not in t:
                errors.append("%s 未引用 companion-doc.md" % tpl)
    out("[templates] 正文净化约束与 companion-doc 引用已检查")

    total = sum(len(load(f)) for f in allmd)
    out("[size] %d 个文件, 合计 %d 字符" % (len(allmd), total))


# ---------------------------------------------------------------- main


def main():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        sys.stdout.write((__doc__ or "").strip() + "\n")
        sys.exit(0)
    if args and args[0] == "--body":
        body = args[1]
        companion = None
        if "--companion" in args:
            companion = args[args.index("--companion") + 1]
        scan_body(body, companion)
    else:
        root = os.path.abspath(args[0]) if args else DEFAULT_ROOT
        scan_skill(root)

    out("")
    out("=== ERRORS ===" if errors else "=== ERRORS: none ===")
    for e in errors:
        out(" - " + e)
    out("=== WARNINGS ===" if warns else "=== WARNINGS: none ===")
    for w in warns:
        out(" - " + w)
    sys.exit(finish())


main()
