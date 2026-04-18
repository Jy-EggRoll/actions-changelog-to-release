const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const env = process.env;

const VERSION = env.INPUT_VERSION;
const PREVIOUS_TAG = env.INPUT_PREVIOUS_TAG || '';
const CHANGELOG_PATH = env.INPUT_CHANGELOG_PATH || 'CHANGELOG.md';
const REPO = env.INPUT_REPO;
const BINARY_NAME = env.INPUT_BINARY_NAME || 'app';
const INCLUDE_DOWNLOAD_TABLE = env.INPUT_INCLUDE_DOWNLOAD_TABLE === 'true';
const PLATFORMS = (env.INPUT_PLATFORMS || 'linux,darwin,windows,freebsd').split(',');
const ARCHITECTURES = (env.INPUT_ARCHITECTURES || '386,amd64,arm,arm64').split(',');
const INCLUDE_CHANGELOG = env.INPUT_INCLUDE_CHANGELOG === 'true';
const INCLUDE_COMMITS = env.INPUT_INCLUDE_COMMITS === 'true';
const INCLUDE_INSTALL_GUIDE = env.INPUT_INCLUDE_INSTALL_GUIDE === 'true';

const ARCH_LABELS = {
  '386': 'x86 (32位)',
  'amd64': 'x64 (64位)',
  'arm': 'ARM (armv7)',
  'arm64': 'ARM64',
  'riscv64': 'RISC-V (64位)',
  's390x': 's390x',
  'ppc64le': 'PowerPC (64位)',
};

const WINDOWS_EXTS = {
  '386': '.exe',
  'amd64': '.exe',
  'arm': '.exe',
  'arm64': '.exe',
  'riscv64': '.exe',
  's390x': '.exe',
  'ppc64le': '.exe',
};

function generateDownloadTable() {
  const hasWindows = PLATFORMS.includes('windows');
  const hasLinux = PLATFORMS.includes('linux');
  const hasDarwin = PLATFORMS.includes('darwin');
  const hasFreeBSD = PLATFORMS.includes('freebsd');

  const cols = [];
  if (hasWindows) cols.push('Windows');
  if (hasLinux) cols.push('Linux');
  if (hasDarwin) cols.push('macOS');
  if (hasFreeBSD) cols.push('FreeBSD');

  let lines = [];
  lines.push('| 架构 | ' + cols.join(' | ') + ' |');
  lines.push('|' + '|'.repeat(cols.length + 1).replace(/\|/g, '------') + '|');

  const base = `https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}`;

  for (const arch of ARCHITECTURES) {
    const label = ARCH_LABELS[arch] || arch;
    let row = `| **${label}** |`;

    for (const platform of PLATFORMS) {
      const ext = platform === 'windows' ? (WINDOWS_EXTS[arch] || '') : '';
      const url = `${base}-${platform}-${arch}${ext}`;
      row += ` [${arch}](${url}) |`;
    }
    lines.push(row);
  }

  return lines.join('\n');
}

function extractChangelog() {
  if (!fs.existsSync(CHANGELOG_PATH)) return '';

  const content = fs.readFileSync(CHANGELOG_PATH, 'utf-8');
  const lines = content.split('\n');
  const result = [];
  let found = false;

  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (found) break;
      if (line.includes(VERSION)) found = true;
      continue;
    }
    if (found) result.push(line);
  }

  return result.join('\n').trim();
}

function getCommits() {
  let prefix, stdout;
  if (!PREVIOUS_TAG) {
    stdout = execSync('git log --pretty=format:"- %s (%h)" --no-merges', { encoding: 'utf-8' });
    prefix = `生成从初始提交到 ${VERSION} 的提交记录\n`;
  } else {
    stdout = execSync(`git log ${PREVIOUS_TAG}..${VERSION} --pretty=format:"- %s (%h)" --no-merges`, { encoding: 'utf-8' });
    prefix = `生成从 ${PREVIOUS_TAG} 到 ${VERSION} 的提交记录\n`;
  }
  return prefix + stdout;
}

function main() {
  const notes = [];

  if (INCLUDE_DOWNLOAD_TABLE) {
    notes.push('## 📥 快速下载\n');
    notes.push(generateDownloadTable());
    notes.push('');

    if (PLATFORMS.includes('windows')) {
      notes.push(`> 💡 **提示**：Windows 用户下载 \`.exe\` 文件，其他系统下载后需要添加执行权限 \`chmod +x ${BINARY_NAME}-*\``);
      notes.push('');
    }
    notes.push('---\n');
  }

  if (INCLUDE_CHANGELOG) {
    const changelog = extractChangelog();
    if (changelog) {
      notes.push('## 更新内容\n');
      notes.push(changelog);
      notes.push('');
    }
  }

  if (INCLUDE_COMMITS) {
    notes.push('## 提交记录\n');
    notes.push(getCommits());
    notes.push('');
  }

  if (INCLUDE_INSTALL_GUIDE && INCLUDE_DOWNLOAD_TABLE) {
    notes.push('---\n');
    notes.push('📦 **安装说明：**\n');
    notes.push('');
    notes.push(`1. 从上方表格中选择并下载对应平台和架构的二进制文件`);
    notes.push(`2. Linux/macOS/BSD 用户需要赋予执行权限：\`chmod +x ${BINARY_NAME}-*\`（建议直接将文件改名为 ${BINARY_NAME} 方便调用和后续的升级）`);
    notes.push(`3. 运行程序（建议直接将文件改名为 ${BINARY_NAME} 方便调用）\`${BINARY_NAME} help\``);
  }

  const output = notes.join('\n');
  fs.writeFileSync(process.env.GITHUB_OUTPUT, `content=${output}\n`, { flag: 'a' });
}

main();