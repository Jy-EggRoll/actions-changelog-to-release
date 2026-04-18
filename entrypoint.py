#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--previous-tag", default="")
    parser.add_argument("--changelog-path", default="CHANGELOG.md")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--binary-name", default="app")
    parser.add_argument("--include-download-table", default="true")
    parser.add_argument("--platforms", default="linux,darwin,windows,freebsd")
    parser.add_argument("--include-changelog", default="true")
    parser.add_argument("--include-commits", default="true")
    parser.add_argument("--include-install-guide", default="true")
    return parser.parse_args()


def generate_download_table(repo, version, binary_name, platforms):
    platforms = [p.strip() for p in platforms.split(",")]

    cols = []
    has_windows = "windows" in platforms
    has_linux = "linux" in platforms
    has_darwin = "darwin" in platforms
    has_freebsd = "freebsd" in platforms

    if has_windows:
        cols.append("Windows")
    if has_linux:
        cols.append("Linux")
    if has_darwin:
        cols.append("macOS")
    if has_freebsd:
        cols.append("FreeBSD")

    win_ext = ".exe" if has_windows else ""

    lines = []
    lines.append("| 架构 | " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["------"] * (len(cols) + 1)) + "|")

    def cell(w, l, d, f):
        parts = []
        if has_windows and w:
            parts.append(f"[w]({w})")
        else:
            parts.append("")
        if has_linux and l:
            parts.append(f"[l]({l})")
        else:
            parts.append("")
        if has_darwin and d:
            parts.append(f"[d]({d})")
        else:
            parts.append("")
        if has_freebsd and f:
            parts.append(f"[f]({f})")
        else:
            parts.append("")
        return " | ".join(("不支持" if not p else p) for p in parts)

    base = f"https://github.com/{repo}/releases/download/{version}/{binary_name}"

    x86_row = "| **x86 (32位)** | "
    if has_windows:
        x86_row += f"[x86]({base}-windows-386{win_ext}) | "
    if has_linux:
        x86_row += f"[x86]({base}-linux-386) | "
    if has_darwin:
        x86_row += "不支持 | "
    if has_freebsd:
        x86_row += "不支持 |"
    lines.append(x86_row.rstrip(" |"))

    x64_row = "| **x64 (64位)** | "
    if has_windows:
        x64_row += f"[x64]({base}-windows-amd64{win_ext}) | "
    if has_linux:
        x64_row += f"[x64]({base}-linux-amd64) | "
    if has_darwin:
        x64_row += f"[x64]({base}-darwin-amd64) | "
    if has_freebsd:
        x64_row += f"[x64]({base}-freebsd-amd64) |"
    lines.append(x64_row.rstrip(" |"))

    arm64_row = "| **ARM64** | "
    if has_windows:
        arm64_row += f"[ARM64]({base}-windows-arm64{win_ext}) | "
    if has_linux:
        arm64_row += f"[ARM64]({base}-linux-arm64) | "
    if has_darwin:
        arm64_row += f"[ARM64]({base}-darwin-arm64) | "
    if has_freebsd:
        arm64_row += f"[ARM64]({base}-freebsd-arm64) |"
    lines.append(arm64_row.rstrip(" |"))

    arm_row = "| **ARM (armv7)** | "
    if has_windows:
        arm_row += "不支持 | "
    if has_linux:
        arm_row += f"[ARM]({base}-linux-arm) | "
    if has_darwin:
        arm_row += "不支持 | "
    if has_freebsd:
        arm_row += "不支持 |"
    lines.append(arm_row.rstrip(" |"))

    return "\n".join(lines)


def extract_changelog(version, changelog_path):
    if not os.path.exists(changelog_path):
        return ""

    content = Path(changelog_path).read_text()
    lines = content.split("\n")
    result = []
    found = False

    for line in lines:
        if line.startswith("## "):
            if found:
                break
            if version in line:
                found = True
            continue
        if found:
            result.append(line)

    return "\n".join(result).strip()


def get_commits(previous_tag, version):
    if not previous_tag:
        result = subprocess.run(
            ["git", "log", "--pretty=format:- %s (%h)", "--no-merges"],
            capture_output=True,
            text=True,
        )
        prefix = f"生成从初始提交到 {version} 的提交记录\n"
    else:
        result = subprocess.run(
            [
                "git",
                "log",
                f"{previous_tag}..{version}",
                "--pretty=format:- %s (%h)",
                "--no-merges",
            ],
            capture_output=True,
            text=True,
        )
        prefix = f"生成从 {previous_tag} 到 {version} 的提交记录\n"

    return prefix + result.stdout


def main():
    args = parse_args()
    notes = []

    if args.include_download_table == "true":
        notes.append("## 📥 快速下载\n")
        notes.append(
            generate_download_table(
                args.repo, args.version, args.binary_name, args.platforms
            )
        )
        notes.append("")

        if "windows" in args.platforms:
            notes.append(
                "> 💡 **提示**：Windows 用户下载 `.exe` 文件，其他系统下载后需要添加执行权限 `chmod +x {}-*`".format(
                    args.binary_name
                )
            )
            notes.append("")
        notes.append("---\n")

    if args.include_changelog == "true":
        changelog = extract_changelog(args.version, args.changelog_path)
        if changelog:
            notes.append("## 更新内容\n")
            notes.append(changelog)
            notes.append("")

    if args.include_commits == "true":
        notes.append("## 提交记录\n")
        notes.append(get_commits(args.previous_tag, args.version))
        notes.append("")

    if args.include_install_guide == "true" and args.include_download_table == "true":
        notes.append("---\n")
        notes.append("📦 **安装说明：**\n")
        notes.append("")
        notes.append(f"1. 从上方表格中选择并下载对应平台和架构的二进制文件")
        notes.append(
            f"2. Linux/macOS/BSD 用户需要赋予执行权限：`chmod +x {args.binary_name}-*`（建议直接将文件改名为 {args.binary_name} 方便调用和后续的升级）"
        )
        notes.append(
            f"3. 运行程序（建议直接将文件改名为 {args.binary_name} 方便调用）`{args.binary_name} help`"
        )

    print("\n".join(notes))


if __name__ == "__main__":
    main()
