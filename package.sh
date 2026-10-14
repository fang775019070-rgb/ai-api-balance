#!/bin/zsh
set -euo pipefail
task_source="${0:A:h}"
task_dist="$task_source/dist"
task_package="$task_dist/AIAPIBalance"
mkdir -p "$task_package/Plugin"
for task_file in README.md README.en.md LICENSE setup-api-key.command 启动余额看板.command; do
  cp "$task_source/$task_file" "$task_package/$task_file"
done
cp "$task_source/Plugin/ai-api-balance.5m.py" "$task_package/Plugin/"
chmod +x "$task_package/Plugin/ai-api-balance.5m.py" "$task_package/setup-api-key.command" "$task_package/启动余额看板.command"
cd "$task_dist"
task_temp="$(mktemp -d "$task_dist/.package.XXXXXX")"
trap 'rm -f "$task_temp/package.zip"; rmdir "$task_temp"' EXIT
# Select files explicitly; never package local caches, credentials or build files.
/usr/bin/zip -q -r "$task_temp/package.zip" \
  AIAPIBalance/README.md AIAPIBalance/README.en.md AIAPIBalance/LICENSE \
  AIAPIBalance/setup-api-key.command AIAPIBalance/启动余额看板.command \
  AIAPIBalance/Plugin/ai-api-balance.5m.py
mv "$task_temp/package.zip" AIAPIBalance-v2.1.0.zip
/usr/bin/shasum -a 256 AIAPIBalance-v2.1.0.zip > AIAPIBalance-SHA256SUMS.txt
print "Packaged: $task_dist/AIAPIBalance-v2.1.0.zip"
