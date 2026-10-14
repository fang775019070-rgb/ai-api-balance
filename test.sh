#!/bin/zsh
set -euo pipefail
task_source="${0:A:h}"
cd "$task_source"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s Tests -v
/bin/zsh -n setup-api-key.command
/bin/zsh -n 启动余额看板.command
/bin/zsh -n package.sh
