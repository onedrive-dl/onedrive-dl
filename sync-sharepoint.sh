#!/usr/bin/env bash
# Convenience launcher for Linux and macOS.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$project_dir/sharepoint_public_sync.py" "$@"
