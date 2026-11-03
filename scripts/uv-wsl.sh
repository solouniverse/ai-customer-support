#!/usr/bin/env bash
set -euo pipefail

export UV_PROJECT_ENVIRONMENT=.venv-linux
export UV_LINK_MODE=copy
exec uv "$@"
