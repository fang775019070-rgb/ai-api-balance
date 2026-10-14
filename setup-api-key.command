#!/bin/zsh
set -eu

task_provider="${1:-}"
if [[ -z "$task_provider" ]]; then
  echo "请选择要设置的平台："
  echo "1) DeepSeek"
  echo "2) OpenRouter"
  echo "3) Kimi（国内站）"
  read "task_choice?请输入 1、2 或 3 / Choose a provider: "
  case "$task_choice" in
    1) task_provider="deepseek" ;;
    2) task_provider="openrouter" ;;
    3) task_provider="kimi" ;;
    *) echo "选择无效。"; read "?按回车键关闭。"; exit 1 ;;
  esac
fi

case "$task_provider" in
  deepseek) task_name="DeepSeek"; task_service="DeepSeek Balance Widget" ;;
  openrouter) task_name="OpenRouter"; task_service="OpenRouter Balance Widget" ;;
  kimi) task_name="Kimi"; task_service="Kimi Balance Widget" ;;
  *) echo "未知平台。"; read "?按回车键关闭。"; exit 1 ;;
esac

echo "$task_name API Key 设置 / API key setup"
if [[ "$task_provider" == "openrouter" ]]; then
  echo "提示：账户总余额需要 OpenRouter Management Key；普通 Key 只能显示自身剩余额度。"
  echo "Account credits require a Management Key; a regular key reports its own remaining limit."
fi
echo ""
echo "在系统的 password 提示处输入 Key，输入内容不会显示。取消请按 Control-C。"
echo "Enter the key at the password prompt. Input is hidden. Control-C cancels."
# Keep -w last: security prompts directly, keeping the key out of command arguments.
# -U updates an existing item; do not delete the old item before a successful save.
if /usr/bin/security add-generic-password -U -s "$task_service" -a "$USER" -w; then
  echo "$task_name API Key 已保存到 macOS 钥匙串 / Saved to macOS Keychain."
  echo "请在菜单中选择“立即刷新全部”。"
else
  echo "保存失败，请检查 macOS 钥匙串权限后重试 / Save failed; check Keychain access."
fi
read "?按回车键关闭窗口。"
