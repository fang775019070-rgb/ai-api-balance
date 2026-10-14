#!/bin/zsh
set -eu
if ! /usr/bin/open -a SwiftBar; then
  print -u2 '请先安装 SwiftBar / Please install SwiftBar first: https://github.com/swiftbar/SwiftBar/releases'
  read '?按回车键关闭 / Press Return to close.'
  exit 1
fi
/usr/bin/open 'swiftbar://refreshplugin?plugin=ai-api-balance.5m.py'
print '已请求启动并刷新。请确认 SwiftBar 的 Plugin Folder 指向本文件夹里的 Plugin。'
print 'Startup and refresh requested. Set the SwiftBar Plugin Folder to this package’s Plugin folder.'
