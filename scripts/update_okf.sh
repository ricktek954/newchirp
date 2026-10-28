#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NEWCHIRP_OKF_VENV_DIR="${NEWCHIRP_OKF_VENV_DIR:-/tmp/newchirp-okf-venv}"
OKF_BIN="$NEWCHIRP_OKF_VENV_DIR/bin/okf"

find_okf_python() {
  if [[ -n "${NEWCHIRP_OKF_PYTHON:-}" ]]; then
    if [[ -x "$NEWCHIRP_OKF_PYTHON" ]]; then
      printf '%s\n' "$NEWCHIRP_OKF_PYTHON"
      return 0
    fi
    echo "Ignoring NEWCHIRP_OKF_PYTHON=$NEWCHIRP_OKF_PYTHON because it is not executable." >&2
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
  elif [[ -x /opt/homebrew/bin/python3 ]]; then
    printf '%s\n' /opt/homebrew/bin/python3
  else
    echo "Unable to find python3. Set NEWCHIRP_OKF_PYTHON to a Python 3 executable." >&2
    return 127
  fi
}

bootstrap_okf() {
  if [[ ! -x "$OKF_BIN" ]]; then
    echo "Creating OKF venv at $NEWCHIRP_OKF_VENV_DIR"
    "$(find_okf_python)" -m venv "$NEWCHIRP_OKF_VENV_DIR"
    "$NEWCHIRP_OKF_VENV_DIR/bin/pip" install --upgrade "okf-generator==0.1.53"
  fi
}

refresh_bundle() {
  local source_dir="$1"
  local bundle_dir="$2"

  if "$OKF_BIN" update "$source_dir" "$bundle_dir"; then
    :
  else
    "$OKF_BIN" generate "$source_dir" "$bundle_dir"
  fi
}

case "${1:-}" in
  --bootstrap)
    bootstrap_okf
    exit 0
    ;;
  --watch)
    bootstrap_okf
    cd "$PROJECT_ROOT"
    refresh_bundle lib okf_bundle
    refresh_bundle scripts okf_bundle_scripts
    echo "Watching lib -> okf_bundle and scripts -> okf_bundle_scripts"

    pids=()
    "$OKF_BIN" update --watch lib okf_bundle &
    pids+=("$!")
    "$OKF_BIN" update --watch scripts okf_bundle_scripts &
    pids+=("$!")

    trap 'kill "${pids[@]}" 2>/dev/null || true' INT TERM
    wait "${pids[@]}"
    exit 0
    ;;
  "")
    ;;
  *)
    echo "Usage: $0 [--bootstrap|--watch]" >&2
    exit 64
    ;;
esac

bootstrap_okf
cd "$PROJECT_ROOT"

refresh_bundle lib okf_bundle
refresh_bundle scripts okf_bundle_scripts
