#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/collect_diagnostics.sh [options]

Collect diagnostics for AI manager troubleshooting.

Options:
  -o, --output-dir <dir>   Output root directory (default: artifacts)
  -k, --keep-dir           Keep unpacked diagnostics directory (default: keep)
      --no-keep-dir        Remove unpacked diagnostics directory after tarball
  -m, --max-error-lines N  Max lines in recent_errors.log (default: 500)
      --no-config          Do not copy config files (.env/.json/.yaml)
      --no-logs            Do not copy log directories
      --dry-run            Print planned actions only
  -h, --help               Show this help
USAGE
}

OUT_ROOT="artifacts"
KEEP_DIR=1
MAX_ERROR_LINES=500
COPY_CONFIG=1
COPY_LOGS=1
DRY_RUN=0

while (($#)); do
  case "$1" in
    -o|--output-dir)
      OUT_ROOT="${2:-}"
      shift 2
      ;;
    -k|--keep-dir)
      KEEP_DIR=1
      shift
      ;;
    --no-keep-dir)
      KEEP_DIR=0
      shift
      ;;
    -m|--max-error-lines)
      MAX_ERROR_LINES="${2:-}"
      shift 2
      ;;
    --no-config)
      COPY_CONFIG=0
      shift
      ;;
    --no-logs)
      COPY_LOGS=0
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${OUT_ROOT}" ]]; then
  echo "output directory cannot be empty" >&2
  exit 2
fi

if ! [[ "${MAX_ERROR_LINES}" =~ ^[0-9]+$ ]]; then
  echo "max-error-lines must be an integer" >&2
  exit 2
fi

TS="$(date +%Y%m%d-%H%M%S)"
HOST="$(hostname 2>/dev/null || echo unknown-host)"
SAFE_HOST="$(echo "$HOST" | tr -cs 'A-Za-z0-9._-' '_')"
OUT_DIR="${OUT_ROOT}/diagnostics-${SAFE_HOST}-${TS}"
OUT_TAR="${OUT_ROOT}/ai-manager-diagnostics-${SAFE_HOST}-${TS}.tar.gz"

mkdir -p "${OUT_DIR}"

log() {
  printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"
}

run_cmd() {
  local name="$1"
  shift

  if ((DRY_RUN)); then
    log "DRY_RUN command -> ${name}: $*"
    return 0
  fi

  {
    echo "# command: $*"
    echo "# time: $(date -Iseconds)"
    echo
    "$@"
  } >"${OUT_DIR}/${name}.txt" 2>&1 || true
}

write_metadata() {
  local meta_file="${OUT_DIR}/metadata.txt"
  {
    echo "generated_at=$(date -Iseconds)"
    echo "hostname=${HOST}"
    echo "output_dir=${OUT_DIR}"
    echo "tarball=${OUT_TAR}"
    echo "max_error_lines=${MAX_ERROR_LINES}"
    echo "copy_logs=${COPY_LOGS}"
    echo "copy_config=${COPY_CONFIG}"
  } >"${meta_file}"
}

collect_recent_errors() {
  local dest="${OUT_DIR}/recent_errors.log"

  if ((DRY_RUN)); then
    log "DRY_RUN recent errors scan -> ${dest}"
    return 0
  fi

  {
    echo "# recent errors (last ${MAX_ERROR_LINES} matched lines)"
    echo
    if [[ -d logs || -d log || -d runtime_logs ]]; then
      rg -n -i 'error|exception|traceback|fatal|panic|failed|timeout|refused' logs log runtime_logs \
        2>/dev/null | tail -n "${MAX_ERROR_LINES}" || true
    else
      echo "No log directories found among: logs/, log/, runtime_logs/."
    fi
  } >"${dest}"
}

copy_logs() {
  ((COPY_LOGS)) || return 0

  for d in logs log runtime_logs; do
    if [[ -d "$d" ]]; then
      if ((DRY_RUN)); then
        log "DRY_RUN copy log dir -> $d"
      else
        cp -r "$d" "${OUT_DIR}/" 2>/dev/null || true
      fi
    fi
  done
}

redact_and_copy_config() {
  ((COPY_CONFIG)) || return 0

  local conf_dir="${OUT_DIR}/config_snapshot"
  if ((DRY_RUN)); then
    log "DRY_RUN copy config files -> ${conf_dir}"
    return 0
  fi

  mkdir -p "${conf_dir}"

  for f in .env .env.local .env.production *.yaml *.yml *.json; do
    [[ -f "$f" ]] || continue

    if [[ "$f" == *.json || "$f" == *.yaml || "$f" == *.yml ]]; then
      cp "$f" "${conf_dir}/" 2>/dev/null || true
      continue
    fi

    # Redact common secret-like values in env files.
    awk -F= '
      BEGIN { OFS="=" }
      /^[[:space:]]*#/ || NF < 2 { print; next }
      {
        key=$1
        val=$0
        sub(/^[^=]*=/, "", val)
        low=tolower(key)
        if (low ~ /(token|secret|password|passwd|key|apikey|api_key|bearer|credential)/) {
          print key, "***REDACTED***"
        } else {
          print $0
        }
      }
    ' "$f" >"${conf_dir}/${f}" 2>/dev/null || true
  done
}

package_output() {
  if ((DRY_RUN)); then
    log "DRY_RUN package -> ${OUT_TAR}"
    return 0
  fi

  mkdir -p "${OUT_ROOT}"
  tar -czf "${OUT_TAR}" -C "${OUT_ROOT}" "$(basename "${OUT_DIR}")"

  if ((KEEP_DIR == 0)); then
    rm -rf "${OUT_DIR}"
  fi
}

log "Collecting diagnostics into ${OUT_DIR}"

write_metadata

# 基础环境
run_cmd system_uname uname -a
run_cmd os_release bash -lc 'cat /etc/os-release'
run_cmd uptime uptime
run_cmd env_sample bash -lc 'env | sort | head -n 200'

# 资源使用
run_cmd cpu_top bash -lc 'ps -eo pid,ppid,comm,%cpu,%mem --sort=-%cpu | head -n 50'
run_cmd memory_free free -h
run_cmd disk_usage df -h

# 网络
run_cmd ip_addr bash -lc 'ip addr || ifconfig'
run_cmd listening_ports bash -lc 'ss -lntup || netstat -lntup'

# 运行时版本
run_cmd python_version bash -lc 'python --version || python3 --version'
run_cmd node_version bash -lc 'node --version'
run_cmd npm_version bash -lc 'npm --version'

# 进程快照
run_cmd processes bash -lc "ps -ef | rg -i 'ai|assistant|manager|guard|daemon|python|node'"

# 错误与文件收集
collect_recent_errors
copy_logs
redact_and_copy_config
package_output

if ((DRY_RUN)); then
  log "Dry-run complete (no files were written except directory skeleton)."
else
  log "Diagnostic package generated: ${OUT_TAR}"
  if ((KEEP_DIR)); then
    log "Unpacked diagnostics kept at: ${OUT_DIR}"
  fi
fi
