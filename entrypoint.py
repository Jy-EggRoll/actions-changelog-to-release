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
    parser.add_argument("--architectures", default="386,amd64,arm,arm64")
    parser.add_argument("--include-changelog", default="true")
    parser.add_argument("--include-commits", default="true")
    parser.add_argument("--include-install-guide", default="true")
    return parser.parse_args()


ARCH_LABELS = {
    "386": "x86 (32位)",
    "amd64": "x64 (64位)",
    "arm": "ARM (armv7)",
    "arm64": "ARM64",
}

WINDOWS_EXTS = {
    "386": ".exe",
    "amd64": ".exe",
    "arm": ".exe",
    "arm64": ".exe",
}


def generate_download_table(repo, version, binary_name, platforms, architectures):
    platforms = [p.strip() for p in platforms.split(",")]
    architectures = [a.strip() for a in architectures.split(",")]

    platform_cols = []
    has_windows = "windows" in platforms
    has_linux = "linux" in platforms
    has_darwin = "darwin" in platforms
    has_freebsd = "freebsd" in platforms

    if has_windows:
        platform_cols.append("Windows")
    if has_linux:
        platform_cols.append("Linux")
    if has_darwin:
        platform_cols.append("macOS")
    if has_freebsd:
        platform_cols.append("FreeBSD")

    lines = []
    lines.append("| 架构 | " + " | ".join(platform_cols) + " |")
    lines.append("|" + "|".join(["------"] * (len(platform_cols) + 1)) + "|")

    base = f"https://github.com/{repo}/releases/download/{version}/{binary_name}"

    for arch in architectures:
        label = ARCH_LABELS.get(arch, arch)
        row = f"| **{label}** |"

        for platform in platforms:
            ext = WINDOWS_EXTS.get(arch, "") if platform == "windows" else ""
            url = f"{base}-{platform}-{arch}{ext}"
            link = f"[{arch}]({url})"
            row += f" {link} |"

        lines.append(row)

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
                args.repo,
                args.version,
                args.binary_name,
                args.platforms,
                args.architectures,
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
