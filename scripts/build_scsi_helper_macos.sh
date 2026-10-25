#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT="${1:-$PROJECT_DIR/tools/newchirp_scsi_mac}"

clang \
  -O2 \
  -Wall \
  -Wextra \
  -Werror \
  -framework IOKit \
  -framework CoreFoundation \
  "$PROJECT_DIR/tools/newchirp_scsi_mac.c" \
  -o "$OUTPUT"

chmod +x "$OUTPUT"
echo "Built $OUTPUT"
