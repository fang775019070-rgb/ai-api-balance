# AI API 余额看板（AI API Balance）v2.1.0

从原个人 API 计费余额工具整理的公开版，菜单栏显示 DeepSeek、OpenRouter、Kimi 国内站余额和额度，每 5 分钟刷新。Key 保存在 macOS 钥匙串。账户余额与单个 Key 的额度分别标注，缓存值有 `~` 标记。

下载 ZIP 后保留整个 AIAPIBalance 文件夹，在 SwiftBar 中选择 Plugin 子文件夹，运行设置脚本输入自己的 Key。需要 macOS、SwiftBar 和 Python 3.9+。安装方法及接口口径见双语 README。

公开版改用系统隐藏密码提示，避免 Key 出现在命令行参数中；缓存采用所有者权限；HTTP 重定向被拒绝。自动测试使用模拟数据，不读取真实钥匙串，也不代表真实账户接口已全部验证。

## English

A public version of the original personal API billing/balance utility. Displays DeepSeek, OpenRouter and Kimi China balances in SwiftBar, refreshing every five minutes. Keys are stored in macOS Keychain using the system's hidden prompt. Account credits and individual key limits are distinguished; cached amounts have a `~` prefix.

Requires macOS, SwiftBar and Python 3.9+. Extract the whole AIAPIBalance folder, select its Plugin subfolder in SwiftBar and run the setup script with your own keys. The package includes Chinese and English setup guides. Automated tests use mocked responses and do not access real credentials or provider accounts.

Packaged from the public source by GitHub Actions. SHA256 checksums included. MIT License.
