# AI 电脑管家 Debug 指南

你这次说“代码已经扔进来了”，但当前仓库里依然主要是诊断工具。
为了让你可以快速把真实问题定位出来，我把诊断脚本升级成了“可配置 + 默认脱敏 + 可 dry-run”的版本。

## 1) 快速开始

```bash
bash scripts/collect_diagnostics.sh
```

默认会生成：

- 压缩包：`artifacts/ai-manager-diagnostics-<hostname>-<timestamp>.tar.gz`
- 展开目录：`artifacts/diagnostics-<hostname>-<timestamp>/`

## 2) 常用参数

```bash
# 只预览动作，不实际采集
bash scripts/collect_diagnostics.sh --dry-run

# 自定义输出目录
bash scripts/collect_diagnostics.sh --output-dir ./tmp_artifacts

# 只保留压缩包，不保留展开目录
bash scripts/collect_diagnostics.sh --no-keep-dir

# 不收集配置文件（适合高敏感环境）
bash scripts/collect_diagnostics.sh --no-config

# 不拷贝 logs 目录
bash scripts/collect_diagnostics.sh --no-logs

# 控制 recent_errors.log 最多行数
bash scripts/collect_diagnostics.sh --max-error-lines 1000
```

## 3) 这版重点改进

- 增加命令行参数，支持输出目录、行数限制、日志/配置开关、dry-run。
- 新增 `metadata.txt`，记录本次采集参数和生成信息。
- `.env*` 默认按 key 关键词进行脱敏（`token/secret/password/key/...`）。
- 错误日志扫描规则增加 `timeout/refused`，对连接类故障更敏感。
- 压缩包名增加主机名，避免多机采集时重名覆盖。

## 4) 建议你优先看的文件

1. `recent_errors.log`
2. `processes.txt`
3. `listening_ports.txt`
4. `metadata.txt`

如果你把这些文件的关键片段贴出来，我可以继续帮你定位到具体模块和修复方向。
