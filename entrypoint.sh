#!/bin/bash
set -e

VERSION=""
PREVIOUS_TAG=""
CHANGELOG_PATH="CHANGELOG.md"
REPO=""
BINARY_NAME="app"
INCLUDE_DOWNLOAD_TABLE="true"
PLATFORMS="linux,darwin,windows,freebsd"
INCLUDE_CHANGELOG="true"
INCLUDE_COMMITS="true"
INCLUDE_INSTALL_GUIDE="true"

while [[ $# -gt 0 ]]; do
  case $1 in
    --version)
      VERSION="$2"
      shift 2
      ;;
    --previous-tag)
      PREVIOUS_TAG="$2"
      shift 2
      ;;
    --changelog-path)
      CHANGELOG_PATH="$2"
      shift 2
      ;;
    --repo)
      REPO="$2"
      shift 2
      ;;
    --binary-name)
      BINARY_NAME="$2"
      shift 2
      ;;
    --include-download-table)
      INCLUDE_DOWNLOAD_TABLE="$2"
      shift 2
      ;;
    --platforms)
      PLATFORMS="$2"
      shift 2
      ;;
    --include-changelog)
      INCLUDE_CHANGELOG="$2"
      shift 2
      ;;
    --include-commits)
      INCLUDE_COMMITS="$2"
      shift 2
      ;;
    --include-install-guide)
      INCLUDE_INSTALL_GUIDE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if [ -z "$VERSION" ]; then
  echo "Error: version is required"
  exit 1
fi

if [ -z "$REPO" ]; then
  echo "Error: repo is required"
  exit 1
fi

generate_download_table() {
  local table=""
  
  IFS=',' read -ra PLATFORM_ARRAY <<< "$PLATFORMS"
  
  local has_linux=false
  local has_darwin=false
  local has_windows=false
  local has_freebsd=false
  
  for p in "${PLATFORM_ARRAY[@]}"; do
    case "$p" in
      linux)  has_linux=true ;;
      darwin)  has_darwin=true ;;
      windows) has_windows=true ;;
      freebsd) has_freebsd=true ;;
    esac
  done
  
  table="${table}| 架构 |"
  [ "$has_windows" = true ] && table="${table} Windows |"
  [ "$has_linux" = true ] && table="${table} Linux |"
  [ "$has_darwin" = true ] && table="${table} macOS |"
  [ "$has_freebsd" = true ] && table="${table} FreeBSD |"
  table="${table}"$'\n'
  
  table="${table}|------|"
  [ "$has_windows" = true ] && table="${table}---------|"
  [ "$has_linux" = true ] && table="${table}-------|"
  [ "$has_darwin" = true ] && table="${table}-------|"
  [ "$has_freebsd" = true ] && table="${table}---------|"
  table="${table}"$'\n'
  
  local win_ext=".exe"
  [ "$has_windows" = false ] && win_ext=""
  
  table="${table}| **x86 (32位)** |"
  [ "$has_windows" = true ] && table="${table} [x86](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-windows-386${win_ext}) |"
  [ "$has_linux" = true ] && table="${table} [x86](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-linux-386) |"
  [ "$has_darwin" = true ] && table="${table} 不支持 |"
  [ "$has_freebsd" = true ] && table="${table} 不支持 |"
  table="${table}"$'\n'
  
  table="${table}| **x64 (64位)** |"
  [ "$has_windows" = true ] && table="${table} [x64](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-windows-amd64${win_ext}) |"
  [ "$has_linux" = true ] && table="${table} [x64](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-linux-amd64) |"
  [ "$has_darwin" = true ] && table="${table} [x64](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-darwin-amd64) |"
  [ "$has_freebsd" = true ] && table="${table} [x64](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-freebsd-amd64) |"
  table="${table}"$'\n'
  
  table="${table}| **ARM64** |"
  [ "$has_windows" = true ] && table="${table} [ARM64](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-windows-arm64${win_ext}) |"
  [ "$has_linux" = true ] && table="${table} [ARM64](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-linux-arm64) |"
  [ "$has_darwin" = true ] && table="${table} [ARM64](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-darwin-arm64) |"
  [ "$has_freebsd" = true ] && table="${table} [ARM64](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-freebsd-arm64) |"
  table="${table}"$'\n'
  
  table="${table}| **ARM (armv7)** |"
  [ "$has_windows" = true ] && table="${table} 不支持 |"
  [ "$has_linux" = true ] && table="${table} [ARM](https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}-linux-arm) |"
  [ "$has_darwin" = true ] && table="${table} 不支持 |"
  [ "$has_freebsd" = true ] && table="${table} 不支持 |"
  table="${table}"$'\n'
  
  echo "$table"
}

generate_release_notes() {
  local release_notes=""

  if [ "$INCLUDE_DOWNLOAD_TABLE" = "true" ]; then
    release_notes="${release_notes}## 📥 快速下载"
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}$(generate_download_table)"
    release_notes="${release_notes}"$'\n'
    
    local win_tip=""
    IFS=',' read -ra PLATFORM_ARRAY <<< "$PLATFORMS"
    for p in "${PLATFORM_ARRAY[@]}"; do
      [ "$p" = "windows" ] && win_tip="Windows 用户下载 \`.exe\` 文件，"
    done
    
    if [ -n "$win_tip" ]; then
      release_notes="${release_notes}> 💡 **提示**：${win_tip}其他系统下载后需要添加执行权限 \`chmod +x ${BINARY_NAME}-*\`"
      release_notes="${release_notes}"$'\n'
      release_notes="${release_notes}"$'\n'
    fi
    release_notes="${release_notes}---"
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}"$'\n'
  fi

  if [ "$INCLUDE_CHANGELOG" = "true" ] && [ -f "$CHANGELOG_PATH" ]; then
    release_notes="${release_notes}## 更新内容"
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}"$'\n'

    local changelog_content
    changelog_content=$(awk -v version="$VERSION" '
      /^##/ { 
        if (found) exit
        if ($0 ~ version) found=1
        next
      }
      found && /^##/ { exit }
      found { print }
    ' "$CHANGELOG_PATH")

    release_notes="${release_notes}${changelog_content}"
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}"$'\n'
  fi

  if [ "$INCLUDE_COMMITS" = "true" ]; then
    release_notes="${release_notes}## 提交记录"
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}"$'\n'

    if [ -z "$PREVIOUS_TAG" ]; then
      release_notes="${release_notes}生成从初始提交到 ${VERSION} 的提交记录"
      release_notes="${release_notes}"$'\n'
      release_notes="${release_notes}$(git log --pretty=format:"- %s (%h)" --no-merges)"
      release_notes="${release_notes}"$'\n'
    else
      release_notes="${release_notes}生成从 ${PREVIOUS_TAG} 到 ${VERSION} 的提交记录"
      release_notes="${release_notes}"$'\n'
      release_notes="${release_notes}$(git log "$PREVIOUS_TAG..$VERSION" --pretty=format:"- %s (%h)" --no-merges)"
      release_notes="${release_notes}"$'\n'
    fi
    release_notes="${release_notes}"$'\n'
  fi

  if [ "$INCLUDE_INSTALL_GUIDE" = "true" ] && [ "$INCLUDE_DOWNLOAD_TABLE" = "true" ]; then
    release_notes="${release_notes}---"
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}📦 **安装说明：**"
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}1. 从上方表格中选择并下载对应平台和架构的二进制文件"
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}2. Linux/macOS/BSD 用户需要赋予执行权限：\`chmod +x ${BINARY_NAME}-*\`（建议直接将文件改名为 ${BINARY_NAME} 方便调用和后续的升级）"
    release_notes="${release_notes}"$'\n'
    release_notes="${release_notes}3. 运行程序（建议直接将文件改名为 ${BINARY_NAME} 方便调用）\`${BINARY_NAME} help\`"
    release_notes="${release_notes}"$'\n'
  fi

  echo "$release_notes"
}

generate_release_notes